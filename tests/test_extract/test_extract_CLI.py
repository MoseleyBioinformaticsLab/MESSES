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



def test_compare():
    """Test that the compare option works."""
    
    test_file = "base_source.xlsx"
    
    command = "messes extract ../" + test_file +" --output " + output_path.as_posix() + " --compare " + output_compare_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stdout

    
    assert output_path.exists()
        
    assert output == "Comparison\nNo differences detected." + "\n"
    
    

def test_modify_worksheet_name():
    """Test that the modify option works with a worksheet name."""
    
    test_file = "modification_test.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix() + " --modify modify"
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


def test_modification_regex():
    """Test that the modify option works with a regex."""
    
    test_file = "modification_test.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix() + " --modify r'.*dify'"
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


def test_modification_csv():
    """Test that the modify option works with a csv file."""
    
    test_file = "modification_test.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix() + " --modify ../modifications.csv"
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
    
    
def test_modification_json():
    """Test that the modify option works with a JSON file."""
    
    test_file = "modification_test.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix() + " --modify ../base_directives.json"
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
    
    
def test_modification_worksheet_name_and_sheetname():
    """Test that the modify option works with worksheet:sheetname."""
    
    test_file = "modification_test.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix() + " --modify ../base_source.xlsx:#modify"
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
    
    
def test_modification_worksheet_name_and_regex():
    """Test that the modify option works with worksheet:regex."""
    
    test_file = "modification_test.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix() + " --modify ../base_source.xlsx:r'.*dify'"
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
    
    
def test_modification_xlsx():
    """Test that the modify option defaults to #modify."""
    
    test_file = "modification_test.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix() + " --modify ../base_source.xlsx"
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


def test_modification_Google_Sheets():
    """Test that the modify option defaults to #modify."""
    
    test_file = "modification_test.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix() + " --modify https://docs.google.com/spreadsheets/d/1g3xM2GW3gYiwDY815LFC5mdaYEJFU49V4AIiobvwP0c/edit?usp=sharing"
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





def test_end_modify_csv():
    """Test that the end-modify option works with a csv file."""
    
    test_file = "modification_test.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix() + " --end-modify ../modifications.csv"
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
    
    
def test_end_modify_json():
    """Test that the end-modify option works with a JSON file."""
    
    test_file = "modification_test.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix() + " --end-modify ../base_directives.json"
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
    
    
def test_end_modify_worksheet_name_and_sheetname():
    """Test that the end-modify option works with worksheet:sheetname."""
    
    test_file = "modification_test.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix() + " --end-modify ../base_source.xlsx:#modify"
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
    
    
def test_end_modify_Google_Sheets_name_and_sheetname():
    """Test that the end-modify option works with worksheet:sheetname."""
    
    test_file = "modification_test.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix() + " --end-modify https://docs.google.com/spreadsheets/d/1g3xM2GW3gYiwDY815LFC5mdaYEJFU49V4AIiobvwP0c/edit?usp=sharing:#modify"
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
    

def test_end_modify_Google_Sheets_default_name():
    """Test that the end-modify option works with worksheet:sheetname."""
    
    test_file = "modification_test.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix() + " --end-modify https://docs.google.com/spreadsheets/d/1g3xM2GW3gYiwDY815LFC5mdaYEJFU49V4AIiobvwP0c/edit?usp=sharing"
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
    
    
def test_end_modify_worksheet_name_and_regex():
    """Test that the end-modify option works with worksheet:regex."""
    
    test_file = "modification_test.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix() + " --end-modify ../base_source.xlsx:r'.*ify'"
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




def test_end_modify():
    """Test that the end-modify option works."""
    
    test_file_1 = "end_modify_1.xlsx"
    test_file_2 = "end_modify_2.xlsx"
    test_file_3 = "end_modify_3_modification.xlsx"
    
    command = "messes extract ../" + test_file_1 + " ../" + test_file_2 +" --output " + output_path.as_posix() + " --end-modify ../" + test_file_3
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("end_modify_compare.json"), "r") as f:
        output_compare_json = json.loads(f.read())
        
    assert output_json == output_compare_json
    
    assert output == ""




def test_automate_worksheet_name():
    """Test that the automate option works with a worksheet name."""
    
    test_file = "automation_test.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix() + " --automate automate"
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


def test_automation_regex():
    """Test that the automate option works with a regex."""
    
    test_file = "automation_test.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix() + " --automate r'.*mate'"
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


def test_automation_csv():
    """Test that the automate option works with a csv file."""
    
    test_file = "automation_test.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix() + " --automate ../tags.csv"
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
    
    
def test_automation_json():
    """Test that the automate option works with a JSON file."""
    
    test_file = "automation_test.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix() + " --automate ../base_directives.json"
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
    
    
def test_automation_worksheet_name_and_sheetname():
    """Test that the automate option works with worksheet:sheetname."""
    
    test_file = "automation_test.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix() + " --automate ../base_source.xlsx:#automate"
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
    
    
def test_automation_worksheet_name_and_regex():
    """Test that the automate option works with worksheet:regex."""
    
    test_file = "automation_test.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix() + " --automate ../base_source.xlsx:r'.*mate'"
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
    
    
def test_automation_xlsx():
    """Test that the automate option defaults to #automate for just a filename."""
    
    test_file = "automation_test.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix() + " --automate ../base_source.xlsx"
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





def test_save_directives():
    """Test that the save-directives option works."""
    
    test_file = "base_source.xlsx"
    directives_to_compare = "comparison_directives.json"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix() + " --save-directives " + directives_to_compare
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
    
    
    with open(pathlib.Path("base_directives.json"), "r") as f:
        base_directives_json = json.loads(f.read())
    
    directives_to_compare = pathlib.Path(directives_to_compare)
    assert directives_to_compare.exists()
    with open(directives_to_compare, "r") as f:
        directives_to_compare_json = json.loads(f.read())
        
    assert base_directives_json == directives_to_compare_json
    
    
    if directives_to_compare.exists():
        os.remove(directives_to_compare)
        time_to_wait=10
        time_counter = 0
        while directives_to_compare.exists():
            time.sleep(1)
            time_counter += 1
            if time_counter > time_to_wait:
                raise FileExistsError(directives_to_compare.as_posix() + " was not deleted within " + str(time_to_wait) + " seconds, so it is assumed that it won't be and something went wrong.")



def test_save_directives_no_json():
    """Test that the save-directives option adds .json to output if not there."""
    
    test_file = "base_source.xlsx"
    directives_to_compare = "comparison_directives"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix() + " --save-directives " + directives_to_compare
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    directives_to_compare = "comparison_directives.json"

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("output_compare.json"), "r") as f:
        output_compare_json = json.loads(f.read())
        
    assert output_json == output_compare_json
    
    assert output == ""
    
    
    with open(pathlib.Path("base_directives.json"), "r") as f:
        base_directives_json = json.loads(f.read())
    
    directives_to_compare = pathlib.Path(directives_to_compare)
    assert directives_to_compare.exists()
    with open(directives_to_compare, "r") as f:
        directives_to_compare_json = json.loads(f.read())
        
    assert base_directives_json == directives_to_compare_json
    
    
    if directives_to_compare.exists():
        os.remove(directives_to_compare)
        time_to_wait=10
        time_counter = 0
        while directives_to_compare.exists():
            time.sleep(1)
            time_counter += 1
            if time_counter > time_to_wait:
                raise FileExistsError(directives_to_compare.as_posix() + " was not deleted within " + str(time_to_wait) + " seconds, so it is assumed that it won't be and something went wrong.")




def test_save_directives_none_to_save():
    """Test that the save-directives option prints a message if there are none to save."""
    
    test_file = "no_directives.csv"
    directives_to_compare = "comparison_directives.json"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix() + " --save-directives " + directives_to_compare
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    
    assert output_path.exists()
        
    assert output == "There are no directives to save." + "\n"
    
    


def test_save_export_xlsx():
    """Test that the save-export option works for Excel type."""
    
    test_file = "base_source.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix() + " --save-export xlsx"
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
    
    test_file = pathlib.Path(test_file)
    saved_export = pathlib.Path("../" + test_file.stem + "_export.xlsx")
    saved_export_df = pandas.read_excel(saved_export, header=None)
    
    test_file_export = pathlib.Path(test_file.stem + "_export.xlsx")
    assert test_file_export.exists()
    export_df = pandas.read_excel(test_file_export, header=None)
    
    assert saved_export_df.equals(export_df)
        
            
    if test_file_export.exists():
        os.remove(test_file_export)
        time_to_wait=10
        time_counter = 0
        while test_file_export.exists():
            time.sleep(1)
            time_counter += 1
            if time_counter > time_to_wait:
                raise FileExistsError(test_file_export.as_posix() + " was not deleted within " + str(time_to_wait) + " seconds, so it is assumed that it won't be and something went wrong.")



def test_save_export_csv():
    """Test that the save-export option works for csv type."""
    
    test_file = "base_source.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix() + " --save-export csv"
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
    
    test_file = pathlib.Path(test_file)
    saved_export = pathlib.Path("../" + test_file.stem + "_export.csv")
    with open(saved_export) as saved_export_handle:
        saved_export_df = pandas.read_csv(saved_export_handle, header=None)
    
    test_file_export = pathlib.Path(test_file.stem + "_export.csv")
    assert test_file_export.exists()
    export_df = pandas.read_csv(test_file_export, header=None)
    
    assert saved_export_df.equals(export_df)
        
            
    if test_file_export.exists():
        os.remove(test_file_export)
        time_to_wait=10
        time_counter = 0
        while test_file_export.exists():
            time.sleep(1)
            time_counter += 1
            if time_counter > time_to_wait:
                raise FileExistsError(test_file_export.as_posix() + " was not deleted within " + str(time_to_wait) + " seconds, so it is assumed that it won't be and something went wrong.")



def test_show_tables():
    """Test that the show option works for the tables sub option."""
    
    test_file = "base_source.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix() + " --show tables"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stdout

    
    assert output_path.exists()
        
    assert output == "Tables:  protocol measurement" + "\n"
    
    
def test_show_lineage():
    """Test that the show option works for the lineage sub option."""
    
    test_file = "base_source.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix() + " --show lineage"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stdout

    
    assert output_path.exists()
        
    assert output == ' protocol :\n   IC-FTMS_measurement :\n     ICMS1' + "\n"


def test_show_lineage_with_children():
    """Test that the show option works for the lineage sub option with child records."""
    
    test_file = "child_tag_example.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix() + " --show lineage"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stdout

    
    assert output_path.exists()
        
    assert output == ' sample :\n   01_A0_Spleen_naive_0days_170427_UKy_GCH_rep1 :\n     01_A0_Spleen_naive_0days_170427_UKy_GCH_rep1-protein\n   02_A1_Spleen_naive_0days_170427_UKy_GCH_rep2 :\n     02_A1_Spleen_naive_0days_170427_UKy_GCH_rep2-protein' + "\n"
    
    
def test_show_all():
    """Test that the show option works for the all sub option."""
    
    test_file = "base_source.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix() + " --show all"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stdout

    
    assert output_path.exists()
        
    assert output == "Tables:  protocol measurement\n" + ' protocol :\n   IC-FTMS_measurement :\n     ICMS1' + "\n"
    
    
def test_show_incorrect_sub_option():
    """Test that the show option prints an error for an incorrect sub option."""
    
    test_file = "base_source.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix() + " --show asdf"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
        
    assert output == "Unknown sub option for \"--show\" option: \"asdf\"" + "\n"
    


def test_delete():
    """Test that the delete option works."""
    
    test_file = "base_source.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix() + ' --delete protocol'
    command = command.split(" ")
    command.append("--delete")
    command.append("measurement,(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench")
    command.append("--delete")
    command.append("measurement,(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench,compound")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("output_compare.json"), "r") as f:
        output_compare_json = json.loads(f.read())
        
    del output_compare_json["protocol"]
    del output_compare_json["measurement"]["(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]
    del output_compare_json["measurement"]["(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["compound"]
        
    assert output_json == output_compare_json
    
    assert output == ""



def test_delete_regex():
    """Test that the delete option works with regex."""
    
    test_file = "base_source.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix() + ' --delete r\'.*tocol\''
    command = command.split(" ")
    command.append("--delete")
    command.append("r\'.*asurement\',r\'.*13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench\'")
    command.append("--delete")
    command.append("measurement,(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench,r\'.*pound\'")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("output_compare.json"), "r") as f:
        output_compare_json = json.loads(f.read())
        
    del output_compare_json["protocol"]
    del output_compare_json["measurement"]["(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]
    del output_compare_json["measurement"]["(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["compound"]
        
    assert output_json == output_compare_json
    
    assert output == ""
    
    
    
def test_keep():
    """Test that the keep option works."""
    
    test_file = "base_source.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix() + ' --keep protocol'
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("output_compare.json"), "r") as f:
        output_compare_json = json.loads(f.read())
        
    del output_compare_json["measurement"]
        
    assert output_json == output_compare_json
    
    assert output == ""
    
    
def test_keep_multiple_tables():
    """Test that the keep option works with multiple tables."""
    
    test_file = "base_source.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix() + ' --keep protocol,measurement'
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
    
    
def test_keep_regex():
    """Test that the keep option works with regex."""
    
    test_file = "base_source.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix() + ' --keep r\'.*tocol\''
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("output_compare.json"), "r") as f:
        output_compare_json = json.loads(f.read())
        
    del output_compare_json["measurement"]
                
    assert output_json == output_compare_json
    
    assert output == ""
    
    

def test_silent():
    """Test that the silent option works."""
    
    test_file = "silent_test.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix() + ' --silent'
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




def test_metadatasource_does_not_exist():
    """Test that invalid metadata sources print a message."""
    
    test_file = "attribute_field_test.xlsx"
    
    command = "messes extract ../" + test_file + " fake_file.xlsx --output " + output_path.as_posix() 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
        
    assert output == "Excel workbook \"fake_file.xlsx\" does not exist.\nExcel workbook \"fake_file.xlsx\" does not exist.\nExcel workbook \"fake_file.xlsx\" does not exist." + "\n"


def test_metadatasource_does_not_exist_Google_Sheets():
    """Test that invalid metadata sources print a message."""
    
    test_file = "attribute_field_test.xlsx"
    
    command = "messes extract ../" + test_file + " https://docs.google.com/spreadsheets/d/1g3xM2GW3gYiwC5mdaYEJFU49V4AIiobvwP0c/edit?usp=sharing --output " + output_path.as_posix() 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
        
    assert output == "The Google Sheets file \"https://docs.google.com/spreadsheets/d/1g3xM2GW3gYiwC5mdaYEJFU49V4AIiobvwP0c/export?format=xlsx\" does not exist or the URL is malformed.\n" +\
        "The Google Sheets file \"https://docs.google.com/spreadsheets/d/1g3xM2GW3gYiwC5mdaYEJFU49V4AIiobvwP0c/export?format=xlsx\" does not exist or the URL is malformed.\n" +\
        "The Google Sheets file \"https://docs.google.com/spreadsheets/d/1g3xM2GW3gYiwC5mdaYEJFU49V4AIiobvwP0c/export?format=xlsx\" does not exist or the URL is malformed.\n"




def test_output_option_no_json_extension():
    """Test that the output option gets .json added if not present."""
    
    test_file = "base_source.xlsx"
    
    command = "messes extract ../" + test_file + " --output output" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
        
    assert output == ""



def test_compare_option_is_not_json():
    """Test that an error is printed if the compare option file is not json."""
    
    test_file = "base_source.xlsx"
    
    command = "messes extract ../" + test_file + " --compare ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
        
    assert output == "Error: The provided file for comparison is not a JSON file." + "\n"
    
    

def test_compare_option_does_not_exist():
    """Test that an error is printed if the compare option file does not exist."""
    
    test_file = "base_source.xlsx"
    
    command = "messes extract ../" + test_file + " --compare ../asdf.asdf --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
        
    assert output == "Error: The provided file for comparison does not exist." + "\n"



def test_empty_directives_warning():
    """Test that a warning is printed if a directives json file doesn't have the proper format."""
    
    test_file = "base_source.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix() + " --modify ../empty_directives.json"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("output_compare.json"), "r") as f:
        output_compare_json = json.loads(f.read())
        
    assert output_json != output_compare_json
    
    assert output == 'Warning: The input directives JSON file is either not a dict or does not contain the directive keyword "modification". This means that modification will not be done.' + "\n"



def test_compare_close_floats():
    """Test that the comparison of floats has some fuzzy matching."""
    
    test_file = "compare_close_floats.xlsx"
    
    command = "messes extract ../" + test_file +" --output " + output_path.as_posix() + " --compare " + output_compare_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stdout

    
    assert output_path.exists()
        
    assert output == "Comparison\nNo differences detected." + "\n"



def test_compare_many_differences():
    """Test printing of all possible differences."""
    
    test_file = "compare_differences_test.xlsx"
    
    command = "messes extract ../" + test_file +" --output " + output_path.as_posix() + " --compare " + output_compare_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stdout

    
    assert output_path.exists()
        
    assert output == "Comparison\nMissing Tables: protocol\nExtra Tables: extra_table\nTable measurement with missing records:\n   (S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench\nTable measurement with extra records:\n   compound1-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench\nTable measurement id (S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench with different fields: comments" + "\n"
    


def test_file_processing_csv():
    """Test that --file_processing removes characters it's supposed to be default for csv files."""
    
    test_file = "bad_endlines.csv"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("bad_endlines_compare.json"), "r") as f:
        output_compare_json = json.loads(f.read())
        
    assert output_json == output_compare_json
    
    assert output == ''
    

def test_file_processing_xlsx():
    """Test that --file_processing removes characters it's supposed to be default for xlsx files."""
    
    test_file = "bad_endlines.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("bad_endlines_compare.json"), "r") as f:
        output_compare_json = json.loads(f.read())
        
    assert output_json == output_compare_json
    
    assert output == ''
    

def test_file_processing_None():
    """Test that --file_processing is disabled when set to None."""
    
    test_file = "bad_endlines.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix() + " --file-cleaning None"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("bad_endlines_compare.json"), "r") as f:
        output_compare_json = json.loads(f.read())
        
    assert output_json != output_compare_json
    
    assert output == ''
    

def test_file_processing_not_default():
    """Test that --file_processing removes characters it's supposed to when manually specified."""
    
    test_file = "base_source.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix() + " --file-cleaning C5"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
                
    assert output_json["measurement"]["(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"]["formula"] == "H8O4"
    
    assert output == ''



