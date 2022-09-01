#!/usr/bin/python3
""" 
 extract_metadata.py
    Extract SIRM metadata and data from excel workbook and JSON files.
    
 Usage:
    extract_metadata.py <metadata_source>... [--delete <metadata_section>...] [options]
    extract_metadata.py --help

    <metadata_source> - input metadata source as csv/json filename or xlsx_filename[:worksheet_name|regular_expression]. "#export" worksheet name is the default.

 Options:
    --help                              - show this help documentation.
    --output <filename_json>            - output json filename.
    --compare <filename_json>           - compare extracted metadata to given JSONized metadata.
    --convert <source>                  - conversion directives worksheet name, regular expression, csv/json filename, or xlsx_filename:[worksheet_name|regular_expression] [default: #convert].
    --end-convert <source>              - apply conversion directives after all metadata merging. Requires csv/json filename or xlsx_filename:[worksheet_name|regular_expression].
    --tagging <source>                  - tagging directives worksheet name, regular expression, csv/json filename, or xlsx_filename:[worksheet_name|regular_expression] [default: #tagging].
    --save-directives <filename_json>   - output filename with conversion and tagging directives in JSON format.
    --save-export <filetype>            - output export worksheet with suffix "_export" and with the indicated xlsx/csv format extension.
    --show <show_option>                - show a part of the metadata. See options below.
    --delete <metadata_section>...      - delete a section of the JSONized metadata. Section format is tableKey or tableKey,IDKey or tableKey,IDKey,fieldName. These can be regular expressions.
    --keep <metadata_tables>            - only keep the selected tables.  Delete the rest.  Table format is tableKey,tableKey,... The tableKey can be a regular expression.
    --silent                            - print no warning messages.
    --cv <filename_json>                - controlled vocabulary that describes the structure of the data. Needed to utulize field tracking functionality.

Show Options:
  tables    - show tables in the extracted metadata.
  lineage   - show parent-child lineages per table.
  all       - show every option.

Regular Expression Format:
  Regular expressions have the form "r'...'" on the command line.
  The re.match function is used, which matches from the beginning of a string, meaning that a regular expression matches as if it starts with a "^".

 Directives JSON Format:
   {
    "conversion" : { table : { field :  { "exact"|"regex"|"levenshtein"|"exact-unique"|"regex-unique"|"levenshtein-unique" :
                      { field_value : { "assign" : { field : value,... }, "append" : { field : value,... }, "prepend" : { field : value,... },
                                        "regex" : { field : regex_pair,... }, "delete" : [ field,... ], "rename" : { old_field : new_field } } } } } }
    "tagging" : [ { "header_tag_descriptions" : [ { "header" : column_description, "tag" : tag_description, "required" : true|false } ],   "exclusion_test" : exclusion_value, "insert" : [ [ cell_content, ... ] ] } ]
   }

"""
#
#   Written by Hunter Moseley, 06/18/2014
#   Copyright Hunter Moseley, 06/18/2014. All rights reserved.
#
#   Hugely Revised (Over 75%) by Hunter Moseley, 08/29/2020
#   Copyright Hunter Moseley, 08/29/2020. All rights reserved.
#


## TODO 
## When creating unit tests make sure to have a check on all pandas read ins that nan values become empty strings.
## Possibly add a step at the end that makes sure all records id field matches the dict key value.
## Possibly use controlled vocabulary to create field tracking JSON. This is done, but is untested.
## Make sure verify_metadata checks for project.id and study.id in subject, samples, and factors.
## Possibly add an option to enumerate id's that aren't unique.
## Possibly check to see if a record's id is already in use while parsing, and print warning to user that 2 records in Excel have same id.
## This is tricky with child tags because the parent is added with the child, so detecting an already existing record might be where the child added a placeholder parent record.
## Should an output filename be required? You can run the program and get nothing out as is.
## Be sure to deal with errors in order. Something like a duplicated header can then make a conversion not match, 
## so deal with the header and then both errors go away.
## Let metadata sources be URLs
## Think about handling column based data, transpose rows and columns and then read in.
## Possibly add a #max-distance tag for levenshtein comaprison to put a minimum distance that must be acheived to be considered a match.
## Possibly add an option not to print warnings about unused conversion directives.
## Document the conversion tag precedence, both that exact goes first, then regex, then levens, and that top most conversions go first.
## Try and make the field tracking a tag isntead of being in CV.
## unique = 3 different names
## Test what happens when tracking_on specifices a field that the records already have in the table. Does it overwrite? #sample%track_on.sample.id

import os.path
import copy
import sys
import re
import collections
import pathlib

import json
import pandas
import docopt
import jellyfish

import copier
import cythonized_tagSheet

silent = False

def main() :
    args = docopt.docopt(__doc__)
    
    if args["--silent"]:
        global silent
        silent = True

    if args["--cv"]:
        with open(args["--cv"],'r') as jsonFile :
            controlledVocabulary = json.load(jsonFile)
        ## TODO add CV validation.
        
        tagParser = TagParser(controlledVocabulary)
    else:
        tagParser = TagParser()
        

    if any([True for arg in sys.argv if arg == "--convert"]):
        convertDefaulted = False
    else:
        convertDefaulted = True
        
    if any([True for arg in sys.argv if arg == "--tagging"]):
        taggingDefaulted = False
    else:
        taggingDefaulted = True

    for metadataSource in args["<metadata_source>"]:
        tagParser.readMetadata(metadataSource, args["--tagging"], taggingDefaulted, args["--convert"], convertDefaulted, args["--save-export"])

    ## --end-convert is needed so that the merged metadata files can all be converted after being merged together.
    ## Without this each metadatasource only gets its own conversion.
    if args["--end-convert"] != None:
        conversionSource = args["--end-convert"]
        if re.search(r"\.xls[xm]?$", conversionSource):
            conversionSource += ":#convert"

        conversionDirectives = tagParser.readDirectives(conversionSource, "conversion")
        tagParser.convert(conversionDirectives)

    if getattr(tagParser, "unusedConversions", None) != None and not silent:
        for (tableKey, fieldKey, comparisonType, conversionID) in tagParser.unusedConversions:
            print("Warning: conversion directive #" + tableKey + "." + fieldKey + "." + comparisonType + "." + conversionID + " never matched.", file=sys.stderr)

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
        if getattr(tagParser, "conversionDirectives", None) != None or getattr(tagParser, "taggingDirectives", None) != None:
            directives = {}
            if getattr(tagParser, "conversionDirectives", None) != None:
                directives["conversion"] = tagParser.conversionDirectives

            if getattr(tagParser, "taggingDirectives", None) != None:
                directives["tagging"] = tagParser.taggingDirectives

            with open(args["--save-directives"],'w') as jsonFile :
                jsonFile.write(json.dumps(directives, sort_keys=True, indent=2, separators=(',', ': ')))
        else:
            print("There are no directives to save.",file=sys.stderr)


def xstr(s) :
    """RETURNS str(s) or a "" if PARAMETER s is None

    :param s:
    :type s: :py:class:`str` or :py:obj:`None`
    :return: string
    :rtype: :py:class:`str`
    """
    return "" if s is None else str(s)

    

class Evaluator(object) :
    """Creates object that calls eval with a given record."""

    evalDetector = re.compile(r'\s*eval\((.*)\)\s*$')
    fieldDetector = re.compile(r'\#(.*)\#$')
    reDetector = re.compile(r"r[\"'](.*)[\"']$")
    evalSplitter = re.compile(r'(\#[^#]+\#)')

    def __init__(self, evalString, useFieldTests = True, listAsString = False) :
        """Initializer

        :param :py:class:`str` evalString: stripped of the "eval(" and ")" parts.
        :param :py:class:`str` name: name for the code object generated.
        :param :py:class:`bool` useFieldTests: whether to use field tests in field name conversion.
        :param :py:class:`bool` listAsString: whether to convert a list into a single string.
        """

        self.evalString = evalString
        self.useFieldTests = useFieldTests
        self.listAsString = listAsString

        tokenList = [token for token in re.split(Evaluator.evalSplitter, evalString) if token != "" and token != None]
        self.fieldTests = {}
        self.requiredFields = []
        finalTokenList = []
        regexCount = 1
        reCopier = copier.Copier()
        for token in tokenList:
            if reCopier(re.match(Evaluator.fieldDetector, token)):
                fieldString = reCopier.value.group(1)
                if reCopier(re.match(Evaluator.reDetector, fieldString)):
                    fieldString = "REGEX" + str(regexCount)
                    regexCount += 1
                    finalTokenList.append(fieldString)
                    self.fieldTests[fieldString] = re.compile(reCopier.value.group(1))
                else:
                    finalTokenList.append(fieldString.replace("%", "_PERCENT_"))
                    self.requiredFields.append(fieldString)
            else:
                finalTokenList.append(token)

        if not useFieldTests:
            self.requiredFields.extend(self.fieldTests.keys())

        self.code = compile("".join(finalTokenList), self.evalString, "eval")

    def evaluate(self, record):
        """RETURN  eval results for the given record.

        :param :py:class:`dict` record:
        :return: value
        :rtype: :py:class:`str` or :py:class:`list`
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

    def hasRequiredFields(self, record):
        """RETURNS whether the record has all required fields.

        :param :py:class:`dict` record:
        :return: boolean
        :rtype: :py:class:`bool`
        """
        return all(field in record for field in self.requiredFields) and ( not self.useFieldTests or not self.fieldTests or \
               all([ len([(fieldName, value) for field, value in record.items() if re.search(fieldTest,field)]) == 1 for fieldName, fieldTest in self.fieldTests.items() ]) )

    @staticmethod
    def isEvalString(evalString):
        """Tests whether the evalString is of the form r"^eval(...)$"

        :param evalString:
        :return: matchObject
        :rtype: :py:class:`re.Match` or :py:obj:`None`
        """
        return re.match(Evaluator.evalDetector, evalString)

class Operand(object) :
    """Class of objects that create string operands for concatenation operations."""
    def __init__(self, value) :
        """Initializer

        :param value:
        :type value: :py:class:`str` or :py:class:`int`
        """
        self.value = value
    
    def __call__(self, record, row) :
        """RETURNS a string.

        :param :py:class:`dict` record:
        :param :py:class:`pandas.core.series.Series` row:
        :return: string
        :rtype: :py:class:`str`
        """
        pass
    
class LiteralOperand(Operand) :
    """Represents string literal operands."""
    def __call__(self, record, row) :
        """RETURNS string value

        :param :py:class:`dict` record:
        :param :py:class:`pandas.core.series.Series` row:
        :return: string
        :rtype: :py:class:`str`
        """
        return self.value

class VariableOperand(Operand) :
    """Represents #table.record%attribute variable operands."""
    def __call__(self, record, row) :
        """RETURNS record field value.

        :param :py:class:`dict` record:
        :param :py:class:`pandas.core.series.Series` row:
        :return: string
        :rtype: :py:class:`str`
        """
        return record[self.value]

class ColumnOperand(Operand) :
    """Represents specific worksheet cells in a given column as operands."""
    def __call__(self, record, row) :
        """RETURNS column value in the given row.

        :param :py:class:`dict` record:
        :param :py:class:`pandas.core.series.Series` row:
        :return: string
        :rtype: :py:class:`str`
        """
        return xstr(row.iloc[self.value]).strip()

class FieldMaker(object) :
    """Creates objects that convert specific information from a worksheet row into a field via concatenation of a list of operands."""
    def __init__(self, field) :
        """Initializer

        :param :py:class:`str` field:
        """
        self.field = field
        self.operands = []

    def create(self, record, row) :
        """Creates field-value and adds to record using PARAMETERS row and record.

        :param :py:class:`dict` record:
        :param :py:class:`pandas.core.series.Series` row:
        :return: value
        :rtype: :py:class:`str`
        """
        value = ""
        for operand in self.operands :
            value += operand(record, row)

        record[self.field] = value

        return value

    def shallowClone(self) :
        """RETURNS clone with shallow copy of operands.

        :return: clone
        :rtype: :class:`FieldMaker`
        """
        clone = FieldMaker(self.field)
        clone.operands = self.operands
        return clone


class ListFieldMaker(FieldMaker) :
    """Creates objects that convert specific information from a worksheet row into a list field via appending of a list of operands."""

    def create(self, record, row) :
        """Creates field-value and adds to record using PARAMETERS row and record.

        :param :py:class:`dict` record:
        :param :py:class:`pandas.core.series.Series` row:
        :return: value
        :rtype: :py:class:`list`
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
    def shallowClone(self) :
        """RETURNS clone with shallow copy of operands.

        :return: clone
        :rtype: :class:`ListFieldMaker`
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
    def child(example, table, parentIDIndex) :
        """RETURNS child object derived from a example object.

        :param :class:`RecordMaker` example: example object with global literal fields.
        :param :py:class:`str` table: table type of record
        :param :py:class`int` parentIDIndex: column index for parentID
        :return: child
        :rtype: :class:`RecordMaker`
        """
        child = RecordMaker()
        child.table = table
        child.fieldMakers = [ maker.shallowClone() for maker in example.fieldMakers ]
        reCopier = copier.Copier()
        for maker in child.fieldMakers :
            if reCopier(re.match('(\w*)\.(.*)$', maker.field)) != None and reCopier.value.group(1) == table :
                maker.field = reCopier.value.group(2)
        child.addField(table,"parentID")
        child.addColumnOperand(parentIDIndex)
        
        return child

    def create(self, row) :
        """RETURNS record created from given row.

        :param :py:class:`pandas.core.series.Series` row:
        :return: tableRecordTuple
        :rtype: :py:class:`tuple`
        """
        record = {}
        for fieldMaker in self.fieldMakers :
            fieldMaker.create(record, row) 
        return self.table, record

    def addField(self, table, field, fieldMakerClass = FieldMaker) :
        """Creates and adds new FieldMaker object.

        :param :py:class:`str` table: table type of record
        :param :py:class:`str` field: field name
        :param fieldMakerClass: field maker class to use
        :type fieldMakerClass: :obj:`FieldMaker` or :obj:`ListFieldMaker`
        """
        if self.table == "" :
            self.table = table
        field = self.properField(table,field)
        self.fieldMakers.append(fieldMakerClass(field))

    def addGlobalField(self, table, field, literal, fieldMakerClass = FieldMaker) :
        """Creates and adds new FieldMaker with literal operand that will be used as global fields for all records created from a row.

        :param :py:class:`str` table: table type of record
        :param :py:class:`str` field: field name
        :param :py:class:`str` literal: literal value of the field
        :param fieldMakerClass: field maker class to use
        :type fieldMakerClass: :obj:`FieldMaker` or :obj:`ListFieldMaker`
        """
        field = table + "." + field
        self.fieldMakers.append(fieldMakerClass(field))
        self.fieldMakers[-1].operands.append(LiteralOperand(literal))

    def addVariableOperand(self, table, field) :
        """Add PARAMETER field as a variable operand to the last FieldMaker.

        :param :py:class:`str` table: table type of record
        :param :py:class:`str` field: field name
        """
        field = self.properField(table,field)
        self.fieldMakers[-1].operands.append(VariableOperand(field))
    
    def addLiteralOperand(self, literal) :
        """Add PARAMETER literal as an operand to the last FieldMaker.

        :param :py:class:`str` literal: literal value to append.
        """
        self.fieldMakers[-1].operands.append(LiteralOperand(literal))

    def addColumnOperand(self, columnIndex) :
        """Add PARAMETER columnIndex as a column variable operand to the last FieldMaker.

        :param :py:class:`int` columnIndex:
        """
        self.fieldMakers[-1].operands.append(ColumnOperand(columnIndex))

    def isInvalidDuplicateField(self, table, field, fieldMakerClass):
        """RETURNS whether a given table.field is an invalid duplicate in the current RecordMaker.

        :param :py:class:`str` table: table type of record
        :param :py:class:`str` field: field name
        :param fieldMakerClass: field maker class to use
        :type fieldMakerClass: :obj:`FieldMaker` or :obj:`ListFieldMaker`
        """
        field = self.properField(table,field)
        return (fieldMakerClass == FieldMaker and self.hasShortField(field)) or len([ index for index in range(len(self.fieldMakers)) if self.fieldMakers[index].field == field and not isinstance(self.fieldMakers[index], ListFieldMaker) ]) > 0

    def hasField(self, table, field, offset=0) :
        """RETURNS whether a given table.field exists in the current RecordMaker.

        :param :py:class:`str` table: table type of record
        :param :py:class:`str` field: field name
        :param :py:class:`int` offset: offset from end to stop looking for #table.field.
        """
        field = self.properField(table,field)
        return self.hasShortField(field, offset) 

    def hasShortField(self, field, offset=0) :
        """RETURNS whether a given field exists in the current RecordMaker.

        :param :py:class:`str` field: field name
        :param :py:class:`int` offset: offset from end to stop looking for #table.field.
        """
        return len([ index for index in range(len(self.fieldMakers)-offset) if self.fieldMakers[index].field == field ]) > 0 

    def isLastField(self, table, field) :
        """RETURNS whether the last FieldMaker is for PARAMETERS table.field.

        :param :py:class:`str` table: table type of record
        :param :py:class:`str` field: field name
        :return: boolean
        :rtype: :py:class:`bool`
        """
        field = self.properField(table,field)
        return self.fieldMakers[-1].field == field

    def hasValidID(self) :
        """RETURNS whether there is a valid id field.

        :return: boolean
        :rtype: :py:class:`bool`
        """
        return self.hasShortField("id") and type(self.shortField("id").operands[0]) is ColumnOperand and not type(self.shortField("id")) == ListFieldMaker

    def properField(self, table, field) :
        """RETURNS proper field name based on given PARAMETER table and field and internal table type of record.

        :param :py:class:`str` table: table type of record
        :param :py:class:`str` field: field name
        :return: properName
        :rtype: :py:class:`str`
        """
        if table != self.table :
            field = table + "." + field
        return field

    ## This is currently never called anywhere, so cannot be tested through the CLI.
    def field(self, table, field) :
        """RETURNS FieldMaker for PARAMETERS table.field.

        :param :py:class:`str` table: table type of record
        :param :py:class:`str` field: field name
        :return: fieldMaker
        :rtype: :class:`FieldMaker` or :class:`ListFieldMaker` or :py:obj:`None`
        """
        field = self.properField(table,field)
        return self.shortField(field)

    def shortField(self, field) :
        """RETURNS FieldMaker for PARAMETER field.

        :param :py:class:`str` field: field name
        :return: fieldMaker
        :rtype: :class:`FieldMaker` or :class:`ListFieldMaker` or :py:obj:`None`
        """
        for fieldMaker in self.fieldMakers :
            if fieldMaker.field == field :
                return fieldMaker
    

class TagParserError(Exception):
    """Exception class for errors thrown by TagParser."""
    def __init__(self, message, fileName, sheetName, rowIndex, columnIndex, endMessage="") :
        """
        :param :py:class:`str` message:
        :param :py:class:`str` fileName:
        :param :py:class:`str` sheetName:
        :param :py:class:`int` rowIndex:
        :param :py:class:`int` columnIndex:
        """
        if re.search(r"\.xls[xm]?$", fileName):
            cellName = TagParserError.columnName(columnIndex) + str(rowIndex+1)
        else:
            cellName = "col " + str(columnIndex+1) + ", row " + str(rowIndex+1)

        self.value = message + " at cell \"" + fileName + ":" + sheetName + "[" + cellName + "]\"" + endMessage
        
    @staticmethod
    def columnName(columnIndex) :
        """RETURNS Excel-style column name for PARAMETER columnIndex (integer).

        :param :py:class:`int` columnIndex:
        :return: name of column
        :rtype: :py:class:`str`
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
    
    def __init__(self, cv = {}):
        self.extraction = {}
        self._createTrackingFromCV(cv)

    reDetector = re.compile(r"r[\"'](.*)[\"']$")
    
    def _createTrackingFromCV(self, cv = {}):
        """Creates field tracking data members from controlled vocabulary.
        
        :param :py:class:`dict` cv: controlled vocabulary JSON
        """
        
        ## Find the tracking fields and create data structures to handle the tracking.
        self.tablesAndFieldsToTrack = {}
        self.tableRecordsToAddTo = {}
        self.trackedFieldsDict = {}
        if cv:
            for tagfieldScopeRecordID, tagfieldScopeRecordAttributes in cv["tagfield_scope"].items():
                if "tracking" in tagfieldScopeRecordAttributes["scope_type"]:
                    fieldToAdd = tagfieldScopeRecordAttributes["tagfield.id"]
                        
                    self.trackedFieldsDict[fieldToAdd] = ""
                    
                    tableAndField = fieldToAdd.split(".")
                    tableToTrack = tableAndField[0]
                    fieldToTrack = tableAndField[1]
                    if tableToTrack in self.tablesAndFieldsToTrack:
                        self.tablesAndFieldsToTrack[tableToTrack].add(fieldToTrack)
                    else:
                        self.tablesAndFieldsToTrack[tableToTrack] = set([fieldToTrack])
                    
                    for table in tagfieldScopeRecordAttributes["table"]:
                        if table in self.tableRecordsToAddTo:
                            self.tableRecordsToAddTo[table].add(fieldToAdd)
                        else:
                            self.tableRecordsToAddTo[table] = set([fieldToAdd])
        

    @staticmethod
    def _isEmptyRow(row) :
        """RETURNS True if PARAMETER row is empty.

        :param :py:class:`pandas.core.series.Series` row:
        :return: boolean
        :rtype: :py:class:`bool`
        """
        for cell in row :
            if xstr(cell).strip() != "" :
                return False
        
        return True

    def _determineTableField(self, params) :
        """RETURNS table and field based on PARAMETER params tuple and last table and field set.

        :param :py:class:`tuple` params: tag parameters
        :return: tableFieldTuple
        :rtype: :py:class:`tuple`
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


    cellSplitter = re.compile(r'([*=+;,]|\"[^\"]*\")|\s+')
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
    tableFieldDetector = re.compile(r'#(\w*)\.(\w+)$')
    attributeDetector = re.compile('#\%(\w+)$')
    trackOnFieldDetector = re.compile(r'#(\w*)\%track\.(\w+\.\w+)$')
    trackOnFieldAttributeDetector = re.compile(r'#(\w*)\%track\.(\w+\.\w+%\w+)$')
    trackOffFieldDetector = re.compile(r'#(\w*)\%untrack\.(\w+\.\w+)$')
    trackOffFieldAttributeDetector = re.compile(r'#(\w*)\%untrack\.(\w+\.\w+%\w+)$')
    def _parseHeaderCell(self, recordMakers, cellString, childWithoutID) :
        """Parses header cell and RETURNS current state of ID inclusion of current child record

        :param :py:class`list` recordMakers: list of recordMaker objects
        :param :py:class`str` cellString: string of worksheet cell.
        :param :py:class:`bool` childWithoutID: entering state of ID inclusion of current child record.
        :return: childWithoutID exiting state of ID inclusion of current child record.
        :rtype: :py:class:`bool`
        """
        if self.columnIndex == 0 and (re.search(TagParser.childDetector, cellString)) :
            raise TagParserError("#.%child tag not allowed in first column", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
        if self.columnIndex != 0 and re.search('#tags', cellString) :
            raise TagParserError("#tags only allowed in first column", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
            
        reCopier = copier.Copier()
        tokens = [ x for x in re.split(TagParser.cellSplitter, cellString) if x != "" and x != None ]
        tokens = [ x if reCopier(re.match(TagParser.stringExtractor, x)) == None else reCopier.value.group(1) for x in tokens ]
        
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
            elif reCopier(re.match(TagParser.childFieldAttributeDetector, token)) or reCopier(re.match(TagParser.childFieldDetector, token)) :  # #table%child.field.attribute combinations
                if not recordMakers[1].hasValidID() :
                    raise TagParserError("no id field in parent record", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                table, field = self._determineTableField(reCopier.value.groups())
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
            elif reCopier(re.match(TagParser.tableFieldAttributeDetector, token)) or reCopier(re.match(TagParser.tableFieldDetector, token)) or reCopier(re.match(TagParser.attributeDetector, token)) : #table.field.attribute combinations
                table, field = self._determineTableField(reCopier.value.groups())
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
            elif reCopier(re.match(TagParser.trackOnFieldDetector, token)) or reCopier(re.match(TagParser.trackOnFieldAttributeDetector, token)) :
                tableToAddTo, tableAndField = self._determineTableField(reCopier.value.groups())
                split = tableAndField.split(".")
                fieldTable = split[0]
                field = split[1]
                if fieldTable in self.tablesAndFieldsToTrack:
                    self.tablesAndFieldsToTrack[fieldTable].add(field)
                else:
                    self.tablesAndFieldsToTrack[fieldTable] = set([field])
                if tableToAddTo in self.tableRecordsToAddTo:
                    self.tableRecordsToAddTo[tableToAddTo].add(tableAndField)
                else:
                    self.tableRecordsToAddTo[tableToAddTo] = set([tableAndField])
                if tableAndField not in self.trackedFieldsDict:
                    self.trackedFieldsDict[tableAndField] = ""
            elif reCopier(re.match(TagParser.trackOffFieldDetector, token)) or reCopier(re.match(TagParser.trackOffFieldAttributeDetector, token)) :
                tableToAddTo, tableAndField = self._determineTableField(reCopier.value.groups())
                split = tableAndField.split(".")
                fieldTable = split[0]
                field = split[1]
                if tableToAddTo in self.tableRecordsToAddTo:
                    self.tableRecordsToAddTo[tableToAddTo].discard(tableAndField)
                    if len(self.tableRecordsToAddTo[tableToAddTo]) == 0:
                        del self.tableRecordsToAddTo[tableToAddTo]
                tableAndFieldInOtherTables = False
                for table, fields in self.tableRecordsToAddTo.items():
                    if tableAndField in fields:
                        tableAndFieldInOtherTables = True
                        break
                if not tableAndFieldInOtherTables:
                    del self.trackedFieldsDict[tableAndField]
                    self.tablesAndFieldsToTrack[fieldTable].discard(field)
                    if len(self.tablesAndFieldsToTrack[fieldTable]) == 0:
                        del self.tablesAndFieldsToTrack[fieldTable]
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


    def _parseHeaderRow(self, row) :
        """Parses PARAMETER header row and RETURNS list of recordMakers.

        :param :py:class:`pandas.core.series.Series` row:
        :return: recordMakers - list of RecordMaker objects.
        :rtype: :py:class:`list`
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

    
    def _parseRow(self, recordMakers, row) :
        """Create new records and add them to the nested extraction dictionary.

        :param :py:class:`list` recordMakers: list of RecordMaker objects.
        :param :py:class:`pandas.core.series.Series` row:
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


    def parseSheet(self, fileName, sheetName, worksheet) :
        """Extracts useful metadata from the worksheet and puts it in the extraction dictionary.

        :param :py:class:`str` fileName:
        :param :py:class:`str` sheetName:
        :param :py:class:`pandas.dataFrame` worksheet:
        """
        self.projectID = ""
        self.studyID = ""
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
            for index in rowsToParse.index:
                self._parseRow(recordMakers, worksheet.loc[index, :])
        
        self.rowIndex = -1


    @staticmethod
    def loadSheet(sheetInfo, isDefaultSearch=False, silent=False):
        """Load and RETURN worksheet as a pandas data frame.

        :param :py:class:`str` sheetInfo: filename and sheetname (if needed).
        :param :py:class:`bool` isDefaultSearch: whether or not the sheetInfo is using default values, determines whether to print some messages
        :return: dataFrameTuple (fileName, sheetName, dataFrame).
        :rtype: :py:class:`tuple` or :py:obj:`None`
        """
        reCopier = copier.Copier()
        if reCopier(re.search(r"^(.*\.xls[xm]?):(.*)$", sheetInfo)):
            if os.path.isfile(reCopier.value.group(1)):
                fileName = reCopier.value.group(1)
                sheetName = reCopier.value.group(2)
                workbook = pandas.ExcelFile(fileName)
                
                ## Convert the sheetname to a regular expression pattern so users can specify a sheetname using a regular expression.
                if re.match(TagParser.reDetector, sheetName):
                    sheetDetector = re.compile(re.match(TagParser.reDetector, sheetName)[1])
                else:
                    sheetDetector = re.compile("^" + re.escape(sheetName) + "$")

                for sheetName in workbook.sheet_names:
                    if re.search(sheetDetector, sheetName) != None:
                        dataFrame = pandas.read_excel(workbook, sheetName, header=None, index_col=None, dtype=str)
                        if len(dataFrame) == 0:
                            print("There is no data in worksheet \"" + sheetInfo + "\".", file=sys.stderr)
                            return None
                        else:
                            ## Empty cells are read in as nan by default, replace with empty string.
                            dataFrame = dataFrame.fillna("")
                            return (fileName, sheetName, dataFrame)
                if not isDefaultSearch:
                    print("r'" + sheetDetector.pattern + "' did not match any sheets in \"" + fileName + "\".", file=sys.stderr)
            else:
                print("Excel workbook \"" + reCopier.value.group(1) + "\" does not exist.", file=sys.stderr)
        elif re.search(r"\.csv$", sheetInfo):
            if pathlib.Path(sheetInfo).exists():
                try:
                    dataFrame = pandas.read_csv(sheetInfo, header=None, index_col=None, dtype=str)
                except pandas.errors.EmptyDataError:
                    print("There is no data in csv file \"" + sheetInfo + "\".", file=sys.stderr)
                    dataFrame = pandas.DataFrame()
                else:
                    ## I don't think there is a way to read in a csv file with no length. All my attempts resulted in an error.
                    ## Thus this is not testable from the CLI.
                    if len(dataFrame) == 0:
                        print("There is no data in csv file \"" + sheetInfo + "\".", file=sys.stderr)
                    else:
                        dataFrame = dataFrame.fillna("") # Empty cells are read in as nan by default. Therefore replace with empty string.
                        fileName = sheetInfo
                        sheetName = ""
                        return (fileName, sheetName, dataFrame)
            else:
                print("The csv file \"" + sheetInfo + "\" does not exist.", file=sys.stderr)
        else:
            raise Exception("Invalid worksheet identifier \"" + sheetInfo + "\" passed into function.")

        return None


    @staticmethod
    def hasFileExtension(string):
        """Tests whether the string has a file extension.

        :param :py:class:`str` string:
        :return: boolean
        :rtype: :py:class:`bool`
        """
        return ".xls" in string or ".xlsx" in string or ".xlsm" in string or ".csv" in string or ".json" in string

    def readMetadata(self, metadataSource, taggingSource, taggingDefaulted, conversionSource, convertDefaulted, saveExtension=None):
        """Reads metadata from source.

        :param :py:class:`str` metadataSource:  metadata source given as a filename with possibly a sheetname if appropriate.
        :param :py:class:`str` taggingSource:  tagging source given as a filename and/or sheetname
        :param :py:class:`bool` taggingDefaulted:  whether the tagging source is the default value or not, passed to readDirectives for message printing
        :param :py:class:`str` conversionSource: conversion source given as a filename and/or sheetname.
        :param :py:class:`bool` convertDefaulted:  whether the convert source is the default value or not, passed to readDirectives for message printing
        """
        reCopier = copier.Copier()
        if not TagParser.hasFileExtension(taggingSource) and reCopier(re.search(r"(.*\.xls[xm]?)", metadataSource)):
            taggingSource = reCopier.value.group(1) + ":" + taggingSource
        elif re.search(r"\.xls[xm]?$", taggingSource):
            taggingSource += ":#tagging"

        if not TagParser.hasFileExtension(conversionSource) and reCopier(re.search(r"(.*\.xls[xm]?)", metadataSource)):
            conversionSource = reCopier.value.group(1) + ":" + conversionSource
        elif re.search(r"\.xls[xm]?$", conversionSource):
            conversionSource += ":#convert"

        if re.search(r"\.xls[xm]?$", metadataSource):
            metadataSource += ":#export"

        taggingDirectives = self.readDirectives(taggingSource, "tagging", taggingDefaulted) if TagParser.hasFileExtension(taggingSource) else None
        ## Structure of conversionDirectives: {table_key:{field_key:{comparison_type:{field_value:{directive:{field_key:directive_value}}}}}} 
        ## The directive value is the new value to give the field or regex, regex is a list, assign is a string.
        ## unique is handled by having "-unique" added to comparison type key, so there is "exact-unique" and "exact".
        conversionDirectives = self.readDirectives(conversionSource, "conversion", convertDefaulted) if TagParser.hasFileExtension(conversionSource) else None

        if re.search(r"\.json$", metadataSource):
            with open(metadataSource, 'r') as jsonFile:
                newMetadata = json.load(jsonFile)
            currentMetadata = self.extraction
            self.extraction = newMetadata
        else:
            currentMetadata = self.extraction
            newMetadata = {}
            self.extraction = newMetadata
            dataFrameTuple = TagParser.loadSheet(metadataSource)

            if dataFrameTuple:
                dataFrame = self.tagSheet(taggingDirectives, dataFrameTuple[2])
                dataFrameTuple = (dataFrameTuple[0], dataFrameTuple[1], dataFrame)

                if saveExtension != None:
                    self.saveSheet(*dataFrameTuple, saveExtension)

                ## Ultimately modifies self.extraction.
                self.parseSheet(*dataFrameTuple)

        if self.extraction:
            self.convert(conversionDirectives)

        newMetadata = self.extraction
        self.extraction = currentMetadata
        self.merge(newMetadata)


    def saveSheet(self, fileName, sheetName, worksheet, saveExtension):
        """Save given worksheet in the given format.

        :param :py:class:`str` fileName: original worksheet filename
        :param :py:class:`str` sheetName:
        :param :py:class:`pandas.dataFrame` worksheet:
        :param :py:class:`str` saveExtension: csv or xlsx
        """
        baseName = os.path.basename(fileName)
        fileName = baseName.rsplit(".",1)[0] + "_export."
        if saveExtension == "csv":
            fileName += "csv"
            worksheet.to_csv(fileName, header=False, index=False)
        else:
            fileName += "xlsx"
            with pandas.ExcelWriter(fileName, engine = "xlsxwriter") as writer:
                worksheet.to_excel(writer, sheet_name = sheetName, index=False, header=False)

    headerSplitter = re.compile(r'[+]|(r?\"[^\"]*\"|r?\'[^\']*\')|\s+')
    def tagSheet(self, taggingDirectives, worksheet):
        """Add tags to the worksheet using the given tagging directives.

        :param :py:class:`dict` taggingDirectives:
        :param :py:class:`pandas.dataFrame` worksheet:
        :return: worksheet
        :rtype: :py:class:`pandas.dataFrame`
        """
        
        worksheet, wasTaggingDirectiveUsed = cythonized_tagSheet.tagSheet(taggingDirectives, worksheet.to_numpy(), silent)
        
        for i, directive in enumerate(wasTaggingDirectiveUsed):
            if not directive and not silent:
                print("Warning: Tagging directive number " + str(i) + " was never used.", file=sys.stderr)
        
        worksheet = pandas.DataFrame(worksheet)

        return worksheet

    conversionComparisonTypes = [ "exact", "regex", "levenshtein" ]
    def _parseConversionSheet(self, fileName, sheetName, worksheet):
        """Extracts conversion directives from a given worksheet.

        "conversion" : { table : { field :  { "exact"|"regex"|"levenshtein"|"exact-unique"|"regex-unique"|"levenshtein-unique" :
                          { field_value : { "assign" : { field : value,... }, "append" : { field : value,... }, "prepend" : { field : value,... },
                                        "regex" : { field : regex_pair,... }, "delete" : [ field,... ], "rename" : { old_field : new_field } } } } } }

        :param :py:class:`str` fileName:
        :param :py:class:`str` sheetName:
        :param :py:class:`pandas.dataFrame` worksheet:
        """
        self.columnIndex = -1
        self.rowIndex = -1
        self.fileName = fileName
        self.sheetName = sheetName

        aColumn = worksheet.iloc[:, 0]

        parsing = False
        reCopier = copier.Copier()
        for self.rowIndex in range(len(aColumn)):
            try:
                if re.match('#tags$', xstr(aColumn.iloc[self.rowIndex]).strip()):
                    parsing = True
                    valueIndex = -1
                    comparisonIndex = -1
                    comparisonType = "regex|exact"
                    userSpecifiedType = False
                    isUnique = "-unique"
                    uniqueIndex = -1
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
                        if reCopier(re.match('\s*#(\w+)\.(\w+|\w+%\w+|\w+\.id)\.value\s*$', cellString)):
                            valueIndex = self.columnIndex
                            table = reCopier.value.group(1)
                            fieldID = reCopier.value.group(2)
                        elif reCopier(re.match('\s*#(\w+)?\.(\w+|\w+%\w+|\w+\.id)\.delete\s*$', cellString)):
                            if valueIndex == -1:
                                raise TagParserError("#table_name.field_name.delete in column before #table_name.field_name.value", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                            if reCopier.value.group(1) is not None and reCopier.value.group(1) != table:
                                raise TagParserError("Table name does not match between #table_name.field_name.value and #table_name.field_name.delete conversion tags", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                            deletionFields.append(reCopier.value.group(2))
                        elif reCopier(re.match('\s*#(\w+)?\.(\w+|\w+%\w+|\w+\.id)\.rename\.(\w+|\w+%\w+|\w+\.id)\s*$', cellString)):
                            if valueIndex == -1:
                                raise TagParserError("#table_name.field_name.rename in column before #table_name.field_name.value", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                            if reCopier.value.group(1) is not None and reCopier.value.group(1) != table:
                                raise TagParserError("Table name does not match between #table_name.field_name.value and #table_name.field_name.rename conversion tags", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                            if reCopier.value.group(2) == reCopier.value.group(3):
                                raise TagParserError("rename conversion directive renames the field to the same name", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                            renameFieldMap[reCopier.value.group(2)] = reCopier.value.group(3)
                        elif reCopier(re.match('\s*#(\w+)?\.(\w+|\w+%\w+|\w+\.id)\.rename\s*$', cellString)):
                            raise TagParserError("Incorrect rename directive format.  Should be #[table_name].field_name.rename.new_field_name", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                        elif reCopier(re.match('\s*(\*#|#)(\w+)?\.(\w+)\.assign\s*$', cellString)) or reCopier(re.match('\s*(#)(\w+)?\.(\w+|\w+%\w+|\w+\.id)\.assign\s*$', cellString)):
                            if valueIndex == -1:
                                raise TagParserError("#table_name.field_name.assign in column before #table_name.field_name.value", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                            if reCopier.value.group(2) is not None and reCopier.value.group(2) != table:
                                raise TagParserError("Table name does not match between #table_name.field_name.value and #table_name.field_name.assign conversion tags", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                            assignIndeces.append(self.columnIndex)
                            assignFieldTypes.append(reCopier.value.group(1))
                            assignFields.append(reCopier.value.group(3))
                        elif reCopier(re.match('\s*(\*#|#)(\w+)?\.(\w+)\.append\s*$', cellString)) or reCopier(re.match('\s*(#)(\w+)?\.(\w+|\w+%\w+|\w+\.id)\.append\s*$', cellString)):
                            if valueIndex == -1:
                                raise TagParserError("#table_name.field_name.append in column before #table_name.field_name.value", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                            if reCopier.value.group(2) is not None and reCopier.value.group(2) != table:
                                raise TagParserError("Table name does not match between #table_name.field_name.value and #table_name.field_name.append conversion tags", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                            appendIndeces.append(self.columnIndex)
                            appendFieldTypes.append(reCopier.value.group(1))
                            appendFields.append(reCopier.value.group(3))
                        elif reCopier(re.match('\s*(\*#|#)(\w+)?\.(\w+)\.prepend\s*$', cellString)) or reCopier(re.match('\s*(#)(\w+)?\.(\w+|\w+%\w+|\w+\.id)\.prepend\s*$', cellString)):
                            if valueIndex == -1:
                                raise TagParserError("#table_name.field_name.prepend in column before #table_name.field_name.value", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                            if reCopier.value.group(2) is not None and reCopier.value.group(2) != table:
                                raise TagParserError("Table name does not match between #table_name.field_name.value and #table_name.field_name.prepend conversion tags", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                            prependIndeces.append(self.columnIndex)
                            prependFieldTypes.append(reCopier.value.group(1))
                            prependFields.append(reCopier.value.group(3))
                        elif reCopier(re.match('\s*#(\w+)?\.(\w+)\.regex\s*$', cellString)) or reCopier(re.match('\s*#(\w+)?\.(\w+|\w+%\w+|\w+\.id)\.regex\s*$', cellString)):
                            if valueIndex == -1:
                                raise TagParserError("#table_name.field_name.regex in column before #table_name.field_name.value", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                            if reCopier.value.group(1) is not None and reCopier.value.group(1) != table:
                                raise TagParserError("Table name does not match between #table_name.field_name.value and #table_name.field_name.regex conversion tags", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                            regexIndeces.append(self.columnIndex)
                            regexFields.append(reCopier.value.group(2))
                        elif reCopier(re.match('\s*#comparison\s*=\s*(exact|regex|regex\|exact|levenshtein)\s*$', cellString)):
                            comparisonType=reCopier.value.group(1)
                            userSpecifiedType = True
                        elif re.match('\s*#comparison\s*$', cellString):
                            comparisonIndex = self.columnIndex
                        elif re.match('\s*#unique\s*=\s*[Tt]rue\s*$', cellString):
                            isUnique = "-unique"
                        elif re.match('\s*#unique\s*=\s*[Ff]alse\s*$', cellString):
                            isUnique = ""
                        elif re.match('\s*#unique\s*$', cellString):
                            uniqueIndex = self.columnIndex
                        self.columnIndex = -1
                    if valueIndex == -1 or (len(assignIndeces) == 0 and len(appendIndeces) == 0 and len(prependIndeces) == 0 and len(regexIndeces) == 0 and len(deletionFields) == 0 and not renameFieldMap):
                        raise TagParserError("Missing #table_name.field_name.value or #.field_name.assign|append|prepend|regex|delete|rename conversion tags", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                    if "id" in deletionFields:
                        raise TagParserError("Not allowed to delete id fields", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                    if not table in self.conversionDirectives:
                        self.conversionDirectives[table] = {}
                    if not fieldID in self.conversionDirectives[table]:
                        self.conversionDirectives[table][fieldID] = {}
                elif re.match('#ignore$', xstr(aColumn.iloc[self.rowIndex]).strip()):
                    pass
                elif TagParser._isEmptyRow(worksheet.iloc[self.rowIndex, :]):
                    parsing = False
                elif parsing:
                    fieldValue = xstr(worksheet.iloc[self.rowIndex, valueIndex]).strip()
                    if comparisonIndex != -1 and reCopier(xstr(worksheet.iloc[self.rowIndex, comparisonIndex]).strip()) in TagParser.conversionComparisonTypes:
                        localComparisonType = reCopier.value
                        
                    else:
                        if not userSpecifiedType or comparisonType == "regex|exact":
                            localComparisonType = "regex" if re.match(TagParser.reDetector, fieldValue) else "exact"
                        else:
                            localComparisonType = comparisonType
                    
                    if localComparisonType == "regex" and not re.match(TagParser.reDetector, fieldValue):
                        print(TagParserError("Comparison type is indicated as regex, but comparison value is not a regex", self.fileName, self.sheetName, self.rowIndex, valueIndex, " This conversion will be skipped."), file=sys.stderr)
                        # raise TagParserError("Comparison type is indicated as regex, but comparison value is not a regex", self.fileName, self.sheetName, self.rowIndex, valueIndex)
                        continue

                    if uniqueIndex != -1 and re.match("[Tt]rue$", xstr(worksheet.iloc[self.rowIndex, uniqueIndex]).strip()):
                        localUnique = "-unique"
                    elif uniqueIndex != -1 and re.match("[Ff]alse$", xstr(worksheet.iloc[self.rowIndex, uniqueIndex]).strip()):
                        localUnique = ""
                    else:
                        localUnique = isUnique

                    localComparisonType += localUnique

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
                        if reCopier(re.match(r"(r[\"'].*[\"'])\s*,\s*(r[\"'].*[\"'])$",regexFieldValue)):
                            regexFieldMap[regexFields[i]] = [ reCopier.value.group(1), reCopier.value.group(2) ]
                        else:
                            raise TagParserError("#table_name.field_name.regex value is not of the correct format r\"...\",r\"...\".", self.fileName, self.sheetName, self.rowIndex, valueIndex)

                    if not localComparisonType in self.conversionDirectives[table][fieldID]:
                        self.conversionDirectives[table][fieldID][localComparisonType] = {}
                    if not fieldValue in self.conversionDirectives[table][fieldID][localComparisonType]:
                        self.conversionDirectives[table][fieldID][localComparisonType][fieldValue] = {}
                    # elif not silent:
                    #     print(TagParserError("Warning: duplicate conversion directive given", self.fileName, self.sheetName, self.rowIndex, self.columnIndex), file=sys.stderr)
                    if assignFieldMap:
                        if "assign" in self.conversionDirectives[table][fieldID][localComparisonType][fieldValue]:
                            ## If any of the keys in assignFieldMap are already in conversionDirectives then it is a duplicate assign conversion.
                            if any([key in self.conversionDirectives[table][fieldID][localComparisonType][fieldValue]["assign"] for key in assignFieldMap]) and not silent:
                                print(TagParserError("Warning: duplicate assign conversion directive given", self.fileName, self.sheetName, self.rowIndex, self.columnIndex), file=sys.stderr)
                            
                            self.conversionDirectives[table][fieldID][localComparisonType][fieldValue]["assign"].update(assignFieldMap)
                        else:
                            self.conversionDirectives[table][fieldID][localComparisonType][fieldValue]["assign"] = assignFieldMap
                    if appendFieldMap:
                        if "append" in self.conversionDirectives[table][fieldID][localComparisonType][fieldValue]:
                            ## If any of the keys in appendFieldMap are already in conversionDirectives then it is a duplicate append conversion.
                            if any([key in self.conversionDirectives[table][fieldID][localComparisonType][fieldValue]["append"] for key in appendFieldMap]) and not silent:
                                print(TagParserError("Warning: duplicate append conversion directive given", self.fileName, self.sheetName, self.rowIndex, self.columnIndex), file=sys.stderr)
                            
                            self.conversionDirectives[table][fieldID][localComparisonType][fieldValue]["append"].update(appendFieldMap)
                        else:
                            self.conversionDirectives[table][fieldID][localComparisonType][fieldValue]["append"] = appendFieldMap
                    if prependFieldMap:
                        if "prepend" in self.conversionDirectives[table][fieldID][localComparisonType][fieldValue]:
                            ## If any of the keys in prependFieldMap are already in conversionDirectives then it is a duplicate prepend conversion.
                            if any([key in self.conversionDirectives[table][fieldID][localComparisonType][fieldValue]["prepend"] for key in prependFieldMap]) and not silent:
                                print(TagParserError("Warning: duplicate prepend conversion directive given", self.fileName, self.sheetName, self.rowIndex, self.columnIndex), file=sys.stderr)
                            
                            self.conversionDirectives[table][fieldID][localComparisonType][fieldValue]["prepend"].update(prependFieldMap)
                        else:
                            self.conversionDirectives[table][fieldID][localComparisonType][fieldValue]["prepend"] = prependFieldMap
                    if regexFieldMap:
                        if "regex" in self.conversionDirectives[table][fieldID][localComparisonType][fieldValue]:
                            ## If any of the keys in regexFieldMap are already in conversionDirectives then it is a duplicate regex conversion.
                            if any([key in self.conversionDirectives[table][fieldID][localComparisonType][fieldValue]["regex"] for key in regexFieldMap]) and not silent:
                                print(TagParserError("Warning: duplicate regex conversion directive given", self.fileName, self.sheetName, self.rowIndex, self.columnIndex), file=sys.stderr)
                            
                            self.conversionDirectives[table][fieldID][localComparisonType][fieldValue]["regex"].update(regexFieldMap)
                        else:
                            self.conversionDirectives[table][fieldID][localComparisonType][fieldValue]["regex"] = regexFieldMap
                    if deletionFields:
                        if "delete" in self.conversionDirectives[table][fieldID][localComparisonType][fieldValue]:
                            ## If any of fields in deletionFields are already in conversionDirectives then it is a duplicate delete conversion.
                            if any([field in self.conversionDirectives[table][fieldID][localComparisonType][fieldValue]["delete"] for field in deletionFields]) and not silent:
                                print(TagParserError("Warning: duplicate delete conversion directive given", self.fileName, self.sheetName, self.rowIndex, self.columnIndex), file=sys.stderr)
                            
                            self.conversionDirectives[table][fieldID][localComparisonType][fieldValue]["delete"].extend(deletionFields)
                        else:
                            self.conversionDirectives[table][fieldID][localComparisonType][fieldValue]["delete"] = deletionFields
                    if renameFieldMap:
                        if "rename" in self.conversionDirectives[table][fieldID][localComparisonType][fieldValue]:
                            ## If any of the keys in renameFieldMap are already in conversionDirectives then it is a duplicate rename conversion.
                            if any([key in self.conversionDirectives[table][fieldID][localComparisonType][fieldValue]["rename"] for key in renameFieldMap]) and not silent:
                                print(TagParserError("Warning: duplicate rename conversion directive given", self.fileName, self.sheetName, self.rowIndex, self.columnIndex), file=sys.stderr)
                            
                            self.conversionDirectives[table][fieldID][localComparisonType][fieldValue]["rename"].update(renameFieldMap)
                        else:
                            self.conversionDirectives[table][fieldID][localComparisonType][fieldValue]["rename"] = renameFieldMap
            except TagParserError as err:
                print(err.value, file=sys.stderr)
                exit(1)
            ## I don't think this can be triggered from the CLI.
            except:
                print(TagParserError("Internal Parser Error", self.fileName, self.sheetName, self.rowIndex, self.columnIndex), file=sys.stderr)
                raise

        self.rowIndex = -1

    def _parseTaggingSheet(self, fileName, sheetName, worksheet):
        """Extracts tagging Directives from a given worksheet.

            "tagging" : [ { "header_tag_descriptions" : [ { "header" : column_description, "tag" : tag_description, "required" : true|false } ],   "exclusion_test" : exclusion_value, "insert" : [ [ cell_content, ... ] ] } ]

        :param :py:class:`str` fileName:
        :param :py:class:`str` sheetName:
        :param :py:class:`pandas.dataFrame` worksheet:
        """
        self.columnIndex = -1
        self.rowIndex = -1
        self.fileName = fileName
        self.sheetName = sheetName

        aColumn = worksheet.iloc[:, 0]

        parsing = False

        reCopier = copier.Copier()
        self.rowIndex = 0
        currTaggingGroup = None
        while self.rowIndex < len(aColumn):
            try:
                if re.match('#tags$', xstr(aColumn.iloc[self.rowIndex]).strip()):
                    parsing = True
                    headerIndex = -1
                    tagIndex = -1
                    usedHeaders = set()
                    ## If #tags group is twice in a row remove it from the directives.
                    if self.taggingDirectives and "header_tag_descriptions" in self.taggingDirectives[-1] and not self.taggingDirectives[-1]["header_tag_descriptions"]:
                        self.taggingDirectives.pop()
                    currTaggingGroup = { "header_tag_descriptions" : [] }
                    requiredIndex = -1
                    self.taggingDirectives.append(currTaggingGroup)
                    for self.columnIndex in range(1, len(worksheet.iloc[self.rowIndex, :])):
                        cellString = xstr(worksheet.iloc[self.rowIndex, self.columnIndex]).strip()
                        if re.match('\s*#header\s*$', cellString):
                            headerIndex = self.columnIndex
                        elif re.match('\s*#tag\.add\s*$', cellString):
                            tagIndex = self.columnIndex
                        elif re.match('\s*#required\s*$', cellString):
                            requiredIndex = self.columnIndex
                        elif reCopier(re.match('\s*#exclude\s*=\s*(.+)\s*$', cellString)):
                            currTaggingGroup["exclusion_test"]=reCopier.value.group(1)
                    self.columnIndex = -1
                    if headerIndex == -1:
                        raise TagParserError("Missing #header tag", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                    if tagIndex == -1:
                        raise TagParserError("Missing #tag.add tag", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                elif re.match('#ignore$', xstr(aColumn.iloc[self.rowIndex]).strip()):
                    pass
                elif re.match('#insert$', xstr(aColumn.iloc[self.rowIndex]).strip()):
                    ## If #insert is found inside of #tags then it needs to be added to the current tag group, otherwise make a new one.
                    if not parsing:
                        currTaggingGroup = {}
                        self.taggingDirectives.append(currTaggingGroup)
                    ## If "insert" is already in the current tagging group then add to it and don't overwrite it.
                    if not "insert" in currTaggingGroup:
                        currTaggingGroup["insert"] = []
                        currTaggingGroup["insert_multiple"] = False
                        for self.columnIndex in range(1, len(worksheet.iloc[self.rowIndex, :])):
                            cellString = xstr(worksheet.iloc[self.rowIndex, self.columnIndex]).strip()
                            if re.match('\s*#multiple\s*=\s*[Tt]rue\s*$', cellString):
                                currTaggingGroup["insert_multiple"] = True
                            elif re.match('\s*#multiple\s*=\s*[Ff]alse\s*$', cellString):
                                currTaggingGroup["insert_multiple"] = False

                    endTagFound = False
                    while self.rowIndex < len(aColumn)-1:
                        self.rowIndex += 1
                        if re.match('#end$', xstr(aColumn.iloc[self.rowIndex]).strip()):
                            endTagFound = True
                            break
                        currTaggingGroup["insert"].append([xstr(worksheet.iloc[self.rowIndex, self.columnIndex]).strip() for self.columnIndex in range(0, len(worksheet.iloc[self.rowIndex, :]))])

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
                        currTaggingGroup["header_tag_descriptions"].append({ "header" : headerValue, "tag" : newTagValue, "required" : localRequired })
                    elif not silent:
                        print(TagParserError("Warning: duplicate header description provided in tagging directive", self.fileName, self.sheetName, self.rowIndex, self.columnIndex), file=sys.stderr)
            except TagParserError as err:
                print(err.value, file=sys.stderr)
                exit(1)
            ## Not sure you can get to this from the CLI.
            except:
                print(TagParserError("Internal Parser Error", self.fileName, self.sheetName, self.rowIndex, self.columnIndex), file=sys.stderr)
                raise

            self.rowIndex += 1

        ## I'm not sure what this was testing for, presumably empty directives need to be removed.
#        if self.taggingDirectives and not self.taggingDirectives[-1]["header_tag_descriptions"]:
#            self.taggingDirectives.pop()
        
        ## Only keep non empty directives.
        self.taggingDirectives = [directive for directive in self.taggingDirectives if "header_tag_descriptions" in directive and directive["header_tag_descriptions"] or not "header_tag_descriptions" in directive]
        

        self.rowIndex = -1

    def readDirectives(self, source, directiveType, isDefaultSearch=False):
        """Read directives source of a given directive type.

        :param :py:class:`str` source: filename with sheetname (optional).
        :param :py:class:`str` directiveType: either "conversion" or "tagging" to call the correct parsing function
        :param :py:class:`bool` isDefaultSearch: whether or not the source is using default values, passed to loadSheet for message printing
        :return: directives
        :rtype: :py:class:`dict`
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
        elif TagParser.hasFileExtension(source):
            dataFrameTuple = TagParser.loadSheet(source, isDefaultSearch)
            if dataFrameTuple != None:
                if directiveType == "conversion":
                    self.conversionDirectives = {}
                    self._parseConversionSheet(*dataFrameTuple)
                    directives = self.conversionDirectives
                else:
                    self.taggingDirectives = []
                    self._parseTaggingSheet(*dataFrameTuple)
                    directives = copy.deepcopy(self.taggingDirectives)

        return directives

    # @staticmethod
    def _applyConversionDirectives(self, record, recordPath, conversions):
        """Apply conversion directives to the given record.

        :param :py:class:`dict` record: table record
        :param :py:class: `str` record_path: recordPath
        :param :py:class:`dict` conversions: nested dict of field additions and deletions.
        """
        if "assign" in conversions:
            for newField, newValue in conversions["assign"].items():
                if type(newValue) == Evaluator:
                    if newValue.hasRequiredFields(record):
                        record[newField] = newValue.evaluate(record)
                    elif not silent:
                        print("Warning: Field assignment directive \"" + newField + "\" missing required field(s) \"" + ",".join([ field for field in newValue.requiredFields if field not in record]) + "\", or a regular expression matched no fields or more than one.", file=sys.stderr)
                else:
                    ## If this is not a copy when it is a list it has unexpected results.
                    record[newField] = copy.deepcopy(newValue)
                
                if newField in record:
                    fieldPath = recordPath + newField
                    if fieldPath in self.changedRecords:
                        if (("assign" == self.changedRecords[fieldPath]["previous_conversion_type"] and self.changedRecords[fieldPath]["previous_conversion_value"] != record[newField]) or\
                           "append" == self.changedRecords[fieldPath]["previous_conversion_type"] or \
                           "prepend" == self.changedRecords[fieldPath]["previous_conversion_type"] or\
                           "regex" == self.changedRecords[fieldPath]["previous_conversion_type"] or \
                           "delete" == self.changedRecords[fieldPath]["previous_conversion_type"]) and not silent:
                            print("Warning: \"" + newField + "\" in record, " + recordPath + ", was assigned a new value after previously being modified by a different conversion directive.", file=sys.stderr)
                    else:
                        self.changedRecords[fieldPath] = {}
                    
                    self.changedRecords[fieldPath]["previous_conversion_type"] = "assign"
                    self.changedRecords[fieldPath]["previous_conversion_value"] = record[newField]

        if "append" in conversions:
            for newField, newValue in conversions["append"].items():
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
                    if "delete" == self.changedRecords[fieldPath]["previous_conversion_type"] and not silent:
                        print("Warning: The field, \"" + newField + "\", in record, " + recordPath + ", was deleted before being appended to by a different conversion directive.", file=sys.stderr)
                else:
                    self.changedRecords[fieldPath] = {}
                
                self.changedRecords[fieldPath]["previous_conversion_type"] = "append"
                self.changedRecords[fieldPath]["previous_conversion_value"] = record[newField]

        if "prepend" in conversions:
            for newField, newValue in conversions["prepend"].items():
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
                    if "delete" == self.changedRecords[fieldPath]["previous_conversion_type"] and not silent:
                        print("Warning: The field, \"" + newField + "\", in record, " + recordPath + ", was deleted before being prepended to by a different conversion directive.", file=sys.stderr)
                else:
                    self.changedRecords[fieldPath] = {}
                
                self.changedRecords[fieldPath]["previous_conversion_type"] = "prepend"
                self.changedRecords[fieldPath]["previous_conversion_value"] = record[newField]

        if "regex" in conversions:
            for newField, regexPair in conversions["regex"].items():
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
                    if "delete" == self.changedRecords[fieldPath]["previous_conversion_type"] and not silent:
                        print("Warning: The field, \"" + newField + "\", in record, " + recordPath + ", was deleted by a conversion directive before attempting to be modified by a regex conversion directive.", file=sys.stderr)
                    if "assign" == self.changedRecords[fieldPath]["previous_conversion_type"] and not silent:
                        print("Warning: The field, \"" + newField + "\", in record, " + recordPath + ", had a regex substitution applied after previously being assigned a new value by an assignment conversion directive.", file=sys.stderr)
                elif fieldInRecord:
                    self.changedRecords[fieldPath] = {}
                
                if fieldInRecord:
                    self.changedRecords[fieldPath]["previous_conversion_type"] = "regex"
                    self.changedRecords[fieldPath]["previous_conversion_value"] = record[newField]

        if "delete" in conversions:
            for deletedField in conversions["delete"]:
                record.pop(deletedField, None)
                
                fieldPath = recordPath + deletedField
                if fieldPath in self.changedRecords:
                    if ("assign" == self.changedRecords[fieldPath]["previous_conversion_type"] or\
                       "append" == self.changedRecords[fieldPath]["previous_conversion_type"] or \
                       "prepend" == self.changedRecords[fieldPath]["previous_conversion_type"] or\
                       "regex" == self.changedRecords[fieldPath]["previous_conversion_type"] or\
                       "rename" == self.changedRecords[fieldPath]["previous_conversion_type"]) and not silent:
                        print("Warning: The field, \"" + deletedField + "\", in record, " + recordPath + ", was deleted after previously being modified by a different conversion directive.", file=sys.stderr)
                else:
                    self.changedRecords[fieldPath] = {}
                
                self.changedRecords[fieldPath]["previous_conversion_type"] = "delete"
                self.changedRecords[fieldPath]["previous_conversion_value"] = ""

        if "rename" in conversions:
            for oldField,newField in conversions["rename"].items():
                fieldInRecord = False
                if oldField in record:
                    
                    if newField in record:
                        print("Warning: A conversion directive has renamed the field \"" + oldField + "\" to \"" + newField + "\" for record " + recordPath + ", but \"" + newField + "\" already existed in the record, so its value was overwritten.", file=sys.stderr)

                    fieldInRecord = True
                    record[newField] = record[oldField]
                    record.pop(oldField, None)
                    
                
                if not fieldInRecord:
                    fieldPath = recordPath + oldField
                    if fieldPath in self.changedRecords:
                        if "delete" == self.changedRecords[fieldPath]["previous_conversion_type"] and not silent:
                            print("Warning: The field, \"" + oldField + "\", in record, " + recordPath + ", was deleted by a conversion directive, and then a different conversion directive attempted to rename it, but it no longer exists.", file=sys.stderr)
                else:
                    fieldPath = recordPath + newField
                    if fieldPath in self.changedRecords:
                        if "delete" == self.changedRecords[fieldPath]["previous_conversion_type"] and not silent:
                            print("Warning: The field, \"" + newField + "\", in record, " + recordPath + ", was deleted by a conversion directive, but then a rename directive created it again from a different field.", file=sys.stderr)
                    else:
                        self.changedRecords[fieldPath] = {}
                
                    self.changedRecords[fieldPath]["previous_conversion_type"] = "rename"
                    self.changedRecords[fieldPath]["previous_conversion_value"] = record[newField]
                    
                    ## not sure if the old field that was removed should be added or not.
                    # if recordPath + oldField not in self.changedRecords:
                    #     self.changedRecords[recordPath + oldField] = {}
                    
                    # self.changedRecords[recordPath + oldField]["previous_conversion_type"] = "rename"
                    # self.changedRecords[recordPath + oldField]["previous_conversion_value"] = record[newField]


    def _applyExactConversionDirectives(self, tableKey, fieldKey, conversionDirectives, usedRecordTuples, isUnique=True):
        """Tests and applies exact conversion directives

        :param :py:class:`str` tableKey: table name (key)
        :param :py:class:`str` fieldKey: field name (key)
        :param :py:class:`dict` conversionDirectives: nested dict of conversion directives
        :param :py:class:`set`  usedRecordTuples: set of used records
        :param :py:class:`set`  usedConversions: set of used conversion directives
        :param :py:class:`bool` isUnique: are the directives uniquely applied?
        """
        comparisonType = "exact" if not isUnique else "exact-unique"
        
        usedRecordTuples = set()

        if comparisonType in conversionDirectives[tableKey][fieldKey]:
            table = self.extraction[tableKey]
            for idKey, record in table.items():
                if fieldKey in record:
                    fieldValue = record[fieldKey]
                    if type(fieldValue) == list:
                        for specificValue in fieldValue:
                            if specificValue in conversionDirectives[tableKey][fieldKey][comparisonType]:
                                if isUnique and (tableKey, fieldKey, specificValue) not in usedRecordTuples:
                                    self._applyConversionDirectives(record, tableKey + "[" + idKey + "]", conversionDirectives[tableKey][fieldKey][comparisonType][specificValue])
                                    usedRecordTuples.add((tableKey, fieldKey, specificValue))
                                    self.usedConversions.add((tableKey, fieldKey, comparisonType, specificValue))
                                elif not isUnique:
                                    self._applyConversionDirectives(record, tableKey + "[" + idKey + "]", conversionDirectives[tableKey][fieldKey][comparisonType][specificValue])
                                    self.usedConversions.add((tableKey, fieldKey, comparisonType, specificValue))
                                else:
                                    print("Warning: conversion directive #" + tableKey + "." + fieldKey + "." + comparisonType + "." + specificValue + " matches more than one record. Only the first record will be changed. Try #unique=false if all matching records should be changed.", file=sys.stderr)
                    
                    elif fieldValue in conversionDirectives[tableKey][fieldKey][comparisonType]:
                        if isUnique and (tableKey, fieldKey, fieldValue) not in usedRecordTuples:
                            self._applyConversionDirectives(record, tableKey + "[" + idKey + "]", conversionDirectives[tableKey][fieldKey][comparisonType][fieldValue])
                            usedRecordTuples.add((tableKey, fieldKey, fieldValue))
                            self.usedConversions.add((tableKey, fieldKey, comparisonType, fieldValue))
                        elif not isUnique:
                            self._applyConversionDirectives(record, tableKey + "[" + idKey + "]", conversionDirectives[tableKey][fieldKey][comparisonType][fieldValue])
                            self.usedConversions.add((tableKey, fieldKey, comparisonType, fieldValue))
                        else:
                            print("Warning: conversion directive #" + tableKey + "." + fieldKey + "." + comparisonType + "." + fieldValue + " matches more than one record. Only the first record will be changed. Try #unique=false if all matching records should be changed.", file=sys.stderr)



    def _applyRegexConversionDirectives(self, tableKey, fieldKey, conversionDirectives, usedRecordTuples, regexObjects, isUnique=True):
        """Tests and applies regular expression conversion directives.

        :param :py:class:`str` tableKey: table name (key)
        :param :py:class:`str` fieldKey: field name (key)
        :param :py:class:`dict` conversionDirectives: nested dict of conversion directives
        :param :py:class:`set`  usedRecordTuples: set of used records
        :param :py:class:`set`  usedConversions: set of used conversion directives
        :param :py:class:`dict` regexObjects: dict of regex string to regex object
        :param :py:class:`bool` isUnique: are the directives uniquely applied?
        """
        comparisonType = "regex" if not isUnique else "regex-unique"
        
        usedRecordTuples = set()
        
        if comparisonType in conversionDirectives[tableKey][fieldKey]:
            table = self.extraction[tableKey]
            for idKey, record in table.items():
                if fieldKey in record:
                    fieldValue = record[fieldKey]
                    for regexID, regexEntry in conversionDirectives[tableKey][fieldKey][comparisonType].items():
                        if type(fieldValue) == list:
                            for specificValue in fieldValue:
                                if re.search(regexObjects[regexID], specificValue):
                                    if isUnique and (tableKey, fieldKey, specificValue) not in usedRecordTuples:
                                        self._applyConversionDirectives(record, tableKey + "[" + idKey + "]", regexEntry)
                                        usedRecordTuples.add((tableKey, fieldKey, specificValue))
                                        self.usedConversions.add((tableKey, fieldKey, comparisonType, regexID))
                                    elif not isUnique:
                                        self._applyConversionDirectives(record, tableKey + "[" + idKey + "]", regexEntry)
                                        self.usedConversions.add((tableKey, fieldKey, comparisonType, regexID))
                                    else:
                                        print("Warning: conversion directive #" + tableKey + "." + fieldKey + "." + comparisonType + "." + regexID + " matches more than one record. Only the first record will be changed. Try #unique=false if all matching records should be changed.", file=sys.stderr)                       
                        
                        elif re.search(regexObjects[regexID], fieldValue):
                            if isUnique and (tableKey, fieldKey, fieldValue) not in usedRecordTuples:
                                self._applyConversionDirectives(record, tableKey + "[" + idKey + "]", regexEntry)
                                usedRecordTuples.add((tableKey, fieldKey, fieldValue))
                                self.usedConversions.add((tableKey, fieldKey, comparisonType, regexID))
                            elif not isUnique:
                                self._applyConversionDirectives(record, tableKey + "[" + idKey + "]", regexEntry)
                                self.usedConversions.add((tableKey, fieldKey, comparisonType, regexID))
                            else:
                                print("Warning: conversion directive #" + tableKey + "." + fieldKey + "." + comparisonType + "." + regexID + " matches more than one record. Only the first record will be changed. Try #unique=false if all matching records should be changed.", file=sys.stderr)



    def _applyLevenshteinConversionDirectives(self, tableKey, fieldKey, conversionDirectives, usedRecordTuples, isUnique=True):
        """Tests and applies levenshtein conversion directives.

        :param :py:class:`str` tableKey: table name (key)
        :param :py:class:`str` fieldKey: field name (key)
        :param :py:class:`dict` conversionDirectives: nested dict of conversion directives
        :param :py:class:`set`  usedRecordTuples: set of used records
        :param :py:class:`bool` isUnique: are the directives uniquely applied?
        """
        comparisonType = "levenshtein" if not isUnique else "levenshtein-unique"

        if comparisonType in conversionDirectives[tableKey][fieldKey]:
            levenshteinComparisons = collections.defaultdict(dict)
            levenshteinComparisonValues = collections.defaultdict(dict)
            for levID, levEntry in conversionDirectives[tableKey][fieldKey][comparisonType].items():
                for idKey, record in self.extraction[tableKey].items():
                    if fieldKey in record:
                        ## If the comparison field is a list field then calculate the distance between all values in the list and use the smallest for comparison.
                        if type(record[fieldKey]) == list:
                            usableValues = [specificValue for specificValue in record[fieldKey] if (tableKey, fieldKey, specificValue) not in usedRecordTuples]
                            if usableValues:
                                levenshteinDistances = [jellyfish.levenshtein_distance(levID, specificValue) for specificValue in usableValues]
                                levenshteinComparisons[levID][idKey] = min(levenshteinDistances)
                                levenshteinComparisonValues[levID][idKey] = usableValues[min(range(len(levenshteinDistances)), key=levenshteinDistances.__getitem__)]
                        elif (tableKey, fieldKey, record[fieldKey]) not in usedRecordTuples:
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
                ## Only 1 match to min value.
                if sum(levenshteinComparisons[levKey][idKey] == minLevValue for levKey in usableLevIDs) == 1:
                    uniqueForIdKey[idKey] = minLevID

            if isUnique:
                uniqueForLevenshteinID = collections.defaultdict(None)
                for levID in levenshteinComparisons.keys():
                    minIDKey = min(levenshteinComparisons[levID].keys(), key=(lambda k: levenshteinComparisons[levID][k]))
                    minIDValue = levenshteinComparisons[levID][minIDKey]
                    if sum(levenshteinComparisons[levID][idKey] == minIDValue for idKey in levenshteinComparisons[levID]) == 1:
                        uniqueForLevenshteinID[levID] = minIDKey

                for levID, levEntry in conversionDirectives[tableKey][fieldKey][comparisonType].items():
                    if levID in uniqueForLevenshteinID and uniqueForIdKey[uniqueForLevenshteinID[levID]] == levID:
                        self._applyConversionDirectives(self.extraction[tableKey][uniqueForLevenshteinID[levID]], tableKey + "[" + uniqueForLevenshteinID[levID] + "]", levEntry)
                        usedRecordTuples.add((tableKey, fieldKey, levenshteinComparisonValues[levID][uniqueForLevenshteinID[levID]]))
                        self.usedConversions.add((tableKey, fieldKey, comparisonType, levID))
            else:
                for idKey, levID in uniqueForIdKey.items():
                    self._applyConversionDirectives(self.extraction[tableKey][idKey], tableKey + "[" + idKey + "]", conversionDirectives[tableKey][fieldKey][comparisonType][levID])
                    self.usedConversions.add((tableKey, fieldKey, comparisonType, levID))

    def convert(self, conversionDirectives):
        """Applies conversionDirectives to the extracted metadata.

        :param :py:class:`dict` conversionDirectives: nested dict structure of conversion directives
        """
        self.conversionDirectives = conversionDirectives
        if conversionDirectives != None:
            conversionDirectives = copy.deepcopy(conversionDirectives) # Must make deepcopy since regex objects being embedded.

            if getattr(self,"unusedConversions", None) is None:
                self.unusedConversions = set()

            if getattr(self,"usedConversions", None) is None:
                self.usedConversions = set()
                
            # Compile regex objects for comparison.
            regexObjects = {}
            for tableDict in conversionDirectives.values():
                for fieldDict in tableDict.values():
                    if "regex" in fieldDict:
                        regexObjects.update({ regexString : re.compile(re.match(TagParser.reDetector, regexString)[1]) for regexString in  fieldDict["regex"].keys()})
                    if "regex-unique" in fieldDict:
                        regexObjects.update({ regexString : re.compile(re.match(TagParser.reDetector, regexString)[1]) for regexString in  fieldDict["regex-unique"].keys()})

            # Compile regex objects for regex substitution directives.
            for tableDict in conversionDirectives.values():
                for fieldDict in tableDict.values():
                    for comparisonTypeDict in fieldDict.values():
                        for fieldValueDict in comparisonTypeDict.values():
                            if "regex" in fieldValueDict:
                                fieldValueDict["regex"] = { newField : [ re.match(TagParser.reDetector, regexPair[0])[1], re.match(TagParser.reDetector, regexPair[1])[1] ]
                                                            for newField,regexPair in fieldValueDict["regex"].items() }

            # Create Evaluator objects for assign directives with "eval(...)" values.
            reCopier = copier.Copier()
            for tableDict in conversionDirectives.values():
                for fieldDict in tableDict.values():
                    for comparisonTypeDict in fieldDict.values():
                        for fieldValueDict in comparisonTypeDict.values():
                            if "assign" in fieldValueDict:
                                for newField in fieldValueDict["assign"].keys():
                                    if isinstance(fieldValueDict["assign"][newField], str) and reCopier(Evaluator.isEvalString(fieldValueDict["assign"][newField])):
                                        fieldValueDict["assign"][newField] = Evaluator(reCopier.value.group(1))

            self.changedRecords = {}
            usedRecordTuples = set()
            for tableKey in conversionDirectives.keys():
                if tableKey in self.extraction:
                    for fieldKey in conversionDirectives[tableKey].keys():
                        ## These functions ultimately modify records in self.extraction.
                        self._applyExactConversionDirectives(tableKey, fieldKey, conversionDirectives, usedRecordTuples, True) # exact-unique conversions
                        self._applyRegexConversionDirectives(tableKey, fieldKey, conversionDirectives, usedRecordTuples, regexObjects, True) # regex-unique conversions
                        self._applyLevenshteinConversionDirectives(tableKey, fieldKey, conversionDirectives, usedRecordTuples, True) # levenshtein-unique conversions
                        self._applyExactConversionDirectives(tableKey, fieldKey, conversionDirectives, usedRecordTuples, False) # exact conversions
                        self._applyRegexConversionDirectives(tableKey, fieldKey, conversionDirectives, usedRecordTuples, regexObjects, False) # regex conversions
                        self._applyLevenshteinConversionDirectives(tableKey, fieldKey, conversionDirectives, usedRecordTuples, False) # levenshtein conversions

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
                    print("Warning: A conversion directive has set at least 2 records in the \"" + tableKey + "\" table to the same id. The output will have less records than expected.", file=sys.stderr)
            
            self.extraction = translated

            # Identify used and unused conversion directives.
            for tableKey in conversionDirectives.keys():
                for fieldKey in conversionDirectives[tableKey].keys():
                    for comparisonType in conversionDirectives[tableKey][fieldKey]:
                        for conversionID in conversionDirectives[tableKey][fieldKey][comparisonType]:
                            if (tableKey, fieldKey, comparisonType, conversionID) not in self.usedConversions:
                                self.unusedConversions.add((tableKey, fieldKey, comparisonType, conversionID))
                            elif (tableKey, fieldKey, comparisonType, conversionID) in self.unusedConversions:
                                self.unusedConversions.remove((tableKey, fieldKey, comparisonType, conversionID))

    def merge(self, newMetadata):
        """Merges new metadata with current metadata.

        :param :py:class:`dict` newMetadata: new nested dict metadata
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
    def isComparable(value1, value2):
        """Compares the two values first as strings and then as floats if convertable.

        :param :py:class:`str` value1:
        :param :py:class:`str` value2:
        :return: boolean
        :rtype: :py:class:`bool`
        """
        if value1 == value2:
            return True

        try:
            value1 = float(value1)
            value2 = float(value2)
        except ValueError:
            return False

        return value1 == value2 or abs(value1 - value2) / max(abs(value1),abs(value2)) < 0.00000001

    def compare(self, otherMetadata, group_size=5, file=sys.stdout):
        """Compare current metadata to other metadata.

        :param :py:class:`dict` otherMetadata: nested dict metadata
        :return: boolean
        :rtype: :py:class:`bool`
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
                            group = missingIDs[0:group_size]
                            missingIDs = missingIDs[group_size:]
                            print("  ", " ".join(group), file=file)
                    else:
                        return True
                extraIDs = [ idKey for idKey in self.extraction[tableKey].keys() if idKey not in otherMetadata[tableKey] ]
                if extraIDs:
                    different = True
                    if file is not None:
                        print("Table", tableKey, "with extra records:", file=file)
                        while extraIDs:
                            group = extraIDs[0:group_size]
                            extraIDs = extraIDs[group_size:]
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

    def deleteMetadata(self, sections):
        """Delete sections of metadata based on given section descriptions.

        :param :py:class`list` sections: list of sections that are lists of strings.
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

    def findParent(self, parentID):
        """RETURNS parent record for given parentID.

        :param :py:class`str` parentID:
        :return: record
        :rtype: :py:class:`dict` or :py:obj:`None`
        """
        for tableKey, table in self.extraction.items():
            if parentID in table:
                return (tableKey,table[parentID])

        return None

    @staticmethod
    def _generateLineage(parentID,parent2children):
        """Generates and RETURNS a lineage structure based on the given parentID.

        :param :py:class`str` parentID:
        :param :py:class:`dict` parent2children: dictionary of parentID to list of children.
        :return: lineageDict
        :rtype: :py:class:`dict`
        """
        if parentID in parent2children:
            return { child : TagParser._generateLineage(child,parent2children) for child in parent2children[parentID] }
        else:
            return None

    def generateLineages(self):
        """Generates and RETUNS parent-child record lineages.

        :return: lineages - lineages by tableID
        :rtype: :py:class`collections.defaultdict`
        """
        entities_with_parentIDs = []
        for tableKey, table in self.extraction.items():
            entities_with_parentIDs.extend((entity, tableKey, self.findParent(entity["parentID"])) for entity in table.values() if "parentID" in entity)

        parent2children = collections.defaultdict(list)
        terminalParentsByTable = collections.defaultdict(list)
        for entity_tuple in entities_with_parentIDs:
            parent2children[entity_tuple[0]["parentID"]].append(entity_tuple[0]["id"])
            if entity_tuple[2] == None:
                terminalParentsByTable[entity_tuple[1]].append(entity_tuple[0]["parentID"])
            elif "parentID" not in entity_tuple[2][1]:
                terminalParentsByTable[entity_tuple[2][0]].append(entity_tuple[0]["parentID"])

        lineages = collections.defaultdict(list)
        for tableKey in  terminalParentsByTable:
            lineages[tableKey] = { parentID : TagParser._generateLineage(parentID,parent2children) for parentID in terminalParentsByTable[tableKey] }

        return lineages

    @staticmethod
    def printLineages(lineages, indentation, group_size=5, file=sys.stdout):
        """Prints the given lineages.

        :param :py:class`collections.defaultdict` lineages:
        :param :py:class`int` indentation: indentation steps
        :param :py:class`int` group_size: number of childIDs to print per line.
        """
        for id in sorted(lineages.keys()):
            if lineages[id]:
                print(" "*indentation,id,":", file=file)
                terminal_children = sorted(childID for childID, children in lineages[id].items() if children == None)
                while terminal_children:
                    children_group = terminal_children[0:group_size]
                    terminal_children = terminal_children[group_size:]
                    print(" "*(indentation+2), ", ".join(children_group),file=file)
                non_terminal_children = {childID : children for childID, children in lineages[id].items() if children }
                TagParser.printLineages(non_terminal_children,indentation+2)
            ## I don't think this can be executed from the CLI, I can get it to print if the table in lineages is an empty dict and that's it.
            else:
                print(" "*indentation,id,file=file)


#
# Main Execution
#
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--profile":
        sys.argv.pop(1)
        import cProfile
        profiler = cProfile.Profile()
        profiler.enable()
        main()
        profiler.disable()
        profiler.print_stats()
    else:
        main()
    
