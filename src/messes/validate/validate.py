# -*- coding: utf-8 -*-
"""
Validate JSON files.

Usage:
    messes validate json <input_JSON> [--cv=<cv> [--csv | --xlsx | --json] | --no_base_schema] 
                                      [--no_extra_checks]
                                      [--additional=<add_schema>] 
                                      [--silent=<level>]
    messes validate save-schema <output_schema> [--input=<input_JSON>] [--cv=<cv> [--csv | --xlsx | --json]] [--silent=<level>]
    messes validate schema <input_schema>
    messes validate cv <cv> [--csv | --xlsx | --json] [--silent=<level>]
    messes validate --help
    
    <input_JSON> - if '-' read from standard input.
    <cv> - can be a JSON, csv, or xlsx file. If xlsx the default sheet name to read in is #validate, 
           to specify a different sheet name separate it from the file name with a colon ex: file_name.xlsx:sheet_name.
           If '-' read from standard input.
    <input_schema> - must be a valid JSON Schema file. If '-' read from standard input.
    <output_schema> - if '-' save to standard output.

Options:
    -h, --help                           - show this screen.
    -v, --version                        - show version.
    --silent <level>                     - if "full" silence all warnings, 
                                           if "nuisance" silence warnings that are more likely to be a nuisance,
                                           if "none" do not silence warnings [default: none].
    --cv <cv>                            - a controlled vocabulary file, can be a JSON, csv, or xlsx file. 
                                           If xlsx the default sheet name to read in is #validate, to specify 
                                           a different sheet name separate it from the file name with a colon 
                                           ex: file_name.xlsx:sheet_name.
    --csv                                - indicates that the controlled vocabulary file is a csv (comma delimited) file.
    --xlsx                               - indicates that the controlled vocabulary file is an xlsx (Excel) file.
    --json                               - indicates that the controlled vocabulary file is a JSON file.
                                           If a file type is not given then it will be guessed from the file extension.
    --additional <add_schema>            - an additional JSON Schema file that will be used to validate <input_JSON>.
    --no_base_schema                     - don't validate with the base JSON schema.
    --no_extra_checks                    - only do JSON Schema validation and nothing else.
    --input <input_JSON>                 - optionally give an input JSON file to save-schema to reproduce the 
                                           schema used to validate in the json command.
    

The "json" command will validate the <input_JSON> against the internal base_schema, and optional schema provided 
by the --cv and --additional options. To validate only against a provided schema, use the --additional and --no_base_schema options.

The "save-schema" command will save the internal base_schema to the <output_schema> location. If --cv is given 
then it will be parsed and placed into the base_schema. If --input is given the protocols table will be added 
in with the CV to reproduce what happens in the json command.

The "schema" command will validate the <input_schema> against the JSON Schema meta schema.

The "cv" command will validate that the <cv> file is a valid controlled vocabulary file.
"""
## TODO take the MS_base_truncated and MS_base files from validate and redo convert tests and examples.

import re
import sys
import io
import json
import pathlib
import itertools
from typing import TextIO

import docopt
import jsonschema

from messes import __version__
from messes.extract import extract
from messes.validate.validate_schema import base_schema, CV_schema


def main() :
    args = docopt.docopt(__doc__, version=__version__)
    
    args["--silent"] = args["--silent"].lower()
    if args["--silent"] not in ["full", "nuisance", "none"]:
        print("Error:  Unknown silent level, " + args["--silent"] + ". Must be one of \"full\", \"nuisance\", or \"none\".", file=sys.stderr)
        sys.exit()
    
    #######################
    ## Handle json command.
    #######################
    if args["json"]:            
        run_json_command(args["<input_JSON>"], args["--cv"], args["--additional"], 
                         args["--no_base_schema"], args["--no_extra_checks"], args["--csv"], 
                         args["--xlsx"], args["--json"], args["--silent"])
    
    
    #############################    
    ## Handle save-schema command
    #############################
    if args["save-schema"]:
        run_save_schema_command(args["--cv"], args["<output_schema>"], args["--input"],
                                args["--csv"], args["--xlsx"], args["--json"], args["--silent"])
    
    
    #########################
    ## Handle schema command.
    #########################
    if args["schema"]:
        run_schema_command(args["<input_schema>"])
        
    
    #####################
    ## Handle cv command.
    #####################
    if args["cv"]:
        run_cv_command(args["<cv>"], args["--csv"], args["--xlsx"], args["--json"], args["--silent"])
    
    
    
        
    
def check(self, instance: object, format: str) -> None:
    """Check whether the instance conforms to the given format.
    
    Modified from jsonschema.FormatChecker.check. Used to raise an error on 
    the custom "integer" and "numeric" formats so their values can be cast 
    to int and float respectively.

    Args:
        instance: the instance to check
        format: the format that instance should conform to

    Raises:
        FormatError:
            if the instance does not conform to ``format``, also raises if it 
            does conform to "integer" or "numeric" formats
    """

    if format not in self.checkers:
        return

    func, raises = self.checkers[format]
    result, cause = None, None
    try:
        result = func(instance)
    except raises as e:
        cause = e
    if not result:
        raise jsonschema.exceptions.FormatError(f"{instance!r} is not a {format!r}", cause=cause)
    elif format == "integer" and isinstance(instance, str):
        raise jsonschema.exceptions.FormatError("safe to convert to int", cause=None) 
    elif format == "numeric" and isinstance(instance, str):
        raise jsonschema.exceptions.FormatError("safe to convert to float", cause=None) 


def convert_formats(validator, instance) -> bool:
    ## Get old check to save and restore.
    original_check = jsonschema.FormatChecker.check
    ## Replace check in FormatChecker.
    jsonschema.FormatChecker.check = check
    
    for error in validator.iter_errors(instance):
        if error.message == "safe to convert to float":
            path = "[%s]" % "][".join(repr(index) for index in error.relative_path)
            exec("instance" + path + "=float(" + "instance" + path + ")")
        elif error.message == "safe to convert to int":
            path = "[%s]" % "][".join(repr(index) for index in error.relative_path)
            exec("instance" + path + "=int(float(" + "instance" + path + "))")
            
    jsonschema.FormatChecker.check = original_check
    
    
def print_better_error_messages(errors_generator) -> bool:
    has_errors = False
    for error in errors_generator:
        has_errors = True
        
        message = ""
        custom_message = ""
        
        if error.validator == "minProperties":
            custom_message = " cannot be empty."
        elif error.validator == "required":
            required_property = re.match(r"(\'.*\')", error.message).group(1)
            if len(error.relative_path) == 0:
                message += "The required property " + required_property + " is missing."
            else:
                message += "The entry " + "[%s]" % "][".join(repr(index) for index in error.relative_path) + " is missing the required property " + required_property + "."
        elif error.validator == "dependencies":
            message += "The entry " + "[%s]" % "][".join(repr(index) for index in error.relative_path) + " is missing a dependent property.\n"
            message += error.message
        elif error.validator == "dependentRequired":
            message += "The entry " + "[%s]" % "][".join(repr(index) for index in error.relative_path) + " is missing a dependent property.\n"
            message += error.message
        elif error.validator == "minLength":
            custom_message = " cannot be an empty string."
        elif error.validator == "maxLength":
            custom_message = " is too long."
        elif error.validator == "minItems":
            custom_message = " cannot be empty."
        elif error.validator == "type":
            if type(error.validator_value) == list:
                custom_message = " is not any of the allowed types: ["
                for allowed_type in error.validator_value:
                    custom_message += "\'" + allowed_type + "\', "
                custom_message = custom_message[:-2]
                custom_message += "]."
            else:
                custom_message = " is not of type \"" + error.validator_value + "\"."
        elif error.validator == "enum":
            custom_message = " is not one of [" + "%s" % ", ".join(repr(index) for index in error.validator_value) + "]."
        elif error.validator == "format":
            custom_message = " is not a valid " + error.validator_value + "."
        elif error.validator == "pattern":
            custom_message = " does not match the regular expression pattern " + str(error.validator_value)
        elif error.validator == "minimum":
            custom_message = " must be greater than or equal to " + str(error.validator_value) + "."
        elif error.validator == "maximum":
            custom_message = " must be less than or equal to " + str(error.validator_value) + "."
        elif error.validator == "uniqueItems":
            custom_message = " has non-unique elements."
        else:
            print(error, file=sys.stderr)
        
        
        if custom_message:
            message = message + "The value for " + "[%s]" % "][".join(repr(index) for index in error.relative_path) + custom_message
        print("Error:  " + message, file=sys.stderr)
    return has_errors
    
    
    
def read_and_validate_controlled_vocabulary(filepath, is_csv, is_xlsx, is_json, no_last_message, silent) -> dict:
    
    from_stdin = False
    if filepath == "-":
        if not is_csv and not is_json:
            ## Have to clear the input or the system prints an extra error.
            sys.stdin.readlines()
            print("Error:  When reading the controlled vocabulary from standard input you must specify that it is '--csv' or '--json'.", file=sys.stderr)
            sys.exit()
        filepath = sys.stdin
        from_stdin = True
        
                
    
    if is_csv or is_xlsx or (not from_stdin and re.search(r".*(\.xls[xm]?|\.csv)", filepath)):
        default_sheet_name = False
        sheet_name = None
        if not from_stdin and (reMatch := re.search(r"^(.*\.xls[xm]?):(.*)$", filepath)):
            filepath = reMatch.group(1)
            sheet_name = reMatch.group(2)
        # elif not from_stdin and re.search(r"\.xls[xm]?$", filepath):
        elif not from_stdin and re.search(r"\.xls[xm]?$", filepath):
            sheet_name = "#validate"
            default_sheet_name = True
        tagParser = extract.TagParser()
        ## In order to print error messages correctly we have to know if loadSheet printed a message or not, so temporarily replace stderr.
        old_stderr = sys.stderr
        sys.stderr = buffer = io.StringIO()
        try:
            if worksheet_tuple := tagParser.loadSheet(filepath, sheet_name, isDefaultSearch=default_sheet_name):
                tagParser.parseSheet(*worksheet_tuple)
                controlled_vocabulary = tagParser.extraction
                sys.stderr = old_stderr
            else:
                sys.stderr = old_stderr
                if buffer.getvalue():
                    ## Have to trim the extra newline off the end of buffer.
                    print(buffer.getvalue()[0:-1], file=sys.stderr)
                elif default_sheet_name:
                    print("Error:  No sheet name was given for the xlsx file, so the default name " +\
                          "of #validate was used, but it was not found in the file.", file=sys.stderr)
                sys.exit()
        except Exception as e:
            sys.stderr = old_stderr
            if from_stdin:
                print("Error:  A problem was encountered trying to read the controlled vocabulary from stdin. " +\
                      "Make sure the indicated file type is correct.", file=sys.stderr)
                sys.exit()
            raise e
    
    elif is_json or (not from_stdin and re.match(r".*\.json$", filepath)):
        if from_stdin:
            try:
                controlled_vocabulary = json.load(filepath)
            except Exception:
                print("Error:  A problem was encountered trying to read the controlled vocabulary from stdin. " +\
                      "Make sure the indicated file type is correct.", file=sys.stderr)
                sys.exit()
        elif not pathlib.Path(filepath).exists():
            print("Error:  The value entered for the controlled vocabulary, " + filepath + ", is not a valid file path or does not exist.", file=sys.stderr)
            sys.exit()
        else:
            with open(filepath, 'r') as jsonFile:
                controlled_vocabulary = json.load(jsonFile)
    
    else:
        print("Error:  Unknown file type for the controlled vocabulary file.", file=sys.stderr)
        sys.exit()
        
    # if (validate_CV_parent_protocols(controlled_vocabulary) or validate_with_arbitrary_schema(controlled_vocabulary, CV_schema)) \
    #    and not no_last_message:
    has_errors = validate_CV_parent_protocols(controlled_vocabulary, silent)
    has_errors = has_errors | print_better_error_messages(create_validator(CV_schema).iter_errors(controlled_vocabulary))
    if has_errors and not no_last_message:
        print("Error:  The provided controlled vocabulary is not valid, so execution stops here.", file=sys.stderr)
        sys.exit()
        
    return controlled_vocabulary
            
    
    
def read_in_JSON_file(filepath: str, description: str) -> dict:
    from_stdin = False
    if filepath == "-":
        filepath = sys.stdin
        from_stdin = True
    
    elif not pathlib.Path(filepath).exists():
        print("Error:  The value entered for the " + description + ", " + filepath + ", is not a valid file path or does not exist.", file=sys.stderr)
        sys.exit()
    
    try:
        if from_stdin:
            user_json = json.load(filepath)
        else:
            with open(filepath, 'r') as jsonFile:
                user_json = json.load(jsonFile)
    except Exception:
        if from_stdin:
            print("Error:  An error was encountered when trying to read in the " + description + " from standard input.", file=sys.stderr)
        else:
            print("Error:  An error was encountered when trying to read in the " + description + ", from the path " + filepath + ".", file=sys.stderr)
        sys.exit()
        
    return user_json
    


def validate_JSON_schema(user_json_schema) -> bool:
    validator_for_user_schema = jsonschema.validators.validator_for(user_json_schema)
    validator_for_meta_schema = jsonschema.validators.validator_for(validator_for_user_schema.META_SCHEMA)
    validator = validator_for_meta_schema(validator_for_meta_schema.META_SCHEMA)
    has_errors = False
    for error in validator.iter_errors(user_json_schema):
        print(error, file=sys.stderr)
        has_errors = True
        
    return has_errors


def create_validator(schema) -> jsonschema.protocols.Validator:
    validator = jsonschema.validators.validator_for(schema)
    format_checker = jsonschema.FormatChecker()
    @format_checker.checks('integer') 
    def is_integer(value):
        if value and isinstance(value, str):
            try:
                float(value)
            except ValueError:
                return False
            return True
        return True
    @format_checker.checks('numeric') 
    def is_float(value):
        if value and isinstance(value, str):
            try:
                float(value)
            except ValueError:
                return False
            return True
        return True
    return validator(schema=schema, format_checker=format_checker)


# def validate_with_arbitrary_schema(instance, schema) -> bool:
#     validator = jsonschema.validators.validator_for(schema)
#     format_checker = jsonschema.FormatChecker()
#     @format_checker.checks('integer') 
#     def is_integer(value):
#         if value and isinstance(value, str):
#             try:
#                 int(value)
#             except ValueError:
#                 return False
#             return True
#         return True
#     @format_checker.checks('numeric') 
#     def is_float(value):
#         if value and isinstance(value, str):
#             try:
#                 float(value)
#             except ValueError:
#                 return False
#             return True
#         return True
#     validator = validator(schema=schema, format_checker=format_checker)
#     errors_generator = validator.iter_errors(instance=instance)
#     return print_better_error_messages(errors_generator)


def validate_CV_parent_protocols(cv, silent):
    if not "parent_protocol" in cv:
        return True
    
    has_errors = False
    for protocol, attributes in cv["parent_protocol"].items():
        has_fields = True if (fields := cv.get(protocol)) else False
        if parent_name := attributes.get("parent_id"):
            ancestors = []
            parent_attributes = attributes
            has_fields = True if (fields := cv.get(parent_name)) else has_fields
            while (parent_name := parent_attributes.get("parent_id")):
                has_fields = True if (fields := cv.get(parent_name)) else has_fields
                if parent_name in ancestors:
                    print("Error:  The protocol, \"" + protocol + "\", in the \"parent_protocol\" table " + \
                          "has a circular ancestry, i.e., somewhere in the lineage a protocol has a " +\
                          "\"parent_id\" to a child in the lineage.", file=sys.stderr)
                    has_errors = True
                    break
                ancestors.append(parent_name)
                if not parent_name in cv["parent_protocol"]:
                    break
                parent_attributes = cv["parent_protocol"][parent_name]
            
            if not has_fields and not (silent == "nuisance" or silent == "full"):
                print("Warning:  The protocol, \"" + protocol + "\"," + \
                      "\" in the \"parent_protocol\" table does not itself have any " +\
                      "fields to validate, nor do any of its ancestors.", file=sys.stderr)
            
            parent_name = attributes["parent_id"]
            if parent_name == protocol:
                print("Error:  The protocol, \"" + protocol + "\", in the \"parent_protocol\" table " + \
                      "has itself listed for its parent_id. Protocols cannot be their own parents.", file=sys.stderr)
                has_errors = True
            
            if parent_name not in cv["parent_protocol"]:
                print("Error:  The parent protocol, \"" + parent_name + "\", for the protocol \"" + protocol + \
                      "\" in the \"parent_protocol\" table is not itself in the \"parent_protocol\" table. " +\
                      "Parent entities must be in the table as well.", file=sys.stderr)
                has_errors = True
            elif (type_to_check := attributes.get("type")) and (parent_type := cv["parent_protocol"][parent_name].get("type")) and \
               type_to_check != parent_type:
                print("Error:  The protocol, \"" + protocol + "\", does not have the same type as its parent \"" + \
                      parent_name + "\".", file=sys.stderr)
                has_errors = True
            
            if parent_name not in cv and not (silent == "nuisance" or silent == "full"):
                print("Warning:  The parent protocol, \"" + parent_name + "\", for the protocol \"" + protocol + \
                      "\" in the \"parent_protocol\" table is not itself in the controlled vocabulary. " +\
                      "Parent entities must be in the controlled vocabulary as well.", file=sys.stderr)
            
        if protocol not in cv and not (silent == "nuisance" or silent == "full"):
            print("Warning:  The protocol, \"" + protocol + \
                  "\" in the \"parent_protocol\" table is not in the controlled vocabulary.", file=sys.stderr)
    return has_errors



def add_protocols_to_CV(protocol_table: dict, cv: dict, silent: str) -> dict:
    protocols_to_add = {}
    for protocol, attributes in protocol_table.items():
        if (parent := attributes.get("parent_protocol")) :
            if isinstance(parent, str):
                if parent in cv["parent_protocol"]:
                    protocols_to_add[protocol] = parent
                    if (protocol_type := attributes.get("type")) and \
                        protocol_type != cv["parent_protocol"][parent]["type"] and not silent == "full":
                        print("Warning:  The protocol from the input JSON, " + protocol + \
                              ", does not have the same type as its parent_protocol, " + parent + \
                              ", in the controlled vocabulary.", file=sys.stderr)
                elif protocol not in cv["parent_protocol"] and not silent == "full":
                    print("Warning:  The protocol from the input JSON, " + protocol + \
                          ", is not in the parent_protocol table of the controlled vocabulary, " +\
                          "nor does it have a parent_protocol in the controlled vocabulary." +\
                          " Records with this protocol cannot have thier fields validated.", file=sys.stderr)
            ## Type is enforced by the base_schema.
            # elif not silent == "full":
            #     print("Warning:  The parent_protocol field of the protocol, " + protocol + \
            #           ", from the input JSON is not a string value." +\
            #           " Records with this protocol cannot have thier fields validated.", file=sys.stderr)
        elif protocol not in cv["parent_protocol"] and not silent == "full":
            print("Warning:  The protocol from the input JSON, " + protocol + \
                  ", is not in the parent_protocol table of the controlled vocabulary, " +\
                  "nor does it have a parent_protocol field." +\
                  " Records with this protocol cannot have thier fields validated.", file=sys.stderr)
    
    for protocol, parent in protocols_to_add.items():
        cv[protocol] = {}
        cv["parent_protocol"][protocol] = {"parent_id":parent}
    return cv


def build_CV_schema(cv):
    protocol_fields = {}
    for protocol, attributes in cv["parent_protocol"].items():
        ancestors = []
        while (parent_name := attributes.get("parent_id")):
            ancestors.append(parent_name)
            if not parent_name in cv["parent_protocol"]:
                break
            attributes = cv["parent_protocol"][parent_name]
        ancestors.reverse()
        
        fields = {}
        for ancestor in ancestors:
            if ancestor in cv:
                fields.update(cv[ancestor])
        
        if protocol in cv:
            fields.update(cv[protocol])
        if fields:
            protocol_fields[protocol] = fields
        
    
    json_schema_numeric_keywords = ["multipleOf", "maximum", "minimum", 
                                    "exclusiveMaximum", "exclusiveMinimum"]

    json_schema_integer_keywords = ["minLength", "maxLength", "minItems", "maxItems", 
                                    "maxContains", "minContains",
                                    "minProperties", "maxProperties"]

    json_schema_complex_keywords = ["allOf", "anyOf", "oneOf", "not", "if", "then", "else",
                                    "properties", "additionalProperties", "dependentSchemas",
                                    "unevaluatedProperties", "unevaluatedItems", "items",
                                    "prefixItems", "contains", "patternProperties", "propertyNames",
                                    "$vocabulary", "$defs", "dependentRequired", "const"]

    json_schema_boolean_keywords = ["uniqueItems"]
    
    ## TODO dependentRequired could be done the same as required, but with a list value instead of boolean. Look at other keywords and see if want to add support.
    allOf = {}
    for protocol, fields in protocol_fields.items():
        
        properties = {}
        required = {}
        for field, field_attributes in fields.items():
            if field_attributes["table"] not in properties:
                properties[field_attributes["table"]] = {}
            properties[field_attributes["table"]][field] = {}
            if field_attributes["table"] not in required:
                required[field_attributes["table"]] = []
            for schema_keyword, keyword_value in field_attributes.items():
                if keyword_value is not None:
                    if schema_keyword == "required":
                        if (isinstance(keyword_value, bool) and keyword_value) or \
                           (isinstance(keyword_value, str) and keyword_value.lower() == "true"):
                               required[field_attributes["table"]].append(field)
                    ## String values might need conversion to other things.
                    elif isinstance(keyword_value, str):
                        if keyword_value:
                            if schema_keyword in json_schema_numeric_keywords:
                                properties[field_attributes["table"]][field][schema_keyword] = float(keyword_value)
                            elif schema_keyword in json_schema_integer_keywords:
                                properties[field_attributes["table"]][field][schema_keyword] = int(keyword_value)
                            elif schema_keyword in json_schema_complex_keywords:
                                properties[field_attributes["table"]][field][schema_keyword] = eval(keyword_value)
                            elif schema_keyword in json_schema_boolean_keywords:
                                properties[field_attributes["table"]][field][schema_keyword] = True if keyword_value.lower() == "true" else False
                            else:
                                properties[field_attributes["table"]][field][schema_keyword] = keyword_value
                    else:
                        properties[field_attributes["table"]][field][schema_keyword] = keyword_value
                        
        for table in properties:
            if table == "protocol":
                if_subschema = {
                                  "anyOf":[
                                      {"properties":{"id":{"const":protocol}},
                                      "required":["id"]},
                                      {"properties":{"parent_id":{"anyOf":[
                                                                  {"const":protocol}, 
                                                                  {"type":"array",
                                                                   "contains":{"const":protocol}}
                                                                  ]}},
                                      "required":["parent_id"]}
                                      ]
                                }
            else:
                if_subschema = {
                                "properties":{"protocol.id":{"anyOf":[
                                                            {"const":protocol}, 
                                                            {"type":"array",
                                                             "contains":{"const":protocol}}
                                                            ]}},
                                "required":["protocol.id"]
                                }
            
            then_subschema = {"properties":properties[table]}
            if required[table]:
                then_subschema["required"] = required[table]
                
            allof_subschema = {"if":if_subschema, "then":then_subschema}
            if table in allOf:
                allOf[table].append(allof_subschema)
            else:
                allOf[table] = [allof_subschema]
                
    for table, schema in allOf.items():
        base_schema["properties"][table]["additionalProperties"]["allOf"] = schema
        
    return base_schema


def id_check(JSON_file):
    """
    Loops over JSON_file and makes sure each field with a period in the name is an id, that each id points to an 
    existing id in another table that exists in JSON_file, that each "parent_id" field points to another record that exists 
    in the same table, and that each "id" field  has a value that is the same as the name of the record.
    
    There are special cases for the subject and sample tables. Their parent_id's can point to other tables, so they are 
    handled special. As of now protocol.id is also handled special since it can be a list."""
    
    
    for table_name, table_records in JSON_file.items():
        for record_name, record_fields in table_records.items():
            for field_name, field_value in record_fields.items():
            
                if re_match := re.match("(.*)\.(.*)", field_name):
                        if re_match.group(2) != "id":
                            print("Error:  In the " + table_name + " table of the input JSON, the record \"" +\
                                  record_name + "\" has a field, " + field_name + \
                                  ", with a period in the name, but it is not an id.", file=sys.stderr)
                           
                        elif not re_match.group(1) in JSON_file:
                            print("Error:  In the " + table_name + " table of the input JSON, the record \"" + \
                                  record_name + "\" has a field, " + field_name + ", that is an id to another table, " + \
                                  re_match.group(1) + ", but that table is not in the input JSON.", file=sys.stderr)

                        elif isinstance(field_value, list) and \
                             len(bad_values := [value for value in field_value if value not in JSON_file[re_match.group(1)]]) > 0:
                            print("Error:  In the " + table_name + " table of the input JSON, the record \"" + \
                                  record_name + "\" has a field, " + field_name + ", that has id's to another table, " + \
                                  re_match.group(1) + ", but at least one of the id's are not in the " + \
                                  re_match.group(1) + " table.", file=sys.stderr)
                            print("The id's are: \n" + '\n'.join(bad_values), file=sys.stderr)
                        
                        elif isinstance(field_value, str) and not field_value in JSON_file[re_match.group(1)]:
                            print("Error:  In the " + table_name + " table of the input JSON, the record \"" + \
                                  record_name + "\" has a field, " + field_name + ", that is an id to another table, " + \
                                  re_match.group(1) + ", but that id, " + field_value + ", is not in the " + \
                                  re_match.group(1) + " table.", file=sys.stderr)

                elif field_name == "parent_id":
                    
                    ## parent_id and lineage of protocols is checked more rigoroursly in another function. Just ignore it here.
                    if table_name == "protocol" :
                        continue
                    
                    if field_value not in table_records:
                        print("Error:  In the " + table_name + " table of the input JSON, the record \"" + \
                              record_name + "\" has a parent_id, " + field_value + ", but this parent is not in the " + \
                              table_name + " table.", file=sys.stderr)
                    
                    ## If a subject has a parent_id it must be a sample.
                    elif table_name == "entity" :
                                                
                        if "type" in record_fields:
                            if record_fields["type"] == "subject" and "type" in table_records[field_value] and not table_records[field_value]["type"] == "sample":
                                print("Error:  In the " + table_name + " table of the input JSON, the subject type record \"" + \
                                      record_name + "\" has a parent_id, " + field_value + \
                                      ", but this parent is not a sample.", file=sys.stderr)

                ## The logic to let the id field be blank here is because it is checked elsewhere and we don't want to double print messages.
                elif field_name == "id" and not "".join(field_value.split()) == "" and not field_value == record_name:
                    print("Error:  In the " + table_name + " table of the input JSON, the record \"" + \
                          record_name + "\" has an id, " + field_value + \
                          ", but this is not the same as its own name.", file=sys.stderr)



def validate_parent_id(table, table_name, entity_name, check_type, type_keyword="type"):    
    has_errors = False
    for entity, attributes in table.items():
        if parent_name := attributes.get("parent_id"):
            ancestors = []
            parent_attributes = attributes
            while (parent_name := parent_attributes.get("parent_id")):
                if parent_name in ancestors:
                    print("Error:  The " + entity_name + ", \"" + entity + "\", in the \"" + \
                          table_name + "\" table has a circular ancestry, i.e., somewhere in the lineage a " + \
                          entity_name + " has a \"parent_id\" to a child in the lineage.", file=sys.stderr)
                    has_errors = True
                    break
                ancestors.append(parent_name)
                if not parent_name in table:
                    break
                parent_attributes = table[parent_name]
            
            parent_name = attributes["parent_id"]
            if parent_name == entity:
                print("Error:  The " + entity_name + ", \"" + entity + "\", in the \"" + \
                      table_name + "\" table has itself listed for its parent_id. " + \
                      "Records cannot be their own parents.", file=sys.stderr)
                has_errors = True
            
            if parent_name not in table:
                print("Error:  The parent " + entity_name + ", \"" + parent_name + \
                      "\", for the " + entity_name + " \"" + entity + \
                      "\" in the \"" + table_name + "\" table is not itself in the \"" + \
                      table_name + "\" table. " +\
                      "Parent entities must be in the table as well.", file=sys.stderr)
                has_errors = True
                        
            elif check_type and (type_to_check := attributes.get(type_keyword)) and \
               (parent_type := table[parent_name].get(type_keyword)) and \
               type_to_check != parent_type:
                print("Error:  The " + entity_name + ", \"" + entity + \
                      "\", does not have the same " + type_keyword + " as its parent \"" + \
                      parent_name + "\".", file=sys.stderr)
                has_errors = True
            
    return has_errors


def iterate_string_or_list(str_or_list):
    """If str_or_list is a string then make it into a list and return the items for looping. 
    If str_or_list is a list then return the items for looping."""
    if isinstance(str_or_list, list):
        return str_or_list
    else:
        return [str_or_list]
    
    
def SS_protocol_check(input_json):
    """Loops over the sample or subject table in input_json depending on the value of sample_or_subject
    and makes sure that each sample/subject has protocols of the correct type depending on its inheritance. 
    Samples that have a sample parent must have a sample_prep type protocol.
    Samples that have a subject parent must have a collection type protocol.
    Subjects must have a treatment type protocol."""
        
    if "protocol" not in input_json or "entity" not in input_json:
        return
    
    for entity_name, entity_fields in input_json["entity"].items() :
        
        if (protocol_values := entity_fields.get("protocol.id")) and \
           (isinstance(protocol_values, str) or isinstance(protocol_values, list)):
            has_type_sample_prep = False 
            has_type_collection = False
            has_type_treatment = False
            
            for protocol_name in iterate_string_or_list(entity_fields["protocol.id"]):
                if protocol_name in input_json["protocol"] and (protocol_type := input_json["protocol"][protocol_name].get("type")):
                    if protocol_type == "sample_prep":
                        has_type_sample_prep = True
                    elif protocol_type == "collection":
                        has_type_collection = True
                    elif protocol_type == "treatment":
                        has_type_treatment = True                                    
                                    
            if (entity_type := entity_fields.get("type")):
            
                if entity_type == "sample" and (parent := entity_fields.get("parent_id")):
                    ## If the sample has a parent and it is a sample then it must have a sample_prep type protocol.
                    if (parent_attributes := input_json["entity"].get(parent)) and \
                       (parent_type := parent_attributes.get("type")):
                        
                        if parent_type == "sample" and not has_type_sample_prep: 
                            print("Error:  Sample " + entity_name + \
                                  " came from a sample, but does not have a sample_prep protocol.", file=sys.stderr)
                            
                        ## If the sample has a parent and it is a subject then it must have a collection type protocol.        
                        elif parent_type == "subject" and not has_type_collection:
                            print("Error:  Sample " + entity_name + \
                                  " came from a subject, but does not have a collection protocol.", file=sys.stderr)                
                        
                ## Check that each subject has a treatment type protocol.            
                if entity_type == "subject" and not has_type_treatment:
                    print("Error:  Subject " + entity_name + " does not have a treatment type protocol.", file=sys.stderr)


def measurement_protocol_check(input_json):
    """Loops over the measurement table in input_json and makes sure that each measurement 
    has at least one measurement type protocol."""
        
    if "measurement" not in input_json or "protocol" not in input_json:
        return
            
    for measurement_name, measurement_fields in input_json["measurement"].items():
        if "protocol.id" in measurement_fields:
            has_type_measurement = False
            
            for protocol_name in iterate_string_or_list(measurement_fields["protocol.id"]):
                if protocol_name in input_json["protocol"] and \
                   (protocol_type := input_json["protocol"][protocol_name].get("type")):
                    if protocol_type == "measurement":
                        has_type_measurement = True
                        break

            if not has_type_measurement:
                print("Error:  Measurement " + measurement_name + \
                      " does not have a measurement type protocol.", file=sys.stderr)


def protocol_all_used_check(input_json, tables_with_protocols):
    """Compiles a list of all of the protocols used by the subjects, samples, and measurements in the subject and sample table 
    of the input_json and checks that every protocol in the protocol table is in that list. For any protocols 
    that appear in the protocol table, but are not used by a subject, sample, or measurement a warning is printed."""
    
    if not "protocol" in input_json:
        return
    
    used_protocols = set()
    
    for table_name in tables_with_protocols:
        if table_name in input_json:
            for fields in input_json[table_name].values():
                if (protocol_values := fields.get("protocol.id")) and \
                   (isinstance(protocol_values, str) or isinstance(protocol_values, list)):
                    for protocol_name in iterate_string_or_list(fields["protocol.id"]):
                        used_protocols.add(protocol_name)                    
    
    ## For every protocol that is in the protocol table but is not used print a warning.          
    for protocol_name in set(input_json["protocol"]) - used_protocols:
        print("Warning:  The protocol, " + protocol_name + \
              ", in the protocol table of the input JSON is not used by any of the entities or measurements.", file=sys.stderr)


def indexes_of_duplicates_in_list(list_of_interest, value_to_find):
    """Returns a list of all of the indexes in list_of_interest where the value equals value_to_find."""

    current_index = 0
    indexes = []

    while True:
        try:
            next_index = list_of_interest.index(value_to_find, current_index)            
        except ValueError:
            break
        else:
            indexes.append(next_index)
            current_index = next_index + 1
        
    return indexes


def protocol_description_check(input_json):
    """Checks that every description field for the protocols in the protocol table of the metadata are unique."""
    
    if not "protocol" in input_json:
        return
    
    protocols_with_descriptions = [protocol_name for protocol_name, protocol_fields in input_json["protocol"].items() if "description" in protocol_fields]
    descriptions = [protocol_fields["description"] for protocol_name, protocol_fields in input_json["protocol"].items() if "description" in protocol_fields]
    protocols_with_matching_descriptions = [indexes_of_duplicates_in_list(descriptions, description) for description in descriptions]
    
    protocols_with_matching_descriptions.sort()
    protocols_with_matching_descriptions = list(group for group,_ in itertools.groupby(protocols_with_matching_descriptions))
    
    for i in range(len(protocols_with_matching_descriptions)):
        if len(protocols_with_matching_descriptions[i]) > 1:
            protocols_to_print = [protocols_with_descriptions[index] for index in protocols_with_matching_descriptions[i]]
            print("Warning: The protocols: \n\n" + "\n".join(protocols_to_print) + "\n\nhave the exact same descriptions.", file=sys.stderr)
                

def factors_checks(input_json, silent):
    """Checks that every factor in the factor table is used at least once by a an entity and other checks."""

    if "factor" not in input_json or "entity" not in input_json:
        return
        
    used_factors = {}
    valid_factors = {}
    for factor_name, factor_fields in input_json["factor"].items():
        if (field := factor_fields.get("field")) and \
            (allowed_values := factor_fields.get("allowed_values")):
            used_factors[factor_name] = {value:False for value in allowed_values}
            valid_factors[factor_name] = {"field":field, "allowed_values":allowed_values}
    
    for entity_name, entity_attributes in input_json["entity"].items():
        for factor_name, factor_fields in valid_factors.items():
            field = factor_fields["field"]
            allowed_values = factor_fields["allowed_values"]
            if entity_factor_value := entity_attributes.get(field):
                if isinstance(entity_factor_value, str):
                    if entity_factor_value in allowed_values:
                        used_factors[factor_name][entity_factor_value] = True
                    elif not (silent == "full" or silent == "nuisance"):
                        print("Warning:  The entity, " + entity_name + \
                              ", has a value, " + entity_factor_value + ", in the field, " + \
                              field + ", that is not in the allowed values of the factor, " + \
                              factor_name + ".", file=sys.stderr)
                elif isinstance(entity_factor_value, list):
                    values_in_allowed_values = [value for value in entity_factor_value if value in allowed_values]
                    if len(values_in_allowed_values) == 1:
                        used_factors[factor_name][values_in_allowed_values[0]] = True
                    elif len(values_in_allowed_values) > 1:
                        print("Error:  The entity, " + entity_name + \
                              ", has more than 1 value in the field, " + \
                              field + ", that is in the allowed values of the factor, " + \
                              factor_name + ". Entities can only have 1 value from each factor.", file=sys.stderr)
                    elif not (silent == "nuisance" or silent == "full"):
                        print("Warning:  The entity, " + entity_name + \
                              ", has no values in the field, " + \
                              field + ", that are in the allowed values of the factor, " + \
                              factor_name + ".", file=sys.stderr)
                elif not silent == "full":
                    print("Warning:  The entity, " + entity_name + \
                          ", has a field, " + \
                          field + ", that is a field for the factor, " + \
                          factor_name + ", but it is not a string or list type.", file=sys.stderr)
                    
    for factor_name, allowed_values in used_factors.items():
        if unused_values := [value_name for value_name, value_used in allowed_values.items() if not value_used]:
            if len(unused_values) == len(allowed_values) and not silent == "full":
                print("Warning:  The factor, " + factor_name + ", was not used by any of the entities.", file=sys.stderr)
            elif not silent == "full":
                for unused_value in unused_values:
                    print("Warning:  The allowed value, " + unused_value + \
                          ", for the factor, " + factor_name + \
                          ", in the factor table of the input JSON is not used by any of the entities.", file=sys.stderr)





def run_json_command(input_json_source:str, cv_source: str|None, additional_schema_source: str|None, 
                     no_base_schema: bool = False, no_extra_checks: bool = False, is_csv: bool = False, 
                     is_xlsx: bool = False, is_json: bool = False, silent: str = "none") -> None:
    """
    """
    if cv_source:
        controlled_vocabulary = read_and_validate_controlled_vocabulary(cv_source, is_csv, is_xlsx, is_json, False, silent)
    ## Read in JSON_schema if given.
    if additional_schema_source:
        user_json_schema = read_in_JSON_file(additional_schema_source, "additional schema")
        if validate_JSON_schema(user_json_schema):
            print("Error:  The provided additional JSON schema is not valid, so execution stops here.", file=sys.stderr)
            sys.exit()
    else:
        user_json_schema = {}
    
    ## Read in input_JSON.
    input_json = read_in_JSON_file(input_json_source, "input JSON")
    
    ## Build CV and combine with base_schema depending on options and validate.
    if cv_source:
        if "protocol" in input_json:
            add_protocols_to_CV(input_json["protocol"], controlled_vocabulary, silent)
        composite_schema = build_CV_schema(controlled_vocabulary)
        if validate_JSON_schema(composite_schema):
            print("Error:  The schema created from the controlled vocabulary is not valid. " +\
                  "Please look at the errors and fix them to validate the input JSON. " +\
                  "The save-schema command can be used to save the created schema.", file=sys.stderr)
            sys.exit()
    elif not no_base_schema:
        composite_schema = base_schema
    else:
        composite_schema = {}
    
    ## Determine the validator for the schema and replace numeric and integer formats by type casting them.
    validator = create_validator(composite_schema)
    convert_formats(validator, input_json)
    
    # validate_with_arbitrary_schema(input_json, composite_schema)
    print_better_error_messages(validator.iter_errors(input_json))
    
    ## Do additional checks JSON Schema can't do.
    if not no_extra_checks:
        check_type_tables = {"protocol":"type"}
        for table_name, table in input_json.items():
            validate_parent_id(table, table_name, table_name, 
                              True if table_name in check_type_tables else False, 
                              check_type_tables[table_name] if table_name in check_type_tables else "type")
        id_check(input_json)
        SS_protocol_check(input_json)
        measurement_protocol_check(input_json)
        factors_checks(input_json, silent)
        if not silent == "full":
            protocol_all_used_check(input_json, ["entity", "measurement"])
            protocol_description_check(input_json)
    
    ## Do additional schema validation if user provided it.
    if additional_schema_source:
        ## Determine the validator for the schema and replace numeric and integer formats by type casting them.
        validator = create_validator(user_json_schema)
        convert_formats(validator, input_json)
        
        # validate_with_arbitrary_schema(input_json, user_json_schema)
        print_better_error_messages(validator.iter_errors(input_json))


def run_save_schema_command(cv_source: str|None, output_schema_path: str|None, input_json_path: str|None,
                            is_csv: bool = False, is_xlsx: bool = False, is_json: bool = False, 
                            silent: str = "none") -> None:
    """
    """
    if cv_source:
        controlled_vocabulary = read_and_validate_controlled_vocabulary(cv_source, is_csv, is_xlsx, is_json, False, silent)
        if input_json_path:
            input_json = read_in_JSON_file(input_json_path, "input JSON")
            if "protocol" in input_json:
                add_protocols_to_CV(input_json["protocol"], controlled_vocabulary, silent)
        composite_schema = build_CV_schema(controlled_vocabulary)
        if validate_JSON_schema(composite_schema) and not silent == "full":
            print("Warning:  The schema created from the controlled vocabulary is not valid.", file=sys.stderr)
    else:
        composite_schema = base_schema
    
    if output_schema_path == "-":
        print(json.dumps(composite_schema, indent=2))
    else:
        if re.match(r".*\.json$", output_schema_path):
            json_save_name = output_schema_path
        else:
            json_save_name = output_schema_path + ".json"
        
        with open(json_save_name,'w') as jsonFile:
            jsonFile.write(json.dumps(composite_schema, indent=2))


def run_schema_command(input_schema_source: str) -> None:
    """
    """
    user_json_schema = read_in_JSON_file(input_schema_source, "input schema")
    if not validate_JSON_schema(user_json_schema):
        print("No errors. This is a valid JSON schema.")


def run_cv_command(cv_source: str|None, is_csv: bool = False, is_xlsx: bool = False, 
                   is_json: bool = False, silent: str = "none") -> None:
    """
    """
    controlled_vocabulary = read_and_validate_controlled_vocabulary(cv_source, is_csv, is_xlsx, is_json, True, silent)
    composite_schema = build_CV_schema(controlled_vocabulary)
    if validate_JSON_schema(composite_schema) and not silent == "full":
        print("Warning:  The schema created from the controlled vocabulary is not valid.", file=sys.stderr)



