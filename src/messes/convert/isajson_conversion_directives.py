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
           "\"filename\"=studies%filename()",
           "\"publicReleaseDate\"=studies%release_date()",
           "\"submissionDate\"=studies%release_date()",
           "\"people\"=studies%people()", 
           "\"protocols\"=studies%protocols()",
           "\"assays\"=#studies/assays",
           "\"materials\"=#studies/materials",   ## Needs code
           "\"processSequence\"=#studies/process", ## Needs code
           "\"factors\"=studies%factors()",
           "\"characteristicCategories\"=#studies/characteristicCategories", ## Needs code
           "\"unitCategories\"=studies%unitCategories()", ## Needs code, search factors, protocols, and entities for units
           "\"comments\"=studies%comments()"
         ],
         "table": "study"
         }
     },
 "studies%filename": {
     "no_id_needed": {
         "value_type": "section_str",
         "fields": [
             "\"s_\"",
             "^.id",
             ],
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
 "studies%assays": {
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
 "studies%materials": {
     "sources": {
         "value_type": "matrix",
         "required": "True",
         "table": "entity",
         "test": "study.id=^id and isa_type=source",
         "headers": [
           "\"@id\"=studies%materials%sources%@id()",
           "\"name\"=id",
           "\"characteristics\"=#studies/assays/materials/samples/characteristics"
         ],
         },
     "samples": {
         "value_type": "matrix",
         "required": "True",
         "table": "entity",
         "test": "study.id=^id and isa_type=sample",
         "headers": [
           "\"@id\"=studies%materials%samples%@id()",
           "\"name\"=id",
           "\"characteristics\"=#studies/assays/materials/samples/characteristics",
           "\"factorValues\"=#studies/assays/materials/samples/factor_values",
           "\"derivesFrom\"=#studies/assays/materials/samples/derives_from"
         ],
         },
     "otherMaterials": {
         "value_type": "matrix",
         "required": "True",
         "table": "entity",
         "test": "study.id=^id and isa_type=extract",
         "headers": [
             "\"@id\"=studies%materials%otherMaterials%@id()",
             "\"name\"=assay(.*)_material(.*)_name",
             "\"type\"=assay(.*)_material(.*)_type", ## Must be either Extract Name or Labeled Extract Name
             "\"characteristics\"=",
             "\"derivesFrom\"="
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
 "studies%protocols": {
     "no_id_needed": {
         "value_type": "section_matrix",
         "required": "True",
         "test": "study.id=^id",
         "optional_headers": [
             "uri",
             "version"
             ],
         "headers": [
           "\"@id\"=\"studies%protocols%@id()",
           "\"name\"=id",
           "\"description\"=description",
           "\"comments\"=studies%protocols%comments()",
           "\"protocolType\"=studies%protocols%type()",
           "\"parameters\"=studies%protocols%parameters()",
           "\"components\"#studies%protocols%components()"
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
 ## A URI can be a path to a local file, so should we look for "filename" or move to "uri"?
 ## For now "uri" is an optional header, but "filename" is what is traditionally used by MESSES.
 # "studies%protocols%uri": {
 #     "no_id_needed": {
 #         "value_type": "section_str",
 #         "fields": [
 #             "\"file:///\"",
 #             "^.filename"
 #             ],
 #         }
 #     },
 ## TODO Going to leave comments as a single field like this for now, but may create a built-in.
 "studies%protocols%comments": {
     "no_id_needed": {
         "value_type": "section_matrix",
         "required": "False",
         "headers": [
           "\"value\"=comments", 
         ],
         }
     },
 "studies%protocols%type": {
     "no_id_needed": {
         "execute": "dumb_parse_ontology_annotation(^.type)", ## Might need to be protocolType or some other field.
         "value_type": "section",
         "required": "False"
         }
     },
 "studies%protocols%parameters": {
     "no_id_needed": {
         "value_type": "section",
         "required": "True",
         "execute": "determine_ISA_parameters_dumb_parse(^.*)"
         }
     },
 "studies%protocols%components": {
     "no_id_needed": {
         "value_type": "section",
         "required": "True",
         "execute": "determine_ISA_components_dumb_parse(^.*)"
         }
     },
 "studies/factors": {
     "no_id_needed": {
         "value_type": "section_matrix",
         "required": "True",
         "test": "study.id=^.id",  
         "headers": [
           "\"@id\"=studies%factors%@id()",
           "\"factorName\"=id",
           "\"factorType\"=studies%factor%type()", ## This is probably the same as name, should we get rid of this?
           "\"comments\"=studies%factor%comments()"
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
         "execute": "dumb_parse_ontology_annotation(^.type)",
         "value_type": "section",
         "required": "False"
         }
     },
 "studies%factor%comments": {
     "no_id_needed": {
         "value_type": "section_matrix",
         "required": "False",
         "headers": [
           "\"value\"=comments", 
         ],
         }
     },
}




