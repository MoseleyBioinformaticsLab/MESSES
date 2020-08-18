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
from messes.fileio import read_files, open_json_file
from os.path import basename, dirname, exists, join, splitext
from os import makedirs
import json
import mwtab


def cli(cmdargs):
    """Method uses docopt package to parse commandline arguments and perform actions accordingly.

    :param cmdargs: Dictionary of parse commandline arguments.
    :type cmdargs: dict
    """

    # messes convert ...
    if cmdargs["convert"]:

        # parse configuration keyword arguments, provided they are supplied.
        config_filepath = cmdargs.get("--config-file")
        config_dict = {}
        if config_filepath:
            config_dict = open_json_file(config_filepath)

        # convert given file(s)
        for internal_data in read_files(cmdargs["<from-path>"]):
            mwtabfile = convert(internal_data, cmdargs["<analysis-type>"], cmdargs.get("--protocol-id"), config_dict)

            # save out converted file(s)
            # ensure an results directory exists
            results_dir = cmdargs.get("--to-path")
            if not results_dir:
                results_dir = "conversion_results/"
            if not exists(dirname(results_dir)):
                makedirs(dirname(results_dir))

            if basename(basename(cmdargs["--to-path"])):
                if splitext(cmdargs["--to-path"])[0] == ".txt":
                    with open(cmdargs["--to-path"], 'w', encoding="utf-8") as outfile:
                        mwtabfile.write(outfile, file_format="mwtab")
                elif splitext(cmdargs["--to-path"])[0].lower() == ".json":
                    with open(cmdargs["--to-path"], 'w', encoding="utf-8") as outfile:
                        json.dump(mwtabfile, outfile, indent=4)
                else:
                    raise ValueError("\"--to-path\" parameter contains invalid file extension (use either .txt or .json)")
            else:
                filename = splitext(basename(cmdargs["<from-path>"]))[0]
                mwtab_json_fpath = join(results_dir, 'mwtab_{}.json'.format(filename))
                mwtab_txt_fpath = join(results_dir, 'mwtab_{}.txt'.format(filename))
                # save JSON
                with open(mwtab_json_fpath, 'w', encoding="utf-8") as outfile:
                    json.dump(mwtabfile, outfile, indent=4)
                # save mwTab (.txt)
                with open(mwtab_txt_fpath, 'w', encoding="utf-8") as outfile:
                    mwfile = next(mwtab.read_files(mwtab_json_fpath))
                    mwfile.write(outfile, file_format="mwtab")
