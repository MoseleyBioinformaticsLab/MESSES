# -*- coding: utf-8 -*-
import pytest

import pathlib
import os
import time
import copy
import json
import subprocess
import re

import pandas


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


# def test_str_override():
#     """Test that override field has precedence over other fields."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../str_override_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path_json.exists()
    
#     with open(output_path_json, "r") as f:
#         output_json = json.loads(f.read())
        
#     assert output_json == {"CHROMATOGRAPHY":{"CHROMATOGRAPHY_SUMMARY":"test_value"}}
#     assert output == ""
    

# def test_str_code():
#     """Test that code field has precedence over other fields."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../str_code_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path_json.exists()
    
#     with open(output_path_json, "r") as f:
#         output_json = json.loads(f.read())
        
#     assert output_json == {"CHROMATOGRAPHY":{"CHROMATOGRAPHY_SUMMARY":"test_value"}}
#     assert output == ""
    

# def test_str_first_record_with_test():
#     """Test that when for_each, code, record_id, and override aren't present the first record that meets the test is used."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../str_first_record_with_test_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path_json.exists()
    
#     with open(output_path_json, "r") as f:
#         output_json = json.loads(f.read())
        
#     assert output_json == {"CHROMATOGRAPHY":{"CHROMATOGRAPHY_SUMMARY":"Targeted IC"}}
#     assert output == ""


# def test_str_record_id():
#     """Test that when for_each, code, and override aren't record_id is used."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../str_record_id_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path_json.exists()
    
#     with open(output_path_json, "r") as f:
#         output_json = json.loads(f.read())
        
#     assert output_json == {"CHROMATOGRAPHY":{"CHROMATOGRAPHY_SUMMARY":"Thermo Dionex ICS-5000+"}}
#     assert output == ""


# def test_str_first_record():
#     """Test that when for_each, code, record_id, and override aren't present the first record is used."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../str_first_record_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path_json.exists()
    
#     with open(output_path_json, "r") as f:
#         output_json = json.loads(f.read())
        
#     assert output_json == {"CHROMATOGRAPHY":{"CHROMATOGRAPHY_SUMMARY":"Before going into the IC-FTMS the frozen sample is reconstituted in water."}}
#     assert output == ""


# def test_str_for_each_with_test():
#     """Test that for_each with a test works as expected."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../str_for_each_with_test_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path_json.exists()
    
#     with open(output_path_json, "r") as f:
#         output_json = json.loads(f.read())
        
#     assert output_json == {"TREATMENT":{"TREATMENT_SUMMARY":"Mouse with allogenic bone marrow transplant. "+\
#                                                             "Fed with semi-liquid diet supplemented with fully labeled glucose for 24 hours before harvest. "+\
#                                                             "Mouse with no treatment. Fed with semi-liquid diet supplemented with fully labeled glucose for 24 hours before harvest. "+\
#                                                             "Mouse with syngenic bone marrow transplant. "+\
#                                                             "Fed with semi-liquid diet supplemented with fully labeled glucose for 24 hours before harvest."}}
#     assert output == ""


# def test_str_for_each():
#     """Test that for_each works as expected."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../str_for_each_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path_json.exists()
    
#     with open(output_path_json, "r") as f:
#         output_json = json.loads(f.read())
        
#     assert output_json == {"TREATMENT":{"TREATMENT_SUMMARY":"Time PointTreatment"}}
#     assert output == ""



# def test_str_code_wrong_value():
#     """Test that when a code tag returns the wrong type an error is printed."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../str_code_wrong_type_error.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert not output_path_json.exists()
            
#     assert output == 'Error: The code conversion tag to create the "TREATMENT_SUMMARY" record in the "TREATMENT" table did not return a string type value.\n'


# def test_str_no_field_error():
#     """Test that when a record does not have an indicated field an error is printed."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../str_no_field_error.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert not output_path_json.exists()
            
#     assert output == 'Error: The conversion tag to create the "CHROMATOGRAPHY_SUMMARY" record in the "CHROMATOGRAPHY" table matched a record in the input "protocol" table, "ICMS1", that did not contain the "asdf" field indicated by the tag.\n'


# def test_str_code_error():
#     """Test that when a code tag encouners an error during execution an error is printed."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../str_code_error.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert not output_path_json.exists()
            
#     assert 'Error: The code conversion tag to create the "TREATMENT_SUMMARY" record in the "TREATMENT" table encountered an error while executing.' in output
#     assert 'Traceback (most recent call last):' in output
#     assert "SyntaxError: '(' was never closed" in output


# def test_str_no_matching_table_records():
#     """Test that when there is no matching records an error is printed."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../str_no_matching_records.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert not output_path_json.exists()
    
#     assert 'Error: When creating the "TREATMENT_SUMMARY" conversion for the "TREATMENT" table,' in output
#     assert 'no records in the "factor" table matched the test value, "asdf", for the test field,' in output
#     assert '"type", indicated in the "test" field of the conversion. This could be from no' in output
#     assert 'records containing the test field or no records matching the test value for that field.' in output


# def test_str_no_matching_table_records_warning():
#     """Test that when there is no matching records and the tag is not required a warning is printed."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../str_no_matching_records_warning.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path_json.exists()
    
#     assert 'Warning: When creating the "TREATMENT_SUMMARY" conversion for the "TREATMENT" table,' in output
#     assert 'no records in the "factor" table matched the test value, "asdf", for the test field,' in output
#     assert '"type", indicated in the "test" field of the conversion. This could be from no' in output
#     assert 'records containing the test field or no records matching the test value for that field.' in output
        

# def test_str_no_table_records():
#     """Test that when there are no records an error is printed."""
    
#     test_file = "MS_base_input_truncated_no_factor_records.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../str_no_records.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert not output_path_json.exists()
    
#     assert 'Error: When creating the "TREATMENT_SUMMARY" conversion for the "TREATMENT" table, there were no records in the indicated "factor" table.' in output
    
    
# def test_str_no_sort_by_field():
#     """Test that when a record doesn't have the indicated field to sort by an error is printed."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../str_no_sort_by.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert not output_path_json.exists()
    
#     assert 'Error: The record, "Treatment", in the "factor" table does not have the field,' in output 
#     assert '\'asdf\', required by the "sort_by" field for the conversion,' in output
#     assert '"TREATMENT_SUMMARY", in the conversion table, "TREATMENT".' in output


# # matrix tags
# def test_matrix_base_case():
#     """Test that a simple matrix tag works as expceted."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../matrix_base_case.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path_json.exists()
    
#     with open(output_path_json, "r") as f:
#         output_json = json.loads(f.read())
        
#     assert output_json == {
#                           "TREATMENT": {
#                             "TREATMENT_SUMMARY": [
#                               {
#                                 "id": "Time Point",
#                                 "field": "time_point",
#                                 "GH_Spleen": "GH_Spleen"
#                               },
#                               {
#                                 "id": "Treatment",
#                                 "field": "protocol.id",
#                                 "GH_Spleen": "GH_Spleen"
#                               }
#                             ]
#                           }
#                         }
    
#     assert output == ""
    

# def test_matrix_collate():
#     """Test that collate field for matrix tag works as expceted."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../matrix_collate_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path_json.exists()
    
#     with open(output_path_json, "r") as f:
#         output_json = json.loads(f.read())
        
#     with open(pathlib.Path("matrix_collate_test_compare.json"), "r") as f:
#         output_compare_json = json.loads(f.read())
        
#     assert output_json == output_compare_json
    
#     assert output == ""
    

# def test_matrix_fields_to_headers():
#     """Test that fields_to_headers field for matrix tag works as expceted."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../matrix_fields_to_headers_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path_json.exists()
    
#     with open(output_path_json, "r") as f:
#         output_json = json.loads(f.read())
        
#     with open(pathlib.Path("matrix_fields_to_headers_test_compare.json"), "r") as f:
#         output_compare_json = json.loads(f.read())
        
#     assert output_json == output_compare_json
    
#     assert output == ""
    

# def test_matrix_fields_to_headers_exclusion():
#     """Test that exclusion_headers field for matrix tag works as expceted."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../matrix_fields_to_headers_exclusion_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path_json.exists()
    
#     with open(output_path_json, "r") as f:
#         output_json = json.loads(f.read())
        
#     with open(pathlib.Path("matrix_fields_to_headers_exclusion_test_compare.json"), "r") as f:
#         output_compare_json = json.loads(f.read())
        
#     assert output_json == output_compare_json
    
#     assert output == ""


# def test_matrix_values_to_str():
#     """Test that values_to_str field for matrix tag works as expceted."""
    
#     test_file = "NMR_base_input.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../matrix_values_to_str_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path_json.exists()
    
#     with open(output_path_json, "r") as f:
#         output_json = json.loads(f.read())
        
#     with open(pathlib.Path("matrix_values_to_str_test_compare.json"), "r") as f:
#         output_compare_json = json.loads(f.read())
        
#     assert output_json == output_compare_json
    
#     assert output == ""


# def test_matrix_code():
#     """Test that code field has precedence over other fields."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../matrix_code_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path_json.exists()
    
#     with open(output_path_json, "r") as f:
#         output_json = json.loads(f.read())
        
#     assert output_json == {"TREATMENT":{"TREATMENT_SUMMARY":[{}]}}
#     assert output == ""


# def test_matrix_code_error():
#     """Test that an error is printed when the code doesn't return a matrix type."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../matrix_code_error_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert not output_path_json.exists()
    
#     assert output == 'Error: The code conversion tag to create the "TREATMENT_SUMMARY" record in the "TREATMENT" table did not return a matrix type value.\n'


# def test_matrix_test():
#     """Test that test field works as expected."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../matrix_test_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path_json.exists()
    
#     with open(output_path_json, "r") as f:
#         output_json = json.loads(f.read())
        
#     assert output_json == {
#                           "TREATMENT": {
#                             "TREATMENT_SUMMARY": [
#                               {
#                                 "id": "Treatment",
#                                 "field": "protocol.id",
#                                 "GH_Spleen": "GH_Spleen"
#                               }
#                             ]
#                           }
#                         }
    
#     assert output == ""


# def test_optional_headers_test():
#     """Test that optional_headers field works as expected."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../matrix_optional_headers_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path_json.exists()
    
#     with open(output_path_json, "r") as f:
#         output_json = json.loads(f.read())
        
#     assert output_json == {
#                           "TREATMENT": {
#                             "TREATMENT_SUMMARY": [
#                               {
#                                 "id": "Time Point",
#                                 "field": "time_point",
#                                 "GH_Spleen": "GH_Spleen",
#                                 "study.id": "GH_Spleen"
#                               },
#                               {
#                                 "id": "Treatment",
#                                 "field": "protocol.id",
#                                 "GH_Spleen": "GH_Spleen",
#                                 "study.id": "GH_Spleen"
#                               }
#                             ]
#                           }
#                         }
    
#     assert output == ""
    

# def test_matrix_collate_error():
#     """Test that an error is printed when the collate field is not in a record."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../matrix_collate_error_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert not output_path_json.exists()
    
#     assert output == 'Error: The record, ' + \
#                       '"(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0-16_A0_Lung_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A", ' + \
#                       'in the "measurement" table does not have the field, "asdf", required by the ' + \
#                       '"collate" field for the conversion, "Data", in the conversion table, "MS_METABOLITE_DATA".\n'


# def test_matrix_header_no_inputkey_error():
#     """Test that an error is printed when there is a header that is not in a record."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../matrix_header_no_inputkey_error_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert not output_path_json.exists()
    
#     assert output == 'Error: The record, '+\
#                       '"(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0-16_A0_Lung_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A",'+\
#                       ' in the "measurement" table does not have the field, "asdf", required by the '+\
#                       '"headers" field for the conversion, "Data", in the conversion table, "MS_METABOLITE_DATA".\n'
                     
# def test_matrix_header_no_outputkey_error():
#     """Test that an error is printed when there is a header that is not in a record."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../matrix_header_no_outputkey_error_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert not output_path_json.exists()
    
#     assert output == 'Error: The record, '+\
#                       '"(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0-16_A0_Lung_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A",'+\
#                       ' in the "measurement" table does not have the field, "qwer", required by the '+\
#                       '"headers" field for the conversion, "Data", in the conversion table, "MS_METABOLITE_DATA".\n'


# def test_matrix_collate_collision_warning():
#     """Test that a warning is printed when a key in collated data is overwritten with a different value."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../matrix_collate_collision_warning.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path_json.exists()
    
#     assert output == 'Warning: When creating the "TREATMENT_SUMMARY" matrix for the ' +\
#            '"TREATMENT" table different values for the output key, "field", were found' +\
#            ' for the collate key "GH_Spleen". Only the last value will be used.\n'


# def test_default_tag():
#     """Test that default field works as expected."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../default_field_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path_json.exists()
    
#     with open(output_path_json, "r") as f:
#         output_json = json.loads(f.read())
        
#     assert output_json == {
#                           "TREATMENT": {
#                             "TREATMENT_SUMMARY": "qwer"
#                           }
#                         }
    
#     assert 'The conversion tag to create the "TREATMENT_SUMMARY" record in the ' +\
#            '"TREATMENT" table could not be created, and reverted to its given default value, "qwer".' in output


# def test_table_not_in_input_error():
#     """Test that an error is printed when a tag indicates a table that isn't in the input."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../table_not_in_input_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert not output_path_json.exists()
    
#     assert output == 'Error: The "table" field value, "asdf", for conversion, ' +\
#                      '"TREATMENT_SUMMARY", in conversion table, "TREATMENT", does ' +\
#                      'not exist in the input JSON.\n'


# def test_table_not_in_input_warning():
#     """Test that a warning is printed when a tag indicates a table that isn't in the input and the tag is not required."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../table_not_in_input_warning_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path_json.exists()
    
#     assert 'Warning: The "table" field value, "asdf", for conversion, ' +\
#            '"TREATMENT_SUMMARY", in conversion table, "TREATMENT", does ' +\
#            'not exist in the input JSON.' in output


# def test_wrong_conversion_type_warning():
#     """Test that a warning is printed when a conversion tag has an unknown type."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../wrong_conversion_type_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path_json.exists()
    
#     assert output == 'Warning: Unknown value_type for the conversion "TREATMENT_SUMMARY" in the "TREATMENT" table. It will be skipped.\n'


# def test_matrix_conversion_returns_none_error():
#     """Test that an error is printed when a matrix conversion tag returns None."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../matrix_conversion_returns_none_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert not output_path_json.exists()
    
#     assert output == 'Error: The conversion tag to create the "TREATMENT_SUMMARY" record in the "TREATMENT" table did not return a value.\n'
    

# def test_conversion_returns_none_warning():
#     """Test that a warning is printed when a conversion tag returns None and is not required."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../conversion_returns_none_warning_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path_json.exists()
    
#     assert output == 'Warning: The non-required conversion tag to create the "TREATMENT_SUMMARY" record in the "TREATMENT" table could not be created.\n'
    

# def test_code_import():
#     """Test that import field works as expected."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../code_import_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path_json.exists()
    
#     with open(output_path_json, "r") as f:
#         output_json = json.loads(f.read())
        
#     assert output_json == {
#                           "TREATMENT": {
#                             "TREATMENT_SUMMARY": [
#                               {}
#                             ]
#                           }
#                         }
    
#     assert output == ""
    

# def test_code_import_path_does_not_exist():
#     """Test that an error is printed when the import field path does not exist."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../code_import_error_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert not output_path_json.exists()
    
#     assert output == 'Error: The path given to import a Python file in the "import" ' +\
#                      'field of the conversion record "TREATMENT_SUMMARY" in the "TREATMENT" table does not exist.\n'


# def test_str_literal_field_test():
#     """Test that a literal field works as expected."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../str_literal_field_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path_json.exists()
    
#     with open(output_path_json, "r") as f:
#         output_json = json.loads(f.read())
        
#     assert output_json == {
#                           "CHROMATOGRAPHY": {
#                             "CHROMATOGRAPHY_SUMMARY": "asdf"
#                           }
#                         }
    
#     assert output == ""


# def test_str_conversion_returns_none_error():
#     """Test that an error is printed when a str conversion tag returns None."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../str_conversion_returns_none_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert not output_path_json.exists()
    
#     assert output == 'Error: The conversion tag to create the "TREATMENT_SUMMARY" record in the "TREATMENT" table did not return a value.\n'



## section tags
## test required field.



