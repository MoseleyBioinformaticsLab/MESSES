# -*- coding: utf-8 -*-
"""
JSON schema for convert validation.
"""



directives_schema = \
{
 "$schema": "https://json-schema.org/draft/2020-12/schema",
 "title": "Conversion Directives",
 "description": "Schema to check that the conversion directives are valid.",

 "type": "object",
 "additionalProperties": {
     "type": "object",
     "additionalProperties":{
         "type":"object",
         "properties":{
             "value_type":{"type":"string", "enum":["str", "section", "matrix"]}
             },
         "required":["value_type"],
         "allOf":[
             {
             "if":{
                 "properties":{"value_type":{"const":"str"}},
                 "required":["value_type"]
               },
             "then":{
                 "properties":{
                     "override":{"type":["string", "null"]},
                     "code":{"type":["string", "null"]},
                     "import":{"type":["string", "null"]},
                     "table":{"type":["string", "null"]},
                     "for_each":{"type":["string", "null", "boolean"], "pattern":"(?i)^true|false$"},
                     "fields":{"type":["array", "null"], "minItems":1, "items":{"type":"string", "minLength":1}},
                     "test":{"type":["string", "null"], "pattern":"^.+=.+$"},
                     "required":{"type":["string", "null", "boolean"], "pattern":"(?i)^true|false$"},
                     "delimiter":{"type":["string", "null"]},
                     "sort_by":{"type":["array", "null"], "minItems":1, "items":{"type":"string", "minLength":1}},
                     "sort_order":{"type":["string", "null"], "pattern":"(?i)^descending|ascending$"},
                     "record_id":{"type":["string", "null"]}
                     },
                 "allOf":[
                     {
                         "if":{"allOf":[
                             {"properties":{"override":{"not":{"type":"string", "minLength":1}}}},
                             {"properties":{"code":{"not":{"type":"string", "minLength":1}}}},
                             ]},
                         "then":{"required":["fields", "table"]}
                         },
                      {
                          "if":{"allOf":[
                              {"properties":{"code":{"not":{"type":"string", "minLength":1}}}},
                              {"properties":{"table":{"not":{"type":"string", "minLength":1}}}},
                              {"properties":{"fields":{"not":{"type":"string", "minLength":1}}}}
                              ]},
                          "then":{"required":["override"]}
                          },
                      {
                          "if":{"allOf":[
                              {"properties":{"override":{"not":{"type":"string", "minLength":1}}}},
                              {"properties":{"table":{"not":{"type":"string", "minLength":1}}}},
                              {"properties":{"fields":{"not":{"type":"string", "minLength":1}}}}
                              ]},
                          "then":{"required":["code"]}
                          }
                     ]
                 }
             },
             {
             "if":{
                 "properties":{"value_type":{"const":"matrix"}},
                 "required":["value_type"]
               },
             "then":{
                 "properties":{
                     "code":{"type":["string", "null"]},
                     "import":{"type":["string", "null"]},
                     "table":{"type":["string", "null"]},
                     "test":{"type":["string", "null"], "pattern":"^.+=.+$"},
                     "required":{"type":["string", "null", "boolean"], "pattern":"(?i)^true|false$"},
                     "sort_by":{"type":["array", "null"], "minItems":1, "items":{"type":"string", "minLength":1}},
                     "sort_order":{"type":["string", "null"], "pattern":"(?i)^descending|ascending$"},
                     "headers":{"type":["array", "null"], "minItems":1, "items":{"type":"string", "minLength":1, "pattern":"^.+=.+$"}},
                     "collate":{"type":["string", "null"]},
                     "exclusion_headers":{"type":["array", "null"], "minItems":1, "items":{"type":"string", "minLength":1}},
                     "optional_headers":{"type":["array", "null"], "minItems":1, "items":{"type":"string", "minLength":1}},
                     "fields_to_headers":{"type":["string", "null", "boolean"], "pattern":"(?i)^true|false$"},
                     "values_to_str":{"type":["string", "null", "boolean"], "pattern":"(?i)^true|false$"}
                     },
                 "allOf":[
                     {
                         "if":{"properties":{"code":{"not":{"type":"string", "minLength":1}}},},
                         "then":{"required":["headers", "table"]}
                         },
                      {
                          "if":{"allOf":[
                              {"properties":{"headers":{"not":{"type":"array", "minItems":1}}}},
                              {"properties":{"table":{"not":{"type":"string", "minLength":1}}}},
                              ]},
                          "then":{"required":["code"]}
                          }
                     ]
                 }
             },
             {
             "if":{
                 "properties":{"value_type":{"const":"section"}},
                 "required":["value_type"]
               },
             "then":{
                 "properties":{
                     "code":{"type":["string", "null"]},
                     "import":{"type":["string", "null"]},
                     },
                 "required":["code"]
                 }
             }
             ]
         }
     }
}
# Marking the end for Sphinx documentation.

# temp = {"ANALYSIS": {
#           "ANALYSIS_TYPE": {
#             "id": "ANALYSIS_TYPE",
#             "table":"asdf",
#             "value_type":"section"
#           }}}
# validate_conversion_directives(temp, tag_schema)
# validate_arbitrary_schema(temp, tag_schema)
# jsonschema.validate(temp, tag_schema)

# try:
#     jsonschema.validate(temp, tag_schema)
# except jsonschema.ValidationError as e:
#     error = e
#     for key, value in e._contents().items():
#                 print(key, value)
#                 print()



