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



# def test_tagging_empty_tag_rows():
#     """Test that a #tags row directly after a #tags row doesn't affect the output."""
    
#     test_file = "tagging_empty_tag_rows.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     with open(output_path, "r") as f:
#         output_json = json.loads(f.read())
        
#     with open(pathlib.Path("output_compare.json"), "r") as f:
#         output_compare_json = json.loads(f.read())
        
#     assert output_json == output_compare_json
    
#     assert output == ""
    
    

# def test_tagging_missing_header_tag_error():
#     """Test that an error is printed when the #header tag is missing."""
    
#     test_file = "tagging_missing_header_tag_error.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert not output_path.exists()
    
#     assert 'Missing #header tag at cell' in output
#     assert "tagging_missing_header_tag_error.xlsx:#tagging[:8]" in output
    
    
# def test_tagging_missing_add_tag_error():
#     """Test that an error is printed when the #tag.add tag is missing."""
    
#     test_file = "tagging_missing_add_tag_error.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert not output_path.exists()
    
#     assert 'Missing #tag.add tag at cell' in output
#     assert "tagging_missing_add_tag_error.xlsx:#tagging[:8]" in output




# def test_tagging_ignore_test():
#     """Test that a #ignore row doesn't affect the output."""
    
#     test_file = "tagging_ignore_test.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     with open(output_path, "r") as f:
#         output_json = json.loads(f.read())
        
#     with open(pathlib.Path("output_compare.json"), "r") as f:
#         output_compare_json = json.loads(f.read())
        
#     assert output_json == output_compare_json
    
#     assert output == ""
    
    
    
# def test_tagging_insert_multiple_false_test():
#     """Test that a #multiple=false is the same as default."""
    
#     test_file = "tagging_insert_multiple_false_test.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     with open(output_path, "r") as f:
#         output_json = json.loads(f.read())
        
#     with open(pathlib.Path("output_compare.json"), "r") as f:
#         output_compare_json = json.loads(f.read())
        
#     assert output_json == output_compare_json
    
#     assert output == ""
    
    
    
def test_tagging_missing_end_tag_error():
    """Test that an error is printed when the #end tag is missing."""
    
    test_file = "tagging_missing_end_tag_error.xlsx"
    
    command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
    
    assert 'Missing #end tag at cell' in output
    assert "tagging_missing_end_tag_error.xlsx:#tagging[Q21]" in output









