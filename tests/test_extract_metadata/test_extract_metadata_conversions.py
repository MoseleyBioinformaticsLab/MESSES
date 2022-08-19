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




# def test_conversion_delete():
#     """Test that conversion delete works."""
    
#     test_file = "conversion_delete_test.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     with open(output_path, "r") as f:
#         output_json = json.loads(f.read())
        
        
#     assert not "formula" in output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]
#     assert not "formula" in output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]

#     assert output == ""



# def test_conversion_delete_before_value():
#     """Test that an error is printed when the delete tag appears before the value tag in conversion."""
    
#     test_file = "conversion_delete_before_value.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert not output_path.exists()        
                   
#     assert "#table_name.field_name.delete in column before #table_name.field_name.value at cell" in output
#     assert "conversion_delete_before_value.xlsx:#convert[B1]" in output



# def test_conversion_delete_table_name_mismatch():
#     """Test that an error is printed when there is a mismatch between the delete tag table and vale tag table in conversion."""
    
#     test_file = "conversion_delete_table_name_mismatch.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert not output_path.exists()        
                   
#     assert "Table name does not match between #table_name.field_name.value and #table_name.field_name.delete conversion tags at cell" in output
#     assert "conversion_delete_table_name_mismatch.xlsx:#convert[C1]" in output



# def test_conversion_rename():
#     """Test that conversion rename works."""
    
#     test_file = "conversion_rename_test.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     with open(output_path, "r") as f:
#         output_json = json.loads(f.read())
        
        
#     assert not "formula" in output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]
#     assert not "formula" in output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]
#     assert "molecular_formula" in output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]
#     assert "molecular_formula" in output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]

#     assert output == ""



# def test_conversion_rename_before_value():
#     """Test that an error is printed when the rename tag appears before the value tag in conversion."""
    
#     test_file = "conversion_rename_before_value.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert not output_path.exists()        
                   
#     assert "#table_name.field_name.rename in column before #table_name.field_name.value at cell" in output
#     assert "conversion_rename_before_value.xlsx:#convert[B1]" in output
    
    
    
# def test_conversion_rename_table_name_mismatch():
#     """Test that an error is printed when there is a mismatch between the rename tag table and vale tag table in conversion."""
    
#     test_file = "conversion_rename_table_name_mismatch.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert not output_path.exists()        
                   
#     assert "Table name does not match between #table_name.field_name.value and #table_name.field_name.rename conversion tags at cell" in output
#     assert "conversion_rename_table_name_mismatch.xlsx:#convert[C1]" in output
    
    
    
# def test_conversion_rename_incorrect_format_error():
#     """Test that an error is printed when the rename tag is formatted incorrectly in conversion."""
    
#     test_file = "conversion_rename_incorrect_format_error.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert not output_path.exists()        
                   
#     assert "Incorrect rename directive format.  Should be #[table_name].field_name.rename.new_field_name at cell" in output
#     assert "conversion_rename_incorrect_format_error.xlsx:#convert[C1]" in output
    



# def test_conversion_assign():
#     """Test that conversion assign works."""
    
#     test_file = "conversion_assign_test.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     with open(output_path, "r") as f:
#         output_json = json.loads(f.read())
        
        
#     assert "asdf" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"]
#     assert "asdf" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"]

#     assert output == ""
    
    
    
# def test_conversion_assign_before_value():
#     """Test that an error is printed when the assign tag appears before the value tag in conversion."""
    
#     test_file = "conversion_assign_before_value.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert not output_path.exists()        
                   
#     assert "#table_name.field_name.assign in column before #table_name.field_name.value at cell" in output
#     assert "conversion_assign_before_value.xlsx:#convert[B1]" in output
    
    
    
# def test_conversion_assign_table_name_mismatch():
#     """Test that an error is printed when there is a mismatch between the assign tag table and vale tag table in conversion."""
    
#     test_file = "conversion_assign_table_name_mismatch.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert not output_path.exists()        
                   
#     assert "Table name does not match between #table_name.field_name.value and #table_name.field_name.assign conversion tags at cell" in output
#     assert "conversion_assign_table_name_mismatch.xlsx:#convert[C1]" in output
    
    
    

# def test_conversion_append():
#     """Test that conversion append works."""
    
#     test_file = "conversion_append_test.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     with open(output_path, "r") as f:
#         output_json = json.loads(f.read())
        
        
#     assert "C5H8O4asdf" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"]
#     assert "C5H8O4asdf" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"]

#     assert output == ""
    
    
    
# def test_conversion_append_before_value():
#     """Test that an error is printed when the append tag appears before the value tag in conversion."""
    
#     test_file = "conversion_append_before_value.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert not output_path.exists()        
                   
#     assert "#table_name.field_name.append in column before #table_name.field_name.value at cell" in output
#     assert "conversion_append_before_value.xlsx:#convert[B1]" in output
    


# def test_conversion_append_table_name_mismatch():
#     """Test that an error is printed when there is a mismatch between the append tag table and vale tag table in conversion."""
    
#     test_file = "conversion_append_table_name_mismatch.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert not output_path.exists()        
                   
#     assert "Table name does not match between #table_name.field_name.value and #table_name.field_name.append conversion tags at cell" in output
#     assert "conversion_append_table_name_mismatch.xlsx:#convert[C1]" in output
    
    
    

# def test_conversion_prepend():
#     """Test that conversion prepend works."""
    
#     test_file = "conversion_prepend_test.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     with open(output_path, "r") as f:
#         output_json = json.loads(f.read())
        
        
#     assert "asdfC5H8O4" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"]
#     assert "asdfC5H8O4" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"]

#     assert output == ""
    
    
    
# def test_conversion_prepend_before_value():
#     """Test that an error is printed when the prepend tag appears before the value tag in conversion."""
    
#     test_file = "conversion_prepend_before_value.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert not output_path.exists()        
                   
#     assert "#table_name.field_name.prepend in column before #table_name.field_name.value at cell" in output
#     assert "conversion_prepend_before_value.xlsx:#convert[B1]" in output
    


# def test_conversion_prepend_table_name_mismatch():
#     """Test that an error is printed when there is a mismatch between the prepend tag table and vale tag table in conversion."""
    
#     test_file = "conversion_prepend_table_name_mismatch.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert not output_path.exists()        
                   
#     assert "Table name does not match between #table_name.field_name.value and #table_name.field_name.prepend conversion tags at cell" in output
#     assert "conversion_prepend_table_name_mismatch.xlsx:#convert[C1]" in output





# def test_conversion_regex():
#     """Test that conversion regex works."""
    
#     test_file = "conversion_regex_test.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     with open(output_path, "r") as f:
#         output_json = json.loads(f.read())
        
        
#     assert "asdf" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"]
#     assert "asdf" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"]

#     assert output == ""
    
    
    
# def test_conversion_regex_before_value():
#     """Test that an error is printed when the regex tag appears before the value tag in conversion."""
    
#     test_file = "conversion_regex_before_value.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert not output_path.exists()        
                   
#     assert "#table_name.field_name.regex in column before #table_name.field_name.value at cell" in output
#     assert "conversion_regex_before_value.xlsx:#convert[B1]" in output
    


# def test_conversion_regex_table_name_mismatch():
#     """Test that an error is printed when there is a mismatch between the regex tag table and vale tag table in conversion."""
    
#     test_file = "conversion_regex_table_name_mismatch.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert not output_path.exists()        
                   
#     assert "Table name does not match between #table_name.field_name.value and #table_name.field_name.regex conversion tags at cell" in output
#     assert "conversion_regex_table_name_mismatch.xlsx:#convert[C1]" in output
    
    



# def test_conversion_comparison():
#     """Test that conversion comparison works."""
    
#     test_file = "conversion_comparison_test.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     with open(output_path, "r") as f:
#         output_json = json.loads(f.read())
        
        
#     assert "asdf" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"]
#     assert "asdf" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"]

#     assert "asdf" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["raw_intensity"]
#     assert "asdf" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["raw_intensity"]

#     assert "asdf" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["corrected_raw_intensity"]
#     assert "asdf" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["corrected_raw_intensity"]

#     assert output == ""
    
    

# def test_conversion_comparison_type_regex():
#     """Test that conversion comparison=regex works."""
    
#     test_file = "conversion_comparison_type_regex_test.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     with open(output_path, "r") as f:
#         output_json = json.loads(f.read())
        
        
#     assert "asdf" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"]
#     assert "asdf" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"]

#     assert "Comparison type is indicated as regex, but comparison value is not a regex at cell" in output
#     assert "conversion_comparison_type_regex_test.xlsx:#convert[B3]" in output
#     assert "conversion_comparison_type_regex_test.xlsx:#convert[B4]" in output



# def test_conversion_comparison_type_exact():
#     """Test that conversion comparison=exact works."""
    
#     test_file = "conversion_comparison_type_exact_test.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     with open(output_path, "r") as f:
#         output_json = json.loads(f.read())
        
        
#     assert "qwer" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"]
#     assert "qwer" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"]

#     assert "Warning: conversion directive #measurement.compound.exact.r'\\(S\\)\\-2\\-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd' never matched." in output
#     assert "Warning: conversion directive #measurement.compound.exact.asdf never matched." in output



# def test_conversion_comparison_type_levenshtein():
#     """Test that conversion comparison=levenshtein works."""
    
#     test_file = "conversion_comparison_type_levenshtein_test.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     with open(output_path, "r") as f:
#         output_json = json.loads(f.read())
        
        
#     assert "zxcv" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"]
#     assert "zxcv" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"]

#     assert "Warning: conversion directive #measurement.compound.levenshtein.(S)-2-Acetolactate_Glutaric acid_Meth never matched." in output
#     assert "Warning: conversion directive #measurement.compound.levenshtein.(S)-2-Acetolactate_Glu never matched." in output



def test_conversion_comparison_type_regex_or_exact():
    """Test that conversion comparison=regex|exact works."""
    
    test_file = "conversion_comparison_type_regex_or_exact_test.xlsx"
    
    command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
        
    assert "asdf" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"]
    assert "asdf" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"]

    assert "Warning: conversion directive #measurement.compound.exact.asdf never matched." in output


















