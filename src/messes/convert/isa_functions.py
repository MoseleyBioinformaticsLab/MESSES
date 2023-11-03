# -*- coding: utf-8 -*-
"""
Functions For ISA Format
------------------------
"""

import sys
import copy

from messes.convert import built_ins

## TODO if study.id and assay id are on records don't overwrite.
## Add messaging to indicate when study and assay ids are generated.
## Require samples at end of lineage to have study.id so we can connect to studies in the table.
## Add a step after study identification. If user gives 3 studies and we detect only 1, then 
## that means to break the study into 3, this isn't an error, just make 3.
## After iddentifying studies and assays using the collection protocol, look for 
## matching protocols after the collection protocol and include them in the study. 
## In other words put protocols common to assays in the study.

## TODO check that if you have multiple measurements in the measurement table for the same entity that things work as expected.
## Make sure that data_files are found and handled correctly for multiple measurements. Test multiple measurements in the table, as well 
## as mulitple protocol.id's on the same measurement.
## Test what happens if study.id on a childless sample is wrong, for example a icms sample marked as in the nmr study.
## Test what happens if icms samples are arbitrarily split into 2 studies, so samples 1-5 in 1 and 6-15 in another.
## Test when some measurements have assay_id's and some don't.
## Test when measurements with 2 different protocol sequences have the same assay_id.
## Test the same assay_id in 2 different studies.

def determine_studies_and_assays(input_json: dict, 
                           entity_table_name: str="entity", 
                           entity_type_key: str="type",
                           parent_key: str="parent_id",
                           protocol_key: str="protocol.id",
                           study_key: str="study.id",
                           assay_key: str="assay_id",
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
    ## Let's assume that childless samples with a measurement need an assay, and those without a measurement don't.
    
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
                if annotation_string := attributes.get(f"{parameter_name}%ontology_annotation"):
                    annotation_dict = built_ins.dumb_parse_ontology_annotation(annotation_string)
                else:
                    annotation_dict = {"annotationValue": parameter_name}
                
                parameter_dict = {"category": {"@id": f"#parameter/{parameter_name}", "parameterName": annotation_dict},
                                  "value": attributes[parameter_name]}
                
                if unit := attributes.get(f"{parameter_name}%unit"):
                    parameter_dict["unit"] = unit
                elif unit := attributes.get(f"{parameter_name}%units"):
                    parameter_dict["unit"] = unit
                
                parameters.append(parameter_dict)
        protocol_parameters[protocol] = parameters
    
    
    
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
        ## If a measurement is done on a non-childless sample how do we handle it?
        ## In ISA I think you would have to create an assay for the data files. Only assays have data files.
        ## Should the existence of a measurement force an assay?
        ## I think yes. The sample can still do on to be part of another study. Maybe only create assay if there is a data file?
        if measurement_sample in samples_with_measurements:
            samples_with_measurements[measurement_sample] = samples_with_measurements[measurement_sample].union(measurement_protocols)
        else:
            samples_with_measurements[measurement_sample] = set(measurement_protocols)
        
    
    ## Studies with multiple assays will cause an issue when creating the process sequence, so shorten 
    ## the sample list down to only find unique sample chains in the study.
    unique_sample_chains_by_study = {}
    for study, samples in study_to_sample_map.items():
        unique_sample_chains_by_study[study] = []
        for sample in samples:
            sample_chain = []
            if sample in samples_with_measurements:
                ancestors = sample_lineages[sample]["ancestors"]
            else:
                ancestors = sample_lineages[sample]["ancestors"] + [sample]
            
            for i, ancestor in enumerate(ancestors):
                protocols = input_json[entity_table_name][ancestor][protocol_key]
                if isinstance(protocols, str):
                    protocols = [protocols]
                
                id_prefix = "#source/" if i == 0 else "#sample/"
                
                sample_chain.append({"name": ancestor,
                                     "protocols": protocols,
                                     "@id": f"{id_prefix}{ancestor}"})
            
            unique_sample_chains_by_study[study].append(sample_chain)
    
    
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
            if assay_key in input_json[measurement_table_name][measurement]:
                assay_id = input_json[measurement_table_name][measurement][assay_key]
        
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
    for assay, attribtues in assays.items():
        chain_list = []
        for sample, measurement_sequences in attributes["entities"].items():
            base_chain = []
            base_chain.append({"name": sample_lineages[sample]["ancestors"][-1],
                                 "protocols": [],
                                 "@id": f"#sample/{sample_lineages[sample]['ancestors'][-1]}"})
            protocols = input_json[entity_table_name][sample][protocol_key]
            if isinstance(protocols, str):
                protocols = [protocols]
            base_chain.append({"name": sample,
                                 "protocols": protocols,
                                 "@id": f"#material/{sample}"})
            
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
    ## Add assay table to input_json.
    input_json["assay"] = {}
    ## Add processes to assays in the input_json so they can be utilized by the conversion directives.
    for assay, process_sequence in assay_process_sequences.items():
        input_json["assay"][assay] = {"process": process_sequence}
    
    
    
    ###########
    ## Add study.id and assay.id to entities and protocols.
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
        for sample, measurement_sequences in attribtues["entities"].items():
            sample_attributes = input_json[entity_table_name][sample]
            if "assay_id" in sample_attributes:
                sample_assay_ids = sample_attributes["assay_id"] if isinstance(sample_attributes["assay_id"], list) else [sample_attributes["assay_id"]]
                if assay not in sample_assay_ids:
                    sample_attributes["assay_id"] = sample_assay_ids + [assay]
            else:
                sample_attributes["assay_id"] = [assay]
            
        for protocol in attributes["protocols"]:
            protocol_attributes = input_json[protocol_table_name][protocol]
            if "assay_id" in protocol_attributes:
                protocol_assay_ids = protocol_attributes["assay_id"] if isinstance(protocol_attributes["assay_id"], list) else [protocol_attributes["assay_id"]]
                if assay not in protocol_assay_ids:
                    protocol_attributes["assay_id"] = protocol_assay_ids + [assay]
            else:
                protocol_attributes["assay_id"] = [assay]
            
            ## Add study to measurement protocols since they didn't get added previously when looping over entities.
            if study_key in protocol_attributes:
                protocol_studies = protocol_attributes[study_key]
                protocol_studies = protocol_studies if isinstance(protocol_studies, list) else [protocol_studies]
            else:
                protocol_studies = []
            study = attributes["study"]
            if study not in protocol_studies:
                protocol_studies.append(study)
            input_json[protocol_table_name][protocol][study_key] = protocol_studies
    








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
















def _handle_errors():
    """
    """

import re



tab_warning_codes_to_skip = [3002]
tab_warning_messages_to_skip = []
tab_warning_supplemental_to_skip = [r'Protocol(s) of type (.*) defined in the ISA-configuration (.*)']

tab_warning_codes_to_modify = []
tab_warning_codes_modification = []
tab_warning_messages_to_modify = [r'A required node factor value is missing value']
tab_warning_messages_modification = ["warning['supplemental']"]
tab_warning_supplemental_to_modify = [r'A property value in (.*) is required']
tab_warning_supplemental_modification = ["warning['supplemental'].replace('required', 'missing')"]


tab_error_codes_to_skip = []
tab_error_messages_to_skip = [r'Measurement/technology type invalid']
tab_error_supplemental_to_skip = []

tab_error_codes_to_modify = []
tab_error_codes_modification = []
tab_error_messages_to_modify = []
tab_error_messages_modification = []
tab_error_supplemental_to_modify = []
tab_error_supplemental_modification = []


json_warning_codes_to_skip = [4004, 3002]
json_warning_messages_to_skip = []
json_warning_supplemental_to_skip = []

json_warning_codes_to_modify = []
json_warning_codes_modification = []
json_warning_messages_to_modify = []
json_warning_messages_modification = []
json_warning_supplemental_to_modify = []
json_warning_supplemental_modification = []


json_error_codes_to_skip = []
json_error_messages_to_skip = []
json_error_supplemental_to_skip = []

json_error_codes_to_modify = []
json_error_codes_modification = []
json_error_messages_to_modify = []
json_error_messages_modification = []
json_error_supplemental_to_modify = []
json_error_supplemental_modification = []




def isa_validation_message_formatting(validation_messages: dict, silent: bool,
                                      warning_codes_to_skip: list[int],
                                      warning_messages_to_skip: list[str],
                                      warning_supplemental_to_skip: list[str],
                                      warning_codes_to_modify: list[int],
                                      warning_codes_modification: list[str],
                                      warning_messages_to_modify: list[str],
                                      warning_messages_modification: list[str],
                                      warning_supplemental_to_modify: list[str],
                                      warning_supplemental_modification: list[str],
                                      error_codes_to_skip: list[int],
                                      error_messages_to_skip: list[str],
                                      error_supplemental_to_skip: list[str],
                                      error_codes_to_modify: list[int],
                                      error_codes_modification: list[str],
                                      error_messages_to_modify: list[str],
                                      error_messages_modification: list[str],
                                      error_supplemental_to_modify: list[str],
                                      error_supplemental_modification: list[str]):
    """
    """
    if validation_messages["validation_finished"]:
        message = ("An unknown error was encountered when validating the ISA format. "
                   "Due to this, the validation was not able to be completed.")
        _handle_errors(True, silent, message)
        
    for warning in validation_messages["warnings"]:
        ## Look to skip.
        if warning['code'] in warning_codes_to_skip or\
           any([True for regex in warning_messages_to_skip if re.match(regex, warning['message'])]) or\
           any([True for regex in warning_supplemental_to_skip if re.match(regex, warning['supplemental'])]):
            continue
        ## Look to modify.
        if warning['code'] in warning_codes_to_modify:
            modification = warning_codes_modification[warning_codes_to_modify.index(warning['code'])]
            _handle_errors(False, silent, eval(modification))
            continue
        
        needs_continue = False
        for i, regex in enumerate(warning_messages_to_modify):
            if re.match(regex, warning['message']):
                needs_continue = True
                modification = warning_messages_modification[i]
                _handle_errors(False, silent, eval(modification))
                break
        if needs_continue:
            continue
        
        needs_continue = False
        for i, regex in enumerate(warning_supplemental_to_modify):
            if re.match(regex, warning['supplemental']):
                needs_continue = True
                modification = warning_supplemental_modification[i]
                _handle_errors(False, silent, eval(modification))
                break
        if needs_continue:
            continue
        
        _handle_errors(False, silent, f"{warning['message']} \n{warning['supplemental']}")
    

    for error in validation_messages["errors"]:
        ## Look to skip.
        if error['code'] in error_codes_to_skip or\
           any([True for regex in error_messages_to_skip if re.match(regex, error['message'])]) or\
           any([True for regex in error_supplemental_to_skip if re.match(regex, error['supplemental'])]):
            continue
        ## Look to modify.
        if error['code'] in error_codes_to_modify:
            modification = error_codes_modification[error_codes_to_modify.index(error['code'])]
            _handle_errors(True, silent, eval(modification))
            continue
        
        needs_continue = False
        for i, regex in enumerate(error_messages_to_modify):
            if re.match(regex, error['message']):
                needs_continue = True
                modification = error_messages_modification[i]
                _handle_errors(True, silent, eval(modification))
                break
        if needs_continue:
            continue
        
        needs_continue = False
        for i, regex in enumerate(error_supplemental_to_modify):
            if re.match(regex, error['supplemental']):
                needs_continue = True
                modification = error_supplemental_modification[i]
                _handle_errors(True, silent, eval(modification))
                break
        if needs_continue:
            continue
        
        _handle_errors(True, silent, f"{error['message']} \n{error['supplemental']}")



