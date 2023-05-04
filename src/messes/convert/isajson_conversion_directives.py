# -*- coding: utf-8 -*-
"""
conversion tags for the ISA-JSON format
"""

## MESSES JSON doesn't have places for more than 1 person, publications, or ontology terms.
## There are people under study and investigation in ISA.
## Factors have a name and an annotationValue. They can be the same, but it isn't clear what the difference is.
## Samples can have multiple parents, but not in MESSES JSON.
## Look at arrayexpress as a repo.

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
           "\"identifier\"=identifier",
           "\"title\"=title",
           "\"filename\"=filename",  ## TODO, need to be able to combine literals with fields to make a unique filename.
           "\"publicReleaseDate\"=", ## TODO, need to be able to run code here.
           "\"submissionDate\"=",
           "\"people\"=#studies/people", ## TODO, implement some kind of recursion so we can execute another directive for people.
           "\"protocols\"=#studies/protocol",
           "\"assay\"=#studies/assay",
           "\"materials\"=#studies/materials",
           "\"processSequence\"=#studies/process",
           "\"factors\"=#studies/factors",
           "\"characteristicCategories\"=#studies/characteristicCategories",
           "\"unitCategories\"=#studies/unitCategories"
         ],
         "table": "study"
         }
     },
 "studies/factors": {
     "no_id_needed": {
         "value_type": "section_matrix",
         "required": "True",
         "headers": [
           "\"@id\"=\"#person/\"PI_first_name",
           "\"factorName\"=id",
           "\"factorType\"=#studies/factor/type"
         ],
         "table": "study"
         }
     },
}




