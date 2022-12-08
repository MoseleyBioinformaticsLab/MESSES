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
    os.chdir(pathlib.Path("tests", "test_extract", "testing_files", "main_dir"))
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




def test_modification_delete():
    """Test that modification delete works."""
    
    test_file = "modification_delete_test.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
        
    assert not "formula" in output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]
    assert not "formula" in output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]

    assert output == ""



def test_modification_delete_before_value():
    """Test that an error is printed when the delete tag appears before the value tag in modification."""
    
    test_file = "modification_delete_before_value.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()        
                   
    assert "#table_name.field_name.delete in column before #table_name.field_name.value at cell" in output
    assert "modification_delete_before_value.xlsx:#modify[B1]" in output



def test_modification_delete_table_name_mismatch():
    """Test that an error is printed when there is a mismatch between the delete tag table and vale tag table in modification."""
    
    test_file = "modification_delete_table_name_mismatch.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()        
                   
    assert "Table name does not match between #table_name.field_name.value and #table_name.field_name.delete modification tags at cell" in output
    assert "modification_delete_table_name_mismatch.xlsx:#modify[C1]" in output



def test_modification_rename():
    """Test that modification rename works."""
    
    test_file = "modification_rename_test.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
        
    assert not "formula" in output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]
    assert not "formula" in output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]
    assert "molecular_formula" in output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]
    assert "molecular_formula" in output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]

    assert output == ""



def test_modification_rename_before_value():
    """Test that an error is printed when the rename tag appears before the value tag in modification."""
    
    test_file = "modification_rename_before_value.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()        
                   
    assert "#table_name.field_name.rename in column before #table_name.field_name.value at cell" in output
    assert "modification_rename_before_value.xlsx:#modify[B1]" in output
    
    
    
def test_modification_rename_table_name_mismatch():
    """Test that an error is printed when there is a mismatch between the rename tag table and vale tag table in modification."""
    
    test_file = "modification_rename_table_name_mismatch.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()        
                   
    assert "Table name does not match between #table_name.field_name.value and #table_name.field_name.rename modification tags at cell" in output
    assert "modification_rename_table_name_mismatch.xlsx:#modify[C1]" in output
    
    
    
def test_modification_rename_incorrect_format_error():
    """Test that an error is printed when the rename tag is formatted incorrectly in modification."""
    
    test_file = "modification_rename_incorrect_format_error.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()        
                   
    assert "Incorrect rename directive format.  Should be #[table_name].field_name.rename.new_field_name at cell" in output
    assert "modification_rename_incorrect_format_error.xlsx:#modify[C1]" in output
    



def test_modification_assign():
    """Test that modification assign works."""
    
    test_file = "modification_assign_test.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
        
    assert "asdf" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"]
    assert "asdf" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"]

    assert output == ""
    
    
    
def test_modification_assign_before_value():
    """Test that an error is printed when the assign tag appears before the value tag in modification."""
    
    test_file = "modification_assign_before_value.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()        
                   
    assert "#table_name.field_name.assign in column before #table_name.field_name.value at cell" in output
    assert "modification_assign_before_value.xlsx:#modify[B1]" in output
    
    
    
def test_modification_assign_table_name_mismatch():
    """Test that an error is printed when there is a mismatch between the assign tag table and vale tag table in modification."""
    
    test_file = "modification_assign_table_name_mismatch.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()        
                   
    assert "Table name does not match between #table_name.field_name.value and #table_name.field_name.assign modification tags at cell" in output
    assert "modification_assign_table_name_mismatch.xlsx:#modify[C1]" in output
    
    
    

def test_modification_append():
    """Test that modification append works."""
    
    test_file = "modification_append_test.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
        
    assert "C5H8O4asdf" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"]
    assert "C5H8O4asdf" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"]

    assert output == ""
    
    
    
def test_modification_append_before_value():
    """Test that an error is printed when the append tag appears before the value tag in modification."""
    
    test_file = "modification_append_before_value.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()        
                   
    assert "#table_name.field_name.append in column before #table_name.field_name.value at cell" in output
    assert "modification_append_before_value.xlsx:#modify[B1]" in output
    


def test_modification_append_table_name_mismatch():
    """Test that an error is printed when there is a mismatch between the append tag table and vale tag table in modification."""
    
    test_file = "modification_append_table_name_mismatch.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()        
                   
    assert "Table name does not match between #table_name.field_name.value and #table_name.field_name.append modification tags at cell" in output
    assert "modification_append_table_name_mismatch.xlsx:#modify[C1]" in output
    
    
    

def test_modification_prepend():
    """Test that modification prepend works."""
    
    test_file = "modification_prepend_test.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
        
    assert "asdfC5H8O4" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"]
    assert "asdfC5H8O4" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"]

    assert output == ""
    
    
    
def test_modification_prepend_before_value():
    """Test that an error is printed when the prepend tag appears before the value tag in modification."""
    
    test_file = "modification_prepend_before_value.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()        
                   
    assert "#table_name.field_name.prepend in column before #table_name.field_name.value at cell" in output
    assert "modification_prepend_before_value.xlsx:#modify[B1]" in output
    


def test_modification_prepend_table_name_mismatch():
    """Test that an error is printed when there is a mismatch between the prepend tag table and vale tag table in modification."""
    
    test_file = "modification_prepend_table_name_mismatch.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()        
                   
    assert "Table name does not match between #table_name.field_name.value and #table_name.field_name.prepend modification tags at cell" in output
    assert "modification_prepend_table_name_mismatch.xlsx:#modify[C1]" in output





def test_modification_regex():
    """Test that modification regex works."""
    
    test_file = "modification_regex_test.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
        
    assert "asdf" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"]
    assert "asdf" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"]

    assert output == ""
    
    
    
def test_modification_regex_before_value():
    """Test that an error is printed when the regex tag appears before the value tag in modification."""
    
    test_file = "modification_regex_before_value.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()        
                   
    assert "#table_name.field_name.regex in column before #table_name.field_name.value at cell" in output
    assert "modification_regex_before_value.xlsx:#modify[B1]" in output
    


def test_modification_regex_table_name_mismatch():
    """Test that an error is printed when there is a mismatch between the regex tag table and vale tag table in modification."""
    
    test_file = "modification_regex_table_name_mismatch.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()        
                   
    assert "Table name does not match between #table_name.field_name.value and #table_name.field_name.regex modification tags at cell" in output
    assert "modification_regex_table_name_mismatch.xlsx:#modify[C1]" in output
    
    



def test_modification_comparison():
    """Test that modification comparison works."""
    
    test_file = "modification_comparison_test.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
        
    assert "asdf" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"]
    assert "asdf" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"]

    assert "asdf" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["raw_intensity"]
    assert "asdf" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["raw_intensity"]

    assert "asdf" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["corrected_raw_intensity"]
    assert "asdf" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["corrected_raw_intensity"]

    assert output == ""
    
    

def test_modification_comparison_type_regex():
    """Test that modification comparison=regex works."""
    
    test_file = "modification_comparison_type_regex_test.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
        
    assert "asdf" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"]
    assert "asdf" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"]

    assert "Comparison type is indicated as regex, but comparison value is not a regex at cell" in output
    assert "modification_comparison_type_regex_test.xlsx:#modify[B3]" in output
    assert "modification_comparison_type_regex_test.xlsx:#modify[B4]" in output



def test_modification_comparison_type_exact():
    """Test that modification comparison=exact works."""
    
    test_file = "modification_comparison_type_exact_test.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
        
    assert "qwer" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"]
    assert "qwer" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"]

    assert "Warning: modification directive #measurement.compound.exact-all.r'\\(S\\)\\-2\\-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd' never matched." in output
    assert "Warning: modification directive #measurement.compound.exact-all.asdf never matched." in output



def test_modification_comparison_type_regex_or_exact():
    """Test that modification comparison=regex|exact works."""
    
    test_file = "modification_comparison_type_regex_or_exact_test.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
        
    assert "asdf" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"]
    assert "asdf" == output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"]

    assert "Warning: modification directive #measurement.compound.exact-all.asdf never matched." in output




def test_modification_assign_after_assign_warning():
    """Test that a warning is printed when 2 assign modifications assign to the same record field."""
    
    test_file = "modification_assign_after_assign_warning.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    assert output == 'Warning: "formula" in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was assigned a new value after previously being modified by a different modification directive.\nWarning: "formula" in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was assigned a new value after previously being modified by a different modification directive.' + "\n"




def test_modification_assign_after_assign_same_value():
    """Test that nothing is printed when 2 assign modifications assign the same value to the same record field."""
    
    test_file = "modification_assign_after_assign_same_value.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    assert output == ""




def test_modification_assign_after_append_warning():
    """Test that a warning is printed when an assign modification follows an append to the same record field."""
    
    test_file = "modification_assign_after_append_warning.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    assert output == 'Warning: "formula" in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was assigned a new value after previously being modified by a different modification directive.\nWarning: "formula" in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was assigned a new value after previously being modified by a different modification directive.' + "\n"



def test_modification_assign_after_prepend_warning():
    """Test that a warning is printed when an assign modification follows a prepend to the same record field."""
    
    test_file = "modification_assign_after_prepend_warning.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    assert output == 'Warning: "formula" in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was assigned a new value after previously being modified by a different modification directive.\nWarning: "formula" in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was assigned a new value after previously being modified by a different modification directive.' + "\n"



def test_modification_assign_after_regex_warning():
    """Test that a warning is printed when an assign modification follows a regex to the same record field."""
    
    test_file = "modification_assign_after_regex_warning.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    assert output == 'Warning: "formula" in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was assigned a new value after previously being modified by a different modification directive.\nWarning: "formula" in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was assigned a new value after previously being modified by a different modification directive.' + "\n"



def test_modification_assign_after_delete_warning():
    """Test that a warning is printed when an assign modification follows a delete to the same record field."""
    
    test_file = "modification_assign_after_delete_warning.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    assert output == 'Warning: "formula" in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was assigned a new value after previously being modified by a different modification directive.\nWarning: "formula" in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was assigned a new value after previously being modified by a different modification directive.' + "\n"




def test_modification_append_after_delete_warning():
    """Test that a warning is printed when an append modification follows a delete to the same record field."""
    
    test_file = "modification_append_after_delete_warning.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    assert output == 'Warning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted before being appended to by a different modification directive.\nWarning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted before being appended to by a different modification directive.' + "\n"



def test_modification_prepend_after_delete_warning():
    """Test that a warning is printed when a prepend modification follows a delete to the same record field."""
    
    test_file = "modification_prepend_after_delete_warning.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    assert output == 'Warning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted before being prepended to by a different modification directive.\nWarning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted before being prepended to by a different modification directive.' + "\n"



def test_modification_regex_after_delete_warning():
    """Test that a warning is printed when a regex modification follows a delete to the same record field."""
    
    test_file = "modification_regex_after_delete_warning.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    assert output == 'Warning: regex substitution (C,asdf) cannot be applied to record with missing field "formula"\nWarning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted by a modification directive before attempting to be modified by a regex modification directive.\nWarning: regex substitution (C,asdf) cannot be applied to record with missing field "formula"\nWarning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted by a modification directive before attempting to be modified by a regex modification directive.' + "\n"



def test_modification_regex_after_assign_warning():
    """Test that a warning is printed when a regex modification follows an assign to the same record field."""
    
    test_file = "modification_regex_after_assign_warning.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    assert output == 'Warning: regex substitution (C,asdf) produces no change in field "formula" value "asdf"\nWarning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], had a regex substitution applied after previously being assigned a new value by an assignment modification directive.\nWarning: regex substitution (C,asdf) produces no change in field "formula" value "asdf"\nWarning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], had a regex substitution applied after previously being assigned a new value by an assignment modification directive.' + "\n"



def test_modification_delete_after_assign_warning():
    """Test that a warning is printed when a delete modification follows an assign to the same record field."""
    
    test_file = "modification_delete_after_assign_warning.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    assert output == 'Warning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted after previously being modified by a different modification directive.\nWarning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted after previously being modified by a different modification directive.' + "\n"



def test_modification_delete_after_append_warning():
    """Test that a warning is printed when a delete modification follows an append to the same record field."""
    
    test_file = "modification_delete_after_append_warning.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    assert output == 'Warning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted after previously being modified by a different modification directive.\nWarning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted after previously being modified by a different modification directive.' + "\n"



def test_modification_delete_after_prepend_warning():
    """Test that a warning is printed when a delete modification follows a prepend to the same record field."""
    
    test_file = "modification_delete_after_prepend_warning.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    assert output == 'Warning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted after previously being modified by a different modification directive.\nWarning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted after previously being modified by a different modification directive.' + "\n"



def test_modification_delete_after_regex_warning():
    """Test that a warning is printed when a delete modification follows a regex to the same record field."""
    
    test_file = "modification_delete_after_regex_warning.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    assert output == 'Warning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted after previously being modified by a different modification directive.\nWarning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted after previously being modified by a different modification directive.' + "\n"



def test_modification_delete_after_rename_warning():
    """Test that a warning is printed when a delete modification follows a rename to the same record field."""
    
    test_file = "modification_delete_after_rename_warning.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    assert output == 'Warning: The field, "asdf", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted after previously being modified by a different modification directive.\nWarning: The field, "asdf", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted after previously being modified by a different modification directive.' + "\n"




def test_modification_rename_after_delete_oldfield_warning():
    """Test that a warning is printed when a rename modification follows a delete on the old field name of the same record field."""
    
    test_file = "modification_rename_after_delete_oldfield_warning.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    assert output == 'Warning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted by a modification directive, and then a different modification directive attempted to rename it, but it no longer exists.\nWarning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted by a modification directive, and then a different modification directive attempted to rename it, but it no longer exists.' + "\n"
   
    
   
def test_modification_rename_after_delete_newfield_warning():
    """Test that a warning is printed when a rename modification follows a delete on the new field name of the same record field."""
    
    test_file = "modification_rename_after_delete_newfield_warning.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    assert output == 'Warning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted by a modification directive, but then a rename directive created it again from a different field.\nWarning: The field, "formula", in record, measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], was deleted by a modification directive, but then a rename directive created it again from a different field.' + "\n"
    

    

def test_modification_rename_overwrite():
    """Test that a warning is printed when a rename modification renames a field to an already existing field."""
    
    test_file = "modification_rename_overwrite.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    assert output == 'Warning: A modification directive has renamed the field "formula" to "compound" for record measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], but "compound" already existed in the record, so its value was overwritten.\nWarning: A modification directive has renamed the field "formula" to "compound" for record measurement[(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench], but "compound" already existed in the record, so its value was overwritten.' + "\n"

    

def test_modification_rename_same_value():
    """Test that an error is printed when a rename modification tries to rename a field to the same name."""
    
    test_file = "modification_rename_same_value.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
    
    assert "rename modification directive renames the field to the same name at cell" in output
    assert "modification_rename_same_value.xlsx:#modify[C1]" in output
    
 
    
def test_modification_missing_tags_error():
    """Test that an error is printed when there are no assing|append|prepend|regex|rename tags."""
    
    test_file = "modification_missing_tags_error.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
    
    assert "Missing #table_name.field_name.value or #.field_name.assign|append|prepend|regex|delete|rename modification tags at cell" in output
    assert "modification_missing_tags_error.xlsx:#modify[:1]" in output



def test_modification_delete_id_error():
    """Test that an error is printed when a tag tries to delete the id field."""
    
    test_file = "modification_delete_id_error.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
    
    assert "Not allowed to delete \"id\" fields at cell" in output
    assert "modification_delete_id_error.xlsx:#modify[:1]" in output
    
    
def test_modification_rename_id_error():
    """Test that an error is printed when a tag tries to rename the id field."""
    
    test_file = "modification_rename_id_error.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
    
    assert "Not allowed to rename \"id\" fields at cell" in output
    assert "modification_rename_id_error.xlsx:#modify[C1]" in output



def test_modification_regex_incorrect_format_error():
    """Test that an error is printed when the regex tag value is not 2 r'...' strings."""
    
    test_file = "modification_regex_incorrect_format_error.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
    
    assert '#table_name.field_name.regex value is not of the correct format r"...",r"...". at cell' in output
    assert "modification_regex_incorrect_format_error.xlsx:#modify[B2]" in output
    
    
    
def test_modification_duplicate_assign_warning():
    """Test that a warning is printed when there are 2 assign tags with the same value in table.field.value column."""
    
    test_file = "modification_duplicate_assign_warning.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    assert 'Warning: duplicate assign modification directive given at cell' in output
    assert "modification_duplicate_assign_warning.xlsx:#modify[:3]" in output
    
    
def test_modification_duplicate_append_warning():
    """Test that a warning is printed when there are 2 append tags with the same value in table.field.value column."""
    
    test_file = "modification_duplicate_append_warning.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    assert 'Warning: duplicate append modification directive given at cell' in output
    assert "modification_duplicate_append_warning.xlsx:#modify[:3]" in output
    
    
def test_modification_duplicate_prepend_warning():
    """Test that a warning is printed when there are 2 prepend tags with the same value in table.field.value column."""
    
    test_file = "modification_duplicate_prepend_warning.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    assert 'Warning: duplicate prepend modification directive given at cell' in output
    assert "modification_duplicate_prepend_warning.xlsx:#modify[:3]" in output
    
    
def test_modification_duplicate_regex_warning():
    """Test that a warning is printed when there are 2 regex tags with the same value in table.field.value column."""
    
    test_file = "modification_duplicate_regex_warning.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    assert 'Warning: duplicate regex modification directive given at cell' in output
    assert "modification_duplicate_regex_warning.xlsx:#modify[:3]" in output
    
    
def test_modification_duplicate_delete_warning():
    """Test that a warning is printed when there are 2 delete tags with the same value in table.field.value column."""
    
    test_file = "modification_duplicate_delete_warning.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    assert 'Warning: duplicate delete modification directive given at cell' in output
    assert "modification_duplicate_delete_warning.xlsx:#modify[:3]" in output
    
    
def test_modification_duplicate_rename_warning():
    """Test that a warning is printed when there are 2 rename tags with the same value in table.field.value column."""
    
    test_file = "modification_duplicate_rename_warning.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    assert 'Warning: duplicate rename modification directive given at cell' in output
    assert "modification_duplicate_rename_warning.xlsx:#modify[:3]" in output



def test_modification_comparison_type_exact_unique_test():
    """Test that values are only changed if it is unique when #match=unique."""
    
    test_file = "modification_comparison_type_exact_unique_test.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    assert "Warning: modification directive #measurement.formula.exact-unique.ghjk never matched." in output
    assert "Warning: modification directive #measurement.compound.exact-unique.(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd never matched." in output
        
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "C5H8O4"
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "C5H8O4"
    
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0"
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1"
    
    assert output_json["measurement"]["asdf-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "qwer"
    
    assert output_json["measurement"]["zxcv-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "zxcv-13C0"
    assert output_json["measurement"]["zxcv-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "zxcv-13C1"


def test_modification_comparison_type_exact_first_test():
    """Test that only the first values are changed when #match=first."""
    
    test_file = "modification_comparison_type_exact_first_test.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    assert "Warning: modification directive #measurement.compound.exact-first.(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd matches more than one record. Only the first record will be changed. Try #match=all if all matching records should be changed, or #match=first-nowarn to silence this message." in output
    assert "Warning: modification directive #measurement.formula.exact-first.qwer matches more than one record. Only the first record will be changed. Try #match=all if all matching records should be changed, or #match=first-nowarn to silence this message." in output
        
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "asdf"
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "C5H8O4"
    
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "asdf"
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1"
    
    assert output_json["measurement"]["asdf-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "qwer"
    assert output_json["measurement"]["asdf-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "asdf-13C1"
    
    
def test_modification_comparison_type_exact_first_nowarn_test():
    """Test that only the first values are changed when #match=first-nowarn and no message is printed."""
    
    test_file = "modification_comparison_type_exact_first-nowarn_test.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    assert output == ""
        
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "asdf"
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "C5H8O4"
    
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "asdf"
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1"
    
    assert output_json["measurement"]["asdf-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "qwer"


def test_modification_comparison_type_exact_all_test():
    """Test that all values are changed when #match=all and no message is printed."""
    
    test_file = "modification_comparison_type_exact_all_test.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    assert output == ""
        
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "asdf"
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "asdf"
    
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "asdf"
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "asdf"
    
    assert output_json["measurement"]["asdf-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "qwer"



def test_modification_comparison_type_regex_unique_test():
    """Test that values are only changed if it is unique when #match=unique."""
    
    test_file = "modification_comparison_type_regex_unique_test.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    assert "Warning: modification directive #measurement.compound.regex-unique.r'\(S\)\-2\-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd' never matched." in output
    assert "Warning: modification directive #measurement.formula.regex-unique.r'ghjk' never matched." in output
        
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "C5H8O4"
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "C5H8O4"
    
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0"
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1"
    
    assert output_json["measurement"]["asdf-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "qwer"
    
    assert output_json["measurement"]["zxcv-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "zxcv-13C0"
    assert output_json["measurement"]["zxcv-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "zxcv-13C1"


def test_modification_comparison_type_regex_first_test():
    """Test that only the first values are changed when #match=first."""
    
    test_file = "modification_comparison_type_regex_first_test.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    assert "Warning: modification directive #measurement.compound.regex-first.r'\\(S\\)\\-2\\-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd' matches more than one record. Only the first record will be changed. Try #match=all if all matching records should be changed, or #match=first-nowarn to silence this message." in output
    assert "Warning: modification directive #measurement.formula.regex-first.r'qwer' matches more than one record. Only the first record will be changed. Try #match=all if all matching records should be changed, or #match=first-nowarn to silence this message." in output
        
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "asdf"
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "C5H8O4"
    
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "asdf"
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1"
    
    assert output_json["measurement"]["asdf-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "qwer"
    assert output_json["measurement"]["asdf-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "asdf-13C1"
    
    
def test_modification_comparison_type_regex_first_nowarn_test():
    """Test that only the first values are changed when #match=first-nowarn and no message is printed."""
    
    test_file = "modification_comparison_type_regex_first-nowarn_test.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    assert output == ""
        
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "asdf"
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "C5H8O4"
    
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "asdf"
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1"
    
    assert output_json["measurement"]["asdf-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "qwer"


def test_modification_comparison_type_regex_all_test():
    """Test that all values are changed when #match=all and no message is printed."""
    
    test_file = "modification_comparison_type_regex_all_test.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    assert output == ""
        
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "asdf"
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "asdf"
    
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "asdf"
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "asdf"
    
    assert output_json["measurement"]["asdf-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "qwer"



def test_modification_comparison_type_levenshtein_unique_test():
    """Test that values are only changed if it is unique when #match=unique."""
    
    test_file = "modification_comparison_type_levenshtein_unique_test.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    assert "Warning: modification directive #measurement.compound.levenshtein-unique.(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd never matched." in output
        
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "C5H8O4"
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "C5H8O4"
    
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0"
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1"
    
    assert output_json["measurement"]["asdf-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "qwer"


def test_modification_comparison_type_levenshtein_first_test():
    """Test that only the first values are changed when #match=first."""
    
    test_file = "modification_comparison_type_levenshtein_first_test.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    assert "Warning: modification directive #measurement.compound.levenshtein-first.(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd matches more than one record. Only the first record will be changed. Try #match=all if all matching records should be changed, or #match=first-nowarn to silence this message." in output
        
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "asdf"
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "C5H8O4"
    
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "asdf"
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1"
    
    assert output_json["measurement"]["asdf-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "qwer"
    
    
def test_modification_comparison_type_levenshtein_first_nowarn_test():
    """Test that only the first values are changed when #match=first-nowarn and no message is printed."""
    
    test_file = "modification_comparison_type_levenshtein_first-nowarn_test.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    assert output == ""
        
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "asdf"
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "C5H8O4"
    
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "asdf"
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1"
    
    assert output_json["measurement"]["asdf-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "qwer"


def test_modification_comparison_type_levenshtein_all_test():
    """Test that all values are changed when #match=all and no message is printed."""
    
    test_file = "modification_comparison_type_levenshtein_all_test.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    assert output == ""
        
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "asdf"
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "asdf"
    
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "asdf"
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "asdf"
    
    assert output_json["measurement"]["asdf-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "qwer"



def test_modification_match_tag_inline_error():
    """Test that an error is printed when #match=asdf."""
    
    test_file = "modification_match_tag_inline_error.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
    
    assert 'Unknown match type "asdf" at cell' in output
    assert "modification_match_tag_inline_error.xlsx:#modify[D1]" in output


def test_modification_match_per_row():
    """Test that #match with values for each line works."""
    
    test_file = "modification_match_per_row.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    assert "Warning: modification directive #measurement.compound.exact-first.(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd matches more than one record. Only the first record will be changed. Try #match=all if all matching records should be changed, or #match=first-nowarn to silence this message." in output
        
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "asdf"
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "C5H8O4"
    
    assert output_json["measurement"]["asdf-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "zxcv"
    assert output_json["measurement"]["asdf-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "zxcv"


def test_modification_match_per_row_error():
    """Test that an error is printed when #match has a bad value."""
    
    test_file = "modification_match_per_row_error.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
    
    assert 'Unknown match type "asdf" at cell' in output
    assert "modification_match_per_row_error.xlsx:#modify[D2]" in output



def test_modification_field_creation():
    """Test that the field is created if it does not exist for assign, append, and prepend."""
    
    test_file = "modification_field_creation.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    assert output == ""
        
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["new_assign_field"] == "asdf"
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["new_assign_list_field"] == ["asdf"]
    
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["new_append_field"] == "asdf"
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["new_append_list_field"] == ["asdf"]
    
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["new_prepend_field"] == "asdf"
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["new_prepend_list_field"] == ["asdf"]




def test_modification_assign_list_field_test():
    """Test that field is overwritten to and from list field type."""
    
    test_file = "modification_assign_list_field_test.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    assert output == ""
        
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["compound"] == "asdf"
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == ["asdf"]
    
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["compound"] == "asdf"
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == ["asdf"]
 
    
 
def test_modification_append_list_field_test():
    """Test that append works with list fields correctly."""
    
    test_file = "modification_append_list_field_test.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    assert output == ""
        
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["compound"] == ["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStdasdf", "asdfasdf"]
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == ["C5H8O4asdf", "qwerqwer"]
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C0asdf"
    
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["compound"] == ["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStdasdf", "asdfasdf"]
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == ["C5H8O4asdf", "qwerqwer"]
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C1asdf"




def test_modification_prepend_list_field_test():
    """Test that prepend works with list fields correctly."""
    
    test_file = "modification_prepend_list_field_test.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    assert output == ""
        
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["compound"] == ["asdf(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd", "asdfasdf"]
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == ["asdfC5H8O4", "qwerqwer"]
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "asdf(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C0"

    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["compound"] == ["asdf(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd", "asdfasdf"]
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == ["asdfC5H8O4", "qwerqwer"]
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["assignment"] == "asdf(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C1"



def test_modification_regex_list_field_test():
    """Test that regex works with list fields correctly."""
    
    test_file = "modification_regex_list_field_test.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    assert output == ""
        
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["compound"] == ["(S)-2-Acetolqwerctqwerte_Glutqwerric qwercid_Methylsuccinic qwercid_MP_NoStd", "qwersdf"]

    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["compound"] == ["(S)-2-Acetolqwerctqwerte_Glutqwerric qwercid_Methylsuccinic qwercid_MP_NoStd", "qwersdf"]



def test_modification_levenshtein_list_field_test():
    """Test that levenshtein works with list fields correctly."""
    
    test_file = "modification_levenshtein_list_field_test.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    assert output == ""
        
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "zxcv"

    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "zxcv"




def test_modification_semicolon_list_field_test():
    """Test that semicolon separators work."""
    
    test_file = "modification_semicolon_list_field_test.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    assert output == ""
        
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == ["preasdfapp", "pre2qwerapp2"]
    
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd,asdf-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == ["preasdfapp", "pre2qwerapp2"]



def test_modification_ignore_test():
    """Test that #ignore works."""
    
    test_file = "modification_ignore_test.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    assert output == ""
        
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "qwer"
    
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "qwer"




def test_modification_unused_test():
    """Test that nothing is printed when there is an unused modification in an individual metadata that is then used in end-modify."""
    
    test_file = "modification_unused_test.xlsx"
    
    command = "messes extract ../" + test_file + " ../base_source_export.csv" + " --output " + output_path.as_posix() + " --end-modify ../" + test_file + ":#modify"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    assert output == ""




def test_modification_id_change():
    """Test that a warning is printed when the modification changes 2 or more records to the same id."""
    
    test_file = "modification_error.xlsx"
    
    command = "messes extract ../" + test_file +" --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output_path.exists()
    
    assert output == "Warning: A modification directive has set at least 2 records in the \"measurement\" table to the same id. The output will have less records than expected." + "\n"




def test_eval_in_modification():
    """Test that eval works in modifications."""
    
    test_file = "eval_in_modification.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
                                
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["asdf"] == "5217592.617829667"
    
    assert output == ""



    
def test_eval_in_modification_error():
    """Test that a message is printed when there is a bad regex in eval for modifications."""
    
    test_file = "eval_in_modification_error.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
                                
    assert not "asdf" in output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]
    
    assert output == "Warning: Field assignment directive \"asdf\" missing required field(s) \"\", or a regular expression matched no fields or more than one.\nWarning: Field assignment directive \"asdf\" missing required field(s) \"\", or a regular expression matched no fields or more than one." + "\n"



def test_list_in_eval_list_tag_modification():
    """Test that a list in eval with list tag in modification is turned into a list of strings."""
    
    test_file = "list_eval_in_modification_list_tag.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
                                
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["asdf"] == ["asdf", "qwer"]
    
    assert output == ""
    
 
    
def test_list_in_eval_modification():
    """Test that a list in eval in modification is turned into a list of strings."""
    
    test_file = "list_eval_in_modification.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
                                
    assert output_json["measurement"]["(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["asdf"] == ["asdf", "qwer"]
    
    assert output == ""
    


    
def test_unused_modification():
    """Test that a warning is printed when there is an unused modification."""
    
    test_file = "unused_modification.xlsx"
    
    command = "messes extract ../" + test_file +" --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    assert output == "Warning: modification directive #measurement.compound.exact-all.asdf never matched." + "\n"
    



def test_field_name_in_eval():
    """Test that using a field in eval works."""
    
    test_file = "modification_field_name_in_eval.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
                                
    assert output_json["sample"]["01_A0_Spleen_naive_0days_170427_UKy_GCH_rep1"]["asdf"] == "zxcv cvbn"
    
    assert output == ""



def test_regex_in_eval():
    """Test that using a regex in eval works."""
    
    test_file = "modification_regex_in_eval.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
                                
    assert output_json["sample"]["01_A0_Spleen_naive_0days_170427_UKy_GCH_rep1"]["asdf"] == "zxcv cvbn"
    
    assert output == ""



