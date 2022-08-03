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
    os.chdir(pathlib.Path("tests", "testing_files", "main_dir"))
    yield
    os.chdir(cwd)
    
output_path = pathlib.Path("output.json")
@pytest.fixture(autouse=True)
def delete_metadata():
    # yield
    if output_path.exists():
        os.remove(output_path)
        time_to_wait=10
        time_counter = 0
        while output_path.exists():
            time.sleep(1)
            time_counter += 1
            if time_counter > time_to_wait:
                raise FileExistsError(output_path + " was not deleted within " + str(time_to_wait) + " seconds, so it is assumed that it won't be and something went wrong.")
                
output_compare_path = pathlib.Path("output_compare.json")




# def test_conversion_id_change():
#     """Test that a warning is printed when the conversion changes 2 or more records to the same id."""
    
#     test_file = "conversion_error.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file +" --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr
    
#     assert output_path.exists()
    
#     assert output == "Warning: A conversion directive has set at least 2 records in the \"measurement\" table to the same id. The output will have less records than expected." + "\n"
    
# def test_multiple_inserts():
#     """Test that #insert in a #tags block is inserted multiple times when #multiple=true."""
    
#     test_file = "multiple_inserts.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix() + " --save-export csv"
#     os.system(command)
    
#     assert output_path.exists()
#     test_file = pathlib.Path(test_file)
#     test_file_export = pathlib.Path(test_file.stem + "_export.csv")
#     assert test_file_export.exists()
    
#     export = pandas.read_csv(test_file_export, header=None)
#     ## There should be 4 #tags in column 0.
#     assert export.iloc[:,0].value_counts()["#tags"] == 4
    
#     if test_file_export.exists():
#         os.remove(test_file_export)
#         time_to_wait=10
#         time_counter = 0
#         while test_file_export.exists():
#             time.sleep(1)
#             time_counter += 1
#             if time_counter > time_to_wait:
#                 raise FileExistsError(test_file_export + " was not deleted within " + str(time_to_wait) + " seconds, so it is assumed that it won't be and something went wrong.")

        
    
# def test_multiple_insert_blocks():
#     """Test that all #insert blocks are added in the export."""
    
#     test_file = "multiple_insert_blocks.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix() + " --save-export csv"
#     os.system(command)
    
#     assert output_path.exists()
#     test_file = pathlib.Path(test_file)
#     test_file_export = pathlib.Path(test_file.stem + "_export.csv")
#     assert test_file_export.exists()
    
#     export = pandas.read_csv(test_file_export, header=None)
#     ## There should be 5 #tags in column 0.
#     assert export.iloc[:,0].value_counts()["#tags"] == 5
    
#     if test_file_export.exists():
#         os.remove(test_file_export)
#         time_to_wait=10
#         time_counter = 0
#         while test_file_export.exists():
#             time.sleep(1)
#             time_counter += 1
#             if time_counter > time_to_wait:
#                 raise FileExistsError(test_file_export + " was not deleted within " + str(time_to_wait) + " seconds, so it is assumed that it won't be and something went wrong.")

    


# def test_duplicate_headers():
#     """Test that a warning is printed when there are duplicate headers. Ex: id and compound both set to the same column."""
    
#     test_file = "duplicate_headers.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file +" --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     assert output == "\'Warning: duplicate header description provided in tagging directive at cell \"../duplicate_headers.xlsx:#tagging[:11]\"\'" + "\n"



# def test_missing_id_in_header():
#     """Test that a warning is printed when there is not an id tag in the header."""
    
#     test_file = "no_id_tag.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file +" --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     assert output == "Warning: The header row at index 1 in the compiled export sheet does not have an \"id\" tag, so it will not be in the JSON output." + "\n"




# def test_child_without_parent_id():
#     """Test that an error is printed when there is a child without a parent id."""
    
#     test_file = "child_tag_no_parent_id.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file +" --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr
    
#     assert subp.returncode == 1
#     assert re.match(r".*'no id field in parent record at cell \"\.\./child_tag_no_parent_id\.xlsx:#export\[C0\]\"'.*", output, re.DOTALL)
    
    
    
# def test_unused_conversion():
#     """Test that a warning is printed when there is an unused conversion."""
    
#     test_file = "unused_conversion.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file +" --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     assert output == "Warning: conversion directive #measurement.compound.exact.asdf never matched." + "\n"



# def test_unused_tag():
#     """Test that a warning is printed when there is an unused tag."""
    
#     test_file = "unused_tag.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file +" --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     assert output == "Warning: Tagging directive number 1 was never used." + "\n"
    
    
    
# def test_no_required_headers():
#     """Test that nothing is printed when no headers are required."""
    
#     test_file = "no_required_headers.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file +" --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     with open(output_path, "r") as f:
#         output_json = json.loads(f.read())
        
#     with open(output_compare_path, "r") as f:
#         output_compare_json = json.loads(f.read())
        
#     assert output_json == output_compare_json
    
#     assert output == ""



# def test_duplicate_columns():
#     """Test that a warning is printed when there are duplicate columns."""
    
#     test_file = "duplicate_columns.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file +" --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     assert output == "Warning: The header, Intensity, in tagging group, 1, was matched to more than 1 column near or on row, 3, in the tagged export.\nWarning: Tagging directive number 1 was never used." + "\n"



def test_exclusion():
    """Test that exclusion tag works."""
    
    test_file = "exclusion_test.xlsx"
    
    command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file +" --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    with open(output_compare_path, "r") as f:
        output_compare_json = json.loads(f.read())
        
    del output_compare_json["measurement"]
        
    assert output_json == output_compare_json
    
    assert output == "Warning: Tagging directive number 1 was never used." + "\n"



## Test --end-convert with 2 metadata sources.


## Test list fields

## Test attributes








