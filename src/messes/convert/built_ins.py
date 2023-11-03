# -*- coding: utf-8 -*-
"""
Built-in functions for the convert command.
"""

import re

from messes.convert import regexes
literal_regex = regexes.literal_regex

def dumb_parse_ontology_annotation(annotations: str|list) -> tuple[str|None, dict|list[dict]|None]:
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
            message = (f"\"{annotation}\" is a malformed ontology annotation. "
                       "It must have 3 colons (:) separating its values.")
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
 


def to_dict(field_values: str|list) -> tuple[str|None, dict|list[dict]|None]:
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
                message = (f"\"{field_value}\" is a malformed dictionary. "
                           "It must have a form like \"key:value,key:value...\".")
                return message, None
            field_value_dict[key] = value
                        
        parsed_field_value_dicts.append(field_value_dict)
    
    if field_values_is_string:
        return None, parsed_field_value_dicts[0]
    else:
        return None, parsed_field_value_dicts



def determine_ISA_parameters_dumb_parse(protocol_fields: dict) -> list[dict]:
    """Create a list of ISA JSON parameters from a protocol's fields.
    
    Loop over the keys in protocol_fields and look for keys that match the pattern 
    (.*)%isa_fieldtype$. If the value of those keys is "parameter" then look for 
    another key like "parameter_name%ontology_annotation" and parse its value to 
    create the parameterName dict for that parameter. If no ontology_annotation 
    attribute is found then create a simple annotation dict like {"annotationValue": parameter_name}.
    
    Args:
        protocol_fields: the protocol's fields to parse to look for parameters.
    
    Returns:
        A list of ISA JSON parameter objects or an empty list if no parameters were found.
    """
    parameters = []
    for field_name, field_value in protocol_fields.items():
        if (match := re.match(r"(.*)%isa_fieldtype$", field_name)) and field_value == "parameter":
            parameter_name = match.group(1)
            if annotation_string := protocol_fields.get(f"{parameter_name}%ontology_annotation"):
                annotation_dict = dumb_parse_ontology_annotation(annotation_string)
            else:
                annotation_dict = {"annotationValue": parameter_name}
            
            parameter_dict = {"@id": f"#parameter/{parameter_name}", "parameterName": annotation_dict}
            parameters.append(parameter_dict)
            
    return parameters



def determine_ISA_components_dumb_parse(protocol_fields: dict) -> list[dict]:
    """Create a list of ISA JSON components from a protocol's fields.
    
    Loop over the keys in protocol_fields and look for keys that match the pattern 
    (.*)%isa_fieldtype$. If the value of those keys is "component" then look for 
    another key like "component_type%ontology_annotation" and parse its value to 
    create the componentType dict for that component. If no ontology_annotation 
    attribute is found then create a simple annotation dict like {"annotationValue": component_type}. 
    componentName is set to protocol_fields[component_type].
    
    Args:
        protocol_fields: the protocol's fields to parse to look for components.
    
    Returns:
        A list of ISA JSON component objects or an empty list if no components were found.
    """
    components = []
    for field_name, field_value in protocol_fields.items():
        if (match := re.match(r"(.*)%isa_fieldtype$", field_name)) and field_value == "component":
            component_type = match.group(1)
            if annotation_string := protocol_fields.get(f"{component_type}%ontology_annotation"):
                annotation_dict = dumb_parse_ontology_annotation(annotation_string)
            else:
                annotation_dict = {"annotationValue": component_type}
            
            component_dict = {"componentName": protocol_fields[component_type], "componentType": annotation_dict}
            components.append(component_dict)
            
    return components


