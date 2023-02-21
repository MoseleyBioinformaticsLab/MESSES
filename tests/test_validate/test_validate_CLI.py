# -*- coding: utf-8 -*-
import pytest

import pathlib
import os
import time
import json
import subprocess
import platform



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


def test_json_command_cv_option_json():
    """Test that the --cv option applies cv checking with JSON cv."""
    
    test_file = "simplified_base_input_cv_error.json"
    
    command = "messes validate json ../" + test_file + " --cv ../controlled_vocabulary_base.json"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == "Error:  The entry ['measurement']['dUMP-13C0-29_C1-2_Lung_allogenic_7days_170427_UKy_GCH_rep2-polar-ICMS_A'] " +\
                      "is missing the required property 'concentration'." + "\n"


def test_json_command_cv_option_csv():
    """Test that the --cv option applies cv checking with csv cv."""
    
    test_file = "simplified_base_input_cv_error.json"
    
    command = "messes validate json ../" + test_file + " --cv ../controlled_vocabulary_base.csv --silent nuisance"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == "Error:  The entry ['measurement']['dUMP-13C0-29_C1-2_Lung_allogenic_7days_170427_UKy_GCH_rep2-polar-ICMS_A'] " +\
                      "is missing the required property 'concentration'." + "\n"
                     

def test_json_command_cv_option_xlsx():
    """Test that the --cv option applies cv checking with xlsx cv."""
    
    test_file = "simplified_base_input_cv_error.json"
    
    command = "messes validate json ../" + test_file + " --cv ../controlled_vocabulary_base.xlsx:Sheet1 --silent nuisance"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == "Error:  The entry ['measurement']['dUMP-13C0-29_C1-2_Lung_allogenic_7days_170427_UKy_GCH_rep2-polar-ICMS_A'] " +\
                      "is missing the required property 'concentration'." + "\n"


def test_json_command_cv_option_xlsx_default_sheet_name():
    """Test that the --cv option applies cv checking with xlsx cv where the sheet name is not specified."""
    
    test_file = "simplified_base_input_cv_error.json"
    
    command = "messes validate json ../" + test_file + " --cv ../controlled_vocabulary_base.xlsx --silent nuisance"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == "Error:  The entry ['measurement']['dUMP-13C0-29_C1-2_Lung_allogenic_7days_170427_UKy_GCH_rep2-polar-ICMS_A'] " +\
                      "is missing the required property 'concentration'." + "\n"
                     

def test_json_command_cv_option_stdin_csv():
    """Test that the --cv option applies cv checking with csv read from stdin."""
    
    test_file = "simplified_base_input_cv_error.json"
    
    if platform.system() == "Windows":
        command = "TYPE ..\\controlled_vocabulary_base.csv | messes validate json ../" + test_file + " --cv - --csv --silent nuisance"
    else:
        command = "cat ../controlled_vocabulary_base.csv | messes validate json ../" + test_file + " --cv - --csv --silent nuisance"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8", shell=True)
    output = subp.stderr
    
    assert output == "Error:  The entry ['measurement']['dUMP-13C0-29_C1-2_Lung_allogenic_7days_170427_UKy_GCH_rep2-polar-ICMS_A'] " +\
                      "is missing the required property 'concentration'." + "\n"


def test_json_command_cv_option_stdin_json():
    """Test that the --cv option applies cv checking with json read from stdin."""
    
    test_file = "simplified_base_input_cv_error.json"
    
    if platform.system() == "Windows":
        command = "TYPE ..\\controlled_vocabulary_base.json | messes validate json ../" + test_file + " --cv - --json --silent nuisance"
    else:
        command = "cat ../controlled_vocabulary_base.json | messes validate json ../" + test_file + " --cv - --json --silent nuisance"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8", shell=True)
    output = subp.stderr
    
    assert output == "Error:  The entry ['measurement']['dUMP-13C0-29_C1-2_Lung_allogenic_7days_170427_UKy_GCH_rep2-polar-ICMS_A'] " +\
                      "is missing the required property 'concentration'." + "\n"


def test_json_command_cv_option_stdin_wrong_type():
    """Test that an error is printed when the filetype is mismatched reading from stdin."""
    
    test_file = "simplified_base_input_cv_error.json"
    
    if platform.system() == "Windows":
        command = "TYPE ..\\controlled_vocabulary_base.json | messes validate json ../" + test_file + " --cv - --csv --silent nuisance"
    else:
        command = "cat ../controlled_vocabulary_base.json | messes validate json ../" + test_file + " --cv - --csv --silent nuisance"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8", shell=True)
    output = subp.stderr
    
    assert output == "Error:  A problem was encountered trying to read the controlled vocabulary from stdin. " +\
                      "Make sure the indicated file type is correct." + "\n"


def test_json_command_cv_option_stdin_wrong_type2():
    """Test that an error is printed when the filetype is mismatched reading from stdin."""
    
    test_file = "simplified_base_input_cv_error.json"
    
    if platform.system() == "Windows":
        command = "TYPE ..\\controlled_vocabulary_base.csv | messes validate json ../" + test_file + " --cv - --json --silent nuisance"
    else:
        command = "cat ../controlled_vocabulary_base.csv | messes validate json ../" + test_file + " --cv - --json --silent nuisance"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8", shell=True)
    output = subp.stderr
    
    assert output == "Error:  A problem was encountered trying to read the controlled vocabulary from stdin. " +\
                      "Make sure the indicated file type is correct." + "\n"


def test_json_command_cv_option_stdin_no_type_given():
    """Test that an error is printed when the filetype is not given when reading from stdin."""
    
    test_file = "simplified_base_input_cv_error.json"
    
    if platform.system() == "Windows":
        command = "TYPE ..\\controlled_vocabulary_base.csv | messes validate json ../" + test_file + " --cv - --silent nuisance"
    else:
        command = "cat ../controlled_vocabulary_base.csv | messes validate json ../" + test_file + " --cv - --silent nuisance"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8", shell=True)
    output = subp.stderr
    
    assert output == "Error:  When reading the controlled vocabulary from standard input you must specify that it is '--csv' or '--json'." + "\n"
    

def test_json_command_read_input_from_stdin():
    """Test that reading input JSON from stdin works."""
    
    if platform.system() == "Windows":
        command = "TYPE ..\\simplified_base_input.json | messes validate json -"
    else:
        command = "cat ../simplified_base_input.json | messes validate json -"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8", shell=True)
    output = subp.stderr
    
    assert output == ""


def test_json_command_read_additional_from_stdin():
    """Test that reading --additional from stdin works."""
    
    test_file = "simplified_base_input_base_error.json"
    
    if platform.system() == "Windows":
        command = "TYPE ..\\base_schema.json | messes validate json ../" + test_file + " --additional - --no_base_schema"
    else:
        command = "cat ../base_schema.json | messes validate json ../" + test_file + " --additional - --no_base_schema"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8", shell=True)
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




##############
## save-schema
##############

def test_save_schema_command_no_options():
    """Test that the save_schema commmand produces expected file with no options."""
    
    command = "messes validate save-schema output"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == ""
    
    with open(output_path_json, 'r') as jsonFile:
        output_schema = json.load(jsonFile)
    
    with open("base_schema.json", 'r') as jsonFile:
        base_schema = json.load(jsonFile)
        
    assert output_schema == base_schema


def test_save_schema_command_cv():
    """Test that the save_schema commmand produces expected file with cv option."""
    
    command = "messes validate save-schema output --cv ../controlled_vocabulary_base.json"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == ""
    
    with open(output_path_json, 'r') as jsonFile:
        output_schema = json.load(jsonFile)
    
    with open("base_schema_plus_cv.json", 'r') as jsonFile:
        base_schema = json.load(jsonFile)
        
    assert output_schema == base_schema
    

def test_save_schema_command_cv_and_input():
    """Test that the save_schema commmand produces expected file with cv option and input JSON."""
    
    command = "messes validate save-schema output.json --input ../simplified_base_input.json --cv ../controlled_vocabulary_base.json"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == ""
    
    with open(output_path_json, 'r') as jsonFile:
        output_schema = json.load(jsonFile)
    
    with open("base_schema_plus_cv_plus_input.json", 'r') as jsonFile:
        base_schema = json.load(jsonFile)
        
    assert output_schema == base_schema
    

def test_save_schema_command_cv_from_stdin_csv():
    """Test that the save_schema commmand produces expected file with cv option reading from stdin csv."""
    
    if platform.system() == "Windows":
        command = "TYPE ..\\controlled_vocabulary_base.csv | messes validate save-schema output --input ../simplified_base_input.json --cv - --csv --silent nuisance"
    else:
        command = "cat ../controlled_vocabulary_base.csv | messes validate save-schema output --input ../simplified_base_input.json --cv - --csv --silent nuisance"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8", shell=True)
    output = subp.stderr
    
    assert output == ""
    
    with open(output_path_json, 'r') as jsonFile:
        output_schema = json.load(jsonFile)
    
    with open("base_schema_plus_cv_plus_input2.json", 'r') as jsonFile:
        base_schema = json.load(jsonFile)
        
    assert output_schema == base_schema


def test_save_schema_command_cv_from_stdin_json():
    """Test that the save_schema commmand produces expected file with cv option reading from stdin json."""
    
    if platform.system() == "Windows":
        command = "TYPE ..\\controlled_vocabulary_base.json | messes validate save-schema output --input ../simplified_base_input.json --cv - --json --silent nuisance"
    else:
        command = "cat ../controlled_vocabulary_base.json | messes validate save-schema output --input ../simplified_base_input.json --cv - --json --silent nuisance"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8", shell=True)
    output = subp.stderr
    
    assert output == ""
    
    with open(output_path_json, 'r') as jsonFile:
        output_schema = json.load(jsonFile)
    
    with open("base_schema_plus_cv_plus_input.json", 'r') as jsonFile:
        base_schema = json.load(jsonFile)
        
    assert output_schema == base_schema
    

def test_save_schema_command_input_from_stdin():
    """Test that the save_schema commmand produces expected file with input option reading from stdin."""
    
    if platform.system() == "Windows":
        command = "TYPE ..\\simplified_base_input.json | messes validate save-schema output --input - --cv ../controlled_vocabulary_base.json"
    else:
        command = "cat ../simplified_base_input.json | messes validate save-schema output --input - --cv ../controlled_vocabulary_base.json"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8", shell=True)
    output = subp.stderr
    
    assert output == ""
    
    with open(output_path_json, 'r') as jsonFile:
        output_schema = json.load(jsonFile)
    
    with open("base_schema_plus_cv_plus_input.json", 'r') as jsonFile:
        base_schema = json.load(jsonFile)
        
    assert output_schema == base_schema
    

def test_save_schema_command_silent_nuisance():
    """Test that the --silent nuisance option silences nuisance warnings."""
    
    command = "messes validate save-schema output --input ../simplified_base_input.json --cv ../controlled_vocabulary_base.csv --silent nuisance"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == ""
    
    with open(output_path_json, 'r') as jsonFile:
        output_schema = json.load(jsonFile)
    
    with open("base_schema_plus_cv_plus_input2.json", 'r') as jsonFile:
        base_schema = json.load(jsonFile)
        
    assert output_schema == base_schema
    

def test_save_schema_command_silent_full():
    """Test that the --silent nuisance option silences nuisance warnings."""
    
    command = "messes validate save-schema output --input ../simplified_base_input_protocol_cv_warning.json --cv ../controlled_vocabulary_base.csv --silent full"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == ""
    
    with open(output_path_json, 'r') as jsonFile:
        output_schema = json.load(jsonFile)
    
    with open("base_schema_plus_cv_plus_input2.json", 'r') as jsonFile:
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
## cv
#############

def test_cv_command_no_errors():
    """Test the cv command."""
    
    test_file = "controlled_vocabulary_base.json"
    
    command = "messes validate cv ../" + test_file
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output == ""


def test_cv_command_read_from_stdin_csv():
    """Test the cv command can read from stdin."""
    
    if platform.system() == "Windows":
        command = "TYPE ..\\controlled_vocabulary_base.csv | messes validate cv - --csv --silent nuisance"
    else:
        command = "cat ../controlled_vocabulary_base.csv | messes validate cv - --csv --silent nuisance"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8", shell=True)
    output = subp.stderr
    
    assert output == ""


def test_cv_command_read_from_stdin_json():
    """Test the cv command can read from stdin."""
    
    if platform.system() == "Windows":
        command = "TYPE ..\\controlled_vocabulary_base.json | messes validate cv - --json"
    else:
        command = "cat ../controlled_vocabulary_base.json | messes validate cv - --json"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8", shell=True)
    output = subp.stderr
    
    assert output == ""
    

def test_cv_command_silent_full():
    """Test the cv command warnings are silenced with silent full."""
    
    command = "messes validate cv ../controlled_vocabulary_base.csv --csv --silent full"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8", shell=True)
    output = subp.stderr
    
    assert output == ""




