from os import system, walk
from messes.fileio import read_files, open_json_file
from os.path import exists
from shutil import rmtree
from subprocess import check_output
import pytest


def teardown_module(module):
    """pytest teardown method for removing temporary files

    :param module:
    :return: None
    """
    if exists("tests/example_data/tmp/"):
        rmtree("tests/example_data/tmp")


def test_read_files():
    f_generator = read_files("example_data/internal_data_files/")
    assert len(list(f_generator)) == 4


if __name__ == "__main__":
    test_read_files()
