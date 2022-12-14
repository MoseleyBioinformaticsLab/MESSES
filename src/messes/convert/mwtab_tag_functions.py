# -*- coding: utf-8 -*-
"""
functions for mwtab format
"""

import sys


def create_sample_lineages(input_json, entity_table_name="entity", parent_key="parentID") -> dict:
    """
    {entity_id:{"ancestors":[ancestor0, ancestor1, ...],
                "siblings":[sibling0, sibling1, ...]}
     ...
    }
    """
    
    lineages = {}
    for entity_name, entity_attributes in input_json[entity_table_name].items():
        ancestors = []
        while parent_name := entity_attributes.get(parent_key):
            ancestors.append(parent_name)
            entity_attributes = input_json[entity_table_name][parent_name]
        ancestors.reverse()
        lineages[entity_name] = {"ancestors":ancestors}
        
    for entity_name in lineages:
        siblings = []
        if not lineages[entity_name]["ancestors"]:
            continue
        parent_name = lineages[entity_name]["ancestors"][0]
        for sibling_name, entity_attributes in input_json[entity_table_name].items():
            if (sibling_parent_name := entity_attributes.get(parent_key)) and sibling_parent_name == parent_name:
                siblings.append(sibling_name)
            
        lineages[entity_name]["siblings"] = siblings

    return lineages



def create_subject_sample_factors(input_json, 
                                  measurement_table_name="measurement", 
                                  sibling_match_field="protocol.id", 
                                  sibling_match_value="protein_extraction",
                                  sample_id_key="sample.id",
                                  entity_table_name="entity", 
                                  entity_type_key="type",
                                  subject_type_value="subject",
                                  parent_key="parentID",
                                  factor_table_name="factor",
                                  factor_field_key="field",
                                  factor_allowed_values_key="allowed_values",
                                  protocol_table_name="protocol",
                                  protocol_field="protocol.id",
                                  protocol_type_field="type",
                                  storage_type_key="storage",
                                  storage_files_key="data_files",
                                  lineage_field_exclusion_list: list[str]|tuple[str] =("study.id", "project.id", "parentID")) -> dict:
    """"""
    
    samples = []
    for measurement_name, measurement_attributes in input_json[measurement_table_name].items():
        if sample_id := measurement_attributes.get(sample_id_key):
            samples.append(sample_id)
            
    lineages = create_sample_lineages(input_json, entity_table_name=entity_table_name, parent_key=parent_key)
    
    factor_fields = {factor_attributes[factor_field_key]:{"name":factor, "allowed_values":factor_attributes[factor_allowed_values_key]} for factor, factor_attributes in input_json[factor_table_name].items()}
    
    ss_factors = []
    for sample in samples:
        if sample not in lineages:
            print("Error: The sample, \"" + sample + "\", pulled from the \"" + measurement_table_name + "\" table is not in the \"" + entity_table_name + "\". Thus the subject-sample-factors cannot be determined.")
            sys.exit()
        
        additional_sample_data = {}
        raw_files = []
        factors = {}
        subject_id = ""
        lineage_count = 0
        ## Loop over all of the sample's ancestors and add them to additional data as well find all the factors, and the closest subject.
        for ancestor in lineages[sample]["ancestors"]:
            for field, field_value in input_json[entity_table_name][ancestor].items():
                if field in lineage_field_exclusion_list:
                    continue
                additional_sample_data["lineage" + str(lineage_count) + "_" + field] = str(field_value)
                
                if field in factor_fields and factor_fields[field]["name"] not in factors:
                    if isinstance(field_value,str) and field_value in factor_fields[field]["allowed_values"]:
                        factors[factor_fields[field]["name"]] = field_value
                    elif isinstance(field_value,list) and (field_values := [value for value in field_value if value in factor_fields[field]["allowed_values"]]):
                        factors[factor_fields[field]["name"]] = field_values[0] if len(field_values) == 1 else str(field_values)
                    
                if not subject_id and field == entity_type_key and field_value == subject_type_value:
                    subject_id = ancestor
            
            ## Look for storage protocols on ancestors that have data files associated with them.
            for protocol_id in input_json[entity_table_name][ancestor][protocol_field]:
                if input_json[protocol_table_name][protocol_id][protocol_type_field] == storage_type_key:
                    data_files = input_json[protocol_table_name][protocol_id][storage_files_key]
                    if isinstance(data_files, list):
                        raw_files += data_files
                    else:
                        raw_files.append(str(data_files))
                    
            lineage_count += 1
        
        ## Look for siblings to add to additional data if sibling_match_field is given.
        if sibling_match_field and sibling_match_value:
            for sibling in lineages[sample]["siblings"]:
                if sibling_match_field in input_json[entity_table_name][sibling] and \
                   sibling_match_value == input_json[entity_table_name][sibling][sibling_match_field]:
                       for field, field_value in input_json[entity_table_name][sibling].items():
                           if field in lineage_field_exclusion_list:
                               continue
                           additional_sample_data["lineage" + str(lineage_count) + "_" + field] = str(field_value)
                       
                       ## Look for storage protocols on siblings that have data files associated with them.
                       for protocol_id in input_json[entity_table_name][sibling][protocol_field]:
                           if input_json[protocol_table_name][protocol_id][protocol_type_field] == storage_type_key:
                               data_files = input_json[protocol_table_name][protocol_id][storage_files_key]
                               if isinstance(data_files, list):
                                   raw_files += data_files
                               else:
                                   raw_files.append(str(data_files))
                
                lineage_count += 1
        
        ## Look for factors on the sample itself.
        for field, field_value in input_json[entity_table_name][sample].items():            
            if field in factor_fields and factor_fields[field]["name"] not in factors:
                if isinstance(field_value,str) and field_value in factor_fields[field]["allowed_values"]:
                    factors[factor_fields[field]["name"]] = field_value
                elif isinstance(field_value,list) and (field_values := [value for value in field_value if value in factor_fields[field]["allowed_values"]]):
                    factors[factor_fields[field]["name"]] = field_values[0] if len(field_values) == 1 else str(field_values)
                    
        ## Look for storage protocol on sample itself.
        for protocol_id in input_json[entity_table_name][sample][protocol_field]:
            if input_json[protocol_table_name][protocol_id][protocol_type_field] == storage_type_key:
                data_files = input_json[protocol_table_name][protocol_id][storage_files_key]
                if isinstance(data_files, list):
                    raw_files += data_files
                else:
                    raw_files.append(str(data_files))
        
        ## Add raw files as a key to additional sample data.
        if raw_files:
            if len(raw_files) == 1:
                additional_sample_data["RAW_FILE_NAME"] = str(raw_files[0])
            else:
                additional_sample_data["RAW_FILE_NAME"] = str(raw_files)
        
        ss_factors.append({"Subject ID":subject_id, "Sample ID":sample, "Factors":factors, "Additional sample data":additional_sample_data})
        
    ## Run some error checking on factors found.
    found_factors = {factor for ss_factor in ss_factors for factor in ss_factor["Factors"]}
    missing_factors = found_factors - set(input_json[factor_table_name])
    if missing_factors:
        print("Warning: There are factors in the \"" + factor_table_name + "\" table that were not found when determining the subject-sample-factors. These factors are: " + ", ".join(missing_factors))
    
    samples_without_all_factors = [ss_factor["Sample ID"] for ss_factor in ss_factors if found_factors - set(ss_factor["Factors"])]
    if samples_without_all_factors:
       print("Warning: The following samples do not have the full set of factors:" + "\n".join(samples_without_all_factors))
        
    return ss_factors