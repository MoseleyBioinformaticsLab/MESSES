# -*- coding: utf-8 -*-

import pytest


from messes.convert.built_ins import dumb_parse_ontology_annotation, to_dict


@pytest.mark.parametrize("instance, expected_output", [
        
        ("source:acession:value:comment", (None,
                                          {'termSource': 'source',
                                           'termAccession': 'acession',
                                           'annotationValue': 'value',
                                           'comments': [{'value': 'comment'}]})),
        (" source: acession: value : comment ", (None,
                                                {'termSource': 'source',
                                                 'termAccession': 'acession',
                                                 'annotationValue': 'value',
                                                 'comments': [{'value': 'comment'}]})),
        (["source:acession:value:comment",
          "source2:acession2:value2:comment2"], (None,
                                                [{'termSource': 'source',
                                                  'termAccession': 'acession',
                                                  'annotationValue': 'value',
                                                  'comments': [{'value': 'comment'}]},
                                                 {'termSource': 'source2',
                                                  'termAccession': 'acession2',
                                                  'annotationValue': 'value2',
                                                  'comments': [{'value': 'comment2'}]}])),
        ])


def test_dumb_parse_ontology_works(instance, expected_output):
    "Test that output is correct for correctly formatted string or list of strings."
    
    output = dumb_parse_ontology_annotation(instance)
    
    assert output[0] == expected_output[0]
    assert output[1] == expected_output[1]


def test_dumb_parse_ontology_error():
    "Test that a message is returned when input is incorrectly formatted."
    
    output = dumb_parse_ontology_annotation("asdf")
    
    assert output[0] == '"asdf" is a malformed ontology annotation. It must have 3 colons (:) separating its values.'
    assert output[1] is None




@pytest.mark.parametrize("instance, expected_output", [
        
        ("key1:value1,key2:value2", (None, {'key1': 'value1', 'key2': 'value2'})),
        ("  key1 : value1  , key2 : value2 ", (None, {'key1': 'value1', 'key2': 'value2'})),
        (["key1:value1,key2:value2",
          "key1:value1,key2:value2"], (None, [{'key1': 'value1', 'key2': 'value2'}, {'key1': 'value1', 'key2': 'value2'}])),
        ])


def test_to_dict_works(instance, expected_output):
    "Test that output is correct for correctly formatted string or list of strings."
    
    output = to_dict(instance)
    
    assert output[0] == expected_output[0]
    assert output[1] == expected_output[1]


def test_to_dict_error():
    "Test that a message is returned when input is incorrectly formatted."
    
    output = to_dict("asdf")
    
    assert output[0] == '"asdf" is a malformed dictionary. It must have a form like "key:value,key:value...".'
    assert output[1] is None



