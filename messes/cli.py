#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from os.path import exists, dirname
from os import makedirs

"""
The messes command-line interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Usage:
    messes -h | --help
    messes --version
    messes convert (<from-path> <to-path>) <analysis-type> [--protocol-id=<id>] [--config-file=<path>]


Options:
    -h, --help                      Show this screen.
    --version                       Show version.
    --protocol-id=<id>              Analysis protocol type of the data file.
    --config-file=<path>            PAth to JSON configuration file.
"""


def write(mwtabfile, results_path):
    """Method for

    :param mwtabfile:
    :param str results_path: Directory for resulting mwtab files to be output into.
    :return:
    """
    # ensure directories exist in given file path
    if not exists(dirname(results_path)):
        makedirs(dirname(results_path))

    internal_data_fname = os.path.basename(internal_data_fpath)
    internal_data_fname_parts = internal_data_fname.split('.')

    if internal_data_fname_parts[-1].lower() == 'json':
        internal_data_fname_parts.pop()  # remove extension
        basefname = ''.join(internal_data_fname_parts)
    else:
        basefname = ''.join(internal_data_fname_parts)

    mwtab_json_fpath = os.path.join(results_dir, 'mwtab_{}{}.json'.format(basefname, protocol_id))
    mwtab_txt_fpath = os.path.join(results_dir, 'mwtab_{}{}.txt'.format(basefname, protocol_id))

    with open(mwtab_json_fpath, 'w') as outfile:
        json.dump(mwtabfile, outfile, indent=4)

    with open(mwtab_json_fpath, 'r') as infile, open(mwtab_txt_fpath, 'w') as outfile:
        mwfile = next(mwtab.read_files(mwtab_json_fpath))
        mwfile.write(outfile, file_format="mwtab")


def cli(cmdargs):

    # messes convert ...
    if cmdargs["convert"]:
        pass
