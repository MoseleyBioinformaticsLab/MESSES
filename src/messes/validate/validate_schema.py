# -*- coding: utf-8 -*-
"""
JSON schema for validate module.
"""

import copy


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

PD_schema =\
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
    PD_schema["additionalProperties"]["additionalProperties"]["properties"][keyword] = {"type":["string", "null", "integer"], "format":"integer"}

for keyword in json_schema_numeric_keywords:
    PD_schema["additionalProperties"]["additionalProperties"]["properties"][keyword] = {"type":["string", "null", "number"], "format":"numeric"}



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
                         "filename": {"type":["string", "array"], "items":{"type":"string", "minLength":1}}
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
                         "parent_id": {"type":["string", "array"]},
                         "protocol.id": {"type":["string", "array"], "minItems":1, "items":{"type":"string", "minLength":1}, "minLength":1},
                         "type": {"type":"string", "enum":["sample", "subject"]}
                         },
                     "required": ["id", "type", "protocol.id"],
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
                         "parent_id": {"type":"string"},
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
                         "parent_id": {"type":"string"},
                         "field": {"type":"string", "minLength":1},
                         "allowed_values": {"type":"array", "minItems":2, "items":{"type":"string", "minLength":1}}
                         },
                     "required": ["id", "field", "allowed_values"]
                     }
            },
    "project":{
             "type": "object",
             "minProperties":1,
             "additionalProperties":{
                     "type":"object",
                     "properties":{
                         "id": {"type":"string", "minLength":1},
                         "parent_id": {"type":"string"},
                         },
                     "required": ["id"]
                     }
            },
    "study":{
             "type": "object",
             "minProperties":1,
             "additionalProperties":{
                     "type":"object",
                     "properties":{
                         "id": {"type":"string", "minLength":1},
                         "parent_id": {"type":"string"},
                         },
                     "required": ["id"]
                     }
            },
    },
 "required": ["entity", "protocol", "measurement", "factor", "project", "study"]
 }


mwtab_schema = \
{
 "type": "object",
 "properties": {
    "protocol":{
        "type": "object",
        "additionalProperties":{
            "type":"object",
            "properties":{
                "machine_type":{"type":"string", "enum":["MS", "NMR"]}},
            "allOf":[
                {
                "if":{"properties":{"machine_type":{"const":"MS"}},
                      "required":["machine_type"]},
                "then":{
                    "properties":{
                        "chromatography_type":{"type":"string", "minLength":1},
                        "column_name":{"type":"string", "minLength":1},
                        "chromatography_instrument_name":{"type":"string", "minLength":1},
                        "instrument":{"type":"string", "minLength":1},
                        "instrument_type":{"type":"string", "minLength":1},
                        "ion_mode":{"type":"string", "minLength":1},
                        "ionization":{"type":"string", "minLength":1}
                        },
                    "required":["chromatography_type", "column_name", "chromatography_instrument_name", "instrument", "instrument_type", "ion_mode", "ionization"]
                    }
                },
                {
                "if":{"properties":{"machine_type":{"const":"NMR"}},
                      "required":["machine_type"]},
                "then":{
                    "properties":{
                        "instrument":{"type":"string", "minLength":1},
                        "instrument_type":{"type":"string", "minLength":1},
                        "NMR_experiment_type":{"type":"string", "minLength":1},
                        "spectrometer_frequency":{"type":["string", "number"], "minLength":1, "format":"numeric"},
                        "spectrometer_frequency%units":{"type":"string", "minLength":1}
                        },
                    "required":["instrument", "instrument_type", "NMR_experiment_type", "spectrometer_frequency", "spectrometer_frequency%units"]
                    }
                },
                {
                "if":{"properties":{"type":{"const":"collection"}},
                      "required":["type"]},
                "then":{
                    "properties":{
                        "description":{"type":"string", "minLength":1},
                        },
                    "required":["description"]
                    }
                },
                {
                "if":{"properties":{"type":{"const":"sample_prep"}},
                      "required":["type"]},
                "then":{
                    "properties":{
                        "description":{"type":"string", "minLength":1},
                        "order":{"type":"string", "minLength":1}
                        },
                    "required":["description", "order"]
                    }
                },
                {
                "if":{"properties":{"type":{"const":"treatment"}},
                      "required":["type"]},
                "then":{
                    "properties":{
                        "description":{"type":"string", "minLength":1},
                        },
                    "required":["description"]
                    }
                },
            ]
            }},
    ## Only the top level subjects have to have these fields, so commenting out because it could be a nuisance.
    # "entity":{
    #     "type":"object",
    #     "additionalProperties":{
    #         "type": "object",
    #         "if":{"properties":{"type":{"const":"subject"}}},
    #         "then":{
    #             "properties":{
    #                 "species":{"type":"string", "minLength":1},
    #                 "species_type":{"type":"string", "minLength":1},
    #                 "taxonomy_id":{"type":"string", "minLength":1}
    #                 },
    #             "required":["species", "species_type", "taxonomy_id"]}
    #         }
    #     },
    "project":{
        "type": "object",
        "additionalProperties":{
                "type":"object",
                "properties":{
                    "PI_email": {"type":"string", "format": "email"},
                    "PI_first_name": {"type":"string", "minLength":1},
                    "PI_last_name": {"type":"string", "minLength":1},
                    "address": {"type":"string", "minLength":1},
                    "department": {"type":"string", "minLength":1},
                    "phone": {"type":"string", "minLength":1},
                    "title": {"type":"string", "minLength":1}
                    },
                "required": ["PI_email", "PI_first_name", "PI_last_name", "address", "department", "phone", "title"]
                }
            },
    "study":{
        "type": "object",
        "additionalProperties":{
                "type":"object",
                "properties":{
                    "PI_email": {"type":"string", "format": "email"},
                    "PI_first_name": {"type":"string", "minLength":1},
                    "PI_last_name": {"type":"string", "minLength":1},
                    "address": {"type":"string", "minLength":1},
                    "department": {"type":"string", "minLength":1},
                    "phone": {"type":"string", "minLength":1},
                    "title": {"type":"string", "minLength":1}
                    },
                "required": ["PI_email", "PI_first_name", "PI_last_name", "address", "department", "phone", "title"]
                }
            },
    "measurement":{
        "type": "object",
        "additionalProperties":{
            "type": "object",
            "properties":{
                "assignment":{"type":"string", "minLength":1},
                "intensity":{"type":["string", "number"], "minLength":1, "format":"numeric"},
                "intensity%type":{"type":"string", "minLength":1}
                },
            "required":["assignment", "intensity", "intensity%type"]
            }
        }
    },
}


# mwtab_schema_MS = copy.deepcopy(mwtab_base_schema)
# mwtab_schema_MS["properties"]["measurement"] = \
#     {
#     "type": "object",
#     "additionalProperties":{
#         "type": "object",
#         "properties":{
#             "assignment":{"type":"string", "minLength":1},
#             "intensity":{"type":["string", "number"], "minLength":1, "format":"numeric", "minimum":0},
#             "intensity%type":{"type":"string", "minLength":1},
#             "formula":{"type":"string", "minLength":1},
#             "compound":{"type":"string", "minLength":1},
#             "isotopologue":{"type":"string", "minLength":1},
#             "isotopologue%type":{"type":"string", "minLength":1}
#             },
#         "required":["assignment", "intensity", "intensity%type", "formula", "compound", "isotopologue", "isotopologue%type"]
#         }
#     }

# mwtab_schema_NMR = copy.deepcopy(mwtab_base_schema)
# mwtab_schema_NMR["properties"]["measurement"] = \
#     {
#     "type": "object",
#     "additionalProperties":{
#         "type": "object",
#         "properties":{
#             "resonance_assignment":{"type":"string", "minLength":1},
#             "intensity":{"type":["string", "number"], "minLength":1, "format":"numeric", "minimum":0},
#             "intensity%type":{"type":"string", "minLength":1},
#             "base_inchi":{"type":["string", "array"], "minItems":1, "minLength":1},
#             "representative_inchi":{"type":["string", "array"], "minItems":1, "minLength":1},
#             "isotopic_inchi":{"type":["string", "array"], "minItems":1, "minLength":1},
#             "peak_description":{"type":["string", "array"], "minItems":1, "minLength":1},
#             "peak_pattern":{"type":"string"},
#             "proton_count":{"type":["string", "number"], "minLength":1, "minimum":0},
#             "transient_peak":{"type":"string", "minLength":1},
#             "transient_peak%type":{"type":"string", "minLength":1}
#             },
#         "required":["resonance_assignment", "intensity", "intensity%type", "base_inchi", 
#                     "representative_inchi", "isotopic_inchi", "peak_description",
#                     "peak_pattern", "proton_count", 
#                     "transient_peak", "transient_peak%type"]
#         }
#     }

# mwtab_schema_NMR_bin = copy.deepcopy(mwtab_base_schema)
# mwtab_schema_NMR_bin["properties"]["measurement"] = \
#     {
#     "type": "object",
#     "additionalProperties":{
#         "type": "object",
#         "properties":{
#             "assignment":{"type":"string", "minLength":1},
#             "intensity":{"type":["string", "number"], "minLength":1, "format":"numeric", "minimum":0},
#             "intensity%type":{"type":"string", "minLength":1}
#             },
#         "required":["assignment", "intensity", "intensity%type"]
#         }
#     }




