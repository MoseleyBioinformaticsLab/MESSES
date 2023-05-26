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






def test_child_without_parent_id():
    """Test that an error is printed when there is a child without a parent id."""
    
    test_file = "child_tag_no_parent_id.xlsx"
    
    command = "messes extract ../" + test_file +" --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    
    assert subp.returncode == 1
    assert "no id field in parent record at cell" in output  
    assert "child_tag_no_parent_id.xlsx:#export[C12]" in output
    
    
        
    

def test_list_field():
    """Test that list fields get pulled in correctly."""
    
    test_file = "list_field_test.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix() 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
                
    assert output_json["measurement"]["1"]["asdf"] == ["1", "2", "3", "4", "5", "6"]
    assert output_json["measurement"]["2"]["asdf"] == ["3", "4", "5", "6", "7", "8"]
    
    assert output == ""



def test_list_field_inline():
    """Test that list fields get pulled in correctly from inline."""
    
    test_file = "list_field_test_inline.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix() 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
                
    assert output_json["sample"]["01_A0_Spleen_naive_0days_170427_UKy_GCH_rep1"]["protocol.id"] == [
                                                                                                      "mouse_tissue_collection",
                                                                                                      "tissue_quench",
                                                                                                      "frozen_tissue_grind",
                                                                                                      "protein_extraction"
                                                                                                    ]
    assert output_json["sample"]["02_A1_Spleen_naive_0days_170427_UKy_GCH_rep2"]["protocol.id"] == [
                                                                                                      "mouse_tissue_collection",
                                                                                                      "tissue_quench",
                                                                                                      "frozen_tissue_grind",
                                                                                                      "protein_extraction"
                                                                                                    ]
    
    assert output == ""



def test_attribute_field():
    """Test that attribute fields get pulled in correctly."""
    
    test_file = "attribute_field_test.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix() 
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
                
    assert output_json["measurement"]["1"]["raw_intensity%type"] == "spectrometer peak area"
    assert output_json["measurement"]["1"]["asdf%asdf"] == "asdf"
    
    assert output == ""




def test_child_tag():
    """Test that child tags work."""
    
    test_file = "child_tag_example.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
                                
    assert output_json["sample"]["01_A0_Spleen_naive_0days_170427_UKy_GCH_rep1-protein"]["parent_id"] == "01_A0_Spleen_naive_0days_170427_UKy_GCH_rep1"
    assert output_json["sample"]["01_A0_Spleen_naive_0days_170427_UKy_GCH_rep1-protein"]["protein_weight"] == "0"
    assert output_json["sample"]["01_A0_Spleen_naive_0days_170427_UKy_GCH_rep1-protein"]["protein_weight%units"] == "mg"
    assert output_json["sample"]["01_A0_Spleen_naive_0days_170427_UKy_GCH_rep1-protein"]["protocol.id"] == ["protein_extraction"]
    
    assert output == ""
    
    
    
def test_variable_operand():
    """Test that variable operand functionality works."""
    
    test_file = "variable_operand_test.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
                                
    assert output_json["asdf"]["id1"]["field1"] == "qwer"
    assert output_json["asdf"]["id1"]["field2"] == "qwerzxcv"
    assert output_json["asdf"]["id1"]["field3"] == "a"
    assert output_json["asdf"]["id1"]["field4"] == "a"
    assert output_json["asdf"]["id1"]["field5"] == "a"
    
    assert output == ""
    
    

def test_variable_operand_error():
    """Test that variable operand prints an error."""
    
    test_file = "variable_operand_test_error.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr
    print(output)

    
    assert not output_path.exists()
        
    assert "'the field or attribute value used for assignment is not previously defined in record at cell" in output
    assert "variable_operand_test_error.xlsx:#export[C1]" in output



def test_global_operand():
    """Test that global field functionality works."""
    
    test_file = "global_field_test.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
                                
    assert "asdf" not in output_json["sample"]["01_A0_Spleen_naive_0days_170427_UKy_GCH_rep1"]
    assert output_json["sample"]["01_A0_Spleen_naive_0days_170427_UKy_GCH_rep1-protein"]["asdf"] == "qwer"
    assert output_json["sample"]["01_A0_Spleen_naive_0days_170427_UKy_GCH_rep1-protein"]["asdf%attribute"] == "zxcv"
    assert output_json["sample"]["01_A0_Spleen_naive_0days_170427_UKy_GCH_rep1-protein"]["qwer"] == "asdf"
    assert output_json["sample"]["01_A0_Spleen_naive_0days_170427_UKy_GCH_rep1-protein"]["qwer%attribute"] == "fghj"
    
    assert output == ""
    
    
def test_global_operand_error():
    """Test that global field prints an error."""
    
    test_file = "global_field_test_error.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
        
    assert "'tags without assignment in first column at cell " in output  
    assert "global_field_test_error.xlsx:#export[A1]" in output 



def test_csv_error():
    """Test that csv file type prints a different error than xlsx."""
    
    test_file = "csv_error_test.csv"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
        
    assert "'tags without assignment in first column at cell " in output  
    assert "csv_error_test.csv:[col 1, row 1]" in output 
    
   
    
def test_undefined_table_name_error():
    """Test that malformed tag with no table name prints error."""
    
    test_file = "undefined_table_name_error.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
        
    assert "'Undefined table name at cell " in output  
    assert "undefined_table_name_error.xlsx:#export[A1]" in output 



def test_child_in_first_column_error():
    """Test that error is printed when a child tag is in first column."""
    
    test_file = "child_in_first_column_error.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
        
    assert "#.%child tag not allowed in first column at cell " in output  
    assert "child_in_first_column_error.xlsx:#export[A1]" in output 
    
    

def test_tags_not_in_first_column_error():
    """Test that error is printed when #tags is not in first column."""
    
    test_file = "tags_not_in_first_column_error.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
        
    assert "#tags only allowed in first column at cell " in output  
    assert "tags_not_in_first_column_error.xlsx:#export[B1]" in output 
    
    
def test_table_in_assignment_error():
    """Test that error is printed when #table is in assignment."""
    
    test_file = "table_in_assignment_error.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
        
    assert "#table, #tags, or #%child tags  in assignment at cell " in output  
    assert "table_in_assignment_error.xlsx:#export[C1]" in output
     
    
    
def test_child_in_assignment_error():
    """Test that error is printed when #%child is in assignment."""
    
    test_file = "child_in_assignment_error.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
        
    assert "#table, #tags, or #%child tags  in assignment at cell " in output  
    assert "child_in_assignment_error.xlsx:#export[C1]" in output
    
    
    
def test_tandem_operators_error():
    """Test that error is printed when malformed tag has 2 operators in a row."""
    
    test_file = "tandem_operators_error.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
        
    assert "tandem +/= operators without intervening operand at cell " in output  
    assert "tandem_operators_error.xlsx:#export[C1]" in output
    
    

def test_tandem_literal_error():
    """Test that error is printed when malformed tag has 2 literals in a row."""
    
    test_file = "tandem_literal_error.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
        
    assert "tandem literal/tag without intervening operator at cell " in output  
    assert "tandem_literal_error.xlsx:#export[C1]" in output
    
    

def test_operator_no_operand_blank_error():
    """Test that error is printed when malformed tag has an operator but no operand that ends in nothing."""
    
    test_file = "operator_no_operand_blank_error.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
        
    assert "+/= operator without second operand at cell " in output  
    assert "operator_no_operand_blank_error.xlsx:#export[C1]" in output
    
    
    
def test_operator_no_operand_semicolon_error():
    """Test that error is printed when malformed tag has an operator but no operand that ends in semicolon."""
    
    test_file = "operator_no_operand_semicolon_error.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
        
    assert "+/= operator without second operand at cell " in output  
    assert "operator_no_operand_semicolon_error.xlsx:#export[C1]" in output
    
    

def test_plus_not_in_assignment_error():
    """Test that error is printed when malformed tag has a + operator not in assignment."""
    
    test_file = "plus_not_in_assignment_error.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
        
    assert "+ operator not in an assignment at cell" in output  
    assert "plus_not_in_assignment_error.xlsx:#export[C1]" in output
    
    
    
def test_comma_not_in_list_assignment_error():
    """Test that error is printed when comma is used in a tag that is not assignment."""
    
    test_file = "comma_not_in_list_assignment_error.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
        
    assert ", operator not in a list field assignment at cell" in output  
    assert "comma_not_in_list_assignment_error.xlsx:#export[C1]" in output
    
    
    
def test_comma_not_in_list_tag_error():
    """Test that error is printed when comma is used in a tag that is not a list field."""
    
    test_file = "comma_not_in_list_tag_error.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
        
    assert ", operator not in a list field assignment at cell" in output  
    assert "comma_not_in_list_tag_error.xlsx:#export[C1]" in output
    
    
    
def test_double_equal_in_tag_error():
    """Test that error is printed when there are 2 = in a tag."""
    
    test_file = "double_equal_in_tag_error.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
        
    assert "second = operator in an assignment at cell" in output  
    assert "double_equal_in_tag_error.xlsx:#export[C1]" in output
    
    
    
def test_star_operator_not_at_beginning_assignment_error():
    """Test that error is printed when * is not at the beginning of an assignment."""
    
    test_file = "star_operator_not_at_beginning_assignment_error.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
        
    assert "* operator is not at the beginning of a field tag at cell" in output  
    assert "star_operator_not_at_beginning_assignment_error.xlsx:#export[C1]" in output
    
    
    
def test_star_operator_not_at_beginning_no_tokens_error():
    """Test that error is printed when * is the only token."""
    
    test_file = "star_operator_not_at_beginning_no_tokens_error.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
        
    assert "* operator is not at the beginning of a field tag at cell" in output  
    assert "star_operator_not_at_beginning_no_tokens_error.xlsx:#export[C1]" in output
    
    
def test_star_operator_not_at_beginning_no_tag_error():
    """Test that error is printed when * is not followed by #."""
    
    test_file = "star_operator_not_at_beginning_no_tag_error.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
        
    assert "* operator is not at the beginning of a field tag at cell" in output  
    assert "star_operator_not_at_beginning_no_tag_error.xlsx:#export[C1]" in output
    
    
 
    
def test_table_tag():
    """Test that the table tag works to change tables."""
    
    test_file = "table_tag_example.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    assert output == ""
    assert "measurement" in output_json
 
 
    
def test_table_tag_without_assignment_no_tokens_error():
    """Test that error is printed when #table is not followed by enough tokens."""
    
    test_file = "table_tag_without_assignment_no_tokens_error.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
        
    assert "#table tag without assignment at cell" in output  
    assert "table_tag_without_assignment_no_tokens_error.xlsx:#export[C1]" in output
    
    

def test_table_tag_without_assignment_no_equal_error():
    """Test that error is printed when #table is not followed by =."""
    
    test_file = "table_tag_without_assignment_no_equal_error.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
        
    assert "#table tag without assignment at cell" in output  
    assert "table_tag_without_assignment_no_equal_error.xlsx:#export[C1]" in output
    
    
    
def test_table_tag_without_assignment_no_word_error():
    """Test that error is printed when #table is not followed by a word."""
    
    test_file = "table_tag_without_assignment_no_word_error.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
        
    assert "#table tag without assignment at cell" in output  
    assert "table_tag_without_assignment_no_word_error.xlsx:#export[C1]" in output



def test_empty_child_error():
    """Test that error is printed when #%child is not followed by anything."""
    
    test_file = "empty_child_error.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
        
    assert "child tag with no field at cell" in output  
    assert "empty_child_error.xlsx:#export[C1]" in output
    
    

def test_child_no_assignment_error():
    """Test that error is printed when #%child.field=value is not an id field."""
    
    test_file = "child_no_assignment_error.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
        
    assert "no assignment allowed with explicit child field at cell" in output  
    assert "child_no_assignment_error.xlsx:#export[C1]" in output
    
    
    
def test_two_child_fields_without_id_error():
    """Test that error is printed when 2 child tags specify a field that isn't an id."""
    
    test_file = "two_child_fields_without_id_error.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
        
    assert "second explicit non-id child field specified at cell" in output  
    assert "two_child_fields_without_id_error.xlsx:#export[C1]" in output
    
    
    
def test_child_table_change_error():
    """Test that error is printed when 2 child tags specify a field that isn't an id."""
    
    test_file = "child_table_change_error.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
        
    assert "second explicit non-id child field specified at cell" in output  
    assert "child_table_change_error.xlsx:#export[C1]" in output



def test_global_field_no_assignment_error():
    """Test that error is printed when the global field tag isn't an assignment."""
    
    test_file = "global_field_no_assignment_error.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
        
    assert "tags without assignment in first column at cell" in output  
    assert "global_field_no_assignment_error.xlsx:#export[A1]" in output
    
    

def test_global_field_not_literal_error():
    """Test that error is printed when the global field tag assignment isn't a literal."""
    
    test_file = "global_field_not_literal_error.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
        
    assert "tags without assignment in first column at cell" in output  
    assert "global_field_not_literal_error.xlsx:#export[A1]" in output



def test_duplicate_field_error():
    """Test that error is printed when there are duplicate fields."""
    
    test_file = "duplicate_field_error.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
        
    assert "field \"asdf\" specified twice in sample record at cell" in output  
    assert "duplicate_field_error.xlsx:#export[E1]" in output
    
    
    
def test_malformed_tag_error():
    """Test that error is printed when # is in a bad token."""
    
    test_file = "malformed_tag_error.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
        
    assert "malformed or unrecognized tag \"#\" at cell" in output  
    assert "malformed_tag_error.xlsx:#export[D1]" in output
    
    

def test_bad_token_error():
    """Test that error is printed when there is a bad token."""
    
    test_file = "bad_token_error.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
        
    assert "bad token \"&\" at cell" in output  
    assert "bad_token_error.xlsx:#export[D1]" in output



def test_child_id_no_assignment():
    """Test that when a child record is created with explicit id it works."""
    
    test_file = "child_id_no_assignment.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    assert output == ""
    assert "1" in output_json["sample"]
    assert "2" in output_json["sample"]



def test_child_without_id_error():
    """Test that error is printed when there is a child record with no id."""
    
    test_file = "child_without_id_error.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
        
    assert "#.child record without id at cell" in output  
    assert "child_without_id_error.xlsx:#export[:1]" in output
    
    
    
def test_same_record_multiple_tables():
    """Test that the same record across multiple tables works."""
    
    test_file = "same_record_multiple_tables.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    assert output == ""
    assert "protein_weight" in output_json["sample"]["01_A0_Spleen_naive_0days_170427_UKy_GCH_rep1"]
    assert output_json["sample"]["01_A0_Spleen_naive_0days_170427_UKy_GCH_rep1"]["protein_weight"] == "0"
    assert output_json["sample"]["01_A0_Spleen_naive_0days_170427_UKy_GCH_rep1"]["protocol.id"] == [
                                                                                                      "mouse_tissue_collection",
                                                                                                      "tissue_quench",
                                                                                                      "frozen_tissue_grind",
                                                                                                      "protein_extraction"
                                                                                                    ]




def test_no_data_message_xlsx():
    """Test that a message is printed when there is no data in a worksheet."""
    
    test_file = "no_data_message.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
            
    assert "There is no data in worksheet" in output
    assert "no_data_message.xlsx:#export" in output
    

def test_no_data_message_Google_Sheets():
    """Test that a message is printed when there is no data in a worksheet."""
    
    test_file = "https://docs.google.com/spreadsheets/d/1_wGthpMlf_cnV15pGY2K_iqUEvy7rYwsqOSjQ5LTJG0/edit#gid=706429643"
    
    command = "messes extract " + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
            
    assert "There is no data in the sheet, #export, of the Google Sheets file" in output
    assert "https://docs.google.com/spreadsheets/d/1_wGthpMlf_cnV15pGY2K_iqUEvy7rYwsqOSjQ5LTJG0/export?format=xlsx" in output



def test_no_sheet_message_xlsx():
    """Test that a message is printed when the user input sheet name is not found."""
    
    test_file = "base_source.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix() + " --modify asdf"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
            
    assert 'r\'^asdf$\' did not match any sheets in' in output
    assert 'base_source.xlsx' in output
    

def test_no_sheet_message_Google_Sheets():
    """Test that a message is printed when the user input sheet name is not found."""
    
    test_file = "https://docs.google.com/spreadsheets/d/1jDMQjFeyETsI_uBQ7v-K2F4w18U-l_HJ9v0EJ4Bm0bg/edit?pli=1#gid=609251734"
    
    command = "messes extract " + test_file  + " --output " + output_path.as_posix() + " --modify asdf"
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
            
    assert 'r\'^asdf$\' did not match any sheets in' in output
    assert 'https://docs.google.com/spreadsheets/d/1jDMQjFeyETsI_uBQ7v-K2F4w18U-l_HJ9v0EJ4Bm0bg/export?format=xlsx' in output



def test_no_data_message_csv():
    """Test that a message is printed when there is no data in a csv file."""
    
    test_file = "no_data_message.csv"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
            
    assert 'There is no data in csv file' in output
    assert "no_data_message.csv" in output
    
    
    
def test_no_csv_file():
    """Test that a message is printed when the input csv file does not exist."""
    
    test_file = "asdf.csv"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
            
    assert 'The csv file' in output
    assert "asdf.csv" in output
    assert "does not exist." in output
    
    
    
def test_invalid_worksheet_identifier():
    """Test that an exception is raised when an input file is incorrectly specified."""
    
    test_file = "asdf.csv:asdf"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
            
    assert 'Invalid worksheet identifier' in output
    assert "asdf.csv:asdf" in output
    assert "passed into function." in output
    
    
    
def test_metadata_json_source():
    """Test that a metadata json source is concatenated with new data."""
    
    test_file = "starting_metadata_test.json"
    test_file2 = "starting_metadata_test.xlsx"
    
    command = "messes extract ../" + test_file + " ../" + test_file2  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    with open(pathlib.Path("output_compare.json"), "r") as f:
        output_compare_json = json.loads(f.read())
        
    assert "test" in output_json
    assert "01_A0_Spleen_naive_0days_170427_UKy_GCH_rep1" in output_json["test"]
    del output_json["test"]
    assert output_json == output_compare_json
            
    assert output == ""



def test_field_concatenation():
    """Test that tags can be concated with a + sign."""
    
    test_file = "tag_concatenation_test.xlsx"
    
    command = "messes extract ../" + test_file + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert output_path.exists()
    
    with open(output_path, "r") as f:
        output_json = json.loads(f.read())
        
    assert output_json["study"]["Study 1"]["title"] == "labeled mouse study 278 Type1"
            
    assert output == ""



def test_second_table_specified():
    """Test that an exception is raised when a second table is on the same tag row specified."""
    
    test_file = "second_table_error.xlsx"
    
    command = "messes extract ../" + test_file  + " --output " + output_path.as_posix()
    command = command.split(" ")
    subp = subprocess.run(command, capture_output=True, encoding="UTF-8")
    output = subp.stderr

    
    assert not output_path.exists()
            
    assert 'second table specified after first table, if trying to specify an id to another table use #.table.id at cell' in output
    assert "second_table_error.xlsx:#export[C1]" in output


