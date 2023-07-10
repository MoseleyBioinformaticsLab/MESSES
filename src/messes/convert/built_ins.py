# -*- coding: utf-8 -*-
"""
Built-in functions for the convert command.
"""

import re

from messes.convert import regexes
literal_regex = regexes.literal_regex

def dumb_parse_ontology_annotation(annotations: str|list) -> dict|list[dict]|None:
    """Create ontology annotation dict or list of dicts from str or list of str.
    
    Args:
        annotations: str or list of str in expected "source:accession:value:comment" format.
        
    Returns:
        A tuple of (message, value), where the message will be None if there are no errors and the value will be None if there are.
        If the annotations parameter is a string, then the value will be a ISA ontologyAnnotation dictionary.
        If the annotations parameter is a list, then the value will be a list of ISA ontologyAnnotation dictionaries.
    """
    annotations_is_string = False
    if isinstance(annotations, str):
        annotations = [annotations]
        annotations_is_string = True
    
    parsed_annotation_dicts = []
    for annotation in annotations:
        annotation_dict = {}
        annotation_parts = [match.group(1) if (match := re.match(literal_regex, part.strip())) else part.strip() for part in annotation.split(":")]
        if len(annotation_parts) != 4:
            message = ("When creating the \"{conversion_record_name}\" conversion "
                       "for the \"{conversion_table}\" table, a record, \"{record_name}\","
                       "in the table, \"{record_table}\", has a malformed ontology annotation, "
                       f"\"{annotation}\", "
                       "in the field, \"{record_field}\". It must have 3 colons (:) separating its values.")
            return message, None
        for i, value in enumerate(annotation_parts):
            if value:
                match i:
                    case 0:
                        annotation_dict["termSource"] = value
                    case 1:
                        annotation_dict["termAccession"] = value
                    case 2:
                        annotation_dict["annotationValue"] = value
                    case 3:
                        annotation_dict["comments"] = [{"value":value}]
                        
        parsed_annotation_dicts.append(annotation_dict)
    
    if annotations_is_string:
        return None, parsed_annotation_dicts[0]
    else:
        return None, parsed_annotation_dicts
 


def to_dict(field_values: str|list) -> dict|list[dict]|None:
    """Create dict or list of dicts from str or list of str.
    
    Args:
        field_values: str or list of str in expected "key:value,key:value..." format.
        
    Returns:
        A tuple of (message, value), where the message will be None if there are no errors and the value will be None if there are.
        If the field_values parameter is a string, then the value will be a dictionary.
        If the field_values parameter is a list, then the value will be a list of dictionaries.
    """
    field_values_is_string = False
    if isinstance(field_values, str):
        field_values = [field_values]
        field_values_is_string = True
    
    parsed_field_value_dicts = []
    for field_value in field_values:
        field_value_dict = {}
        field_value_parts = [part.strip() for part in field_value.split(",")]
        for pair in field_value_parts:
            try:
                key, value = [match.group(1) if (match := re.match(literal_regex, part.strip())) else part.strip() for part in pair.split(":")]
            except ValueError:
                message = ("When creating the \"{conversion_record_name}\" conversion "
                           "for the \"{conversion_table}\" table, a record, \"{record_name}\","
                           "in the table, \"{record_table}\", has a malformed dictionary, "
                           f"\"{field_value}\", "
                           "in the field, \"{record_field}\". It must have a form like \"key:value,key:value...\".")
                return message, None
            field_value_dict[key] = value
                        
        parsed_field_value_dicts.append(field_value_dict)
    
    if field_values_is_string:
        return None, parsed_field_value_dicts[0]
    else:
        return None, parsed_field_value_dicts


