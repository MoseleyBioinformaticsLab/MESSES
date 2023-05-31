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

import pandas
import docopt
import mwtab

from messes.extract import extract
from messes import __version__
from messes.convert import mwtab_conversion_directives
from messes.convert import mwtab_functions
from messes.convert import user_input_checking
from messes.convert import convert_schema

## TODO add check to see if a section type directive is in the same table as others and print a warning because the section type overwrites the others.


supported_formats_and_sub_commands = {"mwtab":["ms", "nmr", "nmr_binned"]}

def main() :
    args = docopt.docopt(__doc__, version=__version__)
    
    ## Validate args.
    # user_input_checking.additional_args_checks(args)
    
    #####################
    ## Determine conversion_directives.
    #####################
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
                        print("Error: No sheet name was given for the file, so the default name " +\
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
            update(conversion_directives, update_conversion_directives)
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
        print("Error: The value entered for <input_JSON>, " + args["<input_JSON>"] + ", is not a valid file path or does not exist.", file=sys.stderr)
        sys.exit()
    try:
        with open(args["<input_JSON>"], 'r') as jsonFile:
            input_json = json.load(jsonFile)
    except Exception as e:
        print("\nError: An error was encountered when trying to read in the <input_JSON>, " + args["<input_JSON>"] + ".\n", file=sys.stderr)
        raise e
    
    #####################
    ## Generate new JSON.
    #####################
    output_json = {}
    for conversion_table, conversion_records in conversion_directives.items():
        for conversion_record_name, conversion_attributes in conversion_records.items():
            required = True
            if (required_attr := conversion_attributes.get("required")) is not None:
                if isinstance(required_attr, bool):
                    required = required_attr
                elif isinstance(required_attr, str) and required_attr.lower() == "false":
                    required = False
                
                    
            default = conversion_attributes.get("default")
            ## Literal check needs to be here if the user wants to use a space.
            if default and (literal_match := re.match(literal_regex, default)):
                default = literal_match.group(1)
            
            if conversion_attributes["value_type"] == "section":
                value = handle_code_field(input_json, conversion_table, conversion_record_name, conversion_attributes, required, args["--silent"])
                keys = [conversion_table]
            elif conversion_attributes["value_type"] == "matrix":
                value = compute_matrix_value(input_json, conversion_table, conversion_record_name, conversion_attributes, required, args["--silent"])
                keys = [conversion_table, conversion_record_name]
            elif conversion_attributes["value_type"] == "str":
                value = compute_string_value(input_json, conversion_table, conversion_record_name, conversion_attributes, required, args["--silent"])
                keys = [conversion_table, conversion_record_name]
            
            if value is None:
                if default is None:
                    if required:
                        print("Error: The conversion directive to create the \"" + conversion_record_name + \
                              "\" record in the \"" + conversion_table + "\" table did not return a value.", 
                              file=sys.stderr)
                        sys.exit()
                    else:
                        if not args["--silent"]:
                            print("Warning: The non-required conversion directive to create the \"" + \
                                  conversion_record_name + "\" record in the \"" + conversion_table + "\" table could not be created.", 
                                  file=sys.stderr)
                        continue
                else:
                    value = default
                    if not args["--silent"]:
                        print("The conversion directive to create the \"" + conversion_record_name + \
                              "\" record in the \"" + conversion_table + \
                              "\" table could not be created, and reverted to its given default value, \"" + default + "\".", 
                              file=sys.stderr)
            
            # if value is None and required:
            #     print("Error: The conversion directive to create the \"" + conversion_record_name + "\" record in the \"" + conversion_table + "\" table did not return a value.")
            #     sys.exit()
            # elif value is None and not required:
            #     if not args["--silent"]:
            #         print("Warning: The non-required conversion directive to create the \"" + conversion_record_name + "\" record in the \"" + conversion_table + "\" table could not be created.")
            #     continue
            
            _nested_set(output_json, keys, value)
    
    
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




literal_regex = r"^\"(.*)\"$"

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


def update(original_dict: dict, upgrade_dict: dict) -> dict:
    """Update a dictionary in a nested fashion.
    
    Args:
        original_dict: the dictionary to update.
        upgrade_dict: the dictionary to update values from.
        
    Returns:
        original_dict, the updated original_dict
    """
    for key, value in upgrade_dict.items():
        if isinstance(value, collections.abc.Mapping):
            original_dict[key] = update(original_dict.get(key, {}), value)
        else:
            original_dict[key] = value
    return original_dict


def _nested_set(dic: dict, keys: list[str], value: Any) -> None:
    """Creates nested dictionaries in dic for all but the last key and creates a key value pair in the last dictionary.
    
    Args:
        dic: the dictionary to set the value in.
        keys: the keys to nest in the dictionaries.
        value: the value to set the last key to in the deepest dicitonary.
    """
    for key in keys[:-1]:
        dic = dic.setdefault(key, {})
    dic[keys[-1]] = value


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


def _build_table_records(has_test: bool, conversion_record_name: str, conversion_table: str, conversion_attributes: dict, 
                         input_json: dict, required: bool, silent: bool, test_field: str="", test_value: str="") -> dict:
    """Loop over a table in the input_json and pull the correct records and sort if necessary.
    
    Args:
        has_test: if True the records need to be filtered by a test.
        conversion_record_name: the name of the conversion record, used for good error messaging.
        conversion_table: the name of the table the conversion record came from, used for good error messaging.
        conversion_attributes: the fields and values of the conversion record.
        input_json: the data to build the records from.
        required: if True then any problems during execution are errors and the program should exit, else it's just a warning.
        silent: if True don't print warning messages.
        test_field: if has_test is True this is the field compare with in the records.
        test_value: if has_test is True this is the value the field must be equal to in the record to be added to the output.
        
    Returns:
        the filtered and sorted records from a table in input_json.
    """
    
    if not conversion_attributes["table"] in input_json:
        message = "The \"table\" field value, \"" + conversion_attributes["table"] + "\", for conversion, \"" + conversion_record_name + \
                  "\", in conversion table, \"" + conversion_table + "\", does not exist in the input JSON."
        return _handle_errors(required, silent, message)
    
    if has_test:
        table_records = {record_name:record_attributes for record_name, record_attributes in input_json[conversion_attributes["table"]].items() if test_field in record_attributes and record_attributes[test_field] == test_value}
    else:
        table_records = input_json[conversion_attributes["table"]]
        
    if not table_records:
        if has_test:
            message = "When creating the \"" + conversion_record_name + \
                      "\" conversion for the \"" + conversion_table + "\" table, no records in the \"" + \
                      conversion_attributes["table"] + "\" table matched the test value, \"" + \
                      test_value + "\", for the test field, \"" + \
                      test_field + "\", indicated in the \"test\" field of the conversion. " +\
                      "This could be from no records containing the test field or no records matching the test value for that field."
        else:
            message = "When creating the \"" + conversion_record_name + \
                      "\" conversion for the \"" + conversion_table + "\" table, there were no records in the indicated \"" + \
                      conversion_attributes["table"] + "\" table."
        
        return _handle_errors(required, silent, message)
    
    if sort_by := conversion_attributes.get("sort_by"):
        try:
            table_records = dict(sorted(table_records.items(), key = lambda pair: _sort_by_getter(pair, sort_by), reverse = conversion_attributes.get("sort_order", "").lower() == "descending"))
            ## table_records used to be a list of dicts and this was the sort, leaving it here in case it is needed.
            # table_records = sorted(table_records, key = operator.itemgetter(*sort_by), reverse = conversion_attributes["sort_order"] == "descending")
        except KeyError as e:
            message = "The record, \"" + e.pair[0] + "\", in the \"" + conversion_attributes["table"] + \
                      "\" table does not have the field, " + str(e) + \
                      ", required by the \"sort_by\" field for the conversion, \"" + \
                      conversion_record_name + "\", in the conversion table, \"" + conversion_table + "\"."
            return _handle_errors(required, silent, message)
        
    return table_records


def handle_code_field(input_json: dict, conversion_table: str, conversion_record_name: str, 
                      conversion_attributes: dict, required: bool, silent: bool=False) -> Any:
    """If conversion_attributes has code and/or import fields then import and run the code appropriately.
    
    Args:
        input_json: dict that the code is likely to operate on.
        conversion_table: the name of the table the conversion record came from, used for good error messaging.
        conversion_record_name: the name of the conversion record, used for good error messaging.
        conversion_attributes: the fields and values of the conversion record.
        required: if True then any problems during execution are errors and the program should exit, else it's just a warning.
        silent: if True don't print warning messages.
        
    Returns:
        the result of eval() or None if there was no "code" field in conversion_attributes.
    """
    
    if import_path := conversion_attributes.get("import"):
        import_pathlib = pathlib.Path(import_path)
        if not import_pathlib.exists():
            message = "The path given to import a Python file in the \"import\" field of the conversion record \"" + \
                      conversion_record_name + "\" in the \"" + conversion_table + "\" table does not exist."
            return _handle_errors(required, silent, message)
        
        import_name = import_pathlib.stem
        global_variables = globals()
        global_variables[import_name] = SourceFileLoader(import_name, import_path).load_module()
    
    if code := conversion_attributes.get("code"):
        try:
            value = eval(code)
        except Exception:
            message = "The code conversion directive to create the \"" + conversion_record_name + \
                      "\" record in the \"" + conversion_table + "\" table encountered an error while executing.\n"
            message += traceback.format_exc()
            return _handle_errors(required, silent, message)
        
        return value
    else:
        return None



def _build_string_value(fields: list[tuple[str,bool]], conversion_table: str, conversion_record_name: str, 
                        record_table: str, record_name: str, record_attributes: dict, required: bool, silent: bool) -> str|None:
    """Build a single string value from the input record and conversion record.
    
    Args:
        fields: a list of tuples where the first value in the tuple is the possible 
                field name and the second is a bool that if True means the first value 
                is a literal and not a field to be accessed in the record.
        conversion_table: the name of the table the conversion record came from, used for good error messaging.
        conversion_record_name: the name of the conversion record, used for good error messaging.
        record_table: the name of the table the record came from, used for good error messaging.
        record_name: the name of the record, used for good error messaging.
        record_attributes: the fields and values of the record.
        required: if True then any problems during execution are errors and the program should exit, else it's just a warning.
        silent: if True don't print warning messages.
    """
    
    value = None
    for field in fields:
        ## Is the field a literal?
        if not field[1]:
            ## If the field is not a literal value and it's not in the record print an error.
            if field[0] not in record_attributes:
                message = "The conversion directive to create the \"" + conversion_record_name + \
                          "\" record in the \"" + conversion_table + "\" table matched a record in the input \"" + \
                          record_table + "\" table, \"" + record_name + "\", that did not contain the \"" + \
                          field[0] + "\" field indicated by the directive."
                _handle_errors(required, silent, message)
                continue
        
            if value:
                value += str(record_attributes[field[0]])
            else:
                value = str(record_attributes[field[0]])
        else:
            if value:
                value += field[0]
            else:
                value = field[0]
            
    return value



def _build_matrix_record_dict(matrix_dict: dict, 
                              collate_key: str, 
                              headers: list[dict], 
                              record_name: str, 
                              record_attributes: dict, 
                              conversion_table: str, 
                              conversion_record_name: str, 
                              conversion_attributes: dict, 
                              fields_to_headers: bool,
                              exclusion_headers: list[str],
                              optional_headers: list[str],
                              values_to_str: bool, 
                              required: bool, 
                              silent: bool) -> dict:
    """Build the dictionary to go in the matrix from the record.
    
    Args:
        matrix_dict: a dictionary already started to add to. If collate is being 
                     used this will have initial values, otherwise it is an empty dict.
        collate_key: a key to group record values around, used to print a warning if 
                     values get overwritten in matrix_dict.
        headers: a list of dicts that is used to add keys and values to matrix_dict,
                 gives an indication if the keys and values to add are literals or should 
                 be fields from the record.
        record_name: the name of the record, used for good error messaging.
        record_attributes: the fields and values of the record.
        conversion_table: the name of the table the conversion record came from, used for good error messaging.
        conversion_record_name: the name of the conversion record, used for good error messaging.
        conversion_attributes: the fields and values of the conversion record.
        fields_to_headers: if True all fields in record_attributes are to be added to matrix_dict.
        exclusion_headers: any fields in this list are not added to matrix_dict.
        optional_headers: fields in this list are added to matrix_dict if they exist.
        values_to_str: cast record values to str before adding to matrix_dict.
        required: if True then any problems during execution are errors and the program should exit, else it's just a warning.
        silent: if True don't print warning messages.
        
    Returns:
        matrix_dict with values filled in from the record.
    """
    
    for header in headers:
        input_key_value, output_key_value = _determine_header_input_keys(header, 
                                                                         record_name, 
                                                                         record_attributes, 
                                                                         conversion_table, 
                                                                         conversion_record_name, 
                                                                         conversion_attributes, 
                                                                         values_to_str, 
                                                                         required, 
                                                                         silent)
        
        if collate_key is not None and input_key_value in matrix_dict and output_key_value != matrix_dict[input_key_value]:
            print("Warning: When creating the \"" + conversion_record_name + \
                  "\" matrix for the \"" + conversion_table + "\" table different values for the output key, \"" + \
                  header["output_key"] + "\", were found for the collate key \"" + collate_key + \
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


def _determine_header_input_keys(header: dict, record_name: str, record_attributes: dict, conversion_table: str, 
                                 conversion_record_name: str, conversion_attributes: dict, values_to_str: bool, 
                                 required: bool, silent: bool) -> tuple[str, Any]:
    """Based on the header dict pull the correct values from the record_attributes.
    
    Args:
        header: a dict of the form {"input_key": str, "input_key_is_literal": bool, "output_key": str, "output_key_is_literal": bool}.
                If the keys are literal then they should be returned as is, if not they are fields in record_attributes.
        record_name: the name of the record, used for good error messaging.
        record_attributes: the fields and values of the record.
        conversion_table: the name of the table the conversion record came from, used for good error messaging.
        conversion_record_name: the name of the conversion record, used for good error messaging.
        conversion_attributes: the fields and values of the conversion record.
        values_to_str: cast record values to str.
        required: if True then any problems during execution are errors and the program should exit, else it's just a warning.
        silent: if True don't print warning messages.
        
    Returns:
        the appropriate key-value pair for the header.
    """
    
    if not header["input_key_is_literal"]:
        if header["input_key"] not in record_attributes:
            message = "The record, \"" + record_name + "\", in the \"" + conversion_attributes["table"] + \
                      "\" table does not have the field, \"" + header["input_key"] + \
                      "\", required by the \"headers\" field for the conversion, \"" + \
                      conversion_record_name + "\", in the conversion table, \"" + conversion_table + "\"."
            return _handle_errors(required, silent, message)
        
        output_key_value = str(record_attributes[header["input_key"]]) if values_to_str else record_attributes[header["input_key"]]
    else:
        output_key_value = header["input_key"]
    
    if not header["output_key_is_literal"]:
        if header["output_key"] not in record_attributes:
            message = "The record, \"" + record_name + "\", in the \"" + conversion_attributes["table"] + \
                      "\" table does not have the field, \"" + header["output_key"] + \
                      "\", required by the \"headers\" field for the conversion, \"" + \
                      conversion_record_name + "\", in the conversion table, \"" + conversion_table + "\"."
            return _handle_errors(required, silent, message)
        
        input_key_value = record_attributes[header["output_key"]]
    else:
        input_key_value = header["output_key"]
        
    return input_key_value, output_key_value




def compute_string_value(input_json: dict, conversion_table: str, conversion_record_name: str, 
                         conversion_attributes: dict, required: bool, silent: bool=False) -> str|None:
    """Determine the string value for the conversion directive.
    
    Args:
        input_json: the data to build the value from.
        conversion_table: the name of the table the conversion record came from, used for good error messaging.
        conversion_record_name: the name of the conversion record, used for good error messaging.
        conversion_attributes: the fields and values of the conversion record.
        required: if True then any problems during execution are errors and the program should exit, else it's just a warning.
        silent: if True don't print warning messages.
    
    Returns:
        the str value for the directive or None if there was a problem and the directive is not required.
    """            
    
    ## override
    if value := conversion_attributes.get("override"):
        if literal_match := re.match(literal_regex, value):
            value = literal_match.group(1)
        return value
    
    ## code
    value = handle_code_field(input_json, conversion_table, conversion_record_name, conversion_attributes, required, silent)
            
    if value is not None:
        if not isinstance(value, str):
            print("Error: The code conversion directive to create the \"" + conversion_record_name + \
                  "\" record in the \"" + conversion_table + "\" table did not return a string type value.", 
                  file=sys.stderr)
            sys.exit()
        
        return value
    
    elif value is None and conversion_attributes.get("code") is not None:
        return None
    
    ## fields
    fields = [((re_match.group(1), True) if (re_match := re.match(literal_regex, field)) else (field, False)) for field in conversion_attributes["fields"]]
    has_test = False
    test_field = ""
    test_value = ""
    if test := conversion_attributes.get("test"):
        has_test = True
        split = test.split("=")
        test_field = split[0].strip()
        test_value = split[1].strip()
    
    ## for_each
    for_each = False
    if (for_each_temp := conversion_attributes.get("for_each")) is not None:
        if isinstance(for_each_temp, bool):
            for_each = for_each_temp
        elif isinstance(for_each_temp, str) and for_each_temp.lower() == "true":
            for_each = True
    
    table_records = _build_table_records(has_test, conversion_record_name, conversion_table, conversion_attributes, 
                                         input_json, required, silent, test_field=test_field, test_value=test_value)
    if table_records is None:
        return None
    
    if for_each:
        delimiter = conversion_attributes.get("delimiter", "")
        if delimiter and (literal_match := re.match(literal_regex, delimiter)):
            delimiter = literal_match.group(1)
        
        value_for_each_record = []
        for record_name, record_attributes in table_records.items():
            value = _build_string_value(fields, 
                                        conversion_table, 
                                        conversion_record_name, 
                                        conversion_attributes["table"], 
                                        record_name, 
                                        record_attributes, 
                                        required, 
                                        silent)
            if value is not None:
                value_for_each_record.append(value)
        
        joined_string = delimiter.join(value_for_each_record) if value_for_each_record else None
        return joined_string
    
    ## record_id
    if conversion_attributes.get("record_id"):
        if not conversion_attributes["record_id"] in table_records:
            message = "The \"record_id\" field value, \"" + conversion_attributes["record_id"] + \
                      "\", for conversion, \"" + conversion_record_name + \
                      "\", in conversion table, \"" + conversion_table + "\", does not exist in the \"" + \
                      conversion_attributes["table"] + "\" table of the input JSON."
            return _handle_errors(required, silent, message)
        record_attributes = table_records[conversion_attributes["record_id"]]
        record_name = conversion_attributes["record_id"]
    # elif has_test:
    #     for record_name, record_attributes in input_json[conversion_attributes["table"]].items():
    #         if test_field in record_attributes and record_attributes[test_field] == test_value:
    #             break
    else:
        record_name, record_attributes = list(table_records.items())[0]
        # record_name, record_attributes = list(input_json[conversion_attributes["table"]].items())[0]
    
    value = _build_string_value(fields, 
                                conversion_table, 
                                conversion_record_name, 
                                conversion_attributes["table"], 
                                record_name, 
                                record_attributes, 
                                required, 
                                silent)
            
    return value

                
                
    
def compute_matrix_value(input_json: dict, conversion_table: str, conversion_record_name: str, 
                         conversion_attributes: dict, required: bool, silent: bool=False) -> list[dict]|None:
    """Determine the matrix value for the conversion directive.
    
    Args:
        input_json: the data to build the matrix from.
        conversion_table: the name of the table the conversion record came from, used for good error messaging.
        conversion_record_name: the name of the conversion record, used for good error messaging.
        conversion_attributes: the fields and values of the conversion record.
        required: if True then any problems during execution are errors and the program should exit, else it's just a warning.
        silent: if True don't print warning messages.
    
    Returns:
        the list of dicts for the directive or None if there was a problem and the directive is not required.
    """ 
    
    value = handle_code_field(input_json, conversion_table, conversion_record_name, conversion_attributes, required, silent)
            
    if value is not None:
        if not isinstance(value, list) or not all([isinstance(record, dict) for record in value]):
            print("Error: The code conversion directive to create the \"" + conversion_record_name + \
                  "\" record in the \"" + conversion_table + "\" table did not return a matrix type value.", 
                  file=sys.stderr)
            sys.exit()
        
        return value
    
    elif value is None and conversion_attributes.get("code") is not None:
        return None
        
    ## fields_to_headers
    fields_to_headers = False
    if (fields_to_headers_temp := conversion_attributes.get("fields_to_headers")) is not None:
        if isinstance(fields_to_headers_temp, bool):
            fields_to_headers = fields_to_headers_temp
        elif isinstance(fields_to_headers_temp, str) and fields_to_headers_temp.lower() == "true":
            fields_to_headers = True
        
    
    ## values_to_str
    values_to_str = False
    if (values_to_str_temp := conversion_attributes.get("values_to_str")) is not None:
        if isinstance(values_to_str_temp, bool):
            values_to_str = values_to_str_temp
        elif isinstance(values_to_str_temp, str) and values_to_str_temp.lower() == "true":
            values_to_str = True
        
            
    has_test = False
    test_field = ""
    test_value = ""
    if test := conversion_attributes.get("test"):
        has_test = True
        split = test.split("=")
        test_field = split[0].strip()
        test_value = split[1].strip()
    
    exclusion_headers = conversion_attributes.get("exclusion_headers", [])
    
    headers = []
    if conversion_attributes.get("headers"):
        for pair in conversion_attributes["headers"]:
            split = pair.split("=")
            output_key = split[0].strip()
            input_key = split[1].strip()
            
            if new_output_key := re.match(literal_regex, output_key):
                output_key = new_output_key.group(1)
                output_key_is_literal = True
            else:
                output_key_is_literal = False
            
            if new_input_key := re.match(literal_regex, input_key):
                input_key = new_input_key.group(1)
                input_key_is_literal = True
            else:
                input_key_is_literal = False
            
            headers.append({"output_key":output_key, "output_key_is_literal": output_key_is_literal, 
                            "input_key":input_key, "input_key_is_literal": input_key_is_literal})
    
    optional_headers = conversion_attributes.get("optional_headers", [])
    
    table_records = _build_table_records(has_test, conversion_record_name, conversion_table, conversion_attributes, 
                                         input_json, required, silent, test_field=test_field, test_value=test_value)
    if table_records is None:
        return None
    
        
    if collate := conversion_attributes.get("collate"):
        ## TODO think about whether to do collate.strip() here to remove spaces.
        records = {}
        for record_name, record_attributes in table_records.items():
            if collate not in record_attributes:
                message = "The record, \"" + record_name + "\", in the \"" + conversion_attributes["table"] + \
                          "\" table does not have the field, \"" + collate + \
                          "\", required by the \"collate\" field for the conversion, \"" + \
                          conversion_record_name + "\", in the conversion table, \"" + conversion_table + "\"."
                return _handle_errors(required, silent, message)
            collate_key = record_attributes[collate]
            
            if collate_key not in records:
                records[collate_key] = {}
            
            records[collate_key] = _build_matrix_record_dict(records[collate_key], 
                                                             collate_key, 
                                                             headers, 
                                                             record_name, 
                                                             record_attributes, 
                                                             conversion_table, 
                                                             conversion_record_name, 
                                                             conversion_attributes, 
                                                             fields_to_headers,
                                                             exclusion_headers,
                                                             optional_headers,
                                                             values_to_str, 
                                                             required, 
                                                             silent)
                                
        records = list(records.values())
    
    else:
        records = []
        for record_name, record_attributes in table_records.items():
            temp_dict =  _build_matrix_record_dict({}, 
                                                   None, 
                                                   headers, 
                                                   record_name, 
                                                   record_attributes, 
                                                   conversion_table, 
                                                   conversion_record_name, 
                                                   conversion_attributes, 
                                                   fields_to_headers,
                                                   exclusion_headers,
                                                   optional_headers,
                                                   values_to_str, 
                                                   required, 
                                                   silent)
            
            records.append(temp_dict)
    
    if not records:
        return None
    return records



    
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
# section_directive_fields = ["code", "import"]


