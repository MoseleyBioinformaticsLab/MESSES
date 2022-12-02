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
                     "required": ["id"]
                     }
            },
    "subject":{
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
                         "protocol.id": {"type":"string", "minLength":1},
                         "status": {"type":"string"},
                         "type": {"type":"string"}
                         },
                     "required": ["id", "project.id", "study.id", "protocol.id"]
                     }
            },
    "sample":{
             "type": "object",
             "minProperties":1,
             "additionalProperties":{
                     "type":"object",
                     "properties":{
                         "id": {"type":"string", "minLength":1},
                         "parentID": {"type":"string", "minLength":1},
                         "project.id": {"type":"string", "minLength":1},
                         "study.id": {"type":"string", "minLength":1},
                         ## TODO possibly change protocol.id to enum all the possible protocols which would be a variable list defined elsewhere.
                         "protocol.id": {"type":"string", "minLength":1},
                         "status": {"type":"string"},
                         "type": {"type":"string"}
                         },
                     "required": ["id", "project.id", "study.id", "protocol.id", "parentID"]
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
                         "protocol.id": {"type":"string", "minLength":1}
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
                         "allowed_values": {"type":"array", "minItems":1}
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






