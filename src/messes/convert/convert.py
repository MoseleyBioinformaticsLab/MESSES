# -*- coding: utf-8 -*-
"""
Convert JSON data to another JSON format.

Usage:
    messes convert mwtab (ms | nmr | nmr_binned) <input_JSON> <output_name> [--update <conversion_directives> | --override <conversion_directives>] [--silent]
    messes convert save-directives mwtab (ms | nmr | nmr_binned) <output_filetype> [<output_name>]
    messes convert generic <input_JSON> <output_name> <conversion_directives> [--silent]
    messes convert --help
    
    <conversion_directives> - can be a JSON, csv, xlsx, or Google Sheets file. If xlsx or Google Sheets the default sheet name to read in is #convert, 
                              to specify a different sheet name separate it from the file name with a colon ex: file_name.xlsx:sheet_name.
                              
    <output_filetype> - "json", "xlsx", or "csv"

Options:
    -h, --help                           - show this screen.
    -v, --version                        - show version.
    --silent                             - silence all warnings.
    --update <conversion_directives>     - conversion directives that will be used to update the built-in directives for the format.
                                           This is intended to be used for simple changes such as updating the value of 
                                           the analysis ID. You only have to specify what needs to change, any values 
                                           that are left out of the update directives won't be changed. If you need to remove 
                                           directives then use the override option.
    --override <conversion_directives>   - conversion directives that will be used to override the built-in directives for the format.
                                           The built-in directives will not be used and these will be used instead.
    
    

The general command structure for convert is convert <format> which will convert an input JSON file over to the supported format. 
The outputs of these commands will save both the JSON conversion and the final format file.

The generic command is the same as the supported formats except the user is required to input conversion directives specifying how to 
convert the input JSON to the desired output JSON. Only an output JSON is saved.

The save-directives command is used to print the default conversion directives used by convert for any of the supported formats. <output-filetype> 
can be one of "json", "xlsx", or "csv". The file is saved as "format_conversion_directives.ext" where ".ext" is replaced with ".json", ".xlsx", 
or ".csv" depending on the value of <output-format>, unless <output_name> is given.

"""

import operator
import re
import sys
import pathlib
from importlib.machinery import SourceFileLoader
import json
import datetime
import collections.abc
import traceback
import io
from typing import Any
from inspect import getmembers, isfunction

import pandas
import docopt
import mwtab

from messes.extract import extract
from messes import __version__
from messes.convert import mwtab_conversion_directives
from messes.convert import mwtab_functions
from messes.convert import user_input_checking
from messes.convert import convert_schema
from messes.convert import built_ins
from messes.convert import regexes

## TODO add check to see if a section type directive is in the same table as others and print an error mixing section and other types can cause an error, and it doesn't make sense anyway.
##   Added this to user_input_checking, needs tested.
## Is tested in both user_input_checking and convert_tags

## TODO check if "fields" in str directives allows calling of nested directives, if so need to make sure the nested directive returns a string value.
##      It does, but instead of doing error checking I just cast the result to str(). This needs documenting.

## Make it so for str directives if the nested directive returns None, but is not required it isn't concatenated into the final output, no error, just dropped.
##   Made this so, but warnings are printed.

## For a matrix type directive if a nested directive is on the left side it must return a string. Make sure the code tests for this.
##  I added a check and warning that will cast the key to a string.

## Add all functions imported through the "import" field to the "built_in" list.
##  Added this, but needs tested, getmembers(importname, is_function) may need to be getmembers(global_variables[importname], is_function)

## TODO make it so the override field in str directives can be a calling record field.  This is done, need to add to documentation.
## Add documentation about "silent" being added to directives.

## If headers in a matrix directive have required=false that header is just left out, add documentation explaining this and showing how you can use
## str directives to get optionality on all headers.

## See if the code that does error checking for nested directive fields i.e. uses calling_record_regex can be turned into a function for reuse.
##  I think I got most of these.

## Update directives schema for all the new changes, "silent", "test", "section" type, "section_matrix" and "section_str" types, "execute".


## Make sure to test importing and using a built-in function.

## Add measurement%transformation and measurement%normalization protocol types. Allows us to handle those for ISA. Require parents and that parent be a measurement type.
## Try just concatenating fields to condense a list of protocols into 1, look for protocol%order field to determine order, if not there assume the order is correct.
## For assays find the storage%measurement protocol and work backward to the first collection to find where to start the assay.
## Leave execute as is for now and don't let it execute nested directives.
## Add a "skip" keyword to skip directives, also make it so directives with "%" in the name are skip=True by default, but will use skip if present.
## For nested directive argument passing, they have to be key=value pairs, but arbitrary string replacement ones must start with a '$'.
##   Search through the values of all fields and look for '$' keys.
##   Still have the issue of dealing with users not passing enough values and haveing some left over though, need to think about this.
## Just leave nested directives in the places you have them now, can extend to other keywords as needed.

built_in_functions = {attributes[0]:attributes[1] for attributes in getmembers(built_ins, isfunction)}

literal_regex = regexes.literal_regex
calling_record_regex = regexes.calling_record_regex
nested_directive_regex = regexes.nested_directive_regex


def main() :
    args = docopt.docopt(__doc__, version=__version__)
    
    ## Validate args.
    # user_input_checking.additional_args_checks(args)
    
    #####################
    ## Determine conversion_directives.
    #####################
    supported_formats_and_sub_commands = {"mwtab":["ms", "nmr", "nmr_binned"]}
    conversion_directives = {}
    format_under_operation = "generic"
    for supported_format, sub_commands in supported_formats_and_sub_commands.items():
        if args[supported_format]:
            format_under_operation = supported_format
            sub_command = [sub_command for sub_command in supported_formats_and_sub_commands[supported_format] if args[sub_command]][0]
            conversion_directives = eval(supported_format + "_conversion_directives." + sub_command + "_directives")
            break
        
    if filepath := next((arg for arg in [args["<conversion_directives>"], args["--update"], args["--override"]] if arg is not None), False):
        if re.search(r".*(\.xls[xm]?|\.csv)", filepath) or extract.TagParser.isGoogleSheetsFile(filepath):
            default_sheet_name = False
            if (reMatch := re.search(r"^(.*\.xls[xm]?):(.*)$", filepath)):
                filepath = reMatch.group(1)
                sheet_name = reMatch.group(2)
            elif re.search(r"\.xls[xm]?$", filepath):
                sheet_name = "#convert"
                default_sheet_name = True
            elif (reMatch := re.search(r"docs.google.com/spreadsheets/d/([^/]*)/[^:]*$", filepath)):
                filepath = "https://docs.google.com/spreadsheets/d/" + reMatch.group(1) + "/export?format=xlsx"
                sheet_name = "#convert"
                default_sheet_name = True
            elif (reMatch := re.search(r"docs.google.com/spreadsheets/d/([^/]*)/.*:(.*)$", filepath)):
                filepath = "https://docs.google.com/spreadsheets/d/" + reMatch.group(1) + "/export?format=xlsx"
                sheet_name = reMatch.group(2)
            tagParser = extract.TagParser()
            ## In order to print error messages correctly we have to know if loadSheet printed a message or not, so temporarily replace stderr.
            old_stderr = sys.stderr
            sys.stderr = buffer = io.StringIO()
            try:
                if worksheet_tuple := tagParser.loadSheet(filepath, sheet_name, isDefaultSearch=default_sheet_name):
                    tagParser.parseSheet(*worksheet_tuple)
                    update_conversion_directives = tagParser.extraction
                    sys.stderr = old_stderr
                else:
                    sys.stderr = old_stderr
                    if buffer.getvalue():
                        ## Have to trim the extra newline off the end of buffer.
                        print(buffer.getvalue()[0:-1], file=sys.stderr)
                    elif default_sheet_name:
                        print("Error: No sheet name was given for the file, so the default name "
                              "of #convert was used, but it was not found in the file.", file=sys.stderr)
                    sys.exit()
            except Exception as e:
                sys.stderr = old_stderr
                raise e
        
        elif re.match(r".*\.json$", filepath):
            with open(filepath, 'r') as jsonFile:
                update_conversion_directives = json.load(jsonFile)
        
        else:
            print("Error: Unknown file type for the conversion directives file.", file=sys.stderr)
            sys.exit()
            
        if args["--update"]:
            _update(conversion_directives, update_conversion_directives)
        else:
            conversion_directives = update_conversion_directives
    
    ##########################
    ## Handle save-directives command.
    ##########################
    if args["save-directives"]:
        if args["<output_name>"]:
            if re.match(r".*\." + args["<output_filetype>"] + "$", args["<output_name>"]):
                save_name = args["<output_name>"]
            else:
                save_name = args["<output_name>"] + "." + args["<output_filetype>"]
        else:
            save_name = format_under_operation + "_" + sub_command + "_conversion_directives." + args["<output_filetype>"]
        
        if args["<output_filetype>"] == "json":
            with open(save_name,'w') as jsonFile:
                jsonFile.write(json.dumps(conversion_directives, indent=2))
        elif args["<output_filetype>"] == "xlsx":
            table_to_save = directives_to_table(conversion_directives)
            table_to_save.to_excel(save_name, index=False, header=False)
        elif args["<output_filetype>"] == "csv":
            table_to_save = directives_to_table(conversion_directives)
            table_to_save.to_csv(save_name, index=False, header=False)
        else:
            print("Error: Unknown output filetype.", file=sys.stderr)
            
        sys.exit()
        
    
    #######################
    ## Validate conversion directives.
    #######################
    user_input_checking.validate_conversion_directives(conversion_directives, convert_schema.directives_schema)
    
    
    ## Read in files.
    if not pathlib.Path(args["<input_JSON>"]).exists():
        print(f"Error: The value entered for <input_JSON>, {args['<input_JSON>']}, is not a valid file path or does not exist.", file=sys.stderr)
        sys.exit()
    try:
        with open(args["<input_JSON>"], 'r') as jsonFile:
            input_json = json.load(jsonFile)
    except Exception as e:
        print(f"\nError: An error was encountered when trying to read in the <input_JSON>, {args['<input_JSON>']}.\n", file=sys.stderr)
        raise e
    
    
    #####################
    ## Generate new JSON.
    #####################
    output_json = {}
    for conversion_table, conversion_records in conversion_directives.items():
        
        if "%" in conversion_table:
            continue
        
        table_value = _determine_directive_table_value(input_json, 
                                                       conversion_table,  
                                                       conversion_directives,
                                                       None, 
                                                       None, 
                                                       None, 
                                                       args["--silent"])
        
        output_json[conversion_table] = table_value
        
    
    
    #########################
    ## Save the generated json.
    #########################
    json_save_name = args["<output_name>"] + ".json"
    with open(json_save_name,'w') as jsonFile:
        jsonFile.write(json.dumps(output_json, indent=2))
    
    if args["mwtab"]:
        ## Optional way to do things compared to the code block below this.
        # with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as tp:
        #     tp.write(json.dumps(output_json))
        #     tp.seek(0)
        #     mwfile = mwtab.mwtab.MWTabFile("")
        #     mwfile.read(tp)
        # with open(args["<output-name>"], 'w', encoding="utf-8") as outfile:
        #     mwfile.write(outfile, file_format="mwtab")
        
        mwtab_key_order = {'METABOLOMICS WORKBENCH':['STUDY_ID', 'ANALYSIS_ID', 'VERSION', 'CREATED_ON'], 
                           'PROJECT':[], 
                           'STUDY':[], 
                           'SUBJECT':[], 
                           'SUBJECT_SAMPLE_FACTORS':[], 
                           'COLLECTION':[], 
                           'TREATMENT':[], 
                           'SAMPLEPREP':[], 
                           'CHROMATOGRAPHY':[], 
                           'ANALYSIS':[], 
                           }
                
        extended_key_order = {"ms":{'MS':[], 
                                    'MS_METABOLITE_DATA':['Units', 'Data', 'Metabolites', 'Extended']},
                              "nmr":{'NM':[], 
                                     'NMR_METABOLITE_DATA':['Units', 'Data', 'Metabolites', 'Extended']},
                              "nmr_binned":{'NM':[], 
                                            'NMR_BINNED_DATA':['Units', 'Data']}}
        
        mwtab_key_order.update(extended_key_order[sub_command])
        
        
        mwtabfile = mwtab.mwtab.MWTabFile("")
        
        ## The mwtab package doesn't ensure correct ordering itself, so we have to make sure everything is ordered correctly.
        for key, sub_keys in mwtab_key_order.items():
            if key in output_json:
                mwtabfile[key] = {}
                for sub_key in sub_keys:
                    if sub_key in output_json[key]:
                        mwtabfile[key][sub_key] = output_json[key][sub_key]
                if isinstance(output_json[key], dict):
                    mwtabfile[key].update(output_json[key])
                else:
                    mwtabfile[key] = output_json[key]
        
        ## If you just update the dict then things can be out of order, so switched to the above method until mwtab is improved.
        # mwtabfile.update(output_json)
        mwtabfile.header = " ".join(
            ["#METABOLOMICS WORKBENCH"]
            + [item[0] + ":" + item[1] for item in mwtabfile["METABOLOMICS WORKBENCH"].items() if item[0] not in ["VERSION", "CREATED_ON"]]
        )            
        
        mwtabfile.source = args["<input_JSON>"]
        validated_file, errors = mwtab.validator.validate_file(mwtabfile)
        
        if "Status: Passing" in errors:
            mwtab_save_name = args["<output_name>"] + ".txt"
            with open(mwtab_save_name, 'w', encoding='utf-8') as outfile:
                mwtabfile.write(outfile, file_format="mwtab")
        else:
            print("Error: An error occured when validating the mwtab file.", file=sys.stderr)
            print(errors, file=sys.stderr)
            sys.exit()





###################
## Helper Functions
###################

def _handle_errors(required: bool, silent: bool, message: str) -> None:
    """If required is True print message as error and exit, else print message as warning if silent is False.
    
    Args:
        required: if the directive is required or not, if True then an error has occurred and we need to exit.
        silent: whether to print a warning message or not.
        message: the message to be printed.
    """
    if required:
        print("Error: " + message, file=sys.stderr)
        sys.exit()
    else:
        if not silent:
            print("Warning: " + message, file=sys.stderr)


def _update(original_dict: dict, upgrade_dict: dict) -> dict:
    """Update a dictionary in a nested fashion.
    
    Args:
        original_dict: the dictionary to update.
        upgrade_dict: the dictionary to update values from.
        
    Returns:
        original_dict, the updated original_dict
    """
    for key, value in upgrade_dict.items():
        if isinstance(value, collections.abc.Mapping):
            original_dict[key] = _update(original_dict.get(key, {}), value)
        else:
            original_dict[key] = value
    return original_dict


# def _nested_set(dic: dict, keys: list[str], value: Any) -> None:
#     """Creates nested dictionaries in dic for all but the last key and creates a key value pair in the last dictionary.
    
#     Args:
#         dic: the dictionary to set the value in.
#         keys: the keys to nest in the dictionaries.
#         value: the value to set the last key to in the deepest dicitonary.
#     """
#     for key in keys[:-1]:
#         dic = dic.setdefault(key, {})
#     dic[keys[-1]] = value


def _sort_by_getter(pair: tuple[str,dict], keys: list[str]) -> list:
    """Piece of a sorted call to return the values of certain keys in a dictionary.
    
    Args:
        pair: the tuple from calling items() on a dict.
        keys: a list of keys to retrieve values from the second element in pair.
        
    Returns:
        a list of the field values from the dict in the tuple based on keys.
        
    Raises:
        KeyError: if any key in keys is not in the second element of pair.
    """
    try:
        return [pair[1][key] for key in keys]
    except KeyError as e:
        e.pair = pair
        raise e

# def _sort_table_records(sort_by, table_records, reverse, conversion_record_name, conversion_table, input_table, required, silent):
#     try:
#         table_records = dict(sorted(table_records.items(), key = lambda pair: _sort_by_getter(pair, sort_by), reverse = reverse))
#         ## table_records used to be a list of dicts and this was the sort, leaving it here in case it is needed.
#         # table_records = sorted(table_records, key = operator.itemgetter(*sort_by), reverse = conversion_attributes["sort_order"] == "descending")
#     except KeyError as e:
#         message = "The \"sort_by\" conversion directive to create the \"" + conversion_record_name + \
#                   "\" conversion in the \"" + conversion_table + "\" table has an input key, " + str(e) + \
#                   ", that was not in the \"" + e.pair[0] + "\" record of the \"" + input_table + "\"."
#         return _handle_errors(required, silent, message)
    
#     return table_records


def _str_to_boolean_get(default: bool, key: str, input_dict: dict) -> bool:
    """Read the field and convert to boolean.
    
    Args:
        default: the default boolean value to return if not found.
        key: the key to the dict to look for the value of.
        input_dict: the dict to look for the key in.
    
    Returns:
        the vlaue of the key as a bool.
    """
    attribute = default
    if (temp_attribute := input_dict.get(key)) is not None:
        if isinstance(temp_attribute, bool):
            attribute = temp_attribute
        elif isinstance(temp_attribute, str):
            if temp_attribute.lower() == "false":
                attribute = False
            else:
                attribute = True
            
    return attribute



###############################
## Functions used by directives
###############################
   

def _parse_test_attribute(attribute_value: str, conversion_table: str, conversion_record_name: str, conversion_attributes: dict,
                          calling_record_table: str|int, calling_record_name: str|int, calling_record_attributes: dict,
                          required: bool, silent: bool) -> tuple[str, str]|tuple[None, None]:
    """Parse the test string into an expression that can be evaled.
    
    Args:
        attribute_value: the value of the test attribute for conversion directive to be parsed.
        conversion_table: the name of the table the conversion record came from, used for good error messaging.
        conversion_record_name: the name of the conversion record, used for good error messaging.
        conversion_attributes: the fields and values of the conversion record.
        calling_record_table: if this is a nested directive, then this should be the table of the record the directive was called on, else None.
        calling_record_name: if this is a nested directive, then this should be the key of the record the directive was called on, else None.
        calling_record_attributes: if this is a nested directive, then this should be the attributes of the record the directive was called on, else None.
        required: if True then any problems during execution are errors and the program should exit, else it's just a warning.
        silent: if True don't print warning messages.
    
    Returns:
        Either a string that can be evaled to do the test or None if there was an error.
    """
    pairs = re.split(r'\s+\&\s+|\s+\|\s+|\s+and\s+|\s+or\s+', attribute_value)
    
    for pair in pairs:
        split = pair.split("=")
        test_field = split[0].strip()
        test_value = split[1].strip()
        
        if (calling_field := _is_field_in_calling_record(test_value, 
                                                         "test", 
                                                         conversion_attributes["test"], 
                                                         conversion_table, 
                                                         conversion_record_name,
                                                         calling_record_table, 
                                                         calling_record_name, 
                                                         calling_record_attributes,
                                                         required, 
                                                         silent))[0]:
            ## No value means it matched the syntax, but there were no fields in the calling record that matched.
            if calling_field[1] is None:
                return None
            test_value = calling_record_attributes[calling_field[1]]
        
        elif match := re.match(literal_regex, test_value):
            test_value = match.group(1)
            
        if match := re.match(literal_regex, test_field):
            test_field = match.group(1)
            
        replacement_text = f"('{test_field}' in record_attributes and record_attributes['{test_field}'] == '{test_value}')"
        attribute_value = attribute_value.replace(pair, replacement_text)
        
    attribute_value = attribute_value.replace("&", "and")
    attribute_value = attribute_value.replace("|", "or")
    return attribute_value
        
        
    

def _build_table_records(has_test: bool, conversion_record_name: str, conversion_table: str, conversion_attributes: dict, 
                         input_json: dict, required: bool, silent: bool, test_string: str="") -> dict:
    """Loop over a table in the input_json and pull the correct records and sort if necessary.
    
    Args:
        has_test: if True the records need to be filtered by a test.
        conversion_record_name: the name of the conversion record, used for good error messaging.
        conversion_table: the name of the table the conversion record came from, used for good error messaging.
        conversion_attributes: the fields and values of the conversion record.
        input_json: the data to build the records from.
        required: if True then any problems during execution are errors and the program should exit, else it's just a warning.
        silent: if True don't print warning messages.
        test_string: if has_test is True this is the field to filter records with.
        
    Returns:
        the filtered and sorted records from a table in input_json.
    """
    
    if not conversion_attributes["table"] in input_json:
        message = (f"The \"table\" field value, \"{conversion_attributes['table']}\", for conversion, \"{conversion_record_name}"
                  f"\", in conversion table, \"{conversion_table}\", does not exist in the input JSON.")
        return _handle_errors(required, silent, message)
    
    if has_test:
        table_records = {record_name:record_attributes for record_name, record_attributes in input_json[conversion_attributes["table"]].items() if eval(test_string)}
    else:
        table_records = input_json[conversion_attributes["table"]]
        
    if not table_records:
        if has_test:
            message = (f"When creating the \"{conversion_record_name}"
                      f"\" conversion for the \"{conversion_table}\" table, no records in the \""
                      f"{conversion_attributes['table']}\" table matched the test, \""
                      f"{conversion_attributes['test']}\", indicated in the \"test\" field of the conversion. "
                      f"This could be from no records containing the test field(s) or no records matching the test value(s) for those field(s).")
        else:
            message = (f"When creating the \"{conversion_record_name}"
                      f"\" conversion for the \"{conversion_table}\" table, there were no records in the indicated \""
                      f"{conversion_attributes['table']}\" table.")
        
        return _handle_errors(required, silent, message)
    
    if sort_by := conversion_attributes.get("sort_by"):
        try:
            table_records = dict(sorted(table_records.items(), key = lambda pair: _sort_by_getter(pair, sort_by), reverse = conversion_attributes.get("sort_order", "").lower() == "descending"))
            ## table_records used to be a list of dicts and this was the sort, leaving it here in case it is needed.
            # table_records = sorted(table_records, key = operator.itemgetter(*sort_by), reverse = conversion_attributes["sort_order"] == "descending")
        except KeyError as e:
            message = (f"The record, \"{e.pair[0]}\", in the \"{conversion_attributes['table']}"
                      f"\" table does not have the field, {e}"
                      f", required by the \"sort_by\" field for the conversion, \""
                      f"{conversion_record_name}\", in the conversion table, \"{conversion_table}\".")
            return _handle_errors(required, silent, message)
        
    return table_records



def _handle_code_field(input_json: dict, conversion_table: str, conversion_record_name: str, 
                       conversion_attributes: dict, conversion_directives: dict, required: bool,
                       calling_record_table: str|int=None, calling_record_name: str|int=None, calling_record_attributes: dict=None, 
                       silent: bool=False) -> Any:
    """If conversion_attributes has code and/or import fields then import and run the code appropriately.
    
    Args:
        input_json: dict that the code is likely to operate on.
        conversion_table: the name of the table the conversion record came from, used for good error messaging.
        conversion_record_name: the name of the conversion record, used for good error messaging.
        conversion_attributes: the fields and values of the conversion record.
        conversion_directives: the conversion directives, used for calling nested directives.
        required: if True then any problems during execution are errors and the program should exit, else it's just a warning.
        calling_record_table: if this is a nested directive, then this should be the table of the record the directive was called on, else None.
        calling_record_name: if this is a nested directive, then this should be the key of the record the directive was called on, else None.
        calling_record_attributes: if this is a nested directive, then this should be the attributes of the record the directive was called on, else None.
        silent: if True don't print warning messages.
        
    Returns:
        the result of eval() or None if there was no "code" field in conversion_attributes.
    """
    
    if import_path := conversion_attributes.get("import"):
        import_pathlib = pathlib.Path(import_path)
        if not import_pathlib.exists():
            message = (f"The path given to import a Python file in the \"import\" field of the conversion record \""
                      f"{conversion_record_name}\" in the \"{conversion_table}\" table does not exist.")
            return _handle_errors(required, silent, message)
        
        import_name = import_pathlib.stem
        global_variables = globals()
        global_variables[import_name] = SourceFileLoader(import_name, import_path).load_module()
        ## Add import functions to built-ins.
        built_in_functions.update({attributes[0]:attributes[1] for attributes in getmembers(import_name, isfunction)})
    
    if code := conversion_attributes.get("code"):
        try:
            value = eval(code)
        except Exception:
            message = (f"The code conversion directive to create the \"{conversion_record_name}"
                      f"\" record in the \"{conversion_table}\" table encountered an error while executing.\n")
            message += traceback.format_exc()
            return _handle_errors(required, silent, message)
        
        return value
    
    else:
        return None




def _is_field_in_calling_record(string_to_test: str, conversion_field_name:str, conversion_field_value: str, 
                                conversion_table: str, conversion_record_name: str,
                                calling_record_table: str|int, calling_record_name: str|int, calling_record_attributes: dict,
                                required: bool, silent: bool) -> tuple[bool, str|None]:
    """Determine if string is meant to access a field in calling record.
    
    Args:
        string_to_test: string to determine if it is pointing to a calling record field.
        conversion_field_name: the name of the field in the conversion directive that might have a calling field syntax, used for error messaging.
        conversion_field_value: the value of the field in the conversion directive that might have a calling field syntax, used for error messaging.
        conversion_table: the name of the table the conversion record came from, used for good error messaging.
        conversion_record_name: the name of the conversion record, used for good error messaging.
        calling_record_table: if this is a nested directive, then this should be the table of the record the directive was called on, else None.
        calling_record_name: if this is a nested directive, then this should be the key of the record the directive was called on, else None.
        calling_record_attributes: if this is a nested directive, then this should be the attributes of the record the directive was called on, else None.
        required: if True then any problems during execution are errors and the program should exit, else it's just a warning.
        silent: if True don't print warning messages.
        
    Returns:
        A tuple where the first value is a bool indicating if string_to_test matches the syntax for accessing a calling record's field, 
        and the second value is the field or None.
    """        
    if re_match := re.match(calling_record_regex, string_to_test):
        calling_field = re_match.group(1)
        
        if not calling_record_attributes:
            message = (f"When creating the \"{conversion_record_name}"
                      f"\" conversion for the \"{conversion_table}\" table, the value for \"{conversion_field_name}\", \""
                      f"{conversion_field_value}\", indicates to use a calling record's attribute value, "
                      f"but this conversion directive is not a nested directive and therefore has no calling record.")
            _handle_errors(required, silent, message)
            return True, None
        
        if calling_field not in calling_record_attributes:
            message = (f"When creating the \"{conversion_record_name}"
                      f"\" conversion for the \"{conversion_table}\" table, the value for \"{conversion_field_name}\", \""
                      f"{conversion_field_value}\", indicates to use a calling record's attribute value, but that attribute, \""
                      f"{calling_field}\", does not exist in the calling record, \""
                      f"{calling_record_name}\", in the calling table, \"{calling_record_table}\".")
            _handle_errors(required, silent, message)
            return True, None
        
        return True, calling_field
    
    return False, None



def _is_field_a_nested_directive(string_to_test: str, 
                                 conversion_table: str, 
                                 conversion_record_name: str,
                                 conversion_directives: dict,
                                 required: bool, silent: bool) -> tuple[bool, str|None]:
    """Determine if string is a nested_directive.
    
    Args:
        string_to_test: string to determine if it is pointing to a calling record field.
        conversion_table: the name of the table the conversion record came from, used for good error messaging.
        conversion_record_name: the name of the conversion record, used for good error messaging.
        conversion_directives: the conversion directives, used for calling nested directives.
        required: if True then any problems during execution are errors and the program should exit, else it's just a warning.
        silent: if True don't print warning messages.
        
    Returns:
        A tuple where the first value is a bool indicating if string_to_test matches the syntax for a nested directive, 
        and the second value is the nested directive name or None.
    """
    
    if re_match := re.match(nested_directive_regex, string_to_test):
        directive = re_match.group(1)
        
        if directive not in conversion_directives:
            message = (f"The conversion directive to create the \"{conversion_record_name}"
                      f"\" record in the \"{conversion_table}\" table tries to call a nested directive, "
                      f"{directive}, but that directive is not in the conversion directives.")
            _handle_errors(required, silent, message)
            return True, None
        
        return True, directive
    
    return False, None



def _execute_directive(input_json: dict, conversion_table: str, conversion_record_name: str, 
                       conversion_attributes: dict, conversion_directives: dict, required: bool, 
                       calling_record_table: str|int=None, calling_record_name: str|int=None, calling_record_attributes: dict=None, 
                       silent: bool=False) -> Any:
    """Call the correct function to execute the directive based on its value_type.
    
    Args:
        input_json: the data to build the matrix from.
        conversion_table: the name of the table the conversion record came from.
        conversion_record_name: the name of the conversion record.
        conversion_attributes: the fields and values of the conversion record.
        conversion_directives: the conversion directives, used for calling nested directives.
        required: if True then any problems during execution are errors and the program should exit, else it's just a warning.
        calling_record_table: if this is a nested directive, then this should be the table of the record the directive was called on, else None.
        calling_record_name: if this is a nested directive, then this should be the key of the record the directive was called on, else None.
        calling_record_attributes: if this is a nested directive, then this should be the attributes of the record the directive was called on, else None.
        silent: if True don't print warning messages.
    
    Returns:
        the value returned by executing the directive.
    """
    
    if conversion_attributes["value_type"] == "section":
        value = compute_section_value(input_json, conversion_table, conversion_record_name, conversion_attributes, conversion_directives, 
                                      required, calling_record_table, calling_record_name, calling_record_attributes, silent)
    elif "matrix" in conversion_attributes["value_type"]:
        value = compute_matrix_value(input_json, conversion_table, conversion_record_name, conversion_attributes, conversion_directives, 
                                     required, calling_record_table, calling_record_name, calling_record_attributes, silent)
    elif "str" in conversion_attributes["value_type"]:
        value = compute_string_value(input_json, conversion_table, conversion_record_name, conversion_attributes, conversion_directives, 
                                     required, calling_record_table, calling_record_name, calling_record_attributes, silent)
        
    return value



def _determine_directive_table_value(input_json: dict, conversion_table: str, conversion_directives: dict,
                                     calling_record_table: str|int=None, calling_record_name: str|int=None, calling_record_attributes: dict=None, 
                                     silent: bool=False) -> Any:
    """Call the correct function to execute the directive based on its value_type.
    
    Args:
        input_json: the data to build the matrix from.
        conversion_table: the name of the table the conversion record came from.
        conversion_directives: the conversion directives, used for calling nested directives.
        calling_record_table: if this is a nested directive, then this should be the table of the record the directive was called on, else None.
        calling_record_name: if this is a nested directive, then this should be the key of the record the directive was called on, else None.
        calling_record_attributes: if this is a nested directive, then this should be the attributes of the record the directive was called on, else None.
        silent: if True don't print warning messages.
    
    Returns:
        the value returned by executing the directive.
    """
    directive_table_output = {}
    for conversion_record_name, conversion_attributes in conversion_directives[conversion_table].items():
        silent = _str_to_boolean_get(silent, "silent", conversion_attributes)
        required = _str_to_boolean_get(True, "required", conversion_attributes)            
        
        default = conversion_attributes.get("default")
        ## Literal check needs to be here if the user wants to use a space.
        if default and (literal_match := re.match(literal_regex, default)):
            default = literal_match.group(1)
            
        value = _execute_directive(input_json, conversion_table, conversion_record_name, 
                                   conversion_attributes, conversion_directives, required, 
                                   calling_record_table, calling_record_name, calling_record_attributes, 
                                   silent)
                
        if value is None:
            if default is None:
                if required:
                    print(f"Error: The conversion directive to create the \"{conversion_record_name}"
                          f"\" record in the \"{conversion_table}\" table did not return a value.", 
                          file=sys.stderr)
                    sys.exit()
                else:
                    if not silent:
                        print("Warning: The non-required conversion directive to create the \""
                              f"{conversion_record_name}\" record in the \"{conversion_table}\" table could not be created.", 
                              file=sys.stderr)
                    continue
            else:
                value = default
                if not silent:
                    print(f"The conversion directive to create the \"{conversion_record_name}"
                          f"\" record in the \"{conversion_table}"
                          f"\" table could not be created, and reverted to its given default value, \"{default}\".", 
                          file=sys.stderr)
                
        if "section" in conversion_attributes["value_type"]:
            directive_table_output = value
        else:
            directive_table_output[conversion_record_name] = value
            
    ##TODO Should there be a check here to see if the entire conversion table returns None and do something?
                
    return directive_table_output if directive_table_output else None



###############################################
## Main API functions to execute each directive
###############################################


def compute_section_value(input_json: dict, conversion_table: str, conversion_record_name: str, 
                         conversion_attributes: dict, conversion_directives: dict, required: bool, 
                         calling_record_table: str|int=None, calling_record_name: str|int=None, 
                         calling_record_attributes: dict=None, silent: bool=False) -> str|None:
    """Determine the value for the conversion directive.
    
    Args:
        input_json: the data to build the value from.
        conversion_table: the name of the table the conversion record came from, used for good error messaging.
        conversion_record_name: the name of the conversion record, used for good error messaging.
        conversion_attributes: the fields and values of the conversion record.
        conversion_directives: the conversion directives, used for calling nested directives.
        required: if True then any problems during execution are errors and the program should exit, else it's just a warning.
        calling_record_table: if this is a nested directive, then this should be the table of the record the directive was called on, else None.
        calling_record_name: if this is a nested directive, then this should be the key of the record the directive was called on, else None.
        calling_record_attributes: if this is a nested directive, then this should be the attributes of the record the directive was called on, else None.
        silent: if True don't print warning messages.
    
    Returns:
        the value for the directive or None if there was a problem and the directive is not required.
    """
    silent = _str_to_boolean_get(silent, "silent", conversion_attributes)
    
    ## code
    value = _handle_code_field(input_json, conversion_table, conversion_record_name, conversion_attributes, conversion_directives, 
                               required, calling_record_table, calling_record_name, calling_record_attributes, silent)
            
    if value is not None:
        return value
    
    elif value is None and conversion_attributes.get("code") is not None:
        return None
    
    ## execute
    if execute := conversion_attributes.get("execute"):
        if match := re.match(r"(.*)\((.*)\)\s*", execute.strip()):
            function_name = match.group(1)
            # function_inputs = match.group(2).split(',')
            ## Going to go on and strip here, but this may need to change in the 
            ## future if people have fields with leading or trailing spaces.
            function_arguments = [word.strip() for word in match.group(2).split(',')]
            
            ## (bool, value) if the bool is true it means the value needs to be evaled().
            function_argument_tuples = []
            for function_argument in function_arguments:
            
                if (calling_field := _is_field_in_calling_record(function_argument, 
                                                                 "execute", 
                                                                 conversion_attributes["execute"], 
                                                                 conversion_table, 
                                                                 conversion_record_name,
                                                                 calling_record_table, 
                                                                 calling_record_name, 
                                                                 calling_record_attributes,
                                                                 required, 
                                                                 silent))[0]:
                    ## No value means it matched the syntax, but there were no fields in the calling record that matched.
                    if calling_field[1] is None:
                        return None
                    function_argument = (False, calling_record_attributes[calling_field[1]])
                
                
                elif match := re.match(literal_regex, function_argument):
                    function_argument = (False, match.group(1))
                
                else:
                    function_argument = (True, f"record_attributes['{function_argument}']")
                
                function_argument_tuples.append(function_argument)
                        
        else:
            message = (f"The conversion directive to create the \"{conversion_record_name}"
                      f"\" record in the \"{conversion_table}\" table has a malformed value for "
                      f"its \"execute\" attribute, \"{execute}\". It should be of the form \"function_name(function_input1, function_input2, ...)\".")
            return _handle_errors(required, silent, message)
        
        
        if "table" not in conversion_attributes:
            
            if any([entry[0] for entry in function_argument_tuples]):
                message = (f"The conversion directive to create the \"{conversion_record_name}"
                          f"\" record in the \"{conversion_table}\" table calls a function in its \"execute\" "
                          f"attribute, \"{execute}\", that has arguments which are attributes to input records, "
                          "but this directive does not provide a \"table\" attribute to pull records from.")
                return _handle_errors(required, silent, message)
            
            return _run_built_in_function(function_name, 
                                          [entry[1] for entry in function_argument_tuples], 
                                          conversion_table, conversion_record_name, 
                                          calling_record_table, calling_record_name, 
                                          required, silent)
            
    ## It is assumed that "execute" will be in the directive because directives should be validated before this is called.
    
    has_test = False
    test_string = ""
    if test := conversion_attributes.get("test"):
        has_test = True
        test_string = _parse_test_attribute(test, conversion_table, conversion_record_name, conversion_attributes,
                                                       calling_record_table, calling_record_name, calling_record_attributes,
                                                       required, silent)
        if test_string is None:
            return None
    
    ## for_each
    for_each = _str_to_boolean_get(False, "for_each", conversion_attributes)
    
    table_records = _build_table_records(has_test, conversion_record_name, conversion_table, conversion_attributes, 
                                         input_json, required, silent, test_string=test_string)
    if table_records is None:
        return None
    
    record_table = conversion_attributes["table"]
    
    if for_each:
        value_for_each_record = []
        for record_name, record_attributes in table_records.items():
            value = _run_built_in_function(function_name, 
                                           [eval(entry[1], {"record_attributes":record_attributes}) if entry[0] else entry[1] for entry in function_argument_tuples], 
                                           conversion_table, conversion_record_name, 
                                           record_table, record_name, 
                                           required, silent)
            
            if value is not None:
                value_for_each_record.append(value)
        
        return value_for_each_record if value_for_each_record else None
    
    ## record_id
    if conversion_attributes.get("record_id"):
        if not conversion_attributes["record_id"] in table_records:
            message = (f"The \"record_id\" field value, \"{conversion_attributes['record_id']}"
                      f"\", for conversion, \"{conversion_record_name}"
                      f"\", in conversion table, \"{conversion_table}\", does not exist in the \""
                      f"{conversion_attributes['table']}\" table of the input JSON.")
            return _handle_errors(required, silent, message)
        record_attributes = table_records[conversion_attributes["record_id"]]
        record_name = conversion_attributes["record_id"]
    else:
        record_name, record_attributes = list(table_records.items())[0]

    
    return _run_built_in_function(function_name, 
                                  [eval(entry[1], {"record_attributes":record_attributes}) if entry[0] else entry[1] for entry in function_argument_tuples], 
                                  conversion_table, conversion_record_name, 
                                  record_table, record_name, 
                                  required, silent)


def _run_built_in_function(function_name: str, function_input: list[Any], 
                           conversion_table: str, conversion_record_name: str, 
                           record_table: str|int|None, record_name: str|int|None,
                           required: bool, silent: bool) -> Any:
    """Execute the built-in function in a try block and handle errors.
    
    Args:
        function_name: the name of the built-in function.
        function_input: the input to call with the function.
        conversion_table: the name of the table the conversion record came from, used for good error messaging.
        conversion_record_name: the name of the conversion record, used for good error messaging.
        record_table: the name of the table the record came from, used for good error messaging.
        record_name: the name of the record, used for good error messaging.
        required: if True then any problems during execution are errors and the program should exit, else it's just a warning.
        silent: if True don't print warning messages.
    
    Returns:
        the value returned by the built-in function or None if there was an error.
    """
    try:
        built_in_message, value = built_in_functions[function_name](*function_input)
    except Exception:
        message = (f"The conversion directive to create the \"{conversion_record_name}"
                  f"\" record in the \"{conversion_table}\" table encountered an error while executing its \"execute\" function.\n")
        message += traceback.format_exc()
        return _handle_errors(required, silent, message)
    
    if built_in_message is not None:
        message = (f"The conversion directive to create the \"{conversion_record_name}"
                  f"\" record in the \"{conversion_table}\" table encountered a problem while executing its \"execute\" function ")
        if record_name is not None and record_table is not None:
            message += f"for the record, \"{record_name}\", in the table, \"{record_table}\":\n"
        else:
            message += ":\n"
            
        message += built_in_message
        # ## built-ins can create error messages that expect to have certain values filled in later.
        # message = message.format(**locals())
        return _handle_errors(required, silent, message)
    else:
        return value




def compute_string_value(input_json: dict, conversion_table: str, conversion_record_name: str, 
                         conversion_attributes: dict, conversion_directives: dict, required: bool, 
                         calling_record_table: str|int=None, calling_record_name: str|int=None, 
                         calling_record_attributes: dict=None, silent: bool=False) -> str|None:
    """Determine the string value for the conversion directive.
    
    Args:
        input_json: the data to build the value from.
        conversion_table: the name of the table the conversion record came from, used for good error messaging.
        conversion_record_name: the name of the conversion record, used for good error messaging.
        conversion_attributes: the fields and values of the conversion record.
        conversion_directives: the conversion directives, used for calling nested directives.
        required: if True then any problems during execution are errors and the program should exit, else it's just a warning.
        calling_record_table: if this is a nested directive, then this should be the table of the record the directive was called on, else None.
        calling_record_name: if this is a nested directive, then this should be the key of the record the directive was called on, else None.
        calling_record_attributes: if this is a nested directive, then this should be the attributes of the record the directive was called on, else None.
        silent: if True don't print warning messages.
    
    Returns:
        the str value for the directive or None if there was a problem and the directive is not required.
    """
    silent = _str_to_boolean_get(silent, "silent", conversion_attributes)
    
    ## override
    if override := conversion_attributes.get("override"):
        
        if (calling_field := _is_field_in_calling_record(override, 
                                                         "override", 
                                                         conversion_attributes["override"], 
                                                         conversion_table, 
                                                         conversion_record_name,
                                                         calling_record_table, 
                                                         calling_record_name, 
                                                         calling_record_attributes,
                                                         required, 
                                                         silent))[0]:
            ## No value means it matched the syntax, but there were no fields in the calling record that matched.
            if calling_field[1] is None:
                return None
            override = calling_record_attributes[calling_field[1]]
        
        elif match := re.match(literal_regex, override):
            override = match.group(1)
                        
        return override
    
    ## code
    value = _handle_code_field(input_json, conversion_table, conversion_record_name, conversion_attributes, conversion_directives, 
                               required, calling_record_table, calling_record_name, calling_record_attributes, silent)
            
    if value is not None:
        if not isinstance(value, str):
            print(f"Error: The code conversion directive to create the \"{conversion_record_name}"
                  f"\" record in the \"{conversion_table}\" table did not return a string type value.", 
                  file=sys.stderr)
            sys.exit()
        
        return value
    
    elif value is None and conversion_attributes.get("code") is not None:
        return None
    
    ## fields
    fields = conversion_attributes["fields"]
    ## TODO move this to user input checking, do the same with section type for execute field and matrix as well, move the tests from tags to input checking as well.
    ## I don't think I can move this because I have to do the check again here anyway to know to return early.
    if "table" not in conversion_attributes:
        if not all([True if re.match(literal_regex, field) or re.match(calling_record_regex, field) else False for field in fields]):
            message = (f"The conversion directive to create the \"{conversion_record_name}"
                      f"\" record in the \"{conversion_table}\" table has elements in its \"fields\" "
                      f"attribute, \"{fields}\", which are attributes to input records, "
                      "but this directive does not provide a \"table\" attribute to pull records from.")
            return _handle_errors(required, silent, message)
    
        return _build_string_value(input_json,
                                   fields, 
                                   conversion_table, 
                                   conversion_record_name, 
                                   conversion_attributes,
                                   conversion_directives,
                                   None, 
                                   None, 
                                   None, 
                                   required, 
                                   calling_record_table, 
                                   calling_record_name, 
                                   calling_record_attributes, 
                                   silent)
    
    has_test = False
    test_string = ""
    if test := conversion_attributes.get("test"):
        has_test = True
        test_string = _parse_test_attribute(test, conversion_table, conversion_record_name, conversion_attributes,
                                                       calling_record_table, calling_record_name, calling_record_attributes,
                                                       required, silent)
        if test_string is None:
            return None
    
    ## for_each
    for_each = _str_to_boolean_get(False, "for_each", conversion_attributes)
    
    table_records = _build_table_records(has_test, conversion_record_name, conversion_table, conversion_attributes, 
                                         input_json, required, silent, test_string=test_string)
    if table_records is None:
        return None
    
    if for_each:
        delimiter = conversion_attributes.get("delimiter", "")
        if delimiter and (literal_match := re.match(literal_regex, delimiter)):
            delimiter = literal_match.group(1)
        
        value_for_each_record = []
        for record_name, record_attributes in table_records.items():
            value = _build_string_value(input_json,
                                        fields, 
                                        conversion_table, 
                                        conversion_record_name, 
                                        conversion_attributes,
                                        conversion_directives,
                                        conversion_attributes["table"], 
                                        record_name, 
                                        record_attributes, 
                                        required, 
                                        calling_record_table, 
                                        calling_record_name, 
                                        calling_record_attributes, 
                                        silent)
            if value is not None:
                value_for_each_record.append(value)
        
        joined_string = delimiter.join(value_for_each_record) if value_for_each_record else None
        return joined_string
    
    ## record_id
    if conversion_attributes.get("record_id"):
        if not conversion_attributes["record_id"] in table_records:
            message = (f"The \"record_id\" field value, \"{conversion_attributes['record_id']}"
                      f"\", for conversion, \"{conversion_record_name}"
                      f"\", in conversion table, \"{conversion_table}\", does not exist in the \""
                      f"{conversion_attributes['table']}\" table of the input JSON.")
            return _handle_errors(required, silent, message)
        record_attributes = table_records[conversion_attributes["record_id"]]
        record_name = conversion_attributes["record_id"]
    else:
        record_name, record_attributes = list(table_records.items())[0]
        # record_name, record_attributes = list(input_json[conversion_attributes["table"]].items())[0]
    
    value = _build_string_value(input_json,
                                fields, 
                                conversion_table, 
                                conversion_record_name, 
                                conversion_attributes,
                                conversion_directives,
                                conversion_attributes["table"], 
                                record_name, 
                                record_attributes, 
                                required, 
                                calling_record_table, 
                                calling_record_name, 
                                calling_record_attributes, 
                                silent)
            
    return value


def _build_string_value(input_json: dict, fields: list[str], conversion_table: str, conversion_record_name: str, conversion_attributes: dict, 
                        conversion_directives: dict, record_table: str, record_name: str, record_attributes: dict, required: bool,
                        calling_record_table: str|int=None, calling_record_name: str|int=None, calling_record_attributes: dict=None, 
                        silent: bool=False) -> str|None:
    """Build a single string value from the input record and conversion record.
    
    Args:
        input_json: the entire input data the output is being created from.
        fields: a list of strings that could be either literal values, fields from a record, or a nested directive.
        conversion_table: the name of the table the conversion record came from, used for good error messaging.
        conversion_record_name: the name of the conversion record, used for good error messaging.
        conversion_attributes: the fields and values of the conversion record.
        conversion_directives: the conversion directives, used for calling nested directives.
        record_table: the name of the table the record came from, used for good error messaging.
        record_name: the name of the record, used for good error messaging.
        record_attributes: the fields and values of the record.
        required: if True then any problems during execution are errors and the program should exit, else it's just a warning.
        calling_record_table: if this is a nested directive, then this should be the table of the record the directive was called on, else None.
        calling_record_name: if this is a nested directive, then this should be the key of the record the directive was called on, else None.
        calling_record_attributes: if this is a nested directive, then this should be the attributes of the record the directive was called on, else None.
        silent: if True don't print warning messages.
        
    Returns:
        The string value based on the fields, or None if there were errors.
    """

    value = None
    for field in fields:
        ## Is the field a literal?
        if (re_match := re.match(literal_regex, field)):
            if value:
                value += re_match.group(1)
            else:
                value = re_match.group(1)
            
        else:
            ## Determine if the field value is for the calling record or the current one.
            if (calling_field := _is_field_in_calling_record(field,
                                                             "fields",
                                                             field,
                                                             conversion_table, 
                                                             conversion_record_name,
                                                             calling_record_table,
                                                             calling_record_name, 
                                                             calling_record_attributes,
                                                             required, 
                                                             silent))[0]:
                ## No value means it matched the syntax, but there were no fields in the calling record that matched.
                if calling_field[1] is None:
                    return None
                        
                if value:
                    value += str(calling_record_attributes[calling_field[1]])
                else:
                    value = str(calling_record_attributes[calling_field[1]])
                
            elif (directive := _is_field_a_nested_directive(field, 
                                                            conversion_table, 
                                                            conversion_record_name,
                                                            conversion_directives,
                                                            required, 
                                                            silent))[0]:
                if directive[1]:
                    table_value = _determine_directive_table_value(input_json, 
                                                                   directive[1],  
                                                                   conversion_directives,
                                                                   record_table, 
                                                                   record_name, 
                                                                   record_attributes, 
                                                                   silent)
                    
                    if table_value is None:
                        ## Look at the silent and required attributes for each 
                        ## nested directive record to determine the required and silent status for the whole table.
                        nested_required = False
                        nested_silent = False
                        for nested_name, nested_attributes in conversion_directives[directive[1]].items():
                            required_attr = _str_to_boolean_get(True, "required", nested_attributes)
                            nested_required = nested_required or required_attr
                            
                            silent_attr = _str_to_boolean_get(silent, "silent", nested_attributes)
                            nested_silent = nested_silent or silent_attr
                        
                                                        
                        if not nested_required:
                            
                            message = (f"When executing the str directive, \"{conversion_record_name}\", "
                                       f"in the conversion table, \"{conversion_table}\", a value in the \"field\" called "
                                       f"the nested directive, \"{directive[1]}\", and a problem was encountered "
                                       "while executing the directive. Since the \"required\" field of the "
                                       "nested directive is \"False\" the field will not be concatenated in the result "
                                       f"created for the record, \"{record_name}\", in the \"{conversion_attributes['table']}\" table.")
                            _handle_errors(nested_required, nested_silent, message)
                            continue
                    
                    
                    if not isinstance(table_value, str):
                        message = (f"When executing the str directive, \"{conversion_record_name}\", "
                                   f"in the conversion table, \"{conversion_table}\", a value in the \"fields\" called "
                                   f"the nested directive, \"{directive[1]}\", and the returned value was "
                                   f"not a string type. Return types must be string types, so, {table_value}, will "
                                   f"be cast to a string type for the record, \"{record_name}\", in the \"{conversion_attributes['table']}\" table.")
                        _handle_errors(False, silent, message)
                        table_value = str(table_value)
                
                else:
                    return None
                
                if value:
                    value += table_value
                else:
                    value = table_value
            
            
            else:
                
                ## If the field is not a literal value and it's not in the record print an error.
                if field not in record_attributes:
                    message = (f"The conversion directive to create the \"{conversion_record_name}"
                              f"\" record in the \"{conversion_table}\" table matched a record in the input \""
                              f"{record_table}\" table, \"{record_name}\", that did not contain the \""
                              f"{field}\" field indicated by the directive.")
                    _handle_errors(required, silent, message)
                    continue
            
                if value:
                    value += str(record_attributes[field])
                else:
                    value = str(record_attributes[field])            
            
    return value

                
                
    
def compute_matrix_value(input_json: dict, conversion_table: str, conversion_record_name: str, 
                         conversion_attributes: dict, conversion_directives: dict, required: bool, 
                         calling_record_table: str|int=None, calling_record_name: str|int=None, calling_record_attributes: dict=None, 
                         silent: bool=False) -> list[dict]|None:
    """Determine the matrix value for the conversion directive.
    
    Args:
        input_json: the data to build the matrix from.
        conversion_table: the name of the table the conversion record came from, used for good error messaging.
        conversion_record_name: the name of the conversion record, used for good error messaging.
        conversion_attributes: the fields and values of the conversion record.
        conversion_directives: the conversion directives, used for calling nested directives.
        required: if True then any problems during execution are errors and the program should exit, else it's just a warning.
        calling_record_table: if this is a nested directive, then this should be the table of the record the directive was called on, else None.
        calling_record_name: if this is a nested directive, then this should be the key of the record the directive was called on, else None.
        calling_record_attributes: if this is a nested directive, then this should be the attributes of the record the directive was called on, else None.
        silent: if True don't print warning messages.
    
    Returns:
        the list of dicts for the directive or None if there was a problem and the directive is not required.
    """
    silent = _str_to_boolean_get(silent, "silent", conversion_attributes)
    
    value = _handle_code_field(input_json, conversion_table, conversion_record_name, conversion_attributes, conversion_directives, 
                               required, calling_record_table, calling_record_name, calling_record_attributes, silent)
            
    if value is not None:
        if not isinstance(value, list) or not all([isinstance(record, dict) for record in value]):
            print(f"Error: The code conversion directive to create the \"{conversion_record_name}"
                  f"\" record in the \"{conversion_table}\" table did not return a matrix type value.", 
                  file=sys.stderr)
            sys.exit()
        
        return value
    
    elif value is None and conversion_attributes.get("code") is not None:
        return None
        
    ## fields_to_headers
    fields_to_headers = _str_to_boolean_get(False, "fields_to_headers", conversion_attributes)
        
    
    ## values_to_str
    values_to_str = _str_to_boolean_get(False, "values_to_str", conversion_attributes)
        
            
    has_test = False
    test_string = ""
    if test := conversion_attributes.get("test"):
        has_test = True
        test_string = _parse_test_attribute(test, conversion_table, conversion_record_name, conversion_attributes,
                                            calling_record_table, calling_record_name, calling_record_attributes,
                                            required, silent)
        if test_string is None:
            return None
    
    exclusion_headers = conversion_attributes.get("exclusion_headers", [])
    
    headers = conversion_attributes.get("headers", [])
    
    optional_headers = conversion_attributes.get("optional_headers", [])
    
    ## If "table" is not in the attributes and headers doesn't contain any values requiring records then return early.
    if "table" not in conversion_attributes:
        ## Chain from itertools is faster, but I don't think the speed is necessary.
        # header_strings = list(chain.from_iterable([header.split('=') for header in headers]))
        header_strings = [string for header in headers for string in header.split('=')]
        if not all([True if re.match(literal_regex, string) or re.match(calling_record_regex, string) else False for string in header_strings]):
            message = (f"The conversion directive to create the \"{conversion_record_name}"
                      f"\" record in the \"{conversion_table}\" table has elements in its \"headers\" "
                      f"attribute, \"{headers}\", which are attributes to input records, "
                      "but this directive does not provide a \"table\" attribute to pull records from.")
            return _handle_errors(required, silent, message)
    
        return _build_matrix_record_dict(input_json,
                                         {}, 
                                         None, 
                                         headers, 
                                         None, 
                                         None, 
                                         conversion_table, 
                                         conversion_record_name, 
                                         conversion_attributes, 
                                         conversion_directives,
                                         fields_to_headers,
                                         exclusion_headers,
                                         optional_headers,
                                         values_to_str, 
                                         required, 
                                         calling_record_table, 
                                         calling_record_name, 
                                         calling_record_attributes,
                                         silent)
    
    table_records = _build_table_records(has_test, conversion_record_name, conversion_table, conversion_attributes, 
                                         input_json, required, silent, test_string=test_string)
    if table_records is None:
        return None
    
        
    if collate := conversion_attributes.get("collate"):
        ## TODO think about whether to do collate.strip() here to remove spaces.
        records = {}
        for record_name, record_attributes in table_records.items():
            if collate not in record_attributes:
                message = (f"The record, \"{record_name}\", in the \"{conversion_attributes['table']}"
                          f"\" table does not have the field, \"{collate}"
                          f"\", required by the \"collate\" field for the conversion, \""
                          f"{conversion_record_name}\", in the conversion table, \"{conversion_table}\".")
                return _handle_errors(required, silent, message)
            collate_key = record_attributes[collate]
            
            if collate_key not in records:
                records[collate_key] = {}
            
            records[collate_key] = _build_matrix_record_dict(input_json,
                                                             records[collate_key], 
                                                             collate_key, 
                                                             headers, 
                                                             record_name, 
                                                             record_attributes, 
                                                             conversion_table, 
                                                             conversion_record_name, 
                                                             conversion_attributes, 
                                                             conversion_directives,
                                                             fields_to_headers,
                                                             exclusion_headers,
                                                             optional_headers,
                                                             values_to_str, 
                                                             required, 
                                                             calling_record_table, 
                                                             calling_record_name, 
                                                             calling_record_attributes,
                                                             silent)
                                
        records = list(records.values())
    
    else:
        records = []
        for record_name, record_attributes in table_records.items():
            temp_dict =  _build_matrix_record_dict(input_json,
                                                   {}, 
                                                   None, 
                                                   headers, 
                                                   record_name, 
                                                   record_attributes, 
                                                   conversion_table, 
                                                   conversion_record_name, 
                                                   conversion_attributes, 
                                                   conversion_directives,
                                                   fields_to_headers,
                                                   exclusion_headers,
                                                   optional_headers,
                                                   values_to_str, 
                                                   required, 
                                                   calling_record_table, 
                                                   calling_record_name, 
                                                   calling_record_attributes,
                                                   silent)
            
            records.append(temp_dict)
    
    return records if records else None


## TODO Check to see if collate and sort fields are a nested directive field that doesn't get added because required=false if it causes an error.
def _build_matrix_record_dict(input_json: dict,
                              matrix_dict: dict, 
                              collate_key: str, 
                              headers: list[str], 
                              record_name: str, 
                              record_attributes: dict, 
                              conversion_table: str, 
                              conversion_record_name: str, 
                              conversion_attributes: dict, 
                              conversion_directives: dict,
                              fields_to_headers: bool,
                              exclusion_headers: list[str],
                              optional_headers: list[str],
                              values_to_str: bool, 
                              required: bool,
                              calling_record_table: str|int=None, 
                              calling_record_name: str|int=None, 
                              calling_record_attributes: dict=None,
                              silent: bool=False) -> dict:
    """Build the dictionary to go in the matrix from the record.
    
    Args:
        input_json: the entire input data the output is being created from.
        matrix_dict: a dictionary already started to add to. If collate is being 
                     used this will have initial values, otherwise it is an empty dict.
        collate_key: a key to group record values around, used to print a warning if 
                     values get overwritten in matrix_dict.
        headers: a list of strings that is used to add keys and values to matrix_dict.
        record_name: the name of the record, used for good error messaging.
        record_attributes: the fields and values of the record.
        conversion_table: the name of the table the conversion record came from, used for good error messaging.
        conversion_record_name: the name of the conversion record, used for good error messaging.
        conversion_attributes: the fields and values of the conversion record.
        conversion_directives: the conversion directives, used for calling nested directives.
        fields_to_headers: if True all fields in record_attributes are to be added to matrix_dict.
        exclusion_headers: any fields in this list are not added to matrix_dict.
        optional_headers: fields in this list are added to matrix_dict if they exist.
        values_to_str: cast record values to str before adding to matrix_dict.
        required: if True then any problems during execution are errors and the program should exit, else it's just a warning.
        calling_record_table: if this is a nested directive, then this should be the table of the record the directive was called on, else None.
        calling_record_name: if this is a nested directive, then this should be the key of the record the directive was called on, else None.
        calling_record_attributes: if this is a nested directive, then this should be the attributes of the record the directive was called on, else None.
        silent: if True don't print warning messages.
        
    Returns:
        matrix_dict with values filled in from the record.
    """
    
    for header in headers:
        input_key, input_key_value, output_key, output_key_value, skip_header = _determine_header_input_keys(input_json,
                                                                                                             header, 
                                                                                                             record_name, 
                                                                                                             record_attributes, 
                                                                                                             conversion_table, 
                                                                                                             conversion_record_name, 
                                                                                                             conversion_attributes, 
                                                                                                             conversion_directives,
                                                                                                             values_to_str, 
                                                                                                             required, 
                                                                                                             calling_record_table, 
                                                                                                             calling_record_name, 
                                                                                                             calling_record_attributes,
                                                                                                             silent)
        
        if skip_header:
            continue
        
        if input_key is None and input_key_value is None and output_key is None and output_key_value is None:
            return None
        
        if collate_key is not None and input_key_value in matrix_dict and output_key_value != matrix_dict[input_key_value]:
            print(f"Warning: When creating the \"{conversion_record_name}"
                  f"\" matrix for the \"{conversion_table}\" table different values for the output key, \""
                  f"{output_key}\", were found for the collate key \"{collate_key}"
                  "\". Only the last value will be used.", 
                  file=sys.stderr)
        
        matrix_dict[input_key_value] = output_key_value
    
    if fields_to_headers:
        if values_to_str:
            matrix_dict.update({field:str(value) for field, value in record_attributes.items() if field not in exclusion_headers})
        else:
            matrix_dict.update({field:value for field, value in record_attributes.items() if field not in exclusion_headers})
    else:
        for header in optional_headers:
            if header in record_attributes:
                matrix_dict[header] = str(record_attributes[header]) if values_to_str else record_attributes[header]
                
    return matrix_dict



def _determine_header_input_keys(input_json: dict, header: str, record_name: str, record_attributes: dict, conversion_table: str, 
                                 conversion_record_name: str, conversion_attributes: dict, conversion_directives: dict, 
                                 values_to_str: bool, required: bool, calling_record_table: str|int=None, 
                                 calling_record_name: str|int=None, calling_record_attributes: dict=None,  
                                 silent: bool=False) -> tuple[str,str, str, Any]:
    """Based on the header dict pull the correct values from the record_attributes.
    
    Args:
        input_json: the entire input data the output is being created from.
        header: a string of the form "input_key=output_key" where the keys can be literal values or fields from a record.
                If the keys are literal then they should be returned as is, if not they are fields in record_attributes.
        record_name: the name of the record, used for good error messaging.
        record_attributes: the fields and values of the record.
        conversion_table: the name of the table the conversion record came from, used for good error messaging.
        conversion_record_name: the name of the conversion record, used for good error messaging.
        conversion_attributes: the fields and values of the conversion record.
        conversion_directives: the conversion directives, used for calling nested directives.
        values_to_str: cast record values to str.
        required: if True then any problems during execution are errors and the program should exit, else it's just a warning.
        calling_record_table: if this is a nested directive, then this should be the table of the record the directive was called on, else None.
        calling_record_name: if this is a nested directive, then this should be the key of the record the directive was called on, else None.
        calling_record_attributes: if this is a nested directive, then this should be the attributes of the record the directive was called on, else None.
        silent: if True don't print warning messages.
        
    Returns:
        the input_key, input_key_value, output_key, output_key_value, skip_header for the header.
        skip_header is a boolean that indicates if the header should be left out of the dictionary being created.
    """
    skip_header = False
    split = header.split("=")
    output_key = split[0].strip()
    input_key = split[1].strip()
    
    for key_name, key in {"input_key":input_key, "output_key":output_key}.items():
        if new_key := re.match(literal_regex, key):
            key = new_key.group(1)
            key_value = key
        
        elif (calling_field := _is_field_in_calling_record(key,
                                                           "headers",
                                                           header,
                                                           conversion_table, 
                                                           conversion_record_name,
                                                           calling_record_table,
                                                           calling_record_name, 
                                                           calling_record_attributes,
                                                           required, 
                                                           silent))[0]:
            ## No value means it matched the syntax, but there were no fields in the calling recod that matched.
            if calling_field[1] is not None:        
                key_value = str(calling_record_attributes[calling_field[1]]) if values_to_str else calling_record_attributes[calling_field[1]]
            else:
                return None, None, None, None, False
        
        elif (directive := _is_field_a_nested_directive(key, 
                                                        conversion_table, 
                                                        conversion_record_name,
                                                        conversion_directives,
                                                        required, 
                                                        silent))[0]:
            
            if directive[1]:
                table_value = _determine_directive_table_value(input_json, 
                                                               directive[1],  
                                                               conversion_directives,
                                                               conversion_attributes["table"], 
                                                               record_name, 
                                                               record_attributes, 
                                                               silent)
                
                if table_value is None:
                    ## Look at the silent and required attributes for each 
                    ## nested directive record to determine the required and silent status for the whole table.
                    nested_required = False
                    nested_silent = False
                    for nested_name, nested_attributes in conversion_directives[directive[1]].items():
                        required_attr = _str_to_boolean_get(True, "required", nested_attributes)
                        nested_required = nested_required or required_attr
                        
                        silent_attr = _str_to_boolean_get(silent, "silent", nested_attributes)
                        nested_silent = nested_silent or silent_attr
                                        
                    
                    if not nested_required:
                        
                        message = (f"When executing the matrix directive, \"{conversion_record_name}\", "
                                   f"in the conversion table, \"{conversion_table}\", a header called "
                                   f"the nested directive, \"{directive[1]}\", and a problem was encountered "
                                   "while executing the directive. Since the \"required\" field of the "
                                   "nested directive is \"False\" the header will not be in the dictionary "
                                   f"created for the record, \"{record_name}\", in the \"{conversion_attributes['table']}\" table.")
                        _handle_errors(nested_required, nested_silent, message)
                        return None, None, None, None, True
                
                key_value = str(table_value) if values_to_str else table_value
                
                if key_name == "output_key" and not isinstance(key_value, str):
                    message = (f"When executing the matrix directive, \"{conversion_record_name}\", "
                               f"in the conversion table, \"{conversion_table}\", a header called "
                               f"the nested directive, \"{directive[1]}\", and the returned value was "
                               f"not a string type. Keys to JSON objects must be string types, so, {key_value}, will "
                               f"be cast to a string type for the record, \"{record_name}\", in the \"{conversion_attributes['table']}\" table.")
                    _handle_errors(False, silent, message)
                    key_value = str(key_value)
            
            else:
                return None, None, None, None, False
                    
        
        else:    
            if key not in record_attributes:
                ## If required is False then the this header is simply skipped.
                ## TODO make sure to add to the documentation that headers not found are skipped if required is false.
                message = (f"The record, \"{record_name}\", in the \"{conversion_attributes['table']}"
                          f"\" table does not have the field, \"{key}"
                          f"\", required by the \"headers\" field for the conversion, \""
                          f"{conversion_record_name}\", in the conversion table, \"{conversion_table}\".")
                _handle_errors(required, silent, message)
                return None, None, None, None, False
            
            key_value = str(record_attributes[key]) if values_to_str else record_attributes[key]
            
        if key_name == "input_key":
            input_key = key
            output_key_value = key_value
        else:
            output_key = key
            input_key_value = key_value
    
    
    
    
    ## Commenting out in case the above loop change doesn't work.
    # ############
    # ## input key
    # ############    
    # if new_input_key := re.match(literal_regex, input_key):
    #     input_key = new_input_key.group(1)
    #     output_key_value = input_key
    
    # elif (calling_field := _is_field_in_calling_record(input_key, 
    #                                                    calling_record_table, 
    #                                                    conversion_table, 
    #                                                    conversion_record_name,
    #                                                    calling_record_name, 
    #                                                    calling_record_attributes,
    #                                                    required, 
    #                                                    silent))[0]:
    #     ## No value means it matched the syntax, but there were no fields in the calling recod that matched.
    #     if calling_field[1]:        
    #         output_key_value = str(calling_record_attributes[calling_field[1]]) if values_to_str else calling_record_attributes[calling_field[1]]
    
    # elif (directive := _is_field_a_nested_directive(input_key, 
    #                                                 conversion_table, 
    #                                                 conversion_record_name,
    #                                                 conversion_directives,
    #                                                 required, 
    #                                                 silent))[0]:
        
    #     if directive[1]:
    #         table_value = _determine_directive_table_value(input_json, 
    #                                                        directive[1],  
    #                                                        conversion_directives,
    #                                                        calling_record_table, 
    #                                                        calling_record_name, 
    #                                                        calling_record_attributes, 
    #                                                        silent)
            
    #         if table_value is None:
    #             nested_required = True
    #             if (required_attr := conversion_attributes.get("required")) is not None:
    #                 if isinstance(required_attr, bool):
    #                     nested_required = required_attr
    #                 elif isinstance(required_attr, str) and required_attr.lower() == "false":
    #                     nested_required = False
                
    #             if not nested_required:
    #                 message = (f"When executing the matrix directive, \"{conversion_record_name}\", "
    #                            f"in the conversion table, \"{conversion_table}\", a header called "
    #                            f"the nested directive, \"{directive[1]}\", and a problem was encountered "
    #                            "while executing the directive. Since the \"required\" field of the "
    #                            "nested directive is \"False\" the header will not be in the dictionary "
    #                            "created for the record, \"{record_name}\", in the \"{conversion_attributes['table']}\" table.")
    #                 _handle_errors(nested_required, 
    #                                new_silent if (new_silent := conversion_directives[directive[1]].get("silent")) else silent, 
    #                                message)
    #                 return None, None, None, None, True
            
    #         output_key_value = str(table_value) if values_to_str else table_value
                
    
    # else:    
    #     if input_key not in record_attributes:
    #         message = (f"The record, \"{record_name}\", in the \"{conversion_attributes['table']}"
    #                   f"\" table does not have the field, \"{input_key}"
    #                   f"\", required by the \"headers\" field for the conversion, \""
    #                   f"{conversion_record_name}\", in the conversion table, \"{conversion_table}\".")
    #         _handle_errors(required, silent, message)
    #         return None, None, None, None, False
        
    #     output_key_value = str(record_attributes[input_key]) if values_to_str else record_attributes[input_key]
        
    # #############
    # ## output key
    # #############
    # if new_output_key := re.match(literal_regex, output_key):
    #     output_key = new_output_key.group(1)
    #     input_key_value = output_key
    
    # elif (calling_field := _is_field_in_calling_record(output_key, 
    #                                                    calling_record_table, 
    #                                                    conversion_table, 
    #                                                    conversion_record_name,
    #                                                    calling_record_name, 
    #                                                    calling_record_attributes,
    #                                                    required, 
    #                                                    silent))[0]:
    #     ## No value means it matched the syntax, but there were no fields in the calling recod that matched.
    #     if calling_field[1]:
    #         input_key_value = str(calling_record_attributes[calling_field[1]]) if values_to_str else calling_record_attributes[calling_field[1]]
    
    # elif (directive := _is_field_a_nested_directive(output_key, 
    #                                                 conversion_table, 
    #                                                 conversion_record_name,
    #                                                 conversion_directives,
    #                                                 required, 
    #                                                 silent))[0]:
        
    #     if directive[1]:
    #         table_value = _determine_directive_table_value(input_json, 
    #                                                        directive[1],  
    #                                                        conversion_directives,
    #                                                        calling_record_table, 
    #                                                        calling_record_name, 
    #                                                        calling_record_attributes, 
    #                                                        silent)
    #         if table_value is None:
    #             nested_required = True
    #             if (required_attr := conversion_attributes.get("required")) is not None:
    #                 if isinstance(required_attr, bool):
    #                     nested_required = required_attr
    #                 elif isinstance(required_attr, str) and required_attr.lower() == "false":
    #                     nested_required = False
                
    #             if not nested_required:
    #                 message = (f"When executing the matrix directive, \"{conversion_record_name}\", "
    #                            f"in the conversion table, \"{conversion_table}\", a header called "
    #                            f"the nested directive, \"{directive[1]}\", and a problem was encountered "
    #                            "while executing the directive. Since the \"required\" field of the "
    #                            "nested directive is \"False\" the header will not be in the dictionary "
    #                            "created for the record, \"{record_name}\", in the \"{conversion_attributes['table']}\" table.")
    #                 _handle_errors(nested_required, 
    #                                new_silent if (new_silent := conversion_directives[directive[1]].get("silent")) else silent, 
    #                                message)
    #                 return None, None, None, None, True
                
    #         input_key_value = str(table_value) if values_to_str else table_value
    
    # else:
    #     if output_key not in record_attributes:
    #         message = (f"The record, \"{record_name}\", in the \"{conversion_attributes['table']}"
    #                   f"\" table does not have the field, \"{output_key}"
    #                   f"\", required by the \"headers\" field for the conversion, \""
    #                   f"{conversion_record_name}\", in the conversion table, \"{conversion_table}\".")
    #         _handle_errors(required, silent, message)
    #         return None, None, None, None, False
        
    #     input_key_value = str(record_attributes[output_key]) if values_to_str else record_attributes[output_key]
        
    return input_key, input_key_value, output_key, output_key_value, skip_header



############################
## save-directives functions
############################
    
def directives_to_table(conversion_directives: dict) -> pandas.core.frame.DataFrame:
    """Convert conversion directives to a tagged table form.
    
    Args:
        conversion_directives: the conversion directives to transform.
        
    Returns:
        a pandas DataFrame that can be saved to csv or xlsx.
    """
    
    df_list = []
    for table, records in conversion_directives.items():
        ## For tables with no records add a simple header and blank row.
        if not records:
            rows = []
            rows.append(["#tags", "#" + table + ".id"])
            rows.append(["",""])
            df_list.append(pandas.DataFrame(rows))
        matched_keys = set()
        for record_name, record_fields in records.items():
            if record_name in matched_keys:
                continue
            records_with_matching_fields = [record_name2 for record_name2, record_fields2 in records.items() if record_fields.keys() == record_fields2.keys()]
            matched_keys.update(records_with_matching_fields)
            
            filtered_fields = record_fields.keys() - ["id"]
            filtered_fields = sorted(filtered_fields)
            rows = []
            rows.append(["#tags", "#" + table + ".id"])
            blank_row = ["",""]
            for field in filtered_fields:
                if isinstance(record_fields[field], list):
                    rows[0].append("*#." + field)
                else:
                    rows[0].append("#." + field)
                blank_row.append("")
                    
            for matched_record_name in records_with_matching_fields:
                row = ["", matched_record_name]
                for field in filtered_fields:
                    value = records[matched_record_name][field]
                    if isinstance(value, list):
                        row.append(",".join(value))
                    else:
                        row.append(value)
                        
                rows.append(row)
            rows.append(blank_row)
            df_list.append(pandas.DataFrame(rows))
            
    return pandas.concat(df_list).fillna("")
            
                    
                
                
# str_directive_fields = ["id", "value_type", "override", "code", "import", "table", "for_each", "fields", "test", "required", "delimiter", "sort_by", "sort_order", "record_id", "default"]
# matrix_directive_fields = ["id", "value_type", "code", "import", "table",  "test", "required", "sort_by", "sort_order", "headers", "collate", "exclusion_headers", "optional_headers", "fields_to_headers", "values_to_str", "default"]
# section_directive_fields = ["value_type", "code", "import", "required", "built-in", "table", "test", "for_each", "sort_by", "sort_order", "record_id", "default"]


