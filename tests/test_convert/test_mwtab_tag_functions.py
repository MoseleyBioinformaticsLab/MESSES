# -*- coding: utf-8 -*-
"""
Test lines that weren't covered during other testing of convert.
"""

import pytest
import json
import os
import pathlib
import copy
import operator

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


def test_ss_factors_are_unique(mwtab_json, capsys):
    """Test that generated ss_factors are unique."""
    working_json = copy.deepcopy(mwtab_json)
    
    with does_not_raise():
        ss_factors = create_subject_sample_factors(working_json)
    captured = capsys.readouterr()
    assert captured.err == ""
    
    ss_factors_compare = []
    for ss_factor in ss_factors:
        if ss_factor in ss_factors_compare:
            assert False
        else:
            ss_factors_compare.append(ss_factor)


def test_parent_not_in_entity_table_error(mwtab_json, capsys):
    """Test that if an entity has a parent that is not in the same table an error is printed."""
    working_json = copy.deepcopy(mwtab_json)
    del working_json["entity"]["01_A0_Colon_naive_0days_170427_UKy_GCH_rep1"]
    with pytest.raises(SystemExit):
        create_subject_sample_factors(working_json)
    captured = capsys.readouterr()
    assert captured.err == 'Error: The parent entity, "01_A0_Colon_naive_0days_170427_UKy_GCH_rep1", ' +\
                            'pulled from the entity "01_A0_Colon_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A" ' +\
                            'in the "entity" table is not in the "entity" table. Parent entities must be in the table with thier children.' + "\n"


def test_measurement_sample_not_in_entity_table_error(mwtab_json, capsys):
    """Test that if a sample in the measurements is not in the entity table an error is printed."""
    working_json = copy.deepcopy(mwtab_json)
    del working_json["entity"]["01_A0_Colon_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A"]
    with pytest.raises(SystemExit):
        create_subject_sample_factors(working_json)
    captured = capsys.readouterr()
    assert captured.err == 'Error: The sample, "01_A0_Colon_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A", ' +\
                            'pulled from the "measurement" table is not in the "entity" table. ' +\
                            'Thus the subject-sample-factors cannot be determined.' + "\n"


def test_data_files_less_than_attribute(mwtab_json, capsys):
    """Test that if data_files has fewere elements than data_files%entity_id a warning is printed."""
    working_json = copy.deepcopy(mwtab_json)
    del working_json["protocol"]["ICMS1"]["data_files"][-1]
    ss_factors = create_subject_sample_factors(working_json)
    captured = capsys.readouterr()
    assert captured.err == 'Warning: The protocol, "ICMS1", has a data_files field that is not ' +\
                           'the same length as its data_files%entity_id field. The raw files for the '+\
                           'subject-sample-factors may be incorrect.' + "\n"
    
    with open("main_dir/SS_factors_compare.json", 'r') as jsonFile:
        ss_factors_compare = json.load(jsonFile)
        
    del ss_factors_compare[-1]["Additional sample data"]["RAW_FILE_NAME"]
    
    assert ss_factors == ss_factors_compare
    

def test_measurement_samples_different_from_protocol_samples(mwtab_json, capsys):
    """Test that if data_files%entity_id has different samples than what are found in the measurements a warning is printed."""
    working_json = copy.deepcopy(mwtab_json)
    del working_json["protocol"]["ICMS1"]["data_files%entity_id"][-1]
    ss_factors = create_subject_sample_factors(working_json)
    captured = capsys.readouterr()
    assert 'Warning: The entities found in the measurement records and ' +\
           'those found in the data_files%entity_id field of the ICMS1 protocol are not the same.' + "\n" in captured.err
    
    with open("main_dir/SS_factors_compare.json", 'r') as jsonFile:
        ss_factors_compare = json.load(jsonFile)
        
    del ss_factors_compare[-1]["Additional sample data"]["RAW_FILE_NAME"]
    
    assert ss_factors == ss_factors_compare


def test_sample_has_factors_str(mwtab_json, capsys):
    """Test when a sample has a factor it is handled correctly."""
    working_json = copy.deepcopy(mwtab_json)
    working_json["entity"]["test_sample"] = {"time_point":"0", 
                                              "protocol.id": [
                                                            "polar_extraction",
                                                            "IC-FTMS_preparation",
                                                            "naive"
                                                            ]
                                              }
    working_json["measurement"]["test_measurement"] = {"id":"test_measurement", "entity.id":"test_sample"}
    working_json["protocol"]["ICMS1"]["data_files%entity_id"].append("test_sample")
    working_json["protocol"]["ICMS1"]["data_files"].append("test_raw_file.raw")
    
    with does_not_raise():
        ss_factors = create_subject_sample_factors(working_json)
    captured = capsys.readouterr()
    assert captured.err == ""
    
    with open("main_dir/SS_factors_compare.json", 'r') as jsonFile:
        ss_factors_compare = json.load(jsonFile)
        
    ss_factors_compare.insert(0,{
                                "Subject ID": "",
                                "Sample ID": "test_sample",
                                "Factors": {
                                  "Time Point": "0",
                                  "Treatment": "naive"
                                },
                                "Additional sample data": {"RAW_FILE_NAME": "test_raw_file.raw"}
                              })
    ss_factors_compare = sorted(ss_factors_compare, key = operator.itemgetter(*["Subject ID", "Sample ID"]))
    
    assert ss_factors == ss_factors_compare


def test_sample_has_factors_list(mwtab_json, capsys):
    """Test when a sample has a factor it is handled correctly."""
    working_json = copy.deepcopy(mwtab_json)
    working_json["entity"]["test_sample"] = {"time_point":["0"], 
                                              "protocol.id": [
                                                            "polar_extraction",
                                                            "IC-FTMS_preparation",
                                                            "naive"
                                                            ]
                                              }
    working_json["measurement"]["test_measurement"] = {"id":"test_measurement", "entity.id":"test_sample"}
    working_json["protocol"]["ICMS1"]["data_files%entity_id"].append("test_sample")
    working_json["protocol"]["ICMS1"]["data_files"].append("test_raw_file.raw")
    
    with does_not_raise():
        ss_factors = create_subject_sample_factors(working_json)
    captured = capsys.readouterr()
    assert captured.err == ""
    
    with open("main_dir/SS_factors_compare.json", 'r') as jsonFile:
        ss_factors_compare = json.load(jsonFile)
        
    ss_factors_compare.insert(0,{
                                "Subject ID": "",
                                "Sample ID": "test_sample",
                                "Factors": {
                                  "Time Point": "0",
                                  "Treatment": "naive"
                                },
                                "Additional sample data": {"RAW_FILE_NAME": "test_raw_file.raw"}
                              })
    ss_factors_compare = sorted(ss_factors_compare, key = operator.itemgetter(*["Subject ID", "Sample ID"]))
    
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
    working_json["measurement"]["test_measurement"] = {"id":"test_measurement", "entity.id":"test_sample"}
    
    with does_not_raise():
        ss_factors = create_subject_sample_factors(working_json)
    captured = capsys.readouterr()
    assert 'Warning: The following samples do not have the full set of factors: ' +\
           '\ntest_sample' + '\n' in captured.err
    

