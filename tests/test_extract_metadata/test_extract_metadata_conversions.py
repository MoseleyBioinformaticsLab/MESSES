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



# def test_conversion_comparison_type_regex_or_exact():
#     """Test that conversion comparison=regex|exact works."""
    
#     test_file = "conversion_comparison_type_regex_or_exact_test.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     with open(output_path, "r") as f:
#         output_json = json.loads(f.read())
        
        
#     assert "asdf" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"]
#     assert "asdf" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"]

#     assert "Warning: conversion directive #measurement.compound.exact.asdf never matched." in output




# def test_conversion_assign_after_assign_warning():
#     """Test that a warning is printed when 2 assign conversions assign to the same record field."""
    
#     test_file = "conversion_assign_after_assign_warning.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     assert output == 'Warning: "formula" in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was assigned a new value after previously being modified by a different conversion directive.\nWarning: "formula" in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was assigned a new value after previously being modified by a different conversion directive.' + "\n"




# def test_conversion_assign_after_assign_same_value():
#     """Test that nothing is printed when 2 assign conversions assign the same value to the same record field."""
    
#     test_file = "conversion_assign_after_assign_same_value.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     assert output == ""




# def test_conversion_assign_after_append_warning():
#     """Test that a warning is printed when an assign conversion follows an append to the same record field."""
    
#     test_file = "conversion_assign_after_append_warning.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     assert output == 'Warning: "formula" in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was assigned a new value after previously being modified by a different conversion directive.\nWarning: "formula" in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was assigned a new value after previously being modified by a different conversion directive.' + "\n"



# def test_conversion_assign_after_prepend_warning():
#     """Test that a warning is printed when an assign conversion follows a prepend to the same record field."""
    
#     test_file = "conversion_assign_after_prepend_warning.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     assert output == 'Warning: "formula" in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was assigned a new value after previously being modified by a different conversion directive.\nWarning: "formula" in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was assigned a new value after previously being modified by a different conversion directive.' + "\n"



# def test_conversion_assign_after_regex_warning():
#     """Test that a warning is printed when an assign conversion follows a regex to the same record field."""
    
#     test_file = "conversion_assign_after_regex_warning.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     assert output == 'Warning: "formula" in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was assigned a new value after previously being modified by a different conversion directive.\nWarning: "formula" in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was assigned a new value after previously being modified by a different conversion directive.' + "\n"



# def test_conversion_assign_after_delete_warning():
#     """Test that a warning is printed when an assign conversion follows a delete to the same record field."""
    
#     test_file = "conversion_assign_after_delete_warning.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     assert output == 'Warning: "formula" in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was assigned a new value after previously being modified by a different conversion directive.\nWarning: "formula" in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was assigned a new value after previously being modified by a different conversion directive.' + "\n"




# def test_conversion_append_after_delete_warning():
#     """Test that a warning is printed when an append conversion follows a delete to the same record field."""
    
#     test_file = "conversion_append_after_delete_warning.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     assert output == 'Warning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted before being appended to by a different conversion directive.\nWarning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted before being appended to by a different conversion directive.' + "\n"



# def test_conversion_prepend_after_delete_warning():
#     """Test that a warning is printed when a prepend conversion follows a delete to the same record field."""
    
#     test_file = "conversion_prepend_after_delete_warning.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     assert output == 'Warning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted before being prepended to by a different conversion directive.\nWarning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted before being prepended to by a different conversion directive.' + "\n"



# def test_conversion_regex_after_delete_warning():
#     """Test that a warning is printed when a regex conversion follows a delete to the same record field."""
    
#     test_file = "conversion_regex_after_delete_warning.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     assert output == 'Warning: regex substitution (C,asdf) cannot be applied to record with missing field "formula"\nWarning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted by a conversion directive before attempting to be modified by a regex conversion directive.\nWarning: regex substitution (C,asdf) cannot be applied to record with missing field "formula"\nWarning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted by a conversion directive before attempting to be modified by a regex conversion directive.' + "\n"



# def test_conversion_regex_after_assign_warning():
#     """Test that a warning is printed when a regex conversion follows an assign to the same record field."""
    
#     test_file = "conversion_regex_after_assign_warning.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     assert output == 'Warning: regex substitution (C,asdf) produces no change in field "formula" value "asdf"\nWarning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], had a regex substitution applied after previously being assigned a new value by an assignment conversion directive.\nWarning: regex substitution (C,asdf) produces no change in field "formula" value "asdf"\nWarning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], had a regex substitution applied after previously being assigned a new value by an assignment conversion directive.' + "\n"



# def test_conversion_delete_after_assign_warning():
#     """Test that a warning is printed when a delete conversion follows an assign to the same record field."""
    
#     test_file = "conversion_delete_after_assign_warning.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     assert output == 'Warning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted after previously being modified by a different conversion directive.\nWarning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted after previously being modified by a different conversion directive.' + "\n"



# def test_conversion_delete_after_append_warning():
#     """Test that a warning is printed when a delete conversion follows an append to the same record field."""
    
#     test_file = "conversion_delete_after_append_warning.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     assert output == 'Warning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted after previously being modified by a different conversion directive.\nWarning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted after previously being modified by a different conversion directive.' + "\n"



# def test_conversion_delete_after_prepend_warning():
#     """Test that a warning is printed when a delete conversion follows a prepend to the same record field."""
    
#     test_file = "conversion_delete_after_prepend_warning.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     assert output == 'Warning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted after previously being modified by a different conversion directive.\nWarning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted after previously being modified by a different conversion directive.' + "\n"



# def test_conversion_delete_after_regex_warning():
#     """Test that a warning is printed when a delete conversion follows a regex to the same record field."""
    
#     test_file = "conversion_delete_after_regex_warning.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     assert output == 'Warning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted after previously being modified by a different conversion directive.\nWarning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted after previously being modified by a different conversion directive.' + "\n"



# def test_conversion_delete_after_rename_warning():
#     """Test that a warning is printed when a delete conversion follows a rename to the same record field."""
    
#     test_file = "conversion_delete_after_rename_warning.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     assert output == 'Warning: The field, "asdf", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted after previously being modified by a different conversion directive.\nWarning: The field, "asdf", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted after previously being modified by a different conversion directive.' + "\n"




# def test_conversion_rename_after_delete_oldfield_warning():
#     """Test that a warning is printed when a rename conversion follows a delete on the old field name of the same record field."""
    
#     test_file = "conversion_rename_after_delete_oldfield_warning.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     assert output == 'Warning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted by a conversion directive, and then a different conversion directive attempted to rename it, but it no longer exists.\nWarning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted by a conversion directive, and then a different conversion directive attempted to rename it, but it no longer exists.' + "\n"
   
    
   
# def test_conversion_rename_after_delete_newfield_warning():
#     """Test that a warning is printed when a rename conversion follows a delete on the new field name of the same record field."""
    
#     test_file = "conversion_rename_after_delete_newfield_warning.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     assert output == 'Warning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted by a conversion directive, but then a rename directive created it again from a different field.\nWarning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted by a conversion directive, but then a rename directive created it again from a different field.' + "\n"
    

    

# def test_conversion_rename_overwrite():
#     """Test that a warning is printed when a rename conversion renames a field to an already existing field."""
    
#     test_file = "conversion_rename_overwrite.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     assert output == 'Warning: A conversion directive has renamed the field "formula" to "compound" for record measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], but "compound" already existed in the record, so its value was overwritten.\nWarning: A conversion directive has renamed the field "formula" to "compound" for record measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], but "compound" already existed in the record, so its value was overwritten.' + "\n"

    

# def test_conversion_rename_same_value():
#     """Test that an error is printed when a rename conversion tries to rename a field to the same name."""
    
#     test_file = "conversion_rename_same_value.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert not output_path.exists()
    
#     assert "rename conversion directive renames the field to the same name at cell" in output
#     assert "conversion_rename_same_value.xlsx:#convert[C1]" in output
    
 
    
# def test_conversion_missing_tags_error():
#     """Test that an error is printed when there are no assing|append|prepend|regex|rename tags."""
    
#     test_file = "conversion_missing_tags_error.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert not output_path.exists()
    
#     assert "Missing #table_name.field_name.value or #.field_name.assign|append|prepend|regex|delete|rename conversion tags at cell" in output
#     assert "conversion_missing_tags_error.xlsx:#convert[:1]" in output



# def test_conversion_delete_id_error():
#     """Test that an error is printed when a tag tries to delete the id field."""
    
#     test_file = "conversion_delete_id_error.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert not output_path.exists()
    
#     assert "Not allowed to delete id fields at cell" in output
#     assert "conversion_delete_id_error.xlsx:#convert[:1]" in output



# def test_conversion_regex_incorrect_format_error():
#     """Test that an error is printed when the regex tag value is not 2 r'...' strings."""
    
#     test_file = "conversion_regex_incorrect_format_error.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert not output_path.exists()
    
#     assert '#table_name.field_name.regex value is not of the correct format r"...",r"...". at cell' in output
#     assert "conversion_regex_incorrect_format_error.xlsx:#convert[B2]" in output
    
    
    
# def test_conversion_duplicate_assign_warning():
#     """Test that a warning is printed when there are 2 assign tags with the same value in table.field.value column."""
    
#     test_file = "conversion_duplicate_assign_warning.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     assert 'Warning: duplicate assign conversion directive given at cell' in output
#     assert "conversion_duplicate_assign_warning.xlsx:#convert[:3]" in output
    
    
# def test_conversion_duplicate_append_warning():
#     """Test that a warning is printed when there are 2 append tags with the same value in table.field.value column."""
    
#     test_file = "conversion_duplicate_append_warning.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     assert 'Warning: duplicate append conversion directive given at cell' in output
#     assert "conversion_duplicate_append_warning.xlsx:#convert[:3]" in output
    
    
# def test_conversion_duplicate_prepend_warning():
#     """Test that a warning is printed when there are 2 prepend tags with the same value in table.field.value column."""
    
#     test_file = "conversion_duplicate_prepend_warning.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     assert 'Warning: duplicate prepend conversion directive given at cell' in output
#     assert "conversion_duplicate_prepend_warning.xlsx:#convert[:3]" in output
    
    
# def test_conversion_duplicate_regex_warning():
#     """Test that a warning is printed when there are 2 regex tags with the same value in table.field.value column."""
    
#     test_file = "conversion_duplicate_regex_warning.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     assert 'Warning: duplicate regex conversion directive given at cell' in output
#     assert "conversion_duplicate_regex_warning.xlsx:#convert[:3]" in output
    
    
# def test_conversion_duplicate_delete_warning():
#     """Test that a warning is printed when there are 2 delete tags with the same value in table.field.value column."""
    
#     test_file = "conversion_duplicate_delete_warning.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     assert 'Warning: duplicate delete conversion directive given at cell' in output
#     assert "conversion_duplicate_delete_warning.xlsx:#convert[:3]" in output
    
    
# def test_conversion_duplicate_rename_warning():
#     """Test that a warning is printed when there are 2 rename tags with the same value in table.field.value column."""
    
#     test_file = "conversion_duplicate_rename_warning.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     assert 'Warning: duplicate rename conversion directive given at cell' in output
#     assert "conversion_duplicate_rename_warning.xlsx:#convert[:3]" in output



## TODO retest unique once you know what the behavior should be.
# def test_conversion_comparison_type_regex_or_exact_unique_test():
#     """Test that only 1 record is changed when unique is true for comparison type regex|exact."""
    
#     test_file = "conversion_comparison_type_regex_or_exact_unique_test.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     with open(output_path, "r") as f:
#         output_json = json.loads(f.read())
        
#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "asdf"
#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "C5H8O4"

#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["compound"] == "asdf"
#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["compound"] == ["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd"]



# def test_conversion_comparison_type_exact_unique_test():
#     """Test that only 1 record is changed when unique is true for cmparison type exact."""
    
#     test_file = "conversion_comparison_type_exact_unique_test.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     with open(output_path, "r") as f:
#         output_json = json.loads(f.read())
        
#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "asdf"
#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "C5H8O4"
    
#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["compound"] == "asdf"
#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["compound"] == ["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd"]



# def test_conversion_comparison_type_regex_unique_test():
#     """Test that only 1 record is changed when unique is true for comparison type regex."""
    
#     test_file = "conversion_comparison_type_regex_unique_test.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     with open(output_path, "r") as f:
#         output_json = json.loads(f.read())
        
#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "asdf"
#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "C5H8O4"
    
#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["compound"] == "asdf"
#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["compound"] == ["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd"]




# def test_conversion_field_creation():
#     """Test that the field is created if it does not exist for assign, append, and prepend."""
    
#     test_file = "conversion_field_creation.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     with open(output_path, "r") as f:
#         output_json = json.loads(f.read())
        
#     assert output == ""
        
#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["new_assign_field"] == "asdf"
#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["new_assign_list_field"] == ["asdf"]
    
#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["new_append_field"] == "asdf"
#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["new_append_list_field"] == ["asdf"]
    
#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["new_prepend_field"] == "asdf"
#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["new_prepend_list_field"] == ["asdf"]




# def test_conversion_assign_list_field_test():
#     """Test that field is overwritten to and from list field type."""
    
#     test_file = "conversion_assign_list_field_test.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     with open(output_path, "r") as f:
#         output_json = json.loads(f.read())
        
#     assert output == ""
        
#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["compound"] == "asdf"
#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == ["asdf"]
    
#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["compound"] == "asdf"
#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == ["asdf"]
 
    
 
# def test_conversion_append_list_field_test():
#     """Test that append works with list fields correctly."""
    
#     test_file = "conversion_append_list_field_test.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     with open(output_path, "r") as f:
#         output_json = json.loads(f.read())
        
#     assert output == ""
        
#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["compound"] == ["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStdasdf", "asdfasdf"]
#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == ["C5H8O4asdf", "qwerqwer"]
#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C0asdf"
    
#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["compound"] == ["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStdasdf", "asdfasdf"]
#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == ["C5H8O4asdf", "qwerqwer"]
#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C1asdf"




# def test_conversion_prepend_list_field_test():
#     """Test that prepend works with list fields correctly."""
    
#     test_file = "conversion_prepend_list_field_test.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     with open(output_path, "r") as f:
#         output_json = json.loads(f.read())
        
#     assert output == ""
        
#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["compound"] == ["asdf(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd", "asdfasdf"]
#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == ["asdfC5H8O4", "qwerqwer"]
#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "asdf(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C0"

#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["compound"] == ["asdf(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd", "asdfasdf"]
#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == ["asdfC5H8O4", "qwerqwer"]
#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "asdf(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C1"



# def test_conversion_regex_list_field_test():
#     """Test that regex works with list fields correctly."""
    
#     test_file = "conversion_regex_list_field_test.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     with open(output_path, "r") as f:
#         output_json = json.loads(f.read())
        
#     assert output == ""
        
#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["compound"] == ["(S)-2-Acetolqwerctqwerte_Glutqwerric qwercid_Methylsuccinic qwercid_MP_NoStd", "qwersdf"]

#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["compound"] == ["(S)-2-Acetolqwerctqwerte_Glutqwerric qwercid_Methylsuccinic qwercid_MP_NoStd", "qwersdf"]



# def test_conversion_levenshtein_list_field_test():
#     """Test that levenshtein works with list fields correctly."""
    
#     test_file = "conversion_levenshtein_list_field_test.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     with open(output_path, "r") as f:
#         output_json = json.loads(f.read())
        
#     assert output == ""
        
#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "zxcv"

#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "zxcv"




# def test_conversion_semicolon_list_field_test():
#     """Test that semicolon separators work."""
    
#     test_file = "conversion_semicolon_list_field_test.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     with open(output_path, "r") as f:
#         output_json = json.loads(f.read())
        
#     assert output == ""
        
#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == ["preasdfapp", "pre2qwerapp2"]
    
#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == ["preasdfapp", "pre2qwerapp2"]



# def test_conversion_ignore_test():
#     """Test that #ignore works."""
    
#     test_file = "conversion_ignore_test.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     with open(output_path, "r") as f:
#         output_json = json.loads(f.read())
        
#     assert output == ""
        
#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "qwer"
    
#     assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "qwer"




# def test_conversion_comparison_type_levenshtein_unique_test():
#     """Test that levenshtien works with #unique=true by making sure it does not match to any records if they have the same minimum distance."""
    
#     test_file = "conversion_comparison_type_levenshtein_unique_test.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " --output " + output_path.as_posix()
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     assert output == "Warning: conversion directive #measurement.compound.levenshtein-unique.(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd never matched." + "\n"



# def test_conversion_unused_test():
#     """Test that nothing is printed when there is an unused conversion in an individual metadata that is then used in end-convert."""
    
#     test_file = "conversion_unused_test.xlsx"
    
#     command = "py -3.7 ../../../src/messes/extract_metadata.py ../" + test_file + " ../base_source_export.csv" + " --output " + output_path.as_posix() + " --end-convert ../" + test_file + ":#convert"
#     command = command.split(" ")
#     subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
#     output = subp.stderr

    
#     assert output_path.exists()
    
#     assert output == ""







## Test unique = True.
## Test having an unused conversion in #convert but then is used in end-convert

