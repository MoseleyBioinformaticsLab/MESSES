# -*- coding: utf-8 -*-
"""
Validate JSON files.

Usage:
    messes validate json <input_JSON> [<controlled_vocabulary> <JSON_schema> --no_base_schema --silent]
    messes validate schema <JSON_schema>
    messes validate print [--save <output_name>]
    messes validate --help
    
    <controlled_vocabulary> - can be a JSON, csv, or xlsx file. If xlsx the default sheet name to read in is #validate, 
                              to specify a different sheet name separate it from the file name with a colon ex: file_name.xlsx:sheet_name.
    <JSON_schema> - must be a valid JSON Schema file.

Options:
    -h, --help                           - show this screen.
    -v, --version                        - show version.
    --silent                             - silence all warnings.
    --no_base_schema                     - don't validate with the base JSON schema.
    --save <output_name>                 - save the base JSON to file.
    
    

"""

import re
import sys
import io
import json
import pathlib

import docopt
import jsonschema
import pandas

from messes import __version__
from messes.extract import extract
from messes.validate import base_schema


def main() :
    args = docopt.docopt(__doc__, version=__version__)
    
    ## Handle schema command.
    if args["schema"]:
        user_json_schema = read_in_JSON_file(args["<JSON_schema>"], "<JSON_schema>")
        if not validate_JSON_schema(user_json_schema):
            print("No errors. This is a valid JSON schema.")
        sys.exit()
        
        
    ## Handle print command
    if args["print"]:
        print(base_schema)
        if args["<output_name>"]:
            if re.match(r".*\.json$", args["<output_name>"]):
                json_save_name = args["<output_name>"]
            else:
                json_save_name = args["<output_name>"] + ".json"
            
            with open(json_save_name,'w') as jsonFile:
                jsonFile.write(json.dumps(base_schema, indent=2))
        sys.exit()
        
    
    ## Handle json command.
    ## Read in controlled_vocabulary if given.
    if args["<controlled_vocabulary>"]:
        controlled_vocabulary = read_in_controlled_vocabulary(args["<controlled_vocabulary>"])
    else:
        controlled_vocabulary = {}
        
    ## Read in JSON_schema if given.
    if args["<JSON_schema>"]:
        user_json_schema = read_in_JSON_file(args["<JSON_schema>"], "<JSON_schema>")
        if validate_JSON_schema(user_json_schema):
            print("Error: The provided <JSON_schema> is not valid, so execution stops here.", file=sys.stderr)
            sys.exit()
    else:
        user_json_schema = {}
    
    ## Read in input_JSON.
    input_json = read_in_JSON_file(args["<input_JSON>"], "<input_JSON>")
        
    
    
    
    
    ## validate a json schema
    validator = jsonschema.validators.validator_for(schema)
    try:
        validator.check_schema(schema)
    except jsonschema.SchemaError:
        print("Error: The schema for index " + str(i) + " in the input JSON schema list is not valid JSON Schema.")
        sys.exit()
        
    
    
    ## Find all errors in validation.
    validator = jsonschema.Draft202012Validator(miagis_schema.metadata_schema)
    errors_generator = validator.iter_errors(metadata)
    print_better_error_messages(errors_generator)
    
    
    
    
def print_better_error_messages(errors_generator) -> None:
    for error in errors_generator:
        
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
            custom_message = " must be \"FAIR\", so it can only include the letters F, A, I, and R in that order, case-insensitive."
        elif error.validator == "minimum":
            custom_message = " must be greater than or equal to " + str(error.validator_value) + "."
        elif error.validator == "maximum":
            custom_message = " must be less than or equal to " + str(error.validator_value) + "."
        else:
            print(error.message, file=sys.stderr)
        
        
        if custom_message:
            message = message + "The value for " + "[%s]" % "][".join(repr(index) for index in error.relative_path) + custom_message
        print(message, file=sys.stderr)
    
    
    
def read_in_controlled_vocabulary(filepath) -> dict:
    if re.search(r".*(\.xls[xm]?|\.csv)", filepath):
        default_sheet_name = False
        if re.search(r"\.xls[xm]?$", filepath):
            filepath += ":#validate"
            default_sheet_name = True
        tagParser = extract.TagParser()
        ## In order to print error messages correctly we have to know if loadSheet printed a message or not, so temporarily replace stderr.
        old_stderr = sys.stderr
        sys.stderr = buffer = io.StringIO()
        if worksheet_tuple := tagParser.loadSheet(filepath, isDefaultSearch=default_sheet_name):
            tagParser.parseSheet(*worksheet_tuple)
            controlled_vocabulary = tagParser.extraction
            sys.stderr = old_stderr
        else:
            sys.stderr = old_stderr
            if buffer.getvalue():
                ## Have to trim the extra newline off the end of buffer.
                print(buffer.getvalue()[0:-1], file=sys.stderr)
            elif default_sheet_name:
                print("Error: No sheet name was given for the xlsx file, so the default name " +\
                      "of #validate was used, but it was not found in the file.", file=sys.stderr)
            sys.exit()
    
    elif re.match(r".*\.json$", filepath):
        with open(filepath, 'r') as jsonFile:
            controlled_vocabulary = json.load(jsonFile)
    
    else:
        print("Error: Unknown file type for the controlled vocabulary file.", file=sys.stderr)
        sys.exit()
        
    return controlled_vocabulary
            
    
    
def read_in_JSON_file(filepath, filename) -> dict:
    if not pathlib.Path(filepath).exists():
        print("Error: The value entered for " + filename + ", " + filepath + ", is not a valid file path or does not exist.", file=sys.stderr)
        sys.exit()
    try:
        with open(filepath, 'r') as jsonFile:
            user_json = json.load(jsonFile)
    except Exception as e:
        print("\nError: An error was encountered when trying to read in the " + filename + ", " + filepath + ".\n", file=sys.stderr)
        raise e
        
    return user_json
    


def validate_JSON_schema(user_json_schema) -> bool:
    validator_for_user_schema = jsonschema.validators.validator_for(user_json_schema)
    validator_for_meta_schema = jsonschema.validators.validator_for(validator_for_user_schema.META_SCHEMA)
    validator = validator_for_meta_schema(validator_for_meta_schema.META_SCHEMA)
    has_errors = False
    for error in validator.iter_errors(user_json_schema):
        print(error)
        has_errors = True
        
    return has_errors




