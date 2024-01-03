# -*- coding: utf-8 -*-
"""
Functions to execute all directive types.
"""

import re
from inspect import getmembers, isfunction
from typing import Any
import pathlib
from importlib.machinery import SourceFileLoader
import traceback
import copy
import sys
## This needs to be imported so it is available for use in code type directives.
import datetime

from messes.convert import built_ins
from messes.convert import regexes
from messes.convert import helper_functions


_handle_errors = helper_functions._handle_errors
_str_to_boolean_get = helper_functions._str_to_boolean_get
_sort_by_getter = helper_functions._sort_by_getter

literal_regex = regexes.literal_regex
calling_record_regex = regexes.calling_record_regex
nested_directive_regex = regexes.nested_directive_regex

built_in_functions = {attributes[0]:attributes[1] for attributes in getmembers(built_ins, isfunction)}


#########################
## Shared Functions
#########################

def _determine_directive_table_value(input_json: dict, conversion_table: str, conversion_directives: dict,
                                     calling_record_table: str|int=None, calling_record_name: str|int=None, calling_record_attributes: dict=None, 
                                     directive_attribute_replacement: dict=None,
                                     silent: bool=False) -> Any:
    """Call the correct function to execute the directive based on its value_type.
    
    Args:
        input_json: the data to build the matrix from.
        conversion_table: the name of the table the conversion record came from.
        conversion_directives: the conversion directives, used for calling nested directives.
        calling_record_table: if this is a nested directive, then this should be the table of the record the directive was called on, else None.
        calling_record_name: if this is a nested directive, then this should be the key of the record the directive was called on, else None.
        calling_record_attributes: if this is a nested directive, then this should be the attributes of the record the directive was called on, else None.
        directive_attribute_replacement: a dictionary like {'all': {field:value, ...}, 'named': {'directive1': {field:value, ...}, ...}} used to overwrite directive attributes for nested directive tables.
        silent: if True don't print warning messages.
    
    Returns:
        the value returned by executing the directive.
    """
    directive_table_output = {}
    for conversion_record_name, conversion_attributes in conversion_directives[conversion_table].items():
        conversion_attributes = copy.deepcopy(conversion_attributes)
        if directive_attribute_replacement:
            for field, value in directive_attribute_replacement["all"].items():
                if field in conversion_attributes:
                    conversion_attributes[field] = value
                if parameters := directive_attribute_replacement["named"].get(conversion_record_name):
                    for field, value in parameters.items():
                        if field in conversion_attributes:
                            conversion_attributes[field] = value
        
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
        value_defaulted = False        
        if value is None:
            if default is None:
                if required:
                    message = (f"The conversion directive to create the \"{conversion_record_name}"
                               f"\" record in the \"{conversion_table}\" table did not return a value.")
                    _handle_errors(required, silent, message)
                    sys.exit()
                else:
                    message = ("The non-required conversion directive to create the \""
                               f"{conversion_record_name}\" record in the \"{conversion_table}\" table could not be created.")
                    _handle_errors(required, silent, message)
                    continue
            else:
                value = default
                value_defaulted = True
                if not silent:
                    message = (f"The conversion directive to create the \"{conversion_record_name}"
                               f"\" record in the \"{conversion_table}"
                               f"\" table could not be created, and reverted to its given default value, \"{default}\".")
                    _handle_errors(required, silent, message)
                
        if "section" in conversion_attributes["value_type"]:
            directive_table_output = value
        else:
            directive_table_output[conversion_record_name] = value
            
    ##TODO Should there be a check here to see if the entire conversion table returns None and do something?
                
    return directive_table_output if directive_table_output or value_defaulted else None



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
            ## The ^.* syntax was created for passing calling record attributes into a built-in function, so it 
            ## might not be appropriate here. If this does weird stuff during testing it should probably just be 
            ## removed. I simply went ahead and added this code to all the spots that might be able to use it 
            ## not just the "execute" keyword.
            if calling_field[1] == "*":
                test_value = calling_record_attributes
            else:
                test_value = calling_record_attributes[calling_field[1]]
        
        elif match := re.match(literal_regex, test_value):
            test_value = match.group(1)
            
        if match := re.match(literal_regex, test_field):
            test_field = match.group(1)
        
        replacement_text = (f"(\"{test_field}\" in record_attributes and "
                            f"((isinstance(record_attributes[\"{test_field}\"], str) and "
                            f"record_attributes[\"{test_field}\"] == \"{test_value}\") or "
                            f"(isinstance(record_attributes[\"{test_field}\"], list) and "
                            f"\"{test_value}\" in record_attributes[\"{test_field}\"])))")
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
                      f"This could be from no records containing the test field(s) or no records matching the test value(s) for those field(s). "
                      f"The full translated test code is: \n{test_string}")
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
        built_in_functions.update({attributes[0]:attributes[1] for attributes in getmembers(global_variables[import_name], isfunction)})
    
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
        
        if calling_field not in calling_record_attributes and calling_field != "*":
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
                                 conversion_table: str, conversion_record_name: str, conversion_directives: dict,
                                 record_table: str|int, record_name: str|int, record_attributes: dict,
                                 calling_record_table: str|int, calling_record_name: str|int, calling_record_attributes: dict,
                                 required: bool, silent: bool) -> tuple[bool, str|None]:
    """Determine if string is a nested_directive.
    
    Determines if string_to_test is a nested diretive, but also parses any parameters passed 
    to the directive and does error checking. Parameters can be literal values, fields to 
    records, or fields to calling records.
    
    Args:
        string_to_test: string to determine if it is pointing to a calling record field.
        conversion_table: the name of the table the conversion record came from, used for good error messaging.
        conversion_record_name: the name of the conversion record, used for good error messaging.
        conversion_directives: the conversion directives, used for calling nested directives.
        record_table: the name of the table for the record the directive has in context.
        record_name: the name of the record the directive has in context.
        record_attributes: the fields and values of the record the directive has in context.
        calling_record_table: if this is a nested directive, then this should be the table of the record the directive was called on, else None.
        calling_record_name: if this is a nested directive, then this should be the key of the record the directive was called on, else None.
        calling_record_attributes: if this is a nested directive, then this should be the attributes of the record the directive was called on, else None.
        required: if True then any problems during execution are errors and the program should exit, else it's just a warning.
        silent: if True don't print warning messages.
        
    Returns:
        A tuple where the first value is a bool indicating if string_to_test matches the syntax for a nested directive, 
        the second value is the nested directive name or None, and the third value is a dictionary of parameters being 
        passed to the nested directive or None.
    """
    
    if re_match := re.match(nested_directive_regex, string_to_test):
        ## Parse string to directive and parameters.
        directive = re_match.group(1)
        parameters = [stripped for word in re_match.group(2).split(',') if (stripped := word.strip())]
        
        ## Check that directive table exists and that parameters are not malformed.
        if directive not in conversion_directives:
            message = (f"The conversion directive to create the \"{conversion_record_name}"
                      f"\" record in the \"{conversion_table}\" table tries to call a nested directive table, "
                      f"{directive}, but that directive table is not in the conversion directives.")
            _handle_errors(required, silent, message)
            return True, None, None
        
        if not all([re.match(r".+=.+", parameter) for parameter in parameters]):
            message = (f"The conversion directive to create the \"{conversion_record_name}"
                      f"\" record in the \"{conversion_table}\" table tries to call a nested directive table, "
                      f"{string_to_test}, but at least one parameter passed to it is malformed. "
                      "All parameters must be of the form \"key=value\" or \"name.key=value\".")
            _handle_errors(required, silent, message)
            return True, None, None
        
        ## Parse parameters into a dictionary to be easily used later.
        nested_directive_keys = {key for values in conversion_directives[directive].values() for key in values.keys()}
        parameters_dict = {"all":{}, "named":{}}
        for parameter in parameters:
            split = [word.strip() for word in parameter.split('=')]
            key_and_name = [word for word in split[0].strip().split('.')]
            key = key_and_name[1] if len(key_and_name) > 1 else key_and_name[0]
            name = key_and_name[0] if len(key_and_name) > 1 else None
            value = split[1].strip()
            
            ## Determine if the value is literal, a record field, or a calling field.
            if (calling_field := _is_field_in_calling_record(value, 
                                                             "a nested directive parameter", 
                                                             parameter, 
                                                             conversion_table, 
                                                             conversion_record_name,
                                                             calling_record_table, 
                                                             calling_record_name, 
                                                             calling_record_attributes,
                                                             required, 
                                                             silent))[0]:
                ## No value means it matched the syntax, but there were no fields in the calling record that matched.
                if calling_field[1] is None:
                    continue
                if calling_field[1] == "*":
                    value = calling_record_attributes
                else:
                    value = calling_record_attributes[calling_field[1]]
            
            
            elif match := re.match(literal_regex, value):
                value = match.group(1)
                        
            else:
                if value not in record_attributes:
                    message = (f"When creating the \"{conversion_record_name}"
                              f"\" conversion for the \"{conversion_table}\" table, the value for a nested directive parameter, "
                              f"\"{parameter}\", indicates to use a record's attribute value, but that attribute, \""
                              f"{value}\", does not exist in the record, \""
                              f"{record_name}\", in the table, \"{record_table}\". "
                              "This parameter will be ignored when calling the nested directive table.")
                    _handle_errors(False, silent, message)
                    continue
                value = record_attributes[value]
            
            ## Check that any named parameters exist and that the key exists in the directive.
            if name:
                if name not in conversion_directives[directive].keys():
                    message = (f"The conversion directive to create the \"{conversion_record_name}"
                              f"\" record in the \"{conversion_table}\" table calls a nested directive table, "
                              f"{directive}, but the parameter, {parameter}, passed to it has a "
                              f"directive name, \"{name}\", that is not in the directive table. "
                              "This parameter will be ignored when calling the nested directive table.")
                    _handle_errors(False, silent, message)
                    continue
                    
                if key not in nested_directive_keys:
                    message = (f"The conversion directive to create the \"{conversion_record_name}"
                              f"\" record in the \"{conversion_table}\" table calls a nested directive table, "
                              f"{directive}, but the parameter, {parameter}, passed to it has a "
                              f"key, \"{key}\", that is not in the directive, \"{name}\", indicated by the parameter. "
                              "This parameter will be ignored when calling the nested directive table.")
                    _handle_errors(False, silent, message)
                    continue
                
                if name in parameters_dict["named"]:
                    if key in parameters_dict["named"][name]:
                        message = (f"The conversion directive to create the \"{conversion_record_name}"
                                  f"\" record in the \"{conversion_table}\" table calls a nested directive table, "
                                  f"{directive}, and the parameter, {parameter}, passed to it has a "
                                  f"key, \"{key}\", that was specified  twice for the \"{name}\" directive. "
                                  "The previously specified value for this parameter will be ignored, "
                                  "and only the latest value will be used.")
                        _handle_errors(False, silent, message)
                    
                    parameters_dict["named"][name][key] = value
                else:
                    parameters_dict["named"][name] = {key:value}
                
                
                
            else:
                ## Check that non-named keys exist somewhere in the directive table.
                if key not in nested_directive_keys:
                    message = (f"The conversion directive to create the \"{conversion_record_name}"
                              f"\" record in the \"{conversion_table}\" table calls a nested directive table, "
                              f"{directive}, but the parameter, {parameter}, passed to it has a key that "
                              "is not in any of the directives within the table. "
                              "This parameter will be ignored when calling the nested directive table.")
                    _handle_errors(False, silent, message)
                    continue
                
                if key in parameters_dict["all"]:
                    message = (f"The conversion directive to create the \"{conversion_record_name}"
                              f"\" record in the \"{conversion_table}\" table calls a nested directive table, "
                              f"{directive}, and the parameter, {parameter}, passed to it has a "
                              f"key, \"{key}\", that was specified  twice. "
                              "The previously specified value for this parameter will be ignored, "
                              "and only the latest value will be used.")
                    _handle_errors(False, silent, message)
                
                parameters_dict["all"][key] = value
        
        return True, directive, parameters_dict
    
    return False, None, None








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
        match = re.match(r"(.+)\((.*)\)", execute.strip())
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
                if calling_field[1] == "*":
                    function_argument = (False, calling_record_attributes)
                else:
                    function_argument = (False, calling_record_attributes[calling_field[1]])
            
            elif match := re.match(literal_regex, function_argument):
                function_argument = (False, match.group(1))
            
            ## Have to handle the empty string case.
            elif not function_argument:
                continue
            
            else:
                function_argument = (True, function_argument)
            
            function_argument_tuples.append(function_argument)
                                
        
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
            ## Check that any arguments that should be fields to a record exist.
            for entry in function_argument_tuples:
                if entry[0] and entry[1] not in record_attributes:
                    message = (f"When creating the \"{conversion_record_name}"
                              f"\" conversion for the \"{conversion_table}\" table, the value for \"execute\", \""
                              f"{conversion_attributes['execute']}\", indicates to use a record's attribute value, but that attribute, \""
                              f"{entry[1]}\", does not exist in the record, \""
                              f"{record_name}\", in the table, \"{record_table}\".")
                    _handle_errors(required, silent, message)
                    return None
            
            value = _run_built_in_function(function_name, 
                                           [record_attributes[entry[1]] if entry[0] else entry[1] for entry in function_argument_tuples], 
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
    
    ## Check that any arguments that should be fields to a record exist.
    for entry in function_argument_tuples:
        if entry[0] and entry[1] not in record_attributes:
            message = (f"When creating the \"{conversion_record_name}"
                      f"\" conversion for the \"{conversion_table}\" table, the value for \"execute\", \""
                      f"{conversion_attributes['execute']}\", indicates to use a record's attribute value, but that attribute, \""
                      f"{entry[1]}\", does not exist in the record, \""
                      f"{record_name}\", in the table, \"{record_table}\".")
            _handle_errors(required, silent, message)
            return None

    
    return _run_built_in_function(function_name, 
                                  [record_attributes[entry[1]] if entry[0] else entry[1] for entry in function_argument_tuples], 
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
            if calling_field[1] == "*":
                override = calling_record_attributes
            else:
                override = calling_record_attributes[calling_field[1]]
        
        elif match := re.match(literal_regex, override):
            override = match.group(1)
                        
        return override
    
    ## code
    value = _handle_code_field(input_json, conversion_table, conversion_record_name, conversion_attributes, conversion_directives, 
                               required, calling_record_table, calling_record_name, calling_record_attributes, silent)
            
    if value is not None:
        if not isinstance(value, str):
            message = (f"The code conversion directive to create the \"{conversion_record_name}"
                       f"\" record in the \"{conversion_table}\" table did not return a string type value.")
            _handle_errors(required, silent, message)
            sys.exit()
        
        return value
    
    elif value is None and conversion_attributes.get("code") is not None:
        return None
    
    ## fields
    fields = conversion_attributes["fields"]
    if "table" not in conversion_attributes:
        if not all([True if re.match(literal_regex, field) or \
                            re.match(calling_record_regex, field) or \
                            re.match(nested_directive_regex, field) else False for field in fields]):
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
                                   calling_record_table, 
                                   calling_record_name, 
                                   calling_record_attributes, 
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
                                                            record_table,
                                                            record_name,
                                                            record_attributes,
                                                            calling_record_table,
                                                            calling_record_name,
                                                            calling_record_attributes,
                                                            required, 
                                                            silent))[0]:
                if directive[1]:
                    table_value = _determine_directive_table_value(input_json, 
                                                                   directive[1],  
                                                                   conversion_directives,
                                                                   record_table, 
                                                                   record_name, 
                                                                   record_attributes, 
                                                                   directive[2],
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
            message = (f"The code conversion directive to create the \"{conversion_record_name}"
                       f"\" record in the \"{conversion_table}\" table did not return a matrix type value.")
            _handle_errors(True, silent, message)
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
        if not all([True if re.match(literal_regex, string) or \
                            re.match(calling_record_regex, string) or \
                            re.match(nested_directive_regex, string) else False for string in header_strings]):
            message = (f"The conversion directive to create the \"{conversion_record_name}"
                      f"\" record in the \"{conversion_table}\" table has elements in its \"headers\" "
                      f"attribute, \"{headers}\", which are attributes to input records, "
                      "but this directive does not provide a \"table\" attribute to pull records from.")
            return _handle_errors(required, silent, message)
    
        return [_build_matrix_record_dict(input_json,
                                         {}, 
                                         None, 
                                         headers, 
                                         calling_record_table, 
                                         calling_record_name, 
                                         calling_record_attributes,
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
                                         silent)]
    
    table_records = _build_table_records(has_test, conversion_record_name, conversion_table, conversion_attributes, 
                                         input_json, required, silent, test_string=test_string)
    if table_records is None:
        return None
    
    record_table = conversion_attributes["table"]
        
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
                                                             record_table,
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
                                                   record_table,
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
                              record_table: str,
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
        record_table: the name of the table the record is from, used for good error messaging.
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
    
    left_keys = set()
    for header in headers:
        input_key, input_key_value, output_key, output_key_value, skip_header = _determine_header_input_keys(input_json,
                                                                                                             header, 
                                                                                                             record_table,
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
        
        if input_key_value in matrix_dict and output_key_value != matrix_dict[input_key_value]:
            if collate_key is not None:
                message = (f"When creating the \"{conversion_record_name}"
                      f"\" matrix for the \"{conversion_table}\" table, the record, \"{record_name}\", "
                      f"from the \"{record_table}\" table produced a different value for the header, \"{header}\", than "
                      f"what was previously found on other records while collating over "
                      f"\"{collate_key}\". The previous value of \"{matrix_dict[input_key_value]}\" will "
                      f"be overwritten with the value produced by the current record, \"{output_key_value}\".")
                _handle_errors(False, silent, message)
            else:
                message = (f"When creating the \"{conversion_record_name}"
                      f"\" matrix for the \"{conversion_table}\" table, the header, "
                      f"\"{header}\", produced the same key value, \"{input_key_value}\", "
                      f"as a previous header. The previous value of \"{matrix_dict[input_key_value]}\" will "
                      f"be overwritten with the new value, \"{output_key_value}\".")
                _handle_errors(False, silent, message)
        
        matrix_dict[input_key_value] = output_key_value
        left_keys.add(input_key_value)
    
    
    if fields_to_headers:
        duplicate_keys = left_keys.intersection(record_attributes.keys())
        if duplicate_keys and collate_key is None:
            duplicate_keys = '\n'.join(sorted(duplicate_keys))
            message = (f"When creating the \"{conversion_record_name}"
                  f"\" matrix for the \"{conversion_table}\" table, the record, \"{record_name}\", "
                  f"from the \"{record_table}\" table has key names in its attributes that are the same as key names specified in "
                  f"the \"headers\" attribute of the directive. Since \"fields_to_headers\" was "
                  f"set to True, the values in the record attributes will overwrite the values "
                  f"specified in \"headers\" for the following keys:\n"
                  f"{duplicate_keys}")
            _handle_errors(False, silent, message)
        
        for field, value in record_attributes.items():
            if field in exclusion_headers:
                continue
            
            value_to_save = str(value) if values_to_str else value
            if collate_key is not None and field in matrix_dict and value_to_save != matrix_dict[field]:
                message = (f"When creating the \"{conversion_record_name}"
                      f"\" matrix for the \"{conversion_table}\" table, the record, \"{record_name}\", "
                      f"from the \"{record_table}\" table has a different value for \"{field}\" than what was previously found on other "
                      f"records while collating over \"{collate_key}\". The previous value of \"{matrix_dict[field]}\" will "
                      f"be overwritten with the value of the current record, \"{value_to_save}\".")
                _handle_errors(False, silent, message)
            
            matrix_dict[field] = value_to_save
        
    else:
        optional_headers_to_add = set(record_attributes.keys()).intersection(optional_headers)
        duplicate_keys = left_keys.intersection(optional_headers_to_add)
        if duplicate_keys and collate_key is None:
            duplicate_key_strings = '\n'.join(sorted(duplicate_keys))
            message = (f"When creating the \"{conversion_record_name}"
                  f"\" matrix for the \"{conversion_table}\" table, the record, \"{record_name}\", "
                  f"from the \"{record_table}\" table has key names in its attributes that are the same as key names specified in "
                  f"the \"headers\" attribute of the directive. Since \"optional_headers\" were "
                  f"given, the values in the record attributes that are also in \"optional_headers\" "
                  f"will overwrite the values specified in \"headers\" for the following keys:\n"
                  f"{duplicate_key_strings}")
            _handle_errors(False, silent, message)
        
        ## Have to loop over optional_headers to preserve order, optional_headers_to_add loses order.
        for header in optional_headers:
            if header not in optional_headers_to_add:
                continue
            value_to_save = str(record_attributes[header]) if values_to_str else record_attributes[header]
            if collate_key is not None and header in matrix_dict and value_to_save != matrix_dict[header]:
                message = (f"When creating the \"{conversion_record_name}"
                      f"\" matrix for the \"{conversion_table}\" table, the record, \"{record_name}\", "
                      f"from the \"{record_table}\" table has a different value for \"{header}\" than what was previously found on other "
                      f"records while collating over \"{collate_key}\". The previous value of \"{matrix_dict[header]}\" will "
                      f"be overwritten with the value of the current record, \"{value_to_save}\".")
                _handle_errors(False, silent, message)
            matrix_dict[header] = value_to_save
                
    return matrix_dict



def _determine_header_input_keys(input_json: dict, header: str, record_table: str, record_name: str, record_attributes: dict, conversion_table: str, 
                                 conversion_record_name: str, conversion_attributes: dict, conversion_directives: dict, 
                                 values_to_str: bool, required: bool, calling_record_table: str|int=None, 
                                 calling_record_name: str|int=None, calling_record_attributes: dict=None,  
                                 silent: bool=False) -> tuple[str,str, str, Any]:
    """Based on the header dict pull the correct values from the record_attributes.
    
    Args:
        input_json: the entire input data the output is being created from.
        header: a string of the form "input_key=output_key" where the keys can be literal values or fields from a record.
                If the keys are literal then they should be returned as is, if not they are fields in record_attributes.
        record_table: the name of the table the record is from, used for good error messaging.
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
    split = header.split("=", 1)
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
                
                if key_name == "output_key" and not isinstance(key_value, str):
                    message = (f"When executing the matrix directive, \"{conversion_record_name}\", "
                               f"in the conversion table, \"{conversion_table}\", a header used a calling "
                               f"record attribute, \"{calling_record_attributes[calling_field[1]]}\", and the value was "
                               f"not a string type. Keys to JSON objects must be string types, so, {key_value}, will "
                               f"be cast to a string type for the record, \"{record_name}\", in the \"{record_table}\" table.")
                    _handle_errors(False, silent, message)
                    key_value = str(key_value)
            else:
                return None, None, None, None, False
        
        elif (directive := _is_field_a_nested_directive(key, 
                                                        conversion_table, 
                                                        conversion_record_name,
                                                        conversion_directives,
                                                        record_table,
                                                        record_name,
                                                        record_attributes,
                                                        calling_record_table,
                                                        calling_record_name,
                                                        calling_record_attributes,
                                                        required, 
                                                        silent))[0]:
            
            if directive[1]:
                table_value = _determine_directive_table_value(input_json, 
                                                               directive[1],  
                                                               conversion_directives,
                                                               record_table, 
                                                               record_name, 
                                                               record_attributes, 
                                                               directive[2],
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
                                   f"created for the record, \"{record_name}\", in the \"{record_table}\" table.")
                        _handle_errors(nested_required, nested_silent, message)
                        return None, None, None, None, True
                
                key_value = str(table_value) if values_to_str else table_value
                
                if key_name == "output_key" and not isinstance(key_value, str):
                    message = (f"When executing the matrix directive, \"{conversion_record_name}\", "
                               f"in the conversion table, \"{conversion_table}\", a header called "
                               f"the nested directive, \"{directive[1]}\", and the returned value was "
                               f"not a string type. Keys to JSON objects must be string types, so, {key_value}, will "
                               f"be cast to a string type for the record, \"{record_name}\", in the \"{record_table}\" table.")
                    _handle_errors(False, silent, message)
                    key_value = str(key_value)
            
            else:
                return None, None, None, None, False
                    
        
        else:    
            if key not in record_attributes:
                ## If required is False then the this header is simply skipped.
                message = (f"The record, \"{record_name}\", in the \"{record_table}"
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
            
    return input_key, input_key_value, output_key, output_key_value, skip_header




