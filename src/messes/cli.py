#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
The messes command-line interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Usage:
    messes -h | --help
    messes --version
    messes extract
    messes convert <from-path> <analysis-type> [--to-path=<path>] [--protocol-id=<id>] [--config-file=<path>]

Options:
    -h, --help                      Show this screen.
    -v, --version                   Show version.
    --t, --to-path=<path>           Path for converted file to be outputted to.
    --p, --protocol-id=<id>         Analysis protocol type of the data file.
    --c, --config-file=<path>       Path to JSON configuration file.
"""

from messes.convert import convert
from messes.fileio import read_files, open_json_file
from os.path import basename, dirname, exists, isdir, join, splitext
from os import makedirs, walk

import json
import mwtab


def cli(cmdargs: dict):
    """Method uses docopt package to parse commandline arguments and perform actions accordingly.

    Args:
        cmdargs: Dictionary of parse commandline arguments.
    """

    # messes convert ...
    if cmdargs["convert"]:

        # parse configuration keyword arguments, provided they are supplied
        config_filepath = cmdargs.get("--config-file")
        config_dict = {}
        if config_filepath:
            config_dict = open_json_file(config_filepath)

        # used when converting directory full of files
        if isdir(cmdargs["<from-path>"]):
            (_, _, filenames) = next(walk(cmdargs["<from-path>"]))

        # convert given file(s)
        for count, internal_data in enumerate(read_files(cmdargs["<from-path>"])):
            mwtabfile = convert(internal_data, cmdargs["<analysis-type>"], cmdargs.get("--protocol-id"), config_dict)

            # save out converted file(s)
            # ensure an results directory exists
            results_dir = cmdargs.get("--to-path")
            if not results_dir:
                results_dir = "conversion_results/"
            if not exists(dirname(results_dir)):
                makedirs(dirname(results_dir))

            if cmdargs.get("--to-path"):
                if basename(cmdargs["--to-path"]):  # output path and filename are given
                    results_path = cmdargs["--to-path"]
                else:
                    if basename(cmdargs["<from-path>"]):  # output path is given and input is single file
                        results_path = join(cmdargs["--to-path"], "mwtab_{}".format(basename(cmdargs["<from-path>"])))
                    else:  # output path is given and input is directory
                        results_path = join(cmdargs["--to-path"], "mwtab_{}".format(filenames[count]))
            else:
                if basename(cmdargs["<from-path>"]):  # input is single file
                    results_path = join(results_dir, "mwtab_{}".format(basename(cmdargs["<from-path>"])))
                else:  # output path is given and input is directory
                    results_path = join(results_dir, "mwtab_{}".format(filenames[count]))

            mwtab_json_fpath = "{}.json".format(splitext(results_path)[0])
            mwtab_txt_fpath = "{}.txt".format(splitext(results_path)[0])
            # save JSON
            with open(mwtab_json_fpath, 'w', encoding="utf-8") as outfile:
                json.dump(mwtabfile, outfile, indent=4)
            # save mwTab (.txt)
            with open(mwtab_txt_fpath, 'w', encoding="utf-8") as outfile:
                mwfile = next(mwtab.read_files(mwtab_json_fpath))
                mwfile.write(outfile, file_format="mwtab")
