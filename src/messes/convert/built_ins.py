# -*- coding: utf-8 -*-
"""
Built-in functions for the convert command.
"""

import re
from typing import Any

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
        A tuple of (message, parameters), where the message will be None if there are no errors.
        parameters are a list of ISA JSON parameter objects or an empty list if no parameters were found.
    """
    parameters = []
    message = None
    for field_name, field_value in protocol_fields.items():
        if (match := re.match(r"(.*)%isa_fieldtype$", field_name)) and field_value == "parameter":
            parameter_name = match.group(1)
            if annotation_string := protocol_fields.get(f"{parameter_name}%ontology_annotation"):
                message, annotation_dict = dumb_parse_ontology_annotation(annotation_string)
            else:
                annotation_dict = {"annotationValue": parameter_name}
            
            parameter_dict = {"@id": f"#parameter/{parameter_name}", "parameterName": annotation_dict}
            parameters.append(parameter_dict)
    parameters = None if not parameters else parameters
            
    return message, parameters



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
        A tuple of (message, components), where the message will be None if there are no errors.
        components are a list of ISA JSON component objects or an empty list if no components were found.
    """
    components = []
    message = None
    for field_name, field_value in protocol_fields.items():
        if (match := re.match(r"(.*)%isa_fieldtype$", field_name)) and field_value == "component":
            component_type = match.group(1)
            if annotation_string := protocol_fields.get(f"{component_type}%ontology_annotation"):
                message, annotation_dict = dumb_parse_ontology_annotation(annotation_string)
            else:
                annotation_dict = {"annotationValue": component_type}
            
            component_dict = {"componentName": protocol_fields[component_type], "componentType": annotation_dict}
            components.append(component_dict)
    components = None if not components else components
            
    return message, components


## Factors and characteristics are similar to components and parameters, but since there is a factor 
## table we do not need to have an isa_fieldtype field to distinguish them, only a way to mark things 
## as a characteristic. using isa_fieldtype might still be preferrable for consistency.
def determine_ISA_characteristics_dumb_parse(entity_fields: dict) -> list[dict]:
    """Create a list of ISA JSON characteristics from an entity's fields.
    
    Loop over the keys in entity_fields and look for keys that match the pattern 
    (.*)%isa_fieldtype$. If the value of those keys is "characteristic" then look for 
    other keys like "characteristic%isa_value" and parse its value to 
    create the dict for that key.
    
    Args:
        entity_fields: the entity's fields to parse to look for characteristics.
    
    Returns:
        A tuple of (message, characteristics), where the message will be None if there are no errors.
        characteristics are a list of ISA JSON characteristics objects or an empty list if no characteristics were found.
    """
    characteristics = []
    message = None
    for field_name, field_value in entity_fields.items():
        if (match := re.match(r"(.*)%isa_fieldtype$", field_name)) and field_value == "characteristic":
            characteristic = match.group(1)
            
            characteristic_dict = {"value": {"annotationValue": entity_fields[characteristic]}, 
                                   "category": {"@id": f"#characteristic/{characteristic}"}}
            
            if (value := entity_fields.get(f"{characteristic}%isa_value")):
                message, parsed_value = dumb_parse_ontology_annotation(value)
                characteristic_dict["value"] = parsed_value
            
            if (value := entity_fields.get(f"{characteristic}%isa_unit")):
                message, parsed_value = dumb_parse_ontology_annotation(value)
                characteristic_dict["unit"] = parsed_value
            elif (unit := entity_fields.get(f"{characteristic}%unit")) or (unit := entity_fields.get(f"{characteristic}%units")):
                characteristic_dict["unit"] = {"@id": f"#unit/{unit}",
                                               "annotationValue": unit}
                
            characteristics.append(characteristic_dict)
    characteristics = None if not characteristics else characteristics
            
    return message, characteristics



def determine_ISA_factor_values_dumb_parse(entity_fields: dict) -> list[dict]:
    """Create a list of ISA JSON factorValues from an entity's fields.
    
    Loop over the keys in entity_fields and look for keys that match the pattern 
    (.*)%isa_factorvalue$. Add the value of the key to a list.
    
    Args:
        entity_fields: the entity's fields to parse to look for factorValues.
    
    Returns:
        A tuple of (message, values), where the message will be None if there are no errors.
        values are a list of ISA JSON factorValues objects or an empty list if no factorValues were found.
    """
    values = []
    for field_name, field_value in entity_fields.items():
        if re.match(r"(.*)%isa_factorvalue$", field_name):
            values.append(field_value)
    values = None if not values else values
            
    return None, values



def determine_ISA_factor_type_dumb_parse(fields: dict) -> list[dict]:
    """Create an ontology annotation for factorType.
    
    Look for an "isa_type" field and parse that as an ontology annotation. 
    Otherwise create a simple annotation using the "id" field.
    
    Args:
        fields: the fields to look for "isa_type".
    
    Returns:
        A tuple of (message, annotation_dict), where the message will be None if there are no errors.
    """
    message = None
    if "isa_type" in fields:
        message, annotation_dict = dumb_parse_ontology_annotation(fields["isa_type"])
    else:
        annotation_dict = {"annotationValue": fields["id"]}
            
    return message, annotation_dict



def determine_ISA_protocol_type_dumb_parse(fields: dict) -> list[dict]:
    """Create an ontology annotation for protocolType.
    
    Look for an "isa_type" field and parse that as an ontology annotation. 
    Otherwise create a simple annotation using the "type" field.
    
    Args:
        fields: the fields to look for "isa_type".
    
    Returns:
        A tuple of (message, annotation_dict), where the message will be None if there are no errors.
    """
    message = None
    if "isa_type" in fields:
        message, annotation_dict = dumb_parse_ontology_annotation(fields["isa_type"])
    else:
        annotation_dict = {"annotationValue": fields["type"]}

            
    return message, annotation_dict



def pass_through(value: Any) -> Any:
    """Simply return the value passed to the function.
    
    This is simply to give an easy way to have individual options for headers 
    in a matrix type directive. Use a nested directive with this function as 
    the execute value and pass a calling record attribute as a parameter so 
    you can set required and silent fields for individual headers.
    
    Args:
        value: any value, but is meant to be a calling record attribute.
    
    Returns:
        A tuple of (None, value).
    """
    return None, value




