# -*- coding: utf-8 -*-
"""
Functions For ISA Format
------------------------
"""


def _handle_errors():
    """
    """

import re



tab_warning_codes_to_skip = [3002]
tab_warning_messages_to_skip = []
tab_warning_supplemental_to_skip = [r'Protocol(s) of type (.*) defined in the ISA-configuration (.*)']

tab_warning_codes_to_modify = []
tab_warning_codes_modification = []
tab_warning_messages_to_modify = [r'A required node factor value is missing value']
tab_warning_messages_modification = ["warning['supplemental']"]
tab_warning_supplemental_to_modify = [r'A property value in (.*) is required']
tab_warning_supplemental_modification = ["warning['supplemental'].replace('required', 'missing')"]


tab_error_codes_to_skip = []
tab_error_messages_to_skip = [r'Measurement/technology type invalid']
tab_error_supplemental_to_skip = []

tab_error_codes_to_modify = []
tab_error_codes_modification = []
tab_error_messages_to_modify = []
tab_error_messages_modification = []
tab_error_supplemental_to_modify = []
tab_error_supplemental_modification = []


json_warning_codes_to_skip = [4004, 3002]
json_warning_messages_to_skip = []
json_warning_supplemental_to_skip = []

json_warning_codes_to_modify = []
json_warning_codes_modification = []
json_warning_messages_to_modify = []
json_warning_messages_modification = []
json_warning_supplemental_to_modify = []
json_warning_supplemental_modification = []


json_error_codes_to_skip = []
json_error_messages_to_skip = []
json_error_supplemental_to_skip = []

json_error_codes_to_modify = []
json_error_codes_modification = []
json_error_messages_to_modify = []
json_error_messages_modification = []
json_error_supplemental_to_modify = []
json_error_supplemental_modification = []




def isa_validation_message_formatting(validation_messages: dict, silent: bool,
                                      warning_codes_to_skip: list[int],
                                      warning_messages_to_skip: list[str],
                                      warning_supplemental_to_skip: list[str],
                                      warning_codes_to_modify: list[int],
                                      warning_codes_modification: list[str],
                                      warning_messages_to_modify: list[str],
                                      warning_messages_modification: list[str],
                                      warning_supplemental_to_modify: list[str],
                                      warning_supplemental_modification: list[str],
                                      error_codes_to_skip: list[int],
                                      error_messages_to_skip: list[str],
                                      error_supplemental_to_skip: list[str],
                                      error_codes_to_modify: list[int],
                                      error_codes_modification: list[str],
                                      error_messages_to_modify: list[str],
                                      error_messages_modification: list[str],
                                      error_supplemental_to_modify: list[str],
                                      error_supplemental_modification: list[str]):
    """
    """
    if validation_messages["validation_finished"]:
        message = ("An unknown error was encountered when validating the ISA format. "
                   "Due to this, the validation was not able to be completed.")
        _handle_errors(True, silent, message)
        
    for warning in validation_messages["warnings"]:
        ## Look to skip.
        if warning['code'] in warning_codes_to_skip or\
           any([True for regex in warning_messages_to_skip if re.match(regex, warning['message'])]) or\
           any([True for regex in warning_supplemental_to_skip if re.match(regex, warning['supplemental'])]):
            continue
        ## Look to modify.
        if warning['code'] in warning_codes_to_modify:
            modification = warning_codes_modification[warning_codes_to_modify.index(warning['code'])]
            _handle_errors(False, silent, eval(modification))
            continue
        
        needs_continue = False
        for i, regex in enumerate(warning_messages_to_modify):
            if re.match(regex, warning['message']):
                needs_continue = True
                modification = warning_messages_modification[i]
                _handle_errors(False, silent, eval(modification))
                break
        if needs_continue:
            continue
        
        needs_continue = False
        for i, regex in enumerate(warning_supplemental_to_modify):
            if re.match(regex, warning['supplemental']):
                needs_continue = True
                modification = warning_supplemental_modification[i]
                _handle_errors(False, silent, eval(modification))
                break
        if needs_continue:
            continue
        
        _handle_errors(False, silent, f"{warning['message']} \n{warning['supplemental']}")
    

    for error in validation_messages["errors"]:
        ## Look to skip.
        if error['code'] in error_codes_to_skip or\
           any([True for regex in error_messages_to_skip if re.match(regex, error['message'])]) or\
           any([True for regex in error_supplemental_to_skip if re.match(regex, error['supplemental'])]):
            continue
        ## Look to modify.
        if error['code'] in error_codes_to_modify:
            modification = error_codes_modification[error_codes_to_modify.index(error['code'])]
            _handle_errors(True, silent, eval(modification))
            continue
        
        needs_continue = False
        for i, regex in enumerate(error_messages_to_modify):
            if re.match(regex, error['message']):
                needs_continue = True
                modification = error_messages_modification[i]
                _handle_errors(True, silent, eval(modification))
                break
        if needs_continue:
            continue
        
        needs_continue = False
        for i, regex in enumerate(error_supplemental_to_modify):
            if re.match(regex, error['supplemental']):
                needs_continue = True
                modification = error_supplemental_modification[i]
                _handle_errors(True, silent, eval(modification))
                break
        if needs_continue:
            continue
        
        _handle_errors(True, silent, f"{error['message']} \n{error['supplemental']}")



