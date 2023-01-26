# -*- coding: utf-8 -*-
"""
Test lines that weren't covered during other testing of convert.
"""

import pytest
import json
import os
import pathlib
import copy

from contextlib import nullcontext as does_not_raise

from messes.convert.mwtab_functions import create_subject_sample_factors


@pytest.fixture(scope="module", autouse=True)
def change_cwd():
    cwd = pathlib.Path.cwd()
    os.chdir(pathlib.Path("tests", "test_convert", "testing_files"))
    yield
    os.chdir(cwd)

cwd = pathlib.Path.cwd()
os.chdir(pathlib.Path("tests", "test_convert", "testing_files"))
with open("MS_base_input_truncated.json", 'r') as jsonFile:
    test_mwtab_json = json.load(jsonFile)
os.chdir(cwd)

@pytest.fixture
def mwtab_json():
    return test_mwtab_json


def test_parent_not_in_entity_table_error(mwtab_json, capsys):
    """Test that if an entity has a parent that is not in the same table an error is printed."""
    working_json = copy.deepcopy(mwtab_json)
    del working_json["entity"]["01_A0_Colon_naive_0days_170427_UKy_GCH_rep1"]
    with pytest.raises(SystemExit):
        create_subject_sample_factors(working_json)
    captured = capsys.readouterr()
    assert captured.err == 'Error: The parent entity, "01_A0_Colon_naive_0days_170427_UKy_GCH_rep1", ' +\
                            'pulled from the entity "01_A0_Colon_naive_0days_170427_UKy_GCH_rep1-lipid" ' +\
                            'in the "entity" table is not in the "entity". Parent entities must be in the table with thier children.' + "\n"


def test_measurement_sample_not_in_entity_table_error(mwtab_json, capsys):
    """Test that if a sample in the measurements is not in the entity table an error is printed."""
    working_json = copy.deepcopy(mwtab_json)
    del working_json["entity"]["16_A0_Lung_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A"]
    with pytest.raises(SystemExit):
        create_subject_sample_factors(working_json)
    captured = capsys.readouterr()
    assert captured.err == 'Error: The sample, "16_A0_Lung_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A", ' +\
                            'pulled from the "measurement" table is not in the "entity". ' +\
                            'Thus the subject-sample-factors cannot be determined.' + "\n"


def test_ancestor_has_storage_protocol_list(mwtab_json, capsys):
    """Test that ancestors's storage protocols are found and added to raw files."""
    working_json = copy.deepcopy(mwtab_json)
    working_json["protocol"]["test_storage"] = {"description":"test storage", 
                                                "id":"test_storage", 
                                                "type":"storage",
                                                "parentID":"file_storage",
                                                "data_files":["test_file.raw"]}
    working_json["entity"]['16_A0_Lung_naive_0days_170427_UKy_GCH_rep1']["protocol.id"].append("test_storage")
    
    with does_not_raise():
        ss_factors = create_subject_sample_factors(working_json)
    captured = capsys.readouterr()
    assert captured.err == ""
    
    with open("main_dir/SS_factors_compare.json", 'r') as jsonFile:
        ss_factors_compare = json.load(jsonFile)
    
    for i, factor in enumerate(ss_factors_compare):
        if "16_A0_Lung_naive_0days_170427_UKy_GCH_rep1" in factor["Sample ID"]:
            ss_factors_compare[i]["Additional sample data"]["lineage1_protocol.id"] = "['mouse_tissue_collection', 'tissue_quench', 'frozen_tissue_grind', 'test_storage']"
            ss_factors_compare[i]["Additional sample data"]["RAW_FILE_NAME"] = "['test_file.raw', '16_A0_Lung_T032017_naive_ICMSA.raw']"
    
    assert ss_factors == ss_factors_compare


def test_ancestor_has_storage_protocol_str(mwtab_json, capsys):
    """Test that ancestors's storage protocols are found and added to raw files."""
    working_json = copy.deepcopy(mwtab_json)
    working_json["protocol"]["test_storage"] = {"description":"test storage", 
                                                "id":"test_storage", 
                                                "type":"storage",
                                                "parentID":"file_storage",
                                                "data_files":"test_file.raw"}
    working_json["entity"]['16_A0_Lung_naive_0days_170427_UKy_GCH_rep1']["protocol.id"].append("test_storage")
    
    with does_not_raise():
        ss_factors = create_subject_sample_factors(working_json)
    captured = capsys.readouterr()
    assert captured.err == ""
    
    with open("main_dir/SS_factors_compare.json", 'r') as jsonFile:
        ss_factors_compare = json.load(jsonFile)
    
    for i, factor in enumerate(ss_factors_compare):
        if "16_A0_Lung_naive_0days_170427_UKy_GCH_rep1" in factor["Sample ID"]:
            ss_factors_compare[i]["Additional sample data"]["lineage1_protocol.id"] = "['mouse_tissue_collection', 'tissue_quench', 'frozen_tissue_grind', 'test_storage']"
            ss_factors_compare[i]["Additional sample data"]["RAW_FILE_NAME"] = "['test_file.raw', '16_A0_Lung_T032017_naive_ICMSA.raw']"
    
    assert ss_factors == ss_factors_compare


def test_sibling_has_storage_protocol_str(mwtab_json, capsys):
    """Test that sibling's storage protocols are found and added to raw files."""
    working_json = copy.deepcopy(mwtab_json)
    working_json["protocol"]["test_storage"] = {"description":"test storage", 
                                                "id":"test_storage", 
                                                "type":"storage",
                                                "parentID":"file_storage",
                                                "data_files":"test_file.raw"}
    working_json["entity"]['16_A0_Lung_naive_0days_170427_UKy_GCH_rep1-protein']["protocol.id"].append("test_storage")
    
    with does_not_raise():
        ss_factors = create_subject_sample_factors(working_json)
    captured = capsys.readouterr()
    assert captured.err == ""
    
    with open("main_dir/SS_factors_compare.json", 'r') as jsonFile:
        ss_factors_compare = json.load(jsonFile)
    
    for i, factor in enumerate(ss_factors_compare):
        if "16_A0_Lung_naive_0days_170427_UKy_GCH_rep1" in factor["Sample ID"]:
            ss_factors_compare[i]["Additional sample data"]["lineage2_protocol.id"] = "['protein_extraction', 'test_storage']"
            ss_factors_compare[i]["Additional sample data"]["RAW_FILE_NAME"] = "['test_file.raw', '16_A0_Lung_T032017_naive_ICMSA.raw']"
    
    assert ss_factors == ss_factors_compare
    

def test_sibling_has_storage_protocol_list(mwtab_json, capsys):
    """Test that sibling's storage protocols are found and added to raw files."""
    working_json = copy.deepcopy(mwtab_json)
    working_json["protocol"]["test_storage"] = {"description":"test storage", 
                                                "id":"test_storage", 
                                                "type":"storage",
                                                "parentID":"file_storage",
                                                "data_files":["test_file.raw"]}
    working_json["entity"]['16_A0_Lung_naive_0days_170427_UKy_GCH_rep1-protein']["protocol.id"].append("test_storage")
    
    with does_not_raise():
        ss_factors = create_subject_sample_factors(working_json)
    captured = capsys.readouterr()
    assert captured.err == ""
    
    with open("main_dir/SS_factors_compare.json", 'r') as jsonFile:
        ss_factors_compare = json.load(jsonFile)
    
    for i, factor in enumerate(ss_factors_compare):
        if "16_A0_Lung_naive_0days_170427_UKy_GCH_rep1" in factor["Sample ID"]:
            ss_factors_compare[i]["Additional sample data"]["lineage2_protocol.id"] = "['protein_extraction', 'test_storage']"
            ss_factors_compare[i]["Additional sample data"]["RAW_FILE_NAME"] = "['test_file.raw', '16_A0_Lung_T032017_naive_ICMSA.raw']"
    
    assert ss_factors == ss_factors_compare


def test_sample_has_factors_str(mwtab_json, capsys):
    """Test when a sample has a factor it is handled correctly."""
    working_json = copy.deepcopy(mwtab_json)
    working_json["entity"]["test_sample"] = {"time_point":"0", 
                                              "protocol.id": [
                                                            "polar_extraction",
                                                            "IC-FTMS_preparation",
                                                            "ICMS_file_storage16",
                                                            "naive"
                                                            ]
                                              }
    working_json["measurement"]["test_measurement"] = {"id":"test_measurement", "sample.id":"test_sample"}
    
    with does_not_raise():
        ss_factors = create_subject_sample_factors(working_json)
    captured = capsys.readouterr()
    assert captured.err == ""
    
    with open("main_dir/SS_factors_compare.json", 'r') as jsonFile:
        ss_factors_compare = json.load(jsonFile)
        
    ss_factors_compare.append({
                                "Subject ID": "",
                                "Sample ID": "test_sample",
                                "Factors": {
                                  "Time Point": "0",
                                  "Treatment": "naive"
                                },
                                "Additional sample data": {
                                  "RAW_FILE_NAME": "16_A0_Lung_T032017_naive_ICMSA.raw"
                                }
                              })
    
    assert ss_factors == ss_factors_compare


def test_sample_has_factors_list(mwtab_json, capsys):
    """Test when a sample has a factor it is handled correctly."""
    working_json = copy.deepcopy(mwtab_json)
    working_json["entity"]["test_sample"] = {"time_point":["0"], 
                                              "protocol.id": [
                                                            "polar_extraction",
                                                            "IC-FTMS_preparation",
                                                            "ICMS_file_storage16",
                                                            "naive"
                                                            ]
                                              }
    working_json["measurement"]["test_measurement"] = {"id":"test_measurement", "sample.id":"test_sample"}
    
    with does_not_raise():
        ss_factors = create_subject_sample_factors(working_json)
    captured = capsys.readouterr()
    assert captured.err == ""
    
    with open("main_dir/SS_factors_compare.json", 'r') as jsonFile:
        ss_factors_compare = json.load(jsonFile)
        
    ss_factors_compare.append({
                                "Subject ID": "",
                                "Sample ID": "test_sample",
                                "Factors": {
                                  "Time Point": "0",
                                  "Treatment": "naive"
                                },
                                "Additional sample data": {
                                  "RAW_FILE_NAME": "16_A0_Lung_T032017_naive_ICMSA.raw"
                                }
                              })
    
    assert ss_factors == ss_factors_compare


def test_storage_data_files_str(mwtab_json, capsys):
    """Test that data_files field for storage protocols can be a string."""
    working_json = copy.deepcopy(mwtab_json)
    working_json["protocol"]["ICMS_file_storage16"]["data_files"] = "16_A0_Lung_T032017_naive_ICMSA.raw"
    
    with does_not_raise():
        ss_factors = create_subject_sample_factors(working_json)
    captured = capsys.readouterr()
    assert captured.err == ""
    
    with open("main_dir/SS_factors_compare.json", 'r') as jsonFile:
        ss_factors_compare = json.load(jsonFile)
            
    assert ss_factors == ss_factors_compare


def test_factors_not_found_warning(mwtab_json, capsys):
    """Test that a warning is printed when there are factors in the factor table that aren't found."""
    working_json = copy.deepcopy(mwtab_json)
    working_json["factor"]["Test Factor"] = {
                                              "allowed_values": [
                                                "0",
                                                "7",
                                                "42"
                                              ],
                                              "id": "Test Factor",
                                              "field": "test_field",
                                              "project.id": "GH_Spleen",
                                              "study.id": "GH_Spleen"
                                            }
    
    with does_not_raise():
        ss_factors = create_subject_sample_factors(working_json)
    captured = capsys.readouterr()
    assert captured.err == 'Warning: There are factors in the "factor" table that ' +\
                            'were not found when determining the subject-sample-factors. ' +\
                            'These factors are: Test Factor' + '\n'
    



def test_sample_missing_factor(mwtab_json, capsys):
    """Test when a sample is missing a factor a warning is printed."""
    working_json = copy.deepcopy(mwtab_json)
    working_json["entity"]["test_sample"] = {"time_point":["0"], 
                                              "protocol.id": [
                                                            "polar_extraction",
                                                            "IC-FTMS_preparation",
                                                            "ICMS_file_storage16"
                                                            ]
                                              }
    working_json["measurement"]["test_measurement"] = {"id":"test_measurement", "sample.id":"test_sample"}
    
    with does_not_raise():
        ss_factors = create_subject_sample_factors(working_json)
    captured = capsys.readouterr()
    assert captured.err == 'Warning: The following samples do not have the full set of factors: ' +\
                            '\ntest_sample' + '\n'
    

