#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from json import loads
from os import walk
from os.path import exists, isdir, isfile, join
from typing import Iterator


def read_files(*sources: list[str]) -> Iterator[dict]:
    """Generator method for validating file and directory paths and yielding the dictionary objects within the given file(s).

    Args:
        sources: A list of JSON filepaths.
        
    Returns:
        Aniterator of file contents.
    """
    for source in sources:
        if isdir(source):
            (_, _, filenames) = next(walk(source))
            for filename in filenames:
                yield open_json_file(join(source, filename))
        elif isfile(source):
            yield open_json_file(source)
        else:
            raise TypeError("Unknown file source.")


def open_json_file(filepath: str) -> dict:
    """Method for validating a given filepath to an existing JSON file and returning the converted dictionary object.

    Args:
        filepath: Path to the JSON file.
    
    Returns:
        File contents as a dictionary.
    """
    internal_data = None
    if exists(filepath):
        try:
            with open(filepath, "r") as f:
                internal_data = loads(f.read())
        except Exception as e:
            raise e

    return internal_data
