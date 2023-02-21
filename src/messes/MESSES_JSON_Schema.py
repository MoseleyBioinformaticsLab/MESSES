# -*- coding: utf-8 -*-




controlledVocabularySchema = {
 "$schema": "https://json-schema.org/draft/2020-12/schema",
 "title": "Controlled Vocabulary JSON",
 "description": "File that contains information about the structure of a dataset.",

 "type": "object",
 "properties": {
     "parent_protocol":{
             "type": "object",
             "minProperties":1,
             "additionalProperties":{
                     "type":"object",
                     "properties":{
                         "filename": {"type":"string"},
                         "id": {"type":"string", "minLength":1},
                         "parentID": {"type":"string"},
                         "type": {"type":"string", "enum":["sample_prep", "treatment", "collection", "storage", "master", "measurement", "default"]}
                         },
                     "required": ["id", "parentID", "type"]
                     }
            },
     "tagfield":{
             "type": "object",
             "minProperties":1,
             "additionalProperties":{
                     "type":"object",
                     "properties":{
                         "description": {"type":"string"},
                         "id": {"type":"string", "minLength":1},
                         "validationCode": {"type":"array", "minItems":1, "items":{"type":"string", "enum":["", "text", "numeric", "list", "list_optional"]}}
                         },
                     "required":["id", "validationCode"]
                     }
            },
     "tagfield_scope":{
             "type":"object",
             "minProperties":1,
             "additionalProperties":{
                     "type":"object",
                     "properties":{
                         "id": {"type":"string", "minLength":1},
                         "parent_protocol.id": {"type":"string", "minLength":1},
                         "scope_type": {"type":"array", "minItems":1, "items":{"type":"string", "enum":["ignore", "optional", "blank", "warning", "tracking"]}},
                         "table": {"type":"array", "minItems":1, "items":{"type":"string", "enum":["subject", "sample", "measurement", "factor", "project", "study", "protocol"]}},
                         "tagfield.id": {"type":"string", "minLength":1}
                         },
                    "required":["id", "parent_protocol.id", "scope_type", "table", "tagfield.id"]
                    }
            },
     "obsolete_tag":{
             "type":"object",
             "additionalProperties":{
                     "type":"object",
                     "properties":{
                         "id": {"type":"string", "minLength":1},
                         "replacement": {"type":"string", "minLength":1}
                         },
                     "required":["id", "replacement"]
                     }
            },
    },
 "required": ["parent_protocol", "tagfield",  "tagfield_scope"]
 }

#jsonschema.validate(cv, controlledVocabularySchema)



## TODO create a program that draws out the sample subject inheritance path and show protocols that create the new record.
## Can we combine subject and sample tables? There is a possible problem where a sample can have a parentID and that id is 
## in both the subject and sample tables.
## Should we have a way to add validation (CV) into the parsed data. For instance if the the data includes CV tables should they 
## be add to the CV? This gives the ability to have a long term persistent CV, but also some validation that is only relevant 
## for that experiment. 

CV_as_JSON_Schema = {
  "type": "object",
 "properties": {
     "protocol":{
             "type": "object",
             "minProperties":1,
             "additionalProperties":{
                     "type":"object",
                     "properties":{
                         "id": {"type":"string", "minLength":1},
                         "parentID": {"type":"string"},
                         ## TODO add an analysis type protocol?
                         "type": {"type":"string", "enum":["sample_prep", "treatment", "collection", "storage", "measurement"]},
                         "description": {"type":"string"},
                         "filename": {"type":"string"}
                         },
                     "patternProperties":{"^.*\.id$":{"format":"id_checker"}},
                     "required": ["id"]
                     }
            },
    # "subject":{
    #          "type": "object",
    #          "minProperties":1,
    #          "additionalProperties":{
    #                  "type":"object",
    #                  "properties":{
    #                      "id": {"type":"string", "minLength":1},
    #                      "parentID": {"type":"string"},
    #                      "project.id": {"type":"string", "minLength":1},
    #                      "study.id": {"type":"string", "minLength":1},
    #                      ## TODO possibly change protocol.id to enum all the possible protocols which would be a variable list defined elsewhere.
    #                      "protocol.id": {"type":"string", "minLength":1},
    #                      "status": {"type":"string"},
    #                      "type": {"type":"string"}
    #                      },
    #                  "required": ["id", "project.id", "study.id", "protocol.id"]
    #                  }
    #         },
    # "sample":{
    #          "type": "object",
    #          "minProperties":1,
    #          "additionalProperties":{
    #                  "type":"object",
    #                  "properties":{
    #                      "id": {"type":"string", "minLength":1},
    #                      "parentID": {"type":"string", "minLength":1},
    #                      "project.id": {"type":"string", "minLength":1},
    #                      "study.id": {"type":"string", "minLength":1},
    #                      ## TODO possibly change protocol.id to enum all the possible protocols which would be a variable list defined elsewhere.
    #                      "protocol.id": {"type":"string", "minLength":1},
    #                      "status": {"type":"string"},
    #                      "type": {"type":"string"}
    #                      },
    #                  "required": ["id", "project.id", "study.id", "protocol.id", "parentID"]
    #                  }
    #         },
    "entity":{
             "type": "object",
             "minProperties":1,
             "additionalProperties":{
                     "type":"object",
                     "properties":{
                         "id": {"type":"string", "minLength":1},
                         "parentID": {"type":"string"},
                         "project.id": {"type":"string", "minLength":1},
                         "study.id": {"type":"string", "minLength":1},
                         ## TODO possibly change protocol.id to enum all the possible protocols which would be a variable list defined elsewhere.
                         "protocol.id": {"type":["string", "array"], "minItems":1, "items":{"type":"string", "minLength":1}, "minLength":1},
                         "status": {"type":"string"},
                         "type": {"type":"string", "enum":["sample", "subject"]}
                         },
                     "required": ["id", "type", "project.id", "study.id", "protocol.id"],
                     "if":{"properties":{"type":{"const":"sample"}}},
                     "then":{"required":["parentID"]}
                     }
             },
    "measurement":{
             "type": "object",
             "minProperties":1,
             "additionalProperties":{
                     "type":"object",
                     "properties":{
                         "id": {"type":"string", "minLength":1},
                         "sample.id": {"type":"string", "minLength":1},
                         "protocol.id": {"type":["string", "array"], "minItems":1, "items":{"type":"string", "minLength":1}, "minLength":1}
                         },
                     "required": ["id", "sample.id", "protocol.id"]
                     }
            },
    "factor":{
             "type": "object",
             "minProperties":1,
             "additionalProperties":{
                     "type":"object",
                     "properties":{
                         "id": {"type":"string", "minLength":1},
                         "project.id": {"type":"string", "minLength":1},
                         "study.id": {"type":"string", "minLength":1},
                         "allowed_values": {"type":"array", "minItems":1, "items":{"type":"string", "minLength":1}}
                         },
                     "required": ["id", "project.id", "study.id", "allowed_values"]
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
 "required": ["subject", "sample", "protocol", "measurement", "factor", "project", "study"]
 }




## Example for adding in checking based on id, parentid, etc.
CV =\
{
"type":"object",
"properties":{
    "protocol":{
        "type":"object",
        "additionalProperties":{
            "type":"object",
            "properties":{
                "id": {"type":"string", "minLength":1},
                "parentID": {"type":["string", "array"]},
                "type": {"type":"string", "enum":["sample_prep", "treatment", "collection", "storage", "measurement"]},
                "description": {"type":"string"},
                "filename": {"type":"string"}
                },
            "required": ["id"],
            "allOf":[
                {
                "if":{
                      "anyOf":[
                          {"properties":{"id":{"const":"Chromatography_MS_measurement"}},
                          "required":["id"]},
                          {"properties":{"parentID":{"anyOf":[
                                                      {"const":"Chromatography_MS_measurement"}, 
                                                      {"type":"array", "contains":{"const":"Chromatography_MS_measurement"}}
                                                      ]}},
                          "required":["parentID"]}
                          ]
                    },
                "then":{
                    "properties":{
                        "chromatography_description": {"type":"string", "minLength":1},
                        "chromatography_instrument_name": {"type":"string", "minLength":1},
                        "chromatography_type": {"type":"string", "minLength":1},
                        "column_name": {"type":"string", "minLength":1},
                        "instrument": {"type":"string", "minLength":1},
                        "instrument_type": {"type":"string", "minLength":1},
                        "ion_mode": {"type":"string", "minLength":1},
                        "ionization": {"type":"string", "minLength":1},
                      },
                      "required": [
                        "chromatography_instrument_name",
                        "chromatography_type",
                        "column_name",
                        "ion_mode",
                        "ionization",
                        "instrument"
                      ]
                    }
                },
                ]
            }
        },
    "entity":{
        "type": "object",
        "minProperties":1,
        "additionalProperties":{
                "type":"object",
                # "properties":{
                #     "id": {"type":"string", "minLength":1},
                #     "parentID": {"type":"string"},
                #     "project.id": {"type":"string", "minLength":1},
                #     "study.id": {"type":"string", "minLength":1},
                #     "protocol.id": {"type":["string", "array"], "minItems":1, "items":{"type":"string", "minLength":1}, "minLength":1},
                #     "status": {"type":"string"},
                #     "type": {"type":"string", "enum":["sample", "subject"]}
                #     },
                # "required": ["id", "type", "project.id", "study.id", "protocol.id"],
                # "if":{"properties":{"type":{"const":"sample"}},
                #       "required":["type"]},
                # "then":{"required":["parentID"]},
                "allOf":[
                    {
                    "if":{
                        "anyOf":[
                            {"properties":{"protocol.id":{"const":"Chromatography_MS_measurement"}
                                                        },
                            "required":["protocol.id"]},
                            {"properties":{"protocol.id":{"contains":{"const":"Chromatography_MS_measurement"}}
                                                        },
                            "required":["protocol.id"]}
                            ]
                        },
                    # "if":{
                    #     "properties":{"protocol.id":{
                    #                             "anyOf":[
                    #                                 {"const":"Chromatography_MS_measurement"}, 
                    #                                 {"contains":{"const":"Chromatography_MS_measurement"}}
                    #                                 ]}},
                    #     # "properties":{"protocol.id":{
                    #     #                             "const":"Chromatography_MS_measurement" 
                    #     #                             }},
                    #     "required":["protocol.id"]
                    #     },
                    "then":{
                        "properties":{
                            "assignment": {"type":"string", "minLength":1},
                            "assignment%method": {"type":"string", "minLength":1},
                            "compound": {"type":"string", "minLength":1},
                            "intensity": {"type":"string", "minLength":1, "format":"is_num"},
                            "intensity%type": {"type":"string", "minLength":1},
                            "intensity%units": {"type":"string", "minLength":1},
                            "isotopologue": {"type":"string", "minLength":1},
                            "isotopologue%type": {"type":"string", "minLength":1},
                            "retention_time": {"type":"string", "minLength":1},
                            "retention_time%units": {"type":"string", "minLength":1},
                            "sample.id": {"type":"string", "minLength":1}
                          },
                          "required": [
                            "assignment%method",
                            "assignment",
                            "intensity",
                            "sample.id"
                          ]
                        }
                    },
                    ]
                }
        }
    }
}


CV =\
{
"type":"object",
"properties":{
    "entity":{
        "type": "object",
        "minProperties":1,
        "additionalProperties":{
                "type":"object",
                "allOf":[
                    {
                    # "if":{
                    #     "anyOf":[
                    #         {"properties":{"protocol.id":{"const":"Chromatography_MS_measurement"}
                    #                                     },
                    #         "required":["protocol.id"]},
                    #         {"properties":{"protocol.id":{"type":"array","contains":{"const":"Chromatography_MS_measurement"}}
                    #                                     },
                    #         "required":["protocol.id"]}
                    #         ]
                    #     },
                    "if":{
                        "properties":{"protocol.id":{
                                                "anyOf":[
                                                    {"const":"Chromatography_MS_measurement"}, 
                                                    {"type":"array","contains":{"const":"Chromatography_MS_measurement"}}
                                                    ]}},
                        # "properties":{"protocol.id":{
                        #                             "const":"Chromatography_MS_measurement" 
                        #                             }},
                        "required":["protocol.id"]
                        },
                    "then":{
                        "properties":{
                            "assignment": {"type":"string", "minLength":1},
                            "assignment%method": {"type":"string", "minLength":1},
                            "compound": {"type":"string", "minLength":1},
                            "intensity": {"type":"string", "minLength":1, "format":"is_num"},
                            "intensity%type": {"type":"string", "minLength":1},
                            "intensity%units": {"type":"string", "minLength":1},
                            "isotopologue": {"type":"string", "minLength":1},
                            "isotopologue%type": {"type":"string", "minLength":1},
                            "retention_time": {"type":"string", "minLength":1},
                            "retention_time%units": {"type":"string", "minLength":1},
                            "sample.id": {"type":"string", "minLength":1}
                          },
                          "required": [
                            "assignment%method",
                            "assignment",
                            "intensity",
                            "sample.id"
                          ]
                        }
                    },
                    ]
                }
        }
    }
}


temp = {"entity":{"asdf":{"field1":"qwer", "protocol.id":"Chromatography_MS_measurement"}}}


jsonschema.validate(temp, CV)



temp = {"protocol": {
    "ICMS1": {
      "chromatography_description": "Targeted IC",
      "chromatography_instrument_name": "Thermo Dionex ICS-5000+",
      "chromatography_type": "Targeted IC",
      "column_name": "Dionex IonPac AS11-HC-4um 2 mm i.d. x 250 mm",
      "description": "ICMS Analytical Experiment with detection of compounds by comparison to standards. \nThermo RAW files are loaded into TraceFinder and peaks are manually curated. The area under the chromatograms is then exported to an Excel file. The area is then corrected for natural abundance. The natural abundance corrected area is then used to calculate the concentration of each compound for each sample. This calculation is done using standards. The first sample ran on the ICMS is a standard that has known concentrations of certain compounds. Then a number of samples are ran (typically 3-4) followed by another standard. The equation to calculate the concentration is \"intensity in sample\"/(\"intensity in first standard\" + ((\"intensity in second standard\" - \"intensity in first standard\")/# of samples) * \"known concentration in standard\", where the \"intensity\" is the aforementioned natural abundance corrected area, and the unlabeled intensity from the standard is used for all isotopologues of the compound. The reconstitution volume is simply the volume that the polar part of the sample was reconstituted to before going into the ICMS. The injection volume is how much of the reconstitution volume was injected into the ICMS. The protein is how much protein was in the entire sample (not only the small portion that was aliquoted for the ICMS). The polar split ratio is the fraction of the polar part of the sample that was aliquoted for the ICMS. This is calculated by dividing the weight of the polar aliquot for ICMS by the total weight of the polar portion of the sample. The protein normalized concentration is calculated using the equation, concentration * (reconstitution volume / 1000 / polar split ratio / protein).",
      "id": "ICMS1",
      # "instrument": "Orbitrap Fusion",
      "instrument_type": "IC-FTMS",
      "ion_mode": "NEGATIVE",
      "ionization": "ESI",
      "parentID": ["Chromatography_MS_measurement"],
      "type": "measurement"
    },
    "IC-FTMS_preparation": {
      "description": "Before going into the IC-FTMS the frozen sample is reconstituted in water.",
      "filename": "",
      "id": "IC-FTMS_preparation",
      "type": "sample_prep"
    }}}

format_checker = jsonschema.FormatChecker()
@format_checker.checks('is_num') 
def is_numeric(value):
    try:
        float(value)
    except ValueError:
        return False
    return True

@format_checker.checks('integer') 
def is_integer(value):
    if value:
        try:
            int(value)
        except ValueError:
            return False
        return True
    return True

jsonschema.validate(temp, CV, format_checker=format_checker)


schema =\
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
                         "parentID": {"type":"string"},
                         ## TODO add an analysis type protocol?
                         "type": {"type":"string", "enum":["sample_prep", "treatment", "collection", "storage", "measurement"]},
                         "description": {"type":"string"},
                         "filename": {"type":"string"}
                         },
                     "patternProperties":{"^.*\.id$":{"format":"id_checker"}},
                     "required": ["id"]
                     }
            }}}


temp =\
    {
     "protocol":{"test":{"id":"test",
                         "sample.id":"qwer"}}
     }


format_checker = jsonschema.FormatChecker()
@format_checker.checks('id_checker') 
def id_exists(value):
    table = re.match(r'(.*)\.id', value).group(1)
    return table in instance

jsonschema.validate(temp, schema, format_checker=format_checker)



import copy
import json
import jsonschema


def is_it_a_num(possible_num) :
    """ Determines whether the input string is a number or not. Returns True if it is, False otherwise. """
    try :
        float(possible_num)
        
    except ValueError :
        return False
    
    return True



def compile_fields_by_protocol(controlled_vocabulary) :
    """ Returns 2 dictionaries where the keys are the protocols in the parent_protocol table of the controlled_vocabulary JSON,
    and the values are a dictionary of the fields. One dictionary is fields for protocols and the other dictionary is fields for 
    subjects, samples, and measurements. The values of the field dictionary are the scope_type, table, and validationCode of the fields.
    The values may also include allowed_values, min, and max if those fields are provided for the record in the tagfield_scope table."""
    
    
    if not "parent_protocol" in controlled_vocabulary or not "tagfield_scope" in controlled_vocabulary or not "tagfield" in controlled_vocabulary:
        return
        
    ## Final dictionary of protocols and fields to return at the end for subjects, samples, and measurements.
    record_fields_by_protocol = {}
    ## Dictionary of protocols and fields to return for protocols.
    protocol_fields_by_protocol = {}
    ## Dictionary of protocols. The keys are the protocols and the values are a list of protocols in its family tree (ancestors).
    protocol_family_tree = {}
    
    ## Iterate through the protocol table to determine all of the protocols and their family tree.
    for protocol, protocol_values in controlled_vocabulary["parent_protocol"].items():
        parent_ids = []
        parent_id = protocol
        parent_protocol_values = protocol_values
        ## Keep looking for parents until you can't find anymore.
        while parent_id != "":
            if not "parentID" in parent_protocol_values:
                break
            else :
                parent_id = parent_protocol_values["parentID"]
                if parent_id != "":
                    if parent_id in controlled_vocabulary["parent_protocol"]:
                        parent_ids.append(parent_id)
                        parent_protocol_values = controlled_vocabulary["parent_protocol"][parent_id]
                    else:
                        break
                else:
                    protocol_family_tree[protocol] = parent_ids
        
        
    ## Iterate through each entry in the tagfield_scope table and pull out the fields.
    ## Fields are found by matching the parent_protocol.id field to a protocol in protocol_family_tree.
    ## If the scope_type of a match is "ignore" then it is a required field.
    for scope_id, scope_values in controlled_vocabulary["tagfield_scope"].items() :
        
        required_fields = ["parent_protocol.id", "scope_type", "tagfield.id", "table"]


        if all(r_field in scope_values for r_field in required_fields) and scope_values["parent_protocol.id"] in protocol_family_tree:
            ## Find the required field in the tagfield table and get its type.
            field = {}
            parent_protocol = scope_values["parent_protocol.id"]
            scope_type = scope_values["scope_type"]
            tagfield_id = scope_values["tagfield.id"]
            table = scope_values["table"]
            
            if tagfield_id in controlled_vocabulary["tagfield"]:
                if "validationCode" in controlled_vocabulary["tagfield"][tagfield_id] :
                    
                    field[tagfield_id] = {"validationCode" : controlled_vocabulary["tagfield"][tagfield_id]["validationCode"], 
                                          "scope_type" : scope_type,
                                          "table" : table}
                    
                    
                    ## If the field has values for allowed_values, min, or max then add them to the dictionary.
                    if "allowed_values" in scope_values and scope_values["allowed_values"] != "" and scope_values["allowed_values"] != []:
                        field[tagfield_id].update({"allowed_values" : scope_values["allowed_values"]})
                        
                    if "min" in scope_values and scope_values["min"] != "" and is_it_a_num(scope_values["min"]) :
                        field[tagfield_id].update({"min" : scope_values["min"]})
                        
                    if "max" in scope_values and scope_values["max"] != "" and is_it_a_num(scope_values["max"]):
                        field[tagfield_id].update({"max" : scope_values["max"]})
                        
                                        
                    if parent_protocol in record_fields_by_protocol:
                        record_fields_by_protocol[parent_protocol].update(field)
                    else:
                        record_fields_by_protocol[parent_protocol] = field
                    
                    
                    if "protocol" in table:
                        
                        ## This was really stupid to debug, but if you don't explicitly copy 
                        ## then when record_fields_by_protocol does an update it will change
                        ## the value in protocol_fields_by_protocol as well.
                        field_copy = copy.deepcopy(field)
                        
                        if parent_protocol in protocol_fields_by_protocol:
                            protocol_fields_by_protocol[parent_protocol].update(field_copy)
                        else:
                            protocol_fields_by_protocol[parent_protocol] = field_copy
                            
                    
                        
    ## Each protocol in record_fields_by_protocol and protocol_fields_by_protocol now has its own fields, 
    ## but not the ones it inherits from its family tree.
    ## Iterate over the family tree and add the fields from each ancestor to each protocol.
    for protocol, ancestors in protocol_family_tree.items() :
        for ancestor in ancestors:
            
            if ancestor in record_fields_by_protocol:
                if protocol in record_fields_by_protocol:
                    ## If the protocol already has a field that its ancestor has then don't overwrite it.
                    ## Only add fields from the ancestor that the protocol doesn't have.
                    for field_name, field_values in record_fields_by_protocol[ancestor].items():
                        if not field_name in record_fields_by_protocol[protocol]:
                            record_fields_by_protocol[protocol][field_name] = field_values
                else:
                    record_fields_by_protocol[protocol] = record_fields_by_protocol[ancestor]
                    
                    
            if ancestor in protocol_fields_by_protocol:
                if protocol in protocol_fields_by_protocol:
                    ## If the protocol already has a field that its ancestor has then don't overwrite it.
                    ## Only add fields from the ancestor that the protocol doesn't have.
                    for field_name, field_values in protocol_fields_by_protocol[ancestor].items():
                        if not field_name in protocol_fields_by_protocol[protocol]:
                            protocol_fields_by_protocol[protocol][field_name] = field_values
                else:
                    protocol_fields_by_protocol[protocol] = protocol_fields_by_protocol[ancestor]
                    
    return record_fields_by_protocol, protocol_fields_by_protocol


## Convert controlled vocabulary to jsonschema
with open('C:/Users/Sparda/Desktop/Moseley Lab/Code/CESB.LIMS/templates_and_CV/controlled_vocabulary/controlled_vocabulary_2022-05-03_hnbm_TT.json','r') as jsonFile :
        cv = json.load(jsonFile)
            
record_fields_by_protocol = {}
protocol_fields_by_protocol = {}
record_fields_by_protocol, protocol_fields_by_protocol = compile_fields_by_protocol(cv)

default_fields = ["filename", "description", "type"]



properties_by_protocol = {}
for protocol_id, protocol_fields in cv["parent_protocol"].items():
    properties_by_protocol[protocol_id] = {}
    if "parentID" in protocol_fields and protocol_fields["parentID"]:
        properties_by_protocol[protocol_id]["parentID"] = protocol_fields["parentID"]
        
    properties_by_protocol[protocol_id]["protocol_properties"] = {"type":"object", "properties":{}}
    properties_by_protocol[protocol_id]["record_properties"] = {"type":"object", "properties":{}}
    
    ## Get the protocol fields.
    required = []
    for field, field_attributes in protocol_fields_by_protocol[protocol_id].items():
        if field in default_fields:
            continue
        
        validationCode = field_attributes["validationCode"]
        if len(validationCode) == 1:
            if "text" in validationCode:
                field_type = "string"
            elif "numeric" in validationCode:
                field_type = "number"
            elif "list" in validationCode:
                field_type = "array"
            elif "list_optional" in validationCode:
                field_type = ["string", "array"]
        else:
            field_type = []
            if "text" in validationCode:
                field_type.append("string")
            if "numeric" in validationCode:
                field_type.append("number")
            if "list" in validationCode or "list_optional" in validationCode:
                field_type.append("array")
                
        if "ignore" in field_attributes["scope_type"]:
            required.append(field)
            
        if "warning" in field_attributes["scope_type"]:
            message_type = "warning"
        else:
            message_type = "error"
        
        properties_by_protocol[protocol_id]["protocol_properties"]["properties"][field] = {"type":field_type, "message_type":message_type}
    properties_by_protocol[protocol_id]["protocol_properties"]["required"] = required
    
    ## Get the record fields.
    required = []
    for field, field_attributes in record_fields_by_protocol[protocol_id].items():
        if "protocol" in field_attributes["table"]:
            continue
        
        validationCode = field_attributes["validationCode"]
        if len(validationCode) == 1:
            if "text" in validationCode:
                field_type = "string"
            elif "numeric" in validationCode:
                field_type = "number"
            elif "list" in validationCode:
                field_type = "array"
            elif "list_optional" in validationCode:
                field_type = ["string", "array"]
        else:
            field_type = []
            if "text" in validationCode:
                field_type.append("string")
            if "numeric" in validationCode:
                field_type.append("number")
            if "list" in validationCode or "list_optional" in validationCode:
                field_type.append("array")
                
        if "ignore" in field_attributes["scope_type"]:
            required.append(field)
            
        if "warning" in field_attributes["scope_type"]:
            message_type = "warning"
        else:
            message_type = "error"
        
        properties_by_protocol[protocol_id]["record_properties"]["properties"][field] = {"type":field_type, "message_type":message_type}
    properties_by_protocol[protocol_id]["record_properties"]["required"] = required
    
with open('C:/Users/Sparda/Desktop/Moseley Lab/New_CV.json','w') as jsonFile :
    jsonFile.write(json.dumps(properties_by_protocol, sort_keys=True, indent=2, separators=(',', ': ')))


data = {}
errors = []
for protocol_id, protocol_fields in data["protocol"]:
    if "parentID" in protocol_fields and protocol_fields["parentID"] in properties_by_protocol:
        validator = jsonschema.Draft202012Validator(properties_by_protocol[protocol_fields["parentID"]])
        errors.append(validator.iter_errors(protocol_fields))
        


## A guide on some properties of the error exception https://python-jsonschema.readthedocs.io/en/stable/errors/        
for error_generator in errors:
    for error in error_generator:
        print(error.message)
        
        if error.schema["message_type"] == "warning":
            print("Warning: " + error.message)
        else:
            print("Error: " + error.message)

## This code lets you validate and get all errors.
## Draft202012Validator is the latest at this time, jsonschema.validotrs._LATEST_VERSION 
## can be used to get the latest version, but I think it's better to stick with this version so future changes can't break our code.
#validator = jsonschema.Draft202012Validator(CV_as_JSON_Schema)
#errors = validator.iter_errors(instance)


with open('C:/Users/Sparda/Desktop/Moseley Lab/Code/CESB.LIMS/templates_and_CV/controlled_vocabulary/controlled_vocabulary_2022-05-03_hnbm_TT.json','r') as jsonFile :
        cv = json.load(jsonFile)

new_cv = {}
new_cv["parent_protocol"] = cv["parent_protocol"]
for protocol, attributes in new_cv["parent_protocol"].items():
    if "parentID" in attributes:
        new_cv["parent_protocol"][protocol]["parent_id"] = attributes["parentID"]
        del new_cv["parent_protocol"][protocol]["parentID"]
    
    fields_dict = {}
    for tagfield_scope, scope_attributes in cv["tagfield_scope"].items():
        if protocol in scope_attributes["parent_protocol.id"]:
            tagfield_dict = {}
            
            table = scope_attributes["table"]
            if "project" in table or "study" in table or "factor" in table:
                continue
            if "measurement" in table:
                tagfield_dict["table"] = "measurement"
            if "subject" in table or "sample" in table:
                tagfield_dict["table"] = "entity"
            if "protocol" in table:
                tagfield_dict["table"] = "protocol"
            
            tagfield = scope_attributes["tagfield.id"]
            validation_code = cv["tagfield"][tagfield]["validationCode"]
            
            tagfield_dict["type"] = []
            if "text" in validation_code:
                tagfield_dict["type"].append("string")
                tagfield_dict["minLength"] = "1"
            if "numeric" in validation_code:
                tagfield_dict["format"] = "numeric"
                tagfield_dict["type"].append("number")
            if "list" in validation_code:
                tagfield_dict["type"].append("array")
                tagfield_dict["minItems"] = "1"
                tagfield_dict["items"] = {"type":"string", "minLength":1}
            if "list_optional" in validation_code:
                tagfield_dict["type"].append("array")
                tagfield_dict["type"].append("null")
                tagfield_dict["items"] = {"type":"string", "minLength":1}
            
            if not tagfield_dict["type"]:
                tagfield_dict["type"] = "string"
                tagfield_dict["minLength"] = "1"
            
            scope_type = scope_attributes["scope_type"]
            if "ignore" in scope_type:
                tagfield_dict["required"] = "True"
            
            if len(tagfield_dict["type"]) == 1:
                tagfield_dict["type"] = tagfield_dict["type"][0]
                
            fields_dict[tagfield] = tagfield_dict
    new_cv[protocol] = fields_dict


with open('C:/Users/Sparda/Desktop/Moseley Lab/Code/MESSES/new_CV.json','w') as jsonFile :
    jsonFile.write(json.dumps(new_cv, sort_keys=True, indent=2, separators=(',', ': ')))

















def check(self, instance: object, format: str) -> None:
    """
    Check whether the instance conforms to the given format.

    Arguments:

        instance (*any primitive type*, i.e. str, number, bool):

            The instance to check

        format:

            The format that instance should conform to

    Raises:

        FormatError:

            if the instance does not conform to ``format``
    """

    if format not in self.checkers:
        return

    func, raises = self.checkers[format]
    result, cause = None, None
    try:
        result = func(instance)
    except raises as e:
        cause = e
    if not result:
        raise jsonschema.exceptions.FormatError(f"{instance!r} is not a {format!r}", cause=cause)
    elif format == "integer" and isinstance(instance, str):
        raise jsonschema.exceptions.FormatError("safe to convert to int", cause=None)
        

## Assumes value is nested in a dict or list.
# def convert_formats(errors_generator, instance) -> bool:
#     for error in errors_generator:
#         # print("[%s]" % "][".join(repr(index) for index in error.relative_path))
#         # for key, value in error._contents().items():
#         #     print(key, value)
#         #     print()
#         if error.message == "safe to convert to float":
#             path = "[%s]" % "][".join(repr(index) for index in error.relative_path)
#             exec("instance" + path + "=int(" + "instance" + path + ")")

def convert_formats(validator, instance) -> bool:
    ## Get old check to save and restore.
    original_check = jsonschema.FormatChecker.check
    ## Replace check in FormatChecker.
    jsonschema.FormatChecker.check = check
    
    for error in validator.iter_errors(instance):
        if error.message == "safe to convert to float":
            path = "[%s]" % "][".join(repr(index) for index in error.relative_path)
            exec("instance" + path + "=float(" + "instance" + path + ")")
        elif error.message == "safe to convert to int":
            path = "[%s]" % "][".join(repr(index) for index in error.relative_path)
            exec("instance" + path + "=int(" + "instance" + path + ")")
            
    jsonschema.FormatChecker.check = original_check
    

def create_validator(schema) -> jsonschema.protocols.Validator:
    validator = jsonschema.validators.validator_for(schema)
    format_checker = jsonschema.FormatChecker()
    @format_checker.checks('integer') 
    def is_integer(value):
        if value and isinstance(value, str):
            try:
                int(value)
            except ValueError:
                return False
            return True
        return True
    @format_checker.checks('numeric') 
    def is_float(value):
        if value and isinstance(value, str):
            try:
                float(value)
            except ValueError:
                return False
            return True
        return True
    return validator(schema=schema, format_checker=format_checker)


# jsonschema.FormatChecker.check = check
# format_checker = jsonschema.FormatChecker()
# # format_checker.check = check

# @format_checker.checks('integer') 
# def is_integer(value):
#     if value and isinstance(value, str):
#         try:
#             int(value)
#         except ValueError:
#             return False
#         return True
#     return True

schema = {'type': 'object', 'properties': {'asdf': {"type":"array", "items":{'format': 'integer'}}}}
# schema = {'format': 'integer'}
instance = {"asdf":["123", 12.5]}
# instance = "123"
validator = jsonschema.validators.validator_for(schema)
# validator = validator(schema=schema, format_checker=format_checker)
validator = create_validator(schema)
convert_formats(validator, instance)
# errors_generator = validator.iter_errors(instance=instance)
# convert_formats(errors_generator, instance)


for error in validator.iter_errors(instance):
    print(error)


jsonschema.validate(instance, schema)




