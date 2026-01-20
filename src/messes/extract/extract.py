#!/usr/bin/python3
""" 
Extract data from Excel workbooks, csv files, and JSON files.
    
 Usage:
    messes extract <metadata_source>... [--delete <metadata_section>...] [options]
    messes extract --help

    <metadata_source> - tagged input metadata source as csv/json filename or 
                        xlsx_filename[:worksheet_name|regular_expression] or 
                        google_sheets_url[:worksheet_name|regular_expression]
                        "#export" worksheet name is the default.

 Options:
    -h, --help                          - show this help documentation.
    -v, --version                       - show the version.
    --silent                            - print no warning messages.
    --output <filename_json>            - output json filename.
    --compare <filename_json>           - compare extracted metadata to given JSONized metadata.
    --modify <source>                   - modification directives worksheet name, regular expression, csv/json filename, or 
                                          xlsx_filename:[worksheet_name|regular_expression] or 
                                          google_sheets_url[:worksheet_name|regular_expression] 
                                          [default: #modify].
    --end-modify <source>               - apply modification directives after all metadata merging. Requires csv/json filename or 
                                          xlsx_filename:[worksheet_name|regular_expression] or 
                                          google_sheets_url[:worksheet_name|regular_expression].
    --automate <source>                 - automation directives worksheet name, regular expression, csv/json filename, or 
                                          xlsx_filename:[worksheet_name|regular_expression] or 
                                          google_sheets_url[:worksheet_name|regular_expression] 
                                          [default: #automate].
    --save-directives <filename_json>   - output filename with modification and automation directives in JSON format.
    --save-export <filetype>            - output export worksheet with suffix "_export" and with the indicated xlsx/csv format extension.
    --show <show_option>                - show a part of the metadata. See options below.
    --delete <metadata_section>...      - delete a section of the JSONized metadata. Section format is tableKey or tableKey,IDKey or tableKey,IDKey,fieldName. These can be regular expressions.
    --keep <metadata_tables>            - only keep the selected tables.  Delete the rest.  Table format is tableKey,tableKey,... The tableKey can be a regular expression.
    --file-cleaning <remove_regex>      - a string or regular expression to remove characters in input files, removes unicode and \r characters by default, enter "None" to disable [default: _x([0-9a-fA-F]{4})_|\r].

Show Options:
  tables    - show tables in the extracted metadata.
  lineage   - show parent-child lineages per table.
  all       - show every option.

Regular Expression Format:
  Regular expressions have the form "r'...'" on the command line.
  The re.match function is used, which matches from the beginning of a string, meaning that a regular expression matches as if it starts with a "^".

 Directives JSON Format:
   {
    "modification" : { table : { field :  { "(exact|regex|levenshtein)\-(first|first\-nowarn|unique|all)" :
                      { field_value : { "assign" : { field : value,... }, "append" : { field : value,... }, "prepend" : { field : value,... },
                                        "regex" : { field : regex_pair,... }, "delete" : [ field,... ], "rename" : { old_field : new_field } } } } } }
    "automation" : [ { "header_tag_descriptions" : [ { "header" : column_description, "tag" : tag_description, "required" : true|false } ],   "exclusion_test" : exclusion_value, "insert" : [ [ cell_content, ... ] ] } ]
   }

"""
#
#   Written by Hunter Moseley, 06/18/2014
#   Copyright Hunter Moseley, 06/18/2014. All rights reserved.
#
#   Hugely Revised (Over 75%) by Hunter Moseley, 08/29/2020
#   Copyright Hunter Moseley, 08/29/2020. All rights reserved.
#
#   Revised significantly by Travis Thompson, 03/03/2023



from __future__ import annotations
import os.path
import copy
import sys
import re
import collections
import pathlib
from typing import TextIO
import json
import urllib.error

import pandas
import docopt
import jellyfish

try:
    from messes.extract import cythonized_tagSheet
except ImportError:
    from messes.extract import tagSheet as cythonized_tagSheet
from messes import __version__

silent = False

def main() :
    args = docopt.docopt(__doc__, version = __version__)
    
    if args["--silent"]:
        global silent
        silent = True
        
    if args["--file-cleaning"] == "None":
        args["--file-cleaning"] = None
        
    
    tagParser = TagParser()
        

    if any([True for arg in sys.argv if arg == "--modify"]):
        modifyDefaulted = False
    else:
        modifyDefaulted = True
        
    if any([True for arg in sys.argv if arg == "--automate"]):
        automateDefaulted = False
    else:
        automateDefaulted = True

    for metadataSource in args["<metadata_source>"]:
        tagParser.readMetadata(metadataSource, args["--automate"], automateDefaulted, args["--modify"], modifyDefaulted, args["--file-cleaning"], args["--save-export"])

    ## --end-modify is needed so that the merged metadata files can all be modified after being merged together.
    ## Without this each metadatasource only gets its own modification.
    if args["--end-modify"] != None:
        modificationSource = args["--end-modify"]
            
        if not TagParser.hasFileExtension(modificationSource) and \
           not TagParser.isGoogleSheetsFile(modificationSource):
               if (reMatch := re.search(r"(.*\.xls[xm]?)", metadataSource)):
                   modificationFilePath = reMatch.group(1) 
                   modificationSheetName = modificationSource
               elif (reMatch := re.search(r"docs.google.com/spreadsheets/d/([^/]*)/.*$", metadataSource)):
                   modificationFilePath = "https://docs.google.com/spreadsheets/d/" + reMatch.group(1) + "/export?format=xlsx"
                   modificationSheetName = modificationSource
               else:
                   modificationFilePath = modificationSource
                   modificationSheetName = None
        elif re.search(r"\.xls[xm]?$", modificationSource):
            modificationFilePath = modificationSource
            modificationSheetName = "#modify"
        elif (reMatch := re.search(r"^(.*\.xls[xm]?):(.*)$", modificationSource)):
            modificationFilePath = reMatch.group(1)
            modificationSheetName = reMatch.group(2)
        elif (reMatch := re.search(r"docs.google.com/spreadsheets/d/([^/]*)/[^:]*$", modificationSource)):
            modificationFilePath = "https://docs.google.com/spreadsheets/d/" + reMatch.group(1) + "/export?format=xlsx"
            modificationSheetName = "#modify"
        elif (reMatch := re.search(r"docs.google.com/spreadsheets/d/([^/]*)/.*:(.*)$", modificationSource)):
            modificationFilePath = "https://docs.google.com/spreadsheets/d/" + reMatch.group(1) + "/export?format=xlsx"
            modificationSheetName = reMatch.group(2)
        else:
            modificationFilePath = modificationSource
            modificationSheetName = None

        modificationDirectives = tagParser.readDirectives(modificationFilePath, modificationSheetName, "modification", args["--file-cleaning"])
        tagParser.modify(modificationDirectives)

    if getattr(tagParser, "unusedModifications", None) != None and not silent:
        for (tableKey, fieldKey, comparisonType, modificationID) in tagParser.unusedModifications:
            print("Warning: modification directive #" + tableKey + "." + fieldKey + "." + comparisonType + "." + modificationID + " never matched.", file=sys.stderr)

    if args["--delete"]:
        sections = [ section.split(",") for section in args["--delete"] ]
        tagParser.deleteMetadata(sections)

    if args["--keep"]:
        keep_strings = args["--keep"].split(",")
        keep_regexes = []
        for string in keep_strings:
            if re.match(TagParser.reDetector, string):
                keep_regexes.append(re.compile(re.match(TagParser.reDetector, string)[1]))
            else:
                keep_regexes.append(re.compile("^" + re.escape(string) + "$"))
        
        tables_to_keep = []
        for regex in keep_regexes:
            for table in tagParser.extraction:
                if re.search(regex, table):
                    tables_to_keep.append(table)
        sections = [ [ tableKey ] for tableKey in tagParser.extraction.keys() if tableKey not in tables_to_keep ]
        tagParser.deleteMetadata(sections)

    if args["--show"]:
        
        validShowSubOption = False
        
        if args["--show"] == "tables" or args["--show"] == "all":
            print("Tables: "," ".join(tagParser.extraction.keys()))
            validShowSubOption = True
    
        if args["--show"] == "lineage" or args["--show"] == "all":
            lineages = tagParser.generateLineages()
            tagParser.printLineages(lineages,indentation=0, file=sys.stdout)
            validShowSubOption = True
        
        if not validShowSubOption:
            print("Unknown sub option for \"--show\" option: \"" + args["--show"] + "\"", file=sys.stderr)

    if args["--output"]: # save to JSON
        if pathlib.Path(args["--output"]).suffix != ".json":
            args["--output"] = args["--output"] + ".json"
        with open(args["--output"],'w') as jsonFile :
            jsonFile.write(json.dumps(tagParser.extraction, sort_keys=True, indent=2, separators=(',', ': ')))

    if args["--compare"]:
        comparePath = pathlib.Path(args["--compare"])
        if comparePath.exists():
            if comparePath.suffix != ".json":
                print("Error: The provided file for comparison is not a JSON file.", file=sys.stderr)
            else:
                with open(comparePath, 'r') as jsonFile:
                    otherMetadata = json.load(jsonFile)
                    print("Comparison", file=sys.stdout)
                    if not tagParser.compare(otherMetadata, file=sys.stdout):
                        print("No differences detected.", file=sys.stdout)
        else:
            print("Error: The provided file for comparison does not exist.", file=sys.stderr)

    if args["--save-directives"]:
        if pathlib.Path(args["--save-directives"]).suffix != ".json":
            args["--save-directives"] = args["--save-directives"] + ".json"
        if getattr(tagParser, "modificationDirectives", None) != None or getattr(tagParser, "automationDirectives", None) != None:
            directives = {}
            if getattr(tagParser, "modificationDirectives", None) != None:
                directives["modification"] = tagParser.modificationDirectives

            if getattr(tagParser, "automationDirectives", None) != None:
                directives["automation"] = tagParser.automationDirectives

            with open(args["--save-directives"],'w') as jsonFile :
                jsonFile.write(json.dumps(directives, sort_keys=True, indent=2, separators=(',', ': ')))
        else:
            print("There are no directives to save.",file=sys.stderr)


def xstr(s: str|None) -> str :
    """Returns str(s) or "" if s is None.

    Args:
        s: input string or None.
        
    Returns:
        str(s) or "" if s is None.        
    """
    return "" if s is None else str(s)

    

class Evaluator(object) :
    """Creates object that calls eval with a given record."""

    evalDetector = re.compile(r'\s*eval\((.*)\)\s*$')
    fieldDetector = re.compile(r'\#(.*)\#$')
    reDetector = re.compile(r"r[\"'](.*)[\"']$")
    evalSplitter = re.compile(r'(\#[^#]+\#)')

    def __init__(self, evalString: str, useFieldTests: bool = True, listAsString: bool = False):
        """Initializer
        
        Args:
            evalString: string of the form eval(...) to deliver to eval(), "eval(" and ")" will be removed.
            useFieldTests: whether to use field tests in field name modification.
            listAsString: whether to convert a list into a single string.
        """

        self.evalString = evalString
        self.useFieldTests = useFieldTests
        self.listAsString = listAsString

        tokenList = [token for token in re.split(Evaluator.evalSplitter, evalString) if token != "" and token != None]
        self.fieldTests = {}
        self.requiredFields = []
        finalTokenList = []
        regexCount = 1
        for token in tokenList:
            if reMatch := re.match(Evaluator.fieldDetector, token):
                fieldString = reMatch.group(1)
                if reMatch := re.match(Evaluator.reDetector, fieldString):
                    fieldString = "REGEX" + str(regexCount)
                    regexCount += 1
                    finalTokenList.append(fieldString)
                    self.fieldTests[fieldString] = re.compile(reMatch.group(1))
                else:
                    finalTokenList.append(fieldString.replace("%", "_PERCENT_"))
                    self.requiredFields.append(fieldString)
            else:
                finalTokenList.append(token)

        if not useFieldTests:
            self.requiredFields.extend(self.fieldTests.keys())

        self.code = compile("".join(finalTokenList), self.evalString, "eval")

    def evaluate(self, record: dict) -> str|list:
        """Return eval results for the given record.
        
        Args:
            record: record from TagParser.extraction.
            
        Returns:
            The results from eval() with the record's contents.
        """
        restricted = { field.replace("%","_PERCENT_") : record[field] for field in self.requiredFields }
        if self.useFieldTests and self.fieldTests:
            restricted.update({  [(fieldName, value) for field, value in record.items() if re.search(fieldTest,field)][0] for fieldName, fieldTest in self.fieldTests.items() })

        value = eval(self.code,restricted)
        if type(value) == list:
            if self.listAsString:
                return ";".join(value)
            else:
                return value
        else:
            return xstr(eval(self.code,restricted))

    def hasRequiredFields(self, record: dict) -> bool:
        """Returns whether the record has all required fields.

        Args:
            record: record from TagParser.extraction.
            
        Returns:
            True if the record has all required fiels, False otherwise.
        """
        return all(field in record for field in self.requiredFields) and ( not self.useFieldTests or not self.fieldTests or \
               all([ len([(fieldName, value) for field, value in record.items() if re.search(fieldTest,field)]) == 1 for fieldName, fieldTest in self.fieldTests.items() ]) )

    @staticmethod
    def isEvalString(evalString: str) -> re.Match|None:
        """Tests whether the evalString is of the form r"^eval(...)$"

        Args:
            evalString: a string to determine whether or not it is of the eval variety.
            
        Returns:
            An re.Match object if the evalString is indeed an eval string, or None if it is not.
        """
        return re.match(Evaluator.evalDetector, evalString)

class Operand(object) :
    """Class of objects that create string operands for concatenation operations."""
    def __init__(self, value: str|int) :
        """Initializer

        Args:
            value: a string or int that represents the value of the operand.
        """
        self.value = value
    
    def __call__(self, record: dict, row: pandas.core.series.Series) :
        """Passes, exists to be overridden.

        Args:
            record: record from TagParser.extraction.
            row: pandas Series that is a row from metadata being parsed.
        """
        pass
    
class LiteralOperand(Operand) :
    """Represents string literal operands."""
    def __call__(self, record: dict, row: pandas.core.series.Series) -> str:
        """Returns string value.

        Args:
            record: record from TagParser.extraction.
            row: pandas Series that is a row from metadata being parsed.
            
        Returns:
            String value of the operand.
        """
        return self.value

class VariableOperand(Operand) :
    """Represents #table.record%attribute variable operands."""
    def __call__(self, record: dict, row: pandas.core.series.Series) -> str:
        """Returns record field value.

        Args:
            record: record from TagParser.extraction.
            row: pandas Series that is a row from metadata being parsed.
            
        Returns:
            The value of the record's field where field is the operand's value.
        """
        return record[self.value]

class ColumnOperand(Operand) :
    """Represents specific worksheet cells in a given column as operands."""
    def __call__(self, record: dict, row: pandas.core.series.Series) -> str:
        """Rerurns column value in the given row.

        Args:
            record: record from TagParser.extraction.
            row: pandas Series that is a row from metadata being parsed.
            
        Returns:
            xstr(row.iloc[self.value]).strip() of a column in the row. The column returned is the index based on the operand's value.
        """
        return xstr(row.iloc[self.value]).strip()

class FieldMaker(object) :
    """Creates objects that convert specific information from a worksheet row into a field via concatenation of a list of operands."""
    def __init__(self, field: str) :
        """Initializer

        Args:
            field: name of a field in a record from TagParser.extraction.
        """
        self.field = field
        self.operands = []

    def create(self, record: dict, row: pandas.core.series.Series) -> str:
        """Creates field-value and adds to record using row and record.

        Args:
            record: record from TagParser.extraction.
            row: pandas Series that is a row from metadata being parsed.
            
        Returns:
            Value created by applying all operands in self.operands and written into record[self.field].
        """
        value = ""
        for operand in self.operands :
            value += operand(record, row)

        record[self.field] = value

        return value

    def shallowClone(self) -> FieldMaker:
        """Returns clone with shallow copy of operands.

        Returns:
            A copy of self, but with a shallow copy of operands.
        """
        clone = FieldMaker(self.field)
        clone.operands = self.operands
        return clone


class ListFieldMaker(FieldMaker) :
    """Creates objects that convert specific information from a worksheet row into a list field via appending of a list of operands."""

    def create(self, record: dict, row: pandas.core.series.Series) -> list:
        """Creates field-value and adds to record using PARAMETERS row and record.

        Args:
            record: record from TagParser.extraction.
            row: pandas Series that is a row from metadata being parsed.
            
        Returns:
            Value created by applying all operands in self.operands and written into record[self.field].
        """
        value = []
        for operand in self.operands :
            if isinstance(operand, ColumnOperand) : # split column operands into separate values.
                ## If the list field contains semicolons use it to split instead of commas.
                if re.match(r".*;.*", operand(record, row)):
                    value.extend(operand(record, row).strip(";").split(";"))
                else:
                    value.extend(operand(record, row).strip(",").split(","))
            else :
                value.append(operand(record, row))

        if self.field in record :
            record[self.field].extend(value)
        else :
            record[self.field] = value

        return value

    ## Currently I don't think this can be called from the CLI. 
    ## The only time shallowClone is called is when a child is created and that is 
    ## only ever called on a FieldMaker type, not ListFieldMaker.
    def shallowClone(self) -> ListFieldMaker:
        """Returns clone with shallow copy of operands.

        Returns:
            A copy of self, but with a shallow copy of operands.
        """
        clone = ListFieldMaker(self.field)
        clone.operands = self.operands
        return clone


class RecordMaker(object) :
    """Creates objects that convert worksheet rows into records for specific tables."""
    def __init__(self) :
        """Initializer"""
        self.table = ""
        self.fieldMakers = []

    @staticmethod
    def child(example: RecordMaker, table: str, parentIDIndex: int) -> RecordMaker:
        """Returns child object derived from a example object.
        
        Args:
            example: RecordMaker with global literal fields.
            table: table where the child record will go.
            parentIDIndex: column index for parentID of the child record.
            
        Returns:
            RecordMaker to make a new child record.
        """
        child = RecordMaker()
        child.table = table
        child.fieldMakers = [ maker.shallowClone() for maker in example.fieldMakers ]
        for maker in child.fieldMakers :
            if (reMatch := re.match('(\w*)\.(.*)$', maker.field)) and reMatch.group(1) == table :
                maker.field = reMatch.group(2)
        child.addField(table,"parent_id")
        child.addColumnOperand(parentIDIndex)
        
        return child

    def create(self, row: pandas.core.series.Series) -> tuple[str,dict]:
        """Returns record created from given row.

        Args:
            row: pandas Series that is a row from metadata being parsed.
            
        Returns:
            The table string and created record in a tuple.
        """
        record = {}
        for fieldMaker in self.fieldMakers :
            fieldMaker.create(record, row) 
        return self.table, record

    def addField(self, table: str, field: str, fieldMakerClass: FieldMaker|ListFieldMaker = FieldMaker):
        """Creates and adds new FieldMaker object.

        Args:
            table: table name to add.
            field: field name to add.
            fieldMakerClass: which type of FieldMaker to add to self.fieldMakers.
        """
        if self.table == "" :
            self.table = table
        field = self.properField(table,field)
        self.fieldMakers.append(fieldMakerClass(field))

    def addGlobalField(self, table: str, field: str, literal: str, fieldMakerClass: FieldMaker|ListFieldMaker = FieldMaker) :
        """Creates and adds new FieldMaker with literal operand that will be used as global fields for all records created from a row.

        Args:
            table: table name to add.
            field: field name to add.
            literal: value of the field to be added.
            fieldMakerClass: which type of FieldMaker to add to self.fieldMakers.
        """
        field = table + "." + field
        self.fieldMakers.append(fieldMakerClass(field))
        self.fieldMakers[-1].operands.append(LiteralOperand(literal))

    def addVariableOperand(self, table: str, field: str) :
        """Add field as a variable operand to the last FieldMaker.

        Args:
            table: table name to add.
            field: field name to add.
        """
        field = self.properField(table,field)
        self.fieldMakers[-1].operands.append(VariableOperand(field))
    
    def addLiteralOperand(self, literal: str) :
        """Add literal as an operand to the last FieldMaker.

        Args:
            literal: value to append.
        """
        self.fieldMakers[-1].operands.append(LiteralOperand(literal))

    def addColumnOperand(self, columnIndex: int) :
        """Add columnIndex as a column variable operand to the last FieldMaker.

        Args:
            columnIndex: column number to add.
        """
        self.fieldMakers[-1].operands.append(ColumnOperand(columnIndex))

    def isInvalidDuplicateField(self, table: str, field: str, fieldMakerClass: FieldMaker|ListFieldMaker) -> bool:
        """Returns whether a given table.field is an invalid duplicate in the current RecordMaker.

        Args:
            table: table name to look for.
            field: field name to look for.
            fieldMakerClass: uses this type to do the correct checks.
            
        Returns:
            True if table.field is an invalid duplicate, False otherwise.
        """
        field = self.properField(table,field)
        return (fieldMakerClass == FieldMaker and self.hasShortField(field)) or len([ index for index in range(len(self.fieldMakers)) if self.fieldMakers[index].field == field and not isinstance(self.fieldMakers[index], ListFieldMaker) ]) > 0

    def hasField(self, table: str, field: str, offset: int =0) -> bool:
        """Returns whether a given table.field exists in the current RecordMaker.

        Args:
            table: table name to look for.
            field: field name to look for.
            offset: offset from end to stop looking for #table.field.
        
        Returns:
            True if table.field exists, False otherwise.
        """
        field = self.properField(table,field)
        return self.hasShortField(field, offset) 

    def hasShortField(self, field: str, offset: int =0) -> bool:
        """Returns whether a given field exists in the current RecordMaker.

        Args:
            field: field name to look for.
            offset: offset from end to stop looking for #table.field.
            
        Returns:
            True if field exists, False otherwise.
        """
        return len([ index for index in range(len(self.fieldMakers)-offset) if self.fieldMakers[index].field == field ]) > 0 

    def isLastField(self, table: str, field: str) -> bool:
        """Returns whether the last FieldMaker is for table.field.

        Args:
            table: table name to look for.
            field: field name to look for.
        
        Returns:
            True if the last FieldMaker is for table.field, False otherwise.
        """
        field = self.properField(table,field)
        return self.fieldMakers[-1].field == field

    def hasValidID(self) -> bool :
        """Returns whether there is a valid id field.

        Returns:
            True if there is a valid id field, False otherwise.
        """
        return self.hasShortField("id") and type(self.shortField("id").operands[0]) is ColumnOperand and not type(self.shortField("id")) == ListFieldMaker

    def properField(self, table: str, field: str) -> str:
        """Returns proper field name based on given table and field and internal self.table.

        Args:
            table: table name to check against internal table name and build proper field name with.
            field: field name to build proper field name with.
            
        Returns:
            "table.field" with the appropriate table.
        """
        if table != self.table :
            field = table + "." + field
        return field

    ## This is currently never called anywhere, so cannot be tested through the CLI.
    def field(self, table: str, field: str) -> FieldMaker|ListFieldMaker|None:
        """Returns FieldMaker for table.field.

        Args:
            table: table name to look for FieldMaker.
            field: field name to look for FieldMaker.
            
        Returns:
            The FieldMaker for the table.field.
        """
        field = self.properField(table,field)
        return self.shortField(field)

    def shortField(self, field: str) -> FieldMaker|ListFieldMaker|None:
        """Returns FieldMaker for field.

        Args:
            field: field name to look for FieldMaker.
            
        Returns:
            The FieldMaker for the field.
        """
        for fieldMaker in self.fieldMakers :
            if fieldMaker.field == field :
                return fieldMaker
    

class TagParserError(Exception):
    """Exception class for errors thrown by TagParser."""
    def __init__(self, message: str, fileName: str, sheetName: str, rowIndex: int, columnIndex: int, endMessage: str =""):
        """
        Args:
            message: start of the message for the exception.
            fileName: the file name where the exception happened.
            sheetName: the sheet name in the Excel file where the exception happened.
            rowIndex: the row index in the tabular file where the exception happened.
            columnIndex: the column index in the tabular file where the exception happened.
            endMessage: the optional end of the message for the exception.
        """
        if re.search(r"\.xls[xm]?$", fileName):
            cellName = TagParserError.columnName(columnIndex) + str(rowIndex+1)
        else:
            cellName = "col " + str(columnIndex+1) + ", row " + str(rowIndex+1)

        self.value = message + " at cell \"" + fileName + ":" + sheetName + "[" + cellName + "]\"" + endMessage
        
    @staticmethod
    def columnName(columnIndex: int) -> str:
        """Returns Excel-style column name for columnIndex (integer).

        Args:
            columnIndex: index of the column in the spreadsheet.
            
        Returns:
            If columnIndex is less than 0 return ":", else return the capital letter(s) of the Excel colummn, Ex: columnIndex = 3 returns "D"
        """
        if columnIndex < 0 :
            return ":"
        dividend = columnIndex+1
        name = ""
        while dividend > 0 :
            modulo = (dividend - 1 ) % 26
            name = chr(65+modulo) + name
            dividend = int((dividend - modulo) / 26)
        return name
        
    def __str__(self) :
        return repr(self.value)

    
class TagParser(object):
    """Creates parser objects that convert tagged .xlsx worksheets into nested dictionary structures for metadata capture."""
    
    def __init__(self):
        self.extraction = {}
        self.tablesAndFieldsToTrack = {}
        self.tableRecordsToAddTo = {}
        self.trackedFieldsDict = {}

    reDetector = re.compile(r"r[\"'](.*)[\"']$")        

    @staticmethod
    def _isEmptyRow(row: pandas.core.series.Series) -> bool:
        """Returns True if row is empty.

        Args:
            row: row from a tabular file.
            
        Returns:
            True if each value in row is the empty string after stripping, False otherwise.
        """
        for cell in row :
            if xstr(cell).strip() != "" :
                return False
        
        return True

    def _determineTableField(self, params: tuple[str]|tuple[str,str]|tuple[str,str,str]) -> tuple[str,str]:
        """Returns table and field based on params tuple and last table and field set.
        
        If table is in params use that for table, else use self.lastTable.
        If field is in params use that for field, else use self.lastField.
        If attribute is in params add that to field.

        Args:
            params: (attribute) or (table, field) or (table, field, attribute), generally the groups from a regular expression.
            
        Returns:
            (table, field) or (table, field%attribute)
            
        Raises:
            TagParserError: if the table or field name are undefined.
        """
        if len(params) > 1 :
            table = params[0]
            field = params[1]
            if len(params) > 2 :
                attribute = params[2]
            else :
                attribute = ""
        else :
            table = ""
            field = ""
            attribute = params[0]
            
        if table == "" :
            if self.lastTable == "" :
                raise TagParserError("Undefined table name", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
            table = self.lastTable
        else :
            self.lastTable = table
        
        if field == "" :
            if self.lastField == "" :
                ## There does not appear to be a way to get to this error from the CLI.
                ## Any tag missing a field triggers a different error.
                raise TagParserError("Undefined field name", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
            field = self.lastField
        else :
            self.lastField = field

        if attribute != "" :
            return table, field + "%" + attribute
        
        return table, field


    cellSplitter = re.compile(r'([*=+;,]|\"[^\"]*\"|#\w+\s*\w+\.(?:\w+\s*\w+%\w+\s*\w+|\w+\s*\w+))|\s+')
    stringExtractor = re.compile(r'\"(.*)\"$')
    operatorDetector = re.compile(r'[=+]')
    wordDetector = re.compile(r'\w+')
    wordOnlyDetector = re.compile('\w+$')
    tagDetector = re.compile(r'#')
    childDetector = re.compile(r'#.*\%child')
    childFieldDetector = re.compile(r'#(\w*)\%child\.(\w+)$')
    childFieldAttributeDetector = re.compile(r'#(\w*)\%child\.(\w+)\%(\w+)$')
    emptyChildDetector = re.compile(r'#(\w*)\%child$')
    tableFieldAttributeDetector = re.compile(r'#(\w*)\.(\w+)\%(\w+)$')
    tableFieldDetector = re.compile(r'#([\w\s-]*)\.(\w+|\w+\.id)$')
    attributeDetector = re.compile('#\%(\w+)$')
    trackFieldDetector = re.compile(r'#(\w*)\%track$')
    untrackFieldDetector = re.compile(r'#(\w*)\%untrack$')
    def _parseHeaderCell(self, recordMakers: list[RecordMaker], cellString: str, childWithoutID: bool) -> bool:
        """Parses header cell and return the current state of ID inclusion of current child record.
        
        Parse cellString and modify recordMakers so they can be used later to create records.
        
        Args:
            recordMakers: list of recordMaker objects.
            cellString: contents of the header cell.
            childWithoutID: whether the current child record has an id or not.
            
        Returns:
            True if the current child record does not have an id, False if it does.
            
        Raises:
            TagParserError: If any of the tags are misformed an error will be raised.
        """
        if self.columnIndex == 0 and (re.search(TagParser.childDetector, cellString)) :
            raise TagParserError("#.%child tag not allowed in first column", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
        if self.columnIndex != 0 and re.search('#tags', cellString) :
            raise TagParserError("#tags only allowed in first column", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
            
        tokens = [ x for x in re.split(TagParser.cellSplitter, cellString) if x != "" and x != None ]
        tokens = [ x if (reMatch := re.match(TagParser.stringExtractor, x)) == None else reMatch.group(1) for x in tokens ]
        
        assignment = False
        fieldMakerClass = FieldMaker
        while len(tokens) > 0 :
            token = tokens.pop(0)
            
            # check for common errors
            ## This cannot be triggered from the CLI with #tags in assignment. It will hit another error about #tags only being on the first column first.
            if assignment and (token == '#table' or token == "#tags" or re.match(TagParser.childDetector, token)) :
                raise TagParserError("#table, #tags, or #%child tags  in assignment", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
            if len(tokens) > 0 and re.match(TagParser.operatorDetector,token) and re.match(TagParser.operatorDetector,tokens[0]) :
                raise TagParserError("tandem +/= operators without intervening operand", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
            if len(tokens) > 0 and re.search(TagParser.wordDetector,token) and re.search(TagParser.wordDetector,tokens[0]) :
                raise TagParserError("tandem literal/tag without intervening operator", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
            if re.match(TagParser.operatorDetector,token) and ( len(tokens) == 0 or tokens[0] == ';' ) :
                raise TagParserError("+/= operator without second operand", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
            if token == '+' and not assignment :
                raise TagParserError("+ operator not in an assignment", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
            if token == ',' and (not assignment or fieldMakerClass != ListFieldMaker) :
                raise TagParserError(", operator not in a list field assignment", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
            if token == '=' and assignment :
                raise TagParserError("second = operator in an assignment", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
            if token == '*' and (assignment or len(tokens) == 0 or not re.match(TagParser.tagDetector,tokens[0]) ) :
                raise TagParserError("* operator is not at the beginning of a field tag", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)

                        
            if token == '#tags' :
                pass
            elif token == '#table' :
                if len(tokens) < 2 or tokens[0] != '=' or not re.match(TagParser.wordOnlyDetector,tokens[1]) :
                    raise TagParserError("#table tag without assignment", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                tokens.pop(0)
                self.lastTable = tokens.pop(0)
            elif re.match(TagParser.emptyChildDetector, token) :
                raise TagParserError("child tag with no field", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
            elif (reMatch := re.match(TagParser.childFieldAttributeDetector, token)) or (reMatch := re.match(TagParser.childFieldDetector, token)) :  # #table%child.field.attribute combinations
                if not recordMakers[1].hasValidID() :
                    raise TagParserError("no id field in parent record", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                table, field = self._determineTableField(reMatch.groups())
                if field != "id" and len(tokens) > 0 and tokens[0] == "=" :
                    raise TagParserError("no assignment allowed with explicit child field", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                if field != "id" and childWithoutID :
                    raise TagParserError("second explicit non-id child field specified", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                if field == "id" and childWithoutID and table != recordMakers[-1].table :
                    raise TagParserError("second explicit non-id child field specified", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                if not childWithoutID :
                    recordMakers.append(RecordMaker.child(recordMakers[0], table, recordMakers[1].shortField("id").operands[0].value))
                ## As far as I can tell this error is impossible to reach from the CLI. Trying to create duplicate fields will lead to triggering one of 
                ## second explicit errors above.
                if recordMakers[-1].isInvalidDuplicateField(table, field, fieldMakerClass) :
                    raise TagParserError(str("field \"") + field + "\" specified twice in " + table + " record", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                recordMakers[-1].addField(table, field, fieldMakerClass)
                if field == "id" :
                    childWithoutID = False
                    if len(tokens) > 0 and tokens[0] == "=" :
                        recordMakers[-1].addColumnOperand(recordMakers[1].shortField("id").operands[0].value)
                    else :                                
                        recordMakers[-1].addColumnOperand(self.columnIndex)
                else :
                    childWithoutID = True
                    recordMakers[-1].addColumnOperand(self.columnIndex)                                
            elif (reMatch := re.match(TagParser.trackFieldDetector, token)) :
                if len(tokens) < 2 or tokens[0] != "=":
                    raise TagParserError("Incorrectly formatted track tag, \"=\" must follow \"track\" and \"table.field\" or \"table.field%attribute\" must follow \"=\"", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                ## Munch the =.
                tokens.pop(0)
                nextToken = tokens.pop(0)
                while True:
                    if not re.match(r"(\w+\.\w+)|(\w+\.\w+%\w+)", nextToken):
                        raise TagParserError("Incorrectly formatted track tag, the field or attribute to be tracked is malformed, must be \"table.field\" or \"table.field%attribute\"", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                    if reMatch.groups()[0] == "":
                        tableToAddTo = self.lastTable
                    else:
                        tableToAddTo = reMatch.groups()[0]
                        self.lastTable = tableToAddTo
                    split = nextToken.split(".")
                    fieldTable = split[0]
                    field = split[1]
                    if fieldTable in self.tablesAndFieldsToTrack:
                        self.tablesAndFieldsToTrack[fieldTable].add(field)
                    else:
                        self.tablesAndFieldsToTrack[fieldTable] = set([field])
                    if tableToAddTo in self.tableRecordsToAddTo:
                        self.tableRecordsToAddTo[tableToAddTo].add(nextToken)
                    else:
                        self.tableRecordsToAddTo[tableToAddTo] = set([nextToken])
                    if nextToken not in self.trackedFieldsDict:
                        self.trackedFieldsDict[nextToken] = ""
                    if tokens:
                        nextToken = tokens.pop(0)
                        if nextToken == ",":
                            nextToken = tokens.pop(0)
                        elif nextToken == ";":
                            break
                    else:
                        break
            elif (reMatch := re.match(TagParser.untrackFieldDetector, token)) :
                if len(tokens) < 2 or tokens[0] != "=":
                    raise TagParserError("Incorrectly formatted untrack tag, \"=\" must follow \"track\" and \"table.field\" or \"table.field%attribute\" must follow \"=\"", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                ## Munch the =.
                tokens.pop(0)
                nextToken = tokens.pop(0)
                while True:
                    if not re.match(r"(\w+\.\w+)|(\w+\.\w+%\w+)", nextToken):
                        raise TagParserError("Incorrectly formatted untrack tag, the field or attribute to be tracked is malformed, must be \"table.field\" or \"table.field%attribute\"", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                    if reMatch.groups()[0] == "":
                        tableToAddTo = self.lastTable
                    else:
                        tableToAddTo = reMatch.groups()[0]
                        self.lastTable = tableToAddTo
                    split = nextToken.split(".")
                    fieldTable = split[0]
                    field = split[1]
                    if tableToAddTo in self.tableRecordsToAddTo:
                        self.tableRecordsToAddTo[tableToAddTo].discard(nextToken)
                        if len(self.tableRecordsToAddTo[tableToAddTo]) == 0:
                            del self.tableRecordsToAddTo[tableToAddTo]
                    tableAndFieldInOtherTables = False
                    for table, fields in self.tableRecordsToAddTo.items():
                        if nextToken in fields:
                            tableAndFieldInOtherTables = True
                            break
                    if not tableAndFieldInOtherTables:
                        del self.trackedFieldsDict[nextToken]
                        self.tablesAndFieldsToTrack[fieldTable].discard(field)
                        if len(self.tablesAndFieldsToTrack[fieldTable]) == 0:
                            del self.tablesAndFieldsToTrack[fieldTable]
                    if tokens:
                        nextToken = tokens.pop(0)
                        if nextToken == ",":
                            nextToken = tokens.pop(0)
                        elif nextToken == ";":
                            break
                    else:
                        break
            elif (reMatch := re.match(TagParser.tableFieldAttributeDetector, token)) or (reMatch := re.match(TagParser.tableFieldDetector, token)) or (reMatch := re.match(TagParser.attributeDetector, token)) : #table.field.attribute combinations
                table, field = self._determineTableField(reMatch.groups())
                currentTable = recordMakers[-1].table
                if currentTable != "" and currentTable != table:
                    raise TagParserError("second table specified after first table, if trying to specify an id to another table use #.table.id", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                if self.columnIndex == 0 :
                    if len(tokens) < 2 or tokens[0] != '=' or re.match(TagParser.tagDetector, tokens[1]) :
                        raise TagParserError("tags without assignment in first column", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                    tokens.pop(0)
                    recordMakers[0].addGlobalField(table, field, tokens.pop(0))                     
                elif assignment :
                    if not recordMakers[-1].hasField(table, field, 1) or recordMakers[-1].isLastField(table,field) :
                        raise TagParserError("the field or attribute value used for assignment is not previously defined in record", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                    recordMakers[-1].addVariableOperand(table, field)
                else :
                    if recordMakers[-1].isInvalidDuplicateField(table, field, fieldMakerClass) :
                        raise TagParserError(str("field \"") + field + "\" specified twice in " + table + " record", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                    recordMakers[-1].addField(table, field, fieldMakerClass)
                    if len(tokens) == 0 or tokens[0] == ';' :
                        recordMakers[-1].addColumnOperand(self.columnIndex)                
            elif token == "=" :
                assignment = True
            elif token == "*" :
                fieldMakerClass = ListFieldMaker
            elif token == "+" :
                ## This check is done above, but this elif needs to be here to munch the + operator so it isn't added as a LiteralOperand.
                if not assignment :
                    raise TagParserError("+ operator not in an assignment", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
            elif token == "," :
                ## This check is done above, but this elif needs to be here to munch the , operator so it isn't added as a LiteralOperand.
                if not assignment or fieldMakerClass != ListFieldMaker:
                    raise TagParserError(", operator not in a list field assignment", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
            elif token == ";" :
                assignment = False
                fieldMakerClass = FieldMaker
            elif re.match('#',token) : # malformed tags
                raise TagParserError("malformed or unrecognized tag \"" + token + "\"", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
            elif assignment : # literals
                recordMakers[-1].addLiteralOperand(token)
            else :
                raise TagParserError("bad token \"" + token + "\"", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                
        return childWithoutID 


    def _parseHeaderRow(self, row: pandas.core.series.Series) -> list[RecordMaker]:
        """Parses header row and returns a list of RecordMakers.
        
        Args:
            row: header row from metadata file.
            
        Returns:
            A list of RecordMakers to be used to create records.
            
        Raises:
            TagParserError: Will raise an error if a child record does not have an id.
        """
        self.lastTable = ""
        self.lastField = ""
        
        recordMakers = [ RecordMaker(), RecordMaker() ]
        childWithoutID = False
        for self.columnIndex in range(0, len(row)) :
            cellString = xstr(row.iloc[self.columnIndex]).strip()
            if re.match('[*]?#', cellString) :
                childWithoutID = self._parseHeaderCell(recordMakers, cellString, childWithoutID) 
        
        self.columnIndex = -1

        if childWithoutID :
            raise TagParserError("#.child record without id", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
        
        recordMakers.pop(0)    # pop example RecordMaker used to hold global literals.    
        return recordMakers

    
    def _parseRow(self, recordMakers: list[RecordMaker], row: pandas.core.series.Series):
        """Create new records and add them to the nested extraction dictionary.
        
        Loop through the RecordMakers in recordMaker and add records to self.extraction 
        based on the values in row.
        
        Args:
            recordMakers: RecordMakers created from parsing a header row.
            row: row of data from a metadata file.
        """
        for recordMaker in recordMakers :
            if not recordMaker.hasValidID():
                return
            table,record = recordMaker.create(row)
            if not table in self.extraction :
                self.extraction[table] = {}

            ## Keep track of ids in specified tables.
            if table in self.tablesAndFieldsToTrack:
                for field in self.tablesAndFieldsToTrack[table]:
                    if field in record:
                        self.trackedFieldsDict[table + "." + field] = record[field]
                        
            ## Copy tracked fields into records if applicable.
            if table in self.tableRecordsToAddTo:
                for fieldToAdd in self.tableRecordsToAddTo[table]:
                    if not fieldToAdd in record and self.trackedFieldsDict[fieldToAdd] != "":
                        record[fieldToAdd] = self.trackedFieldsDict[fieldToAdd]
                    elif fieldToAdd in record:
                        self.trackedFieldsDict[fieldToAdd] = record[fieldToAdd]
            
            
            if not record["id"] in self.extraction[table] :
                self.extraction[table][record["id"]] = record
            else :
                for key in record :
                    if key == "id" :
                        pass
                    ## For when the same record is on multiple tables in the tabular file.
                    elif not key in self.extraction[table][record["id"]] :
                        self.extraction[table][record["id"]][key] = record[key]
                    elif isinstance(self.extraction[table][record["id"]][key], list) :
                        if isinstance(record[key], list):
                            self.extraction[table][record["id"]][key] = self.extraction[table][record["id"]][key] + record[key]
                        else:
                            self.extraction[table][record["id"]][key].append(record[key])
                    elif self.extraction[table][record["id"]][key] != record[key] :
                        self.extraction[table][record["id"]][key] = [ self.extraction[table][record["id"]][key], record[key] ]


    def parseSheet(self, fileName: str, sheetName: str, worksheet: pandas.core.frame.DataFrame):
        """Extracts useful metadata from the worksheet and puts it in the extraction dictionary.
        
        Args:
            fileName: name of the file, used for error messages.
            sheetName: name of the Excel sheet, used for error messages.
            worksheet: the data from the file name and sheet name.
        """
        self.lastTable = ""
        self.lastField = ""
        self.columnIndex = -1
        self.rowIndex = -1
        self.fileName = fileName
        self.sheetName = sheetName

        
        tagRows = worksheet.iloc[:,0].str.match("#tags")
        ignoreRows = worksheet.iloc[:,0].str.match("#ignore")
        emptyRows = (worksheet=="").all(axis=1)
        
        possibleEndOfTagGroupRows = emptyRows | tagRows
        worksheetHeaderRows = worksheet[tagRows]
        endOfTagGroupIndexes = []
        for header_index in worksheetHeaderRows.index:
            endingIndexFound = False
            for index in possibleEndOfTagGroupRows[possibleEndOfTagGroupRows].index:
                if index > header_index:
                    endOfTagGroupIndexes.append(index)
                    endingIndexFound = True
                    break
            if not endingIndexFound:
                endOfTagGroupIndexes.append(possibleEndOfTagGroupRows.index[-1]+1)
            
        for headerRow in range(worksheetHeaderRows.shape[0]):
            headerRowIndex = worksheetHeaderRows.iloc[headerRow,:].name
            self.rowIndex = headerRowIndex
            recordMakers = self._parseHeaderRow(worksheet.loc[headerRowIndex, :])
            ## recordMakers should only ever be either 1 or 2 in size. If 2 then 
            ## it is a child record and the first recordMaker is just making the 
            ## parent record using the child's indicated id.
            ## If there is not validID print a message unless there are no fieldMakers, then assume it is a control flow header row. 
            ## For example a row that just turns tracking on or off.
            if not recordMakers[-1].hasValidID() and recordMakers[-1].fieldMakers and not silent:
                print("Warning: The header row at index " + str(headerRowIndex) + " in the compiled export sheet does not have an \"id\" tag, so it will not be in the JSON output.", file=sys.stderr)
            rowsToParse = [index for index in range(headerRowIndex+1, endOfTagGroupIndexes[headerRow])]
            rowsToParse = ignoreRows.iloc[rowsToParse][~ignoreRows]
            ## If there was a header, but no rows underneath we want to add an empty table.
            if len(rowsToParse) == 0:
                if not recordMakers[0].table in self.extraction :
                    self.extraction[recordMakers[0].table] = {}
            for index in rowsToParse.index:
                self._parseRow(recordMakers, worksheet.loc[index, :])
        
        self.rowIndex = -1


    @staticmethod
    def loadSheet(fileName: str|TextIO, sheetName: str, removeRegex: str|None = None, isDefaultSearch: bool = False) -> tuple[str,str,pandas.core.frame.DataFrame]|None:
        """Load and return worksheet as a pandas data frame.
        
        Args:
            fileName: filename or sys.stdin to read a csv from stdin.
            sheeName: sheet name for an Excel file, ignored if not an Excel file. Can be a regular expression to search for a sheet.
            removeRegex: a string to pass to DataFrame.replace() to replace characters with an empty string in the dataframe that is read in. 
                         Can be a regex. Set to None to not replace anything.
            isDefaultSearch: whether or not the sheetName is using default values, determines whether to print some messages.
            
        Returns:
            None if the worksheet is empty, else (fileName, sheetName, dataFrame)
            
        Raises:
            Exception: If fileName is invalid.
        """
        isGoogleSheetsFile = TagParser.isGoogleSheetsFile(fileName)
        
        if (isinstance(fileName, str) and (reMatch := re.search(r"^(.*\.xls[xm]?)$", fileName))) or isGoogleSheetsFile:
            if os.path.isfile(fileName) or isGoogleSheetsFile:
                try:
                    workbook = pandas.ExcelFile(fileName)
                except urllib.error.HTTPError:
                    print("The Google Sheets file \"" + fileName + "\" does not exist or the URL is malformed.", file=sys.stderr)
                    return None
                
                ## Convert the sheetname to a regular expression pattern so users can specify a sheetname using a regular expression.
                if re.match(TagParser.reDetector, sheetName):
                    sheetDetector = re.compile(re.match(TagParser.reDetector, sheetName)[1])
                else:
                    sheetDetector = re.compile("^" + re.escape(sheetName) + "$")
                
                for sheetName in workbook.sheet_names:
                    if re.search(sheetDetector, sheetName) != None:
                        dataFrame = pandas.read_excel(workbook, sheetName, header=None, index_col=None, nrows=0)
                        converters = {column:str for column in dataFrame.columns}
                        dataFrame = pandas.read_excel(workbook, sheetName, header=None, index_col=None, converters=converters)
                        if len(dataFrame) == 0:
                            if isGoogleSheetsFile:
                                print("There is no data in the sheet, " + sheetName + \
                                      ", of the Google Sheets file \"" + fileName + "\".", file=sys.stderr)
                            else:
                                print("There is no data in worksheet \"" + fileName + ":" + sheetName + "\".", file=sys.stderr)
                            return None
                        else:
                            ## Empty cells are read in as nan by default, replace with empty string.
                            dataFrame = dataFrame.fillna("")
                            if removeRegex:
                                dataFrame.replace(removeRegex, "", regex=True, inplace=True)
                            return (fileName, sheetName, dataFrame)
                if not isDefaultSearch:
                    print("r'" + sheetDetector.pattern + "' did not match any sheets in \"" + fileName + "\".", file=sys.stderr)
            else:
                print("Excel workbook \"" + reMatch.group(1) + "\" does not exist.", file=sys.stderr)
        elif not isinstance(fileName, str) or re.search(r"\.csv$", fileName):
            if not isinstance(fileName, str) or pathlib.Path(fileName).exists():
                try:
                    dataFrame = pandas.read_csv(fileName, header=None, index_col=None, dtype=str)
                except pandas.errors.EmptyDataError:
                    print("There is no data in csv file \"" + fileName + "\".", file=sys.stderr)
                else:
                    ## I don't think there is a way to read in a csv file with no length. All my attempts resulted in an error.
                    ## Thus this is not testable from the CLI.
                    if len(dataFrame) == 0:
                        print("There is no data in csv file \"" + fileName + "\".", file=sys.stderr)
                    else:
                        dataFrame = dataFrame.fillna("") # Empty cells are read in as nan by default. Therefore replace with empty string.
                        if removeRegex:
                            dataFrame.replace(removeRegex, "", regex=True, inplace=True)
                        sheetName = "" if not sheetName else sheetName
                        return (fileName, sheetName, dataFrame)
            else:
                print("The csv file \"" + fileName + "\" does not exist.", file=sys.stderr)
        else:
            raise Exception("Invalid worksheet identifier \"" + fileName + "\" passed into function.")

        return None


    @staticmethod
    def hasFileExtension(string: str) -> bool:
        """Tests whether the string has a file extension.

        Args:
            string: string to test.
            
        Returns:
            True if .xls, .xlsx, .xlsm, .csv, or .json is in string, False otherwise.
        """
        return ".xls" in string or ".xlsx" in string or ".xlsm" in string or ".csv" in string or ".json" in string
    
    @staticmethod
    def isGoogleSheetsFile(string: str) -> bool:
        """Tests whether the string is a Google Sheets URL.

        Args:
            string: string to test.
            
        Returns:
            True if docs.google.com/spreadsheets/d/ is in string, False otherwise.
        """
        return True if isinstance(string, str) and "docs.google.com/spreadsheets/d/" in string else False

    def readMetadata(self, metadataSource: str, automationSource: str, automateDefaulted: bool, modificationSource: str, modifyDefaulted: bool, removeRegex: str|None, saveExtension: str =None):
        """Reads metadata from source.
        
        Args:
            metadataSource: file path to metadata file with possibly a sheetname if appropriate.
            automationSource: file path to automation file or a sheetname.
            automateDefaulted: whether the automation source is the default value or not, passed to readDirectives for message printing.
            modificationSource: file path to modification file or a sheetname.
            modificationDefaulted: whether the modification source is the default value or not, passed to readDirectives for message printing.
            removeRegex: a string to pass to DataFrame.replace() to replace characters with an empty string in the dataframe that is read in. 
                         Can be a regex. Set to None to not replace anything. Passed to loadSheet and readDirectives.
            saveExtension: if "csv" saves the export as a csv file, else saves it as an Excel file.
        """
        ## If automation source is just a sheet name then see if metadata source is an Excel or Google Sheets file.
        if not TagParser.hasFileExtension(automationSource) and \
           not TagParser.isGoogleSheetsFile(automationSource):
               if (reMatch := re.search(r"(.*\.xls[xm]?)", metadataSource)):
                   automationFilePath = reMatch.group(1) 
                   automationSheetName = automationSource
               elif (reMatch := re.search(r"docs.google.com/spreadsheets/d/([^/]*)/.*$", metadataSource)):
                   automationFilePath = "https://docs.google.com/spreadsheets/d/" + reMatch.group(1) + "/export?format=xlsx"
                   automationSheetName = automationSource
               else:
                   automationFilePath = automationSource
                   automationSheetName = None
        elif re.search(r"\.xls[xm]?$", automationSource):
            automationFilePath = automationSource
            automationSheetName = "#automate"
        elif (reMatch := re.search(r"^(.*\.xls[xm]?):(.*)$", automationSource)):
            automationFilePath = reMatch.group(1)
            automationSheetName = reMatch.group(2)
        elif (reMatch := re.search(r"docs.google.com/spreadsheets/d/([^/]*)/[^:]*$", automationSource)):
            automationFilePath = "https://docs.google.com/spreadsheets/d/" + reMatch.group(1) + "/export?format=xlsx"
            automationSheetName = "#automate"
        elif (reMatch := re.search(r"docs.google.com/spreadsheets/d/([^/]*)/.*:(.*)$", automationSource)):
            automationFilePath = "https://docs.google.com/spreadsheets/d/" + reMatch.group(1) + "/export?format=xlsx"
            automationSheetName = reMatch.group(2)
        else:
            automationFilePath = automationSource
            automationSheetName = None
                    
        if not TagParser.hasFileExtension(modificationSource) and \
           not TagParser.isGoogleSheetsFile(modificationSource):
               if (reMatch := re.search(r"(.*\.xls[xm]?)", metadataSource)):
                   modificationFilePath = reMatch.group(1) 
                   modificationSheetName = modificationSource
               elif (reMatch := re.search(r"docs.google.com/spreadsheets/d/([^/]*)/.*$", metadataSource)):
                   modificationFilePath = "https://docs.google.com/spreadsheets/d/" + reMatch.group(1) + "/export?format=xlsx"
                   modificationSheetName = modificationSource
               else:
                   modificationFilePath = modificationSource
                   modificationSheetName = None
        elif re.search(r"\.xls[xm]?$", modificationSource):
            modificationFilePath = modificationSource
            modificationSheetName = "#modify"
        elif (reMatch := re.search(r"^(.*\.xls[xm]?):(.*)$", modificationSource)):
            modificationFilePath = reMatch.group(1)
            modificationSheetName = reMatch.group(2)
        elif (reMatch := re.search(r"docs.google.com/spreadsheets/d/([^/]*)/[^:]*$", modificationSource)):
            modificationFilePath = "https://docs.google.com/spreadsheets/d/" + reMatch.group(1) + "/export?format=xlsx"
            modificationSheetName = "#modify"
        elif (reMatch := re.search(r"docs.google.com/spreadsheets/d/([^/]*)/.*:(.*)$", modificationSource)):
            modificationFilePath = "https://docs.google.com/spreadsheets/d/" + reMatch.group(1) + "/export?format=xlsx"
            modificationSheetName = reMatch.group(2)
        else:
            modificationFilePath = modificationSource
            modificationSheetName = None

        if re.search(r"\.xls[xm]?$", metadataSource):
            metadataFilePath = metadataSource
            metadataSheetName = "#export"
        elif (reMatch := re.search(r"^(.*\.xls[xm]?):(.*)$", metadataSource)):
            metadataFilePath = reMatch.group(1)
            metadataSheetName = reMatch.group(2)
        elif (reMatch := re.search(r"docs.google.com/spreadsheets/d/([^/]*)/[^:]*$", metadataSource)):
            metadataFilePath = "https://docs.google.com/spreadsheets/d/" + reMatch.group(1) + "/export?format=xlsx"
            metadataSheetName = "#export"
        elif (reMatch := re.search(r"docs.google.com/spreadsheets/d/([^/]*)/.*:(.*)$", metadataSource)):
            metadataFilePath = "https://docs.google.com/spreadsheets/d/" + reMatch.group(1) + "/export?format=xlsx"
            metadataSheetName = reMatch.group(2)
        else:
            metadataFilePath = metadataSource
            metadataSheetName = None

        if TagParser.hasFileExtension(automationFilePath) or TagParser.isGoogleSheetsFile(automationFilePath):
            automationDirectives = self.readDirectives(automationFilePath, automationSheetName, "automation", removeRegex, automateDefaulted) 
        else:
            automationDirectives = None
        ## Structure of modificationDirectives: {table_key:{field_key:{comparison_type:{field_value:{directive:{field_key:directive_value}}}}}} 
        ## The directive value is the new value to give the field or regex, regex is a list, assign is a string.
        ## unique is handled by having "-unique" added to comparison type key, so there is "exact-unique" and "exact".
        if TagParser.hasFileExtension(modificationFilePath) or TagParser.isGoogleSheetsFile(modificationFilePath):
            modificationDirectives = self.readDirectives(modificationFilePath, modificationSheetName, "modification", removeRegex, modifyDefaulted) 
        else:
            modificationDirectives = None

        if re.search(r"\.json$", metadataFilePath):
            with open(metadataFilePath, 'r') as jsonFile:
                newMetadata = json.load(jsonFile)
            currentMetadata = self.extraction
            self.extraction = newMetadata
        else:
            currentMetadata = self.extraction
            newMetadata = {}
            self.extraction = newMetadata
            dataFrameTuple = TagParser.loadSheet(metadataFilePath, metadataSheetName, removeRegex=removeRegex)

            if dataFrameTuple:
                dataFrame = self.tagSheet(automationDirectives, dataFrameTuple[2], silent)
                dataFrameTuple = (dataFrameTuple[0], dataFrameTuple[1], dataFrame)

                if saveExtension != None:
                    self.saveSheet(*dataFrameTuple, saveExtension)

                ## Ultimately modifies self.extraction.
                self.parseSheet(*dataFrameTuple)

        if self.extraction:
            self.modify(modificationDirectives)

        newMetadata = self.extraction
        self.extraction = currentMetadata
        self.merge(newMetadata)


    def saveSheet(self, fileName: str, sheetName: str, worksheet: pandas.core.frame.DataFrame, saveExtension: str):
        """Save given worksheet in the given format.
        
        Args:
            fileName: file name or path to save to.
            sheetName: name to give the sheet if saving as Excel.
            worksheet: data to save.
            saveExtension: if "csv" save as csv file, else save as Excel.
        """
        if pathlib.Path(fileName).exists():
            baseName = os.path.basename(fileName)
            fileName = baseName.rsplit(".",1)[0] + "_export."
        elif (reMatch := re.search(r"docs.google.com/spreadsheets/d/([^/]*)/[^:]*$", fileName)):
            fileName = "Google_Sheets_" + reMatch.group(1) + "_export."
        else:
            fileName = "stdin_export."
        if saveExtension == "csv":
            fileName += "csv"
            worksheet.to_csv(fileName, header=False, index=False)
        else:
            fileName += "xlsx"
            with pandas.ExcelWriter(fileName, engine = "xlsxwriter") as writer:
                worksheet.to_excel(writer, sheet_name = sheetName, index=False, header=False)

    headerSplitter = re.compile(r'[+]|(r?\"[^\"]*\"|r?\'[^\']*\')|\s+')
    def tagSheet(self, automationDirectives: dict, worksheet: pandas.core.frame.DataFrame, silent: bool) -> pandas.core.frame.DataFrame:
        """Add tags to the worksheet using the given automation directives.
        
        Args:
            automationDirectives: a dictionary used to place the tags in the appropriate places.
            worksheet: the DataFrame in which to place the tags.
            silent: if True don't print warnings.
            
        Returns:
            The modified worksheet.
        """
        
        worksheet, wasAutomationDirectiveUsed = cythonized_tagSheet.tagSheet(automationDirectives, worksheet.to_numpy(), silent)
        
        for i, directive in enumerate(wasAutomationDirectiveUsed):
            if not directive and not silent:
                print("Warning: Automation directive number " + str(i) + " was never used.", file=sys.stderr)
        
        worksheet = pandas.DataFrame(worksheet)

        return worksheet

    modificationComparisonTypes = [ "exact", "regex", "levenshtein" ]
    matchTypes = ["first", "first-nowarn", "unique", "all"]
    def _parseModificationSheet(self, fileName: str, sheetName: str, worksheet: pandas.core.frame.DataFrame):
        """Extracts modification directives from a given worksheet.

        "modification" : { table : { field :  { "(exact|regex|levenshtein)\-(first|first\-nowarn|unique|all)" :
                          { field_value : { "assign" : { field : value,... }, "append" : { field : value,... }, "prepend" : { field : value,... },
                                            "regex" : { field : regex_pair,... }, "delete" : [ field,... ], "rename" : { old_field : new_field } } } } } }
        
        Loops over worksheet and builds up self.modificationDirectives.
        
        Args:
            fileName: used for printing more descriptive error messages.
            sheetName: used for printing more descriptive error messages.
            worksheet: data used to build the modification directives.
        
        Raises:
            TagParserError: usually raised for malformed tags, but also for other unpredicted errors
            Exception: a catch all in case something unforeseen happens.
        """
        self.columnIndex = -1
        self.rowIndex = -1
        self.fileName = fileName
        self.sheetName = sheetName
        
        aColumn = worksheet.iloc[:, 0]

        parsing = False
        for self.rowIndex in range(len(aColumn)):
            try:
                if re.match('#tags$', xstr(aColumn.iloc[self.rowIndex]).strip()):
                    parsing = True
                    valueIndex = -1
                    comparisonIndex = -1
                    comparisonType = "regex|exact"
                    userSpecifiedType = False
                    matchType = "first"
                    matchIndex = -1
                    assignIndeces = []
                    assignFields = []
                    assignFieldTypes = []
                    appendIndeces = []
                    appendFields = []
                    appendFieldTypes = []
                    prependIndeces = []
                    prependFields = []
                    prependFieldTypes = []
                    regexIndeces = []
                    regexFields = []
                    deletionFields = []
                    renameFieldMap = {}
                    for self.columnIndex in range(1, len(worksheet.iloc[self.rowIndex, :])):
                        cellString = xstr(worksheet.iloc[self.rowIndex, self.columnIndex]).strip()
                        if (reMatch := re.match('\s*#(\w+)\.(\w+|\w+%\w+|\w+\.id)\.value\s*$', cellString)):
                            valueIndex = self.columnIndex
                            table = reMatch.group(1)
                            fieldID = reMatch.group(2)
                        elif (reMatch := re.match('\s*#(\w+)?\.(\w+|\w+%\w+|\w+\.id)\.delete\s*$', cellString)):
                            if valueIndex == -1:
                                raise TagParserError("#table_name.field_name.delete in column before #table_name.field_name.value", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                            if reMatch.group(1) is not None and reMatch.group(1) != table:
                                raise TagParserError("Table name does not match between #table_name.field_name.value and #table_name.field_name.delete modification tags", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                            deletionFields.append(reMatch.group(2))
                        elif (reMatch := re.match('\s*#(\w+)?\.(\w+|\w+%\w+|\w+\.id)\.rename\.(\w+|\w+%\w+|\w+\.id)\s*$', cellString)):
                            if valueIndex == -1:
                                raise TagParserError("#table_name.field_name.rename in column before #table_name.field_name.value", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                            if reMatch.group(1) is not None and reMatch.group(1) != table:
                                raise TagParserError("Table name does not match between #table_name.field_name.value and #table_name.field_name.rename modification tags", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                            if reMatch.group(2) == reMatch.group(3):
                                raise TagParserError("rename modification directive renames the field to the same name", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                            if reMatch.group(2) == "id":
                                raise TagParserError("Not allowed to rename \"id\" fields", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                            renameFieldMap[reMatch.group(2)] = reMatch.group(3)
                        elif (reMatch := re.match('\s*#(\w+)?\.(\w+|\w+%\w+|\w+\.id)\.rename\s*$', cellString)):
                            raise TagParserError("Incorrect rename directive format.  Should be #[table_name].field_name.rename.new_field_name", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                        elif (reMatch := re.match('\s*(\*#|#)(\w+)?\.(\w+)\.assign\s*$', cellString)) or (reMatch := re.match('\s*(#)(\w+)?\.(\w+|\w+%\w+|\w+\.id)\.assign\s*$', cellString)):
                            if valueIndex == -1:
                                raise TagParserError("#table_name.field_name.assign in column before #table_name.field_name.value", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                            if reMatch.group(2) is not None and reMatch.group(2) != table:
                                raise TagParserError("Table name does not match between #table_name.field_name.value and #table_name.field_name.assign modification tags", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                            assignIndeces.append(self.columnIndex)
                            assignFieldTypes.append(reMatch.group(1))
                            assignFields.append(reMatch.group(3))
                        elif (reMatch := re.match('\s*(\*#|#)(\w+)?\.(\w+)\.append\s*$', cellString)) or (reMatch := re.match('\s*(#)(\w+)?\.(\w+|\w+%\w+|\w+\.id)\.append\s*$', cellString)):
                            if valueIndex == -1:
                                raise TagParserError("#table_name.field_name.append in column before #table_name.field_name.value", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                            if reMatch.group(2) is not None and reMatch.group(2) != table:
                                raise TagParserError("Table name does not match between #table_name.field_name.value and #table_name.field_name.append modification tags", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                            appendIndeces.append(self.columnIndex)
                            appendFieldTypes.append(reMatch.group(1))
                            appendFields.append(reMatch.group(3))
                        elif (reMatch := re.match('\s*(\*#|#)(\w+)?\.(\w+)\.prepend\s*$', cellString)) or (reMatch := re.match('\s*(#)(\w+)?\.(\w+|\w+%\w+|\w+\.id)\.prepend\s*$', cellString)):
                            if valueIndex == -1:
                                raise TagParserError("#table_name.field_name.prepend in column before #table_name.field_name.value", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                            if reMatch.group(2) is not None and reMatch.group(2) != table:
                                raise TagParserError("Table name does not match between #table_name.field_name.value and #table_name.field_name.prepend modification tags", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                            prependIndeces.append(self.columnIndex)
                            prependFieldTypes.append(reMatch.group(1))
                            prependFields.append(reMatch.group(3))
                        elif (reMatch := re.match('\s*#(\w+)?\.(\w+)\.regex\s*$', cellString)) or (reMatch := re.match('\s*#(\w+)?\.(\w+|\w+%\w+|\w+\.id)\.regex\s*$', cellString)):
                            if valueIndex == -1:
                                raise TagParserError("#table_name.field_name.regex in column before #table_name.field_name.value", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                            if reMatch.group(1) is not None and reMatch.group(1) != table:
                                raise TagParserError("Table name does not match between #table_name.field_name.value and #table_name.field_name.regex modification tags", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                            regexIndeces.append(self.columnIndex)
                            regexFields.append(reMatch.group(2))
                        elif (reMatch := re.match('\s*#comparison\s*=\s*(exact|regex|regex\|exact|levenshtein)\s*$', cellString)):
                            comparisonType=reMatch.group(1)
                            userSpecifiedType = True
                        elif re.match('\s*#comparison\s*$', cellString):
                            comparisonIndex = self.columnIndex
                        elif re.match('\s*#match\s*=.*$', cellString):
                            if (reMatch := re.match('\s*#match\s*=\s*(first|first-nowarn|unique|all)\s*$', cellString)):
                                matchType = reMatch.group(1)
                            else:
                                badType = re.match('\s*#match\s*=(.*)$', cellString).group(1)
                                raise TagParserError("Unknown match type \"" + badType + "\"", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                        elif re.match('\s*#match\s*$', cellString):
                            matchIndex = self.columnIndex
                        self.columnIndex = -1
                    if valueIndex == -1 or (len(assignIndeces) == 0 and len(appendIndeces) == 0 and len(prependIndeces) == 0 and len(regexIndeces) == 0 and len(deletionFields) == 0 and not renameFieldMap):
                        raise TagParserError("Missing #table_name.field_name.value or #.field_name.assign|append|prepend|regex|delete|rename modification tags", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                    if "id" in deletionFields:
                        raise TagParserError("Not allowed to delete \"id\" fields", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                    if not table in self.modificationDirectives:
                        self.modificationDirectives[table] = {}
                    if not fieldID in self.modificationDirectives[table]:
                        self.modificationDirectives[table][fieldID] = {}
                elif re.match('#ignore$', xstr(aColumn.iloc[self.rowIndex]).strip()):
                    pass
                elif TagParser._isEmptyRow(worksheet.iloc[self.rowIndex, :]):
                    parsing = False
                elif parsing:
                    fieldValue = xstr(worksheet.iloc[self.rowIndex, valueIndex]).strip()
                    if comparisonIndex != -1 and (comparisonString := xstr(worksheet.iloc[self.rowIndex, comparisonIndex]).strip()) in TagParser.modificationComparisonTypes:
                        localComparisonType = comparisonString
                        
                    else:
                        if not userSpecifiedType or comparisonType == "regex|exact":
                            localComparisonType = "regex" if re.match(TagParser.reDetector, fieldValue) else "exact"
                        else:
                            localComparisonType = comparisonType
                    
                    if localComparisonType == "regex" and not re.match(TagParser.reDetector, fieldValue):
                        print(TagParserError("Comparison type is indicated as regex, but comparison value is not a regex", self.fileName, self.sheetName, self.rowIndex, valueIndex, " This modification will be skipped."), file=sys.stderr)
                        # raise TagParserError("Comparison type is indicated as regex, but comparison value is not a regex", self.fileName, self.sheetName, self.rowIndex, valueIndex)
                        continue

                    if matchIndex != -1:
                        matchType = xstr(worksheet.iloc[self.rowIndex, matchIndex]).strip()
                        if matchType not in TagParser.matchTypes:
                            raise TagParserError("Unknown match type \"" + matchType + "\"", self.fileName, self.sheetName, self.rowIndex, matchIndex)
                    localComparisonType += "-" + matchType

                    assignFieldMap = {}
                    for i in range(len(assignIndeces)):
                        assignFieldValue = xstr(worksheet.iloc[self.rowIndex, assignIndeces[i]]).strip()
                        if re.match(r"\*", assignFieldTypes[i]) and not Evaluator.isEvalString(assignFieldValue):
                            ## If the list field contains semicolons use it to split instead of commas.
                            if re.match(r".*;.*", assignFieldValue):
                                assignFieldValue = assignFieldValue.strip(";").split(";")
                            else:
                                assignFieldValue = assignFieldValue.strip(",").split(",")

                        assignFieldMap[assignFields[i]] = assignFieldValue

                    appendFieldMap = {}
                    for i in range(len(appendIndeces)):
                        appendFieldValue = xstr(worksheet.iloc[self.rowIndex, appendIndeces[i]]).strip()
                        if re.match(r"\*", appendFieldTypes[i]):
                            ## If the list field contains semicolons use it to split instead of commas.
                            if re.match(r".*;.*", appendFieldValue):
                                appendFieldValue = appendFieldValue.strip(";").split(";")
                            else:
                                appendFieldValue = appendFieldValue.strip(",").split(",")

                        appendFieldMap[appendFields[i]] = appendFieldValue

                    prependFieldMap = {}
                    for i in range(len(prependIndeces)):
                        prependFieldValue = xstr(worksheet.iloc[self.rowIndex, prependIndeces[i]]).strip()
                        if re.match(r"\*", prependFieldTypes[i]):
                            ## If the list field contains semicolons use it to split instead of commas.
                            if re.match(r".*;.*", prependFieldValue):
                                prependFieldValue = prependFieldValue.strip(";").split(";")
                            else:
                                prependFieldValue = prependFieldValue.strip(",").split(",")

                        prependFieldMap[prependFields[i]] = prependFieldValue

                    regexFieldMap = {}
                    for i in range(len(regexIndeces)):
                        regexFieldValue = xstr(worksheet.iloc[self.rowIndex, regexIndeces[i]]).strip()
                        if (reMatch := re.match(r"(r[\"'].*[\"'])\s*,\s*(r[\"'].*[\"'])$",regexFieldValue)):
                            regexFieldMap[regexFields[i]] = [ reMatch.group(1), reMatch.group(2) ]
                        else:
                            raise TagParserError("#table_name.field_name.regex value is not of the correct format r\"...\",r\"...\".", self.fileName, self.sheetName, self.rowIndex, valueIndex)

                    if not localComparisonType in self.modificationDirectives[table][fieldID]:
                        self.modificationDirectives[table][fieldID][localComparisonType] = {}
                    if not fieldValue in self.modificationDirectives[table][fieldID][localComparisonType]:
                        self.modificationDirectives[table][fieldID][localComparisonType][fieldValue] = {}
                    # elif not silent:
                    #     print(TagParserError("Warning: duplicate modification directive given", self.fileName, self.sheetName, self.rowIndex, self.columnIndex), file=sys.stderr)
                    if assignFieldMap:
                        if "assign" in self.modificationDirectives[table][fieldID][localComparisonType][fieldValue]:
                            ## If any of the keys in assignFieldMap are already in modificationDirectives then it is a duplicate assign modification.
                            if any([key in self.modificationDirectives[table][fieldID][localComparisonType][fieldValue]["assign"] for key in assignFieldMap]) and not silent:
                                print(TagParserError("Warning: duplicate assign modification directive given", self.fileName, self.sheetName, self.rowIndex, self.columnIndex), file=sys.stderr)
                            
                            self.modificationDirectives[table][fieldID][localComparisonType][fieldValue]["assign"].update(assignFieldMap)
                        else:
                            self.modificationDirectives[table][fieldID][localComparisonType][fieldValue]["assign"] = assignFieldMap
                    if appendFieldMap:
                        if "append" in self.modificationDirectives[table][fieldID][localComparisonType][fieldValue]:
                            ## If any of the keys in appendFieldMap are already in modificationDirectives then it is a duplicate append modification.
                            if any([key in self.modificationDirectives[table][fieldID][localComparisonType][fieldValue]["append"] for key in appendFieldMap]) and not silent:
                                print(TagParserError("Warning: duplicate append modification directive given", self.fileName, self.sheetName, self.rowIndex, self.columnIndex), file=sys.stderr)
                            
                            self.modificationDirectives[table][fieldID][localComparisonType][fieldValue]["append"].update(appendFieldMap)
                        else:
                            self.modificationDirectives[table][fieldID][localComparisonType][fieldValue]["append"] = appendFieldMap
                    if prependFieldMap:
                        if "prepend" in self.modificationDirectives[table][fieldID][localComparisonType][fieldValue]:
                            ## If any of the keys in prependFieldMap are already in modificationDirectives then it is a duplicate prepend modification.
                            if any([key in self.modificationDirectives[table][fieldID][localComparisonType][fieldValue]["prepend"] for key in prependFieldMap]) and not silent:
                                print(TagParserError("Warning: duplicate prepend modification directive given", self.fileName, self.sheetName, self.rowIndex, self.columnIndex), file=sys.stderr)
                            
                            self.modificationDirectives[table][fieldID][localComparisonType][fieldValue]["prepend"].update(prependFieldMap)
                        else:
                            self.modificationDirectives[table][fieldID][localComparisonType][fieldValue]["prepend"] = prependFieldMap
                    if regexFieldMap:
                        if "regex" in self.modificationDirectives[table][fieldID][localComparisonType][fieldValue]:
                            ## If any of the keys in regexFieldMap are already in modificationDirectives then it is a duplicate regex modification.
                            if any([key in self.modificationDirectives[table][fieldID][localComparisonType][fieldValue]["regex"] for key in regexFieldMap]) and not silent:
                                print(TagParserError("Warning: duplicate regex modification directive given", self.fileName, self.sheetName, self.rowIndex, self.columnIndex), file=sys.stderr)
                            
                            self.modificationDirectives[table][fieldID][localComparisonType][fieldValue]["regex"].update(regexFieldMap)
                        else:
                            self.modificationDirectives[table][fieldID][localComparisonType][fieldValue]["regex"] = regexFieldMap
                    if deletionFields:
                        if "delete" in self.modificationDirectives[table][fieldID][localComparisonType][fieldValue]:
                            ## If any of fields in deletionFields are already in modificationDirectives then it is a duplicate delete modification.
                            if any([field in self.modificationDirectives[table][fieldID][localComparisonType][fieldValue]["delete"] for field in deletionFields]) and not silent:
                                print(TagParserError("Warning: duplicate delete modification directive given", self.fileName, self.sheetName, self.rowIndex, self.columnIndex), file=sys.stderr)
                            
                            self.modificationDirectives[table][fieldID][localComparisonType][fieldValue]["delete"].extend(deletionFields)
                        else:
                            self.modificationDirectives[table][fieldID][localComparisonType][fieldValue]["delete"] = deletionFields
                    if renameFieldMap:
                        if "rename" in self.modificationDirectives[table][fieldID][localComparisonType][fieldValue]:
                            ## If any of the keys in renameFieldMap are already in modificationDirectives then it is a duplicate rename modification.
                            if any([key in self.modificationDirectives[table][fieldID][localComparisonType][fieldValue]["rename"] for key in renameFieldMap]) and not silent:
                                print(TagParserError("Warning: duplicate rename modification directive given", self.fileName, self.sheetName, self.rowIndex, self.columnIndex), file=sys.stderr)
                            
                            self.modificationDirectives[table][fieldID][localComparisonType][fieldValue]["rename"].update(renameFieldMap)
                        else:
                            self.modificationDirectives[table][fieldID][localComparisonType][fieldValue]["rename"] = renameFieldMap
            except TagParserError as err:
                print(err.value, file=sys.stderr)
                exit(1)
            ## I don't think this can be triggered from the CLI.
            except:
                print(TagParserError("Internal Parser Error", self.fileName, self.sheetName, self.rowIndex, self.columnIndex), file=sys.stderr)
                raise

        self.rowIndex = -1

    def _parseAutomationSheet(self, fileName: str, sheetName: str, worksheet: pandas.core.series.Series):
        """Extracts automation directives from a given worksheet.

        "automation" : [ { "header_tag_descriptions" : [ { "header" : column_description, "tag" : tag_description, "required" : true|false } ],   "exclusion_test" : exclusion_value, "insert" : [ [ cell_content, ... ] ] } ]
            
        Loops over worksheet and builds up self.automationDirectives.
        
        Args:
            fileName: used for printing more descriptive error messages.
            sheetName: used for printing more descriptive error messages.
            worksheet: data used to build the automation directives.

        Raises:
            TagParserError: usually raised for malformed tags, but also for other unpredicted errors
            Exception: a catch all in case something unforeseen happens.
        """
        self.columnIndex = -1
        self.rowIndex = -1
        self.fileName = fileName
        self.sheetName = sheetName

        aColumn = worksheet.iloc[:, 0]

        parsing = False

        self.rowIndex = 0
        currAutomationGroup = None
        while self.rowIndex < len(aColumn):
            try:
                if re.match('#tags$', xstr(aColumn.iloc[self.rowIndex]).strip()):
                    parsing = True
                    headerIndex = -1
                    tagIndex = -1
                    usedHeaders = set()
                    ## If #tags group is twice in a row remove it from the directives.
                    if self.automationDirectives and "header_tag_descriptions" in self.automationDirectives[-1] and not self.automationDirectives[-1]["header_tag_descriptions"]:
                        self.automationDirectives.pop()
                    currAutomationGroup = { "header_tag_descriptions" : [] }
                    requiredIndex = -1
                    self.automationDirectives.append(currAutomationGroup)
                    for self.columnIndex in range(1, len(worksheet.iloc[self.rowIndex, :])):
                        cellString = xstr(worksheet.iloc[self.rowIndex, self.columnIndex]).strip()
                        if re.match('\s*#header\s*$', cellString):
                            headerIndex = self.columnIndex
                        elif re.match('\s*#add\s*$', cellString):
                            tagIndex = self.columnIndex
                        elif re.match('\s*#required\s*$', cellString):
                            requiredIndex = self.columnIndex
                        elif (reMatch := re.match('\s*#exclude\s*=\s*(.+)\s*$', cellString)):
                            currAutomationGroup["exclusion_test"]=reMatch.group(1)
                    self.columnIndex = -1
                    if headerIndex == -1:
                        raise TagParserError("Missing #header tag", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                    if tagIndex == -1:
                        raise TagParserError("Missing #add tag", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                elif re.match('#ignore$', xstr(aColumn.iloc[self.rowIndex]).strip()):
                    pass
                elif re.match('#insert$', xstr(aColumn.iloc[self.rowIndex]).strip()):
                    ## If #insert is found inside of #tags then it needs to be added to the current tag group, otherwise make a new one.
                    if not parsing:
                        currAutomationGroup = {}
                        self.automationDirectives.append(currAutomationGroup)
                    ## If "insert" is already in the current automation group then add to it and don't overwrite it.
                    if not "insert" in currAutomationGroup:
                        currAutomationGroup["insert"] = []
                        currAutomationGroup["insert_multiple"] = False
                        for self.columnIndex in range(1, len(worksheet.iloc[self.rowIndex, :])):
                            cellString = xstr(worksheet.iloc[self.rowIndex, self.columnIndex]).strip()
                            if re.match('\s*#multiple\s*=\s*[Tt]rue\s*$', cellString):
                                currAutomationGroup["insert_multiple"] = True
                            elif re.match('\s*#multiple\s*=\s*[Ff]alse\s*$', cellString):
                                currAutomationGroup["insert_multiple"] = False

                    endTagFound = False
                    while self.rowIndex < len(aColumn)-1:
                        self.rowIndex += 1
                        if re.match('#end$', xstr(aColumn.iloc[self.rowIndex]).strip()):
                            endTagFound = True
                            break
                        currAutomationGroup["insert"].append([xstr(worksheet.iloc[self.rowIndex, self.columnIndex]).strip() for self.columnIndex in range(0, len(worksheet.iloc[self.rowIndex, :]))])

                    if not endTagFound:
                        raise TagParserError("Missing #end tag", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                elif TagParser._isEmptyRow(worksheet.iloc[self.rowIndex, :]):
                    parsing = False
                elif parsing:
                    headerValue = xstr(worksheet.iloc[self.rowIndex, headerIndex]).strip()
                    newTagValue = xstr(worksheet.iloc[self.rowIndex, tagIndex]).strip()
                    localRequired = True if requiredIndex == -1 or re.match("[Tt]rue$", xstr(worksheet.iloc[self.rowIndex, requiredIndex]).strip()) else False

                    if headerValue not in usedHeaders:
                        usedHeaders.add(headerValue)
                        currAutomationGroup["header_tag_descriptions"].append({ "header" : headerValue, "tag" : newTagValue, "required" : localRequired })
                    elif not silent:
                        print(TagParserError("Warning: duplicate header description provided in automation directive", self.fileName, self.sheetName, self.rowIndex, self.columnIndex), file=sys.stderr)
            except TagParserError as err:
                print(err.value, file=sys.stderr)
                exit(1)
            ## Not sure you can get to this from the CLI.
            except:
                print(TagParserError("Internal Parser Error", self.fileName, self.sheetName, self.rowIndex, self.columnIndex), file=sys.stderr)
                raise

            self.rowIndex += 1

        ## I'm not sure what this was testing for, presumably empty directives need to be removed.
#        if self.automationDirectives and not self.automationDirectives[-1]["header_tag_descriptions"]:
#            self.automationDirectives.pop()
        
        ## Only keep non empty directives.
        self.automationDirectives = [directive for directive in self.automationDirectives if "header_tag_descriptions" in directive and directive["header_tag_descriptions"] or not "header_tag_descriptions" in directive]
        

        self.rowIndex = -1

    def readDirectives(self, source: str, sheetName: str, directiveType: str, removeRegex: str|None, isDefaultSearch: bool =False) -> dict:
        """Read directives source of a given directive type.
        
        Args:
            source: file path.
            sheetName: sheet name for an Excel file, ignored if not an Excel file.
            directiveType: either "modification" or "automation" to call the correct parsing function.
            removeRegex: a string to pass to DataFrame.replace() to replace characters with an empty string in the dataframe that is read in. 
                         Can be a regex. Set to None to not replace anything. Passed to loadSheet.
            isDefaultSearch: whether or not the source is using default values, passed to loadSheet for message printing.
        
        Returns:
            The directives that were read in.
        """
        directives = None
        if re.search(r"\.json$", source):
            with open(source, 'r') as jsonFile:
                directives = json.load(jsonFile)
                if type(directives) == dict and directiveType in directives:
                    directives = directives[directiveType]
                else:
                    directives = None
                    if not silent:
                        print("Warning: The input directives JSON file is either not a dict or does not contain the directive keyword \"" + directiveType + "\". This means that " + directiveType + " will not be done.", file=sys.stderr)
        elif TagParser.hasFileExtension(source) or TagParser.isGoogleSheetsFile(source):
            dataFrameTuple = TagParser.loadSheet(source, sheetName, removeRegex=removeRegex, isDefaultSearch=isDefaultSearch)
            if dataFrameTuple != None:
                if directiveType == "modification":
                    self.modificationDirectives = {}
                    self._parseModificationSheet(*dataFrameTuple)
                    directives = self.modificationDirectives
                else:
                    self.automationDirectives = []
                    self._parseAutomationSheet(*dataFrameTuple)
                    directives = copy.deepcopy(self.automationDirectives)

        return directives

    def _applyModificationDirectives(self, record: dict, recordPath: str, modifications: dict):
        """Apply modification directives to the given record.
        
        Args:
            record: a record from self.extraction extracted from metadata.
            recordPath: the path to the record in self.extraction, used for printing warning messages.
            modifications: the modifications to apply to the record.
        """
        if "assign" in modifications:
            for newField, newValue in modifications["assign"].items():
                if type(newValue) == Evaluator:
                    if newValue.hasRequiredFields(record):
                        newValueForRecord = newValue.evaluate(record)
                        if newField in record and not silent:
                            if isinstance(record[newField], list) and not isinstance(newValueForRecord, list):
                                print("Warning: \"" + newField + "\" in record, " + recordPath + ", was assigned a non list type value but was originally a list type value.")
                            elif not isinstance(record[newField], list) and isinstance(newValueForRecord, list):
                                print("Warning: \"" + newField + "\" in record, " + recordPath + ", was assigned a list type value but was not originally a list type value.")
                        
                        record[newField] = newValueForRecord
                        
                    elif not silent:
                        print("Warning: Field assignment directive \"" + newField + "\" missing required field(s) \"" + ",".join([ field for field in newValue.requiredFields if field not in record]) + "\", or a regular expression matched no fields or more than one.", file=sys.stderr)
                else:
                    ## If this is not a copy when it is a list it has unexpected results.
                    newValueForRecord = copy.deepcopy(newValue)
                    if newField in record and not silent:
                        if isinstance(record[newField], list) and not isinstance(newValueForRecord, list):
                            print("Warning: \"" + newField + "\" in record, " + recordPath + ", was assigned a non list type value but was originally a list type value.")
                        elif not isinstance(record[newField], list) and isinstance(newValueForRecord, list):
                            print("Warning: \"" + newField + "\" in record, " + recordPath + ", was assigned a list type value but was not originally a list type value.")
                    
                    record[newField] = newValueForRecord
                
                if newField in record:
                    fieldPath = recordPath + newField
                    if fieldPath in self.changedRecords:
                        if (("assign" == self.changedRecords[fieldPath]["previous_modification_type"] and self.changedRecords[fieldPath]["previous_modification_value"] != record[newField]) or\
                           "append" == self.changedRecords[fieldPath]["previous_modification_type"] or \
                           "prepend" == self.changedRecords[fieldPath]["previous_modification_type"] or\
                           "regex" == self.changedRecords[fieldPath]["previous_modification_type"] or \
                           "delete" == self.changedRecords[fieldPath]["previous_modification_type"]) and not silent:
                            print("Warning: \"" + newField + "\" in record, " + recordPath + ", was assigned a new value after previously being modified by a different modification directive.", file=sys.stderr)
                    else:
                        self.changedRecords[fieldPath] = {}
                    
                    self.changedRecords[fieldPath]["previous_modification_type"] = "assign"
                    self.changedRecords[fieldPath]["previous_modification_value"] = record[newField]

        if "append" in modifications:
            for newField, newValue in modifications["append"].items():
                if newField not in record and type(newValue) == list:
                    record[newField] = newValue.copy()
                elif newField not in record and type(newValue) != list:
                    record[newField] = newValue
                elif type(record[newField]) == list and type(newValue) == list:
                    minLen = min(len(record[newField]),len(newValue))
                    for index in range(minLen):
                        record[newField][index] += newValue[index]
                elif type(record[newField]) == list and type(newValue) != list:
                    for index in range(len(record[newField])):
                        record[newField][index] += newValue
                elif type(record[newField]) != list and type(newValue) == list:
                    record[newField] += newValue[0]
                else:
                    record[newField] += newValue
                    
                fieldPath = recordPath + newField
                if fieldPath in self.changedRecords:
                    if "delete" == self.changedRecords[fieldPath]["previous_modification_type"] and not silent:
                        print("Warning: The field, \"" + newField + "\", in record, " + recordPath + ", was deleted before being appended to by a different modification directive.", file=sys.stderr)
                else:
                    self.changedRecords[fieldPath] = {}
                
                self.changedRecords[fieldPath]["previous_modification_type"] = "append"
                self.changedRecords[fieldPath]["previous_modification_value"] = record[newField]

        if "prepend" in modifications:
            for newField, newValue in modifications["prepend"].items():
                if newField not in record and type(newValue) == list:
                    record[newField] = newValue.copy()
                elif newField not in record and type(newValue) != list:
                    record[newField] = newValue
                elif type(record[newField]) == list and type(newValue) == list:
                    minLen = min(len(record[newField]),len(newValue))
                    for index in range(minLen):
                        record[newField][index] = newValue[index] + record[newField][index]
                elif type(record[newField]) == list and type(newValue) != list:
                    for index in range(len(record[newField])):
                        record[newField][index] = newValue + record[newField][index]
                elif type(record[newField]) != list and type(newValue) == list:
                    record[newField] = newValue[0] + record[newField]
                else:
                    record[newField] = newValue + record[newField]
                    
                fieldPath = recordPath + newField
                if fieldPath in self.changedRecords:
                    if "delete" == self.changedRecords[fieldPath]["previous_modification_type"] and not silent:
                        print("Warning: The field, \"" + newField + "\", in record, " + recordPath + ", was deleted before being prepended to by a different modification directive.", file=sys.stderr)
                else:
                    self.changedRecords[fieldPath] = {}
                
                self.changedRecords[fieldPath]["previous_modification_type"] = "prepend"
                self.changedRecords[fieldPath]["previous_modification_value"] = record[newField]

        if "regex" in modifications:
            for newField, regexPair in modifications["regex"].items():
                fieldInRecord = True
                if newField not in record:
                    fieldInRecord = False
                    if not silent:
                        print("Warning: regex substitution (" + ",".join(regexPair) + ") cannot be applied to record with missing field \"" + newField + "\"", file=sys.stderr)
                elif type(record[newField]) == list:
                    for index in range(len(record[newField])):
                        record[newField][index] = re.sub(regexPair[0],regexPair[1],record[newField][index])
                else:
                    oldValue = record[newField]
                    record[newField] = re.sub(regexPair[0],regexPair[1],record[newField])
                    if oldValue == record[newField]:
                        if not silent:
                            print("Warning: regex substitution (" + ",".join(regexPair) + ") produces no change in field \"" + newField + "\" value \"" + oldValue + "\"", file=sys.stderr)
                            
                fieldPath = recordPath + newField
                if fieldPath in self.changedRecords:
                    if "delete" == self.changedRecords[fieldPath]["previous_modification_type"] and not silent:
                        print("Warning: The field, \"" + newField + "\", in record, " + recordPath + ", was deleted by a modification directive before attempting to be modified by a regex modification directive.", file=sys.stderr)
                    if "assign" == self.changedRecords[fieldPath]["previous_modification_type"] and not silent:
                        print("Warning: The field, \"" + newField + "\", in record, " + recordPath + ", had a regex substitution applied after previously being assigned a new value by an assignment modification directive.", file=sys.stderr)
                elif fieldInRecord:
                    self.changedRecords[fieldPath] = {}
                
                if fieldInRecord:
                    self.changedRecords[fieldPath]["previous_modification_type"] = "regex"
                    self.changedRecords[fieldPath]["previous_modification_value"] = record[newField]

        if "delete" in modifications:
            for deletedField in modifications["delete"]:
                record.pop(deletedField, None)
                
                fieldPath = recordPath + deletedField
                if fieldPath in self.changedRecords:
                    if ("assign" == self.changedRecords[fieldPath]["previous_modification_type"] or\
                       "append" == self.changedRecords[fieldPath]["previous_modification_type"] or \
                       "prepend" == self.changedRecords[fieldPath]["previous_modification_type"] or\
                       "regex" == self.changedRecords[fieldPath]["previous_modification_type"] or\
                       "rename" == self.changedRecords[fieldPath]["previous_modification_type"]) and not silent:
                        print("Warning: The field, \"" + deletedField + "\", in record, " + recordPath + ", was deleted after previously being modified by a different modification directive.", file=sys.stderr)
                else:
                    self.changedRecords[fieldPath] = {}
                
                self.changedRecords[fieldPath]["previous_modification_type"] = "delete"
                self.changedRecords[fieldPath]["previous_modification_value"] = ""

        if "rename" in modifications:
            for oldField,newField in modifications["rename"].items():
                fieldInRecord = False
                if oldField in record:
                    
                    if newField in record:
                        print("Warning: A modification directive has renamed the field \"" + oldField + "\" to \"" + newField + "\" for record " + recordPath + ", but \"" + newField + "\" already existed in the record, so its value was overwritten.", file=sys.stderr)

                    fieldInRecord = True
                    record[newField] = record[oldField]
                    record.pop(oldField, None)
                    
                
                if not fieldInRecord:
                    fieldPath = recordPath + oldField
                    if fieldPath in self.changedRecords:
                        if "delete" == self.changedRecords[fieldPath]["previous_modification_type"] and not silent:
                            print("Warning: The field, \"" + oldField + "\", in record, " + recordPath + ", was deleted by a modification directive, and then a different modification directive attempted to rename it, but it no longer exists.", file=sys.stderr)
                else:
                    fieldPath = recordPath + newField
                    if fieldPath in self.changedRecords:
                        if "delete" == self.changedRecords[fieldPath]["previous_modification_type"] and not silent:
                            print("Warning: The field, \"" + newField + "\", in record, " + recordPath + ", was deleted by a modification directive, but then a rename directive created it again from a different field.", file=sys.stderr)
                    else:
                        self.changedRecords[fieldPath] = {}
                
                    self.changedRecords[fieldPath]["previous_modification_type"] = "rename"
                    self.changedRecords[fieldPath]["previous_modification_value"] = record[newField]
                    
                    ## not sure if the old field that was removed should be added or not.
                    # if recordPath + oldField not in self.changedRecords:
                    #     self.changedRecords[recordPath + oldField] = {}
                    
                    # self.changedRecords[recordPath + oldField]["previous_modification_type"] = "rename"
                    # self.changedRecords[recordPath + oldField]["previous_modification_value"] = record[newField]


    def _applyExactModificationDirectives(self, tableKey: str, fieldKey: str, modificationDirectives: dict):
        """Tests and applies exact modification directives
        
        Args:
            tableKey: table key in modificationDirectives to get to the modification to apply.
            fieldKey: field key in modificationDirectives to get to the modification to apply.
            modificationDirectives: contains the modifications to apply.
        """
        comparisonTypes = ["exact-first", "exact-first-nowarn", "exact-unique", "exact-all"]
        firstTypes = ["exact-first", "exact-first-nowarn"]
        
        for comparisonType in comparisonTypes:
            if comparisonType == "exact-unique":
                isUnique=True
            else:
                isUnique=False
            if comparisonType in firstTypes:
                isFirst=True
            else:
                isFirst=False
        
            matchedFieldValues = {}
    
            if comparisonType in modificationDirectives[tableKey][fieldKey]:
                table = self.extraction[tableKey]
                for idKey, record in table.items():
                    if fieldKey in record:
                        fieldValue = record[fieldKey]
                        if type(fieldValue) == list:
                            for specificValue in fieldValue:
                                if specificValue in modificationDirectives[tableKey][fieldKey][comparisonType]:
                                    if isFirst:
                                        if specificValue not in matchedFieldValues:
                                            self._applyModificationDirectives(record, tableKey + "[" + idKey + "]", modificationDirectives[tableKey][fieldKey][comparisonType][specificValue])
                                            matchedFieldValues[specificValue] = {"idKey":idKey, "numberOfMatches":1}
                                            self.usedModifications.add((tableKey, fieldKey, comparisonType, specificValue))
                                        elif comparisonType == "exact-first" and not silent:
                                            print("Warning: modification directive #" + tableKey + "." + fieldKey + "." + comparisonType + "." + specificValue + " matches more than one record. Only the first record will be changed. Try #match=all if all matching records should be changed, or #match=first-nowarn to silence this message.", file=sys.stderr)
                                    
                                    elif isUnique:
                                        if specificValue not in matchedFieldValues:
                                            matchedFieldValues[specificValue] = {"idKey":idKey, "numberOfMatches":1}
                                        else:
                                            matchedFieldValues[specificValue]["numberOfMatches"] += 1
                                            
                                    else:
                                        self._applyModificationDirectives(record, tableKey + "[" + idKey + "]", modificationDirectives[tableKey][fieldKey][comparisonType][specificValue])
                                        self.usedModifications.add((tableKey, fieldKey, comparisonType, specificValue))
                        
                        elif fieldValue in modificationDirectives[tableKey][fieldKey][comparisonType]:
                            if isFirst:
                                if fieldValue not in matchedFieldValues:
                                    self._applyModificationDirectives(record, tableKey + "[" + idKey + "]", modificationDirectives[tableKey][fieldKey][comparisonType][fieldValue])
                                    matchedFieldValues[fieldValue] = {"idKey":idKey, "numberOfMatches":1}
                                    self.usedModifications.add((tableKey, fieldKey, comparisonType, fieldValue))
                                elif comparisonType == "exact-first" and not silent:
                                    print("Warning: modification directive #" + tableKey + "." + fieldKey + "." + comparisonType + "." + fieldValue + " matches more than one record. Only the first record will be changed. Try #match=all if all matching records should be changed, or #match=first-nowarn to silence this message.", file=sys.stderr)
                            
                            elif isUnique:
                                if fieldValue not in matchedFieldValues:
                                    matchedFieldValues[fieldValue] = {"idKey":idKey, "numberOfMatches":1}
                                else:
                                    matchedFieldValues[fieldValue]["numberOfMatches"] += 1
                                    
                            else:
                                self._applyModificationDirectives(record, tableKey + "[" + idKey + "]", modificationDirectives[tableKey][fieldKey][comparisonType][fieldValue])
                                self.usedModifications.add((tableKey, fieldKey, comparisonType, fieldValue))

                if isUnique:
                    for fieldValue, attributes in matchedFieldValues.items():
                        if attributes["numberOfMatches"] == 1:
                            self._applyModificationDirectives(table[attributes["idKey"]], tableKey + "[" + attributes["idKey"] + "]", modificationDirectives[tableKey][fieldKey][comparisonType][fieldValue])
                            self.usedModifications.add((tableKey, fieldKey, comparisonType, fieldValue))




    def _applyRegexModificationDirectives(self, tableKey: str, fieldKey: str, modificationDirectives: dict, regexObjects: dict):
        """Tests and applies regular expression modification directives.

        Args:
            tableKey: table key in modificationDirectives to get to the modification to apply.
            fieldKey: field key in modificationDirectives to get to the modification to apply.
            modificationDirectives: contains the modifications to apply.
            regexObjects: mapping of the regex string in the directives to their compiled objects.
        """
        comparisonTypes = ["regex-first", "regex-first-nowarn", "regex-unique", "regex-all"]
        firstTypes = ["regex-first", "regex-first-nowarn"]
        
        for comparisonType in comparisonTypes:
            if comparisonType == "regex-unique":
                isUnique=True
            else:
                isUnique=False
            if comparisonType in firstTypes:
                isFirst=True
            else:
                isFirst=False
        
            matchedRegexIDs = {}
                    
            if comparisonType in modificationDirectives[tableKey][fieldKey]:
                table = self.extraction[tableKey]
                for idKey, record in table.items():
                    if fieldKey in record:
                        fieldValue = record[fieldKey]
                        for regexID, regexEntry in modificationDirectives[tableKey][fieldKey][comparisonType].items():
                            if type(fieldValue) == list:
                                for specificValue in fieldValue:
                                    if re.search(regexObjects[regexID], specificValue):
                                        if isFirst:
                                            if regexID not in matchedRegexIDs:
                                                self._applyModificationDirectives(record, tableKey + "[" + idKey + "]", regexEntry)
                                                matchedRegexIDs[regexID] = {"idKey":idKey, "numberOfMatches":1}
                                                self.usedModifications.add((tableKey, fieldKey, comparisonType, regexID))
                                            elif comparisonType == "regex-first" and not silent:
                                                print("Warning: modification directive #" + tableKey + "." + fieldKey + "." + comparisonType + "." + regexID + " matches more than one record. Only the first record will be changed. Try #match=all if all matching records should be changed, or #match=first-nowarn to silence this message.", file=sys.stderr)
                                        
                                        elif isUnique:
                                            if regexID not in matchedRegexIDs:
                                                matchedRegexIDs[regexID] = {"idKey":idKey, "numberOfMatches":1}
                                            else:
                                                matchedRegexIDs[regexID]["numberOfMatches"] += 1
                                                
                                        else:
                                            self._applyModificationDirectives(record, tableKey + "[" + idKey + "]", regexEntry)
                                            self.usedModifications.add((tableKey, fieldKey, comparisonType, regexID))
                                                                    
                            elif re.search(regexObjects[regexID], fieldValue):
                                if isFirst:
                                    if regexID not in matchedRegexIDs:
                                        self._applyModificationDirectives(record, tableKey + "[" + idKey + "]", regexEntry)
                                        matchedRegexIDs[regexID] = {"idKey":idKey, "numberOfMatches":1}
                                        self.usedModifications.add((tableKey, fieldKey, comparisonType, regexID))
                                    elif comparisonType == "regex-first" and not silent:
                                        print("Warning: modification directive #" + tableKey + "." + fieldKey + "." + comparisonType + "." + regexID + " matches more than one record. Only the first record will be changed. Try #match=all if all matching records should be changed, or #match=first-nowarn to silence this message.", file=sys.stderr)
                                
                                elif isUnique:
                                    if regexID not in matchedRegexIDs:
                                        matchedRegexIDs[regexID] = {"idKey":idKey, "numberOfMatches":1}
                                    else:
                                        matchedRegexIDs[regexID]["numberOfMatches"] += 1
                                        
                                else:
                                    self._applyModificationDirectives(record, tableKey + "[" + idKey + "]", regexEntry)
                                    self.usedModifications.add((tableKey, fieldKey, comparisonType, regexID))
                    
                if isUnique:
                    for regexID, attributes in matchedRegexIDs.items():
                        if attributes["numberOfMatches"] == 1:
                            self._applyModificationDirectives(table[attributes["idKey"]], tableKey + "[" + attributes["idKey"] + "]", modificationDirectives[tableKey][fieldKey][comparisonType][regexID])
                            self.usedModifications.add((tableKey, fieldKey, comparisonType, regexID))



    def _applyLevenshteinModificationDirectives(self, tableKey: str, fieldKey: str, modificationDirectives: dict):
        """Tests and applies levenshtein modification directives.

        Args:
            tableKey: table key in modificationDirectives to get to the modification to apply.
            fieldKey: field key in modificationDirectives to get to the modification to apply.
            modificationDirectives: contains the modifications to apply.
        """
        comparisonTypes = ["levenshtein-first", "levenshtein-first-nowarn", "levenshtein-unique", "levenshtein-all"]
        firstTypes = ["levenshtein-first", "levenshtein-first-nowarn"]
        
        for comparisonType in comparisonTypes:
            if comparisonType == "levenshtein-unique":
                isUnique=True
            else:
                isUnique=False
            if comparisonType in firstTypes:
                isFirst=True
            else:
                isFirst=False
        
            if comparisonType in modificationDirectives[tableKey][fieldKey]:
                levenshteinComparisons = collections.defaultdict(dict)
                levenshteinComparisonValues = collections.defaultdict(dict)
                for levID, levEntry in modificationDirectives[tableKey][fieldKey][comparisonType].items():
                    for idKey, record in self.extraction[tableKey].items():
                        if fieldKey in record:
                            ## If the comparison field is a list field then calculate the distance between all values in the list and use the smallest for comparison.
                            if type(record[fieldKey]) == list:
                                fieldValues = record[fieldKey]
                                levenshteinDistances = [jellyfish.levenshtein_distance(levID, specificValue) for specificValue in fieldValues]
                                levenshteinComparisons[levID][idKey] = min(levenshteinDistances)
                                levenshteinComparisonValues[levID][idKey] = fieldValues[min(range(len(levenshteinDistances)), key=levenshteinDistances.__getitem__)]
                            else:
                                levenshteinComparisons[levID][idKey] = jellyfish.levenshtein_distance(levID, record[fieldKey])
                                levenshteinComparisonValues[levID][idKey] = record[fieldKey]
                
                idKeySet = set()
                for levID in levenshteinComparisons.keys():
                    idKeySet |= set(levenshteinComparisons[levID].keys())
    
                uniqueForIdKey = collections.defaultdict(None)
                for idKey in idKeySet:
                    usableLevIDs = [levID for levID in levenshteinComparisons.keys() if idKey in levenshteinComparisons[levID]]
                    minLevID = min(levenshteinComparisons.keys(), key=(lambda k: levenshteinComparisons[k][idKey]))
                    minLevValue = levenshteinComparisons[minLevID][idKey]
                    ## Assign only if there is 1 match to the minimum levenshtein distance.
                    if sum(levenshteinComparisons[levKey][idKey] == minLevValue for levKey in usableLevIDs) == 1:
                        uniqueForIdKey[idKey] = minLevID
                        
                
                uniqueForLevenshteinID = collections.defaultdict(None)
                for levID in levenshteinComparisons.keys():
                    minIDKey = min(levenshteinComparisons[levID].keys(), key=(lambda k: levenshteinComparisons[levID][k]))
                    minIDValue = levenshteinComparisons[levID][minIDKey]
                    if isFirst:
                        idKeysThatHaveMinValue = [idKey for idKey in levenshteinComparisons[levID] if levenshteinComparisons[levID][idKey] == minIDValue]
                        uniqueForLevenshteinID[levID] = idKeysThatHaveMinValue[0]
                        if comparisonType == "levenshtein-first" and len(idKeysThatHaveMinValue) > 1 and not silent:
                            print("Warning: modification directive #" + tableKey + "." + fieldKey + "." + comparisonType + "." + levID + " matches more than one record. Only the first record will be changed. Try #match=all if all matching records should be changed, or #match=first-nowarn to silence this message.", file=sys.stderr)
                            
                    elif isUnique:
                        if sum(levenshteinComparisons[levID][idKey] == minIDValue for idKey in levenshteinComparisons[levID]) == 1:
                            uniqueForLevenshteinID[levID] = minIDKey
                            
                    else:
                        idKeysThatHaveMinValue = [idKey for idKey in levenshteinComparisons[levID] if levenshteinComparisons[levID][idKey] == minIDValue]
                        uniqueForLevenshteinID[levID] = idKeysThatHaveMinValue

                
                if isFirst or isUnique:
                    for levID, levEntry in modificationDirectives[tableKey][fieldKey][comparisonType].items():
                        if levID in uniqueForLevenshteinID and uniqueForIdKey[uniqueForLevenshteinID[levID]] == levID:
                            self._applyModificationDirectives(self.extraction[tableKey][uniqueForLevenshteinID[levID]], tableKey + "[" + uniqueForLevenshteinID[levID] + "]", levEntry)
                            self.usedModifications.add((tableKey, fieldKey, comparisonType, levID))
                else:
                    for levID, levEntry in modificationDirectives[tableKey][fieldKey][comparisonType].items():
                        if levID in uniqueForLevenshteinID:
                            for idKey in uniqueForLevenshteinID[levID]:
                                self._applyModificationDirectives(self.extraction[tableKey][idKey], tableKey + "[" + idKey + "]", levEntry)
                                self.usedModifications.add((tableKey, fieldKey, comparisonType, levID))
                
                

    def modify(self, modificationDirectives: dict):
        """Applies modificationDirectives to the extracted metadata.

        Args:
            modificationDirectives: contains the modifications to apply.
        """
        self.modificationDirectives = modificationDirectives
        if modificationDirectives != None:
            modificationDirectives = copy.deepcopy(modificationDirectives) # Must make deepcopy since regex objects being embedded.

            if getattr(self,"unusedModifications", None) is None:
                self.unusedModifications = set()

            if getattr(self,"usedModifications", None) is None:
                self.usedModifications = set()
                
            # Compile regex objects for comparison.
            regexObjects = {}
            for tableDict in modificationDirectives.values():
                for fieldDict in tableDict.values():
                    for regex_type in ["regex-first", "regex-first-nowarn", "regex-unique", "regex-all"]:
                        if regex_type in fieldDict:
                            regexObjects.update({ regexString : re.compile(re.match(TagParser.reDetector, regexString)[1]) for regexString in  fieldDict[regex_type].keys()})
            
            # Compile regex objects for regex substitution directives.
            for tableDict in modificationDirectives.values():
                for fieldDict in tableDict.values():
                    for comparisonTypeDict in fieldDict.values():
                        for fieldValueDict in comparisonTypeDict.values():
                            if "regex" in fieldValueDict:
                                fieldValueDict["regex"] = { newField : [ re.match(TagParser.reDetector, regexPair[0])[1], re.match(TagParser.reDetector, regexPair[1])[1] ]
                                                            for newField,regexPair in fieldValueDict["regex"].items() }

            # Create Evaluator objects for assign directives with "eval(...)" values.
            for tableDict in modificationDirectives.values():
                for fieldDict in tableDict.values():
                    for comparisonTypeDict in fieldDict.values():
                        for fieldValueDict in comparisonTypeDict.values():
                            if "assign" in fieldValueDict:
                                for newField in fieldValueDict["assign"].keys():
                                    if isinstance(fieldValueDict["assign"][newField], str) and (reMatch := Evaluator.isEvalString(fieldValueDict["assign"][newField])):
                                        fieldValueDict["assign"][newField] = Evaluator(reMatch.group(1))

            self.changedRecords = {}
            for tableKey in modificationDirectives.keys():
                if tableKey in self.extraction:
                    for fieldKey in modificationDirectives[tableKey].keys():
                        ## These functions ultimately modify records in self.extraction.
                        self._applyExactModificationDirectives(tableKey, fieldKey, modificationDirectives)
                        self._applyRegexModificationDirectives(tableKey, fieldKey, modificationDirectives, regexObjects)
                        self._applyLevenshteinModificationDirectives(tableKey, fieldKey, modificationDirectives)

            # Identify changed IDs.
#            idTranslation = collections.defaultdict(dict)
#            for tableKey, table in self.extraction.items():
#                idTranslation[tableKey + ".id"].update({ idKey : record["id"] for idKey, record in table.items() if idKey != record["id"] })

            # Translate changed IDs.
            translated = {}
            for tableKey,table in self.extraction.items() :
                translated[tableKey] = { record["id"] : record for record in table.values() }
                ## This bit of code appears to be unnecessary and useless. 
                ## idTranslation's keys aren't fieldkeys so this will never match anything.
#                for record in table.values():
#                    for fieldKey, fieldValue in record.items() :
#                        if fieldKey in idTranslation:
#                            if type(fieldValue) == list:
#                                for index in range(len(fieldValue)):
#                                    if fieldValue[index] in idTranslation[fieldKey]:
#                                        fieldValue[index] = idTranslation[fieldKey][fieldValue[index]]
#                            elif fieldValue in idTranslation[fieldKey]:
#                                record[fieldKey] = idTranslation[fieldKey][fieldValue]

            for tableKey in self.extraction:
                if len(self.extraction[tableKey]) > len(translated[tableKey]) and not silent:
                    print("Warning: A modification directive has set at least 2 records in the \"" + tableKey + "\" table to the same id. The output will have less records than expected.", file=sys.stderr)
            
            self.extraction = translated

            # Identify used and unused modification directives.
            for tableKey in modificationDirectives.keys():
                for fieldKey in modificationDirectives[tableKey].keys():
                    for comparisonType in modificationDirectives[tableKey][fieldKey]:
                        for modificationID in modificationDirectives[tableKey][fieldKey][comparisonType]:
                            if (tableKey, fieldKey, comparisonType, modificationID) not in self.usedModifications:
                                self.unusedModifications.add((tableKey, fieldKey, comparisonType, modificationID))
                            elif (tableKey, fieldKey, comparisonType, modificationID) in self.unusedModifications:
                                self.unusedModifications.remove((tableKey, fieldKey, comparisonType, modificationID))

    def merge(self, newMetadata: dict):
        """Merges new metadata with current metadata.

        Args:
            newMetadata: dict to merge with self.extraction dict.
        """
        for tableKey, table in newMetadata.items():
            if tableKey not in self.extraction:
                self.extraction[tableKey] = table
            else:
                for idKey, record in table.items():
                    if idKey not in self.extraction[tableKey]:
                        self.extraction[tableKey][idKey] = record
                    else:
                        self.extraction[tableKey][idKey].update(record)

    @staticmethod
    def isComparable(value1: str, value2: str) -> bool:
        """Compares the two values first as strings and then as floats if convertable.

        Args:
            value1: first value to compare.
            value2: second value to compare.
        """
        if value1 == value2:
            return True

        try:
            value1 = float(value1)
            value2 = float(value2)
        except ValueError:
            return False

        return value1 == value2 or abs(value1 - value2) / max(abs(value1),abs(value2)) < 0.00000001

    def compare(self, otherMetadata: dict, groupSize: int =5, file: TextIO|None =sys.stdout) -> bool:
        """Compare current metadata to other metadata.

        Args:
            otherMetadata: dict to compare with self.extraction.
            groupSize: number of record ids to print on a single line before printing more on a new line.
            file: the IO to print messages to, if None then just return True or False instead of printing messages.
            
        Returns:
            True if otherMetadata and self.extraction are different, False otherwise.
        """
        different = False

        missingTables = [ tableKey for tableKey in otherMetadata.keys() if tableKey not in self.extraction ]
        if missingTables:
            different = True
            if file is not None:
                print("Missing Tables:"," ".join(missingTables), file=file)
            else:
                return True

        extraTables = [ tableKey for tableKey in self.extraction.keys() if tableKey not in otherMetadata ]
        if extraTables:
            different = True
            if file is not None:
                print("Extra Tables:"," ".join(extraTables), file=file)
            else:
                return True

        for tableKey, table in otherMetadata.items():
            if tableKey in self.extraction:
                missingIDs = [ idKey for idKey in table.keys() if idKey not in self.extraction[tableKey] ]
                if missingIDs:
                    different = True
                    if file is not None:
                        print("Table", tableKey, "with missing records:", file=file)
                        while missingIDs:
                            group = missingIDs[0:groupSize]
                            missingIDs = missingIDs[groupSize:]
                            print("  ", " ".join(group), file=file)
                    else:
                        return True
                extraIDs = [ idKey for idKey in self.extraction[tableKey].keys() if idKey not in otherMetadata[tableKey] ]
                if extraIDs:
                    different = True
                    if file is not None:
                        print("Table", tableKey, "with extra records:", file=file)
                        while extraIDs:
                            group = extraIDs[0:groupSize]
                            extraIDs = extraIDs[groupSize:]
                            print("  ", " ".join(group), file=file)
                    else:
                        return True

                for idKey, record in table.items():
                    if idKey in self.extraction[tableKey]:
                        differentFields = [ field for field, value in record.items() if field not in self.extraction[tableKey][idKey] or not TagParser.isComparable(value, self.extraction[tableKey][idKey][field]) ]
                        differentFields.extend([ field for field in self.extraction[tableKey][idKey] if field not in record ])
                        if differentFields:
                            different = True
                            if file is not None:
                                print("Table", tableKey, "id", idKey, "with different fields:", ", ".join(differentFields), file=file)
                            else:
                                return True

        return different

    def deleteMetadata(self, sections: list[list[str]]):
        """Delete sections of metadata based on given section descriptions.

        Args:
            sections: list of sections that are lists of strings. The strings should be regular expressions.
        """
        compiled_sections = [ [ re.compile(re.match(TagParser.reDetector, keyElement)[1]) if re.match(TagParser.reDetector, keyElement) else re.compile("^" + re.escape(keyElement) + "$") for keyElement in section ] for section in sections ]

        for section in compiled_sections:
            matched_key_levels = [ (None,None,self.extraction) ]
            for keyDetector in section:
                new_matched_key_levels = []
                for section_level_tuple in matched_key_levels:
                    new_matched_key_levels.extend((keyName, section_level_tuple[2], section_level_tuple[2][keyName]) for keyName in section_level_tuple[2] if re.search(keyDetector,keyName))
                matched_key_levels = new_matched_key_levels

            for section_level_tuple in matched_key_levels:
                if section_level_tuple[0] != None:
                    del section_level_tuple[1][section_level_tuple[0]]

    def findParent(self, parentID: str) -> tuple[str,dict]|None:
        """Returns parent record for given parentID.

        Args:
            parentID: the id to look for in the records of self.extraction.
            
        Returns:
            None if the parentID was not found, (tableKey,parentRecord) if it was.
        """
        for tableKey, table in self.extraction.items():
            if parentID in table:
                return (tableKey,table[parentID])

        return None

    @staticmethod
    def _generateLineage(parentID: str, parent2children: dict) -> dict|None:
        """Generates and returns a lineage structure based on the given parentID.
        
        Args:
            parentID: key to look for in parent2children.
            parent2children: dictionary of parentID to list of children.
            
        Returns:
            None if parentID is not in parent2children, a dictionary of children for the parentID if it is.
        """
        if parentID in parent2children:
            return { child : TagParser._generateLineage(child,parent2children) for child in parent2children[parentID] }
        else:
            return None

    def generateLineages(self) -> dict:
        """Generates and returns parent-child record lineages.

        Returns:
            lineages by tableKey.
        """
        entities_with_parentIDs = []
        for tableKey, table in self.extraction.items():
            entities_with_parentIDs.extend((entity, tableKey, self.findParent(entity["parent_id"])) for entity in table.values() if "parent_id" in entity)

        parent2children = collections.defaultdict(list)
        terminalParentsByTable = collections.defaultdict(list)
        for entity_tuple in entities_with_parentIDs:
            parent2children[entity_tuple[0]["parent_id"]].append(entity_tuple[0]["id"])
            if entity_tuple[2] == None:
                terminalParentsByTable[entity_tuple[1]].append(entity_tuple[0]["parent_id"])
            elif "parent_id" not in entity_tuple[2][1]:
                terminalParentsByTable[entity_tuple[2][0]].append(entity_tuple[0]["parent_id"])

        lineages = collections.defaultdict(list)
        for tableKey in  terminalParentsByTable:
            lineages[tableKey] = { parentID : TagParser._generateLineage(parentID,parent2children) for parentID in terminalParentsByTable[tableKey] }

        return lineages

    @staticmethod
    def printLineages(lineages: collections.defaultdict, indentation: int, groupSize: int =5, file : TextIO =sys.stdout):
        """Prints the given lineages.
        
        Args:
            lineages: dictionary where the keys are table names and values are a dictionary of parentID and children.
            indentation: number of spaces of indentation to print.
            groupSize: number of childIDs to print per line.
        """
        for id in sorted(lineages.keys()):
            if lineages[id]:
                print(" "*indentation,id,":", file=file)
                terminal_children = sorted(childID for childID, children in lineages[id].items() if children == None)
                while terminal_children:
                    children_group = terminal_children[0:groupSize]
                    terminal_children = terminal_children[groupSize:]
                    print(" "*(indentation+2), ", ".join(children_group),file=file)
                non_terminal_children = {childID : children for childID, children in lineages[id].items() if children }
                TagParser.printLineages(non_terminal_children,indentation+2)
            ## I don't think this can be executed from the CLI, I can get it to print if the table in lineages is an empty dict and that's it.
            else:
                print(" "*indentation,id,file=file)



