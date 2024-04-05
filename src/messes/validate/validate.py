# -*- coding: utf-8 -*-
"""
Validate JSON files.

Usage:
    messes validate json <input_JSON> [--pds=<pds> [--csv | --xlsx | --json | --gs] | --no_base_schema] 
                                      [--no_extra_checks]
                                      [--additional=<add_schema>...] 
                                      [--format=<format>]
                                      [--silent=<level>]
    messes validate save-schema <output_schema> [--input=<input_JSON>] 
                                                [--pds=<pds> [--csv | --xlsx | --json | --gs]] 
                                                [--format=<format>]
                                                [--silent=<level>]
    messes validate schema <input_schema>
    messes validate pds <pds> [--csv | --xlsx | --json | --gs] [--silent=<level>] [--save=<output_name>]
    messes validate pds-to-table <pds_json> <output_name> [<output_filetype>]
    messes validate pds-to-json <pds_tabular> [--csv | --xlsx | --gs] <output_name>
    messes validate cd-to-json-schema <conversion_directives> [--csv | --xlsx | --json | --gs] <output_schema>
    messes validate --help
    
    <input_JSON> - if '-' read from standard input.
    <pds> - can be a JSON, csv, xlsx, or Google Sheets file. If xlsx or Google Sheets, the default sheet name to read in is #validate, 
           to specify a different sheet name separate it from the file name with a colon ex: file_name.xlsx:sheet_name.
           If '-' read from standard input.
    <input_schema> - must be a valid JSON Schema file. If '-' read from standard input.
    <output_schema> - if '-' save to standard output.
    <output_name> - path to save tabular pds to, if '-' save to standard output as CSV.
    <output_filetype> - "xlsx" or "csv", defaults to "csv".
    <conversion_directives> - can be a JSON, csv, xlsx, or Google Sheets file. If xlsx or Google Sheets, 
                              the default sheet name to read in is #convert, to specify a different 
                              sheet name separate it from the file name with a colon ex: file_name.xlsx:sheet_name.
                              If '-' read from standard input.

Options:
    -h, --help                           - show this screen.
    -v, --version                        - show version.
    --silent <level>                     - if "full" silence all warnings, 
                                           if "nuisance" silence warnings that are more likely to be a nuisance,
                                           if "none" do not silence warnings [default: none].
    --pds <pds>                            - a protocol-dependent schema file, can be a JSON, csv, or xlsx file. 
                                           If xlsx the default sheet name to read in is #validate, to specify 
                                           a different sheet name separate it from the file name with a colon 
                                           ex: file_name.xlsx:sheet_name.
    --csv                                - indicates that the protocol-dependent schema file is a csv (comma delimited) file.
    --xlsx                               - indicates that the protocol-dependent schema file is an xlsx (Excel) file.
    --json                               - indicates that the protocol-dependent schema file is a JSON file.
    --gs                                 - indicates that the protocol-dependent schema file is a Google Sheets file.
                                           If a file type is not given then it will be guessed from the file extension.
    --additional <add_schema>            - an additional JSON Schema file that will be used to validate <input_JSON>.
    --format <format>                    - additional validation done for the desired supported format. 
                                           Current supported formats: 
                                               mwtab
    --no_base_schema                     - don't validate with the base JSON schema.
    --no_extra_checks                    - only do JSON Schema validation and nothing else.
    --input <input_JSON>                 - optionally give an input JSON file to save-schema to reproduce the 
                                           schema used to validate in the json command.
    --save <output_name>                 - save the JSON Schema created from the protocol-dependent schema.
    

The "json" command will validate the <input_JSON> against the internal base_schema, and optional schema provided 
by the --pds and --additional options. To validate only against a provided schema, use the --additional and --no_base_schema options.

The "save-schema" command will save the internal base_schema to the <output_schema> location. If --pds is given 
then it will be parsed and placed into the base_schema. If --input is given, the protocols table will be added 
in with the PDS to reproduce what happens in the json command. If --format is used, then that format schema is 
saved instead of the base_schema.

The "schema" command will validate the <input_schema> against the JSON Schema meta schema.

The "pds" command will validate that the <pds> file is a valid protocol-dependent schema file. 
If the --save option is given, then save the built JSON Schema.

The "pds-to-table" command will read in a protocol-dependent schema in JSON form and save it out in a tabular form.

The "pds-to-json" command will read in a protocol-dependent schema in tabular form and save it out in a JSON form. 

The "cd-to-json-schema" command will read in conversion directives and create a JSON Schema 
template file that can be filled in and used to validate files that will be converted using those directives.
"""

## TODO What about adding a check so that attribute fields of list fields have to be the same length as the parent field? for data_files and data_files%entity_id

import re
import sys
import io
import json
import pathlib
import itertools
from typing import Any
from collections.abc import Iterable

import docopt
import jsonschema

from messes import __version__
from messes.extract import extract
from messes.validate.validate_schema import base_schema, PD_schema, mwtab_schema
from messes.convert.convert import directives_to_table, literal_regex
from messes.convert import user_input_checking
from messes.convert import convert_schema

supported_formats = ["mwtab"]

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
        run_json_command(args["<input_JSON>"], args["--pds"], args["--additional"], 
                         args["--no_base_schema"], args["--no_extra_checks"], 
                         args["--csv"], args["--xlsx"], args["--json"], args["--gs"], 
                         args["--silent"], args["--format"])
    
    
    #############################    
    ## Handle save-schema command
    #############################
    if args["save-schema"]:
        run_save_schema_command(args["--pds"], args["<output_schema>"], args["--input"],
                                args["--csv"], args["--xlsx"], args["--json"], args["--gs"], 
                                args["--silent"], args["--format"])
    
    
    #########################
    ## Handle schema command.
    #########################
    if args["schema"]:
        run_schema_command(args["<input_schema>"])
        
    
    #####################
    ## Handle pds command.
    #####################
    if args["pds"]:
        run_pds_command(args["<pds>"], args["--save"], args["--csv"], args["--xlsx"], 
                        args["--json"], args["--gs"], args["--silent"])
        
    
    ##########################
    ## Handle pds-to-table command.
    ##########################
    if args["pds-to-table"]:
        run_pds_to_table_command(args["<pds_json>"], args["<output_name>"], 
                                 args["<output_filetype>"], args["--silent"])
        
    
    ##########################
    ## Handle pds-to-json command.
    ##########################
    if args["pds-to-json"]:
        run_pds_to_json_command(args["<pds_tabular>"], args["--csv"], args["--xlsx"], 
                                args["--gs"], args["<output_name>"], args["--silent"])
        
    
    ##########################
    ## Handle pds-to-table command.
    ##########################
    if args["cd-to-json-schema"]:
        run_conversion_directives_to_json_schema_command(args["<conversion_directives>"], 
                                                         args["--csv"], args["--xlsx"], 
                                                         args["--json"], args["--gs"], 
                                                         args["<output_schema>"], args["--silent"])
        
    
    
    
## User defined types.
JSON = dict[str, Any]|list|str|int|float|None
    
def check(self, instance: object, format: str) -> None:
    """Check whether the instance conforms to the given format.
    
    Modified from jsonschema.FormatChecker.check. Used to raise an error on 
    the custom "integer", "str_integer", "numeric", and "str_numeric" formats 
    so their values can be cast to int and float appropriately.

    Args:
        instance: the instance to check
        format: the format that instance should conform to

    Raises:
        FormatError:
            if the instance does not conform to ``format`` 
            if the instance does conform to "integer", "str_integer", "numeric", and "str_numeric" formats
            if the instance is not a string and the format is "str_integer" or "str_numeric"
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
    elif (format == "integer" or format == "str_integer") and isinstance(instance, str):
        raise jsonschema.exceptions.FormatError("safe to convert to int", cause=None) 
    elif (format == "numeric" or format == "str_numeric") and isinstance(instance, str):
        raise jsonschema.exceptions.FormatError("safe to convert to float", cause=None)
    elif (format == "str_integer" or format == "str_numeric") and not isinstance(instance, str):
        raise jsonschema.exceptions.FormatError("not str", cause=None)


def convert_formats(validator: jsonschema.protocols.Validator, instance: dict|str|list) -> dict|str|list:
    """Convert "integer" and "numeric" formats to int and float.
    
    Special function to iterate over JSON schema errors and if the custom "integer", 
    "str_integer", "numeric", and "str_numeric" formats are found, converts that value 
    in the instance to the appropriate type. If the value is not a string and the format 
    is "str_integer" or "str_numeric", prints an error.
    
    Args:
        validator: Validator from the jsonschema library to run iter_errors() on.
        instance: the instance to have its values converted.
        
    Returns:
        The modified instance.
    """
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
        elif error.message == "not str":
            path = "[%s]" % "][".join(repr(index) for index in error.relative_path)
            print("Error:  The value for " + path + " is not of type \"string\".", file=sys.stderr)
            
            
    jsonschema.FormatChecker.check = original_check
    
    return instance
    
    
def print_better_error_messages(errors_generator: Iterable[jsonschema.exceptions.ValidationError]) -> bool:
    """Print better error messages for jsonschema validation errors.
    
    Args:
        errors_generator: the generator returned from validator.iter_errors().
    
    Returns:
        True if there were errors, False otherwise.
    """
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
            if error.validator_value == 1 and isinstance(error.instance, str):
                custom_message = " cannot be an empty string."
            else:
                custom_message = " is too short."
        elif error.validator == "maxLength":
            custom_message = " is too long."
        elif error.validator == "minItems":
            if error.validator_value == 1:
                custom_message = " cannot be empty."
            else:
                custom_message = " must have at least " + str(error.validator_value) + " items."
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
    
    
def read_and_validate_PDS(filepath: str, is_csv: bool, is_xlsx: bool, 
                          is_json: bool, is_gs: bool, no_last_message: bool, silent: str) -> JSON:
    """Read in the protocol-dependent schema from filepath and validate it.
    
    Args:
        filepath: the path to the protocol-dependent schema or "-" meaning to read from stdin.
        is_csv: whether the protocol-dependent schema is a csv file, used for reading from stdin.
        is_xlsx: whether the protocol-dependent schema is a xlsx file.
        is_json: whether the protocol-dependent schema is a json file, used for reading from stdin.
        is_json: whether the protocol-dependent schema is a Google Sheets file.
        no_last_message: if True do not print a message about the protocol-dependent schema being invalid and execution stopping.
        silent: if "full" do not print any warnings, if "nuisance" do not print nuisance warnings.
    
    Returns:
        The protocol-dependent schema.
    
    Raises:
        SystemExit: Will raise errors if filepath does not exist or there is a read in error.
    """
    PDS = read_json_or_tabular_file(filepath, is_csv, is_xlsx, is_json, is_gs, 
                                    "protocol-dependent schema", "#validate", silent)
        
    # if (validate_PDS_parent_protocols(PDS) or validate_with_arbitrary_schema(PDS, PD_schema)) \
    #    and not no_last_message:
    has_errors = validate_PDS_parent_protocols(PDS, silent)
    has_errors = has_errors | print_better_error_messages(create_validator(PD_schema).iter_errors(PDS))
    if has_errors:
        if not no_last_message:
            print("Error:  The provided protocol-dependent schema is not valid, so execution stops here.", file=sys.stderr)
        sys.exit()
        
    return PDS    


def read_json_or_tabular_file(filepath: str, is_csv: bool, is_xlsx: bool, 
                              is_json: bool, is_gs: bool, file_title: str, 
                              default_sheet_name: str, silent: str) -> JSON:
    """Read in a file from filepath.
    
    Args:
        filepath: the path to the file or "-" meaning to read from stdin.
        is_csv: whether the file is a csv file, used for reading from stdin.
        is_xlsx: whether the file is a xlsx file.
        is_json: whether the file is a json file, used for reading from stdin.
        is_json: whether the file is a Google Sheets file.
        file_title: a string to use for printing error messages about the file.
        default_sheet_name: sheet name to default to for Excel and Google Sheets files.
        silent: if "full" do not print any warnings, if "nuisance" do not print nuisance warnings.
    
    Returns:
        The file contents.
    
    Raises:
        SystemExit: Will raise errors if filepath does not exist or there is a read in error.
    """
    from_stdin = False
    if filepath == "-":
        if not is_csv and not is_json:
            ## Have to clear the input or the system prints an extra error.
            sys.stdin.readlines()
            print("Error:  When reading the " + file_title + " from standard input you must specify that it is '--csv' or '--json'.", file=sys.stderr)
            sys.exit()
        filepath = sys.stdin
        from_stdin = True
        
                
    
    if is_csv or is_xlsx or is_gs or \
       (not from_stdin and (re.search(r".*(\.xls[xm]?|\.csv)", filepath) or extract.TagParser.isGoogleSheetsFile(filepath))):
        default_sheet_name_used = False
        sheet_name = None
        if not from_stdin:
            if (reMatch := re.search(r"^(.*\.xls[xm]?):(.*)$", filepath)):
                filepath = reMatch.group(1)
                sheet_name = reMatch.group(2)
            # elif not from_stdin and re.search(r"\.xls[xm]?$", filepath):
            elif re.search(r"\.xls[xm]?$", filepath):
                sheet_name = default_sheet_name
                default_sheet_name_used = True
            elif (reMatch := re.search(r"docs.google.com/spreadsheets/d/([^/]*)/[^:]*$", filepath)):
                filepath = "https://docs.google.com/spreadsheets/d/" + reMatch.group(1) + "/export?format=xlsx"
                sheet_name = default_sheet_name
                default_sheet_name_used = True
            elif (reMatch := re.search(r"docs.google.com/spreadsheets/d/([^/]*)/.*:(.*)$", filepath)):
                filepath = "https://docs.google.com/spreadsheets/d/" + reMatch.group(1) + "/export?format=xlsx"
                sheet_name = reMatch.group(2)
        tagParser = extract.TagParser()
        ## In order to print error messages correctly we have to know if loadSheet printed a message or not, so temporarily replace stderr.
        old_stderr = sys.stderr
        sys.stderr = buffer = io.StringIO()
        try:
            if worksheet_tuple := tagParser.loadSheet(filepath, sheet_name, isDefaultSearch=default_sheet_name_used):
                tagParser.parseSheet(*worksheet_tuple)
                file_contents = tagParser.extraction
                sys.stderr = old_stderr
            else:
                sys.stderr = old_stderr
                if buffer.getvalue():
                    ## Have to trim the extra newline off the end of buffer.
                    print(buffer.getvalue()[0:-1], file=sys.stderr)
                elif default_sheet_name_used:
                    print("Error:  No sheet name was given for the file, so the default name " +\
                          "of " + default_sheet_name + " was used, but it was not found in the file.", file=sys.stderr)
                sys.exit()
        except Exception as e:
            sys.stderr = old_stderr
            if from_stdin:
                print("Error:  A problem was encountered when trying to read the " + file_title + " from stdin. " +\
                      "Make sure the indicated file type is correct.", file=sys.stderr)
                sys.exit()
            raise e
    
    elif is_json or (not from_stdin and re.match(r".*\.json$", filepath)):
        if from_stdin:
            try:
                file_contents = json.load(filepath)
            except Exception:
                print("Error:  A problem was encountered when trying to read the " + file_title + " from stdin. " +\
                      "Make sure the indicated file type is correct.", file=sys.stderr)
                sys.exit()
        elif not pathlib.Path(filepath).exists():
            print("Error:  The value entered for the " + file_title + ", " + filepath + ", is not a valid file path or does not exist.", file=sys.stderr)
            sys.exit()
        else:
            with open(filepath, 'r') as jsonFile:
                file_contents = json.load(jsonFile)
    
    else:
        print("Error:  Unknown file type for the " + file_title + " file.", file=sys.stderr)
        sys.exit()
        
    return file_contents
            
       
def read_in_JSON_file(filepath: str, description: str) -> JSON:
    """Read in a JSON file from filepath.
    
    Args:
        filepath: the path to the JSON file or "-" meaning to read from stdin.
        description: a name for the JSON file to print more specific error messages.
        
    Returns:
        The JSON file.
    
    Raises:
        SystemExit: Will raise errors if filepath does not exist or there is a read in error.
    """
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


def save_out_JSON_file(filepath: str, json_to_save: dict) -> None:
    """Handle renaming and directing JSON to the correct output.
    
    Args:
        filepath: the path to save the JSON file to or "-" meaning to write to stdout.
        json_to_save: the JSON to save out.
    """
    if filepath == "-":
        print(json.dumps(json_to_save, indent=2))
    else:
        if re.match(r".*\.json$", filepath):
            json_save_name = filepath
        else:
            json_save_name = filepath + ".json"
        
        with open(json_save_name,'w') as jsonFile:
            jsonFile.write(json.dumps(json_to_save, indent=2))
            

def validate_JSON_schema(user_json_schema: JSON) -> bool:
    """Validate an arbitrary JSON schema.
    
    Args:
        user_json_schema: JSON schema to validate.
        
    Returns:
        True if there were validation errors, False otherwise.
    """
    validator_for_user_schema = jsonschema.validators.validator_for(user_json_schema)
    validator_for_meta_schema = jsonschema.validators.validator_for(validator_for_user_schema.META_SCHEMA)
    validator = validator_for_meta_schema(validator_for_meta_schema.META_SCHEMA)
    has_errors = False
    for error in validator.iter_errors(user_json_schema):
        print(error, file=sys.stderr)
        has_errors = True
        
    return has_errors


def create_validator(schema: JSON) -> jsonschema.protocols.Validator:
    """Create a validator for the given schema.
    
    Args:
        schema: the JSON schema to create a validator for.
        
    Returns:
        A jsonschema.protocols.Validator to validate the schema with an added format checker 
        that is aware of the custom formats "integer", "str_integer", "numeric", and "str_numeric".
    """
    validator = jsonschema.validators.validator_for(schema)
    format_checker = jsonschema.FormatChecker()
    @format_checker.checks('integer') 
    def is_integer(value):
        if value is not None and isinstance(value, str):
            try:
                float(value)
            except ValueError:
                return False
            return True
        return True
    @format_checker.checks('str_integer') 
    def is_str_integer(value):
        if value is not None and isinstance(value, str):
            try:
                float(value)
            except ValueError:
                return False
            return True
        return True
    @format_checker.checks('numeric') 
    def is_float(value):
        if value is not None and isinstance(value, str):
            try:
                float(value)
            except ValueError:
                return False
            return True
        return True
    @format_checker.checks('str_numeric') 
    def is_str_float(value):
        if value is not None and isinstance(value, str):
            try:
                float(value)
            except ValueError:
                return False
            return True
        return True
    return validator(schema=schema, format_checker=format_checker)


def mwtab_checks(input_json: dict) -> None:
    """Check that the input_json is ready for mwtab conversion.
    
    Run checks that cannot be done by JSON Schema. They are the following:
        Check that at least 1 protocol has the "machine_type" field.
        Check that the first collection protocol has a "sample_type" field.
        Check that there are at least 1 collection type, treatment type, and sample_prep type protocols.
        Check that the first subject has the "species", "species_type", and "taxonomy_id" fields.
    
    Args:
        input_json: the JSON to perform the checks on.
    """
    if protocol_table := input_json.get("protocol"):
        has_machine_type = False
        is_first_collection_type = True
        has_collection_type = False
        has_sample_prep_type = False
        has_treatment_type = False
        for protocol, attributes in protocol_table.items():
            if "machine_type" in attributes:
                has_machine_type = True
            
            if protocol_type := attributes.get("type"):
                if protocol_type == "collection":
                    if is_first_collection_type and "sample_type" not in attributes:
                        print("Error:  The first collection protocol, " + protocol + \
                              ", does not have the required \"sample_type\" field for the mwtab conversion.", file=sys.stderr)
                    is_first_collection_type = False
                    has_collection_type = True
                    
                if protocol_type == "sample_prep":
                    has_sample_prep_type = True
                    
                if protocol_type == "treatment":
                    has_treatment_type = True
                    
    if not has_machine_type:
        print("Error:  No protocols have a \"machine_type\" field used to mark " +\
              "the protocol that contains the instrument information for the mwtab conversion.", file=sys.stderr)
            
    if not has_collection_type:
        print("Error:  There are no \"collection\" type protocols. There must be " +\
              "at least one for the mwtab conversion.", file=sys.stderr)
    
    if not has_sample_prep_type:
        print("Error:  There are no \"sample_prep\" type protocols. There must be " +\
              "at least one for the mwtab conversion.", file=sys.stderr)
            
    if not has_treatment_type:
        print("Error:  There are no \"treatment\" type protocols. There must be " +\
              "at least one for the mwtab conversion.", file=sys.stderr)
            
    
    if entity_table := input_json.get("entity"):
        for entity, attributes in entity_table.items():
            if (entity_type := attributes.get("type")) and entity_type == "subject":
                fields_not_in_subject = [field for field in ["species", "species_type", "taxonomy_id"] if field not in attributes]
                if fields_not_in_subject:
                    print("Error:  The first subject, " + entity + ", does not have the " +\
                          "following required fields for the mwtab conversion:\n" +\
                          "\n".join(fields_not_in_subject), file=sys.stderr)
                break



def validate_PDS_parent_protocols(pds: JSON, silent: str) -> bool:
    """Validate the parent_protocols table of the protocol-dependent schema.
    
    Args:
        pds: the protocol-dependent schema in JSON form.
        silent: if "full" do not print any warnings, if "nuisance" do not print nuisance warnings.
    
    Returns:
        True if there were errors (warnings don't count), False otherwise.
    """
    if not "parent_protocol" in pds:
        return True
    
    has_errors = False
    for protocol, attributes in pds["parent_protocol"].items():
        has_fields = True if pds.get(protocol) else False
        if parent_name := attributes.get("parent_id"):
            ancestors = []
            parent_attributes = attributes
            has_fields = True if pds.get(parent_name) else has_fields
            while (parent_name := parent_attributes.get("parent_id")):
                has_fields = True if pds.get(parent_name) else has_fields
                if parent_name in ancestors:
                    print("Error:  The protocol, \"" + protocol + "\", in the \"parent_protocol\" table " + \
                          "has a circular ancestry, i.e., somewhere in the lineage a protocol has a " +\
                          "\"parent_id\" to a child in the lineage.", file=sys.stderr)
                    has_errors = True
                    break
                ancestors.append(parent_name)
                if not parent_name in pds["parent_protocol"]:
                    break
                parent_attributes = pds["parent_protocol"][parent_name]
            
            if not has_fields and not (silent == "nuisance" or silent == "full"):
                print("Warning:  The protocol, \"" + protocol + "\"," + \
                      "\" in the \"parent_protocol\" table does not itself have any " +\
                      "fields to validate, nor do any of its ancestors.", file=sys.stderr)
            
            parent_name = attributes["parent_id"]
            if parent_name == protocol:
                print("Error:  The protocol, \"" + protocol + "\", in the \"parent_protocol\" table " + \
                      "has itself listed for its parent_id. Protocols cannot be their own parents.", file=sys.stderr)
                has_errors = True
            
            if parent_name not in pds["parent_protocol"]:
                print("Error:  The parent protocol, \"" + parent_name + "\", for the protocol \"" + protocol + \
                      "\" in the \"parent_protocol\" table is not itself in the \"parent_protocol\" table. " +\
                      "Parent entities must be in the table as well.", file=sys.stderr)
                has_errors = True
            
            elif (type_to_check := attributes.get("type")) and (parent_type := pds["parent_protocol"][parent_name].get("type")) and \
               type_to_check != parent_type:
                print("Error:  The protocol, \"" + protocol + "\", does not have the same type as its parent \"" + \
                      parent_name + "\".", file=sys.stderr)
                has_errors = True
            
            if parent_name not in pds and not (silent == "nuisance" or silent == "full"):
                print("Warning:  The parent protocol, \"" + parent_name + "\", for the protocol \"" + protocol + \
                      "\" in the \"parent_protocol\" table is not itself in the protocol-dependent schema. " +\
                      "Parent entities must be in the protocol-dependent schema as well.", file=sys.stderr)
            
        if protocol not in pds and not (silent == "nuisance" or silent == "full"):
            print("Warning:  The protocol, \"" + protocol + \
                  "\" in the \"parent_protocol\" table is not in the protocol-dependent schema.", file=sys.stderr)
    return has_errors



def add_protocols_to_PDS(protocol_table: dict, pds: JSON, silent: str) -> JSON:
    """Add the protocols from the table to the protocol-dependent schema.
    
    Args:
        protocol_table: the protocol table from the input JSON.
        pds: the protocol-dependent schema in JSON form.
        silent: if "full" do not print any warnings, if "nuisance" do not print nuisance warnings.
        
    Returns:
        The updated protocol-dependent schema.
    """
    protocols_to_add = {}
    for protocol, attributes in protocol_table.items():
        if (parent := attributes.get("parent_protocol")) :
            if isinstance(parent, str):
                if parent in pds["parent_protocol"]:
                    protocols_to_add[protocol] = parent
                    if (protocol_type := attributes.get("type")) and \
                        protocol_type != pds["parent_protocol"][parent]["type"] and not silent == "full":
                        print("Warning:  The protocol from the input JSON, " + protocol + \
                              ", does not have the same type as its parent_protocol, " + parent + \
                              ", in the protocol-dependent schema.", file=sys.stderr)
                elif protocol not in pds["parent_protocol"] and not silent == "full":
                    print("Warning:  The protocol from the input JSON, " + protocol + \
                          ", is not in the parent_protocol table of the protocol-dependent schema, " +\
                          "nor does it have a parent_protocol in the protocol-dependent schema." +\
                          " Records with this protocol cannot have thier fields validated.", file=sys.stderr)
            ## Type is enforced by the base_schema.
            # elif not silent == "full":
            #     print("Warning:  The parent_protocol field of the protocol, " + protocol + \
            #           ", from the input JSON is not a string value." +\
            #           " Records with this protocol cannot have thier fields validated.", file=sys.stderr)
        elif protocol not in pds["parent_protocol"] and not silent == "full":
            print("Warning:  The protocol from the input JSON, " + protocol + \
                  ", is not in the parent_protocol table of the protocol-dependent schema, " +\
                  "nor does it have a parent_protocol field." +\
                  " Records with this protocol cannot have thier fields validated.", file=sys.stderr)
    
    for protocol, parent in protocols_to_add.items():
        pds[protocol] = {}
        pds["parent_protocol"][protocol] = {"parent_id":parent}
    return pds


def build_PD_schema(pds: JSON) -> JSON:
    """Build a JSON schema from the protocol-dependent schema.
    
    Args:
        pds: the protocol-dependent schema in JSON form.
    
    Returns:
        A JSON schema created by combining the base schema and a schema created from the protocol-dependent schema.
    """
    protocol_fields = {}
    for protocol, attributes in pds["parent_protocol"].items():
        ancestors = []
        while (parent_name := attributes.get("parent_id")) and parent_name not in ancestors:
            ancestors.append(parent_name)
            if not parent_name in pds["parent_protocol"]:
                break
            attributes = pds["parent_protocol"][parent_name]
        ancestors.reverse()
        
        fields = {}
        for ancestor in ancestors:
            if ancestor in pds:
                fields.update(pds[ancestor])
        
        if protocol in pds:
            fields.update(pds[protocol])
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


def id_check(JSON_file: JSON) -> None:
    """Validate id fields for records in JSON_file.
    
    Loops over JSON_file and makes sure each field with a period in the name is an id, that each id points to an 
    existing id in another table that exists in JSON_file, that each "parent_id" field points to another record that exists 
    in the same table, and that each "id" field  has a value that is the same as the name of the record.
    
    There is a special check for the "entity" table that checks that subject types have a sample type parent. 
    
    Args:
        JSON_file: the JSON to validate ids for.
    """
    
    
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


def validate_parent_id(table: dict, table_name: str, entity_name: str, check_type: bool, type_keyword: str = "type") -> bool:    
    """Validate the "parent_id" fields for the table.
    
    Args:
        table: the table to validate {record_name:{attribute1:value1, ...}, ...}.
        table_name: the name of the table, used for printing better error messages.
        entity_name: name of the entities of the table, used for printing better error messages.
        check_type: if True check that the type of the parent is the same as the child.
        type_keyword: the keyword to use to check the types of the parent and child.
    
    Returns:
        True if there were errors, False otherwise.
    """
    has_errors = False
    for entity, attributes in table.items():
        if parents := attributes.get("parent_id"):
            ancestors = []
            parents = parents if isinstance(parents, list) else [parents]
            no_errors = True
            next_parents = parents
            while next_parents and no_errors:
                parents = next_parents
                next_parents = []
                for parent_name in parents:
                    ancestors.append(parent_name)
                    if parent_name in table and (grandparents := table[parent_name].get("parent_id")):
                        grandparents = grandparents if isinstance(grandparents, list) else [grandparents]
                        for grandparent_name in grandparents:
                            if grandparent_name in ancestors:
                                ## Don't print the circular ancestry message if an entity has itself as a parent.
                                ## This is specifically checked for just below this.
                                if grandparent_name != entity:
                                    print("Error:  The " + entity_name + ", \"" + entity + "\", in the \"" + \
                                          table_name + "\" table has a circular ancestry, i.e., somewhere in the lineage a " + \
                                          entity_name + " has a \"parent_id\" to a child in the lineage.", file=sys.stderr)
                                has_errors = True
                                no_errors = False
                                break
                            next_parents.append(grandparent_name)
                    if not no_errors:
                        break
                                    
            parents = attributes["parent_id"]
            parents = parents if isinstance(parents, list) else [parents]
            for parent_name in parents:
                if parent_name == entity:
                    print("Error:  The " + entity_name + ", \"" + entity + "\", in the \"" + \
                          table_name + "\" table has itself listed in its parent_id. " + \
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


def iterate_string_or_list(str_or_list: str|list) -> list:
    """If str_or_list is a string then make it into a list and return the items for looping.
    
    If str_or_list is a list then return it as is.
    
    Args:
        str_or_list: a string to return as a list containing that string or a list to return as is.
    
    Returns:
        str_or_list as a list.
    """
    if isinstance(str_or_list, list):
        return str_or_list
    else:
        return [str_or_list]
    
    
def SS_protocol_check(input_json: JSON) -> None:
    """Validates the subjects and samples protocols.
    
    Loops over the entity table in input_json and makes sure that each sample/subject 
    has protocols of the correct type depending on its inheritance. 
    Samples that have a sample parent must have a sample_prep type protocol.
    Samples that have a subject parent must have a collection type protocol.
    Subjects must have a treatment type protocol.
    
    Args:
        input_json: the JSON to validate.
    """
        
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


def measurement_protocol_check(input_json: JSON) -> None:
    """Loops over the measurement table in input_json and makes sure that each measurement 
    has at least one measurement type protocol.
    
    Args:
        input_json: the JSON to validate.
    """
        
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


def protocol_all_used_check(input_json: JSON, tables_with_protocols: list[str]) -> None:
    """Validates that all protocols in the protocol table are used at least once.
    
    Compiles a list of all of the protocols used by the records in tables_with_protocols 
    and checks that every protocol in the protocol table is in that list. For any protocols 
    that appear in the protocol table, but are not used by any records a warning is printed.
    
    Args:
        input_json: the JSON to validate.
        tables_with_protocols: the tables in input_json that have records with "protocol.id" fields.
    """
    
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


def indexes_of_duplicates_in_list(list_of_interest: list, value_to_find: Any) -> list[int]:
    """Returns a list of all of the indexes in list_of_interest where the value equals value_to_find.
    
    Args:
        list_of_interest: list to find indexes in.
        value_to_find: value to look for in list_of_interest and find its index.
        
    Returns:
        A list of all the indexes where value_to_find is in list_of_interest.
    """

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


def protocol_description_check(input_json: JSON) -> None:
    """Checks that every description field for the protocols in the protocol table of the metadata are unique.
    
    Args:
        input_json: the JSON to validate.
    """
    
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
                

def factors_checks(input_json: JSON, silent: str) -> None:
    """Validates some logic about the factors.
    
    Checks that every factor in the factor table is used at least once by an entity. 
    Whether or not values in the factor field are allowed values.
    If there are more than 1 allowed values in the factor field.
    That factor fields are str or list types.
    
    Args:
        input_json: the JSON to validate.
        silent: if "full" do not print any warnings, if "nuisance" do not print nuisance warnings.
    """

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


def _check_format(format_check: str|None) -> None:
    """Check that format_check is a supported format.
    
    If format_check is not in supported_formats then print an error and close the program.
    
    Args:
        format_check: format to check if it is supported.
    """
    
    if format_check:
        if format_check not in supported_formats:
            extra_message = '\n   '.join(['"' + supported_format + '"' for supported_format in supported_formats])
            print("Error:  Unknown format, " + format_check + ". Must be one of:\n   " + extra_message, file=sys.stderr)
            sys.exit()


def run_json_command(input_json_source: str, pds_source: str|None, additional_schema_sources: list[str], 
                     no_base_schema: bool = False, no_extra_checks: bool = False, is_csv: bool = False, 
                     is_xlsx: bool = False, is_json: bool = False, is_gs: bool = False, silent: str = "none", 
                     format_check: str|None = None) -> None:
    """Run the json command.
    
    Args:
        input_json_source: either a filepath or "-" to read from stdin.
        pds_source: either a filepath or "-" to read from stdin, if not None.
        additional_schema_sources: either a filepath or "-" to read from stdin, if not None.
        no_base_schema: if True do not validate with the base_schema, ignored if pds_source is given.
        no_extra_checks: if True only do JSON Schema validations.
        is_csv: if True the pds_source is a csv file.
        is_xlsx: if True the pds_source is an xlsx file.
        is_json: if True the pds_source is a JSON file.
        is_gs: if True the pds_source is a Google Sheets file.
        silent: if "full" do not print any warnings, if "nuisance" do not print nuisance warnings.
    """
    
    _check_format(format_check)
    
    if pds_source:
        PDS = read_and_validate_PDS(pds_source, is_csv, is_xlsx, is_json, is_gs, False, silent)
    ## Read in JSON_schema if given.
    if additional_schema_sources:
        user_json_schemas = []
        for additional_schema_source in additional_schema_sources:
            user_json_schema = read_in_JSON_file(additional_schema_source, "additional schema")
            if validate_JSON_schema(user_json_schema):
                print("Error:  The additional JSON schema, " + additional_schema_source + ", is not valid, so execution stops here.", file=sys.stderr)
                sys.exit()
            user_json_schemas.append(user_json_schema)
    # else:
    #     user_json_schema = {}
    
    ## Read in input_JSON.
    input_json = read_in_JSON_file(input_json_source, "input JSON")
    
    ## Build PDS and combine with base_schema depending on options and validate.
    if pds_source:
        if "protocol" in input_json:
            add_protocols_to_PDS(input_json["protocol"], PDS, silent)
        composite_schema = build_PD_schema(PDS)
        if validate_JSON_schema(composite_schema):
            print("Error:  The schema created from the protocol-dependent schema is not valid. " +\
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
    if additional_schema_sources:
        for user_json_schema in user_json_schemas:
            ## Determine the validator for the schema and replace numeric and integer formats by type casting them.
            validator = create_validator(user_json_schema)
            convert_formats(validator, input_json)
            
            # validate_with_arbitrary_schema(input_json, user_json_schema)
            print_better_error_messages(validator.iter_errors(input_json))
        
    match format_check:
        case "mwtab":
            print_better_error_messages(create_validator(mwtab_schema).iter_errors(input_json))
            mwtab_checks(input_json)


def run_save_schema_command(pds_source: str|None, output_schema_path: str, input_json_path: str|None,
                            is_csv: bool = False, is_xlsx: bool = False, is_json: bool = False, 
                            is_gs: bool = False, silent: str = "none", format_check: str|None = None) -> None:
    """Run the save-schema command.
    
    Args:
        pds_source: either a filepath or "-" to read from stdin, if not None.
        output_schema_path: the path to save the output JSON to.
        input_json_path: either a filepath or "-" to read from stdin, if not None.
        is_csv: if True the pds_source is a csv file.
        is_xlsx: if True the pds_source is an xlsx file.
        is_json: if True the pds_source is a JSON file.
        is_gs: if True the pds_source is a Google Sheets file.
        silent: if "full" do not print any warnings, if "nuisance" do not print nuisance warnings.
    """
    
    _check_format(format_check)
    
    if format_check:
        match format_check:
            case "mwtab":
                composite_schema = mwtab_schema
    
    elif pds_source:
        PDS = read_and_validate_PDS(pds_source, is_csv, is_xlsx, is_json, is_gs, False, silent)
        if input_json_path:
            input_json = read_in_JSON_file(input_json_path, "input JSON")
            if "protocol" in input_json:
                add_protocols_to_PDS(input_json["protocol"], PDS, silent)
        composite_schema = build_PD_schema(PDS)
        if validate_JSON_schema(composite_schema) and not silent == "full":
            print("Warning:  The schema created from the protocol-dependent schema is not valid.", file=sys.stderr)
    else:
        composite_schema = base_schema
    
    save_out_JSON_file(output_schema_path, composite_schema)
    


def run_schema_command(input_schema_source: str) -> None:
    """Run the schema command.
    
    Args:
        input_schema_source: the path to the JSON Schema file to read and validate.
    """
    user_json_schema = read_in_JSON_file(input_schema_source, "input schema")
    if not validate_JSON_schema(user_json_schema):
        print("No errors. This is a valid JSON schema.")


def run_pds_command(pds_source: str, output_path: str|None = None, is_csv: bool = False, is_xlsx: bool = False, 
                   is_json: bool = False, is_gs: bool = False, silent: str = "none") -> None:
    """Run the pds command.
    
    Args:
        pds_source: either a filepath or "-" to read from stdin.
        output_path: if given then save the JSON Schema from the PDS.
        is_csv: if True the pds_source is a csv file.
        is_xlsx: if True the pds_source is an xlsx file.
        is_json: if True the pds_source is a JSON file.
        is_gs: if True the pds_source is a Google Sheets file.
        silent: if "full" do not print any warnings, if "nuisance" do not print nuisance warnings.
    """
    PDS = read_and_validate_PDS(pds_source, is_csv, is_xlsx, is_json, is_gs, True, silent)
    composite_schema = build_PD_schema(PDS)
    if validate_JSON_schema(composite_schema) and not silent == "full":
        print("Warning:  The schema created from the protocol-dependent schema is not valid.", file=sys.stderr)
    
    if output_path:
        save_out_JSON_file(output_path, composite_schema)


def run_pds_to_table_command(pds_source: str, output_path: str, output_filetype: str, silent: str = "none") -> None:
    """Run the pds-to-table command.
    
    Args:
        pds_source: either a filepath or "-" to read from stdin.
        output_path: either a filepath or "-" to write to stdout.
        output_filetype: either "xlsx" or "csv".
        silent: if "full" do not print any warnings, if "nuisance" do not print nuisance warnings.
    """
    PDS = read_and_validate_PDS(pds_source, False, False, True, False, False, silent)
    
    if output_path == "-":
        table_to_save = directives_to_table(PDS)
        table_to_save.to_csv(sys.stdout, index=False, header=False)
    else:
        output_filetype = output_filetype if output_filetype else "csv"
        
        if re.match(r".*\." + output_filetype + "$", output_path):
            save_name = output_path
        else:
            save_name = output_path + "." + output_filetype
        
        if output_filetype == "xlsx":
            table_to_save = directives_to_table(PDS)
            table_to_save.to_excel(save_name, index=False, header=False)
        elif output_filetype == "csv":
            table_to_save = directives_to_table(PDS)
            table_to_save.to_csv(save_name, index=False, header=False)
        else:
            print("Error:  Unknown output filetype.", file=sys.stderr)
    

def run_pds_to_json_command(pds_source: str, is_csv: bool, is_xlsx: bool, is_gs: bool, 
                            output_path: str, silent: str = "none") -> None:
    """Run the pds-to-json command.
    
    Args:
        pds_source: either a filepath or "-" to read from stdin.
        is_csv: if True the pds_source is a csv file.
        is_xlsx: if True the pds_source is an xlsx file.
        is_gs: if True the pds_source is a Google Sheets file.
        output_path: either a filepath or "-" to write to stdout.
        silent: if "full" do not print any warnings, if "nuisance" do not print nuisance warnings.
    """
    PDS = read_and_validate_PDS(pds_source, is_csv, is_xlsx, False, is_gs, False, silent)
    
    save_out_JSON_file(output_path, PDS)    
        

def run_conversion_directives_to_json_schema_command(conversion_directives_source: str, 
                                                 is_csv: bool, is_xlsx: bool, is_json: bool, 
                                                 is_gs: bool, output_schema_path: str, 
                                                 silent: str) -> None:
    """Run the cd-to-json command.
    
    Args:
        conversion_directives_source: either a filepath or "-" to read from stdin.
        is_csv: if True the conversion_directives_source is a csv file.
        is_xlsx: if True the conversion_directives_source is an xlsx file.
        is_json: if True the conversion_directives_source is a JSON file.
        is_gs: if True the conversion_directives_source is a Google Sheets file.
        silent: if "full" do not print any warnings, if "nuisance" do not print nuisance warnings.
    """
    conversion_directives = read_json_or_tabular_file(conversion_directives_source, 
                                                      is_csv, is_xlsx, is_json, is_gs,
                                                      "conversion directives", "#convert", silent)
    try:
        user_input_checking.validate_conversion_directives(conversion_directives, convert_schema.directives_schema)
    except SystemExit:
        print("Error:  The conversion directives are not valid, so a JSON schema could not be created.", file=sys.stderr)
        sys.exit()
        
    def add_table(schema, table):
        if table not in schema["properties"]:
            schema["properties"][table] = {"type":"object", "additionalProperties":{"type":"object", "properties":{}}}
        
    def add_field(schema, table, field, required):
        schema["properties"][table]["additionalProperties"]["properties"][field] = {}
        if required:
            if "required" in schema["properties"][table]["additionalProperties"]:
                if field not in schema["properties"][table]["additionalProperties"]["required"]:
                    schema["properties"][table]["additionalProperties"]["required"].append(field)
            else:
                schema["properties"][table]["additionalProperties"]["required"] = [field]
    
    new_schema = {"type":"object", "properties":{}}
    for conversion_table, directives in conversion_directives.items():
        for directive, directive_attributes in directives.items():
            if "table" not in directive_attributes:
                continue
            table = directive_attributes["table"]
            required = True
            if (required_attr := directive_attributes.get("required")) is not None:
                if isinstance(required_attr, bool):
                    required = required_attr
                elif isinstance(required_attr, str) and required_attr.lower() == "false":
                    required = False
            
            ## "headers" keyword
            if directive_attributes.get("headers"):
                for pair in directive_attributes["headers"]:
                    split = pair.split("=")
                    output_key = split[0].strip()
                    input_key = split[1].strip()
                    
                    if not re.match(literal_regex, output_key):
                        add_table(new_schema, table)
                        add_field(new_schema, table, output_key, required)
                        
                    if not re.match(literal_regex, input_key):
                        add_table(new_schema, table)
                        add_field(new_schema, table, input_key, required)
                        
            ## "fields" keyword
            if fields := directive_attributes.get("fields"):
                for field in fields:
                    if not re.match(literal_regex, field):
                        add_table(new_schema, table)
                        add_field(new_schema, table, field, required)
                        
            ## "test" keyword
            if test := directive_attributes.get("test"):
                split = test.split("=")
                test_field = split[0].strip()
                add_table(new_schema, table)
                add_field(new_schema, table, test_field, required)
            
            ## "collate" keyword
            if collate := directive_attributes.get("collate"):
                add_table(new_schema, table)
                add_field(new_schema, table, collate, required)
                
            ## "sort_by" keyword
            if sort_by := directive_attributes.get("sort_by"):
                for field in sort_by:
                    if not re.match(literal_regex, field):
                        add_table(new_schema, table)
                        add_field(new_schema, table, field, required)
                        
            ## "optional_headers" keyword
            if optional_headers := directive_attributes.get("optional_headers"):
                for field in optional_headers:
                    if not re.match(literal_regex, field):
                        add_table(new_schema, table)
                        add_field(new_schema, table, field, False)
                
    
    save_out_JSON_file(output_schema_path, new_schema)


