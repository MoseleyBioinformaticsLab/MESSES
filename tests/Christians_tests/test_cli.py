from os import system, walk
from messes import __version__
from os.path import basename, exists, splitext
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


def test_version_command():
    """Method to test the '--version' commandline method.

    Method uses Python's subprocess package to call the '--version' commandline method and capture the output. The
    output is then decoded and asserted to be equal to the installed package version.

    :raises AssertionError: Raises AssertionError if method fails
    :return:
    """
    command = "messes --version"
    returned_output = check_output(command, shell=True).decode("utf-8").strip()
    assert returned_output == "Version: " + __version__


@pytest.mark.parametrize("files_source, analysis_type, etc", [
    ("tests/example_data/internal_data_files/DI-FTMS_Results_colon.json", "MS",
     "--t=tests/example_data/tmp/ --c=tests/config_files/DI-FTMS_config.json"),
    ("tests/example_data/internal_data_files/ICMS_Results_colon-2020-06-08.json", "MS",
     "--t=tests/example_data/tmp/ --c=tests/config_files/ICMS_config.json"),
    ("tests/example_data/internal_data_files/NMR_Results_colon_1H-2020-06-10.json", "NMR",
     "--p=NMR1 --t=tests/example_data/tmp/ --c=tests/config_files/NMR_config.json"),
    ("tests/example_data/internal_data_files/NMR_Results_colon_HSQC-2020-06-10.json", "NMR",
     "--p=NMR2 --t=tests/example_data/tmp/ --c=tests/config_files/NMR_config.json"),
    ("tests/example_data/internal_data_files/test_directory/", "NMR",
     "--p=NMR1 --t=tests/example_data/tmp/ --c=tests/config_files/NMR_config.json"),
])
def test_convert_command(files_source, analysis_type, etc):
    """Method to test the 'convert' commandline method.

    :return:
    """
    command = "messes convert mwtab {} {} {}".format(
        files_source, analysis_type, etc
    )
    assert system(command) == 0

    params = {items.split("=")[0]: items.split("=")[1] for items in etc.split()}

    if basename(files_source):
        assert "mwtab_{}.txt".format(splitext(basename(files_source))[0]) in next(walk(params["--t"]))[2]
        assert "mwtab_{}.json".format(splitext(basename(files_source))[0]) in next(walk(params["--t"]))[2]
    else:
        for filename in next(walk(files_source))[2]:
            assert "mwtab_{}.txt".format(splitext(basename(filename))[0]) in next(walk(params["--t"]))[2]
            assert "mwtab_{}.json".format(splitext(basename(filename))[0]) in next(walk(params["--t"]))[2]
