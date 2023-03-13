# -*- coding: utf-8 -*-
"""
Functions For mwtab Format
--------------------------
"""

import sys
import operator


def create_sample_lineages(input_json: dict, entity_table_name: str="entity", parent_key: str="parent_id") -> dict:
    """Determine all the ancestors and siblings for each entity in the entity table.
    
    The returned dictionary is of the form:
    
    {entity_id:{"ancestors":[ancestor0, ancestor1, ...],
                "siblings":[sibling0, sibling1, ...]}
     ...
    }
    
    Args:
        input_json: the dictionary where the entity table is.
        entity_table_name: the name of the entity table in input_json.
        parent_key: the field name for the field that points to the entity's parent.
        
    Returns:
        a dictionary where the keys are the entity ids and the values are a dictionary 
        of it's ancestors and siblings.
    """
    
    lineages = {}
    for entity_name, entity_attributes in input_json[entity_table_name].items():
        ancestors = []
        while parent_name := entity_attributes.get(parent_key):
            ancestors.append(parent_name)
            if parent_name not in input_json[entity_table_name]:
                print("Error: The parent entity, \"" + parent_name + "\", pulled from the entity \"" + entity_name + \
                      "\" in the \"" + entity_table_name + "\" table is not in the \"" + entity_table_name + "\". " +\
                      "Parent entities must be in the table with thier children.", file=sys.stderr)
                sys.exit()
            entity_attributes = input_json[entity_table_name][parent_name]
        ancestors.reverse()
        lineages[entity_name] = {"ancestors":ancestors}
        
    for entity_name in lineages:
        siblings = []
        if not lineages[entity_name]["ancestors"]:
            lineages[entity_name]["siblings"] = []
            continue
        parent_name = lineages[entity_name]["ancestors"][-1]
        for sibling_name, entity_attributes in input_json[entity_table_name].items():
            if (sibling_parent_name := entity_attributes.get(parent_key)) and sibling_parent_name == parent_name:
                siblings.append(sibling_name)
            
        lineages[entity_name]["siblings"] = siblings

    return lineages



def create_subject_sample_factors(input_json: dict, 
                                  measurement_table_name: str="measurement", 
                                  sibling_match_field: str="protocol.id", 
                                  sibling_match_value: str="protein_extraction",
                                  sample_id_key: str="entity.id",
                                  entity_table_name: str="entity", 
                                  entity_type_key: str="type",
                                  subject_type_value: str="subject",
                                  parent_key: str="parent_id",
                                  factor_table_name: str="factor",
                                  factor_field_key: str="field",
                                  factor_allowed_values_key: str="allowed_values",
                                  protocol_table_name: str="protocol",
                                  protocol_field: str="protocol.id",
                                  protocol_type_field: str="type",
                                  storage_type_value: str="storage",
                                  storage_files_key: str="data_files",
                                  lineage_field_exclusion_list: list[str]|tuple[str] =("study.id", "project.id", "parent_id")) -> list[dict]:
    """Create the SUBJECT_SAMPLE_FACTORS section of the mwTab JSON.
    
    Args:
        input_json: the data to build from.
        measurement_table_name: the name of the table in input_json where the measurements are.
        sibling_match_field: the field to use to determine if a sibling should be added to the SSF.
        sibling_match_value the value to use to determine if a sibling should be added to the SSF.
        sample_id_key: the field in the measurement that has the sample id associated with it.
        entity_table_name: the name of the table in input_json where the entities are.
        entity_type_key: the field in entity records where the type is located.
        subject_type_value: the value in the type key that means the entity is a subject.
        parent_key: the field that points to the parent of the record.
        factor_table_name: the name of the table in input_json where the factors are.
        factor_field_key: the field in factor records that tells what the factor field is in other records.
        factor_allowed_values_key: the field in factor records where the allowed values for that factor are.
        protocol_table_name: the name of the table in input_json where the protocols are.
        protocol_field: the field in records that contains the protocol(s) of the record.
        protocol_type_field: the field in protocol records where the type is located.
        storage_type_value: the value in the type key that means the protocol is a storage type.
        sotrage_files_key: the field in a storage type protocol record where the file names are located.
        lineage_field_exclusion_list: the fields in entity records that should not be added as additional data.
        
    Returns:
        a list of SUBJECT_SAMPLE_FACTORS.
    """
    
    samples = set()
    for measurement_name, measurement_attributes in input_json[measurement_table_name].items():
        if sample_id := measurement_attributes.get(sample_id_key):
            samples.add(sample_id)
            
    lineages = create_sample_lineages(input_json, entity_table_name=entity_table_name, parent_key=parent_key)
    
    factor_fields = {factor_attributes[factor_field_key]:{"name":factor, "allowed_values":factor_attributes[factor_allowed_values_key]} for factor, factor_attributes in input_json[factor_table_name].items()}
    
    ss_factors = []
    for sample in samples:
        if sample not in lineages:
            print("Error: The sample, \"" + sample + "\", pulled from the \"" + measurement_table_name + \
                  "\" table is not in the \"" + entity_table_name + "\". Thus the subject-sample-factors cannot be determined.", file=sys.stderr)
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
                if input_json[protocol_table_name][protocol_id][protocol_type_field] == storage_type_value:
                    data_files = input_json[protocol_table_name][protocol_id][storage_files_key]
                    if isinstance(data_files, list):
                        raw_files += data_files
                    else:
                        raw_files.append(str(data_files))
                    
            lineage_count += 1
        
        ## Look for siblings to add to additional data if sibling_match_field is given.
        if sibling_match_field and sibling_match_value:
            for sibling in lineages[sample]["siblings"]:
                match_field_value = input_json[entity_table_name][sibling][sibling_match_field]
                if sibling_match_field in input_json[entity_table_name][sibling] and \
                   ((isinstance(match_field_value, str) and sibling_match_value == match_field_value) or\
                   (isinstance(match_field_value, list) and sibling_match_value in match_field_value)):
                       for field, field_value in input_json[entity_table_name][sibling].items():
                           if field in lineage_field_exclusion_list:
                               continue
                           additional_sample_data["lineage" + str(lineage_count) + "_" + field] = str(field_value)
                       
                       ## Look for storage protocols on siblings that have data files associated with them.
                       for protocol_id in input_json[entity_table_name][sibling][protocol_field]:
                           if input_json[protocol_table_name][protocol_id][protocol_type_field] == storage_type_value:
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
            if input_json[protocol_table_name][protocol_id][protocol_type_field] == storage_type_value:
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
    missing_factors = set(input_json[factor_table_name]) - found_factors
    if missing_factors:
        print("Warning: There are factors in the \"" + factor_table_name +\
              "\" table that were not found when determining the subject-sample-factors. These factors are: " +\
              ", ".join(missing_factors), file=sys.stderr)
    
    samples_without_all_factors = [ss_factor["Sample ID"] for ss_factor in ss_factors if found_factors - set(ss_factor["Factors"])]
    if samples_without_all_factors:
       print("Warning: The following samples do not have the full set of factors: \n" + "\n".join(samples_without_all_factors), file=sys.stderr)
    
    ## Sort ss_factors.
    ss_factors = sorted(ss_factors, key = operator.itemgetter(*["Subject ID", "Sample ID"]))
        
    return ss_factors