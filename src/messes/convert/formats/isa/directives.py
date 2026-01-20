# -*- coding: utf-8 -*-
"""
conversion tags for the ISA-JSON format
"""

import copy


## How do you include an arbitrary file in ISA that is not necessarily an input or output to a process?
## For instance a database or pdf description of a protocol. You can add them to an assay in the JSON form,
## but if it isn't connected to a process I don't think it will show up in the TAB. Do you just include it 
## in the directory?

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
  


## There are spots for comments in several places in ISA, but they end up having to be on one record for MESSES, so they would need 
## to be separated with words, such as type_comment_name vs comment_name for factorType comments vs factor comments.

## studies/protocols/paramters causes big issues, specifically parameterName. First instance of 2 layers of nesting. protocols 
## can have multiple parameters and parameters can have multiple comments. In order to handle a nested conversion diretive call 
## for the comments need to be able to pass a parameter or something with it so we can know which parameter to focus on the context on.

## May need to add silent=True to a lot of the directives.

## You can have multiple "Protocol REF" columns in a row without error. In the JSON subsequent Protocol REF 
## columns are converted by creating processes that have no inputs or outputs but simply point to the next 
## process. For example, if you have 2 Protocol REF columns there will be 1 process with inputs, but no outputs 
## and it will point to the next process that has no inputs, but does have outputs and points to the previous 
## process.


## TODO Add which file the properties for each JSON object comes from. For example, the "measurementType" comes from the investigation file for assay objects.
## Check to see if ISAtools looks for duplicate @id, for example if 2 people have the same one.
## Add a section in the conversion_directives documentation explaining the "pass_through" built-in, 
## so users can give silent and required fields to individual headers in a matrix.

## If an otherMaterials object has "extract-" in the "name" it will be removed before 
## adding it in the column when converting to Tab. Otherwise it will use the "name" value directly.
## Ex:
# {'@id': '#material/extract-G-0.1-aliquot1',
#  'characteristics': [],
#  'name': 'extract-G-0.1-aliquot1',
#  'type': 'Extract Name'}
## Will put "G-0.1-aliquot1" in "Extract Name" column.

# {'@id': '#material/extract-G-0.1-aliquot1',
#  'characteristics': [],
#  'name': 'asdf',
#  'type': 'Extract Name'}
## Will put "asdf" in "Extract Name" column.

## isatools validate does not check if the same factor is specified twice in the factorValues 
## of sample objects. There is an issue in example BII-I-1 where some samples have the same 
## factor declared multiple times in their factorValues and thus when you convert from Tab to 
## JSON and back to Tab there are missing values. One sample is 'S-0.1-aliquot11'.

## isatools validate doesn't check if an input is used in 2 different processes.
## Not sure if that is an error or not. Ask ISA people about it.

## All sources in a single study must have the same characteristics. If they don't the 
## conversion code of JSON to Tab will fail. In theory these could be added as blank values for sources 
## that don't have them in their "characteristics", but the code doesn't do that.

## When converting from JSON to Tab the code computes a graph for the studies (not sure on the details), 
## and then later when it is trying to write out the actual tabular file it finds the longest 
## node path in the study and uses it as a template. This means that certain things will cause 
## an error. Specifically, all of the processes in a study have to have the same set/subset 
## of protocols. For example, a protocol sequence like protocolA -> protocolB -> protocolC, and 
## a sequence like protocolD -> protocolE -> protocolF are not compatible and cannot be 
## in the same study. A sequence like protocolA -> protocolB -> protocolC and protocolA -> protocolB 
## are okay though because the second sequence is a subset of the first. This makes some sense when 
## considering the structure of the tabular version of the format, but you can create a study Tab 
## format file manually that has different protocol names in the same "Protocol REF" column and 
## there is no error or warning in validation.

## Even though otherMaterials are in the materials object for a study if you have a 
## process with an otherMaterial in the inputs or outputs you will get an error. 
## "from_dict" in "process.py" does not look for inputs or outputs in the otherMaterials dict. 
## Not sure if this is intended or a bug.

## Samples can only derive from sources! This is significant due to how we classify 
## subjects and samples.

## Samples can't derive from samples in the sense that you can't put a sample in the 
## "derivesFrom" field of a sample object, but you can create a process with a sample 
## input and output which will create a proper study Tab format file. You do have 
## to give the output a different ID though. If you create a process with the same 
## sample as input and output it will not carry through to the study Tab file. 
## If the input is a sample and the output is a source then the sample also won't 
## carry through to the Tab unless there is also a process that has samples as inputs 
## and outputs. This might also apply for the case when the input and output are the 
## same sample. This is confusing, so I will try to explain. In the ISA_traversal.py 
## file I tested this. I added a process that took "#sample/sample-E-0.07-aliquot1" 
## as an input and made a new sample output "#sample/sample-E-0.07-aliquot1_1". I also 
## added a process that took "#sample/sample-E-0.07-aliquot6" as input and made a new 
## source output "#source/source-E-0.07-aliquot6_1". If both are in the JSON then 
## "E-0.07-aliquot6" will still be in the Tab file, but if only the process with 
## the new source is in the JSON then "E-0.07-aliquot6" will not be in the Tab file.

## Looks like you can't have different protocols in the same Protocol REF column, 
## so how we do factors won't work. We can't have "naive", "allogenic", and "syngenic" 
## in 1 column, they have to be different studies.
## This was an error, and I submitted a PR to isatools.

## For JSON, it is checked that samples must derive from sources, but if you make an 
## otherMaterial derive from a sample there is no error. If it follows the same logic 
## then otherMaterials can only derive from otherMaterials. The JSON Schema should 
## probably be changed to indicate that it can derive from a sample.

## You can only have either 1 sample/material node or 1 data file node as input/output 
## to a process. 
## A tab file like:
# "Sample Name"	"Protocol REF"	"Extract Name"	"Raw Data File"	"Protocol REF"	"Raw Data File"
# "C-0.07-aliquot1"	"mRNA extraction"	"C-0.07-aliquot1"	"E-MAXD-4-raw-data-426648549.txt"	"biotin labeling"	"E-MAXD-4-raw-data-426648603.txt"
## Will create a process like:
# [{'@id': '#process/a992051d-01b0-4d7c-b077-e33c28ba34c6',
#   'name': '',
#   'performer': '',
#   'date': '',
#   'executesProtocol': {'@id': '#protocol/107ecb45-f09f-4def-9ad1-03dc0b2fd5bb'},
#   'parameterValues': [],
#   'inputs': [{'@id': '#sample/7751cb29-6d48-4f74-a272-aea592edc53b'}],
#   'outputs': [{'@id': '#material/ad9f236d-1a78-44ad-8bf7-e89cb7d35229'}],
#   'comments': [],
#   'nextProcess': {'@id': '#process/762c5bf2-4f7f-42d6-b7d5-66f3b9dbe44a'}},
#  {'@id': '#process/762c5bf2-4f7f-42d6-b7d5-66f3b9dbe44a',
#   'name': '',
#   'performer': '',
#   'date': '',
#   'executesProtocol': {'@id': '#protocol/0fcd509b-c098-47e1-90f5-97112c86c643'},
#   'parameterValues': [],
#   'inputs': [{'@id': '#data_file/08257e1a-c185-43e3-bcf3-26b0b2913749'}],
#   'outputs': [{'@id': '#data_file/87ce1bce-b7b2-41b7-bb31-64f0b0c41566'}],
#   'comments': [],
#   'previousProcess': {'@id': '#process/a992051d-01b0-4d7c-b077-e33c28ba34c6'}}]
## Notice how the second process in the sequence uses a data_file as input, but the 
## first process had a material output. There is no way to get the processes pull 
## both the material and data file in as outputs to the first and inputs to the second.
## Make sure to separate protocols that produce both into 2 different protocols.
## Should probably add a check for this in validation.


## 1-22-2024
## I changed the code in isatab.dump.write.py and submitted a PR, but it isn't 
## accepted yet. I'm not sure they have even seen it again. I have found an issue 
## with the change I made. If a data file does not have a type, there is an issue.
## If there is no type, then the label is "" and several column names such as "Sample Name" 
## get replaced with the empty string. I feel like the solution is either to require 
## a "type" field on data, or check to see if the label is empty and replace it with 
## "Raw Data File" or something. I need to see what happens in this situation with the 
## unmodified code.



## TODO There are a couple of things that need to be verified with the ISA people.
## 1. What are the "configs" about when validating ISA-JSON?
## 2. For assay_schema it says the technologyType property is an object with a ontologyAnnotation property that is an ontology annotation, 
##    but the examples just have it as an ontology annotation without the surrounding object and property. This validates without error.
## 3. What are @id's? The hashtag does not appear to be used correctly and dereferencing them is difficult.
## 4. Does derivesFrom in samples have to be a source? 
##    Are you supposed to the collapse the lineage for each sample so that derivesFrom is the source and not the most recent sample?
##    The derivesFrom field is an array of source_schema, not sample_schema.
## 5. Critical errors that prevent JSON creation will sometimes show up as warnings in the output. For example a sample name in an 
##    assay that is not in the study will be a warning, but is a fatal error.
## 6. It is said in the specification that source to sample must have a sample collection type protocol, but the example doesn't follow this.
## 7. The provided JSON examples and what is generated when you use convert are different. Comments (PRIDE Accession) appear on data files (in provided example) when they should be on the process (in converted).
## 8. The DOI regex doesn't match proper DOIs. In isatab > defaults.py  
##    _RX_DOI = compile(r'(10[.][0-9]{4,}(?:[.][0-9]+)*/(?:(?![%"#? ])\\S)+)') should be 
##    _RX_DOI = compile(r'(10[.][0-9]{4,}(?:[.][0-9]+)*/(?:(?![%"#? ])\S)+)')  
##    There is and extra back slash before \S that shouldn't be there.
##    Should be able to handle doi: and https://...
## 9. A line like  Study Publication DOI	""  reports a required property warning. How is a "required" property a warning?
## 10. check_protocol_fields() in "rules_40xx.py" should be in "rules_10xx.py".
## 11. If you run isatab.validate with no configuration xmls you get errors:
##     validation_dict = isatab.validate(open('C:/Users/Sparda/Desktop/Moseley Lab/Code/MESSES/isadatasets/tab/BII-I-1_validated/i_investigation.txt'), config_dir='C:/Users/Sparda/Desktop/Moseley Lab/Code/MESSES/isadatasets/tab/BII-I-1_validated/')
##     validation_dict
     #  {'errors': [{'message': 'Measurement/technology type invalid',
     #   'supplemental': 'Measurement protein expression profiling/technology mass spectrometry, STUDY ASSAY.0',
     #   'code': 4002},
     #  {'message': 'Measurement/technology type invalid',
     #   'supplemental': 'Measurement metabolite profiling/technology mass spectrometry, STUDY ASSAY.0',
     #   'code': 4002},
     #  {'message': 'Measurement/technology type invalid',
     #   'supplemental': 'Measurement transcription profiling/technology DNA microarray, STUDY ASSAY.0',
     #   'code': 4002},
     #  {'message': 'Measurement/technology type invalid',
     #   'supplemental': 'Measurement transcription profiling/technology DNA microarray, STUDY ASSAY.1',
     #   'code': 4002},
     #  {'message': 'Unknown/System Error',
     #   'supplemental': "The validator could not identify what the error is: ('[sample]', '')",
     #   'code': 0}],
     # 'warnings': [{'message': 'DOI is not valid format',
     #   'supplemental': 'Found 10.1186/jbiol54 in DOI field',
     #   'code': 3002},
     #  {'message': 'DOI is not valid format',
     #   'supplemental': 'Found 10.1186/jbiol54 in DOI field',
     #   'code': 3002}],
     # 'info': [],
     # 'validation_finished': False}
## The issue appears to be in "rules_40xx.py" in "check_measurement_technology_types()" 
## if (lowered_mt, lowered_tt) not in configs.keys():    should be   if config and (lowered_mt, lowered_tt) not in configs.keys():
## I don't think checking for config to exist will work, because of the hard coded stuff described below. You have 
## to have an entry in configs for sample and investigation or you get other errors.
## There is another issue in "validate/rules/core.py" in ISAStudyValidator it is hard coded to look for ('[sample]', '') 
## in configs to assign in its params. This will raise a keyerror. 
## There is another issue in "rules_40xx.py" in "check_investigation_against_config()" The line 53 
## "config_fields = configs[('[investigation]', '')].get_isatab_configuration()[0].get_field()" hard codes looking for ('[investigation]', '')
## You must have an xml file for each measurement type and technology type combination in your data. 
## If you don't there will be an error due to "assay_table" not getting added to ISAAssayValidator 

## 12. The code values don't match up. In isatab/validate/rules/defaults.py in ASSAY_RULES_MAPPING the entry, 
##     {'rule': check_required_fields, 'params': ['assay_table', 'config'], 'identifier': '4003'} has the 4003 identifier, but 
##     the corresponding "rule" function in rules_40xx.py "check_required_fields" has codes for 4010 and 4013.
## 13. BII-I-1.json is not converted correctly. It doesn't match what the python conversion produces, and also doesn't 
##     validate well. You can see many factors and units are missing in the appropriate assay samples.
## 14. It looks like the JSON validate checks that some things are used, but Tab does not. For instance, JSON validate 
##     reports that "BTO" Ontology Source is not used, but Tab does not (BII-I-1).
## 15. In isajson -> validate.py I think there is an issue in check_study_and_assay_graphs(). It checks 
##     every process so there are a lot of the same warnings repeated over and over. (BII-I-1)
## 16. Converting from JSON to Tab does not look for inputs and outputs in otherMaterials 
##     (at least for studies, not sure about assays). otherMaterial inputs and outputs are 
##     simply dropped and don't show up in the Tab. According to the JSON Schema you should 
##     be able to have an otherMaterial in input or output.
## 17. ISAJSON to Tab conversion errors if 2 different protocols are at the same process level. 
##     For instance, if you have a study with "growth protocol" and "growth protocol 2" in the same 
##     Protocol REF column it will convert to JSON fine, and validate fine, but if you try to convert 
##     the generated JSON back to Tab you get a Key Error. The generated JSON also validates with no 
##     messages regarding this issue.

## Note that to see these errors I needed to add code to display the traceback for the keyerror caught in the isajson validation.
## It's around line 925.
## 18. There is an error during validation of the JSON if an assay does not have the "dataFiles" attribute.
##     File "C:\Python310\lib\site-packages\isatools\isajson\validate.py", line 57, in get_data_file_ids
##       data_file_ids.extend([data_file["@id"] for data_file in assay_json["dataFiles"]])
##     Either make this a required key in the schema or change this bit of code so it doesn't run if 
##     the attribute isn't there.
## 19. Same as 18 but for "outputs" in a process.
##     File "C:\Python310\lib\site-packages\isatools\isajson\validate.py", line 67, in <listcomp>
##       for o in process["outputs"]] for process in
## 20. Same as 18 but for "parameters" in a protocol.
##     File "C:\Python310\lib\site-packages\isatools\isajson\validate.py", line 179, in <listcomp>
##       return [elem for iterabl in [[param["@id"] for param in protocol["parameters"]] for protocol in
## 21. Same as 18 but for "@id" in a category in unitCategories.
##     File "C:\Python310\lib\site-packages\isatools\isajson\validate.py", line 316, in <listcomp>
##       return [category["@id"] for category in study_or_assay_json["unitCategories"]]
## 22. Same as 18 but for "@id" in a characteristic.
##     File "C:\Python310\lib\site-packages\isatools\isajson\validate.py", line 322, in get_study_unit_category_ids_in_materials_and_processes
##       [[characteristic["unit"]["@id"] if "unit" in characteristic.keys() else None for
## 23. Same as 18 but for "publications". Note this also applies for publications in studies.
##     File "C:\Python310\lib\site-packages\isatools\isajson\validate.py", line 474, in check_dois
##       for ipub in isa_json["publications"]:
## 24. Same as 18 but for "ontologySourceReferences".
##     File "C:\Python310\lib\site-packages\isatools\isajson\validate.py", line 572, in check_ontology_sources
##       for ontology_source in isa_json["ontologySourceReferences"]:

    
## 25. On line 675 in isajson/validate.py the function check_measurement_technology_types catches a KeyError and writes a message 
##     indicating that a configuration could not be loaded. This hides the case when "technologyType" or "measurementType" is 
##     not in an assay or if they do not have an "annotationValue" field. The real problem is that the assay does not have these 
##     fields and that is not clearly communicated to the user. Instead they would think there is a file load problem.

## 26. Are measurement and technology type required for assays?

## 27. In isajson/validate.py in the function check_protocol_parameter_ids_usage() it manually adds 
##     "#parameter/Array_Design_REF" to the list of parameters to look for and has a comment that says 
##     "special case". If you don't use this parameter then a warning is reported. Should this actually 
##     be there? It is a superflous warning unless you use that parameter. Is it a required parameter?

## In rules 40xx the function check_investigation_against_config creates a warning for "required" fields.
## This should either be an error or not call them "required".

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
           "id"
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
 
 "ontologySourceReferences": {
     "no_id_needed": {
         "value_type": "section_matrix",
         "required": "False",
         "optional_headers": [
             "name",
             "description",
             "file",
             "version"
             ],
         "table": "ontology_source",
         "default": []
         }
     },
 
 "publications": {
     "no_id_needed": {
         "value_type": "section_matrix",
         "required": "False",
         "optional_headers": [
             "pubMedID",
             "doi",
             "authorList",
             "title"
             ],
         "headers": [
           "\"status\"=publications%status()",
         ],
         "table": "publication",
         "default": []
         }
     },
 "publications%status": {
     "no_id_needed": {
         "execute": "dumb_parse_ontology_annotation(^.status)",
         "value_type": "section",
         "required": "False"
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
         "optional_headers": [
             "address",
             "affiliation",
             "email",
             "phone",
             "fax",
             "midInitials",
             "firstName",
             "lastName"
             ],
         "headers": [
           "\"@id\"=people%@id()",
           "\"roles\"=people%roles()"
         ],
         "table": "people"
         }
     },
 "people%@id": {
     "no_id_needed": {
         "value_type": "section_str",
         "required": "False",
         "fields": [
             "\"#people/\"",
             "^.firstName",
             "\"_\"",
             "^.lastName"
             ],
         }
     },
 ## Alternative way to do the @id.
 # "people%@id": {
 #     "no_id_needed": {
 #         "value_type": "str",
 #         "required": "False",
 #         "code": "f\"#people/{calling_record_attributes['firstName']}_{calling_record_attributes['lastName']}\"",
 #         }
 #     },
 "people%roles": {
     "no_id_needed": {
         "execute": "dumb_parse_ontology_annotation(^.roles)",
         "value_type": "section",
         "required": "False"
         }
     },
 
 
 
 
 "studies": {
     "no_id_needed": {
         "value_type": "section_matrix",
         "required": "True",
         "headers": [
           "\"description\"=description",
           "\"identifier\"=id",
           "\"title\"=title",
           "\"processSequence\"=process",    ## Created in pre-directive step.
           "\"characteristicCategories\"=characteristic_categories", ## Created in pre-directive step.
           "\"unitCategories\"=unit_categories", ## Created in pre-directive step.
           "\"filename\"=filename",   ## Created in pre-directive step.
           "\"publicReleaseDate\"=studies%release_date()",
           "\"submissionDate\"=studies%release_date()",
           "\"people\"=studies%people()",
           "\"studyDesignDescriptors\"=studies%descriptors()",
           "\"protocols\"=studies%protocols()",
           "\"assays\"=studies%assays()",
           "\"materials\"=studies%materials()",   ## Needs code
           "\"factors\"=studies%factors()",
           ## publications keyword is added below since it is very similar to the investigation publication so it is reused.
         ],
         "table": "study",
         "test": "type=\"study\""
         }
     },
 "studies%release_date": {
     "no_id_needed": {
         "code": "str(datetime.datetime.now().date())",
         "value_type": "section",
         "required": "True"
         }
     },
 "studies%people": {
     "no_id_needed": {
         "value_type": "section_matrix",
         "required": "True",
         "optional_headers": [
             "address",
             "affiliation",
             "email",
             "phone",
             "fax",
             "midInitials",
             "firstName",
             "lastName"
             ],
         "headers": [
           "\"@id\"=people%@id()",
           "\"roles\"=people%roles()"
         ],
         "table": "people",
         "test": "study.id=^.id"
         }
     },
 ## TODO think about adding default empty list value, convert might need a change to allow for adding empty list and dict.
 "studies%descriptors": {
     "no_id_needed": {
         "execute": "dumb_parse_ontology_annotation(^.descriptors)",
         "value_type": "section",
         "required": "False"
         }
     },
 
 
 "studies%protocols": {
     "no_id_needed": {
         "value_type": "section_matrix",
         "required": "True",
         "test": "study.id=^.id",
         "optional_headers": [
             "version"
             ],
         "headers": [
           "\"@id\"=studies%protocols%@id()",
           "\"name\"=id",
           "\"uri\"=studies%protocols%uri()",
           "\"description\"=description",
           "\"protocolType\"=studies%protocols%type()",
           "\"parameters\"=studies%protocols%parameters()",
           "\"components\"=studies%protocols%components()"
         ],
         "table": "protocol"
         }
     },
 "studies%protocols%@id": {
     "no_id_needed": {
         "value_type": "section_str",
         "fields": [
             "\"#protocol/\"",
             "^.id"
             ],
         }
     },
  "studies%protocols%uri": {
      "no_id_needed": {
          "value_type": "section_str",
          "fields": [
              "^.filename"
              ],
          "required": "False"
          }
      },
 "studies%protocols%type": {
     "no_id_needed": {
         "execute": "determine_ISA_protocol_type_dumb_parse(^.*)",
         "value_type": "section",
         "required": "False"
         }
     },
 "studies%protocols%parameters": {
     "no_id_needed": {
         "value_type": "section",
         "required": "False",
         "execute": "determine_ISA_parameters_dumb_parse(^.*)",
         "default": []
         }
     },
 "studies%protocols%components": {
     "no_id_needed": {
         "value_type": "section",
         "required": "False",
         "execute": "determine_ISA_components_dumb_parse(^.*)"
         }
     },
 
 
 
 "studies%assays": {
     "no_id_needed": {
         "value_type": "section_matrix",
         "required": "True",
         "test": "parent_id=^.id",
         "headers": [
           "\"@id\"=studies%assays%@id()",
           "\"filename\"=filename", ## Added in pre-directive step.
           "\"technologyPlatform\"=studies%assays%technologyPlatform()",  ## Added in pre-directive step.
           "\"measurementType\"=studies%assays%measurementType()",   ## Added in pre-directive step.
           "\"technologyType\"=studies%assays%technologyType()",   ## Added in pre-directive step.
           "\"dataFiles\"=data_files",  ## Added in pre-directive step.
           "\"characteristicCategories\"=characteristic_categories", ## Created in pre-directive step.
           "\"unitCategories\"=unit_categories", ## Created in pre-directive step.
           "\"processSequence\"=process",    ## Created in pre-directive step.
           "\"materials\"=studies%assays%materials()"
         ],
         "table": "study"
         }
     },
 "studies%assays%@id": {
     "no_id_needed": {
         "value_type": "section_str",
         "required": "False",
         "fields": [
             "\"#assay/\"",
             "^.id"
             ],
         }
     },
 "studies%assays%technologyType": {
     "no_id_needed": {
         "value_type": "section",
         "required": "False",
         "execute": "pass_through(^.technology_type)",
         }
     },
 "studies%assays%technologyPlatform": {
     "no_id_needed": {
         "value_type": "section_str",
         "required": "False",
         "fields": [
             "technology_platform"
             ],
         }
     },
 "studies%assays%measurementType": {
     "no_id_needed": {
         "value_type": "section",
         "required": "False",
         "execute": "pass_through(^.measurement_type)",
         }
     },
 ## assay materials can use almost the same directives as studies%materials, so it is added below.
 
 
 
 "studies%materials": {
     "sources": {
         "value_type": "matrix",
         "required": "True",
         "table": "entity",
         "test": "study.id=^.id and isa_type=source",
         "headers": [
           "\"@id\"=studies%materials%sources%@id()",
           "\"name\"=id",
           "\"characteristics\"=studies%assays%materials%sources%characteristics()"
         ],
         },
     "samples": {
         "value_type": "matrix",
         "required": "True",
         "table": "entity",
         "test": "study.id=^.id and isa_type=sample",
         "headers": [
           "\"@id\"=studies%materials%samples%@id()",
           "\"name\"=id",
           "\"characteristics\"=studies%assays%materials%sources%characteristics()",
           "\"factorValues\"=studies%assays%materials%samples%factorvalues()",
         ],
         },
     "otherMaterials": {
         "value_type": "matrix",
         "required": "True",
         "table": "entity",
         "test": "study.id=^.id and isa_type=material",
         "headers": [
             "\"@id\"=studies%materials%otherMaterials%@id()",
             "\"name\"=id",
             "\"type\"=studies%assays%materials%otherMaterials%type()", 
             "\"characteristics\"=studies%assays%materials%sources%characteristics()",
             ]
         }
     },
 "studies%materials%sources%@id": {
     "no_id_needed": {
         "value_type": "section_str",
         "required": "False",
         "fields": [
             "\"#source/\"",
             "^.id"
             ],
         }
     },
 "studies%assays%materials%sources%characteristics": {
     "no_id_needed": {
         "value_type": "section",
         "required": "False",
         "execute": "determine_ISA_characteristics_dumb_parse(^.*)"
         }
     },
 
 "studies%materials%samples%@id": {
     "no_id_needed": {
         "value_type": "section_str",
         "required": "False",
         "fields": [
             "\"#sample/\"",
             "^.id"
             ],
         }
     },
 "studies%assays%materials%samples%factorvalues": {
     "no_id_needed": {
         "value_type": "section",
         "required": "False",
         "execute": "determine_ISA_factor_values_dumb_parse(^.*)"
         }
     },
 "studies%materials%otherMaterials%@id": {
     "no_id_needed": {
         "value_type": "section_str",
         "required": "False",
         "fields": [
             "\"#material/\"",
             "^.id"
             ],
         }
     },
 "studies%assays%materials%otherMaterials%type": {
     "no_id_needed": {
         "value_type": "section_str",
         "required": "False",
         "fields": [
             "^.isa_materialtype",
             ],
         "default": "Extract Name"
         }
     },
 
 
 "studies%factors": {
     "no_id_needed": {
         "value_type": "section_matrix",
         "required": "True",
         "test": "study.id=^.id",  
         "headers": [
           "\"@id\"=studies%factors%@id()",
           "\"factorName\"=id",
           "\"factorType\"=studies%factor%type()",
         ],
         "table": "factor"
         }
     },
 "studies%factors%@id": {
     "no_id_needed": {
         "value_type": "section_str",
         "required": "False",
         "fields": [
             "\"#factor/\"",
             "^.id"
             ],
         }
     },
 "studies%factor%type": {
     "no_id_needed": {
         "execute": "determine_ISA_factor_type_dumb_parse(^.*)",
         "value_type": "section",
         "required": "False"
         }
     },
}


assay_materials = copy.deepcopy(directives["studies%materials"])
del assay_materials["sources"]
directives["studies%assays%materials"] = assay_materials

study_publications = copy.deepcopy(directives["publications"])
study_publications["no_id_needed"]["test"] = "study.id=^.id"
directives["studies%publications"] = study_publications
directives["studies"]["no_id_needed"]["headers"].append("\"publications\"=studies%publications()")


