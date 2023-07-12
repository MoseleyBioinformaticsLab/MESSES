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
    

# def test_str_override_literal():
#     """Test that override field has precedence over other fields and works with literal value."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../str_override_literal_test.json" 
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
    

# def test_str_record_id_error():
#     """Test that when the indicated record_id is missing an error is printed."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../str_record_id_error_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert not output_path_json.exists()
    
#     assert output == 'Error: The "record_id" field value, "asdf", for conversion, ' +\
#                       '"CHROMATOGRAPHY_SUMMARY", in conversion table, "CHROMATOGRAPHY", ' +\
#                       'does not exist in the "protocol" table of the input JSON.' +'\n'


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


# def test_str_for_each_bool():
#     """Test that for_each works as expected when it is a bool."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../str_for_each_bool_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

#     assert output_path_json.exists()
    
#     with open(output_path_json, "r") as f:
#         output_json = json.loads(f.read())
        
#     assert output_json == {"TREATMENT":{"TREATMENT_SUMMARY":"Time PointTreatment"}}
#     assert output == ""


# def test_str_code_wrong_value():
#     """Test that when a code directive returns the wrong type an error is printed."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../str_code_wrong_type_error.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

#     assert not output_path_json.exists()
            
#     assert output == 'Error: The code conversion directive to create the "TREATMENT_SUMMARY" record in the "TREATMENT" table did not return a string type value.\n'


# def test_str_no_field_error():
#     """Test that when a record does not have an indicated field an error is printed."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../str_no_field_error.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

#     assert not output_path_json.exists()
            
#     assert output == 'Error: The conversion directive to create the "CHROMATOGRAPHY_SUMMARY" record in the "CHROMATOGRAPHY" table matched a record in the input "protocol" table, "ICMS1", that did not contain the "asdf" field indicated by the directive.\n'


# def test_str_code_error():
#     """Test that when a code directive encouners an error during execution an error is printed."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../str_code_error.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

#     assert not output_path_json.exists()
            
#     assert 'Error: The code conversion directive to create the "TREATMENT_SUMMARY" record in the "TREATMENT" table encountered an error while executing.' in output
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
#     assert 'no records in the "factor" table matched the test, "type=asdf",' in output
#     assert 'indicated in the "test" field of the conversion. This could be from no' in output
#     assert 'records containing the test field(s) or no records matching the test value(s) for those field(s).' in output


# def test_str_no_matching_table_records_warning():
#     """Test that when there is no matching records and the directive is not required a warning is printed."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../str_no_matching_records_warning.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

#     assert output_path_json.exists()
    
#     assert 'Warning: When creating the "TREATMENT_SUMMARY" conversion for the "TREATMENT" table,' in output
#     assert 'no records in the "factor" table matched the test, "type=asdf",' in output
#     assert 'indicated in the "test" field of the conversion. This could be from no' in output
#     assert 'records containing the test field(s) or no records matching the test value(s) for those field(s).' in output


# def test_str_no_matching_table_records_bool_warning():
#     """Test that when there is no matching records and the directive is not required a warning is printed, and that required field can be a bool."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../str_no_matching_records_bool_warning.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

#     assert output_path_json.exists()
        
#     assert 'Warning: When creating the "TREATMENT_SUMMARY" conversion for the "TREATMENT" table,' in output
#     assert 'no records in the "factor" table matched the test, "type=asdf",' in output
#     assert 'indicated in the "test" field of the conversion. This could be from no' in output
#     assert 'records containing the test field(s) or no records matching the test value(s) for those field(s).' in output
        

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
    
#     assert 'Error: The record, "Time Point", in the "factor" table does not have the field,' in output 
#     assert '\'asdf\', required by the "sort_by" field for the conversion,' in output
#     assert '"TREATMENT_SUMMARY", in the conversion table, "TREATMENT".' in output


# # matrix directives
# def test_matrix_base_case():
#     """Test that a simple matrix directive works as expceted."""
    
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
#                               },
#                               {
#                                 "id": "Treatment",
#                                 "field": "protocol.id",
#                               }
#                             ]
#                           }
#                         }
    
#     assert output == ""
    

# def test_matrix_collate():
#     """Test that collate field for matrix directive works as expceted."""
    
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
#     """Test that fields_to_headers field for matrix directive works as expceted."""
    
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
    

# def test_matrix_fields_to_headers_bool():
#     """Test that fields_to_headers field for matrix directive works as expceted if it is a bool."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../matrix_fields_to_headers_bool_test.json" 
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
#     """Test that exclusion_headers field for matrix directive works as expceted."""
    
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
#     """Test that values_to_str field for matrix directive works as expected."""
    
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


# def test_matrix_values_to_str_bool():
#     """Test that values_to_str field for matrix directive works as expceted when it is a bool."""
    
#     test_file = "NMR_base_input.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../matrix_values_to_str_bool_test.json" 
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
    
#     assert output == 'Error: The code conversion directive to create the "TREATMENT_SUMMARY" record in the "TREATMENT" table did not return a matrix type value.\n'


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
#                                 'allowed_values': ['0', '7', '42'],
#                                 "id": "Time Point",
#                                 "field": "time_point",
#                               },
#                               {
#                                 'allowed_values': ['naive', 'syngenic', 'allogenic'],
#                                 "id": "Treatment",
#                                 "field": "protocol.id",
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
#                       '"(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0-01_A0_Colon_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A", ' + \
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
#                       '"(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0-01_A0_Colon_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A",'+\
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
#                       '"(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0-01_A0_Colon_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A",'+\
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
    
#     assert 'Warning: When creating the "ENTITY_SUMMARY" matrix for the "ENTITY" ' +\
#             'table different values for the output key, "replicate", were found for the ' +\
#             'collate key "subject". Only the last value will be used.\n' in output


# def test_default_directive():
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
    
#     assert 'The conversion directive to create the "TREATMENT_SUMMARY" record in the ' +\
#             '"TREATMENT" table could not be created, and reverted to its given default value, "qwer".' in output


# def test_default_literal_directive():
#     """Test that default field works as expected when it is a literal value."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../default_field_literal_test.json" 
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
    
#     assert 'The conversion directive to create the "TREATMENT_SUMMARY" record in the ' +\
#             '"TREATMENT" table could not be created, and reverted to its given default value, "qwer".' in output


# def test_table_not_in_input_error():
#     """Test that an error is printed when a directive indicates a table that isn't in the input."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../table_not_in_input_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr
    
#     assert not output_path_json.exists()
    
#     assert output == 'Error: The "table" field value, "asdf", for conversion, ' +\
#                       '"TREATMENT_SUMMARY", in conversion table, "TREATMENT", does ' +\
#                       'not exist in the input JSON.\n'


# def test_table_not_in_input_warning():
#     """Test that a warning is printed when a directive indicates a table that isn't in the input and the directive is not required."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../table_not_in_input_warning_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr
    
#     assert output_path_json.exists()
    
#     assert 'Warning: The "table" field value, "asdf", for conversion, ' +\
#             '"TREATMENT_SUMMARY", in conversion table, "TREATMENT", does ' +\
#             'not exist in the input JSON.' in output


# def test_matrix_conversion_returns_none_error():
#     """Test that an error is printed when a matrix conversion directive returns None."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../matrix_conversion_returns_none_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr
    
#     assert not output_path_json.exists()
    
#     assert output == 'Error: The conversion directive to create the "TREATMENT_SUMMARY" record in the "TREATMENT" table did not return a value.\n'
    

# def test_conversion_returns_none_warning():
#     """Test that a warning is printed when a conversion directive returns None and is not required."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../conversion_returns_none_warning_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr
    
#     assert output_path_json.exists()
    
#     assert output == 'Warning: The non-required conversion directive to create the "TREATMENT_SUMMARY" record in the "TREATMENT" table could not be created.\n'
    

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
#                       'field of the conversion record "TREATMENT_SUMMARY" in the "TREATMENT" table does not exist.\n'


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
#     """Test that an error is printed when a str conversion directive returns None."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../str_conversion_returns_none_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr
    
#     assert not output_path_json.exists()
    
#     assert output == 'Error: The conversion directive to create the "TREATMENT_SUMMARY" record in the "TREATMENT" table did not return a value.\n'


# def test_silent_in_directive_works():
#     """Test that a warning is not printed when silent is true."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../conversion_returns_none_warning_silent_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr
    
#     assert output_path_json.exists()
#     ## Should output this, but it should be silenced.
#     #'Warning: The non-required conversion directive to create the "TREATMENT_SUMMARY" record in the "TREATMENT" table could not be created.\n'
#     assert output == ""


# def test_section_conversion_with_multiple_directives_error():
#     """Test that an error is printed when a conversion directive has a section type and additional directives in the same table."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../conversion_section_with_multiple_directives_error.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr
    
#     assert not output_path_json.exists()
    
#     assert output == 'ValidationError: In the conversion directives, the table, "TREATMENT", has multiple directives and one of them is a section type. Section type directives must be the only directive type in a table if it is present.\n'


# def test_str_that_calls_nested_directive_returning_none_is_not_concatenated():
#     """Test that a warning is printed when a str conversion directive calls a nested directive that returns None is not required."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../str_nested_directive_returns_none_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr
    
#     assert output_path_json.exists()
    
#     with open(output_path_json, "r") as f:
#         output_json = json.loads(f.read())
        
#     assert output_json == {"CHROMATOGRAPHY":{"CHROMATOGRAPHY_SUMMARY":"Before going into the IC-FTMS the frozen sample is reconstituted in water."}}
    
#     assert ('Warning: When executing the str directive, "CHROMATOGRAPHY_SUMMARY", in the conversion table, '
#             '"CHROMATOGRAPHY", a value in the "field" called the nested directive, "nested_directive%", and '
#             'a problem was encountered while executing the directive. Since the "required" field of the nested '
#             'directive is "False" the field will not be concatenated in the result created for the record, '
#             '"IC-FTMS_preparation", in the "protocol" table.') in output
    
#     assert ('Warning: The non-required conversion directive to create the "no_id_needed" '
#             'record in the "nested_directive%" table could not be created.') in output


# def test_str_that_calls_nested_directive_returning_none_is_not_concatenated_silent():
#     """Test that a warning is NOT printed when a str conversion directive calls a nested directive that returns None is not required and has silent=True."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../str_nested_directive_returns_none_silent_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr
    
#     assert output_path_json.exists()
    
#     assert output == ""


# def test_matrix_that_calls_nested_directive_returning_none_is_not_in_dict():
#     """Test that a warning is printed when a matrix conversion directive calls a nested directive that returns None is not required."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../matrix_nested_directive_returns_none_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr
    
#     assert output_path_json.exists()
    
#     with open(output_path_json, "r") as f:
#         output_json = json.loads(f.read())
        
#     assert output_json == {"CHROMATOGRAPHY":{"CHROMATOGRAPHY_SUMMARY":[{"desc":"Tissue is frozen in liquid nitrogen to stop metabolic processes."}]}}
    
#     assert ('Warning: When executing the matrix directive, "CHROMATOGRAPHY_SUMMARY", in the conversion table, '
#             '"CHROMATOGRAPHY", a header called the nested directive, "nested_directive%", and '
#             'a problem was encountered while executing the directive. Since the "required" field of the nested '
#             'directive is "False" the header will not be in the dictionary created for the record, '
#             '"tissue_quench", in the "protocol" table.') in output
    
#     assert ('Warning: The non-required conversion directive to create the "no_id_needed" '
#             'record in the "nested_directive%" table could not be created.') in output
    

# def test_matrix_that_calls_nested_directive_returning_none_is_not_in_dict_silent():
#     """Test that a warning is NOT printed when a matrix conversion directive calls a nested directive that returns None is not required and has silent=True."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../matrix_nested_directive_returns_none_silent_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr
    
#     assert output_path_json.exists()
    
#     assert output == ""


# def test_test_keyword_literal_field_test():
#     """Test that literal fields work as expected for the test keyword."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../test_keyword_literal_field_test.json" 
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


# def test_test_keyword_calling_field_for_non_nested_directive_error():
#     """Test that an error is printed when a directive indicates to use a field from a calling record, but is not a nested directive."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../test_keyword_calling_field_for_non_nested_directive_error.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr
    
#     assert not output_path_json.exists()
        
#     assert ('Error: When creating the "CHROMATOGRAPHY_SUMMARY" conversion for '
#             'the "CHROMATOGRAPHY" table, the value for "test", "machine_type=^.MS", '
#             'indicates to use a calling record\'s attribute value, but this conversion '
#             'directive is not a nested directive and therefore has no calling record.') in output


# def test_test_keyword_calling_field_works():
#     """Test that calling field works as expected for the test keyword."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../test_keyword_calling_field_works.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr
    
#     assert output_path_json.exists()
    
#     with open(output_path_json, "r") as f:
#         output_json = json.loads(f.read())
        
#     assert output_json == {
#                           "directive1": {
#                             "name1": "asdf"
#                           }
#                         }
    
#     assert output == ""


# def test_test_keyword_calling_field_not_in_record_error():
#     """Test that an error is printed when a directive indicates to use a field from a calling record, but that field is not in the record."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../test_keyword_calling_field_not_in_record_error.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr
    
#     assert not output_path_json.exists()
        
#     assert ('Error: When creating the "no_id_needed" conversion for the "directive2%" table, '
#             'the value for "test", "machine_type=^.asdf", indicates to use a calling record\'s '
#             'attribute value, but that attribute, "asdf", does not exist in the calling record, '
#             '"ICMS1", in the calling table, "protocol".') in output


# def test_nested_directive_not_in_directives_error():
#     """Test that an error is printed when a nested directive is called, but that directive is not in the directives."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../test_nested_directive_not_in_directives_error.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr
    
#     assert not output_path_json.exists()
        
#     assert ('Error: The conversion directive to create the "name1" record in the '
#             '"directive1" table tries to call a nested directive, directive3%, but '
#             'that directive is not in the conversion directives.') in output


# def test_section_execute_standalone():
#     """Test that the execute attribute for section directives works on its own."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../section_execute_standalone_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr
    
#     assert output_path_json.exists()
    
#     with open(output_path_json, "r") as f:
#         output_json = json.loads(f.read())
        
#     assert output_json == {
#                           "directive1": {
#                             "termSource": "source",
#                             "termAccession": "accession",
#                             "annotationValue": "value",
#                             "comments": [
#                               {
#                                 "value": "comment"
#                               }
#                             ]
#                           }
#                         }
    
#     assert output == ""


# def test_section_execute_nested():
#     """Test that the execute attribute for section directives works when nested."""
    
#     test_file = "MS_base_input_truncated.json"
    
#     command = "messes convert generic ../" + test_file  + " output ../section_execute_nested_test.json" 
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr
    
#     assert output_path_json.exists()
    
#     with open(output_path_json, "r") as f:
#         output_json = json.loads(f.read())
        
#     assert output_json == {
#                           "directive1": {
#                             "name1": [
#                               {
#                                 "asdf": {
#                                   "termSource": "source",
#                                   "termAccession": "accession",
#                                   "annotationValue": "value",
#                                   "comments": [
#                                     {
#                                       "value": "comment"
#                                     }
#                                   ]
#                                 }
#                               }
#                             ]
#                           }
#                         }
    
#     assert output == ""


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
















