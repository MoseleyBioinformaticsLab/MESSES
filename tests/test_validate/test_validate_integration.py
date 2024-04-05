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
    os.chdir(pathlib.Path("tests", "test_validate", "testing_files", "main_dir"))
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
                


def test_silent_unknown_level():
    """Test that if the silent option has an unknown value an error is printed."""
    
    test_file = "simplified_base_input.json"
    
    command = "messes validate json ../" + test_file + " --silent asdf"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == 'Error:  Unknown silent level, asdf. Must be one of "full", "nuisance", or "none".\n'


def test_integer_and_numeric_format_conversion():
    """Test that integer and numeric formats get type cast."""
    
    test_file = "simplified_base_input.json"
    
    command = "messes validate json ../" + test_file + " --pds ../PDS_base_format_conversion_check.json"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    errors = [
        "Error:  The value for " +\
        "['measurement']['dUMP-13C0-29_C1-2_Lung_allogenic_7days_170427_UKy_GCH_rep2-polar-ICMS_A']['concentration'] " +\
        "must be less than or equal to -1.",
        "Error:  The value for " +\
        "['measurement']['dUMP-13C0-29_C1-2_Lung_allogenic_7days_170427_UKy_GCH_rep2-polar-ICMS_A']['corrected_raw_intensity'] " +\
        "must be less than or equal to -1.",
        "Error:  The value for " +\
        "['measurement']['dUMP-13C0-30_C1-20_Lung_allogenic_7days_170427_UKy_GCH_rep3-polar-ICMS_A']['concentration'] " +\
        "must be less than or equal to -1.",
        "Error:  The value for " +\
        "['measurement']['dUMP-13C0-30_C1-20_Lung_allogenic_7days_170427_UKy_GCH_rep3-polar-ICMS_A']['corrected_raw_intensity'] " +\
        "must be less than or equal to -1."
        ]
    for error in errors:
        assert error in output


def test_str_integer_and_str_numeric_format_conversion():
    """Test that str_integer and str_numeric formats get type cast."""
    
    test_file = "simplified_base_input.json"
    
    command = "messes validate json ../" + test_file + " --pds ../PDS_base_format_conversion_check2.json"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    errors = [
        "Error:  The value for " +\
        "['measurement']['dUMP-13C0-29_C1-2_Lung_allogenic_7days_170427_UKy_GCH_rep2-polar-ICMS_A']['concentration'] " +\
        "must be less than or equal to -1.",
        "Error:  The value for " +\
        "['measurement']['dUMP-13C0-29_C1-2_Lung_allogenic_7days_170427_UKy_GCH_rep2-polar-ICMS_A']['corrected_raw_intensity'] " +\
        "must be less than or equal to -1.",
        "Error:  The value for " +\
        "['measurement']['dUMP-13C0-30_C1-20_Lung_allogenic_7days_170427_UKy_GCH_rep3-polar-ICMS_A']['concentration'] " +\
        "must be less than or equal to -1.",
        "Error:  The value for " +\
        "['measurement']['dUMP-13C0-30_C1-20_Lung_allogenic_7days_170427_UKy_GCH_rep3-polar-ICMS_A']['corrected_raw_intensity'] " +\
        "must be less than or equal to -1."
        ]
    for error in errors:
        assert error in output
        

def test_str_integer_and_str_numeric_format_type_check():
    """Test that str_integer and str_numeric formats check for string type."""
    
    test_file = "simplified_base_input_str_format_errors.json"
    
    command = "messes validate json ../" + test_file + " --pds ../PDS_base_format_conversion_check2.json"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    errors = [
        "Error:  The value for " +\
        "['measurement']['dUMP-13C0-29_C1-2_Lung_allogenic_7days_170427_UKy_GCH_rep2-polar-ICMS_A']['concentration'] " +\
        "is not of type \"string\".",
        "Error:  The value for " +\
        "['measurement']['dUMP-13C0-29_C1-2_Lung_allogenic_7days_170427_UKy_GCH_rep2-polar-ICMS_A']['corrected_raw_intensity'] " +\
        "is not of type \"string\".",
        "Error:  The value for " +\
        "['measurement']['dUMP-13C0-30_C1-20_Lung_allogenic_7days_170427_UKy_GCH_rep3-polar-ICMS_A']['concentration'] " +\
        "is not of type \"string\".",
        "Error:  The value for " +\
        "['measurement']['dUMP-13C0-30_C1-20_Lung_allogenic_7days_170427_UKy_GCH_rep3-polar-ICMS_A']['corrected_raw_intensity'] " +\
        "is not of type \"string\"."
        ]
    for error in errors:
        assert error in output


def test_pds_xlsx_no_sheet_found():
    """Test that xlsx files where sheet name can't be found or isn't given prints an error."""
    
    test_file = "simplified_base_input.json"
    
    command = "messes validate json ../" + test_file + " --pds ../PDS_base_bad_sheet_name.xlsx"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == "Error:  No sheet name was given for the file, so the default " +\
                      "name of #validate was used, but it was not found in the file." + "\n"
    
                      
def test_pds_Google_Sheets_no_sheet_found():
    """Test that Google Sheets files where sheet name can't be found or isn't given prints an error."""
    
    test_file = "simplified_base_input.json"
    
    command = "messes validate json ../" + test_file + " --pds https://docs.google.com/spreadsheets/d/1R_KXzdc2xyVzWYkQiF7XbvlMaJ3USFZGBqWpNojEd3k/edit#gid=1704460543"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == "Error:  No sheet name was given for the file, so the default " +\
                      "name of #validate was used, but it was not found in the file." + "\n"


def test_pds_xlsx_bad_sheet_name():
    """Test that xlsx files where user gives bad sheet name prints an error."""
    
    test_file = "simplified_base_input.json"
    
    command = "messes validate json ../" + test_file + " --pds ../PDS_base_bad_sheet_name.xlsx:Sheet1"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert "r'^Sheet1$' did not match any sheets in " in output
    assert 'PDS_base_bad_sheet_name.xlsx' in output


def test_pds_Google_Sheets_bad_sheet_name():
    """Test that Google Sheets files where user gives bad sheet name prints an error."""
    
    test_file = "simplified_base_input.json"
    
    command = "messes validate json ../" + test_file + " --pds https://docs.google.com/spreadsheets/d/1R_KXzdc2xyVzWYkQiF7XbvlMaJ3USFZGBqWpNojEd3k/edit#gid=1704460543:Sheet1"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert "r'^Sheet1$' did not match any sheets in " in output
    assert 'https://docs.google.com/spreadsheets/d/1R_KXzdc2xyVzWYkQiF7XbvlMaJ3USFZGBqWpNojEd3k/export?format=xlsx' in output


def test_pds_unknown_file_type():
    """Test that error is printed when there is an unknown filetype for pds."""
    
    test_file = "simplified_base_input.json"
    
    command = "messes validate json ../" + test_file + " --pds ../PDS_base_bad_sheet_name.asdf"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == "Error:  Unknown file type for the protocol-dependent schema file." + "\n"


def test_pds_invalid():
    """Test that error is printed when the pds is invalid."""
    
    test_file = "simplified_base_input.json"
    
    command = "messes validate json ../" + test_file + " --pds ../PDS_base_invalid.json"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    errors = [
        "Error:  The value for ['Chromatography_MS_measurement']['chromatography_description']['table'] " +\
        "is not one of ['protocol', 'entity', 'measurement'].",
        "Error:  The value for ['Chromatography_MS_measurement']['chromatography_description']['minLength'] " +\
        "is not a valid integer.",
        "Error:  The value for ['Chromatography_MS_measurement']['chromatography_description']['maximum'] " +\
        "is not a valid numeric.",
        "Error:  The provided protocol-dependent schema is not valid, so execution stops here."
        ]
    
    for error in errors:
        assert error in output


def test_file_path_doesnt_exist_json():
    """Test that error is printed when a json file doesn't exist."""
    
    test_file = "simplified_base_input_asdf.json"
    
    command = "messes validate json ../" + test_file + " --pds ../PDS_base.json"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert "Error:  The value entered for the input JSON," in output
    assert "is not a valid file path or does not exist." in output


def test_file_path_doesnt_exist_pds():
    """Test that error is printed when the pds file doesn't exist."""
    
    test_file = "simplified_base_input.json"
    
    command = "messes validate json ../" + test_file + " --pds ../PDS_base_asdf.json"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert "Error:  The value entered for the protocol-dependent schema," in output
    assert "is not a valid file path or does not exist." in output


def test_read_in_error_stdin_json():
    """Test that error is printed when a json file is read from stdin and encounters an error."""
    
    command = "messes validate json -"
    command = command.split(" ")
    with open("../bad_JSON_file.json") as file:
        subp = subprocess.run(command, stdin=file, capture_output=True, encoding="UTF-8")
    output = subp.stderr
        
    assert output == "Error:  An error was encountered when trying to read in the input JSON from standard input." + "\n"


def test_read_in_error_json():
    """Test that error is printed when a json file is read in and encounters an error."""
    
    test_file = "bad_JSON_file.json"
    
    command = "messes validate json ../" + test_file
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert "Error:  An error was encountered when trying to read in the input JSON, from the path" in output


def test_build_PDS_errors():
    """Test that errors are printed when adding protocols with problems to the PDS."""
    
    test_file = "simplified_base_input_protocol_problems.json"
    
    command = "messes validate json ../" + test_file + " --pds ../PDS_base.json"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    errors = [
        'Warning:  The protocol from the input JSON, ICMS1, does not have the same type ' +\
        'as its parent_protocol, IC-FTMS_measurement, in the protocol-dependent schema.',
        
        'Warning:  The protocol from the input JSON, allogenic, is not in the parent_protocol ' +\
        'table of the protocol-dependent schema, nor does it have a parent_protocol in the protocol-dependent ' +\
        'schema. Records with this protocol cannot have thier fields validated.',
        
        'Warning:  The protocol from the input JSON, zxcv, is not in the parent_protocol ' +\
        'table of the protocol-dependent schema, nor does it have a parent_protocol field. ' +\
        'Records with this protocol cannot have thier fields validated.'
        ]
    
    for error in errors:
        assert error in output


def test_boolean_keyword():
    """Test that boolean keywords in PDS get translated correctly when building schema."""
    
    test_file = "simplified_base_input_boolean_keyword.json"
    
    command = "messes validate json ../" + test_file + " --pds ../PDS_base_boolean_keyword.json --silent nuisance"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == "Error:  The value for ['protocol']['ICMS1']['array1'] has non-unique elements." + "\n"


def test_id_errors():
    """Test that errors are printed when id fields have errors."""
    
    test_file = "simplified_base_input_id_errors.json"
    
    command = "messes validate json ../" + test_file + " --silent nuisance"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    errors = [
        'Error:  The parent project, "asdf", for the project "GH_Spleen" in the "project" table ' +\
        'is not itself in the "project" table. Parent entities must be in the table as well.',
        
        'Error:  The protocol, "IC-FTMS_preparation", does not have the same type as its parent "ICMS1".',
        
        'Error:  The entity, "30_C1-20_Lung_allogenic_7days_170427_UKy_GCH_rep3", in the "entity" ' +\
        'table has a circular ancestry, i.e., somewhere in the lineage a entity has a "parent_id" to a child in the lineage.',
        
        'Error:  The entity, "30_C1-20_Lung_allogenic_7days_170427_UKy_GCH_rep3-polar-ICMS_A", in the ' +\
        '"entity" table has a circular ancestry, i.e., somewhere in the lineage a entity has a "parent_id" to a child in the lineage.',
        
        'Error:  The entity, "15_C1-20_allogenic_7days_UKy_GCH_rep3", in the "entity" table has a ' +\
        'circular ancestry, i.e., somewhere in the lineage a entity has a "parent_id" to a child in the lineage.',
        
        'Error:  In the project table of the input JSON, the record "GH_Spleen" has a field, asdf.id, ' +\
        'that is an id to another table, asdf, but that table is not in the input JSON.',
        
        'Error:  In the project table of the input JSON, the record "GH_Spleen" has a field, qwer.asdf, ' +\
        'with a period in the name, but it is not an id.',
        
        'Error:  In the project table of the input JSON, the record "GH_Spleen" has a field, entity.id, ' +\
        "that has id's to another table, entity, but at least one of the id's are not in the entity table.\n" +\
        "The id's are: \n" +\
        "asdf\n" +\
        "qwer",
        
        'Error:  In the project table of the input JSON, the record "GH_Spleen" has a field, measurement.id, ' +\
        'that is an id to another table, measurement, but that id, asdf, is not in the measurement table.',
        
        'Error:  In the project table of the input JSON, the record "GH_Spleen" has a parent_id, asdf, ' +\
        'but this parent is not in the project table.',
        
        'Error:  In the project table of the input JSON, the record "GH_Spleen" has an id, asdf, ' +\
        'but this is not the same as its own name.',
        
        'Error:  In the entity table of the input JSON, the subject type record "14_C1-2_allogenic_7days_UKy_GCH_rep2" ' +\
        'has a parent_id, 15_C1-20_allogenic_7days_UKy_GCH_rep3, but this parent is not a sample.'
        ]
    
    for error in errors:
        assert error in output


def test_parent_id_errors():
    """Test that errors are printed when parent_id fields have errors."""
    
    test_file = "simplified_base_input_parent_id_errors.json"
    
    command = "messes validate json ../" + test_file + " --silent nuisance"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    errors = [
        'Error:  The protocol, "IC-FTMS_preparation", in the "protocol" table has itself ' +\
        'listed in its parent_id. Records cannot be their own parents.',
        
        'Error:  The protocol, "ICMS1", does not have the same type as its parent "IC-FTMS_preparation".',
        
        'Error:  The parent protocol, "asdf", for the protocol "allogenic" in the "protocol" ' +\
        'table is not itself in the "protocol" table. Parent entities must be in the table as well.'
        ]
    
    for error in errors:
        assert error in output


def test_no_protocol_table():
    """Test that subject sample protocol check is skipped."""
    
    test_file = "simplified_base_input_no_protocol_table.json"
    
    command = "messes validate json ../" + test_file + " --silent nuisance"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert 'Error:  Sample 30_C1-20_Lung_allogenic_7days_170427_UKy_GCH_rep3-polar-ICMS_A' + \
            " came from a sample, but does not have a sample_prep protocol." not in output
    assert 'Error:  Measurement dUMP-13C0-29_C1-2_Lung_allogenic_7days_170427_UKy_GCH_rep2-polar-ICMS_A ' +\
            'does not have a measurement type protocol.' not in output


def test_SS_protocol_errors():
    """Test that errors are printed when entities don't have appropriate protocols."""
    
    test_file = "simplified_base_input_SS_protocol_errors.json"
    
    command = "messes validate json ../" + test_file + " --silent nuisance"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    errors = [
        'Error:  Sample 29_C1-2_Lung_allogenic_7days_170427_UKy_GCH_rep2 came from a subject, ' +\
        'but does not have a collection protocol.',
        
        'Error:  Sample 30_C1-20_Lung_allogenic_7days_170427_UKy_GCH_rep3-polar-ICMS_A came from ' +\
        'a sample, but does not have a sample_prep protocol.',
        
        'Error:  Subject 15_C1-20_allogenic_7days_UKy_GCH_rep3 does not have a treatment type protocol.'
        ]
    
    for error in errors:
        assert error in output


def test_measurement_protocol_error():
    """Test that an error is printed when a measurement doesn't have a measurement type protocol."""
    
    test_file = "simplified_base_input_measurement_bad_protocol.json"
    
    command = "messes validate json ../" + test_file + " --silent nuisance"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == "Error:  Measurement " +\
                      "dUMP-13C0-29_C1-2_Lung_allogenic_7days_170427_UKy_GCH_rep2-polar-ICMS_A " +\
                      "does not have a measurement type protocol." + "\n"


def test_protocol_same_description_warning():
    """Test that a warning is printed when 2 protocols have the same descscription."""
    
    test_file = "simplified_base_input_protocol_same_descriptions.json"
    
    command = "messes validate json ../" + test_file + " --silent nuisance"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == "Warning: The protocols: \n\n" +\
                      "IC-FTMS_preparation\n" +\
                      "allogenic\n\n" +\
                      "have the exact same descriptions." + "\n"


def test_no_factor_table():
    """Test that a warning is printed when 2 protocols have the same descscription."""
    
    test_file = "simplified_base_input_no_factors_table.json"
    
    command = "messes validate json ../" + test_file
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert "Warning:  The factor, Time Point, was not used by any of the entities." not in output


def test_factor_errors():
    """Test that errors are printed when entities don't have appropriate factors."""
    
    test_file = "simplified_base_input_factor_errors.json"
    
    command = "messes validate json ../" + test_file
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    errors = [        
        'Warning:  The entity, 29_C1-2_Lung_allogenic_7days_170427_UKy_GCH_rep2, ' +\
        'has no values in the field, protocol.id, that are in the allowed values of the factor, Treatment.',
        
        'Warning:  The entity, 29_C1-2_Lung_allogenic_7days_170427_UKy_GCH_rep2-polar-ICMS_A, ' +\
        'has a value, polar_extraction, in the field, protocol.id, that is not in the allowed values of the factor, Treatment.',
        
        'Warning:  The entity, 30_C1-20_Lung_allogenic_7days_170427_UKy_GCH_rep3-polar-ICMS_A, ' +\
        'has a field, protocol.id, that is a field for the factor, Treatment, but it is not a string or list type.',
        
        'Error:  The entity, 15_C1-20_allogenic_7days_UKy_GCH_rep3, has more than 1 value ' +\
        'in the field, protocol.id, that is in the allowed values of the factor, Treatment. ' +\
        'Entities can only have 1 value from each factor.',
        
        'Warning:  The allowed value, naive, for the factor, Treatment, in the factor table ' +\
        'of the input JSON is not used by any of the entities.',
        
        'Warning:  The allowed value, syngenic, for the factor, Treatment, in the factor ' +\
        'table of the input JSON is not used by any of the entities.',
        
        'Warning:  The factor, Time Point, was not used by any of the entities.'
        ]
    
    for error in errors:
        assert error in output


def test_additional_schema_invalid():
    """Test that an error is printed when the additional JSON schema is invalid."""
    
    test_file = "simplified_base_input.json"
    
    command = "messes validate json ../" + test_file + " --additional ../invalid_JSON_Schema.json"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert "Error:  The additional JSON schema, ../invalid_JSON_Schema.json, is not valid, so execution stops here." in output







