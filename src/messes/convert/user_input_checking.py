# -*- coding: utf-8 -*-
"""
Validates user input, erroring early and allowing the rest of the program to assume inputs are sanitized.
"""

import re
import sys
import pathlib

import jsonschema


def validate_conversion_directives(conversion_directives: dict, schema: dict):
    """Validate conversion directives.
    
    Wraps around jsonschema.validate() to give more human readable errors 
    for most validation errors.
    
    Args:
        dict_to_validate: instance to validate.
        schema: JSON Schema to validate the instance with.
        
    Raises:
        jsonschema.ValidationError: any validation errors that aren't handled reraise the original.
    """
        
    try:
        jsonschema.validate(conversion_directives, schema)
    except jsonschema.ValidationError as e:
        
        message = "ValidationError: An error was found in the " + schema["title"] + ".\n"
        custom_message = ""
        
        if e.validator == "minProperties":
            message += "The entry " + "[%s]" % "][".join(repr(index) for index in e.relative_path) + " cannot be empty."
        elif e.validator == "required":
            required_property = re.match(r"(\'.*\')", e.message).group(1)
            special_names = ["'code'", "'table'", "'fields'", "'headers'", "'record_id'", "'for_each'", "'override'"]
            
            if required_property in special_names:
                value_type_map = ["str", "matrix", "section"]
                value_type = value_type_map[e.schema_path[3]]
                
                if value_type == "str":
                    message += "'str' type directives have 3 valid configurations:\n" +\
                               "\t1. They have an 'override' property.\n" +\
                               "\t2. They have a 'code' property.\n" +\
                               "\t3. They have the 'table' and 'fields' properties.\n" +\
                               "The entry "+ "[%s]" % "][".join(repr(index) for index in e.relative_path) +\
                               " is not one of the valid configurations."
                
                if value_type == "matrix":
                    message += "'matrix' type directives must either have a 'code' property or 'headers' and 'table' properties.\n" +\
                               "The entry "+ "[%s]" % "][".join(repr(index) for index in e.relative_path) +\
                               " is missing one of these properties."
                
                if value_type == "section":
                    message += "The entry " + "[%s]" % "][".join(repr(index) for index in e.relative_path) + " is missing the required property " + required_property + "."
            else:
                if len(e.relative_path) == 0:
                    message += "The required property " + required_property + " is missing."
                else:
                    message += "The entry " + "[%s]" % "][".join(repr(index) for index in e.relative_path) + " is missing the required property " + required_property + "."
                               
        elif e.validator == "minLength":
            custom_message = " cannot be an empty string."
        elif e.validator == "maxLength":
            custom_message = " is too long."
        elif e.validator == "minItems":
            custom_message = " cannot be empty."
        elif e.validator == "type":
            if type(e.validator_value) == list:
                custom_message = " is not any of the allowed types: ["
                for allowed_type in e.validator_value:
                    custom_message += "\'" + allowed_type + "\', "
                custom_message = custom_message[:-2]
                custom_message += "]."
            else:
                custom_message = " is not of type \"" + e.validator_value + "\"."
        elif e.validator == "enum":
            custom_message = " is not one of [" + "%s" % ", ".join(repr(index) for index in e.validator_value) + "]."
        elif e.validator == "format":
            custom_message = " is not a valid " + e.validator_value + "."
        elif e.validator == "minimum":
            custom_message = " must be greater than or equal to " + str(e.validator_value) + "."
        elif e.validator == "maximum":
            custom_message = " must be less than or equal to " + str(e.validator_value) + "."
        elif e.validator == "pattern":
            ## All of the properties except 'headers' are strings, so path will be 3, but headers is a list so path will be 4.
            property_name = e.relative_path[-2] if len(e.relative_path) == 4 else e.relative_path[-1]
            properties_with_patterns = ["for_each", "required", "fields_to_headers", "values_to_str"]
            if property_name in properties_with_patterns:
                message += "The '" + property_name + "' property for entry " + \
                           "[%s]" % "][".join(repr(index) for index in list(e.relative_path)[0:-1]) + \
                           " must be 'True' or 'False'."
            elif property_name == "test":
                message += "The '" + property_name + "' property for entry " + \
                           "[%s]" % "][".join(repr(index) for index in list(e.relative_path)[0:-1]) + \
                           " must have an '=' in the middle. Ex. type=MS"
            elif property_name == "headers":
                message += "Each element in the '" + property_name + "' property for entry " + \
                           "[%s]" % "][".join(repr(index) for index in list(e.relative_path)[0:-2]) + \
                           " must have an '=' in the middle. Ex. type=MS"
            elif property_name == "sort_order":
                message += "The '" + property_name + "' property for entry " + \
                           "[%s]" % "][".join(repr(index) for index in list(e.relative_path)[0:-1]) + \
                           " must be 'ascending' or 'descending'"
            else:
                raise e
        else:
            raise e
        
        
        if custom_message:
            message = message + "The value for " + "[%s]" % "][".join(repr(index) for index in e.relative_path) + custom_message
        print(message, file=sys.stderr)
        sys.exit()



# def additional_args_checks(args: dict):
#     """Run some checks on args that jsonschema can't do.
    
#     This assumes that args has been validated with a JSON schema and does some 
#     further checking to make sure the values entered by the user make sense. 
#     Prints a message and exits the program if problems are found.
    
#     Args:
#         args: the arguments entered into the program by the user.
#     """
#     file_path_properties = ["--update", "--override", "<conversion_directives>", "<input_JSON>"]
#     for path in file_path_properties:
#         if args[path] and not pathlib.Path(args[path]).exists():
#             print("Error: The value entered for " + path + " is not a valid file path or does not exist.", file=sys.stderr)
#             sys.exit()
                
        







