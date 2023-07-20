# -*- coding: utf-8 -*-
import pytest

import pathlib
import os
import time
import json
import subprocess



@pytest.fixture(scope="module", autouse=True)
def change_cwd():
    cwd = pathlib.Path.cwd()
    os.chdir(pathlib.Path("tests", "test_convert", "testing_files", "main_dir"))
    yield
    os.chdir(cwd)
    
output_path_json = pathlib.Path("output.json")
@pytest.fixture(autouse=True)
def delete_json():
    # yield
    if output_path_json.exists():
        os.remove(output_path_json)
        time_to_wait=10
        time_counter = 0
        while output_path_json.exists():
            time.sleep(1)
            time_counter += 1
            if time_counter > time_to_wait:
                raise FileExistsError(output_path_json + " was not deleted within " + str(time_to_wait) + " seconds, so it is assumed that it won't be and something went wrong.")




def test_default_directive():
    """Test that default field works as expected."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../default_field_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json == {
                          "TREATMENT": {
                            "TREATMENT_SUMMARY": "qwer"
                          }
                        }
    
    assert 'The conversion directive to create the "TREATMENT_SUMMARY" record in the ' +\
            '"TREATMENT" table could not be created, and reverted to its given default value, "qwer".' in output


def test_default_literal_directive():
    """Test that default field works as expected when it is a literal value."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../default_field_literal_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json == {
                          "TREATMENT": {
                            "TREATMENT_SUMMARY": "qwer"
                          }
                        }
    
    assert 'The conversion directive to create the "TREATMENT_SUMMARY" record in the ' +\
            '"TREATMENT" table could not be created, and reverted to its given default value, "qwer".' in output


def test_table_not_in_input_error():
    """Test that an error is printed when a directive indicates a table that isn't in the input."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../table_not_in_input_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert not output_path_json.exists()
    
    assert output == 'Error: The "table" field value, "asdf", for conversion, ' +\
                      '"TREATMENT_SUMMARY", in conversion table, "TREATMENT", does ' +\
                      'not exist in the input JSON.\n'


def test_table_not_in_input_warning():
    """Test that a warning is printed when a directive indicates a table that isn't in the input and the directive is not required."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../table_not_in_input_warning_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output_path_json.exists()
    
    assert 'Warning: The "table" field value, "asdf", for conversion, ' +\
            '"TREATMENT_SUMMARY", in conversion table, "TREATMENT", does ' +\
            'not exist in the input JSON.' in output


def test_conversion_returns_none_warning():
    """Test that a warning is printed when a conversion directive returns None and is not required."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../conversion_returns_none_warning_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output_path_json.exists()
    
    assert output == 'Warning: The non-required conversion directive to create the "TREATMENT_SUMMARY" record in the "TREATMENT" table could not be created.\n'
    

def test_code_import():
    """Test that import field works as expected."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../code_import_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json == {
                          "TREATMENT": {
                            "TREATMENT_SUMMARY": [
                              {}
                            ]
                          }
                        }
    
    assert output == ""
    

def test_code_import_path_does_not_exist():
    """Test that an error is printed when the import field path does not exist."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../code_import_error_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert not output_path_json.exists()
    
    assert output == 'Error: The path given to import a Python file in the "import" ' +\
                      'field of the conversion record "TREATMENT_SUMMARY" in the "TREATMENT" table does not exist.\n'


def test_silent_in_directive_works():
    """Test that a warning is not printed when silent is true."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../conversion_returns_none_warning_silent_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output_path_json.exists()
    ## Should output this, but it should be silenced.
    #'Warning: The non-required conversion directive to create the "TREATMENT_SUMMARY" record in the "TREATMENT" table could not be created.\n'
    assert output == ""


def test_section_conversion_with_multiple_directives_error():
    """Test that an error is printed when a conversion directive has a section type and additional directives in the same table."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../conversion_section_with_multiple_directives_error.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert not output_path_json.exists()
    
    assert output == 'ValidationError: In the conversion directives, the table, "TREATMENT", has multiple directives and one of them is a section type. Section type directives must be the only directive type in a table if it is present.\n'



def test_test_keyword_literal_field_test():
    """Test that literal fields work as expected for the test keyword."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../test_keyword_literal_field_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json == {
                          "CHROMATOGRAPHY": {
                            "CHROMATOGRAPHY_SUMMARY": "asdf"
                          }
                        }
    
    assert output == ""


def test_test_keyword_calling_field_for_non_nested_directive_error():
    """Test that an error is printed when a directive indicates to use a field from a calling record, but is not a nested directive."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../test_keyword_calling_field_for_non_nested_directive_error.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert not output_path_json.exists()
        
    assert ('Error: When creating the "CHROMATOGRAPHY_SUMMARY" conversion for '
            'the "CHROMATOGRAPHY" table, the value for "test", "machine_type=^.MS", '
            'indicates to use a calling record\'s attribute value, but this conversion '
            'directive is not a nested directive and therefore has no calling record.') in output


def test_test_keyword_calling_field_works():
    """Test that calling field works as expected for the test keyword."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../test_keyword_calling_field_works.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json == {
                          "directive1": {
                            "name1": "asdf"
                          }
                        }
    
    assert output == ""


def test_test_keyword_calling_field_not_in_record_error():
    """Test that an error is printed when a directive indicates to use a field from a calling record, but that field is not in the record."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../test_keyword_calling_field_not_in_record_error.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert not output_path_json.exists()
        
    assert ('Error: When creating the "no_id_needed" conversion for the "directive2%" table, '
            'the value for "test", "machine_type=^.asdf", indicates to use a calling record\'s '
            'attribute value, but that attribute, "asdf", does not exist in the calling record, '
            '"ICMS1", in the calling table, "protocol".') in output


def test_test_keyword_calling_field_not_in_record_warning():
    """Test that a warning is printed when a directive indicates to use a field from a calling record, but that field is not in the record."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../test_keyword_calling_field_not_in_record_warning.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json == {
                          "directive1": None
                        }
        
    assert ('Warning: When creating the "no_id_needed" conversion for the "directive2%" table, '
            'the value for "test", "machine_type=^.asdf", indicates to use a calling record\'s '
            'attribute value, but that attribute, "asdf", does not exist in the calling record, '
            '"ICMS1", in the calling table, "protocol".') in output


def test_nested_directive_not_in_directives_error():
    """Test that an error is printed when a nested directive is called, but that directive is not in the directives."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../test_nested_directive_not_in_directives_error.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert not output_path_json.exists()
        
    assert ('Error: The conversion directive to create the "name1" record in the '
            '"directive1" table tries to call a nested directive, directive3%, but '
            'that directive is not in the conversion directives.') in output


def test_nested_directive_not_in_directives_warning():
    """Test that a warning is printed when a nested directive is called, but that directive is not in the directives."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../test_nested_directive_not_in_directives_warning.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json == {
                          "directive1": None
                        }
        
    assert ('Warning: The conversion directive to create the "name1" record in the '
            '"directive1" table tries to call a nested directive, directive3%, but '
            'that directive is not in the conversion directives.') in output

