# -*- coding: utf-8 -*-
import pytest

import pathlib
import os
import time
import json
import subprocess
import re

import pandas


@pytest.fixture(scope="module", autouse=True)
def change_cwd():
    cwd = pathlib.Path.cwd()
    os.chdir(pathlib.Path("tests", "test_convert", "testing_files", "main_dir"))
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
                
output_path_txt = pathlib.Path("output.txt")
@pytest.fixture(autouse=True)
def delete_txt():
    # yield
    if output_path_txt.exists():
        os.remove(output_path_txt)
        time_to_wait=10
        time_counter = 0
        while output_path_txt.exists():
            time.sleep(1)
            time_counter += 1
            if time_counter > time_to_wait:
                raise FileExistsError(output_path_txt + " was not deleted within " + str(time_to_wait) + " seconds, so it is assumed that it won't be and something went wrong.")

output_path_print_directives = pathlib.Path("mwtab_ms_conversion_directives.json")
@pytest.fixture(autouse=True)
def delete_print_directives():                
    if output_path_print_directives.exists():
        os.remove(output_path_print_directives)
        time_to_wait=10
        time_counter = 0
        while output_path_print_directives.exists():
            time.sleep(1)
            time_counter += 1
            if time_counter > time_to_wait:
                raise FileExistsError(output_path_print_directives + " was not deleted within " + str(time_to_wait) + " seconds, so it is assumed that it won't be and something went wrong.")

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



                


def read_text_from_txt(doc_path):    
    with open(doc_path, encoding = "utf-8") as document:
        lines = document.readlines()
    
    return "".join(lines)


def test_mwtab_MS_command():
    """Test that the mwtab ms command creates the expected json and mwtab format files."""
    
    test_file = "MS_base_input.json"
    
    command = "messes convert mwtab ms ../" + test_file  + " output" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("MS_output_compare.json"), "r") as f:
        output_compare_json = json.loads(f.read())
    
    del output_json["METABOLOMICS WORKBENCH"]["CREATED_ON"]
    del output_compare_json["METABOLOMICS WORKBENCH"]["CREATED_ON"]
    assert output_json == output_compare_json
    
    assert output_path_txt.exists()
    
    with open(output_path_txt, "r", encoding = "utf-8") as f:
        output_txt = "".join(f.readlines())
        
    with open(pathlib.Path("MS_output_compare.txt"), "r", encoding = "utf-8") as f:
        output_compare_txt = "".join(f.readlines())
        
    output_txt = re.sub(r"^CREATED_ON.*$", "", output_txt, flags=re.MULTILINE)
    output_compare_txt = re.sub(r"^CREATED_ON.*$", "", output_compare_txt, flags=re.MULTILINE)
    assert output_txt == output_compare_txt
    
    assert output == ""
    
    
def test_mwtab_NMR_command():
    """Test that the mwtab nmr command creates the expected json and mwtab format files."""
    
    test_file = "NMR_base_input.json"
    
    command = "messes convert mwtab nmr ../" + test_file  + " output" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("NMR_output_compare.json"), "r") as f:
        output_compare_json = json.loads(f.read())
    
    del output_json["METABOLOMICS WORKBENCH"]["CREATED_ON"]
    del output_compare_json["METABOLOMICS WORKBENCH"]["CREATED_ON"]
    assert output_json == output_compare_json
    
    assert output_path_txt.exists()
    
    with open(output_path_txt, "r", encoding = "utf-8") as f:
        output_txt = "".join(f.readlines())
        
    with open(pathlib.Path("NMR_output_compare.txt"), "r", encoding = "utf-8") as f:
        output_compare_txt = "".join(f.readlines())
        
    output_txt = re.sub(r"^CREATED_ON.*$", "", output_txt, flags=re.MULTILINE)
    output_compare_txt = re.sub(r"^CREATED_ON.*$", "", output_compare_txt, flags=re.MULTILINE)
    assert output_txt == output_compare_txt
    
    assert output == ""


def test_mwtab_NMR_binned_command():
    """Test that the mwtab nmr_binned command creates the expected json and mwtab format files."""
    
    test_file = "NMR_binned_base_input.json"
    
    command = "messes convert mwtab nmr_binned ../" + test_file  + " output" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("NMR_binned_output_compare.json"), "r") as f:
        output_compare_json = json.loads(f.read())
    
    del output_json["METABOLOMICS WORKBENCH"]["CREATED_ON"]
    del output_compare_json["METABOLOMICS WORKBENCH"]["CREATED_ON"]
    assert output_json == output_compare_json
    
    assert output_path_txt.exists()
    
    with open(output_path_txt, "r", encoding = "utf-8") as f:
        output_txt = "".join(f.readlines())
        
    with open(pathlib.Path("NMR_binned_output_compare.txt"), "r", encoding = "utf-8") as f:
        output_compare_txt = "".join(f.readlines())
        
    output_txt = re.sub(r"^CREATED_ON.*$", "", output_txt, flags=re.MULTILINE)
    output_compare_txt = re.sub(r"^CREATED_ON.*$", "", output_compare_txt, flags=re.MULTILINE)
    assert output_txt == output_compare_txt
    
    assert output == ""


def test_mwtab_MS_update_command():
    """Test that the mwtab ms command --update creates the expected json and mwtab format files."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert mwtab ms ../" + test_file  + " output --update ../mwtab_ms_conversion_directives_update.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("MS_output_compare_truncated.json"), "r") as f:
        output_compare_json = json.loads(f.read())
    
    del output_json["METABOLOMICS WORKBENCH"]["CREATED_ON"]
    del output_compare_json["METABOLOMICS WORKBENCH"]["CREATED_ON"]
    output_compare_json["METABOLOMICS WORKBENCH"]["ANALYSIS_ID"] = "AN000001"
    assert output_json == output_compare_json
    
    assert output_path_txt.exists()
    
    with open(output_path_txt, "r", encoding = "utf-8") as f:
        output_txt = "".join(f.readlines())
        
    with open(pathlib.Path("MS_output_compare_truncated.txt"), "r", encoding = "utf-8") as f:
        output_compare_txt = "".join(f.readlines())
        
    output_txt = re.sub(r"^CREATED_ON.*$", "", output_txt, flags=re.MULTILINE)
    output_compare_txt = re.sub(r"^CREATED_ON.*$", "", output_compare_txt, flags=re.MULTILINE)
    output_compare_txt = re.sub(r"AN000000", "AN000001", output_compare_txt, flags=re.MULTILINE)
    assert output_txt == output_compare_txt
    
    assert output == ""


def test_mwtab_MS_override_command():
    """Test that the mwtab ms command --override creates the expected json and mwtab format files."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert mwtab ms ../" + test_file  + " output --override ../mwtab_ms_conversion_directives_override.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("MS_output_compare_truncated.json"), "r") as f:
        output_compare_json = json.loads(f.read())
    
    del output_json["METABOLOMICS WORKBENCH"]["CREATED_ON"]
    del output_compare_json["METABOLOMICS WORKBENCH"]["CREATED_ON"]
    output_compare_json["METABOLOMICS WORKBENCH"]["ANALYSIS_ID"] = "AN000001"
    output_compare_json["METABOLOMICS WORKBENCH"]["STUDY_ID"] = "ST000001"
    del output_compare_json["TREATMENT"]["TREATMENT_PROTOCOL_FILENAME"]
    assert output_json == output_compare_json
    
    assert output_path_txt.exists()
    
    with open(output_path_txt, "r", encoding = "utf-8") as f:
        output_txt = "".join(f.readlines())
        
    with open(pathlib.Path("MS_output_compare_truncated.txt"), "r", encoding = "utf-8") as f:
        output_compare_txt = "".join(f.readlines())
        
    output_txt = re.sub(r"^CREATED_ON.*$", "", output_txt, flags=re.MULTILINE)
    output_compare_txt = re.sub(r"^CREATED_ON.*$", "", output_compare_txt, flags=re.MULTILINE)
    output_compare_txt = re.sub(r"AN000000", "AN000001", output_compare_txt, flags=re.MULTILINE)
    output_compare_txt = re.sub(r"ST000000", "ST000001", output_compare_txt, flags=re.MULTILINE)
    output_compare_txt = re.sub(r"^TR:TREATMENT_PROTOCOL_FILENAME.*\n", "", output_compare_txt, flags=re.MULTILINE)
    assert output_txt == output_compare_txt
    
    assert output == ""


def test_mwtab_MS_silent_command():
    """Test that the mwtab ms command --silent silences warnings."""
    
    test_file = "MS_base_input_truncated_no_field_warning.json"
    
    command = "messes convert mwtab ms ../" + test_file  + " output --silent" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path_json.exists()
    
    assert output_path_txt.exists()
    
    assert output == ""


def test_printdirectives_mwtab_MS_json():
    """Test that the save-directives mwtab ms command creates the expected json file."""
    
    command = "messes convert save-directives mwtab ms json output" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("mwtab_ms_conversion_directives_compare.json"), "r") as f:
        output_compare_json = json.loads(f.read())
    
    assert output_json == output_compare_json
        
    assert output == ""
    

def test_printdirectives_mwtab_MS_xlsx():
    """Test that the save-directives mwtab ms command creates the expected xlsx file."""
    
    command = "messes convert save-directives mwtab ms xlsx output" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    output_path = pathlib.Path("output.xlsx")
    time_to_wait=10
    time_counter = 0
    while not output_path.exists():
        time.sleep(1)
        time_counter += 1
        if time_counter > time_to_wait:
            raise FileNotFoundError(output_path + "was never created.")
            
    assert output_path.exists()
    
    output_df = pandas.read_excel(output_path)
        
    output_compare_df = pandas.read_excel("mwtab_ms_conversion_directives_compare.xlsx")
    
    assert output_df.equals(output_compare_df)
        
    assert output == ""
    

def test_printdirectives_mwtab_MS_csv():
    """Test that the save-directives mwtab ms command creates the expected csv file."""
    
    command = "messes convert save-directives mwtab ms csv output" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    output_path = pathlib.Path("output.csv")
    time_to_wait=10
    time_counter = 0
    while not output_path.exists():
        time.sleep(1)
        time_counter += 1
        if time_counter > time_to_wait:
            raise FileNotFoundError(output_path + "was never created.")
    
    assert output_path.exists()
    
    output_df = pandas.read_csv(output_path)
        
    output_compare_df = pandas.read_csv("mwtab_ms_conversion_directives_compare.csv")
    
    assert output_df.equals(output_compare_df)
        
    assert output == ""
    

def test_printdirectives_mwtab_MS_autoname():
    """Test that the save-directives mwtab ms command autonames the output file."""
    
    command = "messes convert save-directives mwtab ms json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    output_path = pathlib.Path("mwtab_ms_conversion_directives.json")
    time_to_wait=10
    time_counter = 0
    while not output_path.exists():
        time.sleep(1)
        time_counter += 1
        if time_counter > time_to_wait:
            raise FileNotFoundError(output_path + "was never created.")
    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("mwtab_ms_conversion_directives_compare.json"), "r") as f:
        output_compare_json = json.loads(f.read())
    
    assert output_json == output_compare_json
        
    assert output == ""
    
                

def test_printdirectives_mwtab_MS_json_extension():
    """Test that the save-directives mwtab ms command won't add the filetype extension if it is already present."""
    
    command = "messes convert save-directives mwtab ms json output.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("mwtab_ms_conversion_directives_compare.json"), "r") as f:
        output_compare_json = json.loads(f.read())
    
    assert output_json == output_compare_json
        
    assert output == ""


def test_printdirectives_mwtab_NMR_json():
    """Test that the save-directives mwtab nmr command creates the expected json file."""
    
    command = "messes convert save-directives mwtab nmr json output" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("mwtab_nmr_conversion_directives_compare.json"), "r") as f:
        output_compare_json = json.loads(f.read())
    
    assert output_json == output_compare_json
        
    assert output == ""
    

def test_printdirectives_mwtab_NMR_xlsx():
    """Test that the save-directives mwtab nmr command creates the expected xlsx file."""
    
    command = "messes convert save-directives mwtab nmr xlsx output" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    output_path = pathlib.Path("output.xlsx")
    time_to_wait=10
    time_counter = 0
    while not output_path.exists():
        time.sleep(1)
        time_counter += 1
        if time_counter > time_to_wait:
            raise FileNotFoundError(output_path + "was never created.")
            
    assert output_path.exists()
    
    output_df = pandas.read_excel(output_path)
        
    output_compare_df = pandas.read_excel("mwtab_nmr_conversion_directives_compare.xlsx")
    
    assert output_df.equals(output_compare_df)
        
    assert output == ""
    

def test_printdirectives_mwtab_NMR_csv():
    """Test that the save-directives mwtab nmr command creates the expected csv file."""
    
    command = "messes convert save-directives mwtab nmr csv output" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    output_path = pathlib.Path("output.csv")
    time_to_wait=10
    time_counter = 0
    while not output_path.exists():
        time.sleep(1)
        time_counter += 1
        if time_counter > time_to_wait:
            raise FileNotFoundError(output_path + "was never created.")
    
    assert output_path.exists()
    
    output_df = pandas.read_csv(output_path)
        
    output_compare_df = pandas.read_csv("mwtab_nmr_conversion_directives_compare.csv")
    
    assert output_df.equals(output_compare_df)
        
    assert output == ""
    

def test_printdirectives_mwtab_NMR_binned_json():
    """Test that the save-directives mwtab nmr_binned command creates the expected json file."""
    
    command = "messes convert save-directives mwtab nmr_binned json output" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("mwtab_nmr_binned_conversion_directives_compare.json"), "r") as f:
        output_compare_json = json.loads(f.read())
    
    assert output_json == output_compare_json
        
    assert output == ""
    

def test_printdirectives_mwtab_NMR_binned_xlsx():
    """Test that the save-directives mwtab nmr_binned command creates the expected xlsx file."""
    
    command = "messes convert save-directives mwtab nmr_binned xlsx output" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    output_path = pathlib.Path("output.xlsx")
    time_to_wait=10
    time_counter = 0
    while not output_path.exists():
        time.sleep(1)
        time_counter += 1
        if time_counter > time_to_wait:
            raise FileNotFoundError(output_path + "was never created.")
            
    assert output_path.exists()
    
    output_df = pandas.read_excel(output_path)
        
    output_compare_df = pandas.read_excel("mwtab_nmr_binned_conversion_directives_compare.xlsx")
    
    assert output_df.equals(output_compare_df)
        
    assert output == ""
    

def test_printdirectives_mwtab_NMR_binned_csv():
    """Test that the save-directives mwtab nmr_binned command creates the expected csv file."""
    
    command = "messes convert save-directives mwtab nmr_binned csv output" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    output_path = pathlib.Path("output.csv")
    time_to_wait=10
    time_counter = 0
    while not output_path.exists():
        time.sleep(1)
        time_counter += 1
        if time_counter > time_to_wait:
            raise FileNotFoundError(output_path + "was never created.")
    
    assert output_path.exists()
    
    output_df = pandas.read_csv(output_path)
        
    output_compare_df = pandas.read_csv("mwtab_nmr_binned_conversion_directives_compare.csv")
    
    assert output_df.equals(output_compare_df)
        
    assert output == ""
    

def test_mwtab_generic_command():
    """Test that the generic command creates the expected json file."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output mwtab_ms_conversion_directives_compare.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("MS_output_compare_truncated.json"), "r") as f:
        output_compare_json = json.loads(f.read())
    
    del output_json["METABOLOMICS WORKBENCH"]["CREATED_ON"]
    del output_compare_json["METABOLOMICS WORKBENCH"]["CREATED_ON"]
    assert output_json == output_compare_json
        
    assert output == ""
    

def test_mwtab_generic_silent_command():
    """Test that the generic command --silent option silences warnings."""
    
    test_file = "MS_base_input_truncated_no_field_warning.json"
    
    command = "messes convert generic ../" + test_file  + " output mwtab_ms_conversion_directives_compare.json --silent" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("MS_output_compare_truncated.json"), "r") as f:
        output_compare_json = json.loads(f.read())
    
    del output_json["METABOLOMICS WORKBENCH"]["CREATED_ON"]
    del output_compare_json["METABOLOMICS WORKBENCH"]["CREATED_ON"]
    del output_compare_json["COLLECTION"]["COLLECTION_PROTOCOL_FILENAME"]
    assert output_json == output_compare_json
        
    assert output == ""


def test_xlsx_read_in():
    """Test that xlsx files are read in as expected."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output mwtab_ms_conversion_directives_compare.xlsx:Sheet1" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("MS_output_compare_truncated.json"), "r") as f:
        output_compare_json = json.loads(f.read())
    
    del output_json["METABOLOMICS WORKBENCH"]["CREATED_ON"]
    del output_compare_json["METABOLOMICS WORKBENCH"]["CREATED_ON"]
    assert output_json == output_compare_json
        
    assert output == ""
    

def test_Google_Sheets_read_in():
    """Test that Google Sheets files are read in as expected."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output https://docs.google.com/spreadsheets/d/1ebwRw2hEaeJBdBBnCj3UAR79O7tJqSa_TodpA7Twle0/edit#gid=273139213:Sheet1" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path_json.exists()
    
    with open(output_path_json, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("Google_Sheets_compare.json"), "r") as f:
        output_compare_json = json.loads(f.read())
    
    del output_json["METABOLOMICS WORKBENCH"]["CREATED_ON"]
    del output_compare_json["METABOLOMICS WORKBENCH"]["CREATED_ON"]
    assert output_json == output_compare_json
        
    assert output == ""
    

def test_xlsx_no_default_sheetname_error():
    """Test that an error is printed when the xlsx file does not have the default sheet name."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output mwtab_ms_conversion_directives_compare.xlsx" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert not output_path_json.exists()
        
    assert output == "Error: No sheet name was given for the file, so the default name " +\
                      "of #convert was used, but it was not found in the file.\n"


def test_Google_Sheets_no_default_sheetname_error():
    """Test that an error is printed when the Google Sheets file does not have the default sheet name."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output https://docs.google.com/spreadsheets/d/1ebwRw2hEaeJBdBBnCj3UAR79O7tJqSa_TodpA7Twle0/edit#gid=273139213" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert not output_path_json.exists()
        
    assert output == "Error: No sheet name was given for the file, so the default name " +\
                      "of #convert was used, but it was not found in the file.\n"
                      

def test_xlsx_does_not_exist_error():
    """Test that an error is printed when the xlsx file does not exist."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output mwtab_ms_conversion_directives_compa.xlsx" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert not output_path_json.exists()
        
    assert output == "Excel workbook \"mwtab_ms_conversion_directives_compa.xlsx\" does not exist.\n"


def test_Google_Sheets_does_not_exist_error():
    """Test that an error is printed when the Google Sheets file does not exist."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output https://docs.google.com/spreadsheets/d/1McMXCw_WURntkWTo6HfP8U3DWpBj91OhUyPpaaQ/edit#gid=273139213:Sheet1" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert not output_path_json.exists()
        
    assert output == "The Google Sheets file \"https://docs.google.com/spreadsheets/d/1McMXCw_WURntkWTo6HfP8U3DWpBj91OhUyPpaaQ/export?format=xlsx\" does not exist or the URL is malformed.\n"
    
    
def test_xlsx_does_not_have_given_sheetname():
    """Test that an error is printed when the given sheet name does not exist."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output mwtab_ms_conversion_directives_compare.xlsx:asdf" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert not output_path_json.exists()
        
    assert output == "r'^asdf$' did not match any sheets in \"mwtab_ms_conversion_directives_compare.xlsx\".\n"


def test_Google_Sheets_does_not_have_given_sheetname():
    """Test that an error is printed when the given sheet name does not exist."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output https://docs.google.com/spreadsheets/d/1ebwRw2hEaeJBdBBnCj3UAR79O7tJqSa_TodpA7Twle0/edit#gid=273139213:asdf" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert not output_path_json.exists()
        
    assert output == "r'^asdf$' did not match any sheets in \"https://docs.google.com/spreadsheets/d/1ebwRw2hEaeJBdBBnCj3UAR79O7tJqSa_TodpA7Twle0/export?format=xlsx\".\n"
                     
                     
def test_conversion_directives_wrong_file_type():
    """Test that an error is printed when the conversion directives file is the wrong type."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert generic ../" + test_file  + " output mwtab_ms_conversion_directives_compare.txt" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert not output_path_json.exists()
        
    assert output == "Error: Unknown file type for the conversion directives file.\n"


def test_print_directives_wrong_file_type():
    """Test that an error is printed when the indicated file type is not csv, xlsx, or json is the wrong type."""
        
    command = "messes convert save-directives mwtab ms asdf"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert not output_path_json.exists()
        
    assert output == "Error: Unknown output filetype.\n"
    

def test_mwtab_validation_error():
    """Test that an error is printed when the mwtab validation fails."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert mwtab ms ../" + test_file  + " output --override ../mwtab_validation_error.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert output_path_json.exists()
    
    assert 'Error: An error occured when validating the mwtab file.' in output
    assert 'Status: Contains Validation Errors' in output
    

def test_input_json_does_not_exist_error():
    """Test that an error is printed when the input json does not exist."""
    
    command = "messes convert generic ../asdf.json output mwtab_ms_conversion_directives_compare.json"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert not output_path_json.exists()
        
    assert output == "Error: The value entered for <input_JSON>, ../asdf.json, is not a valid file path or does not exist.\n"
    
    
def test_input_json_is_not_json_error():
    """Test that an error is printed when the input json is not a json file."""
    
    command = "messes convert generic ../import_test.py output mwtab_ms_conversion_directives_compare.json"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    assert not output_path_json.exists()
        
    assert "Error: An error was encountered when trying to read in the <input_JSON>, ../import_test.py." in output


def test_unordered_directives_mwtab_MS():
    """Test that unordered conversion directives create the mwtab in the correct order."""
    
    test_file = "MS_base_input_truncated.json"
    
    command = "messes convert mwtab ms ../" + test_file  + " output --override ../mwtab_ms_conversion_directives_unordered.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

        
    assert output_path_txt.exists()
    
    with open(output_path_txt, "r", encoding = "utf-8") as f:
        output_txt = "".join(f.readlines())
        
    with open(pathlib.Path("MS_output_compare_truncated.txt"), "r", encoding = "utf-8") as f:
        output_compare_txt = "".join(f.readlines())
        
    output_txt = re.sub(r"^CREATED_ON.*$", "", output_txt, flags=re.MULTILINE)
    output_compare_txt = re.sub(r"^CREATED_ON.*$", "", output_compare_txt, flags=re.MULTILINE)
    assert output_txt == output_compare_txt
    
    assert output == ""
    

def test_unordered_directives_mwtab_NMR():
    """Test that unordered conversion directives create the mwtab in the correct order."""
    
    test_file = "NMR_base_input.json"
    
    command = "messes convert mwtab nmr ../" + test_file  + " output --override ../mwtab_nmr_conversion_directives_unordered.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

        
    assert output_path_txt.exists()
    
    with open(output_path_txt, "r", encoding = "utf-8") as f:
        output_txt = "".join(f.readlines())
        
    with open(pathlib.Path("NMR_output_compare.txt"), "r", encoding = "utf-8") as f:
        output_compare_txt = "".join(f.readlines())
        
    output_txt = re.sub(r"^CREATED_ON.*$", "", output_txt, flags=re.MULTILINE)
    output_compare_txt = re.sub(r"^CREATED_ON.*$", "", output_compare_txt, flags=re.MULTILINE)
    assert output_txt == output_compare_txt
    
    assert output == ""


def test_unordered_directives_mwtab_NMR_binned():
    """Test that unordered conversion directives create the mwtab in the correct order."""
    
    test_file = "NMR_binned_base_input.json"
    
    command = "messes convert mwtab nmr_binned ../" + test_file  + " output --override ../mwtab_nmr_binned_conversion_directives_unordered.json" 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

        
    assert output_path_txt.exists()
    
    with open(output_path_txt, "r", encoding = "utf-8") as f:
        output_txt = "".join(f.readlines())
        
    with open(pathlib.Path("NMR_binned_output_compare.txt"), "r", encoding = "utf-8") as f:
        output_compare_txt = "".join(f.readlines())
        
    output_txt = re.sub(r"^CREATED_ON.*$", "", output_txt, flags=re.MULTILINE)
    output_compare_txt = re.sub(r"^CREATED_ON.*$", "", output_compare_txt, flags=re.MULTILINE)
    assert output_txt == output_compare_txt
    
    assert output == ""

