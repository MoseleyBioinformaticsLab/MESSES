#!/usr/bin/python3
""" 
 extract_metadata.py
    Extract SIRM metadata and data from excel workbook and JSON files.
    
 Usage:
    extract_metadata.py <parser_settings> <metadata_source>... [--delete <metadata_section>...] [options]
    extract_metadata.py --help

    <parser_settings> - input json settings filename
    <metadata_source> - input metadata source as csv/json filename or xlsx_filename[:worksheet_name|regular_expression]. "#export" worksheet name is the default.

 Options:
    --help                              - show this help documentation.
    --output <filename_json>            - output json filename.
    --compare <filename_json>           - compare extracted metadata to given JSONized metadata.
    --convert <source>                  - conversion directives worksheet name, regular expression, csv/json filename, or xlsx_filename[:worksheet_name|regular_expression] [default: #convert].
    --end-convert <source>              - apply conversion directives after all metadata merging. Requires csv/json filename or xlsx_filename:worksheet_name|regular_expression.
    --tagging <source>                  - tagging directives worksheet name, regular expression, csv/json filename, or xlsx_filename[:worksheet_name|regular_expression] [default: #tagging].
    --save-directives <filename_json>   - output filename with conversion and tagging directives in JSON format.
    --save-export <filetype>            - output export worksheet with suffix "_export" and with the indicated xlsx/csv format extension.
    --show <show_option>                - show a part of the metadata. See options below.
    --delete <metadata_section>...      - delete a section of the JSONized metadata. Section format is tableKey or tableKey,IDKey or tableKey,IDKey,fieldName. These can be regular expressions.
    --keep <metadata_tables>            - only keep the selected tables.  Delete the rest.  Table format is tableKey,tableKey,... The tableKey can be a regular expression.
    --silent                            - print no warning messages.

Show Options:
  tables    - show tables in the extracted metadata.
  lineage   - show parent-child lineages per table.
  all       - show every option.

Regular Expression Format:
  Regular expressions have the form "r'...'" on the command line.
  The re.match function is used, which matches from the beginning of a string, meaning that a regular expression matches as if it starts with a "^".

 Tag Parser Settings JSON Format:
   {
   "tableHierarchy" : { table_key : order_value },
   "knownAttributes" : { attribute_key : boolean },
   "allowedParents" : { table_key : [ parent_table_key, ... ] },
   "ignoreProjectStudy" : boolean
   }

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


## TODO export saves where the excel file is instead of cwd.
## When creating unit tests make sure to have a check on all pandas read ins that nan values become empty strings.
## Possibly add a step at the end that makes sure all records id field matches the dict key value.

import os.path
import copy
import sys
import re
import collections

import json
import pandas
import docopt
import jellyfish

import dinit
import jsonCommentRemover
import copier

silent = False

def main() :
    args = docopt.docopt(__doc__)

    if args["--silent"]:
        global silent
        silent = True

    # load tag parser settings JSON file
    with open(args["<parser_settings>"],'r') as jsonFile :
        tagParserSettings = json.loads(jsonCommentRemover.json_minify(''.join(jsonFile.readlines())))

    tagParserSettings["extraction"] = {}
    tagParser = TagParser(tagParserSettings)


    for metadataSource in args["<metadata_source>"]:
        tagParser.readMetadata(metadataSource, args["--tagging"], args["--convert"], args["--save-export"])

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
        keep = args["--keep"].split(",")
        sections = [ [ tableKey ] for tableKey in tagParser.extraction.keys() if tableKey not in keep ]
        tagParser.deleteMetadata(sections)

    if args["--show"] == "tables" or args["--show"] == "all":
        print("Tables: "," ".join(tagParser.extraction.keys()))

    if args["--show"] == "lineage" or args["--show"] == "all":
        lineages = tagParser.generateLineages()
        tagParser.printLineages(lineages,indentation=0, file=sys.stdout)

    if args["--output"]: # save to JSON
        with open(args["--output"],'w') as jsonFile :
            jsonFile.write(json.dumps(tagParser.extraction, sort_keys=True, indent=2, separators=(',', ': ')))

    if args["--compare"]:
        with open(args["--compare"], 'r') as jsonFile:
            otherMetadata = json.load(jsonFile)
            print("Comparison", file=sys.stdout)
            if not tagParser.compare(otherMetadata, file=sys.stdout):
                print("No differences detected.", file=sys.stdout)

    if args["--save-directives"]:
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
        return self.hasShortField("id") and type(self.shortField("id").operands[0]) is ColumnOperand

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

    def field(self, table, field) :
        """RETURNS FieldMaker for PARAMETERS table.field.

        :param :py:class:`str` table: table type of record
        :param :py:class:`str` field: field name
        :return: fieldMaker
        :rtype: :class:`FieldMaker` or :class:`ListFieldMaker` or :py:obj:`None`
        """
        field = self.properField(table,field)
        return shortField(field)

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
    def __init__(self, message, fileName, sheetName, rowIndex, columnIndex) :
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

        self.value = message + " at cell \"" + fileName + ":" + sheetName + "[" + cellName + "]\""
        
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

    
class TagParser(dinit.DictInit):
    """Creates parser objects that convert tagged .xlsx worksheets into nested dictionary structures for metadata capture."""
    _requiredMembers = [ "tableHierarchy", "knownAttributes", "ignoreProjectStudy" ]

    reDetector = re.compile(r"r[\"'](.*)[\"']$")

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
        
        if not table in self.tableHierarchy :
                raise TagParserError("Unknown table name \""+table+"\"", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)

        if field == "" :
            if self.lastField == "" :
                raise TagParserError("Undefined field name", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
            field = self.lastField
        else :
            self.lastField = field

        if attribute != "" :
            if not attribute in self.knownAttributes :
                raise TagParserError("Unknown attribute name", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
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
                if recordMakers[-1].isInvalidDuplicateField(table, field, fieldMakerClass) :
                    raise TagParserError(str("field \"") + field + "\" specified twice in " + table + " record", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
                recordMakers[-1].addField(table, field, fieldMakerClass)
                if field == "id" :
                    childWithoutID = False
                    if     len(tokens) > 0 and tokens[0] == "=" :
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
                        raise TagParserError("assignment tag is not previously defined in record", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
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
                if not assignment :
                    raise TagParserError("+ operator not in an assignment", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
            elif token == "," :
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
            table,record = recordMaker.create(row)
            if not table in self.extraction :
                self.extraction[table] = {}

            if not self.ignoreProjectStudy :
                if self.tableHierarchy[table] > self.tableHierarchy["project"] and not "project.id" in record and self.projectID != "" :
                    record["project.id"] = self.projectID
                elif "project.id" in record :
                    self.projectID = record["project.id"]

                if self.tableHierarchy[table] > self.tableHierarchy["study"] and not "study.id" in record and self.studyID != "" :
                    record["study.id"] = self.studyID
                elif "study.id" in record :
                    self.studyID = record["study.id"]

                if table == "project" :
                    self.projectID = record["id"]
                elif table == "study" :
                    self.studyID = record["id"]

            if not record["id"] in self.extraction[table] :
                self.extraction[table][record["id"]] = record
            else :
                for key in record :
                    if key == "id" :
                        pass
                    elif not key in self.extraction[table][record["id"]] :
                        self.extraction[table][record["id"]][key] = record[key]
                    elif isinstance(self.extraction[table][record["id"]][key], list) :
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

        aColumn = worksheet.iloc[:, 0]


        parsing = False
        recordMakers = ""
         ## Look through in each row of column A.
        for self.rowIndex in range(len(aColumn)) :
            try :
                  ## Convert the cell contents to a string and strip whitespace off the ends.
                  ## See if it contains "#tags".
                if re.match('#tags', xstr(aColumn.iloc[self.rowIndex]).strip()) :
                    parsing = True
                       ## If the cell contains "#tags" then this is a header row for a table. Parse the header.
                    recordMakers = self._parseHeaderRow(worksheet.iloc[self.rowIndex, :])
                  ## If the call contains "#ignore" then this row should be ignored.
                elif re.match('#ignore', xstr(aColumn.iloc[self.rowIndex]).strip()) :
                    pass
                  ## If "#tags" or "#ignore" could not be found then see if the entire row is empty.
                  ## If the row is empty it is either a pass or the end of a table, either way set parsing 
                  ## to false since we are not parsing a table in either case.
                elif TagParser._isEmptyRow(worksheet.iloc[self.rowIndex, :]) :
                    parsing = False
                  ## If parsing is set then we are parsing a table of records so parse this row.
                elif parsing :
                    self._parseRow(recordMakers, worksheet.iloc[self.rowIndex, :])
            except TagParserError as err:
                print(err.value, file=sys.stderr)
                exit(1)
            except :
                print(TagParserError("Internal Parser Error", self.fileName, self.sheetName, self.rowIndex, self.columnIndex), file=sys.stderr)
                raise

        
        self.rowIndex = -1


    @staticmethod
    def loadSheet(sheetInfo, silent=False):
        """Load and RETURN worksheet as a pandas data frame.

        :param :py:class:`str` sheetInfo: filename and sheetname (if needed).
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
                    sheetDetector = re.compile("^"+sheetName+"$")

                for sheetName in workbook.sheet_names:
                    if re.search(sheetDetector, sheetName) != None:
                        dataFrame = pandas.read_excel(workbook, sheetName, header=None, index_col=None, dtype=str)
                        if len(dataFrame) == 0:
                            print("There is no data in worksheet \"" + sheetInfo + "\".", file=sys.stderr)
                        else:
                            ## Empty cells are read in as nan by default, replace with empty string.
                            dataFrame = dataFrame.fillna("")
                            return (fileName, sheetName, dataFrame)
                if not silent:
                    print("No usable worksheet \"" + sheetInfo + "\" found.", file=sys.stderr)
            else:
                print("Excel workbook \"" + reCopier.value.group(1) + "\" does not exist.", file=sys.stderr)
        elif re.search(r"\.csv$", sheetInfo):
            dataFrame = pandas.read_csv(sheetInfo, header=None, index_col=None, dtype=str)
            if len(dataFrame) == 0:
                print("There is no data in worksheet \"" + sheetInfo + "\".", file=sys.stderr)
            else:
                dataFrame = dataFrame.fillna("") # Empty cells are read in as nan by default. Therefore replace with empty string.
                fileName = sheetInfo
                sheetName = ""
                return (fileName, sheetName, dataFrame)
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

    def readMetadata(self, metadataSource, taggingSource, conversionSource, saveExtension=None):
        """Reads metadata from source.

        :param :py:class:`str` metadataSource:  metadata source given as a filename with possibly a sheetname if appropriate.
        :param :py:class:`str` taggingSource:  tagging source given as a filename and/or sheetname
        :param :py:class:`str` conversionSource: conversion source given as a filename and/or sheetname.
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

        taggingDirectives = self.readDirectives(taggingSource, "tagging") if TagParser.hasFileExtension(taggingSource) else None
        ## Structure of conversionDirectives: {table_key:{field_key:{comparison_type:{field_value:{directive:{field_key:directive_value}}}}}} 
        ## The directive value is the new value to give the field or regex, regex is a list, assign is a string.
        ## unique is handled by having "-unique" added to comparison type key, so there is "exact-unique" and "exact".
        conversionDirectives = self.readDirectives(conversionSource, "conversion") if TagParser.hasFileExtension(conversionSource) else None

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

        self.extraction = currentMetadata
        self.merge(newMetadata)


    def saveSheet(self, fileName, sheetName, worksheet, saveExtension):
        """Save given worksheet in the given format.

        :param :py:class:`str` fileName: original worksheet filename
        :param :py:class:`str` sheetName:
        :param :py:class:`pandas.dataFrame` worksheet:
        :param :py:class:`str` saveExtension: csv or xlsx
        """
        fileName = "_export.".join(fileName.rsplit(".",1))
        if saveExtension == "csv":
            worksheet.to_csv(fileName, header=False, index=False)
        else:
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
        self.taggingDirectives = taggingDirectives
        if taggingDirectives != None:
            ## Copy so it is not the same pointer as self.taggingDirectives.
            taggingDirectives = copy.deepcopy(taggingDirectives)
            reCopier = copier.Copier()

            if not any(worksheet.iloc[:, 0] == '#tags') and not all(worksheet.iloc[:, 0] == ''):
                worksheet.insert(0,"","",True) # Insert empty column for #tags cells, if it does not exist.
                worksheet.set_axis(range(worksheet.shape[1]), axis="columns", inplace=True)

            usedRows = set()
            # Process each tagging group.
            for taggingGroup in taggingDirectives:
                if "header_tag_descriptions" not in taggingGroup:
                    # Insert at the beginning of the sheet
                    if "insert" in taggingGroup and len(taggingGroup["insert"]):
                        temp_df = pandas.DataFrame(taggingGroup["insert"], dtype=str)
                        worksheet = pandas.concat([temp_df, worksheet]).fillna("")
                        usedRows = set(row + len(temp_df) for row in usedRows)
                        usedRows.update(range(len(temp_df)))
#                        insertNum = len(taggingGroup["insert"])
#                        worksheet = pandas.concat([worksheet.iloc[0:insertNum+1, :], worksheet.iloc[:,:]])
#                        worksheet.iloc[0:insertNum+1, :] = ""
#                        for insertIndex in range(insertNum):
#                            while len(taggingGroup["insert"][insertIndex]) > len(worksheet.iloc[insertIndex,:]):
#                                worksheet.insert(len(worksheet.iloc[insertIndex,:]), "", "", True)
#                            worksheet.iloc[insertIndex,0:len(taggingGroup["insert"][insertIndex])] = taggingGroup["insert"][insertIndex]
#                        usedRows.update(range(insertNum+1))
                    continue

                ## Loop through the header tag descriptions and determine the required headers and tests for them.
                ## This is just setting up some data structures to make modifying worksheet easier later.
                headerTests = {}
                requiredHeaders = set()
                for headerTagDescription in taggingGroup["header_tag_descriptions"]:
                    ## If the added tag is an eval() tag created the header test differently.
                    if reCopier(Evaluator.isEvalString(headerTagDescription["header"])):
                        evaluator = Evaluator(reCopier.value.group(1), False, True)
                        headerTagDescription["field_maker"] = evaluator
                        headerTagDescription["header_list"] = []
                        headerTagDescription["header_tests"] = evaluator.fieldTests.copy()
                        headerTagDescription["header_tests"].update({ headerString : re.compile("^" + headerString + "$") for headerString in evaluator.requiredFields if headerString not in evaluator.fieldTests })
                        headerTests.update(headerTagDescription["header_tests"])

                        if headerTagDescription["required"]:
                            requiredHeaders.update(headerTagDescription["header_tests"].keys())
                    else:
                        headerTagDescription["header_list"] = [ token for token in re.split(TagParser.headerSplitter, headerTagDescription["header"]) if token != "" and token != None ]
                        headerTagDescription["header_tests"] = {}
                        fieldMaker = FieldMaker(headerTagDescription["header"])
                        for headerString in headerTagDescription["header_list"]:
                            if reCopier(re.match(TagParser.reDetector, headerString)):
                                fieldMaker.operands.append(VariableOperand(headerString))
                                headerTagDescription["header_tests"][headerString] = re.compile(reCopier.value.group(1))
                                headerTests[headerString] = headerTagDescription["header_tests"][headerString]
                            elif reCopier(re.match(TagParser.stringExtractor, headerString)):
                                fieldMaker.operands.append(LiteralOperand(reCopier.value.group(1)))
                            else:
                                fieldMaker.operands.append(VariableOperand(headerString))
                                headerTagDescription["header_tests"][headerString] = re.compile("^" + headerString + "$")
                                headerTests[headerString] = headerTagDescription["header_tests"][headerString]

                        if headerTagDescription["required"]:
                            requiredHeaders.update(headerTagDescription["header_tests"].keys())

                        if len(headerTagDescription["header_list"]) > 1 or len(headerTagDescription["header_list"]) != len(headerTagDescription["header_tests"]):
                            headerTagDescription["field_maker"] = fieldMaker

                ## Actually modify worksheet.
                insert = False
                rowIndex = 0
                while rowIndex < len(worksheet.iloc[:, 0]):
                    if rowIndex in usedRows:
                        rowIndex += 1
                        continue

                    row = worksheet.iloc[rowIndex, :]
                    header2ColumnIndex = {}
                    for headerString, headerTest in headerTests.items():
                        columnIndeces = [ columnIndex for columnIndex in range(1,len(row)) if re.search(headerTest, xstr(row.iloc[columnIndex]).strip()) ]
                        if len(columnIndeces) == 1: # must be unique match
                            header2ColumnIndex[headerString] = columnIndeces[0]

                    if len(set(header2ColumnIndex[headerString] for headerString in requiredHeaders if headerString in header2ColumnIndex)) == len(requiredHeaders): # found header row
                        found = False
                        endingRowIndex = rowIndex+1
                        for endingRowIndex in range(rowIndex+1, len(worksheet.iloc[:, 0])):
                            if TagParser._isEmptyRow(worksheet.iloc[endingRowIndex, :]) or re.match('#tags$', xstr(worksheet.iloc[endingRowIndex,0]).strip()) or endingRowIndex in usedRows:
                                found = True
                                break

                        if not found:
                            endingRowIndex = len(worksheet.iloc[:, 0])

                        if endingRowIndex != rowIndex+1: # Ignore header row with empty line after it.
                            if "insert" in taggingGroup and len(taggingGroup["insert"]) and (not insert or taggingGroup["insert_multiple"]):
                                insert = True
                                insertNum = len(taggingGroup["insert"])
                                worksheet = pandas.concat([worksheet.iloc[0:rowIndex+insertNum+1, :], worksheet.iloc[rowIndex:, :]])
                                worksheet.iloc[rowIndex:rowIndex+insertNum+1, :] = ""
                                for insertIndex in range(insertNum):
                                    while len(taggingGroup["insert"][insertIndex]) > len(worksheet.iloc[rowIndex+insertIndex, :]):
                                        worksheet.insert(len(worksheet.iloc[rowIndex+insertIndex, :]), "", "", True)
                                    worksheet.iloc[rowIndex+insertIndex, 0:len(taggingGroup["insert"][insertIndex])] = taggingGroup["insert"][insertIndex]
                                usedRows = set(index if index < rowIndex else index+insertNum+1 for index in usedRows)
                                usedRows.update(range(rowIndex,rowIndex+insertNum+1))
                                rowIndex += insertNum+1
                                endingRowIndex += insertNum+1

                            # Insert #tags row and the #tags and #ignore tags.
                            worksheet = pandas.concat([ worksheet.iloc[0:rowIndex+1,:], worksheet.iloc[rowIndex:,:] ])
                            worksheet.iloc[rowIndex+1,:] = ""
                            worksheet.iloc[rowIndex,0] = "#ignore"
                            worksheet.iloc[rowIndex+1,0] = "#tags"
                            endingRowIndex += 1

                            usedRows = set(index if index < rowIndex+1 else index+1 for index in usedRows)
                            usedRows.update(range(rowIndex,endingRowIndex))

                            # Create correct relative column order.
                            originalTDColumnIndeces = [ 1000 for x in range(len(taggingGroup["header_tag_descriptions"])) ]
                            for tdIndex in range(len(taggingGroup["header_tag_descriptions"])):
                                if "field_maker" in taggingGroup["header_tag_descriptions"][tdIndex] and \
                                        all( headerString in header2ColumnIndex for headerString in taggingGroup["header_tag_descriptions"][tdIndex]["header_tests"] ):
                                    originalTDColumnIndeces[tdIndex] = 1001
                                elif "field_maker" not in taggingGroup["header_tag_descriptions"][tdIndex] and not taggingGroup["header_tag_descriptions"][tdIndex]["header_list"]:
                                    originalTDColumnIndeces[tdIndex] = 1001
                                elif "field_maker" not in taggingGroup["header_tag_descriptions"][tdIndex] and taggingGroup["header_tag_descriptions"][tdIndex]["header_list"][0] in header2ColumnIndex:
                                    originalTDColumnIndeces[tdIndex] = header2ColumnIndex[taggingGroup["header_tag_descriptions"][tdIndex]["header_list"][0]]

                            newTDColumnIndeces = originalTDColumnIndeces.copy()
                            for tdIndex in range(len(taggingGroup["header_tag_descriptions"])):
                                # insert new column if needed
                                if (newTDColumnIndeces[tdIndex] == 1001 or newTDColumnIndeces[tdIndex] < 1000) and reCopier(min(newTDColumnIndeces[tdIndex+1:]+[len(worksheet.columns)])) < newTDColumnIndeces[tdIndex]:
                                    worksheet.insert(reCopier.value, "", "", True)
                                    header2ColumnIndex = { headerString:(index+1 if index >= reCopier.value else index) for headerString, index in header2ColumnIndex.items() } # must be done before the next if, else statement
                                    if originalTDColumnIndeces[tdIndex] != 1001: # copy normal columns
                                        worksheet.iloc[rowIndex:endingRowIndex, reCopier.value] = worksheet.iloc[rowIndex:endingRowIndex, newTDColumnIndeces[tdIndex]+1]
                                        header2ColumnIndex[taggingGroup["header_tag_descriptions"][tdIndex]["header_list"][0]] = reCopier.value

                                    newTDColumnIndeces[tdIndex] = reCopier.value
                                    newTDColumnIndeces[tdIndex+1:] = [ index+1 if index >= reCopier.value and index < 1000 else index for index in newTDColumnIndeces[tdIndex+1:] ]

                            # Add tags.
                            for tdIndex in range(len(taggingGroup["header_tag_descriptions"])):
                                if originalTDColumnIndeces[tdIndex] != 1000:
                                    worksheet.iloc[rowIndex+1, newTDColumnIndeces[tdIndex]] = taggingGroup["header_tag_descriptions"][tdIndex]["tag"]

                            # Compose new columns.
                            makerIndeces = [ tdIndex for tdIndex in range(len(taggingGroup["header_tag_descriptions"])) if originalTDColumnIndeces[tdIndex] == 1001 ]
                            for rIndex in range(rowIndex + 2, endingRowIndex):
                                row = worksheet.iloc[rIndex, :]
                                record = { headerString:xstr(row.iloc[cIndex]).strip() for headerString, cIndex in header2ColumnIndex.items() }
                                for tdIndex in makerIndeces:
                                    if "field_maker" in taggingGroup["header_tag_descriptions"][tdIndex]:
                                        if type(taggingGroup["header_tag_descriptions"][tdIndex]["field_maker"]) == FieldMaker:
                                            worksheet.iloc[rIndex, newTDColumnIndeces[tdIndex]] = taggingGroup["header_tag_descriptions"][tdIndex]["field_maker"].create(record, row)
                                        else:
                                            worksheet.iloc[rIndex, newTDColumnIndeces[tdIndex]] = taggingGroup["header_tag_descriptions"][tdIndex]["field_maker"].evaluate(record)
                    else:
                        rowIndex += 1

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
                    comparisonType = "exact"
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
                        elif reCopier(re.match('\s*#comparison\s*=\s*(exact|regex|levenshtein)\s*$', cellString)):
                            comparisonType=reCopier.value.group(1)
                        elif re.match('\s*#comparison\s*$', cellString):
                            comparisonIndex = self.columnIndex
                        elif re.match('\s*#unique\s*=\s*[Tt]rue\s*$', cellString):
                            isUnique = "-unique"
                        elif re.match('\s*#unique\s*=\s*[Ff]alse\s*$', cellString):
                            isUnique = ""
                        elif re.match('\s*#unique\s*$', cellString):
                            uniqueIndex = self.columnIndex
                        self.columnIndex = -1
                    if valueIndex == -1 or (len(assignIndeces) == 0 and len(appendIndeces) == 0 and len(prependIndeces) == 0 and len(regexIndeces) == 0 and len(deletionFields) == 0):
                        raise TagParserError("Missing #table_name.field_name.value or #.field_name.assign|append|prepend|regex|delete conversion tags", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)
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
                        localComparisonType = "regex" if re.match(TagParser.reDetector, fieldValue) else comparisonType

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
                        if re.match(r"\*", assignFieldTypes[i]):
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
                            raise TagParserError("#table_name.field_name.regex value is not of the correct format r\"...\",r\"...\".", self.fileName, self.sheetName, self.rowIndex, self.columnIndex)

                    if not localComparisonType in self.conversionDirectives[table][fieldID]:
                        self.conversionDirectives[table][fieldID][localComparisonType] = {}
                    if not fieldValue in self.conversionDirectives[table][fieldID][localComparisonType]:
                        self.conversionDirectives[table][fieldID][localComparisonType][fieldValue] = {}
                    elif not silent:
                        print(TagParserError("Warning: duplicate conversion directive given", self.fileName, self.sheetName, self.rowIndex, self.columnIndex), file=sys.stderr)
                    if assignFieldMap:
                        self.conversionDirectives[table][fieldID][localComparisonType][fieldValue]["assign"] = assignFieldMap
                    if appendFieldMap:
                        self.conversionDirectives[table][fieldID][localComparisonType][fieldValue]["append"] = appendFieldMap
                    if prependFieldMap:
                        self.conversionDirectives[table][fieldID][localComparisonType][fieldValue]["prepend"] = prependFieldMap
                    if regexFieldMap:
                        self.conversionDirectives[table][fieldID][localComparisonType][fieldValue]["regex"] = regexFieldMap
                    if deletionFields:
                        self.conversionDirectives[table][fieldID][localComparisonType][fieldValue]["delete"] = deletionFields
                    if renameFieldMap:
                        self.conversionDirectives[table][fieldID][localComparisonType][fieldValue]["rename"] = renameFieldMap
            except TagParserError as err:
                print(err.value, file=sys.stderr)
                exit(1)
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
                    parsing = False
#                    currTaggingGroup = {}
#                    self.taggingDirectives.append(currTaggingGroup)
                    ## TODO delete below 3 lines and uncomment top 2.
                    if currTaggingGroup is None:
                        currTaggingGroup = {}
                        self.taggingDirectives.append(currTaggingGroup)
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
            except:
                print(TagParserError("Internal Parser Error", self.fileName, self.sheetName, self.rowIndex, self.columnIndex), file=sys.stderr)
                raise

            self.rowIndex += 1

        if self.taggingDirectives and not self.taggingDirectives[-1]["header_tag_descriptions"]:
            self.taggingDirectives.pop()

        self.rowIndex = -1

    def readDirectives(self, source, directiveType):
        """Read directives source of a given directive type.

        :param :py:class:`str` source: filename with sheetname (optional).
        :return: directives
        :rtype: :py:class:`dict`
        """
        directives = None
        if re.search(r"\.json$", source):
            with open(source, 'r') as jsonFile:
                directives = json.load(jsonFile)
                if type(directives) == dict:
                    if directiveType in directives:
                        directives = directives[directiveType]
                else:
                    directives = None
        elif TagParser.hasFileExtension(source):
            dataFrameTuple = TagParser.loadSheet(source, silent=True)
            if dataFrameTuple != None:
                if directiveType == "conversion":
                    self.conversionDirectives = {}
                    self._parseConversionSheet(*dataFrameTuple)
                    directives = self.conversionDirectives
                else:
                    self.taggingDirectives = []
                    self._parseTaggingSheet(*dataFrameTuple)
                    directives = self.taggingDirectives

        return directives

    @staticmethod
    def _applyConversionDirectives(record, conversions):
        """Apply conversion directives to the given record.

        :param :py:class:`dict` record: table record
        :param :py:class:`dict` conversions: nested dict of field additions and deletions.
        """
        if "assign" in conversions:
            for newField, newValue in conversions["assign"].items():
                if type(newValue) == Evaluator:
                    if newValue.hasRequiredFields(record):
                        record[newField] = newValue.evaluate(record)
                    elif not silent:
                        print("Warning: Field assignment directive \"" + newField + "\" missing required field(s) \"" + ",".join([ field for field in newValue.requiredFields if field not in record]) + "\"", file=sys.stderr)
                else:
                    record[newField] = newValue

        if "append" in conversions:
            for newField, newValue in conversions["append"].items():
                if newField not in record and type(newValue) == list:
                    record[newField] = newValue.copy()
                elif newField not in record and type(newValue) != list:
                    record[newField] = newValue
                elif type(record[newField]) == list and type(newValue) == list:
                    minLen = min(len(record[newField]),min(newValue))
                    for index in range(minLen):
                        record[newField][index] += newValue[index]
                elif type(record[newField]) == list and type(newValue) != list:
                    for index in range(len(record[newField])):
                        record[newField][index] += newValue
                elif type(record[newField]) != list and type(newValue) == list:
                    record[newField] += newValue[0]
                else:
                    record[newField] += newValue

        if "prepend" in conversions:
            for newField, newValue in conversions["prepend"].items():
                if newField not in record and type(newValue) == list:
                    record[newField] = newValue.copy()
                elif newField not in record and type(newValue) != list:
                    record[newField] = newValue
                elif type(record[newField]) == list and type(newValue) == list:
                    minLen = min(len(record[newField]),min(newValue))
                    for index in range(minLen):
                        record[newField][index] = record[newField][index] + newValue[index]
                elif type(record[newField]) == list and type(newValue) != list:
                    for index in range(len(record[newField])):
                        record[newField][index] = newValue + record[newField][index]
                elif type(record[newField]) != list and type(newValue) == list:
                    record[newField] = newValue[0] + record[newField]
                else:
                    record[newField] = newValue + record[newField]

        if "regex" in conversions:
            for newField, regexPair in conversions["regex"].items():
                if newField not in record:
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

        if "delete" in conversions:
            for deletedField in conversions["delete"]:
                record.pop(deletedField, None)

        if "rename" in conversions:
            for oldField,newField in conversions["rename"].items():
                if oldField in record:
                    record[newField] = record[oldField]
                    record.pop(oldField, None)


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

        if comparisonType in conversionDirectives[tableKey][fieldKey]:
            table = self.extraction[tableKey]
            for idKey, record in table.items():
                if fieldKey in record:
                    fieldValue = record[fieldKey]
                    if type(fieldValue) == list:
                        for specificValue in fieldValue:
                            if (tableKey, fieldKey, specificValue) not in usedRecordTuples and specificValue in conversionDirectives[tableKey][fieldKey][comparisonType]:
                                TagParser._applyConversionDirectives(record, conversionDirectives[tableKey][fieldKey][comparisonType][specificValue])
                                if isUnique:
                                    usedRecordTuples.add((tableKey, fieldKey, specificValue))
                                self.usedConversions.add((tableKey, fieldKey, comparisonType, specificValue))
                            elif isUnique and (tableKey, fieldKey, specificValue) in usedRecordTuples and specificValue in conversionDirectives[tableKey][fieldKey][comparisonType] and not silent:
                                print("Warning: conversion directive #" + tableKey + "." + fieldKey + "." + comparisonType + "." + specificValue + " matches more than one record. Only the first record will be changed. Try #unique=false if all matching records should be changed.", file=sys.stderr)
                    elif (tableKey, fieldKey, fieldValue) not in usedRecordTuples and fieldValue in conversionDirectives[tableKey][fieldKey][comparisonType]:
                        TagParser._applyConversionDirectives(record, conversionDirectives[tableKey][fieldKey][comparisonType][fieldValue])
                        if isUnique:
                            usedRecordTuples.add((tableKey, fieldKey, fieldValue))
                        self.usedConversions.add((tableKey, fieldKey, comparisonType, fieldValue))
                    elif isUnique and (tableKey, fieldKey, fieldValue) in usedRecordTuples and fieldValue in conversionDirectives[tableKey][fieldKey][comparisonType] and not silent:
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

        if comparisonType in conversionDirectives[tableKey][fieldKey]:
            table = self.extraction[tableKey]
            for idKey, record in table.items():
                if fieldKey in record:
                    fieldValue = record[fieldKey]
                    for regexID, regexEntry in conversionDirectives[tableKey][fieldKey][comparisonType].items():
                        if type(fieldValue) == list:
                            for specificValue in fieldValue:
                                if (tableKey, fieldKey, specificValue) not in usedRecordTuples and re.search(regexObjects[regexID], specificValue):
                                    TagParser._applyConversionDirectives(record, regexEntry)
                                    if isUnique:
                                        usedRecordTuples.add((tableKey, fieldKey, specificValue))
                                    self.usedConversions.add((tableKey, fieldKey, comparisonType, regexID))
                                elif isUnique and (tableKey, fieldKey, specificValue) in usedRecordTuples and re.search(regexObjects[regexID], specificValue) and not silent:
                                    print("Warning: conversion directive #" + tableKey + "." + fieldKey + "." + comparisonType + "." + regexID + " matches more than one record. Only the first record will be changed. Try #unique=false if all matching records should be changed.", file=sys.stderr)
                        elif (tableKey, fieldKey, fieldValue) not in usedRecordTuples and re.search(regexObjects[regexID], fieldValue):
                            TagParser._applyConversionDirectives(record, regexEntry)
                            if isUnique:
                                usedRecordTuples.add((tableKey, fieldKey, fieldValue))
                            self.usedConversions.add((tableKey, fieldKey, comparisonType, regexID))
                        elif isUnique and (tableKey, fieldKey, fieldValue) in usedRecordTuples and re.search(regexObjects[regexID], fieldValue) and not silent:
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
                        TagParser._applyConversionDirectives(self.extraction[tableKey][uniqueForLevenshteinID[levID]], levEntry)
                        usedRecordTuples.add((tableKey, fieldKey, levenshteinComparisonValues[levID][uniqueForLevenshteinID[levID]]))
                        self.usedConversions.add((tableKey, fieldKey, comparisonType, levID))
            else:
                for idKey, levID in uniqueForIdKey.items():
                    TagParser._applyConversionDirectives(self.extraction[tableKey][idKey], conversionDirectives[tableKey][fieldKey][comparisonType][levID])
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
                                    if reCopier(Evaluator.isEvalString(fieldValueDict["assign"][newField])):
                                        fieldValueDict["assign"][newField] = Evaluator(reCopier.value.group(1))

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
            idTranslation = collections.defaultdict(dict)
            for tableKey, table in self.extraction.items():
                idTranslation[tableKey + ".id"].update({ idKey : record["id"] for idKey, record in table.items() if idKey != record["id"] })

            # Translate changed IDs.
            translated = {}
            for tableKey,table in self.extraction.items() :
                translated[tableKey] = { record["id"] : record for record in table.values() }
                for record in table.values():
                    for fieldKey, fieldValue in record.items() :
                        if fieldKey in idTranslation:
                            if type(fieldValue) == list:
                                for index in range(len(fieldValue)):
                                    if fieldValue[index] in idTranslation[fieldKey]:
                                        fieldValue[index] = idTranslation[fieldKey][fieldValue[index]]
                            elif fieldValue in idTranslation[fieldKey]:
                                record[fieldKey] = idTranslation[fieldKey][fieldValue]

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
                            if file is not None:
                                print("Table", tableKey, "id", idKey, "with different fields:", ", ".join(differentFields), file=file)
                            else:
                                return True

        return different

    def deleteMetadata(self, sections):
        """Delete sections of metadata based on given section descriptions.

        :param :py:class`list` sections: list of sections that are lists of strings.
        """
        compiled_sections = [ [ re.compile(re.match(TagParser.reDetector, keyElement)[1]) if re.match(TagParser.reDetector, keyElement) else re.compile("^" + keyElement + "$") for keyElement in section ] for section in sections ]

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
            else:
                print(" "*indentation,id,file=file)


#
# Main Execution
#
if __name__ == "__main__":
    main()
    
