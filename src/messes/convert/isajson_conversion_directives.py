# -*- coding: utf-8 -*-
"""
conversion tags for the ISA-JSON format
"""

## MESSES JSON doesn't have places for more than 1 person, publications, or ontology terms.
## There are people under study and investigation in ISA.
## Factors have a name and an annotationValue. They can be the same, but it isn't clear what the difference is. annotationValue has to be more scientific. For example a name could be "exposure time", but the AV would be "time".
## Samples can have multiple parents, but not in MESSES JSON.
## Look at arrayexpress as a repo.
## Factors are nested within studies in ISA, so factors may have to have a study.id field for ISA submissions.
## ontology_annotations are a recurring theme. I think we can mimic it by simply adding the fields to records where 
## people want to add them. The 5 possible fields are @id, annotationValue, termAccession, termSource and comments.
## @id could be its own field, but I think it is easy enough to create by simply using the record name/id or annotationValue ex. #ontology_annotation/"id"
## annotationValue could be its own field, but the name/id will often be this value.  ontology_name, annotation_name?
## termAccession has to be mapped to a new field for a url value.  ontology_url, annotation_url?
## termSource has to be mapped to a new field for the name of the source.  ontology_source, annotation_source?
## comments are actually a name and a string in ISA, so it would need 2 fields  comment_name, comment_value  comment, comment%name
 # "studies/factors/type": {
 #     "no_id_needed": {
 #         "value_type": "section_matrix",
 #         "required": "True",
 #         "headers": [
 #           "\"@id\"=\"#ontology_annotation/\"id",
 #           "\"annotationValue\"=id",
 #           "\"termAccession\"=term_url",
 #           "\"termSource\"=term_source_name"
 #           "\"comments\"=#studies/factors/comments"
 #         ],
 #         "table": "factor"
 #         }
 #     }
 
## Need a way to pass information from calling directive to called directive.
## One way is caret method shown below, another is making directive calling signature like a function call 
## and allowing parameters to be passed with it. ex. "\"factorType\"=#studies/factor/type arg1 arg2"
 # "studies/factors": {
 #     "no_id_needed": {
 #         "value_type": "section_matrix",
 #         "required": "True",
 #         "test": "study.id=^id",  ## Possible way to indicate that the id should come from the record that called it. The caret could be special character.
 #         "headers": [
 #           "\"@id\"=\"#factor/\"id",
 #           "\"factorName\"=id",
 #           "\"factorType\"=#studies/factor/type",
 #           "\"comments\"=#studies/factors/comments"
 #         ],
 #         "table": "factor"  ## Table might not matter, or we use this to select a record within a table.
 #         }
 #     }
 
## The caret strategy above might eliminate the need to call a nested directive with a limited scope. 
## I was thinking that you could use the table field to control whether the input_json parameter to the 
## directive function was the whole json or just a specific table or record, but with the caret (^) notation 
## we can use the test and record_id fields to limit the directive to the calling record.
## See "studies/factors/type" below for an example.
## Caret notation would need special checks to make sure directives are valid. Non-nested directives can't have carets.

## Comments are a list of name value pairs. It's easy to add 1 comment with the current MESSES system, 
## but multiple is more difficult. Could do something like having pairs such as comment1_name, comment1_value 
## and then add regex selection to conversion directives. regex selection might be good to add anyway. 
## Even with regex selection there is not a way in the directives to create a matrix from a single record. 
## Could add a keyword such as field_collate that would indicate to create a new record in the matrix 
## based on fields in each record instead of for each record.
# "Data": {
#   "required": "True",
#   "field_collate": "True",
#   "table": "factor",
#   "test": "id=^id",
#   "headers": [
#       "\"name\"=r\"comment(.*)_name\""
#       "\"value\"=r\"comment(.*)_value\""
#       ],
#   "id": "Data",
#   "value_type": "matrix"
# }

## Have to make sure the header doesn't match 2 fields.
## Have to make sure each group has all of the headers, cant have a group that has a name and no value for example.
# import re

# record_fields =\
# {
#  "comment1_name" : "comment 1 name",
#  "comment2_name" : "comment 2 name",
#  "comment1_value" : "comment 1 value",
#  "comment2_value" : "comment 2 value"
#  }

# grouping_regex_detector = r"r\"(.*\(.*\).*)\""

# headers = [
#       "r\"comment(.*)_name\"",
#       "r\"comment(.*)_value\""
#       ]

# ## Note headers is just the output keys here.
# matrix_records = {}
# for header in headers:
#     if not (header_regex := re.match(grouping_regex_detector, header)):
#         continue
    
#     header_regex = header_regex.group(1)
#     field_to_collate_key_map = {field:re_match.group(1) for field in record_fields if (re_match := re.match(header_regex, field))}
    
#     collate_key_to_field_map = {}
#     for field, collate_key in field_to_collate_key_map.items():
#         if collate_key in collate_key_to_field_map:
#             print("Error:  header regex matches 2 fields with the same group.")
#         else:
#             collate_key_to_field_map[collate_key] = field
            
#     for field, collate_key in collate_key_to_field_map.items():
#         matrix_records.setdefault(collate_key, {})
#         matrix_records[collate_key][header_input_key] = record_fields[field]

# matrix_records = list(matrix_records.values())

# ## Change this so it accumulates all bad headers and print at the end.
# for record in matrix_records:
#     if not set(record.keys()) - header_input_keys:
#         print("Error:  When collating fields from header regular expressions for the conversion directive {directive_name}, " +\
#               "not all regular expressions matched a field for each group. The following headers did not have a match for all groups:")

## The above code and idea for field_collate would not be easy to incorporate into the current convert code because the current code 
## expects each record to produce 1 dictionary instead of multiple. Since this is just here for ISA comments we may be able to just 
## only allow one comment per record and not worry about it. Actually, we might need something like this for people too.

## There are spots for comments in several places in ISA, but they end up having to be on one record for MESSES, so they would need 
## to be separated with words, such as type_comment_name vs comment_name for factorType comments vs factor comments.

## studies/protocols/paramters causes big issues, specifically parameterName. First instance of 2 layers of nesting. protocols 
## can have multiple parameters and parameters can have multiple comments. In order to handle a nested conversion diretive call 
## for the comments need to be able to pass a parameter or something with it so we can know which parameter to focus on the context on.

## May need to expand "test" keyword to be able to handle & and |.


## TODO There are a couple of things that need to be verified with the ISA people.
## 1. What are the "configs" about when validating ISA-JSON?
## 2. For assay_schema it says the technologyType property is an object with a ontologyAnnotation property that is an ontology annotation, 
##    but the examples just have it as an ontology annotation without the surrounding object and property. This validates without error.
## 3. What are @id's? The hashtag does not appear to be used correctly and dereferencing them is difficult.

directives = \
{
 ## Top level strings.
 "description": {
     "no_id_needed": {
         "value_type": "section_str",
         "required": "True",
         "fields": [
           "description"
         ],
         "table": "project"
         }
     },
 "identifier": {
     "no_id_needed": {
         "value_type": "section_str",
         "required": "True",
         "fields": [
           "identifier"
         ],
         "table": "project"
         }
     },
 "title": {
     "no_id_needed": {
         "value_type": "section_str",
         "required": "True",
         "fields": [
           "title"
         ],
         "table": "project"
         }
     },
 "publicReleaseDate": {
     "no_id_needed": {
         "code": "str(datetime.datetime.now().date())",
         "value_type": "section",
         "required": "True"
         }
     },
 "submissionDate": {
     "no_id_needed": {
         "code": "str(datetime.datetime.now().date())",
         "value_type": "section",
         "required": "True"
         }
     },
 ## Top level matrices.
 "people": {
     "no_id_needed": {
         "value_type": "section_matrix",
         "required": "True",
         "headers": [
           "\"@id\"=\"#person/\"PI_first_name",  ## TODO, either make it so you can mix literal and field values or add @id's at the end of the program.
           "\"address\"=address",
           "\"affiliation\"=institution",
           "\"email\"=PI_email",
           "\"firstName\"=PI_first_name",
           "\"lastName\"=PI_last_name",
           "\"phone\"=PI_phone"
         ],
         "table": "project"
         }
     },
 "studies": {
     "no_id_needed": {
         "value_type": "section_matrix",
         "required": "True",
         "headers": [
           "\"description\"=description",
           "\"identifier\"=identifier", ## This will probably be "id" as it's just a name.
           "\"title\"=title",
           "\"filename\"=filename",  ## TODO, need to be able to combine literals with fields to make a unique filename.
           "\"publicReleaseDate\"=", ## TODO, need to be able to run code here. Could probably just redirect to another directive that runs code.
           "\"submissionDate\"=",
           "\"people\"=#studies/people", ## TODO, implement some kind of recursion so we can execute another directive for people.
           "\"protocols\"=#studies/protocols",
           "\"assays\"=#studies/assays",
           "\"materials\"=#studies/materials",
           "\"processSequence\"=#studies/process",
           "\"factors\"=#studies/factors",
           "\"characteristicCategories\"=#studies/characteristicCategories",
           "\"unitCategories\"=#studies/unitCategories",
           "\"comments\"=#studies/comments"
         ],
         "table": "study"
         }
     },
 "studies/assays": {
     "no_id_needed": {
         "value_type": "section_matrix",
         "required": "True",
         "test": "id=^id",
         "headers": [
           "\"@id\"=\"#assay/\"assay(.*)_id",
           "\"filename\"=assay(.*)_filename",
           "\"technologyPlatform\"=assay(.*)_tech_platform",
           "\"comments\"=#studies/assays/comments",  ## Same as protocols/comments but assays aren't in thier own table.
           "\"measurementType\"=#studies/assays/measurement_type",  ## Same as protocols/type, but assays aren't in thier own table.
           "\"technologyType\"=#studies/assays/technology_type", ## Same as measurementType above.
           "\"dataFiles\"=#studies/assays/files",
           "\"materials\"=#studies/assays/materials"
         ],
         "table": "study"
         }
     },
 "studies/assays/files": {  
     "no_id_needed": {
         "value_type": "section_matrix",
         "required": "True",
         "test": "id=^id",  
         "headers": [
           "\"@id\"=\"#assay_file/\"assay(.*)_filename(.*)",
           "\"name\"=assay(.*)_filename(.*)",
           "\"type\"=assay(.*)_filename(.*)_type",
           "\"comments\"=#studies/assays/files/comments" ## Same as studies/protocols/comments but need to use parameters or assay(.*)_comment(.*) or something.
         ],
         "table": "study"  
         }
     },
 "studies/assays/materials": {
     "samples": {
         "value_type": "matrix",
         "required": "True",
         "table": "entity",
         "test": "assay_id=PARAM_1 & study.id=^id",  ## No table for assays, so would have to put them in study or something.
         "headers": [
           "\"@id\"=\"#sample/\"id",
           "\"name\"=id",
           "\"characteristics\"=#studies/assays/materials/samples/characteristics", ## Similar to studies/assays/materials/samples/characteristics but for factors.
           "\"factorValues\"=#studies/assays/materials/samples/factor_values",
           "\"derivesFrom\"=#studies/assays/materials/samples/derives_from",
         ],
         },
     "otherMaterials": {
         "value_type": "matrix",
         "required": "True",
         "table": "study",
         "test": "id=^id",
         "headers": [
             "\"@id\"=\"#material/\"assay(.*)_material(.*)_name",
             "\"name\"=assay(.*)_material(.*)_name",
             "\"type\"=assay(.*)_material(.*)_type", ## Must be either Extract Name or Labeled Extract Name
             "\"characteristics\"=", ## Same as studies/assays/materials/samples/characteristics, but materials are on study record maybe.
             "\"derivesFrom\"="
             ]
         }
     },
 "studies/assays/materials/samples/characteristics": {  
     "no_id_needed": {
         "value_type": "section_matrix",
         "required": "True",
         "test": "id=^id",  
         "headers": [
           "\"@id\"=\"#characteristic/\"characteristic_(.*)_name",
           "\"category\"=#studies/assays/materials/samples/characteristics/category",
           "\"value\"=characteristic_(.*)_value",  ## This could a string, number, or ontology annotation. Assuming string/number for now.
           "\"unit\"=#studies/assays/materials/samples/characteristics/unit" ## This is an ontology annotation just like protocols/type
         ],
         "table": "entity"  
         }
     },
 "studies/assays/materials/samples/characteristics/category": {
     "@id": {
         "value_type": "str",
         "required": "True",
         "table": "entity",
         "record_id": "^id",
         "fields": [
           "\"#characteristic_category/\"",
           "PARAM_1",  ## This needs to be the category name from the category that called it, but I'm not sure how to pass it as a parameter.
         ],
         },
     "characteristicType": { ## This has to be an object, but I don't have an easy way to direct to another directive.
         "value_type": "object",
         "required": "True",
         "table": "entity",
         "record_id": "^id",
         "headers": [
             "\"annotationValue\"=category_name",  ## This would probably need to be PARAM_1_name where the parameter is the category group in the calling directive.
             "\"termAccession\"=category_url",
             "\"termSource\"=category_source",
             "\"comments\"=#studies/assays/materials/samples/characteristics/category/comments"
             ]
         }
     },
 "studies/assays/materials/samples/characteristics/category/comments": {
     "no_id_needed": {
         "value_type": "section_matrix",
         "required": "True",
         "table": "entity",
         "test": "id=^id",
         "headers": [
             "\"name\"=category_comment_name" ## Note that "category" probably needs to be replaced with a parameter for the category name.
             "\"value\"=category_comment_value"
             ]
         }
     },
 "studies/protocols": {
     "no_id_needed": {
         "value_type": "section_matrix",
         "required": "True",
         "test": "study.id=^id",  ## May not need this if there is 1 study so protocols don't have a study.id field.
         "headers": [
           "\"@id\"=\"#protocol/\"id",
           "\"name\"=id",
           "\"description\"=description",
           "\"uri\"=uri",
           "\"version\"=version",
           "\"comments\"=#studies/protocols/comments",
           "\"protocolType\"=#studies/protocols/type",
           "\"parameters\"=#studies/protocols/parameters",
           "\"components\"=#studies/protocols/components"
         ],
         "table": "protocol"
         }
     },
 "studies/protocols/comments": {  
     "no_id_needed": {
         "value_type": "section_matrix",
         "required": "True",
         "test": "id=^id",  
         "headers": [
           "\"name\"=comment_name",
           "\"value\"=comment_value", 
         ],
         "table": "protocol"  
         }
     },
 "studies/protocols/type": {
     "@id": {
         "value_type": "str",
         "required": "True",
         "table": "protocol",
         "record_id": "^id",
         "fields": [
             "\"ontology_annotation/\"",
             "id"
             ]
         },
     "annotationValue": {
         "value_type": "str",
         "required": "True",
         "table": "protocol",
         "record_id": "^id",
         "fields": [
             "id"
             ]
         },
     "termAccession": {
         "value_type": "str",
         "required": "True",
         "table": "protocol",
         "record_id": "^id",
         "fields": [
             "term_url"
             ]
         },
     "termSource": {
         "value_type": "str",
         "required": "True",
         "table": "protocol",
         "record_id": "^id",
         "fields": [
             "term_source_name"
             ]
         },
     "comments": {
         "value_type": "matrix",
         "required": "True",
         "table": "protocol",
         "test": "id=^id",
         "headers": [
             "\"name\"=type_comment_name"
             "\"value\"=type_comment_value"
             ]
         },
     },
 "studies/protocols/parameters": {  ## May need field collate for this and need to concat regex with literal values.
     "no_id_needed": {
         "value_type": "section_matrix",
         "required": "True",
         "test": "id=^id",  
         "headers": [
           "\"@id\"=\"#parameter/\"parameter(.*)_id",
           "\"parameterName\"=#studies/protocols/parameters/name", ## May have to call this directive with a parameter for the parameter_id so it can be used when called.
         ],
         "table": "protocol"  
         }
     },
 "studies/protocols/parameters/name": {
     "@id": {
         "value_type": "str",
         "required": "True",
         "table": "protocol",
         "record_id": "^id",
         "fields": [
             "\"ontology_annotation/\"",
             "parameter(.*)_id"          ## Instead of this, PARAM_1 or PARAM1 or something to say to place the paramter given to the directive here.
             ]
         },
     "annotationValue": {
         "value_type": "str",
         "required": "True",
         "table": "protocol",
         "record_id": "^id",
         "fields": [
             "parameter(.)_id"
             ]
         },
     "termAccession": {
         "value_type": "str",
         "required": "True",
         "table": "protocol",
         "record_id": "^id",
         "fields": [
             "parameter(.*)_term_url"
             ]
         },
     "termSource": {
         "value_type": "str",
         "required": "True",
         "table": "protocol",
         "record_id": "^id",
         "fields": [
             "parameter(.*)_term_source_name"
             ]
         },
     "comments": {
         "value_type": "matrix",
         "required": "True",
         "table": "protocol",
         "test": "id=^id",
         "headers": [
             "\"name\"=parameter(.*)_comment(.*)_name"  ## This is a problem, would need to generalize the group matching to more than 1 in regex. Could be done by concatenating group values.
             "\"value\"=parameter(.*)_comment(.*)_value" ## If we make replace parameters step 1, then could do PARAM_1_comment(.*)_value.
             ]
         },
     },
 "studies/protocols/components": {  
     "no_id_needed": {
         "value_type": "section_matrix",
         "required": "True",
         "test": "id=^id",  
         "headers": [
           "\"componentName\"=component(.*)_name",
           "\"componentType\"=#studies/protocols/components/type", 
         ],
         "table": "protocol"  
         }
     },
 "studies/protocols/components/type": {
     "@id": {
         "value_type": "str",
         "required": "True",
         "table": "protocol",
         "record_id": "^id",
         "fields": [
             "\"component/\"",
             "component(.*)_id"
             ]
         },
     "annotationValue": {
         "value_type": "str",
         "required": "True",
         "table": "protocol",
         "record_id": "^id",
         "fields": [
             "component(.*)_id"
             ]
         },
     "termAccession": {
         "value_type": "str",
         "required": "True",
         "table": "protocol",
         "record_id": "^id",
         "fields": [
             "component(.*)_term_url"
             ]
         },
     "termSource": {
         "value_type": "str",
         "required": "True",
         "table": "protocol",
         "record_id": "^id",
         "fields": [
             "component(.*)_term_source_name"
             ]
         },
     "comments": {
         "value_type": "matrix",
         "required": "True",
         "table": "protocol",
         "test": "id=^id",
         "headers": [
             "\"name\"=component(.*)_comment(.*)_name"
             "\"value\"=component(.*)_comment(.*)_value"
             ]
         },
     },
 "studies/factors": {  ## Need a way to tell this conversion directive to filter by the study that called it. Caret notation fixes this I think.
     "no_id_needed": {
         "value_type": "section_matrix",
         "required": "True",
         "test": "study.id=^id",  ## Possible way to indicate that the id should come from the record that called it. The caret could be special character.
         "headers": [
           "\"@id\"=\"#factor/\"id",
           "\"factorName\"=id",
           "\"factorType\"=#studies/factor/type",
           "\"comments\"=#studies/factors/comments"
         ],
         "table": "factor"  ## Table might not matter, or we use this to select a record within a table.
         }
     },
 "studies/factors/type": {
     "@id": {
         "value_type": "str",
         "required": "True",
         "table": "factor",
         "record_id": "^id",
         "fields": [
             "\"ontology_annotation/\"",
             "id"
             ]
         },
     "annotationValue": {
         "value_type": "str",
         "required": "True",
         "table": "factor",
         "record_id": "^id",
         "fields": [
             "id"
             ]
         },
     "termAccession": {
         "value_type": "str",
         "required": "True",
         "table": "factor",
         "record_id": "^id",
         "fields": [
             "term_url"
             ]
         },
     "termSource": {
         "value_type": "str",
         "required": "True",
         "table": "factor",
         "record_id": "^id",
         "fields": [
             "term_source_name"
             ]
         },
     "comments": {  ## Need a way to limit this to the current factor, possibly through the table field.
         "value_type": "matrix",
         "required": "True",
         "table": "factor",
         "test": "id=^id",
         "headers": [
             "\"name\"=type_comment_name"
             "\"value\"=type_comment_value"
             ]
         },
     },
 "studies/factors/comments": {  
     "no_id_needed": {
         "value_type": "section_matrix",
         "required": "True",
         "test": "id=^id",  
         "headers": [
           "\"name\"=comment_name",
           "\"value\"=comment_value", 
         ],
         "table": "factor"  
         }
     },
}




