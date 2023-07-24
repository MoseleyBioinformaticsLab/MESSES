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



def test_section_execute_standalone():
    """Test that the execute attribute for section directives works on its own."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../section_execute_standalone_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json == {
                          "directive1": {
                            "termSource": "source",
                            "termAccession": "accession",
                            "annotationValue": "value",
                            "comments": [
                              {
                                "value": "comment"
                              }
                            ]
                          }
                        }
    
    assert output == ""


def test_section_execute_nested():
    """Test that the execute attribute for section directives works when nested."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output ../section_execute_nested_test.json" 
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
                                "asdf": {
                                  "termSource": "source",
                                  "termAccession": "accession",
                                  "annotationValue": "value",
                                  "comments": [
                                    {
                                      "value": "comment"
                                    }
                                  ]
                                }
                              }
                            ]
                          }
                        }
    
    assert output == ""


def test_section_execute_first_record():
    """Test that the section directive will use the first record in the table if no test, for_each, or record_id are given."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../section_execute_first_record_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json == {
                          "directive1": {
                            "termSource": "source",
                            "termAccession": "accession",
                            "annotationValue": "value",
                            "comments": [
                              {
                                "value": "comment"
                              }
                            ]
                          }
                        }
    
    assert output == ""


def test_section_execute_for_each():
    """Test that the section directive will return a list with for_each=True."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../section_execute_for_each_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json == {
                          "directive1": [
                            {
                              "termSource": "source",
                              "termAccession": "accession",
                              "annotationValue": "value",
                              "comments": [
                                {
                                  "value": "comment"
                                }
                              ]
                            },
                            {
                              "termSource": "source2",
                              "termAccession": "accession2",
                              "annotationValue": "value2",
                              "comments": [
                                {
                                  "value": "comment2"
                                }
                              ]
                            }
                          ]
                        }
    
    assert output == ""


def test_section_execute_for_each_error():
    """Test that when encountering an error a messge will be printed and record skipped."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../section_execute_for_each_error.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json == {
                          "directive1": [
                            {
                              "termSource": "source",
                              "termAccession": "accession",
                              "annotationValue": "value",
                              "comments": [
                                {
                                  "value": "comment"
                                }
                              ]
                            },
                            {
                              "termSource": "source2",
                              "termAccession": "accession2",
                              "annotationValue": "value2",
                              "comments": [
                                {
                                  "value": "comment2"
                                }
                              ]
                            }
                          ]
                        }
    
    assert output == ('Warning: The conversion directive to create the "name1" record in the '
                      '"directive1" table encountered a problem while executing its "execute" '
                      'function for the record, "polar_extraction", in the table, "protocol":\n'
                      '"source3 accession3 value3 comment3" is a malformed ontology annotation. '
                      'It must have 3 colons (:) separating its values.\n')


def test_section_execute_for_each_all_None():
    """Test that when all records return None, the directive returns None."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../section_execute_for_each_all_None.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json == {
                          "directive1": None
                        }
    
    assert ('Warning: The non-required conversion directive to create the '
            '"name1" record in the "directive1" table could not be created.\n') in output


def test_section_execute_bad_test_keyword():
    """Test that when the test keyword returns None the directive returns None."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../section_execute_bad_test_keyword.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json == {
                          "directive1": None
                        }
    
    assert ('Warning: The non-required conversion directive to create the '
            '"name1" record in the "directive1" table could not be created.\n') in output


def test_section_execute_no_records_error():
    """Test that when the test matches no records a message is printed and the directive returns None."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../section_execute_no_records_error.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json == {
                          "directive1": None
                        }
    
    assert ('Warning: The non-required conversion directive to create the '
            '"name1" record in the "directive1" table could not be created.\n') in output
    
    assert ('Warning: When creating the "name1" conversion for the "directive1" '
            'table, no records in the "protocol" table matched the test, "order=7", '
            'indicated in the "test" field of the conversion. This could be from '
            'no records containing the test field(s) or no records matching the '
            'test value(s) for those field(s).') in output


def test_section_execute_record_id():
    """Test that the record_id attribute works."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../section_execute_record_id.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json == {
                          "directive1": {
                            "termSource": "source2",
                            "termAccession": "accession2",
                            "annotationValue": "value2",
                            "comments": [
                              {
                                "value": "comment2"
                              }
                            ]
                          }
                        }
    
    assert output == ""


def test_section_execute_nested_calling_record_args():
    """Test that the calling record attributes work as args."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../section_execute_nested_calling_record_args.json" 
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
                                "asdf": {
                                  "termSource": "source2",
                                  "termAccession": "accession2",
                                  "annotationValue": "value2",
                                  "comments": [
                                    {
                                      "value": "comment2"
                                    }
                                  ]
                                }
                              }
                            ]
                          }
                        }
    
    assert output == ""


def test_section_execute_record_id_error():
    """Test that a message is printed when the record_id attribute is bad."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../section_execute_record_id_error.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert not output_path_json.exists()
        
    assert output == ('Error: The "record_id" field value, "protein_extractio", '
                      'for conversion, "name1", in conversion table, "directive1", '
                      'does not exist in the "protocol" table of the input JSON.\n')


def test_section_execute_malformed_value():
    """Test that a message is printed when the execute attribute is bad."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../section_execute_malformed_value.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert not output_path_json.exists()
        
    assert output == ('Error: The conversion directive to create the "name1" record '
                      'in the "directive1" table has a malformed value for its '
                      '"execute" attribute, "dumb_parse_ontology_annotation(ontology_annotation". '
                      'It should be of the form "function_name(function_input1, function_input2, ...)".\n')


def test_section_execute_calling_field_for_non_nested_directive_error():
    """Test that an error is printed when a parameter indicates to use a field from a calling record, but is not a nested directive."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../section_execute_calling_field_for_non_nested_directive_error.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert not output_path_json.exists()
        
    assert ('Error: When creating the "name1" conversion for the "directive1" '
            'table, the value for "execute", "dumb_parse_ontology_annotation(^.order)", '
            'indicates to use a calling record\'s attribute value, but this conversion '
            'directive is not a nested directive and therefore has no calling record.') in output


def test_section_no_table_error():
    """Test that a message is printed when the execute arguments require records, but table is not given."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../section_no_table_error.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert not output_path_json.exists()
        
    assert output == ('Error: The conversion directive to create the "name1" '
                      'record in the "directive1" table calls a function in its '
                      '"execute" attribute, "dumb_parse_ontology_annotation(ontology_annotation)", '
                      'that has arguments which are attributes to input records, but '
                      'this directive does not provide a "table" attribute to pull records from.\n')


def test_section_code_returns_None():
    """Test that a message is printed when the code attribute returns None."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../section_code_returns_None.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert not output_path_json.exists()
        
    assert output == ('Error: The conversion directive to create the "name1" '
                      'record in the "directive1" table did not return a value.\n')


def test_section_execute_nested_calling_record_args_error():
    """Test that a message is printed when the calling record doesn't have the arg specified."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../section_execute_nested_calling_record_args_error.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert not output_path_json.exists()        
    
    assert output == ('Error: When creating the "name2" conversion for the "directive2%" '
                      'table, the value for "execute", "dumb_parse_ontology_annotation(^.ontology_annotatio)", '
                      'indicates to use a calling record\'s attribute value, but that '
                      'attribute, "ontology_annotatio", does not exist in the calling record, '
                      '"protein_extraction", in the calling table, "protocol".\n')


def test_section_execute_standalone_error():
    """Test that a message is printed when the execute function errors without a record value."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../section_execute_standalone_error.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert not output_path_json.exists()        
    
    assert output == ('Error: The conversion directive to create the "name1" record '
                      'in the "directive1" table encountered a problem while executing its "execute" function :\n'
                      '"asdf:  xcvb" is a malformed ontology annotation. It must have 3 colons (:) separating its values.\n')


def test_section_execute_unhandled_error():
    """Test that a message is printed when the execute function errors unexpectedly."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../section_execute_unhandled_error.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert not output_path_json.exists()        
    
    assert ('Error: The conversion directive to create the "name1" record in the '
            '"directive1" table encountered an error while executing its "execute" function.') in output
    
    assert ("TypeError: 'int' object is not iterable") in output


def test_built_in_import():
    """Test that importing a built-in function works as expected."""
    
    test_file = "base_input_for_section_execute.json"
    
    command = "messes convert generic ../" + test_file  + " output ../built_in_import_test.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert output_path_json.exists()
    
    assert output == ""
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json == {
                          "directive1": "asdf"
                        }
    
    




