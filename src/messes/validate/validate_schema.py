# -*- coding: utf-8 -*-
"""
JSON schema for validate module.
"""

CV_schema =\
{
"type":"object",
"properties":{
    "parent_protocol":{"type":"object",
                       "properties":{
                           "type":{"type":"string", "enum":["sample_prep", "treatment", "collection", "storage", "measurement"]},
                           "parentID":{"type":["string", "null"]}
                           },
                       "required":["type"]
                       }
    },
"additionalProperties":{
    "type":"object",
    "properties":{
        "table":{"type":"string", "enum":["protocol", "entity", "measurement"]},
        "required":{"type":["string", "null", "boolean"], "minLength":1, "pattern":"(?i)^true|false$"}
        }
    } 
}


