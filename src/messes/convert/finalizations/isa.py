# -*- coding: utf-8 -*-
"""
Code for finalizing ISA conversion.
"""

import pathlib

from isatools.convert import json2isatab
from isatools import isajson, isatab

from messes.convert import isa_functions


def finalization(json_save_name: str, silent: bool) -> None:
    """
    """
    
    validation_messages = isajson.validate(open(json_save_name))
    isa_functions.isa_validation_message_formatting(validation_messages, silent, **isa_functions.json_formatting_dict)
    
    with open(json_save_name) as file_pointer:
        json2isatab.convert(file_pointer, "ISA_Tab", validate_first=False)

    validation_messages = isatab.validate(open(pathlib.Path("ISA_Tab", "i_investigation.txt")))
    isa_functions.isa_validation_message_formatting(validation_messages, silent, **isa_functions.tab_formatting_dict)

