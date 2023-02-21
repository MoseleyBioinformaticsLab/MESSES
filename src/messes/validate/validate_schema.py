# -*- coding: utf-8 -*-
"""
JSON schema for validate module.
"""


json_schema_numeric_keywords = ["multipleOf", "maximum", "minimum", 
                                "exclusiveMaximum", "exclusiveMinimum"]

json_schema_integer_keywords = ["minLength", "maxLength", "minItems", "maxItems", 
                                "maxContains", "minContains",
                                "minProperties", "maxProperties"]

json_schema_complex_keywords = ["allOf", "anyOf", "oneOf", "not", "if", "then", "else",
                                "properties", "additionalProperties", "dependentSchemas",
                                "unevaluatedProperties", "unevaluatedItems", "items",
                                "prefixItems", "contains", "patternProperties", "propertyNames",
                                "$vocabulary", "$defs", "dependentRequired", "const"]

json_schema_boolean_keywords = ["uniqueItems"]

CV_schema =\
{
"type":"object",
"properties":{
    "parent_protocol":{"type":"object",
                       "minProperties":1,
                       "additionalProperties":{
                           "type":"object",
                           "properties":{
                               "type":{"type":"string", "enum":["sample_prep", "treatment", "collection", "storage", "measurement"]},
                               "parent_id":{"type":["string", "null"]}
                               },
                           "required":["type"]
                           },
                       }
    },
"required":["parent_protocol"],
"additionalProperties":{
    "type":"object",
    "additionalProperties":{
        "properties":{
            "table":{"type":"string", "enum":["protocol", "entity", "measurement"]},
            "required":{"type":["string", "null", "boolean"], "pattern":"(?i)^true|false$"},
            "uniqueItems":{"type":["string", "null", "boolean"], "pattern":"(?i)^true|false$"},
            },
        "required":["table"]
        }
    }
}


for keyword in json_schema_integer_keywords:
    CV_schema["additionalProperties"]["additionalProperties"]["properties"][keyword] = {"type":["string", "null", "integer"], "format":"integer"}

for keyword in json_schema_numeric_keywords:
    CV_schema["additionalProperties"]["additionalProperties"]["properties"][keyword] = {"type":["string", "null", "number"], "format":"numeric"}



base_schema = \
{
 "type": "object",
 "properties": {
     "protocol":{
             "type": "object",
             "minProperties":1,
             "additionalProperties":{
                     "type":"object",
                     "properties":{
                         "id": {"type":"string", "minLength":1},
                         "parent_id": {"type":"string"},
                         "parent_protocol": {"type":"string"},
                         "type": {"type":"string", "enum":["sample_prep", "treatment", "collection", "storage", "measurement"]},
                         "description": {"type":"string"},
                         "filename": {"type":["string", "array"], "minItems":1, "items":{"type":"string", "minLength":1}}
                         },
                     "required": ["id", "type"]
                     }
            },
    "entity":{
             "type": "object",
             "minProperties":1,
             "additionalProperties":{
                     "type":"object",
                     "properties":{
                         "id": {"type":"string", "minLength":1},
                         "parent_id": {"type":"string"},
                         "project.id": {"type":"string", "minLength":1},
                         "study.id": {"type":"string", "minLength":1},
                         "protocol.id": {"type":["string", "array"], "minItems":1, "items":{"type":"string", "minLength":1}, "minLength":1},
                         "status": {"type":"string"},
                         "type": {"type":"string", "enum":["sample", "subject"]}
                         },
                     "required": ["id", "type", "project.id", "study.id", "protocol.id"],
                     "if":{"properties":{"type":{"const":"sample"}},
                           "required":["type"]},
                     "then":{"required":["parent_id"]}
                     }
             },
    "measurement":{
             "type": "object",
             "minProperties":1,
             "additionalProperties":{
                     "type":"object",
                     "properties":{
                         "id": {"type":"string", "minLength":1},
                         "entity.id": {"type":"string", "minLength":1},
                         "protocol.id": {"type":["string", "array"], "minItems":1, "items":{"type":"string", "minLength":1}, "minLength":1}
                         },
                     "required": ["id", "entity.id", "protocol.id"]
                     }
            },
    "factor":{
             "type": "object",
             "minProperties":1,
             "additionalProperties":{
                     "type":"object",
                     "properties":{
                         "id": {"type":"string", "minLength":1},
                         "field": {"type":"string", "minLength":1},
                         "project.id": {"type":"string", "minLength":1},
                         "study.id": {"type":"string", "minLength":1},
                         "allowed_values": {"type":"array", "minItems":1, "items":{"type":"string", "minLength":1}}
                         },
                     "required": ["id", "field", "project.id", "study.id", "allowed_values"]
                     }
            },
    "project":{
             "type": "object",
             "minProperties":1,
             "additionalProperties":{
                     "type":"object",
                     "properties":{
                         "id": {"type":"string", "minLength":1},
                         "PI_email": {"type":"string", "format": "email"},
                         "PI_first_name": {"type":"string", "minLength":1},
                         "PI_last_name": {"type":"string", "minLength":1},
                         "address": {"type":"string", "minLength":1},
                         "department": {"type":"string", "minLength":1},
                         "phone": {"type":"string", "minLength":1},
                         "title": {"type":"string", "minLength":1},
                         },
                     "required": ["id", "PI_email", "PI_first_name", "PI_last_name", "address", "department", "phone", "title"]
                     }
            },
    "study":{
             "type": "object",
             "minProperties":1,
             "additionalProperties":{
                     "type":"object",
                     "properties":{
                         "id": {"type":"string", "minLength":1},
                         "PI_email": {"type":"string", "format": "email"},
                         "PI_first_name": {"type":"string", "minLength":1},
                         "PI_last_name": {"type":"string", "minLength":1},
                         "address": {"type":"string", "minLength":1},
                         "department": {"type":"string", "minLength":1},
                         "phone": {"type":"string", "minLength":1},
                         "title": {"type":"string", "minLength":1},
                         },
                     "required": ["id", "PI_email", "PI_first_name", "PI_last_name", "address", "department", "phone", "title"]
                     }
            },
    },
 "required": ["entity", "protocol", "measurement", "factor", "project", "study"]
 }

