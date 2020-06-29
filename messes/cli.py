#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
The messes command-line interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Usage:
    messes -h | --help
    messes --version
    messes convert <from-path> <analysis-type> [--to-path=<path>] [--protocol-id=<id>] [--config-file=<path>]

Options:
    -h, --help                      Show this screen.
    --version                       Show version.
    --to-path=<path>                Path for converted file to be outputted to.
    --protocol-id=<id>              Analysis protocol type of the data file.
    --config-file=<path>            Path to JSON configuration file.
"""

from messes.convert import convert
from messes.fileio import read_files
from os.path import dirname, join
from os import makedirs
import json
from datetime import datetime
import mwtab


def cli(cmdargs):

    # messes convert ...
    if cmdargs["convert"]:

        # ensure an results directory exists
        results_dir = cmdargs.get("--to-path")
        if not results_dir:
            results_dir = "conversion_results"
            makedirs(results_dir)

        for internal_data in read_files(cmdargs["<from-path>"]):
            mwtabfile = convert(internal_data, cmdargs["<analysis-type>"], cmdargs.get("--protocol-id"))

            filename = str(datetime.now()).replace(".", "_").replace(":", "_").replace(" ", "_")
            mwtab_json_fpath = join(results_dir, 'mwtab_{}.json'.format(filename))
            mwtab_txt_fpath = join(results_dir, 'mwtab_{}.txt'.format(filename))

            with open(mwtab_json_fpath, 'w') as outfile:
                json.dump(mwtabfile, outfile, indent=4)

            with open(mwtab_txt_fpath, 'w') as outfile:
                mwfile = next(mwtab.read_files(mwtab_json_fpath))
                mwfile.write(outfile, file_format="mwtab")
