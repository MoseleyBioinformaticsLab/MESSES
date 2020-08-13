from os import system
from messes import __version__
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


def test_version_command():
    """Method to test the '--version' commandline method.

    Method uses Python's subprocess package to call the '--version' commandline method and capture the output. The
    output is then decoded and asserted to be equal to the installed package version.

    :raises AssertionError: Raises AssertionError if method fails
    :return:
    """
    command = "python -m messes --version"
    returned_output = check_output(command, shell=True).decode("utf-8").strip()
    assert returned_output == __version__


@pytest.mark.parametrize("files_source, analysis_type, to_path, config_source", [
    ("tests/example_data/internal_data_files/DI-FTMS_Results_colon.json", "MS",
     "tests/example_data/tmp/mwtab/mwtab_DI-FTMS_Results_colon.txt", "config_files/DI-FTMS_config.json"),
    ("tests/example_data/internal_data_files/ICMS_Results_colon-2020-06-08.json", "MS",
     "tests/example_data/tmp/mwtab/mwtab_ICMS_Results_colon-2020-06-08.txt", "config_files/ICMS_config.json"),
])
def test_convert_command(files_source, analysis_type, to_path, config_source):
    """Method to test the 'convert' commandline method.

    messes convert <from-path> <analysis-type> [--to-path=<path>] [--protocol-id=<id>] [--config-file=<path>]

    :param files_source:
    :param analysis_type:
    :param to_path:
    :param config_source
    :type files_source: str
    :type analysis_type: str
    :type to_path: str
    :type config_source: str
    :return:
    """
    command = "python -m messes convert {} {} --to-path={} --config-file={}".format(
        files_source, analysis_type, to_path, config_source
    )
    assert system(command) == 0
