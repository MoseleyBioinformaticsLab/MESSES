# -*- coding: utf-8 -*-
import pytest

import pathlib
import os
import time
import json
import subprocess
import io

import pandas


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

output_path_csv = pathlib.Path("output.csv")
@pytest.fixture(autouse=True)
def delete_csv():                
    if output_path_csv.exists():
        os.remove(output_path_csv)
        time_to_wait=10
        time_counter = 0
        while output_path_csv.exists():
            time.sleep(1)
            time_counter += 1
            if time_counter > time_to_wait:
                raise FileExistsError(output_path_csv + " was not deleted within " + str(time_to_wait) + " seconds, so it is assumed that it won't be and something went wrong.")
                
output_path_xlsx = pathlib.Path("output.xlsx")
@pytest.fixture(autouse=True)
def delete_xlsx():                
    if output_path_xlsx.exists():
        os.remove(output_path_xlsx)
        time_to_wait=10
        time_counter = 0
        while output_path_xlsx.exists():
            time.sleep(1)
            time_counter += 1
            if time_counter > time_to_wait:
                raise FileExistsError(output_path_xlsx + " was not deleted within " + str(time_to_wait) + " seconds, so it is assumed that it won't be and something went wrong.")
                


#############
## json
#############

def test_json_command_no_options_no_errors():
    """Test the json command with no options, so only base schema validation on a file with no problems."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes validate json ../" + test_file + " --silent nuisance"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == ""
    

def test_json_command_no_options_base_errors():
    """Test that an error is printed when a base error occurs."""
    
    test_file = "simplified_base_input_base_error.json"
    
    command = "messes validate json ../" + test_file
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == "Error:  The entry ['factor']['Time Point'] is missing the required property 'allowed_values'." + "\n"


def test_json_command_no_base_schema():
    """Test the json command with --no_base_schema option."""
    
    test_file = "simplified_base_input_base_error.json"
    
    command = "messes validate json ../" + test_file + " --no_base_schema"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == ""
    

def test_json_command_no_options_extra_errors():
    """Test that an error is printed when an extra check error occurs."""
    
    test_file = "simplified_base_input_extra_error.json"
    
    command = "messes validate json ../" + test_file
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == 'Error:  In the measurement table of the input JSON, the record ' +\
                      '"dUMP-13C0-29_C1-2_Lung_allogenic_7days_170427_UKy_GCH_rep2-polar-ICMS_A" ' +\
                      'has a field, entity.id, that is an id to another table, entity, but that id,' +\
                      ' 29_C1-2_Lung_allogenic_7days_170427_UKy_GCH_rep2-polar-ICMS_, is not in the entity table.' + "\n"


def test_json_command_no_extra_checks():
    """Test the json command with --no_extra_checks option."""
    
    test_file = "simplified_base_input_extra_error.json"
    
    command = "messes validate json ../" + test_file + " --no_extra_checks"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == ""
    

def test_json_command_no_extra_checks_and_no_base_schema():
    """Test the json command with --no_extra_checks option and the --no_base_schema option."""
    
    test_file = "simplified_base_input_extra_and_base_error.json"
    
    command = "messes validate json ../" + test_file + " --no_extra_checks --no_base_schema"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == ""
    

def test_json_command_additional_schema_option():
    """Test that the same error as base_schema is printed when the base schema is given as an additional schema."""
    
    test_file = "simplified_base_input_base_error.json"
    
    command = "messes validate json ../" + test_file + " --additional ../base_schema.json"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == "Error:  The entry ['factor']['Time Point'] is missing the required property 'allowed_values'." + "\n" +\
                      "Error:  The entry ['factor']['Time Point'] is missing the required property 'allowed_values'." + "\n"


def test_json_command_additional_schema_option_no_base_schema():
    """Test that only one error is printed when the --no_base_schema options given and additional schema is base schema."""
    
    test_file = "simplified_base_input_base_error.json"
    
    command = "messes validate json ../" + test_file + " --additional ../base_schema.json --no_base_schema"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == "Error:  The entry ['factor']['Time Point'] is missing the required property 'allowed_values'." + "\n"


def test_json_command_pds_option_json():
    """Test that the --pds option applies pds checking with JSON pds."""
    
    test_file = "simplified_base_input_pds_error.json"
    
    command = "messes validate json ../" + test_file + " --pds ../PDS_base.json --silent nuisance"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == "Error:  The entry ['measurement']['dUMP-13C0-29_C1-2_Lung_allogenic_7days_170427_UKy_GCH_rep2-polar-ICMS_A'] " +\
                      "is missing the required property 'concentration'." + "\n"


def test_json_command_pds_option_csv():
    """Test that the --pds option applies pds checking with csv pds."""
    
    test_file = "simplified_base_input_pds_error.json"
    
    command = "messes validate json ../" + test_file + " --pds ../PDS_base.csv --silent nuisance"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == "Error:  The entry ['measurement']['dUMP-13C0-29_C1-2_Lung_allogenic_7days_170427_UKy_GCH_rep2-polar-ICMS_A'] " +\
                      "is missing the required property 'concentration'." + "\n"
                     

def test_json_command_pds_option_xlsx():
    """Test that the --pds option applies pds checking with xlsx pds."""
    
    test_file = "simplified_base_input_pds_error.json"
    
    command = "messes validate json ../" + test_file + " --pds ../PDS_base.xlsx:Sheet1 --silent nuisance"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == "Error:  The entry ['measurement']['dUMP-13C0-29_C1-2_Lung_allogenic_7days_170427_UKy_GCH_rep2-polar-ICMS_A'] " +\
                      "is missing the required property 'concentration'." + "\n"


def test_json_command_pds_option_xlsx_default_sheet_name():
    """Test that the --pds option applies pds checking with xlsx pds where the sheet name is not specified."""
    
    test_file = "simplified_base_input_pds_error.json"
    
    command = "messes validate json ../" + test_file + " --pds ../PDS_base.xlsx --silent nuisance"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == "Error:  The entry ['measurement']['dUMP-13C0-29_C1-2_Lung_allogenic_7days_170427_UKy_GCH_rep2-polar-ICMS_A'] " +\
                      "is missing the required property 'concentration'." + "\n"
                     

def test_json_command_pds_option_stdin_csv():
    """Test that the --pds option applies pds checking with csv read from stdin."""
    
    test_file = "simplified_base_input_pds_error.json"
    
    command = "messes validate json ../" + test_file + " --pds - --csv --silent nuisance"
    command = command.split(" ")
    with open("../PDS_base.csv") as file:
        subp = subprocess.run(command, stdin=file, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == "Error:  The entry ['measurement']['dUMP-13C0-29_C1-2_Lung_allogenic_7days_170427_UKy_GCH_rep2-polar-ICMS_A'] " +\
                      "is missing the required property 'concentration'." + "\n"


def test_json_command_pds_option_stdin_json():
    """Test that the --pds option applies pds checking with json read from stdin."""
    
    test_file = "simplified_base_input_pds_error.json"
    
    command = "messes validate json ../" + test_file + " --pds - --json --silent nuisance"
    command = command.split(" ")
    with open("../PDS_base.json") as file:
        subp = subprocess.run(command, stdin=file, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == "Error:  The entry ['measurement']['dUMP-13C0-29_C1-2_Lung_allogenic_7days_170427_UKy_GCH_rep2-polar-ICMS_A'] " +\
                      "is missing the required property 'concentration'." + "\n"


def test_json_command_pds_option_stdin_wrong_type():
    """Test that an error is printed when the filetype is mismatched reading from stdin."""
    
    test_file = "simplified_base_input_pds_error.json"
    
    command = "messes validate json ../" + test_file + " --pds - --csv --silent nuisance"
    command = command.split(" ")
    with open("../PDS_base.json") as file:
        subp = subprocess.run(command, stdin=file, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == "Error:  A problem was encountered when trying to read the protocol-dependent schema from stdin. " +\
                      "Make sure the indicated file type is correct." + "\n"


def test_json_command_pds_option_stdin_wrong_type2():
    """Test that an error is printed when the filetype is mismatched reading from stdin."""
    
    test_file = "simplified_base_input_pds_error.json"
    
    command = "messes validate json ../" + test_file + " --pds - --json --silent nuisance"
    command = command.split(" ")
    with open("../PDS_base.csv") as file:
        subp = subprocess.run(command, stdin=file, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == "Error:  A problem was encountered when trying to read the protocol-dependent schema from stdin. " +\
                      "Make sure the indicated file type is correct." + "\n"


def test_json_command_pds_option_stdin_no_type_given():
    """Test that an error is printed when the filetype is not given when reading from stdin."""
    
    test_file = "simplified_base_input_pds_error.json"
    
    command = "messes validate json ../" + test_file + " --pds - --silent nuisance"
    command = command.split(" ")
    with open("../PDS_base.csv") as file:
        subp = subprocess.run(command, stdin=file, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == "Error:  When reading the protocol-dependent schema from standard input you must specify that it is '--csv' or '--json'." + "\n"
    

def test_json_command_read_input_from_stdin():
    """Test that reading input JSON from stdin works."""
    
    command = "messes validate json -"
    command = command.split(" ")
    with open("../simplified_base_input.json") as file:
        subp = subprocess.run(command, stdin=file, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == ""


def test_json_command_read_additional_from_stdin():
    """Test that reading --additional from stdin works."""
    
    test_file = "simplified_base_input_base_error.json"
    
    command = "messes validate json ../" + test_file + " --additional - --no_base_schema"
    command = command.split(" ")
    with open("../base_schema.json") as file:
        subp = subprocess.run(command, stdin=file, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == "Error:  The entry ['factor']['Time Point'] is missing the required property 'allowed_values'." + "\n"


def test_json_command_silent_full():
    """Test that --silent full silences all warnings."""
    
    test_file = "simplified_base_input_warnings.json"
    
    command = "messes validate json ../" + test_file + " --silent full"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == ""
    
    
def test_json_command_silent_nuisance():
    """Test that --silent nuisance silences nuisance warnings."""
    
    test_file = "simplified_base_input_warnings.json"
    
    command = "messes validate json ../" + test_file + " --silent nuisance"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == "Warning:  The allowed value, naive, for the factor, Treatment, " +\
                      "in the factor table of the input JSON is not used by any of the entities.\n" +\
                      "Warning:  The allowed value, syngenic, for the factor, Treatment, " +\
                      "in the factor table of the input JSON is not used by any of the entities.\n" +\
                      "Warning:  The protocol, dummy, in the protocol table of the input JSON is " +\
                      "not used by any of the entities or measurements." + "\n"


def test_json_command_format_mwtab_MS():
    """Test that --format mwtab works."""
    
    test_file = "MS_base_input_truncated_mwtab_error.json"
    
    command = "messes validate json ../" + test_file + " --silent nuisance --format mwtab"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    errors = [
        "Error:  The entry ['protocol']['naive'] is missing the required property 'description'.",
        "Error:  The entry ['protocol']['IC-FTMS_preparation'] is missing the required property 'order'.",
        "Error:  The entry ['protocol']['frozen_tissue_grind'] is missing the required property 'order'.",
        "Error:  The entry ['protocol']['ICMS1'] is missing the required property 'column_name'.",
        "Error:  The entry ['protocol']['protein_extraction'] is missing the required property 'order'.",
        "Error:  The entry ['protocol']['tissue_quench'] is missing the required property 'order'.",
        "Error:  The entry ['protocol']['mouse_tissue_collection'] is missing the required property 'description'.",
        "Error:  The entry ['protocol']['polar_extraction'] is missing the required property 'description'.",
        "Error:  The entry ['protocol']['polar_extraction'] is missing the required property 'order'.",
        "Error:  The entry ['measurement']['(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0-16_A0_Lung_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A'] is missing the required property 'assignment'.",
        "Error:  The entry ['measurement']['(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0-16_A0_Lung_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A'] is missing the required property 'intensity'."
        ]
    for error in errors:
        assert error in output
        

def test_json_command_format_mwtab_extra_MS():
    """Test that --format mwtab works for the extra checks."""
    
    test_file = "MS_base_input_truncated_mwtab_extra_error.json"
    
    command = "messes validate json ../" + test_file + " --silent nuisance --format mwtab"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    errors = [
        'Error:  The first collection protocol, mouse_tissue_collection, does not have the required "sample_type" field for the mwtab conversion.',
        'Error:  No protocols have a "machine_type" field used to mark the protocol that contains the instrument information for the mwtab conversion.',
        'Error:  The first subject, 01_A0_naive_0days_UKy_GCH_rep1, does not have the following required fields for the mwtab conversion:',
        'species',
        'species_type',
        'taxonomy_id'
        ]
    for error in errors:
        assert error in output
        

def test_json_command_format_mwtab_extra_MS_2():
    """Test that --format mwtab works for the extra checks 2."""
    
    test_file = "MS_base_input_truncated_mwtab_extra_error_2.json"
    
    command = "messes validate json ../" + test_file + " --silent nuisance --format mwtab"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    errors = [
        'Error:  There are no "collection" type protocols. There must be at least one for the mwtab conversion.',
        'Error:  There are no "sample_prep" type protocols. There must be at least one for the mwtab conversion.',
        'Error:  There are no "treatment" type protocols. There must be at least one for the mwtab conversion.'
        ]
    for error in errors:
        assert error in output
        

def test_json_command_format_mwtab_NMR():
    """Test that --format mwtab works."""
    
    test_file = "NMR_base_input_mwtab_error.json"
    
    command = "messes validate json ../" + test_file + " --silent nuisance --format mwtab"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    errors = [
        "Error:  The entry ['measurement'][\"AXP-1'_1-16_A0_Lung_naive_0days_170427_UKy_GCH_rep1-polar-NMR_A-NMR2\"] " +\
        "is missing the required property 'intensity'."
        ]
    for error in errors:
        assert error in output
        

def test_json_command_format_mwtab_NMR_bin():
    """Test that --format mwtab works."""
    
    test_file = "NMR_binned_base_input_mwtab_error.json"
    
    command = "messes validate json ../" + test_file + " --silent nuisance --format mwtab"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == "Error:  The entry ['measurement']['224.71133001281973-976.6723646467382'] is missing the required property 'intensity'.\n"


def test_json_command_format_bad_format():
    """Test that an unknown format prints an error."""
    
    test_file = "NMR_binned_base_input_mwtab_error.json"
    
    command = "messes validate json ../" + test_file + " --silent nuisance --format asdf"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    from messes.validate.validate import supported_formats
    extra_message = '\n   '.join(['"' + supported_format + '"' for supported_format in supported_formats])
    
    assert "Error:  Unknown format, asdf." in output
    assert extra_message in output



#############
# save-schema
#############

def test_save_schema_command_no_options():
    """Test that the save_schema commmand produces expected file with no options."""
    
    command = "messes validate save-schema output"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == ""
    
    assert output_path_json.exists()
    
    with open(output_path_json, 'r') as jsonFile:
        output_schema = json.load(jsonFile)
    
    with open("base_schema.json", 'r') as jsonFile:
        base_schema = json.load(jsonFile)
        
    assert output_schema == base_schema


def test_save_schema_command_pds():
    """Test that the save_schema commmand produces expected file with pds option."""
    
    command = "messes validate save-schema output --pds ../PDS_base.json --silent nuisance"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == ""
    
    assert output_path_json.exists()
    
    with open(output_path_json, 'r') as jsonFile:
        output_schema = json.load(jsonFile)
    
    with open("base_schema_plus_pds.json", 'r') as jsonFile:
        base_schema = json.load(jsonFile)
        
    assert output_schema == base_schema
    

def test_save_schema_command_pds_and_input():
    """Test that the save_schema commmand produces expected file with pds option and input JSON."""
    
    command = "messes validate save-schema output.json --input ../simplified_base_input.json --pds ../PDS_base.json --silent nuisance"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == ""
    
    assert output_path_json.exists()
    
    with open(output_path_json, 'r') as jsonFile:
        output_schema = json.load(jsonFile)
    
    with open("base_schema_plus_pds_plus_input.json", 'r') as jsonFile:
        base_schema = json.load(jsonFile)
        
    assert output_schema == base_schema
    

def test_save_schema_command_pds_from_stdin_csv():
    """Test that the save_schema commmand produces expected file with pds option reading from stdin csv."""
    
    command = "messes validate save-schema output --input ../simplified_base_input.json --pds - --csv --silent nuisance"
    command = command.split(" ")
    with open("../PDS_base.csv") as file:
        subp = subprocess.run(command, stdin=file, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == ""
    
    assert output_path_json.exists()
    
    with open(output_path_json, 'r') as jsonFile:
        output_schema = json.load(jsonFile)
    
    with open("base_schema_plus_pds_plus_input2.json", 'r') as jsonFile:
        base_schema = json.load(jsonFile)
        
    assert output_schema == base_schema


def test_save_schema_command_pds_from_stdin_json():
    """Test that the save_schema commmand produces expected file with pds option reading from stdin json."""
    
    command = "messes validate save-schema output --input ../simplified_base_input.json --pds - --json --silent nuisance"
    command = command.split(" ")
    with open("../PDS_base.json") as file:
        subp = subprocess.run(command, stdin=file, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == ""
    
    assert output_path_json.exists()
    
    with open(output_path_json, 'r') as jsonFile:
        output_schema = json.load(jsonFile)
    
    with open("base_schema_plus_pds_plus_input.json", 'r') as jsonFile:
        base_schema = json.load(jsonFile)
        
    assert output_schema == base_schema
    

def test_save_schema_command_input_from_stdin():
    """Test that the save_schema commmand produces expected file with input option reading from stdin."""
    
    command = "messes validate save-schema output --input - --pds ../PDS_base.json --silent nuisance"
    command = command.split(" ")
    with open("../simplified_base_input.json") as file:
        subp = subprocess.run(command, stdin=file, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == ""
    
    assert output_path_json.exists()
    
    with open(output_path_json, 'r') as jsonFile:
        output_schema = json.load(jsonFile)
    
    with open("base_schema_plus_pds_plus_input.json", 'r') as jsonFile:
        base_schema = json.load(jsonFile)
        
    assert output_schema == base_schema
    

def test_save_schema_command_silent_nuisance():
    """Test that the --silent nuisance option silences nuisance warnings."""
    
    command = "messes validate save-schema output --input ../simplified_base_input.json --pds ../PDS_base.csv --silent nuisance"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == ""
    
    assert output_path_json.exists()
    
    with open(output_path_json, 'r') as jsonFile:
        output_schema = json.load(jsonFile)
    
    with open("base_schema_plus_pds_plus_input2.json", 'r') as jsonFile:
        base_schema = json.load(jsonFile)
        
    assert output_schema == base_schema
    

def test_save_schema_command_silent_full():
    """Test that the --silent nuisance option silences nuisance warnings."""
    
    command = "messes validate save-schema output --input ../simplified_base_input_protocol_pds_warning.json --pds ../PDS_base.csv --silent full"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == ""
    
    assert output_path_json.exists()
    
    with open(output_path_json, 'r') as jsonFile:
        output_schema = json.load(jsonFile)
    
    with open("base_schema_plus_pds_plus_input2.json", 'r') as jsonFile:
        base_schema = json.load(jsonFile)
        
    assert output_schema == base_schema


def test_save_schema_command_stdout():
    """Test that the save_schema commmand prints to stdout."""
    
    command = "messes validate save-schema -"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == ""
    
    output_schema = json.loads(subp.stdout)
    
    with open("base_schema.json", 'r') as jsonFile:
        base_schema = json.load(jsonFile)
        
    assert output_schema == base_schema


def test_save_schema_command_format_mwtab():
    """Test that the save_schema commmand produces expected file for the mwtab format."""
    
    command = "messes validate save-schema output --format mwtab --silent nuisance"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == ""
    
    assert output_path_json.exists()
    
    with open(output_path_json, 'r') as jsonFile:
        output_schema = json.load(jsonFile)
    
    with open("mwtab_schema.json", 'r') as jsonFile:
        base_schema = json.load(jsonFile)
        
    assert output_schema == base_schema
    


#############
## schema
#############

def test_schema_command_error():
    """Test that the schema commmand prints an error for bad schema."""
    
    command = "messes validate schema ../invalid_JSON_Schema.json"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert "'asdf' is not valid under any of the given schemas" in output
    
    assert subp.stdout != "No errors. This is a valid JSON schema.\n"
    

def test_schema_command_success():
    """Test that the schema commmand prints on no errors."""
    
    command = "messes validate schema base_schema.json"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == ""
    
    assert subp.stdout == "No errors. This is a valid JSON schema.\n"


#############
## pds
#############

def test_pds_command_no_errors():
    """Test the pds command."""
    
    test_file = "PDS_base.json"
    
    command = "messes validate pds ../" + test_file + " --silent nuisance"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == ""
    

def test_pds_command_save_option():
    """Test the pds command saves the JSON Schema when --save is given."""
    
    test_file = "PDS_base.json"
    
    command = "messes validate pds ../" + test_file + " --silent nuisance --save output"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == ""
    
    assert output_path_json.exists()
    
    with open(output_path_json, 'r') as jsonFile:
        output_schema = json.load(jsonFile)
    
    with open("PDS_JSON_Schema.json", 'r') as jsonFile:
        directives_schema = json.load(jsonFile)
        
    assert output_schema == directives_schema


def test_pds_command_read_from_stdin_csv():
    """Test the pds command can read from stdin."""
    
    command = "messes validate pds - --csv --silent nuisance"
    command = command.split(" ")
    with open("../PDS_base.csv") as file:
        subp = subprocess.run(command, stdin=file, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == ""


def test_pds_command_read_from_stdin_json():
    """Test the pds command can read from stdin."""
    
    command = "messes validate pds - --json --silent nuisance"
    command = command.split(" ")
    with open("../PDS_base.json") as file:
        subp = subprocess.run(command, stdin=file, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == ""
    

def test_pds_command_silent_full():
    """Test the pds command warnings are silenced with silent full."""
    
    command = "messes validate pds ../PDS_base.csv --csv --silent full"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == ""


#################
## pds-to-table
#################

def test_pds_to_table_command_csv():
    """Test the pds-to-table command works as expected for csv output."""
    
    command = "messes validate pds-to-table ../PDS_base.json output csv"
    command = command.split(" ")
    subprocess.run(command, capture_output=True, encoding="UTF-8")
    
    compare_df = pandas.read_csv("pds_to_table.csv", header=None)
    new_df = pandas.read_csv("output.csv", header=None)
    
    assert compare_df.equals(new_df)


def test_pds_to_table_command_xlsx():
    """Test the pds-to-table command works as expected for xlsx output."""
    
    command = "messes validate pds-to-table ../PDS_base.json output xlsx"
    command = command.split(" ")
    subprocess.run(command, capture_output=True, encoding="UTF-8")
    
    compare_df = pandas.read_excel("pds_to_table.xlsx", header=None)
    new_df = pandas.read_excel("output.xlsx", header=None)
    
    assert compare_df.equals(new_df)


def test_pds_to_table_command_stdout():
    """Test the pds-to-table command works as expected for stdout output."""
    
    command = "messes validate pds-to-table ../PDS_base.json -"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stdout
    
    compare_df = pandas.read_csv("pds_to_table.csv", header=None)
    new_df = pandas.read_csv(io.StringIO(output), header=None)
    
    assert compare_df.equals(new_df)


def test_pds_to_table_command_invalid_output_type():
    """Test the pds-to-table command prints an error when the output filetype is invalid."""
    
    command = "messes validate pds-to-table ../PDS_base.json output asdf"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert "Error:  Unknown output filetype." in output



#################
## pds-to-json
#################

def test_pds_to_json_command():
    """Test the pds-to-json command works as expected."""
    
    command = "messes validate pds-to-json ../PDS_base.csv output"
    command = command.split(" ")
    subprocess.run(command, capture_output=True, encoding="UTF-8")
    
    assert output_path_json.exists()
    
    with open(output_path_json, 'r') as jsonFile:
        output_schema = json.load(jsonFile)
    
    with open("pds_to_json.json", 'r') as jsonFile:
        directives_schema = json.load(jsonFile)
    
    assert output_schema == directives_schema


#################
## cd-to-json-schema
#################

def test_cd_to_json_schema_command():
    """Test the cd-to-json-schema command works as expected."""
    
    command = "messes validate cd-to-json-schema ../mwtab_ms_conversion_directives.json output"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == ""
    
    assert output_path_json.exists()
    
    with open(output_path_json, 'r') as jsonFile:
        output_schema = json.load(jsonFile)
    
    with open("MS_directives_schema.json", 'r') as jsonFile:
        directives_schema = json.load(jsonFile)
        
    assert output_schema == directives_schema
    

def test_cd_to_json_schema_command_invalid_directives():
    """Test the cd-to-json-schema command prints an error when the directives are invalid."""
    
    command = "messes validate cd-to-json-schema ../mwtab_ms_conversion_directives_error.json output"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert "Error:  The conversion directives are not valid, so a JSON schema could not be created." in output
    

