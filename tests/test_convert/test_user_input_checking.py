# -*- coding: utf-8 -*-

import pytest

import os
import pathlib

from jsonschema import ValidationError
from contextlib import nullcontext as does_not_raise

from messes.convert.user_input_checking import validate_conversion_directives 
# from messes.convert.user_input_checking import additional_args_checks
from messes.convert.convert_schema import directives_schema
from messes.convert.mwtab_conversion_directives import ms_directives, nmr_directives, nmr_binned_directives


## Commenting $schema out because the jsonschema package produces warnings if left in. It is a known issue in their package. 10-18-2021
@pytest.fixture
def test_schema():
    schema = {
#     "$schema": "https://json-schema.org/draft/2020-12/schema",
     "title": "Test Schema",
     "description": "Schema to test tracker_validate",
     
     "type": "object",
     "minProperties":1,
     "properties": {
             "required_test":{"type": "object",
                              "properties": {"required_test": {"type": "string"}},
                              "required": ["required_test"]},
             "max_length_test":{"type": "string", "maxLength":2},
             "empty_string_test": {"type": "string", "minLength": 1},
             "empty_list_test": {"type": "array", "minItems":1},
             "wrong_type_test": {"type": "string"}, 
             "wrong_list_type": {"type":["string", "array"]},
             "enum_test": {"type":"string", "enum":["asdf"]},
             "other_error_type": {"type": "number", "exclusiveMaximum":100}
             },
     "required": ["required_test"]
             
    }
     
    return schema

@pytest.mark.parametrize("instance, error_message", [
        
        ({}, "ValidationError: An error was found in the Test Schema.\nThe entry [] cannot be empty."),
        ({"asdf":"asdf"}, "ValidationError: An error was found in the Test Schema.\nThe required property \'required_test\' is missing."),
        ({"required_test":{"asdf":"asdf"}}, "ValidationError: An error was found in the Test Schema.\nThe entry [\'required_test\'] is missing the required property \'required_test\'."),
        ({"required_test":{"required_test":""}, "max_length_test":"asdf"}, "ValidationError: An error was found in the Test Schema.\nThe value for ['max_length_test'] is too long."),
        ({"required_test":{"required_test":""}, "empty_string_test":""}, "ValidationError: An error was found in the Test Schema.\nThe value for ['empty_string_test'] cannot be an empty string."),
        ({"required_test":{"required_test":""}, "empty_list_test":[]}, "ValidationError: An error was found in the Test Schema.\nThe value for ['empty_list_test'] cannot be empty."),
        ({"required_test":{"required_test":""}, "wrong_list_type":{}}, "ValidationError: An error was found in the Test Schema.\nThe value for ['wrong_list_type'] is not any of the allowed types: ['string', 'array']."),
        ({"required_test":{"required_test":""}, "wrong_type_test":123}, "ValidationError: An error was found in the Test Schema.\nThe value for ['wrong_type_test'] is not of type \"string\"."),
        ({"required_test":{"required_test":""}, "enum_test":"qwer"}, "ValidationError: An error was found in the Test Schema.\nThe value for ['enum_test'] is not one of ['asdf']."),
        ])


def test_validate_conversion_directives(instance, test_schema, error_message, capsys):
        
    with pytest.raises(SystemExit):
        validate_conversion_directives(instance, test_schema)
    captured = capsys.readouterr()
    assert captured.err == error_message + "\n"


def test_validate_conversion_directives_other_errors(test_schema, capsys):
    
    instance = {"required_test":{"required_test":""}, "other_error_type":1000}
    
    with pytest.raises(ValidationError):
        validate_conversion_directives(instance, test_schema)
        

def test_validate_conversion_directives_no_error(test_schema):
    with does_not_raise():
        validate_conversion_directives({"required_test":{"required_test":""}}, test_schema)
        


malformed_str_message = "ValidationError: An error was found in the Conversion Directives.\n" +\
                        "'str' type directives have 3 valid configurations:\n" +\
                        "\t1. They have an 'override' property.\n" +\
                        "\t2. They have a 'code' property.\n" +\
                        "\t3. They have the 'table' and 'fields' properties.\n" +\
                        "The entry ['ANALYSIS']['ANALYSIS_TYPE']" +\
                        " is not one of the valid configurations."
                        
malformed_matrix_message = "ValidationError: An error was found in the Conversion Directives.\n" +\
                           "'matrix' type directives must either have a 'code' property or 'headers' and 'table' properties.\n" +\
                           "The entry ['ANALYSIS']['ANALYSIS_TYPE']" +\
                           " is missing one of these properties."

@pytest.mark.parametrize("instance, error_message", [
        
        ({"ANALYSIS": {
            "ANALYSIS_TYPE": {
              "id": "ANALYSIS_TYPE",
              "value_type": "str",
              "fields":["wqer"],
            }}}, malformed_str_message),
        ({"ANALYSIS": {
            "ANALYSIS_TYPE": {
              "id": "ANALYSIS_TYPE",
            }}}, "ValidationError: An error was found in the Conversion Directives.\nThe entry ['ANALYSIS']['ANALYSIS_TYPE'] is missing the required property 'value_type'."),
        ({"ANALYSIS": {
            "ANALYSIS_TYPE": {
              "id": "ANALYSIS_TYPE",
              "value_type": "matrix",
            }}}, malformed_matrix_message),
        ({"ANALYSIS": {
            "ANALYSIS_TYPE": {
              "id": "ANALYSIS_TYPE",
              "value_type":"section"
            }}}, "ValidationError: An error was found in the Conversion Directives.\nThe entry ['ANALYSIS']['ANALYSIS_TYPE'] is missing the required property 'code'."),
        ({"ANALYSIS": {
            "ANALYSIS_TYPE": {
              "id": "ANALYSIS_TYPE",
              "value_type":"matrix",
              "table":"qwer",
              "headers":["asdf"]
            }}}, "ValidationError: An error was found in the Conversion Directives.\nEach element in the 'headers' property for entry ['ANALYSIS']['ANALYSIS_TYPE'] must have an '=' in the middle. Ex. type=MS"),
        ({"ANALYSIS": {
            "ANALYSIS_TYPE": {
              "id": "ANALYSIS_TYPE",
              "value_type":"str",
              "table":"qwer",
              "fields":["asdf"],
              "for_each":"True",
              "test":"asdf"
            }}}, "ValidationError: An error was found in the Conversion Directives.\nThe 'test' property for entry ['ANALYSIS']['ANALYSIS_TYPE'] must have an '=' in the middle. Ex. type=MS"),
        ({"ANALYSIS": {
            "ANALYSIS_TYPE": {
              "id": "ANALYSIS_TYPE",
              "value_type":"str",
              "table":"qwer",
              "fields":["asdf"],
              "for_each":"True",
              "sort_order":"asdf"
            }}}, "ValidationError: An error was found in the Conversion Directives.\nThe 'sort_order' property for entry ['ANALYSIS']['ANALYSIS_TYPE'] must be 'ascending' or 'descending'"),
        ({"ANALYSIS": {
            "ANALYSIS_TYPE": {
              "id": "ANALYSIS_TYPE",
              "value_type":"str",
              "table":"qwer",
              "fields":["asdf"],
              "for_each":"True",
              "required":"asdf"
            }}}, "ValidationError: An error was found in the Conversion Directives.\nThe 'required' property for entry ['ANALYSIS']['ANALYSIS_TYPE'] must be 'True' or 'False'."),
        ({"ANALYSIS": {
            "ANALYSIS_TYPE": {
              "id": "ANALYSIS_TYPE",
              "value_type":"str",
              "table":"qwer",
              "fields":["asdf"],
              "for_each":"asdf",
              "record_id":"asdf"
            }}}, "ValidationError: An error was found in the Conversion Directives.\nThe 'for_each' property for entry ['ANALYSIS']['ANALYSIS_TYPE'] must be 'True' or 'False'."),
        ({"ANALYSIS": {
            "ANALYSIS_TYPE": {
              "id": "ANALYSIS_TYPE",
              "value_type":"matrix",
              "table":"qwer",
              "headers":["asdf=qwer"],
              "fields_to_headers":"asdf"
            }}}, "ValidationError: An error was found in the Conversion Directives.\nThe 'fields_to_headers' property for entry ['ANALYSIS']['ANALYSIS_TYPE'] must be 'True' or 'False'."),
        ({"ANALYSIS": {
            "ANALYSIS_TYPE": {
              "id": "ANALYSIS_TYPE",
              "value_type":"matrix",
              "table":"qwer",
              "headers":["asdf=qwer"],
              "values_to_str":"asdf"
            }}}, "ValidationError: An error was found in the Conversion Directives.\nThe 'values_to_str' property for entry ['ANALYSIS']['ANALYSIS_TYPE'] must be 'True' or 'False'."),
        ({"ANALYSIS": {
            "ANALYSIS_TYPE": {
              "id": "ANALYSIS_TYPE",
              "value_type":"asdf",
              "table":"qwer",
              "headers":["asdf=qwer"],
              "values_to_str":"asdf"
            }}}, "ValidationError: An error was found in the Conversion Directives.\nThe value for ['ANALYSIS']['ANALYSIS_TYPE']['value_type'] is not one of ['str', 'section', 'matrix']."),
        ])

def test_validate_conversion_directives_malformed_directives_errors(instance, error_message, capsys):
    """Test that some certain kinds of malformed directives error."""
        
    with pytest.raises(SystemExit):
        validate_conversion_directives(instance, directives_schema)
    captured = capsys.readouterr()
    assert captured.err == error_message + "\n"
    

@pytest.mark.parametrize("instance", [
        
        ({"ANALYSIS": {
            "ANALYSIS_TYPE": {
              "id": "ANALYSIS_TYPE",
              "value_type": "str",
              "table":"asdf",
              "fields":["wqer"],
              "record_id":"xcvb"
            }}}),
        ({"ANALYSIS": {
            "ANALYSIS_TYPE": {
              "id": "ANALYSIS_TYPE",
              "value_type": "str",
              "code":"asdf"
            }}}),
        ({"ANALYSIS": {
            "ANALYSIS_TYPE": {
              "id": "ANALYSIS_TYPE",
              "value_type": "str",
              "override":"asdf"
            }}}),
        ({"ANALYSIS": {
            "ANALYSIS_TYPE": {
              "id": "ANALYSIS_TYPE",
              "value_type": "str",
              "table":"asdf",
              "fields":["wqer"],
              "for_each":"True"
            }}}),
        ({"ANALYSIS": {
            "ANALYSIS_TYPE": {
              "id": "ANALYSIS_TYPE",
              "value_type": "matrix",
              "headers":["asdf=qwer"],
              "table":"qwer"
            }}}),
        ({"ANALYSIS": {
            "ANALYSIS_TYPE": {
              "id": "ANALYSIS_TYPE",
              "value_type": "matrix",
              "code":"asdf"
            }}}),
        ({"ANALYSIS": {
            "ANALYSIS_TYPE": {
              "id": "ANALYSIS_TYPE",
              "value_type":"section",
              "code":"asdf"
            }}}),
        ])

def test_validate_conversion_directives_passing(instance):
    """Test that certain directives pass without error."""
    with does_not_raise():
        validate_conversion_directives(instance, directives_schema)


def test_validate_conversion_directives_MS_directives():
    """Test that the mass spec directives pass."""
    with does_not_raise():
        validate_conversion_directives(ms_directives, directives_schema)


def test_validate_conversion_directives_NMR_directives():
    """Test that the NMR directives pass."""
    with does_not_raise():
        validate_conversion_directives(nmr_directives, directives_schema)

def test_validate_conversion_directives_NMR_binned_directives():
    """Test that the NMR binned directives pass."""
    with does_not_raise():
        validate_conversion_directives(nmr_binned_directives, directives_schema)



# @pytest.mark.parametrize("args, error_message", [
        
#         ({"--update":"asdf", "--override":"", "<conversion_directives>":"", "<input_JSON>":""}, "Error: The value entered for --update is not a valid file path or does not exist."),
#         ({"--update":"", "--override":"asdf", "<conversion_directives>":"", "<input_JSON>":""}, "Error: The value entered for --override is not a valid file path or does not exist."),
#         ({"--update":"", "--override":"", "<conversion_directives>":"asdf", "<input_JSON>":""}, "Error: The value entered for <conversion_directives> is not a valid file path or does not exist."),
#         ({"--update":"", "--override":"", "<conversion_directives>":"", "<input_JSON>":"asdf"}, "Error: The value entered for <input_JSON> is not a valid file path or does not exist."),
#         ])


# def test_additional_args_checks_errors(args, error_message, capsys):
#     with pytest.raises(SystemExit):
#         additional_args_checks(args)
#     captured = capsys.readouterr()
#     assert captured.err == error_message + "\n"

# def test_additional_args_checks_passing():
#     additional_args_checks({"--update":"", "--override":"", "<conversion_directives>":"", "<input_JSON>":""})



