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



    
def test_multiple_inserts():
    """Test that #insert in a #tags block is inserted multiple times when #multiple=true."""
    
    test_file = "multiple_inserts.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix() + " --save-export csv"
    os.system(command)
    
    assert output_path.exists()
    test_file = pathlib.Path(test_file)
    test_file_export = pathlib.Path(test_file.stem + "_export.csv")
    assert test_file_export.exists()
    
    export = pandas.read_csv(test_file_export, header=None)
    ## There should be 4 #tags in column 0.
    assert export.iloc[:,0].value_counts()["#tags"] == 4
    
    if test_file_export.exists():
        os.remove(test_file_export)
        time_to_wait=10
        time_counter = 0
        while test_file_export.exists():
            time.sleep(1)
            time_counter += 1
            if time_counter > time_to_wait:
                raise FileExistsError(test_file_export.as_posix() + " was not deleted within " + str(time_to_wait) + " seconds, so it is assumed that it won't be and something went wrong.")



def test_duplicate_headers():
    """Test that a warning is printed when there are duplicate headers. Ex: id and compound both set to the same column."""
    
    test_file = "duplicate_headers.xlsx"
    
    command = "messes extract ../" + test_file +" --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    assert output == "\'Warning: duplicate header description provided in automation directive at cell \"../duplicate_headers.xlsx:#automate[:11]\"\'" + "\n"




def test_missing_id_in_header():
    """Test that a warning is printed when there is not an id tag in the header."""
    
    test_file = "no_id_tag.xlsx"
    
    command = "messes extract ../" + test_file +" --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    assert output == "Warning: The header row at index 0 in the compiled export sheet does not have an \"id\" tag, so it will not be in the JSON output." + "\n"




def test_unused_tag():
    """Test that a warning is printed when there is an unused tag."""
    
    test_file = "unused_tag.xlsx"
    
    command = "messes extract ../" + test_file +" --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    assert output == "Warning: Automation directive number 1 was never used." + "\n"



    
def test_no_required_headers():
    """Test that nothing is printed when no headers are required."""
    
    test_file = "no_required_headers.xlsx"
    
    command = "messes extract ../" + test_file +" --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    with open(output_compare_path, "r") as f:
        output_compare_json = json.loads(f.read())
        
    assert output_json == output_compare_json
    
    assert output == ""




def test_duplicate_columns():
    """Test that a warning is printed when there are duplicate columns."""
    
    test_file = "duplicate_columns.xlsx"
    
    command = "messes extract ../" + test_file +" --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    assert output == "Warning: The header, Intensity, in automation group, 1, was matched to more than 1 column near or on row, 4, in the tagged export.\nWarning: Automation directive number 1 was never used." + "\n"




def test_regex_in_eval():
    """Test that a regex inside an eval works."""
    
    test_file = "regex_in_eval.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("output_compare.json"), "r") as f:
        output_compare_json = json.loads(f.read())
                        
    assert output_json == output_compare_json
    
    assert output == ""




def test_list_in_eval():
    """Test that a list in eval is turned into semicolon separated string."""
    
    test_file = "eval_list.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
                                
    assert output_json["measurement"]["(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["asdf"] == "asdf;qwer"
    
    assert output == ""



def test_list_in_eval_list_tag():
    """Test that a list in eval with list tag is turned into a list of strings."""
    
    test_file = "eval_list_list_tag.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
                                
    assert output_json["measurement"]["(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["asdf"] == ["asdf", "qwer"]
    
    assert output == ""
    




def test_exclusion():
    """Test that exclusion tag works."""
    
    test_file = "exclusion_test.xlsx"
    
    command = "messes extract ../" + test_file +" --output " + output_path.as_posix()
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
    
    assert output == "Warning: Automation directive number 1 was never used." + "\n"
  

        
    
def test_multiple_insert_blocks():
    """Test that all #insert blocks are added in the export."""
    
    test_file = "multiple_insert_blocks.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix() + " --save-export csv"
    os.system(command)
    
    assert output_path.exists()
    test_file = pathlib.Path(test_file)
    test_file_export = pathlib.Path(test_file.stem + "_export.csv")
    assert test_file_export.exists()
    
    export = pandas.read_csv(test_file_export, header=None)
    ## There should be 5 #tags in column 0.
    assert export.iloc[:,0].value_counts()["#tags"] == 5
    
    if test_file_export.exists():
        os.remove(test_file_export)
        time_to_wait=10
        time_counter = 0
        while test_file_export.exists():
            time.sleep(1)
            time_counter += 1
            if time_counter > time_to_wait:
                raise FileExistsError(test_file_export.as_posix() + " was not deleted within " + str(time_to_wait) + " seconds, so it is assumed that it won't be and something went wrong.")

    


def test_automation_empty_tag_rows():
    """Test that a #tags row directly after a #tags row doesn't affect the output."""
    
    test_file = "automation_empty_tag_rows.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("output_compare.json"), "r") as f:
        output_compare_json = json.loads(f.read())
        
    assert output_json == output_compare_json
    
    assert output == ""
    
    

def test_automation_missing_header_tag_error():
    """Test that an error is printed when the #header tag is missing."""
    
    test_file = "automation_missing_header_tag_error.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
    
    assert 'Missing #header tag at cell' in output
    assert "automation_missing_header_tag_error.xlsx:#automate[:8]" in output
    
    
def test_automation_missing_add_tag_error():
    """Test that an error is printed when the #tag.add tag is missing."""
    
    test_file = "automation_missing_add_tag_error.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
    
    assert 'Missing #add tag at cell' in output
    assert "automation_missing_add_tag_error.xlsx:#automate[:8]" in output




def test_automation_ignore_test():
    """Test that a #ignore row doesn't affect the output."""
    
    test_file = "automation_ignore_test.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("output_compare.json"), "r") as f:
        output_compare_json = json.loads(f.read())
        
    assert output_json == output_compare_json
    
    assert output == ""
    
    
    
def test_automation_insert_multiple_false_test():
    """Test that a #multiple=false is the same as default."""
    
    test_file = "automation_insert_multiple_false_test.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("output_compare.json"), "r") as f:
        output_compare_json = json.loads(f.read())
        
    assert output_json == output_compare_json
    
    assert output == ""
    
    
    
def test_automation_missing_end_tag_error():
    """Test that an error is printed when the #end tag is missing."""
    
    test_file = "automation_missing_end_tag_error.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
    
    assert 'Missing #end tag at cell' in output
    assert "automation_missing_end_tag_error.xlsx:#automate[Q21]" in output



def test_automation_field_tracking():
    """Test that field tracking and untracking works."""
    
    test_file = "tracking_test.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
                
    assert output_json["sample"]["01_A0_Spleen_naive_0days_170427_UKy_GCH_rep1"]["project.id"] == "Project1"
    assert output_json["sample"]["02_A1_Spleen_naive_0days_170427_UKy_GCH_rep2"]["project.id"] == "Project1"
    assert output_json["sample"]["01_A0_Spleen_naive_0days_170427_UKy_GCH_rep1"]["project.id%number"] == "1"
    assert output_json["sample"]["02_A1_Spleen_naive_0days_170427_UKy_GCH_rep2"]["project.id%number"] == "1"
    
    assert output_json["sample"]["03_A0_Spleen_naive_0days_170427_UKy_GCH_rep1"]["project.id%number"] == "1"
    assert output_json["sample"]["04_A1_Spleen_naive_0days_170427_UKy_GCH_rep2"]["project.id%number"] == "1"
    assert "project.id" not in output_json["sample"]["03_A0_Spleen_naive_0days_170427_UKy_GCH_rep1"]
    assert "project.id" not in output_json["sample"]["04_A1_Spleen_naive_0days_170427_UKy_GCH_rep2"]
    
    assert output == ""
    
    
def test_automation_field_tracking2():
    """Test that field tracking and untracking works."""
    
    test_file = "tracking_test2.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
                
    assert output_json["sample"]["01_A0_Spleen_naive_0days_170427_UKy_GCH_rep1"]["project.id"] == "Project1"
    assert output_json["sample"]["02_A1_Spleen_naive_0days_170427_UKy_GCH_rep2"]["project.id"] == "Project1"
    assert output_json["sample"]["01_A0_Spleen_naive_0days_170427_UKy_GCH_rep1"]["project.id%number"] == "1"
    assert output_json["sample"]["02_A1_Spleen_naive_0days_170427_UKy_GCH_rep2"]["project.id%number"] == "1"
    
    assert output_json["sample"]["03_A0_Spleen_naive_0days_170427_UKy_GCH_rep1"]["project.id%number"] == "1"
    assert output_json["sample"]["04_A1_Spleen_naive_0days_170427_UKy_GCH_rep2"]["project.id%number"] == "1"
    assert "project.id" not in output_json["sample"]["03_A0_Spleen_naive_0days_170427_UKy_GCH_rep1"]
    assert "project.id" not in output_json["sample"]["04_A1_Spleen_naive_0days_170427_UKy_GCH_rep2"]
    
    assert output == ""


def test_automation_field_tracking3():
    """Test that field tracking and untracking works."""
    
    test_file = "tracking_test3.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
    
    assert output_json["factor"]["01_A0_Spleen_naive_0days_170427_UKy_GCH_rep1"]["project.id"] == "Project1"
    assert output_json["factor"]["02_A1_Spleen_naive_0days_170427_UKy_GCH_rep2"]["project.id"] == "Project1"
    assert output_json["factor"]["01_A0_Spleen_naive_0days_170427_UKy_GCH_rep1"]["project.id%number"] == "1"
    assert output_json["factor"]["02_A1_Spleen_naive_0days_170427_UKy_GCH_rep2"]["project.id%number"] == "1"
            
    assert output_json["sample"]["01_A0_Spleen_naive_0days_170427_UKy_GCH_rep1"]["project.id"] == "Project1"
    assert output_json["sample"]["02_A1_Spleen_naive_0days_170427_UKy_GCH_rep2"]["project.id"] == "Project1"
    assert output_json["sample"]["01_A0_Spleen_naive_0days_170427_UKy_GCH_rep1"]["project.id%number"] == "1"
    assert output_json["sample"]["02_A1_Spleen_naive_0days_170427_UKy_GCH_rep2"]["project.id%number"] == "1"
    
    assert output_json["sample"]["03_A0_Spleen_naive_0days_170427_UKy_GCH_rep1"]["project.id%number"] == "1"
    assert output_json["sample"]["04_A1_Spleen_naive_0days_170427_UKy_GCH_rep2"]["project.id%number"] == "1"
    assert "project.id" not in output_json["sample"]["03_A0_Spleen_naive_0days_170427_UKy_GCH_rep1"]
    assert "project.id" not in output_json["sample"]["04_A1_Spleen_naive_0days_170427_UKy_GCH_rep2"]
    
    assert output == ""


def test_automation_tracking_not_enough_tokens_error():
    """Test that an error is printed when there are not enough tokens in track tag."""
    
    test_file = "tracking_not_enough_tokens_error.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
    
    assert 'Incorrectly formatted track tag, "=" must follow "track" and "table.field" or "table.field%attribute" must follow "=" at cell' in output
    assert "tracking_not_enough_tokens_error.xlsx:#export[B1]" in output


def test_automation_tracking_no_equal_sign_error():
    """Test that an error is printed when there is no = after the track tag."""
    
    test_file = "tracking_no_equal_sign_error.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
    
    assert 'Incorrectly formatted track tag, "=" must follow "track" and "table.field" or "table.field%attribute" must follow "=" at cell' in output
    assert "tracking_no_equal_sign_error.xlsx:#export[B1]" in output


def test_automation_untracking_no_equal_sign_error():
    """Test that an error is printed when there is no = after the untrack tag."""
    
    test_file = "untracking_no_equal_sign_error.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
    
    assert 'Incorrectly formatted untrack tag, "=" must follow "untrack" and "table.field" or "table.field%attribute" must follow "=" at cell' in output
    assert "untracking_no_equal_sign_error.xlsx:#export[B14]" in output


def test_automation_untracking_not_enough_tokens_error():
    """Test that an error is printed when there are not enough tokens in untrack tag."""
    
    test_file = "untracking_not_enough_tokens_error.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
    
    assert 'Incorrectly formatted untrack tag, "=" must follow "untrack" and "table.field" or "table.field%attribute" must follow "=" at cell' in output
    assert "untracking_not_enough_tokens_error.xlsx:#export[B14]" in output


def test_automation_tracking_malformed_field_error():
    """Test that an error is printed when the field to track is malformed."""
    
    test_file = "tracking_malformed_field_error.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
    
    assert 'Incorrectly formatted track tag, the field or attribute to be tracked is malformed, must be "table.field" or "table.field%attribute" at cell' in output
    assert "tracking_malformed_field_error.xlsx:#export[B1]" in output
    

def test_automation_untracking_malformed_field_error():
    """Test that an error is printed when the field to untrack is malformed."""
    
    test_file = "untracking_malformed_field_error.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
    
    assert 'Incorrectly formatted untrack tag, the field or attribute to be tracked is malformed, must be "table.field" or "table.field%attribute" at cell' in output
    assert "untracking_malformed_field_error.xlsx:#export[B14]" in output


def test_automation_tracking_list_test():
    """Test that field tracking works with a list of values."""
    
    test_file = "tracking_list_test.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
                
    assert output_json["sample"]["01_A0_Spleen_naive_0days_170427_UKy_GCH_rep1"]["project.id"] == "Project1"
    assert output_json["sample"]["02_A1_Spleen_naive_0days_170427_UKy_GCH_rep2"]["project.id"] == "Project1"
    assert output_json["sample"]["01_A0_Spleen_naive_0days_170427_UKy_GCH_rep1"]["project.id%number"] == "1"
    assert output_json["sample"]["02_A1_Spleen_naive_0days_170427_UKy_GCH_rep2"]["project.id%number"] == "1"
    
    assert "project.id%number" not in output_json["sample"]["03_A0_Spleen_naive_0days_170427_UKy_GCH_rep1"]
    assert "project.id%number" not in output_json["sample"]["04_A1_Spleen_naive_0days_170427_UKy_GCH_rep2"]
    assert "project.id" not in output_json["sample"]["03_A0_Spleen_naive_0days_170427_UKy_GCH_rep1"]
    assert "project.id" not in output_json["sample"]["04_A1_Spleen_naive_0days_170427_UKy_GCH_rep2"]
    
    assert output == ""



def test_automation_spaces_in_header():
    """Test that headers with spaces in them are matched without regex."""
    
    test_file = "automation_spaces_in_header_test.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("output_compare.json"), "r") as f:
        output_compare_json = json.loads(f.read())
        
    assert output_json == output_compare_json
            
    assert output == ""


def test_automation_transpose():
    """Test that the #transpose works in automate."""
    
    test_file = "automation_transpose.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("output_compare2.json"), "r") as f:
        output_compare_json = json.loads(f.read())
        
    assert output_json == output_compare_json
            
    assert output == ""


def test_automation_header_and_increment():
    """Test that the #HEADER# and #INCREMENT# keywords work in automate."""
    
    test_file = "automation_header_and_increment.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("output_compare3.json"), "r") as f:
        output_compare_json = json.loads(f.read())
        
    assert output_json == output_compare_json
            
    assert output == ""


def test_automation_filter():
    """Test that the #filter works in automate."""
    
    test_file = "automation_filter.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("output_compare4.json"), "r") as f:
        output_compare_json = json.loads(f.read())
        
    assert output_json == output_compare_json
            
    assert output == ""


def test_automation_sort():
    """Test that the #sort works in automate."""
    
    test_file = "automation_sort.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("output_compare5.json"), "r") as f:
        output_compare_json = json.loads(f.read())
        
    assert output_json == output_compare_json
            
    assert output == ""


def test_automation_sort_bad_tag():
    """Test that a badly constructed #sort tag produces an error."""
    
    test_file = "automation_sort_bad_tag.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
            
    assert ('Exception: Error: A #sort tag in automation group 0 has a badly '
            'constructed header:sortorder pair, asdf:qwer:zxcv. It should be '
            'of the form "header:ascending" or "header:descending". Put double '
            'quotes around the header if it contains a colon.') in output


def test_automation_sort_header_not_found():
    """Test that when a header in #sort is not found it produces an error."""
    
    test_file = "automation_sort_header_not_found.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
            
    assert ("Error: The following header(s) in the #sort tag of automation group 0 were not found in the data: ['asdf']") in output


def test_automation_filter_bad_tag():
    """Test that a badly constructed #filter tag produces an error."""
    
    test_file = "automation_filter_bad_tag.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
            
    assert ('Error: A #filter tag in automation group 0 has a badly constructed '
            'header:filter pair, asdf:zxcv:qwer:unique. It should be of the form '
            '"header:filter". Put double quotes around the header or filter if it contains a colon.') in output


def test_automation_filter_header_not_found():
    """Test that when a header in #filter is not found it produces an error."""
    
    test_file = "automation_filter_header_not_found.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
            
    assert ("Error: The following header(s) in the #filter tag of automation group 0 were not found in the data: ['asdf']") in output


def test_automation_sort_not_copy_error():
    """Test that when #copy is not given with #sort it produces an error."""
    
    test_file = "automation_sort_no_copy.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
            
    assert ('"#copy" must be specified in #tags column if "#sort" is specified. ') in output


def test_automation_filter_not_copy_error():
    """Test that when #copy is not given with #filter it produces an error."""
    
    test_file = "automation_filter_no_copy.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
            
    assert ('"#copy" must be specified in #tags column if "#filter" is specified. ') in output
