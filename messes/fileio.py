#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from json import loads
from os import walk
from os.path import exists, isdir, isfile

from os.path import dirname
from os import makedirs


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
                yield open_internal_data_file(filename)
        elif isfile(source):
            yield open_internal_data_file(source)
        else:
            raise TypeError("Unknown file source.")


def open_internal_data_file(internal_data_filepath):
    """
    Method for validating a given filepath to an internal JSON data exists and returning the

    :param str internal_data_filepath:
    :return:
    """
    internal_data = None
    if exists(internal_data_filepath):
        try:
            with open(internal_data_filepath, "r") as f:
                internal_data = loads(f.read())
        except Exception as e:
            raise e

    return internal_data


# def write(mwtabfile, results_path):
#     """Method for
#
#     :param mwtabfile:
#     :param str results_path: Directory for resulting mwtab files to be output into.
#     :return:
#     """
#     # ensure directories exist in given file path
#     if not exists(dirname(results_path)):
#         makedirs(dirname(results_path))
#
#     internal_data_fname = os.path.basename(internal_data_fpath)
#     internal_data_fname_parts = internal_data_fname.split('.')
#
#     if internal_data_fname_parts[-1].lower() == 'json':
#         internal_data_fname_parts.pop()  # remove extension
#         basefname = ''.join(internal_data_fname_parts)
#     else:
#         basefname = ''.join(internal_data_fname_parts)
#
#     mwtab_json_fpath = os.path.join(results_dir, 'mwtab_{}{}.json'.format(basefname, protocol_id))
#     mwtab_txt_fpath = os.path.join(results_dir, 'mwtab_{}{}.txt'.format(basefname, protocol_id))
#
#     with open(mwtab_json_fpath, 'w') as outfile:
#         json.dump(mwtabfile, outfile, indent=4)
#
#     with open(mwtab_json_fpath, 'r') as infile, open(mwtab_txt_fpath, 'w') as outfile:
#         mwfile = next(mwtab.read_files(mwtab_json_fpath))
#         mwfile.write(outfile, file_format="mwtab")
