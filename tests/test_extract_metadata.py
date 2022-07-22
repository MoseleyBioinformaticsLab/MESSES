# -*- coding: utf-8 -*-
import pytest

import pathlib
import os
import time
import copy


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




def test_conversion_id_change():
    """Test that a warning is printed when the conversion changes 2 or more records to the same id."""
    
    command = "python ../../../src/messes/extract_metadata.py "
    os.system(command)
    
    assert metadata_path.exists()
    
    metadata = load_json(metadata_path.as_posix())
    
    del metadata["date"]
    del metadata_compare["date"]
    
    assert metadata_compare == metadata
    
def test_multiple_inserts():
    """Test that #insert in a #tags block is inserted multiple times when #multiple=true."""
    
def test_multiple_insert_blocks():
    """Test that all #insert blocks are added in the export."""
