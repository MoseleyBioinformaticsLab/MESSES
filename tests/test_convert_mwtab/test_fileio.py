from messes.fileio import read_files


def test_read_files():
    """Method to test messes.fileio.read_files() method.

    :raises AssertionError: Raises AssertionError if method fails
    :return:
    """
    f_generator = read_files("tests/example_data/internal_data_files")
    assert len(list(f_generator)) == 4
