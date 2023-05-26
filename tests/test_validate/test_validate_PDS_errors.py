# -*- coding: utf-8 -*-
import pytest

import pathlib
import os
import time
import subprocess



@pytest.fixture(scope="module", autouse=True)
def change_cwd():
    cwd = pathlib.Path.cwd()
    os.chdir(pathlib.Path("tests", "test_validate", "testing_files", "bad_PDSs"))
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
  




def test_no_parent_protocol_table():
    """Test that error is printed when there is no parent_protocol table in the PDS."""
    
    command = "messes validate pds PDS_base_no_parent_table.json"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert "Error:  The required property 'parent_protocol' is missing." in output


def test_parent_protocol_table_errors():
    """Test that error is printed for various problems in the parent_protocol table."""
    
    command = "messes validate pds PDS_base_parent_protocol_errors.json"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    errors = [
        'Error:  The protocol, "Chromatography_MS_measurement", in the "parent_protocol" ' +\
        'table has a circular ancestry, i.e., somewhere in the lineage a protocol has a ' +\
        '"parent_id" to a child in the lineage.',

        'Error:  The protocol, "Chromatography_MS_measurement", in the "parent_protocol" ' +\
        'table has itself listed for its parent_id. Protocols cannot be their own parents.',
        
        'Warning:  The protocol, "qwer"," in the "parent_protocol" table does not itself ' +\
        'have any fields to validate, nor do any of its ancestors.',

        'Error:  The parent protocol, "asdf", for the protocol "qwer" in the "parent_protocol" ' +\
        'table is not itself in the "parent_protocol" table. Parent entities must be in the table as well.',

        'Warning:  The parent protocol, "asdf", for the protocol "qwer" in the "parent_protocol" ' +\
        'table is not itself in the protocol-dependent schema. Parent entities must be in the protocol-dependent schema as well.',

        'Warning:  The protocol, "qwer" in the "parent_protocol" table is not in the protocol-dependent schema.',

        'Error:  The protocol, "GCMS_measurement", in the "parent_protocol" table has a circular ' +\
        'ancestry, i.e., somewhere in the lineage a protocol has a "parent_id" to a child in the lineage.',

        'Error:  The protocol, "IC-FTMS_measurement", in the "parent_protocol" table has a circular ' +\
        'ancestry, i.e., somewhere in the lineage a protocol has a "parent_id" to a child in the lineage.',

        'Error:  The protocol, "MS_measurement", in the "parent_protocol" table has a circular ' +\
        'ancestry, i.e., somewhere in the lineage a protocol has a "parent_id" to a child in the lineage.',

        "Error:  The value for ['parent_protocol']['Chromatography_MS_measurement']['type'] " +\
        "is not one of ['sample_prep', 'treatment', 'collection', 'storage', 'measurement'].",
        
        "Error:  The value for ['Chromatography_MS_measurement']['chromatography_description']['minLength'] " +\
        "is not a valid integer.",
        
        'Error:  The protocol, "GCMS_measurement", does not have the same type as its parent "MS_measurement".'
        ]
    
    for error in errors:
        assert error in output


def test_invalid_schema():
    """Test that error is printed when the schema built from PDS is invalid."""
    
    command = "messes validate pds PDS_base_bad_type.json"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert "Warning:  The schema created from the protocol-dependent schema is not valid." in output


def test_invalid_schema_save_schema():
    """Test that error is printed when the schema built from PDS is invalid for save-schema command."""
    
    command = "messes validate save-schema output --pds PDS_base_bad_type.json"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert "Warning:  The schema created from the protocol-dependent schema is not valid." in output


def test_invalid_schema_json():
    """Test that error is printed when the schema built from pds is invalid for json command."""
    
    command = "messes validate json ../simplified_base_input.json --pds PDS_base_bad_type.json"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert "Error:  The schema created from the protocol-dependent schema is not valid. " +\
          "Please look at the errors and fix them to validate the input JSON. " +\
          "The save-schema command can be used to save the created schema." in output










