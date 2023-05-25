# -*- coding: utf-8 -*-
import pytest

import jsonschema

from messes.validate.validate import print_better_error_messages, create_validator

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
             "other_error_type": {"type": "number", "exclusiveMaximum":100},
             "dependent_test": {"type":"string"},
             "dependent_test2": {"type":"string"},
             "pattern_test":{"pattern":"^.*asdf$"},
             "min_test":{"minimum":100}
             },
     "required": ["required_test"],
     "dependencies":{"dependent_test":["asdf"]},
     "dependentRequired":{"dependent_test2":["qwer"]}
             
    }
     
    return schema


@pytest.mark.parametrize("instance, error_message", [
        
        ({}, "The value for [] cannot be empty."),
        ({"asdf":"asdf"}, "The required property \'required_test\' is missing."),
        ({"required_test":{"asdf":"asdf"}}, "The entry [\'required_test\'] is missing the required property \'required_test\'."),
        ({"required_test":{"required_test":""}, "max_length_test":"asdf"}, "The value for ['max_length_test'] is too long."),
        ({"required_test":{"required_test":""}, "empty_string_test":""}, "The value for ['empty_string_test'] cannot be an empty string."),
        ({"required_test":{"required_test":""}, "empty_list_test":[]}, "The value for ['empty_list_test'] cannot be empty."),
        ({"required_test":{"required_test":""}, "wrong_list_type":{}}, "The value for ['wrong_list_type'] is not any of the allowed types: ['string', 'array']."),
        ({"required_test":{"required_test":""}, "wrong_type_test":123}, "The value for ['wrong_type_test'] is not of type \"string\"."),
        ({"required_test":{"required_test":""}, "enum_test":"qwer"}, "The value for ['enum_test'] is not one of ['asdf']."),
        ({"dependent_test2":""}, "Error:  The entry [] is missing a dependent property.\n'qwer' is a dependency of 'dependent_test2'"),
        ({"pattern_test":""}, "Error:  The value for ['pattern_test'] does not match the regular expression pattern ^.*asdf$"),
        ({"min_test":50}, "Error:  The value for ['min_test'] must be greater than or equal to 100."),
        ])


def test_print_better_error_messages_common_errors(instance, test_schema, error_message, capsys):
    """Test that various bad instances produce the error we expect."""
    
    print_better_error_messages(create_validator(test_schema).iter_errors(instance))
    captured = capsys.readouterr()
    assert error_message in captured.err
    

def test_print_better_error_messages_dependencies(test_schema, capsys):
    """Have to test the dependencies keyword with an old validator draft."""
    
    print_better_error_messages(jsonschema.validators.Draft4Validator(test_schema).iter_errors({"dependent_test":""}))
    captured = capsys.readouterr()
    assert "Error:  The entry [] is missing a dependent property.\n'asdf' is a dependency of 'dependent_test'" in captured.err


def test_print_better_error_messages_other_errors(test_schema, capsys):
    """Test that an error type not specifically caught for a special message defaults to jsonschema message."""
    
    instance = {"required_test":{"required_test":""}, "other_error_type":1000}
    
    assert print_better_error_messages(create_validator(test_schema).iter_errors(instance))
        

def test_print_better_error_messages_no_error(test_schema, capsys):
    """Test that no message is produced and False is returned when schema is valid."""
    
    assert not print_better_error_messages(create_validator(test_schema).iter_errors({"required_test":{"required_test":""}}))
    captured = capsys.readouterr()
    assert captured.err == ""
