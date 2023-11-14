# -*- coding: utf-8 -*-
"""
Functions For ISA Format
------------------------
"""

import sys
import copy
import re

from messes.convert import built_ins

## TODO if study.id and assay id are on records don't overwrite.
## Add messaging to indicate when study and assay ids are generated.
## Require samples at end of lineage to have study.id so we can connect to studies in the table.
## Add a step after study identification. If user gives 3 studies and we detect only 1, then 
## that means to break the study into 3, this isn't an error, just make 3.
## After iddentifying studies and assays using the collection protocol, look for 
## matching protocols after the collection protocol and include them in the study. 
## In other words put protocols common to assays in the study.

## TODO assays are going to be studies that inherit from a study. Add "type" attribute that is "study" or "assay".
## Add validation so that assays must have a type "assay" and a parent_id. The parent must be a study.
## Studies aren't required to have a type, but if there is a parent_id it must have a type and must be assay.
## Double check this logic with Hunter.

## TODO check that if you have multiple measurements in the measurement table for the same entity that things work as expected.
## Make sure that data_files are found and handled correctly for multiple measurements. Test multiple measurements in the table, as well 
## as mulitple protocol.id's on the same measurement.
## Test what happens if study.id on a childless sample is wrong, for example a icms sample marked as in the nmr study.
## Test what happens if icms samples are arbitrarily split into 2 studies, so samples 1-5 in 1 and 6-15 in another.
## Test when some measurements have assay_id's and some don't.
## Test when measurements with 2 different protocol sequences have the same assay_id.
## Test the same assay_id in 2 different studies.
## Test what happens when a measurement is done on a non-childless sample, for example 15_C1-20_Colon_allogenic_7days_170427_UKy_GCH_rep3

def initilization(input_json: dict, 
                           entity_table_name: str="entity", 
                           entity_type_key: str="type",
                           parent_key: str="parent_id",
                           protocol_key: str="protocol.id",
                           study_key: str="study.id",
                           entity_key: str="entity.id",
                           factor_table_name: str="factor",
                           factor_field_key: str="field",
                           factor_allowed_values_key: str="allowed_values",
                           protocol_table_name: str="protocol",
                           protocol_type_key: str="type",
                           measurement_table_name: str="measurement",
                           study_table_name: str="study") -> dict:
    """
    """
    
    ## Find parameter values to add processes for all protocols. Will be used later.    
    ## Need to add parameters to children from parents first.
    protocol_lineages, _ = _determine_lineages_and_sequences(input_json, protocol_table_name, parent_key)
    _propagate_ancestor_attributes(input_json, protocol_lineages, protocol_table_name)
    
    protocol_parameters = {}
    for protocol, attributes in input_json[protocol_table_name].items():
        parameters = []
        for field_name, field_value in attributes.items():
            if (match := re.match(r"(.*)%isa_fieldtype$", field_name)) and field_value == "parameter":
                parameter_name = match.group(1)
                ## TODO, should the field be {parameter_name}%ontology_annotation or {parameter_name}%isa_parametername ?
                if annotation_string := attributes.get(f"{parameter_name}%ontology_annotation"):
                    annotation_dict = _handle_ontology_parsing(annotation_string, 
                                                               f"{parameter_name}%ontology_annotation", 
                                                               "parameterNames", 
                                                               protocol_table_name, 
                                                               protocol)
                else:
                    annotation_dict = {"annotationValue": parameter_name}
                
                parameter_dict = {"category": {"@id": f"#parameter/{parameter_name}", "parameterName": annotation_dict},
                                  "value": attributes[parameter_name]}
                
                if (unit := attributes.get(f"{parameter_name}%unit")) or (unit := attributes.get(f"{parameter_name}%units")):
                    parameter_dict["unit"] = unit
                if (value := attributes.get(f"{parameter_name}%isa_unit")):
                    parsed_value = _handle_ontology_parsing(value, 
                                                            f"{parameter_name}%isa_unit", 
                                                            "parameterNames", 
                                                            protocol_table_name, 
                                                            protocol)
                    parameter_dict["unit"] = parsed_value
                
                parameters.append(parameter_dict)
        protocol_parameters[protocol] = parameters
    
    ## Studies and assays are both in the study table, so separate them.
    input_studies = {}
    input_assays = {}
    for study, attributes in input_json[study_table_name].items():
        if attributes.get("parent_id"):
            input_assays[study] = attributes
        else:
            input_studies[study] = attributes
    
    
    #############
    ## Studies
    #############
    sample_lineages, _ = _determine_lineages_and_sequences(input_json, entity_table_name, parent_key)
    _propagate_ancestor_attributes(input_json, sample_lineages, entity_table_name)
    
    all_ancestors = [ancestor for sample, sample_attributes in sample_lineages.items() for ancestor in sample_attributes["ancestors"]]
    childless_samples = [sample for sample in sample_lineages if sample not in all_ancestors]
    study_to_sample_map = {}
    sample_to_study_map = {}
    for sample in childless_samples:
        entity_studies = input_json[entity_table_name][sample][study_key]
        entity_studies = entity_studies if isinstance(entity_studies, list) else [entity_studies]
        entity_studies = [study for study in entity_studies if study in input_studies]
        sample_to_study_map[sample] = entity_studies
        for study in entity_studies:
            if study in study_to_sample_map:
                study_to_sample_map[study].append(sample)
            else:
                study_to_sample_map[study] = [sample]
            
            ## propogate studies to ancestors if not already there
            for ancestor in sample_lineages[sample]['ancestors']:
                if study_key in input_json[entity_table_name][ancestor]:  
                    ancestor_studies = input_json[entity_table_name][ancestor][study_key]
                    ancestor_studies = ancestor_studies if isinstance(ancestor_studies, list) else [ancestor_studies]
                    if study not in ancestor_studies:
                        ancestor_studies.append(study)
                        input_json[entity_table_name][ancestor][study_key] = ancestor_studies
                else:
                    input_json[entity_table_name][ancestor][study_key] = [study]
    
    samples_with_measurements = {}
    for measurement, attributes in input_json[measurement_table_name].items():
        measurement_sample = attributes[entity_key]
        measurement_protocols = attributes[protocol_key] if isinstance(attributes[protocol_key], list) else [attributes[protocol_key]]
        if measurement_sample in samples_with_measurements:
            samples_with_measurements[measurement_sample] = samples_with_measurements[measurement_sample].union(measurement_protocols)
        else:
            samples_with_measurements[measurement_sample] = set(measurement_protocols)
        
    
    ## Determine the ancestors to include in each sample chain and remove subsets.
    ## This isn't strictly necessary because processes that are subsets of each other will 
    ## be ignored when creating the Tab format.
    study_to_sample_chains = {}
    for study, samples in study_to_sample_map.items():
        study_to_sample_chains[study] = []
        for sample in samples:
            if sample in samples_with_measurements:
                ancestors = sample_lineages[sample]["ancestors"]
            else:
                ancestors = sample_lineages[sample]["ancestors"] + [sample]
            study_to_sample_chains[study].append(ancestors)
    
    study_to_sample_chains_subsets_removed = {}
    for study, sample_chains in study_to_sample_chains.items():
        study_to_sample_chains_subsets_removed[study] = []
        for sample_chain in sample_chains:
            set_sample_chain = set(sample_chain)
            if any([set_sample_chain.issubset(chain) for chain in study_to_sample_chains_subsets_removed[study]]) or\
               any([chain for chain in sample_chains if set_sample_chain < set(chain)]):
                continue
            study_to_sample_chains_subsets_removed[study].append(sample_chain)
    
    ## Studies with multiple assays will cause an issue when creating the process sequence, so shorten 
    ## the sample list down to only find unique sample chains in the study.
    unique_sample_chains_by_study = {}
    for study, sample_chains in study_to_sample_chains_subsets_removed.items():
        unique_sample_chains_by_study[study] = []
        for chain in sample_chains:
            psuedo_process = []
            
            for i, ancestor in enumerate(chain):
                protocols = input_json[entity_table_name][ancestor][protocol_key]
                if isinstance(protocols, str):
                    protocols = [protocols]
                
                isa_type = "source" if i == 0 else "sample"
                
                if "isa_type" not in input_json[entity_table_name][ancestor]:
                    input_json[entity_table_name][ancestor]["isa_type"] = isa_type
                
                psuedo_process.append({"name": ancestor,
                                       "protocols": protocols,
                                       "@id": f"#{isa_type}/{ancestor}"})
            
            unique_sample_chains_by_study[study].append(psuedo_process)
    
    
    ## Create a processSequence
    study_process_sequences = _create_process_sequences(unique_sample_chains_by_study)
    ## Add processes to studies in the input_json so they can be utilized by the conversion directives.
    for study, process_sequence in study_process_sequences.items():
        input_json[study_table_name][study]["process"] = process_sequence
    
    
    
    #############
    ## Assays
    #############
    measurement_lineages, measurement_sequences = _determine_lineages_and_sequences(input_json, measurement_table_name, parent_key)
    ordered_unique_measurement_sequences = _order_sequences(measurement_sequences, measurement_lineages)
    _propagate_ancestor_attributes(input_json, measurement_lineages, measurement_table_name)
    
    ## Find unique measurement_protocol_sequences.
    measurement_protocol_sequences = []
    measurement_protocol_sequence_to_entities = {}
    assays = {}
    for sequence in ordered_unique_measurement_sequences:
        protocol_sequence = []
        assay_id = None
        for measurement in sequence:
            protocol = input_json[measurement_table_name][measurement][protocol_key]
            ## It is assumed that all measurements in a lineage have the same entity.id.
            entity = input_json[measurement_table_name][measurement][entity_key]
            protocol_list = protocol if isinstance(protocol, list) else [protocol]
            
            for protocol_name in protocol_list:
                protocol_sequence.append(protocol_name)
                
            ## It is assumed that all measurements in a lineage have the same assay_id.
            if study_key in input_json[measurement_table_name][measurement]:
                measurment_studies = input_json[measurement_table_name][measurement][study_key]
                measurment_studies if isinstance(measurment_studies, list) else [measurment_studies]
                assay_ids = [study for study in measurment_studies if study in input_assays]
                if assay_ids:
                    assay_id = assay_ids[0]
            ## Old when assay_id was used instead of assays being a study.
            # if assay_key in input_json[measurement_table_name][measurement]:
            #     assay_id = input_json[measurement_table_name][measurement][assay_key]
        
        if protocol_sequence not in measurement_protocol_sequences:
            measurement_protocol_sequences.append(protocol_sequence)
        
        str_protocol_sequence = str(protocol_sequence)
        if not assay_id:
            assay_id = str_protocol_sequence
        if str_protocol_sequence not in measurement_protocol_sequence_to_entities:
            measurement_protocol_sequence_to_entities[str_protocol_sequence] = {"assay_ids": set([assay_id]),
                                                                                 "sequence": protocol_sequence, 
                                                                                 "entities": set([entity])
                                                                                 }
        else:
            measurement_protocol_sequence_to_entities[str_protocol_sequence]["entities"].add(entity)
            measurement_protocol_sequence_to_entities[str_protocol_sequence]["assay_ids"].add(assay_id)
        
        ## TODO should measurement entites only be in 1 study? 
        ## If they have multiple studies then this code will duplicate that row for each study-assay combination.
        entity_studies = input_json[entity_table_name][entity][study_key]
        entity_studies = entity_studies if isinstance(entity_studies, list) else [entity_studies]
        for study in entity_studies:
            unique_assay_id = f"{study}_{assay_id}"
            if unique_assay_id in assays:
                if entity in assays[unique_assay_id]["entities"]:
                    if protocol_sequence not in assays[unique_assay_id]["entities"][entity]:
                        assays[unique_assay_id]["entities"][entity].append(protocol_sequence)
                else:
                    assays[unique_assay_id]["entities"][entity] = [protocol_sequence]
                
                assays[unique_assay_id]["protocols"] = assays[unique_assay_id]["protocols"].union(protocol_sequence)
            else:
                assays[unique_assay_id] = {"entities": {entity:[protocol_sequence]}, 
                                           "protocols":set(),
                                           "study": study}
            
    
    ## Construct sample chains for assays.
    sample_chains_by_assay = {}
    for assay, attributes in assays.items():
        chain_list = []
        for sample, measurement_sequences in attributes["entities"].items():
            base_chain = []
            
            protocols = input_json[entity_table_name][sample][protocol_key]
            if isinstance(protocols, str):
                protocols = [protocols]
            
            if "isa_type" in input_json[entity_table_name][sample]:
                isa_type = input_json[entity_table_name][sample]["isa_type"]
            else:
                isa_type = "material"
                ## Add isa_type to sample.
                input_json[entity_table_name][sample]["isa_type"] = isa_type
            
            if isa_type == "material":
                ## TODO move this check to validate. If they mark as extract, but 
                ## it should be a sample, or doesn't have a measurement, should that 
                ## be an error? Should we check in validate?
                if not sample_lineages[sample]["ancestors"]:
                    message = (f"Error:  The entity, \"{sample}\", in the {entity_table_name} "
                               "indicates that it is a material ISA type in its \"isa_type\" "
                               "field, but it does not have any ancestors.")
                    print(message, file=sys.stderr)
                    sys.exit()
                
                base_chain.append({"name": sample_lineages[sample]["ancestors"][-1],
                                   "protocols": [],
                                   "@id": f"#sample/{sample_lineages[sample]['ancestors'][-1]}"})
                base_chain.append({"name": sample,
                                   "protocols": protocols,
                                   "@id": f"#material/{sample}"})
                
            else:
                base_chain.append({"name": sample,
                                   "protocols": protocols,
                                   "@id": f"#sample/{sample}"})
            
            
            for measurement_sequence in measurement_sequences:
                sample_chain = copy.deepcopy(base_chain)
                for measurement_protocol in measurement_sequence:
                    measurement_protocol_attributes = input_json[protocol_table_name][measurement_protocol]
                    ## Find data files and simply treat them like samples, so add to sample_chain.
                    if "data_files" in measurement_protocol_attributes and \
                       "data_files%entity_id" in measurement_protocol_attributes and \
                       sample in measurement_protocol_attributes["data_files%entity_id"]:
                           index = measurement_protocol_attributes["data_files%entity_id"].index(sample)
                           data_file = measurement_protocol_attributes["data_files"][index]
                           sample_chain.append({"name": data_file,
                                                "protocols": [measurement_protocol],
                                                "@id": f"#data/{data_file}"})
                    else:
                        sample_chain[-1]["protocols"].append(measurement_protocol)
            
                chain_list.append(sample_chain)
        sample_chains_by_assay[assay] = chain_list

    ## Create assay processSequences.
    assay_process_sequences = _create_process_sequences(sample_chains_by_assay)
    ## Add processes to assays in the input_json so they can be utilized by the conversion directives.
    for assay, process_sequence in assay_process_sequences.items():
        ## If the assay is not in the study table then add it.
        if assay not in input_json[study_table_name]:
            input_json[study_table_name][assay] = {"process": process_sequence,
                                                   "parent_id": assays[assay]["study"],
                                                   "type": "assay"}
            ## Add to input_assays for convenience.
            input_assays[assay] = input_json[study_table_name][assay]
        else:
            input_json[study_table_name][assay]["process"] = process_sequence
    
    
    
    #############
    ## If there is not a filename field in the study/assay, then add one.
    #############
    for study, attributes in input_json[study_table_name].items():
        if study in input_studies:
            if "filename" not in attributes:
                attributes["filename"] = f"s_{study}.txt"
            elif not re.match(r"s_.*", attributes["filename"]):
                attributes["filename"] = "s_" + attributes["filename"]
        else:
            if "filename" not in attributes:
                attributes["filename"] = f"a_{study}.txt"
            elif not re.match(r"a_.*", attributes["filename"]):
                attributes["filename"] = "a_" + attributes["filename"]
            
    
    
    ###########
    ## Add study.id to entities and protocols.
    ###########
    ## Add study to most protocols by looping over entities and copying the entities studies to its protocols.
    for entity, attributes in input_json[entity_table_name].items():
        entity_studies = attributes[study_key]
        entity_studies = entity_studies if isinstance(entity_studies, list) else [entity_studies]
        entity_protocols = attributes[protocol_key]
        entity_protocols = entity_protocols if isinstance(entity_protocols, list) else [entity_protocols]
        for protocol in entity_protocols:
            protocol_attributes = input_json[protocol_table_name][protocol]
            if study_key in protocol_attributes:
                protocol_studies = protocol_attributes[study_key]
                protocol_studies = protocol_studies if isinstance(protocol_studies, list) else [protocol_studies]
            else:
                protocol_studies = []
            for study in entity_studies:
                if study not in protocol_studies:
                    protocol_studies.append(study)
            input_json[protocol_table_name][protocol][study_key] = protocol_studies

    
    
    ## This could be moved into the loop that creates the sample_chains_by_assay if speed is needed.
    for assay, attributes in assays.items():
        study = attributes["study"]
        for entity, measurement_sequences in attributes["entities"].items():
            entity_studies = input_json[entity_table_name][entity][study_key]
            entity_studies = entity_studies if isinstance(entity_studies, list) else [entity_studies]
            if assay not in entity_studies:
                entity_studies.append(assay)
                input_json[entity_table_name][entity][study_key] = entity_studies
            
        for protocol in attributes["protocols"]:
            protocol_attributes = input_json[protocol_table_name][protocol]
            if study_key in protocol_attributes:
                protocol_studies = protocol_attributes[study_key]
                protocol_studies = protocol_studies if isinstance(protocol_studies, list) else [protocol_studies]
                if assay not in protocol_studies:
                    protocol_attributes[study_key] = protocol_studies + [assay]
            else:
                protocol_attributes[study_key] = [assay]
            
            ## Add study to measurement protocols since they didn't get added previously when looping over entities.
            if study not in protocol_studies:
                protocol_studies.append(study)
            
            input_json[protocol_table_name][protocol][study_key] = protocol_studies
    
    
    ##############
    ## Add attributes to factor fields in entities so they are picked up by conversion directives
    ##############
    ## TODO add a note in the documentation that units for a factor should be on the entity. Or at least that's where they will be picked up from.
    categories_to_studies = {}
    ## Used to track the different units across parameters, factors, and characteristics.
    units_to_studies = {}
    factor_field_to_id = {attributes["field"]: f"#factor/{factor}" for factor, attributes in input_json[factor_table_name].items()}
    for entity, attributes in input_json[entity_table_name].items():
        ## All entities should have study.id's after propagation.
        entity_studies = attributes[study_key] if isinstance(attributes[study_key], list) else [attributes[study_key]]
        ## categorize characteristics by study and assay.
        for field_name, field_value in attributes:
            if (match := re.match(r"(.*)%isa_fieldtype$", field_name)) and field_value == "characteristic":
                characteristic = match.group(1)
                
                category_dict = {"@id": f"#characteristic/{characteristic}",
                                 "characteristicType": {"annotationValue": characteristic}}
                ## TODO think about whether this is a good idea, it would be better if the categories were in 1 place, but
                ## this has the potential to have the same category with 2 different types.
                if (value := attributes.get(f"{characteristic}%isa_characteristictype")):
                    category_dict["characteristicType"] = _handle_ontology_parsing(value, 
                                                                                   f"{characteristic}%isa_characteristictype", 
                                                                                   "category", 
                                                                                   entity_table_name, 
                                                                                   entity)
                
                ## Look for a unit field to add to unitCategories.
                unit_category = None
                if (value := attributes.get(f"{characteristic}%isa_unit")):
                    parsed_value = _handle_ontology_parsing(value, 
                                                            f"{characteristic}%isa_unit", 
                                                            "unitCategory", 
                                                            entity_table_name, 
                                                            entity)
                    unit_category = parsed_value
                elif (unit := attributes.get(f"{characteristic}%unit")) or (unit := attributes.get(f"{characteristic}%units")):
                    unit_category = {"annotationValue": unit}
                
                ## Not sure I need this, I just add to study directly below.
                # if unit_category:
                #     str_unit = str(unit_category)
                #     if str_unit in units_to_studies:
                #         units_to_studies[str_unit]["studies"] = units_to_studies[str_unit]["studies"].union(entity_studies)
                #     else:
                #         units_to_studies[str_unit] = {"unit": unit_category,
                #                                       "studies": set(entity_studies)}
                
                
                for study in entity_studies:
                    if unit_category:
                        if "unit_categories" in input_json[study_table_name][study]:
                            if unit_category not in input_json[study_table_name][study]["unit_categories"]:
                                input_json[study_table_name][study]["unit_categories"].append(unit_category)
                        else:
                            input_json[study_table_name][study]["unit_categories"] = [unit_category]
                    
                    ## I changed this to check that the category_dict is in the list instead.
                    # if characteristic in categories_to_studies:
                    #     if study in categories_to_studies[characteristic]:
                    #         continue
                    #     categories_to_studies[characteristic].add(study)
                    # else:
                    #     categories_to_studies[characteristic] = {study}
                    
                    if "characteristic_categories" in input_json[study_table_name][study]:
                        if category_dict not in input_json[study_table_name][study]["characteristic_categories"]:
                            input_json[study_table_name][study]["characteristic_categories"].append(category_dict)
                    else:
                        input_json[study_table_name][study]["characteristic_categories"] = [category_dict]
                    
                    
        ## Add attributes to factors.
        for factor, factor_id in factor_field_to_id.items():
            if factor in attributes and f"{factor}%isa_factorvalue" not in attributes:
                factor_value_dict = {"value": {"annotationValue": attributes[factor]}, 
                                     "category": {"@id": factor_id}}
                
                if (value := attributes.get(f"{factor}%isa_value")):
                    parsed_value = _handle_ontology_parsing(value, f"{factor}%isa_value", "factorValues", entity_table_name, entity)
                    factor_value_dict["value"] = parsed_value
                
                if (unit := attributes.get(f"{factor}%unit")) or (unit := attributes.get(f"{factor}%units")):
                    factor_value_dict["unit"] = {"annotationValue": unit}
                if (value := attributes.get(f"{factor}%isa_unit")):
                    parsed_value = _handle_ontology_parsing(value, f"{factor}%isa_unit", "factorValues", entity_table_name, entity)
                    factor_value_dict["unit"] = parsed_value
                    
                input_json[entity_table_name][entity][f"{factor}%isa_factorvalue"] = factor_value_dict
                
                for study in entity_studies:
                    if unit_category := factor_value_dict.get("unit"):
                        if "unit_categories" in input_json[study_table_name][study]:
                            if unit_category not in input_json[study_table_name][study]["unit_categories"]:
                                input_json[study_table_name][study]["unit_categories"].append(unit_category)
                        else:
                            input_json[study_table_name][study]["unit_categories"] = [unit_category]


    ## Go through protocol parameters and add parameter units to studies.
    ## Studies should have been propagated to protocols in above code.
    for protocol, parameters in protocol_parameters.items():
        protocol_studies = protocol_attributes[study_key]
        protocol_studies = protocol_studies if isinstance(protocol_studies, list) else [protocol_studies]
        for parameter in parameters:
            if unit_category := parameter.get("unit"):
                for study in protocol_studies:
                    if "unit_categories" in input_json[study_table_name][study]:
                        if unit_category not in input_json[study_table_name][study]["unit_categories"]:
                            input_json[study_table_name][study]["unit_categories"].append(unit_category)
                    else:
                        input_json[study_table_name][study]["unit_categories"] = [unit_category]


    ################
    ## Get measurementType, technologyPlatform, technologyType, and dataFiles for assays
    ################
    for assay, attributes in assays.items():
        for protocol in attributes["protocols"]:
            protocol_attributes = input_json[protocol_table_name]
            for field_name, field_value in protocol_attributes.items():
                ## technologyPlatform
                technology_platform = None
                if (match := re.match(r"(.*)%isa_fieldtype$", field_name)) and field_value == "technologyplatform":
                    technology_platform = protocol_attributes[match.group(1)]
                                
                ## technologyType
                technology_type_dict = None
                if (match := re.match(r"(.*)%isa_fieldtype$", field_name)) and field_value == "technologytype":
                    technology_type = match.group(1)
                    
                    technology_type_dict = {"ontologyAnnotation": {"annotationValue": protocol_attributes[technology_type]}}
                    
                    if (value := protocol_attributes.get(f"{technology_type}%isa_ontologyannotation")):
                        parsed_value = _handle_ontology_parsing(value, 
                                                                f"{technology_type}%isa_ontologyannotation", 
                                                                "technologyType", 
                                                                protocol_table_name, 
                                                                protocol)
                        technology_type_dict["ontologyAnnotation"] = parsed_value
                
                ## measurementType
                measurement_type = None
                if (match := re.match(r"(.*)%isa_fieldtype$", field_name)) and field_value == "measurementtype":
                    measurement_type = match.group(1)
                    
                    measurement_type_dict = {"annotationValue": protocol_attributes[measurement_type]}
                    
                    if (value := protocol_attributes.get(f"{measurement_type}%isa_ontologyannotation")):
                        parsed_value = _handle_ontology_parsing(value, 
                                                                f"{measurement_type}%isa_ontologyannotation", 
                                                                "measurementType", 
                                                                protocol_table_name, 
                                                                protocol)
                        measurement_type_dict = parsed_value
                
                ## dataFiles
                data_files = None
                if field_name == "data_files" and field_value:
                    data_files_list = field_value.copy()
                    data_files = []
                    for data_file in data_files_list:
                        data_file_dict = {"@id": f"#data/{data_file}",
                                          "name": data_file}
                        data_files.append(data_file_dict)
                    
                    if data_types := protocol_attributes.get("data_files%isa_type"):
                        for i, data_type in data_types:
                            data_files[i]["type"] = data_type
                        
                        
                        
            assay_attributes = input_json[study_table_name][assay]
            if "technology_platform" not in assay_attributes:
                if technology_platform:
                    assay_attributes["technology_platform"] = technology_platform
            
            if "technology_type" not in assay_attributes:
                if technology_type_dict:
                    assay_attributes["technology_type"] = technology_type_dict
            
            if "measurement_type" not in assay_attributes:
                if measurement_type_dict:
                    assay_attributes["measurement_type"] = measurement_type_dict
            
            if "data_files" not in assay_attributes:
                if data_files:
                    assay_attributes["data_files"] = data_files
                    
    return input_json
    
    
    







def _create_process_sequences(unique_sample_chains_by_identifier: dict, protocol_parameters: dict):
    """
    """
    
    process_sequences = {}
    for identifier, sample_chains in unique_sample_chains_by_identifier.items():
        process_sequence = []
        protocol_uses = {}
        sequence_by_protocol = {}
        for sample_chain in sample_chains:
            temp_sequence = []
            for i in range(len(sample_chain)-1):
                pair = sample_chain[i:i+2]
                
                if i == 0:
                    protocol_chain = pair[0]["protocols"] + pair[1]["protocols"]
                else:
                    protocol_chain = pair[1]["protocols"]
            
                create_new_sequence = True
                if str(protocol_chain) in sequence_by_protocol:
                    ## If the same input sample appears for the same protocol sequence then that means it produced 
                    ## multiple samples as output, so add the new output to the already created process.
                    for k, input_samples in enumerate(sequence_by_protocol[str(protocol_chain)]["input_samples"]):
                        if pair[0] in input_samples:
                            output_dict = {"@id": pair[1]["@id"]}
                            sequence_by_protocol[str(protocol_chain)]["last_processes"][k]["outputs"].append(output_dict)
                            sequence_by_protocol[str(protocol_chain)]["output_samples"][k].append([pair[1]["name"]])
                            create_new_sequence = False
                            break
                    
                    ## If the same output sample appears for the same protocol sequence then that means multiple 
                    ## samples were used as input, so add the new input to the already created process.
                    for k, output_samples in enumerate(sequence_by_protocol[str(protocol_chain)]["output_samples"]):
                        if pair[1] in output_samples:
                            input_dict = {"@id": pair[0]["@id"]}
                            sequence_by_protocol[str(protocol_chain)]["first_processes"][k]["inputs"].append(input_dict)
                            sequence_by_protocol[str(protocol_chain)]["input_samples"][k].append([pair[0]["name"]])
                            create_new_sequence = False
                            break
                
                if create_new_sequence:
                    for j, protocol in enumerate(protocol_chain):
                        if protocol in protocol_uses:
                            protocol_uses[protocol] += 1
                        else:
                            protocol_uses[protocol] = 1
                        
                        process = {"@id": f"#process/{protocol}_{protocol_uses[protocol]}",
                                   "executesProtocol":protocol,
                                   "parameterValues": protocol_parameters[protocol]}
                        
                        if j == 0:
                            process["inputs"] = [{"@id": pair[0]["@id"]}]
                            first_process = process
                        if j == len(protocol_chain)-1:
                            process["outputs"] = [{"@id": pair[1]["@id"]}]
                            last_process = process
                        
                        temp_sequence.append(process)
                
                if str(protocol_chain) not in sequence_by_protocol:
                    sequence_by_protocol[str(protocol_chain)] = {"first_processes":[first_process], 
                                                                 "last_processes":[last_process],
                                                                 "input_samples":[[pair[0]["name"]]],
                                                                 "output_samples":[[pair[1]["name"]]]}
                else:
                    sequence_by_protocol[str(protocol_chain)]["first_processes"].append(first_process)
                    sequence_by_protocol[str(protocol_chain)]["last_processes"].append(last_process)
                    sequence_by_protocol[str(protocol_chain)]["input_samples"].append([pair[0]["name"]])
                    sequence_by_protocol[str(protocol_chain)]["output_samples"].append([pair[1]["name"]])
                
                    
            ## Add nextProcess and previousProcess to all processes.
            for i, process in enumerate(temp_sequence):
                if i < len(temp_sequence)-1:
                    process["nextProcess"] = temp_sequence[i+1]["@id"]
                if i > 0:
                    process["previousProcess"] = temp_sequence[i-1]["@id"]
            
            process_sequence += temp_sequence
        process_sequences[identifier] = process_sequence
    return process_sequences







def _determine_lineages_and_sequences(input_json: dict, table_name: str, parent_key: str):
    """Determine lineages and unique sequences for a given table.
    """
    
    sequences = []
    lineages = {}
    for entity_name, entity_attributes in input_json[table_name].items():
        sequence = set()
        sequence.add(entity_name)
        ancestors = []
        while parent_name := entity_attributes.get(parent_key):
            sequence.add(parent_name)
            ancestors.append(parent_name)
            if parent_name not in input_json[table_name]:
                print(f"Error: The parent {table_name}, \"" + parent_name + f"\", pulled from the {table_name} \"" + entity_name + \
                      "\" in the \"" + table_name + "\" table is not in the \"" + table_name + "\" table. " +\
                      "Parents must be in the table with thier children.", file=sys.stderr)
                sys.exit()
            entity_attributes = input_json[table_name][parent_name]
        sequences.append(sequence)
        ancestors.reverse()
        lineages[entity_name] = {"ancestors":ancestors}
    
    ## Add children to lineages. Direct children only, grandchildren aren't included.
    for sample, sample_attributes in lineages.items():
        sample_attributes["children"] = []
        for sample2, sample2_attributes in lineages.items():
            if sample2_attributes["ancestors"] and sample == sample2_attributes["ancestors"][-1]:
                sample_attributes["children"].append(sample2)
    
    unique_sequences = [list(sequence) for sequence in sequences if \
                        not any([sequence.issubset(sequence2) for sequence2 in sequences if sequence2 != sequence])]
    
    return lineages, unique_sequences



def _order_sequences(unique_sequences: list, lineages: dict):
    """Put sequences in proper lineage order.
    """
    
    new_sequences = []
    for sequence in unique_sequences:
        ancestor_lens = []
        for sample in sequence:
            ancestor_lens.append(len(lineages[sample]["ancestors"]))
        end_sample = sequence[ancestor_lens.index(max(ancestor_lens))]
        
        proper_sequence = lineages[end_sample]["ancestors"] + [end_sample]
        
        new_sequences.append(proper_sequence)
        
    return new_sequences



def _propagate_ancestor_attributes(input_json: dict, lineages: dict, table_name: str):
    """Propagate ancestor attributes to children.
    
    Start from the first ancestor and loop over it's children updating the attributes 
    for each child.
    """
    
    for entity, family in lineages.items():
        if ancestors := family["ancestors"]:
            originator_attributes = copy.deepcopy(ancestors[0])
            for ancestor in ancestors[1:]:
                originator_attributes.update(input_json[table_name][ancestor])
            originator_attributes.update(input_json[table_name][entity])
            input_json[table_name][entity] = originator_attributes
    
    return input_json
            



## TODO, figure out the best way to pass silent argument into here.
def _handle_ontology_parsing(value: str|list[str], field_name: str, category: str, table_name: str, entry_name: str):
    """
    """
    
    built_in_message, parsed_value = built_ins.dumb_parse_ontology_annotation(value)
    if built_in_message:
        message = (f"When creating the {category} for the entry, \"{entry_name}\", in the "
                   f"\"{table_name}\" table there was an error parsing the field, "
                   f"\"{field_name}\", into an ontology annotation:\n")
        message += built_in_message
        print(message, file=sys.stderr)
        sys.exit()
    
    return parsed_value







# def determine_studies_and_assays_old(input_json: dict, 
#                            entity_table_name: str="entity", 
#                            entity_type_key: str="type",
#                            parent_key: str="parent_id",
#                            protocol_key: str="protocol.id",
#                            study_key: str="study.id",
#                            entity_key: str="entity.id",
#                            factor_table_name: str="factor",
#                            factor_field_key: str="field",
#                            factor_allowed_values_key: str="allowed_values",
#                            protocol_table_name: str="protocol",
#                            protocol_type_key: str="type",
#                            measurement_table_name: str="measurement",
#                            study_table_name: str="study") -> dict:
#     """
#     """
        
#     sample_lineages, unique_sequences = _determine_lineages_and_sequences(input_json, entity_table_name, parent_key)
#     ordered_unique_sample_sequences = _order_sequences(unique_sequences, sample_lineages)
    
#     ## If protocols are a factor, they should be treated as 1 when looking for unique 
#     ## sequences to determine studies and assays.
#     factor_protocol_sets = []
#     for factor_values in input_json[factor_table_name].values():
#         if factor_values[factor_field_key] == protocol_key:
#             factor_protocol_sets.append(factor_values[factor_allowed_values_key])
    
    
#     measurement_lineages, measurement_sequences = _determine_lineages_and_sequences(input_json, measurement_table_name, parent_key)
#     ordered_unique_measurement_sequences = _order_sequences(measurement_sequences, measurement_lineages)
    
#     ## Find unique measurement_protocol_sequences.
#     measurement_protocol_sequences = []
#     measurement_protocol_sequence_to_entities = {}
#     for sequence in ordered_unique_measurement_sequences:
#         protocol_sequence = []
#         entities = set()
#         for measurement in sequence:
#             protocol = input_json[measurement_table_name][measurement][protocol_key]
#             entities.add(input_json[measurement_table_name][measurement][entity_key])
#             protocol_list = protocol if isinstance(protocol, list) else [protocol]
            
#             for protocol_name in protocol_list:
#                 for i, factor_protocols in enumerate(factor_protocol_sets):
#                     if protocol_name in factor_protocols:
#                         protocol_name = f"factor_protocol_{i}"
#                 protocol_sequence.append(protocol_name)
        
#         if protocol_sequence not in measurement_protocol_sequences:
#             measurement_protocol_sequences.append(protocol_sequence)
        
#         if str(protocol_sequence) not in measurement_protocol_sequence_to_entities:
#             measurement_protocol_sequence_to_entities[str(protocol_sequence)] = {"sequence": protocol_sequence, "entities": entities}
#         else:
#             measurement_protocol_sequence_to_entities[str(protocol_sequence)]["entities"] = measurement_protocol_sequence_to_entities[str(protocol_sequence)]["entities"].union(entities)
    
#     measurement_entity_protocol_map = {}
#     for key, attributes in measurement_protocol_sequence_to_entities.items():
#         for sample in attributes["entities"]:
#             if sample in measurement_entity_protocol_map:
#                 measurement_entity_protocol_map[sample][key] = attributes["sequence"]
#             else:
#                 measurement_entity_protocol_map[sample] = {key: attributes["sequence"]}
    
    
    
#     protocol_sequences = []
#     childless_samples_to_protocol_sequences = {}
#     protocol_sequence_attributes = {}
#     for sequence in ordered_unique_sample_sequences:
#         end_sample = sequence[-1]
        
#         protocol_sequence = []
#         for sample in sequence:
#             protocol = input_json[entity_table_name][sample][protocol_key]
#             protocol_list = protocol if isinstance(protocol, list) else [protocol]
            
#             for protocol_name in protocol_list:
#                 for i, factor_protocols in enumerate(factor_protocol_sets):
#                     if protocol_name in factor_protocols:
#                         protocol_name = f"factor_protocol_{i}"
#                 protocol_sequence.append(protocol_name)
        
#         if sequences_dict := measurement_entity_protocol_map.get(sample):
#             for protocol_names in sequences_dict.values():
#                 protocol_sequence_copy = protocol_sequence.copy()
#                 protocol_sequence_copy += protocol_names
                
#                 if protocol_sequence_copy not in protocol_sequences:
#                     protocol_sequences.append(protocol_sequence_copy)
                
#                 if str(protocol_sequence_copy) in protocol_sequence_attributes:
#                     protocol_sequence_attributes[str(protocol_sequence_copy)]["samples"].append(end_sample)
#                 else:
#                     protocol_sequence_attributes[str(protocol_sequence_copy)] = {"samples" : [end_sample]}
                
#                 if end_sample in childless_samples_to_protocol_sequences:
#                     childless_samples_to_protocol_sequences[end_sample].add(str(protocol_sequence_copy))
#                 else:
#                     childless_samples_to_protocol_sequences[end_sample] = set([str(protocol_sequence_copy)])
#         else:
#             if protocol_sequence not in protocol_sequences:
#                 protocol_sequences.append(protocol_sequence)
            
#             if str(protocol_sequence) in protocol_sequence_attributes:
#                 protocol_sequence_attributes[str(protocol_sequence)]["samples"].append(end_sample)
#             else:
#                 protocol_sequence_attributes[str(protocol_sequence)] = {"samples" : [end_sample]}
            
#             if end_sample in childless_samples_to_protocol_sequences:
#                 childless_samples_to_protocol_sequences[end_sample].add(str(protocol_sequence))
#             else:
#                 childless_samples_to_protocol_sequences[end_sample] = set([str(protocol_sequence)])
#     childless_samples_to_protocol_sequences = {key:list(value) for key, value in childless_samples_to_protocol_sequences.items()}
    
#     ## For each protocol sequence work backwards and find the first collection protocol 
#     ## to find where the study should end and assay begin. Might need to change this 
#     ## to look for a common study sequence of protocols at the beginning of each 
#     ## full sequence and make that the study. tissue_quench and frozen_tissue_grind 
#     ## feel like they should be in the study since they are common to both the polar and 
#     ## protein extractions.
#     # unique_truncated_protocol_sequences = []
#     # for protocol_sequence in protocol_sequences:
#     #     reverse_sequence = protocol_sequence.copy()
#     #     reverse_sequence.reverse()
#     #     for protocol in reverse_sequence:
#     #         ## Factor protocols were previously replaced and won't be in the input_json.
#     #         ## They should only ever be treatments, so this shouldn't ever be triggered, 
#     #         ## but I am leaving it just in case.
#     #         if "factor_protocol" in protocol:
#     #             continue
#     #         if input_json[protocol_table_name][protocol][protocol_type_key] == "collection":
#     #             new_sequence = reverse_sequence[reverse_sequence.index(protocol):]
#     #             new_sequence.reverse()
#     #             if new_sequence not in unique_truncated_protocol_sequences:
#     #                 unique_truncated_protocol_sequences.append(new_sequence)
#     #             break
            
#     ## Instead of looking for "collection" protocol just look for matching subsets.
#     longest_matching_subsequences = []
#     for protocol_sequence in protocol_sequences:
#         subsequences = [[]] * len(protocol_sequences)
#         for i in range(len(protocol_sequence)+1):
#             for sequence_index, sequence in enumerate(protocol_sequences):
#                 if len(sequence) >= i and sequence[0:i] == protocol_sequence[0:i]:
#                     subsequences[sequence_index] = sequence[0:i]
#         longest_matching_subsequences.append(subsequences)
        
#     unique_matching_subsequences = []
#     for i, subsequences in enumerate(longest_matching_subsequences):
#         for j, sequence in enumerate(subsequences):
#             if i == j:
#                 continue
#             if sequence not in unique_matching_subsequences:
#                 unique_matching_subsequences.append(sequence)
    
#     ## Get the number of study IDs on the subjects. If there are too few then that is an error.
#     all_ancestors = [ancestor for sample, sample_attributes in sample_lineages.items() for ancestor in sample_attributes["ancestors"]]
#     childless_samples = [sample for sample in sample_lineages if sample not in all_ancestors]
#     studies = {}
#     for sample in childless_samples:
#         study = input_json[entity_table_name][sample][study_key]
#         protocol_sequences = childless_samples_to_protocol_sequences[sample]
#         for protocol_sequence in protocol_sequences:
#             attributes = protocol_sequence_attributes[protocol_sequence]
            
#             if study in studies:
#                 studies[study]["samples"].append(sample)
#                 if protocol_sequence not in studies[study]["sequences"]:
#                     studies[study]["sequences"].append(protocol_sequence)
#             else:
#                 studies[study] = {"samples": [sample], "sequences": [protocol_sequence]}
            
#             if "study" not in attributes:
#                 protocol_sequence_attributes[protocol_sequence]["study"] = [study]
#             elif study not in attributes["study"]:
#                 protocol_sequence_attributes[protocol_sequence]["study"].append(study)
        
    
#     if (num_of_studies := len(studies)) < (num_of_unique_seq := len(unique_matching_subsequences)):
#         message = ("Error:  Based on the number of unique protocol sequences it was determined that "
#                    f"there should be at least {num_of_unique_seq} studies, but only {num_of_studies} "
#                    "were found in the study IDs on the samples.")
#         print(message, file=sys.stderr)
#         sys.exit()
    
#     ## Studies with multiple assays will cause an issue when creating the process sequence, so shorten 
#     ## the sample list down to only find unique sample chains in the study.
#     unique_sample_chains_by_study = {}
#     for study, attributes in studies.items():
#         samples = attributes["samples"]
#         unique_sample_chains_by_study[study] = []
#         for sample in samples:
#             sample_chain = []
#             ancestors = sample_lineages[sample]["ancestors"]
            
#             for i, ancestor in enumerate(ancestors):
#                 protocols = input_json[entity_table_name][ancestor][protocol_key]
#                 if isinstance(protocols, str):
#                     protocols = [protocols]
                
#                 id_prefix = "#source/" if i == 0 else "#sample/"
                
#                 sample_chain.append({"name": ancestor,
#                                      "protocols": protocols,
#                                      "@id": f"{id_prefix}{ancestor}"})
            
#             unique_sample_chains_by_study[study].append(sample_chain)
    
#     ## Create a processSequence
#     study_process_sequences = _create_process_sequences(unique_sample_chains_by_study)
#     ## Add processes to studies in the input_json so they can be utilized by the conversion directives.
#     for study, process_sequence in study_process_sequences.items():
#         input_json[study_table_name][study]["process"] = process_sequence
    
    
    
    
#     #####################
#     ## Determine assays.
#     #####################
#     assays = {}
#     for study, attributes in studies.items():
#         sequence_to_assay_map = {}
#         for i, sequence in enumerate(attributes["sequences"]):
#             sequence_to_assay_map[sequence] = f"_assay_{i}"
        
#         for sample in attributes["samples"]:
#             for protocol_sequence in childless_samples_to_protocol_sequences[sample]:
#                 assay_id = input_json[entity_table_name][sample][study_key] + \
#                     sequence_to_assay_map[protocol_sequence]
#                 if assay_id in assays:
#                     assays[assay_id].append(sample)
#                 else:
#                     assays[assay_id] = [sample]
    
    
#     ## Construct sample chains for assays.
#     sample_chains_by_assay = {}
#     for assay, samples in assays.items():
#         chain_list = []
#         for sample in samples:
#             sample_chain = []
#             sample_chain.append({"name": sample_lineages[sample]["ancestors"][-1],
#                                  "protocols": [],
#                                  "@id": f"#sample/{sample_lineages[sample]['ancestors'][-1]}"})
#             protocols = input_json[entity_table_name][sample][protocol_key]
#             if isinstance(protocols, str):
#                 protocols = [protocols]
#             sample_chain.append({"name": sample,
#                                  "protocols": protocols,
#                                  "@id": f"#material/{sample}"})
            
#             ## Find data files and simply treat them like samples, so add to sample_chain.
#             if measurement_protocols := measurement_entity_protocol_map.get(sample):
#                 ## measurement_protocols is a list of lists. Each nested list are the protocols 
#                 ## that were found on a measurement that had the sample as the entity.id.
#                 for protocol_list in measurement_protocols:
#                     for measurement_protocol in protocol_list:
#                         measurement_protocol_attributes = input_json[protocol_table_name][measurement_protocol]
#                         if "data_files" in measurement_protocol_attributes and \
#                            "data_files%entity_id" in measurement_protocol_attributes and \
#                            sample in measurement_protocol_attributes["data_files%entity_id"]:
#                                index = measurement_protocol_attributes["data_files%entity_id"].index(sample)
#                                data_file = measurement_protocol_attributes["data_files"][index]
#                                sample_chain.append({"name": data_file,
#                                                     "protocols": [measurement_protocol],
#                                                     "@id": f"#data/{data_file}"})
#                         else:
#                             sample_chain[-1]["protocols"].append(measurement_protocol)
#             chain_list.append(sample_chain)
#         sample_chains_by_assay[assay] = chain_list

#     ## Create assay processSequences.
#     assay_process_sequences = _create_process_sequences(sample_chains_by_assay)
#     ## Add assay table to input_json.
#     input_json["assay"] = {}
#     ## Add processes to assays in the input_json so they can be utilized by the conversion directives.
#     for assay, process_sequence in assay_process_sequences.items():
#         input_json["assay"][assay] = {"process": process_sequence}
    
    
    
#     ###########
#     ## Add study.id and assay.id to entities and protocols.
#     ###########
    
    
    
    
    
#     # matching_subsequence = []
#     # for subsequence in unique_matching_subsequences:
#     #     if len(subsequence) != len(protocol_chain):
#     #         continue
#     #     subsequence_matches = True
#     #     for i, protocol in enumerate(subsequence):
#     #         if re_match := re.match(r"factor_protocol_(\d+)", protocol):
#     #             if protocol_chain[i] not in factor_protocol_sets[int(re_match.groups(1)[0])]:
#     #                 subsequence_matches = False
#     #                 break
#     #         elif protocol != protocol_chain[i]:
#     #             subsequence_matches = False
#     #     if subsequence_matches:
#     #         matching_subsequence = subsequence.copy()
#     #         break


