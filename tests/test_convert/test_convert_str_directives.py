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


def test_str_override():
    """Test that override field has precedence over other fields."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../str_override_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json == {"CHROMATOGRAPHY":{"CHROMATOGRAPHY_SUMMARY":"test_value"}}
    assert output == ""
    

def test_str_override_literal():
    """Test that override field has precedence over other fields and works with literal value."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../str_override_literal_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json == {"CHROMATOGRAPHY":{"CHROMATOGRAPHY_SUMMARY":"test_value"}}
    assert output == ""
    

def test_str_code():
    """Test that code field has precedence over other fields."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../str_code_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json == {"CHROMATOGRAPHY":{"CHROMATOGRAPHY_SUMMARY":"test_value"}}
    assert output == ""
    

def test_str_first_record_with_test():
    """Test that when for_each, code, record_id, and override aren't present the first record that meets the test is used."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../str_first_record_with_test_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json == {"CHROMATOGRAPHY":{"CHROMATOGRAPHY_SUMMARY":"Targeted IC"}}
    assert output == ""


def test_str_record_id():
    """Test that when for_each, code, and override aren't record_id is used."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../str_record_id_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json == {"CHROMATOGRAPHY":{"CHROMATOGRAPHY_SUMMARY":"Thermo Dionex ICS-5000+"}}
    assert output == ""
    

def test_str_record_id_error():
    """Test that when the indicated record_id is missing an error is printed."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../str_record_id_error_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path_json.exists()
    
    assert output == 'Error: The "record_id" field value, "asdf", for conversion, ' +\
                      '"CHROMATOGRAPHY_SUMMARY", in conversion table, "CHROMATOGRAPHY", ' +\
                      'does not exist in the "protocol" table of the input JSON.' +'\n'


def test_str_first_record():
    """Test that when for_each, code, record_id, and override aren't present the first record is used."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../str_first_record_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json == {"CHROMATOGRAPHY":{"CHROMATOGRAPHY_SUMMARY":"Before going into the IC-FTMS the frozen sample is reconstituted in water."}}
    assert output == ""


def test_str_for_each_with_test():
    """Test that for_each with a test works as expected."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../str_for_each_with_test_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json == {"TREATMENT":{"TREATMENT_SUMMARY":"Mouse with allogenic bone marrow transplant. "+\
                                                            "Fed with semi-liquid diet supplemented with fully labeled glucose for 24 hours before harvest. "+\
                                                            "Mouse with no treatment. Fed with semi-liquid diet supplemented with fully labeled glucose for 24 hours before harvest. "+\
                                                            "Mouse with syngenic bone marrow transplant. "+\
                                                            "Fed with semi-liquid diet supplemented with fully labeled glucose for 24 hours before harvest."}}
    assert output == ""


def test_str_for_each():
    """Test that for_each works as expected."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../str_for_each_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json == {"TREATMENT":{"TREATMENT_SUMMARY":"Time PointTreatment"}}
    assert output == ""


def test_str_for_each_bool():
    """Test that for_each works as expected when it is a bool."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../str_for_each_bool_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json == {"TREATMENT":{"TREATMENT_SUMMARY":"Time PointTreatment"}}
    assert output == ""


def test_str_code_wrong_value():
    """Test that when a code directive returns the wrong type an error is printed."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../str_code_wrong_type_error.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert not output_path_json.exists()
            
    assert output == 'Error: The code conversion directive to create the "TREATMENT_SUMMARY" record in the "TREATMENT" table did not return a string type value.\n'


def test_str_no_field_error():
    """Test that when a record does not have an indicated field an error is printed."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../str_no_field_error.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert not output_path_json.exists()
            
    assert output == 'Error: The conversion directive to create the "CHROMATOGRAPHY_SUMMARY" record in the "CHROMATOGRAPHY" table matched a record in the input "protocol" table, "ICMS1", that did not contain the "asdf" field indicated by the directive.\n'


def test_str_code_error():
    """Test that when a code directive encouners an error during execution an error is printed."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../str_code_error.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert not output_path_json.exists()
            
    assert 'Error: The code conversion directive to create the "TREATMENT_SUMMARY" record in the "TREATMENT" table encountered an error while executing.' in output
    assert 'Traceback (most recent call last):' in output
    assert "SyntaxError: '(' was never closed" in output


def test_str_no_matching_table_records():
    """Test that when there is no matching records an error is printed."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../str_no_matching_records.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert not output_path_json.exists()
    
    assert 'Error: When creating the "TREATMENT_SUMMARY" conversion for the "TREATMENT" table,' in output
    assert 'no records in the "factor" table matched the test, "type=asdf",' in output
    assert 'indicated in the "test" field of the conversion. This could be from no' in output
    assert 'records containing the test field(s) or no records matching the test value(s) for those field(s).' in output


def test_str_no_matching_table_records_warning():
    """Test that when there is no matching records and the directive is not required a warning is printed."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../str_no_matching_records_warning.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert output_path_json.exists()
    
    assert 'Warning: When creating the "TREATMENT_SUMMARY" conversion for the "TREATMENT" table,' in output
    assert 'no records in the "factor" table matched the test, "type=asdf",' in output
    assert 'indicated in the "test" field of the conversion. This could be from no' in output
    assert 'records containing the test field(s) or no records matching the test value(s) for those field(s).' in output


def test_str_no_matching_table_records_bool_warning():
    """Test that when there is no matching records and the directive is not required a warning is printed, and that required field can be a bool."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../str_no_matching_records_bool_warning.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert output_path_json.exists()
        
    assert 'Warning: When creating the "TREATMENT_SUMMARY" conversion for the "TREATMENT" table,' in output
    assert 'no records in the "factor" table matched the test, "type=asdf",' in output
    assert 'indicated in the "test" field of the conversion. This could be from no' in output
    assert 'records containing the test field(s) or no records matching the test value(s) for those field(s).' in output
        

def test_str_no_table_records():
    """Test that when there are no records an error is printed."""
    
    test_file = "MS_base_input_truncated_no_factor_records.json"
    
    command = "messes convert generic ../" + test_file  + " output ../str_no_records.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert not output_path_json.exists()
    
    assert 'Error: When creating the "TREATMENT_SUMMARY" conversion for the "TREATMENT" table, there were no records in the indicated "factor" table.' in output
    
    
def test_str_no_sort_by_field():
    """Test that when a record doesn't have the indicated field to sort by an error is printed."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../str_no_sort_by.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert not output_path_json.exists()
    
    assert 'Error: The record, "Time Point", in the "factor" table does not have the field,' in output 
    assert '\'asdf\', required by the "sort_by" field for the conversion,' in output
    assert '"TREATMENT_SUMMARY", in the conversion table, "TREATMENT".' in output


def test_str_literal_field_test():
    """Test that a literal field works as expected."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../str_literal_field_test.json" 
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


def test_str_conversion_returns_none_error():
    """Test that an error is printed when a str conversion directive returns None."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../str_conversion_returns_none_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert not output_path_json.exists()
    
    assert output == 'Error: The conversion directive to create the "TREATMENT_SUMMARY" record in the "TREATMENT" table did not return a value.\n'


def test_str_that_calls_nested_directive_returning_none_is_not_concatenated():
    """Test that a warning is printed when a str conversion directive calls a nested directive that returns None is not required."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../str_nested_directive_returns_none_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json == {"CHROMATOGRAPHY":{"CHROMATOGRAPHY_SUMMARY":"Before going into the IC-FTMS the frozen sample is reconstituted in water."}}
    
    assert ('Warning: When executing the str directive, "CHROMATOGRAPHY_SUMMARY", in the conversion table, '
            '"CHROMATOGRAPHY", a value in the "field" called the nested directive, "nested_directive%", and '
            'a problem was encountered while executing the directive. Since the "required" field of the nested '
            'directive is "False" the field will not be concatenated in the result created for the record, '
            '"IC-FTMS_preparation", in the "protocol" table.') in output
    
    assert ('Warning: The non-required conversion directive to create the "no_id_needed" '
            'record in the "nested_directive%" table could not be created.') in output


def test_str_that_calls_nested_directive_returning_none_is_not_concatenated_silent():
    """Test that a warning is NOT printed when a str conversion directive calls a nested directive that returns None is not required and has silent=True."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../str_nested_directive_returns_none_silent_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output_path_json.exists()
    
    assert output == ""


def test_str_override_calling_record_args():
    """Test that the calling record attributes work as args for override attribute."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../str_override_calling_record_args.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json == {
                          "directive1": {
                            "name1": [
                              {
                                "asdf": "4"
                              }
                            ]
                          }
                        }
    
    assert output == ""


def test_str_override_calling_record_args_error():
    """Test that a message is printed when the override attribute has a bad calling record arg."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../str_override_calling_record_args_error.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert not output_path_json.exists()        
    
    assert output == ('Error: When creating the "name2" conversion for the '
                      '"directive2%" table, the value for "override", "^.orde", '
                      'indicates to use a calling record\'s attribute value, but '
                      'that attribute, "orde", does not exist in the calling record, '
                      '"protein_extraction", in the calling table, "protocol".\n')


def test_str_fields_calling_record_args_solo():
    """Test that the calling record attributes work as args for field attribute."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../str_fields_calling_record_args_solo.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json == {
                          "directive1": {
                            "name1": [
                              {
                                "asdf": "4"
                              }
                            ]
                          }
                        }
    
    assert output == ""


def test_str_fields_calling_record_args_multiple():
    """Test that the calling record attributes work as args for field attribute."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../str_fields_calling_record_args_multiple.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json == {
                          "directive1": {
                            "name1": [
                              {
                                "asdf": "asdf43"
                              }
                            ]
                          }
                        }
    
    assert output == ""


def test_str_fields_calling_record_args_error():
    """Test that a message is printed when the fields attribute has a bad calling record arg."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../str_fields_calling_record_args_error.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert not output_path_json.exists()        
    
    assert output == ('Error: When creating the "name2" conversion for the "directive2%" '
                      'table, the value for "fields", "^.orde", indicates to use a '
                      'calling record\'s attribute value, but that attribute, "orde", '
                      'does not exist in the calling record, "protein_extraction", '
                      'in the calling table, "protocol".\n')


def test_str_fields_cals_wrong_nested_type():
    """Test that a message is printed when the fields attribute calls a nested directive that does not return a str type."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../str_fields_calls_wrong_nested_type.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json == {
                          "directive1": {
                            "name1": "[123]"
                          }
                        }
    
    assert output == ('Warning: When executing the str directive, "name1", in the '
                      'conversion table, "directive1", a value in the "fields" '
                      'called the nested directive, "directive2%", and the returned '
                      'value was not a string type. Return types must be string types, '
                      'so, [123], will be cast to a string type for the record, '
                      '"protein_extraction", in the "protocol" table.\n')


def test_str_fields_calls_nonexistent_nested_directive():
    """Test that a message is printed when the fields attribute calls a nested directive that doens't exist."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../str_fields_calls_nonexistent_nested_directive.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert not output_path_json.exists()        
    
    assert output == ('Error: The conversion directive to create the "name1" '
                      'record in the "directive1" table tries to call a nested '
                      'directive, directive3%, but that directive is not in the '
                      'conversion directives.\n')


def test_str_fields_nested_directive_works():
    """Test that nested directives work for field attribute."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../str_fields_nested_directive_works.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json == {
                          "directive1": {
                            "name1": "asdfqwer4"
                          }
                        }
    
    assert output == ""


def test_str_fields_calling_field_for_non_nested_directive_error():
    """Test that an error is printed when a fields element indicates to use a field from a calling record, but is not a nested directive."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../str_fields_calling_field_for_non_nested_directive_error.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert not output_path_json.exists()
        
    assert ('Error: When creating the "name1" conversion for the "directive1" '
            'table, the value for "fields", "^.order", indicates to use a '
            'calling record\'s attribute value, but this conversion directive '
            'is not a nested directive and therefore has no calling record.') in output


def test_str_no_table_error():
    """Test that a message is printed when the fields elements require a record, but table is not given."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../str_no_table_error.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert not output_path_json.exists()
        
    assert output == ('Error: The conversion directive to create the "name2" '
                      'record in the "directive2%" table has elements in its '
                      '"fields" attribute, "[\'order\']", which are attributes '
                      'to input records, but this directive does not provide a '
                      '"table" attribute to pull records from.\n')


def test_str_no_table_works():
    """Test that a str directive can return early if fields is entirely composed of literal values and calling record values."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../str_no_table_works.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json == {
                          "directive1": {
                            "name1": [
                              {
                                "asdf": "4"
                              }
                            ]
                          }
                        }
    
    assert output == ''




