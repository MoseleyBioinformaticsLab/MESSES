# -*- coding: utf-8 -*-
"""
helper functions used throughout the package.
"""

import sys
import collections.abc



def _handle_errors(required: bool, silent: bool, message: str) -> None:
    """If required is True print message as error and exit, else print message as warning if silent is False.
    
    Args:
        required: if the directive is required or not, if True then an error has occurred and we need to exit.
        silent: whether to print a warning message or not.
        message: the message to be printed.
    """
    if required:
        print("Error:  " + message, file=sys.stderr)
        sys.exit()
    else:
        if not silent:
            print("Warning:  " + message, file=sys.stderr)


def _update(original_dict: dict, upgrade_dict: dict) -> dict:
    """Update a dictionary in a nested fashion.
    
    Args:
        original_dict: the dictionary to update.
        upgrade_dict: the dictionary to update values from.
        
    Returns:
        original_dict, the updated original_dict
    """
    for key, value in upgrade_dict.items():
        if isinstance(value, collections.abc.Mapping):
            original_dict[key] = _update(original_dict.get(key, {}), value)
        else:
            original_dict[key] = value
    return original_dict


# def _nested_set(dic: dict, keys: list[str], value: Any) -> None:
#     """Creates nested dictionaries in dic for all but the last key and creates a key value pair in the last dictionary.
    
#     Args:
#         dic: the dictionary to set the value in.
#         keys: the keys to nest in the dictionaries.
#         value: the value to set the last key to in the deepest dicitonary.
#     """
#     for key in keys[:-1]:
#         dic = dic.setdefault(key, {})
#     dic[keys[-1]] = value


def _sort_by_getter(pair: tuple[str,dict], keys: list[str]) -> list:
    """Piece of a sorted call to return the values of certain keys in a dictionary.
    
    Args:
        pair: the tuple from calling items() on a dict.
        keys: a list of keys to retrieve values from the second element in pair.
        
    Returns:
        a list of the field values from the dict in the tuple based on keys.
        
    Raises:
        KeyError: if any key in keys is not in the second element of pair.
    """
    try:
        return [pair[1][key] for key in keys]
    except KeyError as e:
        e.pair = pair
        raise e

# def _sort_table_records(sort_by, table_records, reverse, conversion_record_name, conversion_table, input_table, required, silent):
#     try:
#         table_records = dict(sorted(table_records.items(), key = lambda pair: _sort_by_getter(pair, sort_by), reverse = reverse))
#         ## table_records used to be a list of dicts and this was the sort, leaving it here in case it is needed.
#         # table_records = sorted(table_records, key = operator.itemgetter(*sort_by), reverse = conversion_attributes["sort_order"] == "descending")
#     except KeyError as e:
#         message = "The \"sort_by\" conversion directive to create the \"" + conversion_record_name + \
#                   "\" conversion in the \"" + conversion_table + "\" table has an input key, " + str(e) + \
#                   ", that was not in the \"" + e.pair[0] + "\" record of the \"" + input_table + "\"."
#         return _handle_errors(required, silent, message)
    
#     return table_records


def _str_to_boolean_get(default: bool, key: str, input_dict: dict) -> bool:
    """Read the field and convert to boolean.
    
    Args:
        default: the default boolean value to return if not found.
        key: the key to the dict to look for the value of.
        input_dict: the dict to look for the key in.
    
    Returns:
        the vlaue of the key as a bool.
    """
    attribute = default
    if (temp_attribute := input_dict.get(key)) is not None:
        if isinstance(temp_attribute, bool):
            attribute = temp_attribute
        elif isinstance(temp_attribute, str):
            if temp_attribute.lower() == "false":
                attribute = False
            else:
                attribute = True
            
    return attribute



