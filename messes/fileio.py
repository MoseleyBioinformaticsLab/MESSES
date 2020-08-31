#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from json import loads
from os import walk
from os.path import exists, isdir, isfile, join


def read_files(*sources):
    """
    Generator method for validating file and directory paths and yielding the dictionary objects within the given
    file(s).

    :param sources:
    :return:
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


def open_json_file(filepath):
    """
    Method for validating a given filepath to an existing JSON file and returning the converted dictionary object.

    :param str filepath:
    :return:
    """
    internal_data = None
    if exists(filepath):
        try:
            with open(filepath, "r") as f:
                internal_data = loads(f.read())
        except Exception as e:
            raise e

    return internal_data
