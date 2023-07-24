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



def test_matrix_base_case():
    """Test that a simple matrix directive works as expceted."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../matrix_base_case.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json == {
                          "TREATMENT": {
                            "TREATMENT_SUMMARY": [
                              {
                                "id": "Time Point",
                                "field": "time_point",
                              },
                              {
                                "id": "Treatment",
                                "field": "protocol.id",
                              }
                            ]
                          }
                        }
    
    assert output == ""
    

def test_matrix_collate():
    """Test that collate field for matrix directive works as expceted."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../matrix_collate_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("matrix_collate_test_compare.json"), "r") as f:
        output_compare_json = json.loads(f.read())
        
    assert output_json == output_compare_json
    
    assert output == ""
    

def test_matrix_fields_to_headers():
    """Test that fields_to_headers field for matrix directive works as expceted."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../matrix_fields_to_headers_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("matrix_fields_to_headers_test_compare.json"), "r") as f:
        output_compare_json = json.loads(f.read())
        
    assert output_json == output_compare_json
    
    assert output == ""
    

def test_matrix_fields_to_headers_bool():
    """Test that fields_to_headers field for matrix directive works as expceted if it is a bool."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../matrix_fields_to_headers_bool_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("matrix_fields_to_headers_test_compare.json"), "r") as f:
        output_compare_json = json.loads(f.read())
        
    assert output_json == output_compare_json
    
    assert output == ""
    

def test_matrix_fields_to_headers_exclusion():
    """Test that exclusion_headers field for matrix directive works as expceted."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../matrix_fields_to_headers_exclusion_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("matrix_fields_to_headers_exclusion_test_compare.json"), "r") as f:
        output_compare_json = json.loads(f.read())
        
    assert output_json == output_compare_json
    
    assert output == ""


def test_matrix_values_to_str():
    """Test that values_to_str field for matrix directive works as expected."""
    
    test_file = "NMR_base_input.json"
    
    command = "messes convert generic ../" + test_file  + " output ../matrix_values_to_str_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("matrix_values_to_str_test_compare.json"), "r") as f:
        output_compare_json = json.loads(f.read())
        
    assert output_json == output_compare_json
    
    assert output == ""


def test_matrix_values_to_str_bool():
    """Test that values_to_str field for matrix directive works as expceted when it is a bool."""
    
    test_file = "NMR_base_input.json"
    
    command = "messes convert generic ../" + test_file  + " output ../matrix_values_to_str_bool_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("matrix_values_to_str_test_compare.json"), "r") as f:
        output_compare_json = json.loads(f.read())
        
    assert output_json == output_compare_json
    
    assert output == ""


def test_matrix_code():
    """Test that code field has precedence over other fields."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../matrix_code_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json == {"TREATMENT":{"TREATMENT_SUMMARY":[{}]}}
    assert output == ""


def test_matrix_code_error():
    """Test that an error is printed when the code doesn't return a matrix type."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../matrix_code_error_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path_json.exists()
    
    assert output == 'Error: The code conversion directive to create the "TREATMENT_SUMMARY" record in the "TREATMENT" table did not return a matrix type value.\n'


def test_matrix_test():
    """Test that test field works as expected."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../matrix_test_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json == {
                          "TREATMENT": {
                            "TREATMENT_SUMMARY": [
                              {
                                "id": "Treatment",
                                "field": "protocol.id",
                              }
                            ]
                          }
                        }
    
    assert output == ""


def test_optional_headers_test():
    """Test that optional_headers field works as expected."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../matrix_optional_headers_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json == {
                          "TREATMENT": {
                            "TREATMENT_SUMMARY": [
                              {
                                'allowed_values': ['0', '7', '42'],
                                "id": "Time Point",
                                "field": "time_point",
                              },
                              {
                                'allowed_values': ['naive', 'syngenic', 'allogenic'],
                                "id": "Treatment",
                                "field": "protocol.id",
                              }
                            ]
                          }
                        }
    
    assert output == ""
    

def test_matrix_collate_error():
    """Test that an error is printed when the collate field is not in a record."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../matrix_collate_error_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path_json.exists()
    
    assert output == 'Error: The record, ' + \
                      '"(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0-01_A0_Colon_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A", ' + \
                      'in the "measurement" table does not have the field, "asdf", required by the ' + \
                      '"collate" field for the conversion, "Data", in the conversion table, "MS_METABOLITE_DATA".\n'


def test_matrix_header_no_inputkey_error():
    """Test that an error is printed when there is a header that is not in a record."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../matrix_header_no_inputkey_error_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path_json.exists()
    
    assert output == 'Error: The record, '+\
                      '"(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0-01_A0_Colon_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A",'+\
                      ' in the "measurement" table does not have the field, "asdf", required by the '+\
                      '"headers" field for the conversion, "Data", in the conversion table, "MS_METABOLITE_DATA".\n'
 
                        
def test_matrix_header_no_outputkey_error():
    """Test that an error is printed when there is a header that is not in a record."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../matrix_header_no_outputkey_error_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path_json.exists()
    
    assert output == 'Error: The record, '+\
                      '"(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0-01_A0_Colon_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A",'+\
                      ' in the "measurement" table does not have the field, "qwer", required by the '+\
                      '"headers" field for the conversion, "Data", in the conversion table, "MS_METABOLITE_DATA".\n'


def test_matrix_collate_collision_warning():
    """Test that a warning is printed when a key in collated data is overwritten with a different value."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../matrix_collate_collision_warning.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path_json.exists()
    
    assert 'Warning: When creating the "ENTITY_SUMMARY" matrix for the "ENTITY" ' +\
            'table, different values for the output key, "replicate", were found for the ' +\
            'collate key "subject". Only the last value will be used.\n' in output


def test_matrix_conversion_returns_none_error():
    """Test that an error is printed when a matrix conversion directive returns None."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../matrix_conversion_returns_none_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert not output_path_json.exists()
    
    assert output == 'Error: The conversion directive to create the "TREATMENT_SUMMARY" record in the "TREATMENT" table did not return a value.\n'
    

def test_matrix_that_calls_nested_directive_returning_none_is_not_in_dict():
    """Test that a warning is printed when a matrix conversion directive calls a nested directive that returns None is not required."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../matrix_nested_directive_returns_none_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json == {"CHROMATOGRAPHY":{"CHROMATOGRAPHY_SUMMARY":[{"desc":"Tissue is frozen in liquid nitrogen to stop metabolic processes."}]}}
    
    assert ('Warning: When executing the matrix directive, "CHROMATOGRAPHY_SUMMARY", in the conversion table, '
            '"CHROMATOGRAPHY", a header called the nested directive, "nested_directive%", and '
            'a problem was encountered while executing the directive. Since the "required" field of the nested '
            'directive is "False" the header will not be in the dictionary created for the record, '
            '"tissue_quench", in the "protocol" table.') in output
    
    assert ('Warning: The non-required conversion directive to create the "no_id_needed" '
            'record in the "nested_directive%" table could not be created.') in output
    

def test_matrix_that_calls_nested_directive_returning_none_is_not_in_dict_silent():
    """Test that a warning is NOT printed when a matrix conversion directive calls a nested directive that returns None is not required and has silent=True."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../matrix_nested_directive_returns_none_silent_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output_path_json.exists()
    
    assert output == ""


def test_matrix_headers_nested_directives_work():
    """Test that nested directives work for headers attribute."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../matrix_headers_nested_directives_work.json" 
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
                                "asdf": "4",
                                "4": "asdf"
                              }
                            ]
                          }
                        }
    
    assert output == ""


def test_matrix_headers_nested_directive_returns_wrong_type():
    """Test that a message is printed when a nested directive returns a non string type for key values."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../matrix_headers_nested_directive_returns_wrong_type.json" 
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
                                "123": "asdf"
                              }
                            ]
                          }
                        }
    
    assert output == ('Warning: When executing the matrix directive, "name1", in '
                      'the conversion table, "directive1", a header called the nested directive, '
                      '"directive2%", and the returned value was not a string type. Keys to '
                      'JSON objects must be string types, so, 123, will be cast to a '
                      'string type for the record, "protein_extraction", in the "protocol" table.\n')
    

def test_matrix_headers_calling_record_attribute_wrong_type():
    """Test that a message is printed when a calling record attribute is a non string type for key values."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../matrix_headers_calling_record_attribute_wrong_type.json" 
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
                                "asdf": [
                                  {
                                    "1": "asdf"
                                  }
                                ]
                              }
                            ]
                          }
                        }
    
    assert output == ('Warning: When executing the matrix directive, "name2", in '
                      'the conversion table, "directive2%", a header used a calling '
                      'record attribute, "1", and the value was not a string type. '
                      'Keys to JSON objects must be string types, so, 1, will be '
                      'cast to a string type for the record, "naive", in the "protocol" table.\n')


def test_matrix_record_doesnt_have_header_field():
    """Test that a message is printed when a record doesn't have the attribute indicated in the headers."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../matrix_record_doesn't_have_header_field.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json == {
                          "directive1": {
                            "name1": [
                                None
                            ]
                          }
                        }
    
    assert output == ('Warning: The record, "protein_extraction", in the "protocol" '
                      'table does not have the field, "qwer", required by the "headers" '
                      'field for the conversion, "name1", in the conversion table, "directive1".\n')


def test_matrix_headers_calls_nonexistent_nested_directive():
    """Test that a message is printed when the headers attribute calls a nested directive that doens't exist."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../matrix_headers_calls_nonexistent_nested_directive.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert not output_path_json.exists()        
    
    assert output == ('Error: The conversion directive to create the "name1" '
                      'record in the "directive1" table tries to call a nested '
                      'directive, directive3%, but that directive is not in the '
                      'conversion directives.\n')


def test_matrix_headers_calling_field_for_non_nested_directive_error():
    """Test that an error is printed when a headers element indicates to use a field from a calling record, but is not a nested directive."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../matrix_headers_calling_field_for_non_nested_directive_error.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert not output_path_json.exists()
        
    assert ('Error: When creating the "name1" conversion for the "directive1" '
            'table, the value for "headers", ""asdf"=^.order", indicates to use '
            'a calling record\'s attribute value, but this conversion directive is '
            'not a nested directive and therefore has no calling record.') in output


def test_matrix_no_table_works():
    """Test that a matrix directive can return early if headers is entirely composed of literal values and calling record values."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../matrix_no_table_works.json" 
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
                                "asdf": [
                                  {
                                    "asdf": "4"
                                  }
                                ]
                              }
                            ]
                          }
                        }
    
    assert output == ''


def test_matrix_no_table_error():
    """Test that a message is printed when the header elements require a record, but table is not given."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../matrix_no_table_error.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert not output_path_json.exists()
        
    assert output == ('Error: The conversion directive to create the "name2" '
                      'record in the "directive2%" table has elements in its '
                      '"headers" attribute, "[\'"asdf"=order\']", which are '
                      'attributes to input records, but this directive does not '
                      'provide a "table" attribute to pull records from.\n')


def test_matrix_header_calling_field_not_in_record_error():
    """Test that an error is printed when a header indicates to use a field from a calling record, but that field is not in the record."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../matrix_header_calling_field_not_in_record_error.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert not output_path_json.exists()
        
    assert ('Error: When creating the "name2" conversion for the "directive2%" '
            'table, the value for "headers", ""asdf"=^.orde", indicates to use a '
            'calling record\'s attribute value, but that attribute, "orde", does '
            'not exist in the calling record, "protein_extraction", in the calling table, "protocol".') in output


def test_matrix_header_duplicate_keys_warning():
    """Test that a warning is printed when there are headers with the same key name."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../matrix_headers_duplicate_keys_warning.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output_path_json.exists()
        
    assert ('Warning: When creating the "Extended" matrix for the "MS_METABOLITE_DATA" '
            'table, the key "Metabolite", was specified twice in the "headers" attribute. '
            'Only the last value will be used.') in output


def test_matrix_fields_to_headers_duplicate_keys_warning():
    """Test that a warning is printed when there are specified header keys that are the same
    as what is in the record attributes when fields_to_headers is True."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../matrix_fields_to_headers_duplicate_keys_warning.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output_path_json.exists()
        
    assert ('Warning: When creating the "Extended" matrix for the "MS_METABOLITE_DATA" table, '
            'the record, "tissue_quench", has key names in its attributes that are the '
            'same as key names specified in the "headers" attribute of the directive. '
            'Since "fields_to_headers" was set to True, the values in the record '
            'attributes will overwrite the values specified in "headers" for the following keys:\n'
            'id\n'
            'type') in output


def test_matrix_optional_headers_duplicate_keys_warning():
    """Test that a warning is printed when there are specified header keys that are the same
    as what is in the record attributes and optional_headers."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../matrix_optional_headers_duplicate_keys_warning.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output_path_json.exists()
        
    assert ('Warning: When creating the "Extended" matrix for the "MS_METABOLITE_DATA" table, '
            'the record, "tissue_quench", has key names in its attributes that are the '
            'same as key names specified in the "headers" attribute of the directive. '
            'Since "optional_headers" were given, the values in the record '
            'attributes that are also in "optional_headers" will overwrite the values '
            'specified in "headers" for the following keys:\n'
            'id\n'
            'type') in output