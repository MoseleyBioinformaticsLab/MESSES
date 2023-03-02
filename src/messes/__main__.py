#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MESSES Command-Line Interface
    The MESSES package has functionality to extract data, validate data, and convert data to other formats for deposition into public repositories.
    
Online Documentation: https://moseleybioinformaticslab.github.io/messes/

Usage:
    messes -h | --help     print this screen.
    messes --full-help     help documentation on all commands.
    messes --version       print the version.
    messes extract ...     extract data from Excel workbooks, csv files, and JSON.
    messes validate ...    validate JSON files.
    messes convert ...     convert JSON to other file formats.

For help on a specific command, use the command option -h or --help.
For example:
    messes extract --help   for help documentation about the extract command.
"""

import sys

from messes import __version__
from messes.extract import extract
from messes.validate import validate
from messes.convert import convert


def main():
    
    if len(sys.argv) > 1 and sys.argv[1] == "extract":
        extract.main()
    elif len(sys.argv) > 1 and sys.argv[1] == "validate":
        validate.main()
    elif len(sys.argv) > 2 and sys.argv[1] == "convert":
        convert.main()
    elif len(sys.argv) > 1 and (sys.argv[1] == "--version" or sys.argv[1] == "-v") :
        print("Version: ",__version__)
    elif len(sys.argv) > 1 and sys.argv[1] == "--full-help":
        print(__doc__)
        print("-"*80)
        print(extract.__doc__)
        print("-"*80)
        print(validate.__doc__)
        print("-"*80)
        print(convert.__doc__)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()

