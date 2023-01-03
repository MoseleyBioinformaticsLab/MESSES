# -*- coding: utf-8 -*-
"""
Convert JSON data to another JSON format.

Usage:
    messes convert mwtab (ms | nmr | nmr_binned) <input_JSON> <output_name> [--update <conversion_tags> | --override <conversion_tags>] [--silent]
    messes convert print-tags mwtab (ms | nmr | nmr_binned) <output_filetype> [<output_name>]
    messes convert generic <input_JSON> <output_name> <conversion_tags> [--silent]
    messes convert --help
    
    <conversion_tags> - can be a JSON, csv, or xlsx file. If xlsx the default sheet name to read in is #convert, 
                        to specify a different sheet name separate it from the file name with a colon ex: file_name.xlsx:sheet_name.

Options:
    -h, --help                           - show this screen.
    -v, --version                        - show version.
    --silent                             - silence all warnings.
    --update <conversion_tags>           - conversion tags that will be used to update the built-in tags for the format.
                                           This is intended to be used for simple changes such as updating the value of 
                                           the analysis ID. You only have to specify what needs to change, any values 
                                           that are left out of the update tags won't be changed. If you need to remove 
                                           tags then use the override option.
    --override <conversion_tags>         - conversion tags that will be used to override the built-in tags for the format.
                                           The entire tag JSON must be specified, any tags that are not in the override JSON 
                                           will be removed.
    
    

The general command structure for convert is convert <format> which will convert an input JSON file over to the supported format. 
The outputs of these commands will save both the JSON conversion and the final format file.
The generic command is the same as the supported formats except the user is required to input conversion tags specifying how to 
convert the input JSON to the desired output JSON. Only an output JSON is saved.
The print-tags command is used to print the default conversion tags used by convert for any of the supported formats. <output-filetype> 
can be one of "json", "xlsx", or "csv". The file is saved as "format_conversion_tags.ext" where ".ext" is replaced with ".json", ".xlsx", 
or ".csv" depending on the value of <output-format>.

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

import pandas
import docopt
import mwtab

from ..extract import extract
from .. import __version__
from . import mwtab_conversion_tags
from . import mwtab_tag_functions

## Should all protocol types loop over all protocols and concat them or only certain ones? collection does not and treatment does currently.
## Should the MS metabolite Data be intensity or corrected_raw_intensity? There are submitted data using intensity, but the convert code is corrected_raw.
## natural abundance corrected and protein normalized peak area for intensity vs natural abundance corrected peak area for corrected_raw
## Currently the Treatment factor in SSF is a list, make sure this converts into mwTab text correctly.
## Optionally put non required fields as empty strings instead of not including them. This is done with default value.
## Should default value work if code is given but fails? Right now only works if field is not found.

supported_formats_and_sub_commands = {"mwtab":["ms", "nmr", "nmr_binned"]}

def main() :
    args = docopt.docopt(__doc__, version=__version__)
    
    ## Validate args.
    
    
    ## Determine conversion_tags.
    conversion_tags = {}
    format_under_operation = "generic"
    for supported_format, sub_commands in supported_formats_and_sub_commands.items():
        if args[supported_format]:
            format_under_operation = supported_format
            sub_command = [sub_command for sub_command in supported_formats_and_sub_commands[supported_format] if args[sub_command]][0]
            conversion_tags = eval(supported_format + "_conversion_tags." + sub_command + "_tags")
            break
        
    if filepath := next((arg for arg in [args["<conversion_tags>"], args["--update"], args["--override"]] if arg is not None), False):
        if re.search(r".*(\.xls[xm]?|\.csv)", filepath):
            default_sheet_name = False
            if re.search(r"\.xls[xm]?$", filepath):
                filepath += ":#convert"
                default_sheet_name = True
            tagParser = extract.TagParser()
            if worksheet_tuple := tagParser.loadSheet(filepath, isDefaultSearch=default_sheet_name):
                tagParser.parseSheet(*worksheet_tuple)
                update_conversion_tags = tagParser.extraction
            else:
                if default_sheet_name:
                    print("Error: No sheet name was given for the xlsx file, so the default name " +\
                          "of #convert was used, but it was not found in the file.", file=sys.stderr)
                sys.exit()
        
        elif re.match(r".*\.json$", filepath):
            with open(filepath, 'r') as jsonFile:
                update_conversion_tags = json.load(jsonFile)
        
        else:
            print("Error: Unknown file type for the conversion tags file.", file=sys.stderr)
            sys.exit()
            
        if args["--update"]:
            update(conversion_tags, update_conversion_tags)
        else:
            conversion_tags = update_conversion_tags
    
    ## Handle print-tags command.
    ## TODO add an option so it prints to screen instead of saving.
    if args["print-tags"]:
        if args["<output_name>"]:
            if re.match(r".*\." + args["<output_filetype>"] + "$", args["<output_name>"]):
                save_name = args["<output_name>"]
            else:
                save_name = args["<output_name>"] + "." + args["<output_filetype>"]
        else:
            save_name = format_under_operation + "_" + sub_command + "_conversion_tags." + args["<output_filetype>"]
        
        if args["<output_filetype>"] == "json":
            with open(save_name,'w') as jsonFile:
                jsonFile.write(json.dumps(conversion_tags, indent=2))
        elif args["<output_filetype>"] == "xlsx":
            table_to_save = tags_to_table(conversion_tags)
            table_to_save.to_excel(save_name, index=False, header=False)
        elif args["<output_filetype>"] == "csv":
            table_to_save = tags_to_table(conversion_tags)
            table_to_save.to_csv(save_name, index=False, header=False)
        else:
            print("Error: Unknown output filetype.", file=sys.stderr)
            
        sys.exit()
        
    
    ## Validate conversion tags.
    ## Make sure fields tag has a requirement for at least 1 value.
    
    
    ## Read in files.
    with open(args["<input_JSON>"], 'r') as jsonFile:
        input_json = json.load(jsonFile)
    
    
    ## Generate new JSON.
    output_json = {}
    for conversion_table, conversion_records in conversion_tags.items():
        for conversion_record_name, conversion_attributes in conversion_records.items():
            required = True
            if required_attr := conversion_attributes.get("required"):
                if required_attr.lower() == "false":
                    required = False
                    
            default = conversion_attributes.get("default")
            if default and (literal_match := re.match(literal_regex, default)):
                default = literal_match.group(1)
            
            if conversion_attributes["value_type"] == "section":
                value = handle_code_tag(input_json, conversion_table, conversion_record_name, conversion_attributes, required, args["--silent"])
                keys = [conversion_table]
            elif conversion_attributes["value_type"] == "matrix":
                value = compute_matrix_value(input_json, conversion_table, conversion_record_name, conversion_attributes, required, args["--silent"])
                keys = [conversion_table, conversion_record_name]
            elif conversion_attributes["value_type"] == "str":
                value = compute_string_value(input_json, conversion_table, conversion_record_name, conversion_attributes, required, args["--silent"])
                keys = [conversion_table, conversion_record_name]
            else:
                print("Warning: Unknown value_type for the conversion \"" + conversion_record_name + \
                      "\" in the \"" + conversion_table + "\" table. It will be skipped.", file=sys.stderr)
                continue
            
            if value is None:
                if default is None:
                    if required:
                        print("Error: The conversion tag to create the \"" + conversion_record_name + \
                              "\" record in the \"" + conversion_table + "\" table did not return a value.", 
                              file=sys.stderr)
                        sys.exit()
                    else:
                        if not args["--silent"]:
                            print("Warning: The non-required conversion tag to create the \"" + \
                                  conversion_record_name + "\" record in the \"" + conversion_table + "\" table could not be created.", 
                                  file=sys.stderr)
                        continue
                else:
                    value = default
                    if not args["--silent"]:
                        print("The conversion tag to create the \"" + conversion_record_name + \
                              "\" record in the \"" + conversion_table + \
                              "\" table could not be created, and reverted to its given default value, \"" + default + "\".", 
                              file=sys.stderr)
            
            # if value is None and required:
            #     print("Error: The conversion tag to create the \"" + conversion_record_name + "\" record in the \"" + conversion_table + "\" table did not return a value.")
            #     sys.exit()
            # elif value is None and not required:
            #     if not args["--silent"]:
            #         print("Warning: The non-required conversion tag to create the \"" + conversion_record_name + "\" record in the \"" + conversion_table + "\" table could not be created.")
            #     continue
            
            _nested_set(output_json, keys, value)
    
    
    
    ## Save the generated json.
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
        
        mwtabfile = mwtab.mwtab.MWTabFile("")
        mwtabfile.update(output_json)
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

def _handle_errors(required, silent, message):
    if required:
        print("Error: " + message, file=sys.stderr)
        sys.exit()
    else:
        if not silent:
            print("Warning: " + message, file=sys.stderr)
        return None


def update(original_dict, upgrade_dict):
    for key, value in upgrade_dict.items():
        if isinstance(value, collections.abc.Mapping):
            original_dict[key] = update(original_dict.get(key, {}), value)
        else:
            original_dict[key] = value
    return original_dict


def _nested_set(dic, keys, value):
    for key in keys[:-1]:
        dic = dic.setdefault(key, {})
    dic[keys[-1]] = value


def _sort_by_getter(pair, keys):
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
#         message = "The \"sort_by\" conversion tag to create the \"" + conversion_record_name + \
#                   "\" conversion in the \"" + conversion_table + "\" table has an input key, " + str(e) + \
#                   ", that was not in the \"" + e.pair[0] + "\" record of the \"" + input_table + "\"."
#         return _handle_errors(required, silent, message)
    
#     return table_records


def _build_table_records(has_test, conversion_record_name, conversion_table, conversion_attributes, 
                         input_json, required, silent, test_field="", test_value=""):
    
    if not conversion_attributes["table"] in input_json:
        message = "The \"table\" field value, \"" + conversion_attributes["table"] + "\", for conversion, \"" + conversion_record_name + \
                  "\", in conversion table, \"" + conversion_table + "\", does not exist in the input JSON."
        return _handle_errors(required, silent, message)
    
    if has_test:
        table_records = {record:record_attributes for record, record_attributes in input_json[conversion_attributes["table"]].items() if test_field in record_attributes and record_attributes[test_field] == test_value}
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
            table_records = dict(sorted(table_records.items(), key = lambda pair: _sort_by_getter(pair, sort_by), reverse = conversion_attributes.get("sort_order", "") == "descending"))
            ## table_records used to be a list of dicts and this was the sort, leaving it here in case it is needed.
            # table_records = sorted(table_records, key = operator.itemgetter(*sort_by), reverse = conversion_attributes["sort_order"] == "descending")
        except KeyError as e:
            message = "The record, \"" + e.pair[0] + "\", in the \"" + conversion_attributes["table"] + \
                      "\" table does not have the field, " + str(e) + \
                      ", required by the \"sort_by\" field for the conversion, \"" + \
                      conversion_record_name + "\", in the conversion table, \"" + conversion_table + "\"."
            return _handle_errors(required, silent, message)
        
    return table_records


def handle_code_tag(input_json, conversion_table, conversion_record_name, conversion_attributes, required, silent=False):
    """"""
    
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
            message = "The code conversion tag to create the \"" + conversion_record_name + \
                      "\" record in the \"" + conversion_table + "\" table encountered an error while executing.\n"
            message += traceback.format_exc()
            return _handle_errors(required, silent, message)
        
        return value
    else:
        return None



def _build_string_value(fields, conversion_table, conversion_record_name, record_table, record_name, record_attributes, required, silent):
    value = None
    for field in fields:
        ## Is the field a literal?
        if not field[1]:
            ## If the field is not a literal value and it's not in the record print an error.
            if field[0] not in record_attributes:
                message = "The conversion tag to create the \"" + conversion_record_name + \
                          "\" record in the \"" + conversion_table + "\" table matched a record in the input \"" + \
                          record_table + "\" table, \"" + record_name + "\", that did not contain the \"" + \
                          field[0] + "\" field indicated by the tag."
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



def _build_matrix_record_dict(matrix_dict, 
                              collate_key, 
                              headers, 
                              record, 
                              record_attributes, 
                              conversion_table, 
                              conversion_record_name, 
                              conversion_attributes, 
                              fields_to_headers,
                              exclusion_headers,
                              optional_headers,
                              values_to_str, 
                              required, 
                              silent):
    for header in headers:
        input_key_value, output_key_value = _determine_header_input_keys(header, 
                                                                         record, 
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


def _determine_header_input_keys(header, record, record_attributes, conversion_table, conversion_record_name, conversion_attributes, values_to_str, required, silent):
    if not header["input_key_is_literal"]:
        if header["input_key"] not in record_attributes:
            message = "The record, \"" + record + "\", in the \"" + conversion_attributes["table"] + \
                      "\" table does not have the field, \"" + header["input_key"] + \
                      "\", required by the \"headers\" field for the conversion, \"" + \
                      conversion_record_name + "\", in the conversion table, \"" + conversion_table + "\"."
            return _handle_errors(required, silent, message)
        
        output_key_value = str(record_attributes[header["input_key"]]) if values_to_str else record_attributes[header["input_key"]]
    else:
        output_key_value = header["input_key"]
    
    if not header["output_key_is_literal"]:
        if header["output_key"] not in record_attributes:
            message = "The record, \"" + record + "\", in the \"" + conversion_attributes["table"] + \
                      "\" table does not have the field, \"" + header["output_key"] + \
                      "\", required by the \"headers\" field for the conversion, \"" + \
                      conversion_record_name + "\", in the conversion table, \"" + conversion_table + "\"."
            return _handle_errors(required, silent, message)
        
        input_key_value = record_attributes[header["output_key"]]
    else:
        input_key_value = header["output_key"]
        
    return input_key_value, output_key_value




def compute_string_value(input_json, conversion_table, conversion_record_name, conversion_attributes, required, silent=False):
    """"""            
    
    ## override
    if value := conversion_attributes.get("override"):
        ## Not sure why I put this here. override should always be interpreted as literal and just copy whatever is in the field.
        # if literal_match := re.match(literal_regex, value):
        #     value = literal_match.group(1)
        return value
    
    ## code
    value = handle_code_tag(input_json, conversion_table, conversion_record_name, conversion_attributes, required, silent)
            
    if value is not None:
        if not isinstance(value, str):
            print("Error: The code conversion tag to create the \"" + conversion_record_name + \
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
    if for_each_temp := conversion_attributes.get("for_each"):
        if for_each_temp.lower() == "true":
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
            value_for_each_record.append(value)
        
        joined_string = delimiter.join(value_for_each_record)
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

                
                
    
def compute_matrix_value(input_json, conversion_table, conversion_record_name, conversion_attributes, required, silent=False):
    """"""
    
    value = handle_code_tag(input_json, conversion_table, conversion_record_name, conversion_attributes, required, silent)
            
    if value is not None:
        if not isinstance(value, list) or not all([isinstance(record, dict) for record in value]):
            print("Error: The code conversion tag to create the \"" + conversion_record_name + \
                  "\" record in the \"" + conversion_table + "\" table did not return a matrix type value.", 
                  file=sys.stderr)
            sys.exit()
        
        return value
    
    elif value is None and conversion_attributes.get("code") is not None:
        return None
        
    ## fields_to_headers
    fields_to_headers = False
    if fields_to_headers_temp := conversion_attributes.get("fields_to_headers"):
        if fields_to_headers_temp.lower() == "true":
            fields_to_headers = True
    
    ## values_to_str
    values_to_str = False
    if values_to_str_temp := conversion_attributes.get("values_to_str"):
        if values_to_str_temp.lower() == "true":
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
    
    ## TODO Should there be an option so that headers are not required to be in the input data?
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
    
    ## TODO think about changing optional_headers to inclusion_headers and having an option about printing warnings if the headers aren't there.
    optional_headers = conversion_attributes.get("optional_headers", [])
    
    table_records = _build_table_records(has_test, conversion_record_name, conversion_table, conversion_attributes, 
                                         input_json, required, silent, test_field=test_field, test_value=test_value)
    if table_records is None:
        return None
    
        
    if collate := conversion_attributes.get("collate"):
        ## TODO think about whether to do collate.strip() here to remove spaces.
        ## TODO make sure there is validation that checks that headers are unique.
        records = {}
        for record, record_attributes in table_records.items():
            if collate not in record_attributes:
                message = "The record, \"" + record + "\", in the \"" + conversion_attributes["table"] + \
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
                                                             record, 
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
            
            ## TODO pull this for loop into a function and replace here and below.
            # for header in headers:
            #     input_key_value, output_key_value = _determine_header_input_keys(header, 
            #                                                                      record, 
            #                                                                      record_attributes, 
            #                                                                      conversion_table, 
            #                                                                      conversion_record_name, 
            #                                                                      conversion_attributes, 
            #                                                                      values_to_str, 
            #                                                                      required, 
            #                                                                      silent)
                
            #     if input_key_value in records[collate_key] and output_key_value != records[collate_key][input_key_value]:
            #         print("Warning: When creating the \"" + conversion_record_name + \
            #               "\" matrix for the \"" + conversion_table + "\" table different values for the output key, \"" + \
            #               header["output_key"] + "\", were found for the collate key \"" + collate_key + \
            #               "\". Only the last value will be used.", 
            #               file=sys.stderr)
                
            #     records[collate_key][input_key_value] = output_key_value
            
            # if fields_to_headers:
            #     if values_to_str:
            #         records[collate_key].update({field:str(value) for field, value in record_attributes.items() if field not in exclusion_headers})
            #     else:
            #         records[collate_key].update({field:value for field, value in record_attributes.items() if field not in exclusion_headers})
            # else:
            #     for header in optional_headers:
            #         if header in record_attributes:
            #             records[collate_key][header] = str(record_attributes[header]) if values_to_str else record_attributes[header]
                    
        records = list(records.values())
    
    else:
        records = []
        for record, record_attributes in table_records.items():
            temp_dict =  _build_matrix_record_dict({}, 
                                                   None, 
                                                   headers, 
                                                   record, 
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
            
            # for header in headers:
            #     input_key_value, output_key_value = _determine_header_input_keys(header, 
            #                                                                      record, 
            #                                                                      record_attributes, 
            #                                                                      conversion_table, 
            #                                                                      conversion_record_name, 
            #                                                                      conversion_attributes, 
            #                                                                      values_to_str, 
            #                                                                      required, 
            #                                                                      silent)
                
            #     temp_dict[input_key_value] = output_key_value
                
            # if fields_to_headers:
            #     if values_to_str:
            #         temp_dict.update({field:str(value) for field, value in record_attributes.items() if field not in exclusion_headers})
            #     else:
            #         temp_dict.update({field:value for field, value in record_attributes.items() if field not in exclusion_headers})
            # else:
            #     for header in optional_headers:
            #         if header in record_attributes:
            #             temp_dict[header] = str(record_attributes[header]) if values_to_str else record_attributes[header]
                    
            records.append(temp_dict)
    
    if not records:
        return None
    return records



    
def tags_to_table(conversion_tags: dict) -> pandas.core.frame.DataFrame:
    """"""
    
    df_list = []
    for table, records in conversion_tags.items():
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
            
                    
                
                
str_tag_fields = ["id", "value_type", "override", "code", "import", "table", "for_each", "fields", "test", "required", "delimiter", "sort_by", "sort_order", "record_id"]
matrix_tag_fields = ["id", "value_type", "code", "import", "table",  "test", "required", "sort_by", "sort_order", "headers", "collate", "exclusion_headers", "optional_headers", "fields_to_headers", "values_to_str"]
section_tag_fields = ["code", "import"]





# input_json["entity"] = {}
# for sample_name, sample_attributes in input_json["sample"].items():
#     input_json["entity"][sample_name] = sample_attributes
#     input_json["entity"][sample_name]["type"] = "sample"
# for subject_name, subject_attributes in input_json["subject"].items():
#     input_json["entity"][subject_name] = subject_attributes
#     input_json["entity"][subject_name]["type"] = "subject"

# input_json["factor"] = \
# {'Treatment': {
#   'allowed_values': ['naive', 'syngenic', 'allogenic'],
#   'id': 'Treatment',
#   'field': 'protocol.id',
#   'project.id': 'GH_Spleen',
#   'study.id': 'GH_Spleen'},
#  'Time Point': {
#   'allowed_values': ['0', '7', '42'],
#   'id': 'Time Point',
#   'field': 'time_point',
#   'project.id': 'GH_Spleen',
#   'study.id': 'GH_Spleen'}}


## Create binned nmr
# from random import uniform

# temp = {}
# for measurement, measurement_attributes in input_json["measurement"].items():
#     bottom_range = uniform(0, 1000)
#     top_range = uniform(bottom_range, 1000)
    
#     assignment = str(bottom_range) + "-" + str(top_range)
#     intensity = measurement_attributes["intensity"]
#     units = measurement_attributes["intensity%type"]
    
#     temp[assignment] = {"intensity": intensity, "intensity%type":units, "assignment":assignment, "sample.id":measurement_attributes["sample.id"]}
    
# input_json["measurement"] = temp

# with open('C:/Users/Sparda/Desktop/Moseley Lab/Code/MESSES/tests/test_convert/testing_files/NMR_binned_base_input.json','w') as jsonFile:
#     jsonFile.write(json.dumps(input_json, indent=2))


## Remove isotopologues from MS data
# keys_to_delete = []
# for measurement, measurement_attributes in input_json["measurement"].items():
#     if measurement_attributes["isotopologue"] != "13C0":
#         keys_to_delete.append(measurement)
        
# for key in keys_to_delete:
#     del input_json["measurement"][key]

# with open('C:/Users/Sparda/Desktop/Moseley Lab/Code/MESSES/tests/test_convert/testing_files/MS_base_input_truncated.json','w') as jsonFile:
#     jsonFile.write(json.dumps(input_json, indent=2))
