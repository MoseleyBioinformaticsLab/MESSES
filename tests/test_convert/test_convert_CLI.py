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
    os.chdir(pathlib.Path("tests", "test_convert", "testing_files", "main_dir"))
    yield
    os.chdir(cwd)
    
output_path_json = pathlib.Path("output.json")
@pytest.fixture(autouse=True)
def delete_metadata():
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
def delete_metadata():
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

                
output_compare_path = pathlib.Path("output_compare.json")


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
        
    assert output_json == output_compare_json
    
    assert output_path_txt.exists()
    
    with open(output_path_txt, "r", encoding = "utf-8") as f:
        output_txt = "".join(f.readlines())
        
    with open(pathlib.Path("MS_output_compare.txt"), "r", encoding = "utf-8") as f:
        output_compare_txt = "".join(f.readlines())
        
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
        
    assert output_json == output_compare_json
    
    assert output_path_txt.exists()
    
    with open(output_path_txt, "r", encoding = "utf-8") as f:
        output_txt = "".join(f.readlines())
        
    with open(pathlib.Path("NMR_output_compare.txt"), "r", encoding = "utf-8") as f:
        output_compare_txt = "".join(f.readlines())
        
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
        
    assert output_json == output_compare_json
    
    assert output_path_txt.exists()
    
    with open(output_path_txt, "r", encoding = "utf-8") as f:
        output_txt = "".join(f.readlines())
        
    with open(pathlib.Path("NMR_binned_output_compare.txt"), "r", encoding = "utf-8") as f:
        output_compare_txt = "".join(f.readlines())
        
    assert output_txt == output_compare_txt
    
    assert output == ""






