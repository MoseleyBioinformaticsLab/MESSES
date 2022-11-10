# -*- coding: utf-8 -*-
"""
Convert JSON data to another JSON format.

Usage:
    messes convert -h | --help
    messes convert mwtab <input-JSON> <output-name> [--tag-override=<conversion-tags>] [--silent]
    messes convert generic <input-JSON> <output-name> <conversion-tags> [--silent]
    messes convert print-tags <format>

Options:
    -h, --help                      Show this screen.
    -v, --version                   Show version.
    --tag-override                  Conversion tags that will be used to update the built-in tags for the format.

"""

import operator
import re
import sys
import pathlib
from importlib.machinery import SourceFileLoader
import json
import datetime

import docopt
import mwtab

from . import extract


## Should all protocol types loop over all protocols and concat them or only certain ones? collection does not and treatment does currently.
## Should the MS metabolite Data be intensity or corrected_raw_intensity? There are submitted data using intensity, but the convert code is corrected_raw.
## natural abundance corrected and protein normalized peak area for intensity vs natural abundance corrected peak area for corrected_raw
## Currently the Treatment factor in SSF is a list, make sure this converts into mwTab text correctly.

def main() :
    args = docopt.docopt(__doc__)
    
    ## Validate args.
    
    ## Read in files.
    with open(args["<input-JSON>"], 'r') as jsonFile:
        internal_data = json.load(jsonFile)
        
    if args["<conversion-tags>"]:
        if re.search(r".*(\.xls[xm]?|\.csv)", args["<conversion-tags>"]):
            if re.search(r"\.xls[xm]?$", args["<conversion-tags>"]):
                args["<conversion-tags>"] += ":#convert"
            tagParser = extract.tagParser()
            worksheet_tuple = tagParser.loadsheet(args["<conversion-tags>"])
            tagParser.parseSheet(*worksheet_tuple)
            conversion_tags = tagParser.extraction
        
        elif re.match(r".*\.json$", args["<conversion-tags>"]):
            with open(args["<conversion-tags>"], 'r') as jsonFile:
                conversion_tags = json.load(jsonFile)
        
        else:
            print("Error: Unknown file type for the conversion tags file.")
            sys.exit()
    
    ## Validate conversion tags.
    
    ## Generate new JSON.
    output_json = {}
    for record_table, records in conversion_tags.items():
        for record_name, attributes in records.items():
            if required := attributes.get("required"):
                if required.lower() == "false":
                    required = False
                else:
                    required = True
            
            if attributes["value_type"] == "section":
                value = handle_code_tag(internal_data, record_table, record_name, attributes)
                keys = [record_table]
            elif attributes["value_type"] == "matrix":
                value = compute_matrix_value(internal_data, record_table, record_name, attributes)
                keys = [record_table, record_name]
            elif attributes["value_type"] == "str":
                value = compute_string_value(internal_data, record_table, record_name, attributes)
                keys = [record_table, record_name]
            else:
                print("Warning: Unknown value_type for the conversion \"" + record_name + "\" in the \"" + record_table + "\" table. It will be skipped.")
                
            if value is None and required:
                print("Error: The conversion tag to create the \"" + record_name + "\" record in the \"" + record_table + "\" table did not return a value.")
                sys.exit()
            elif value is None and not required:
                if not args["--silent"]:
                    print("Warning: The non-required conversion tag to create the \"" + record_name + "\" record in the \"" + record_table + "\" table could not be created.")
                continue
            
            nested_set(output_json, keys, value)
    
    ## Optional way to do things compared to the code block below this.
    # with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as tp:
    #     tp.write(json.dumps(output_json))
    #     tp.seek(0)
    #     mwfile = mwtab.mwtab.MWTabFile("")
    #     mwfile.read(tp)
    # with open(args["<output-name>"], 'w', encoding="utf-8") as outfile:
    #     mwfile.write(outfile, file_format="mwtab")
    
    mwtabfile = mwtab.mwtab.MWTabFile("")
    mwtabfile.update(output_json)
    mwtabfile.header = " ".join(
        ["#METABOLOMICS WORKBENCH"]
        + [item[0] + ":" + item[1] for item in mwtabfile["METABOLOMICS WORKBENCH"].items() if item[0] not in ["VERSION", "CREATED_ON"]]
    )            
    
    mwtabfile.source = args["<output-name>"]
    mwtab.validator.validate_file(mwtabfile, verbose=True)
    
    with open(args["<output-name>"],'w') as jsonFile :
        jsonFile.write(json.dumps(output_json, indent=2))
        
        
    with open(args["<output-name>"], 'w', encoding='utf-8') as outfile:
        mwtabfile.write(outfile, file_format="mwtab")



def nested_set(dic, keys, value):
    for key in keys[:-1]:
        dic = dic.setdefault(key, {})
    dic[keys[-1]] = value



def handle_code_tag(internal_data, record_table, record_name, attributes):
    """"""
    
    if import_path := attributes.get("import"):
        import_name = pathlib.Path(import_path).stem
        global_variables = globals()
        global_variables[import_name] = SourceFileLoader(import_name, import_path).load_module()
    
    if code := attributes.get("code"):
        try:
            value = eval(code)
        except Exception as error:
            print("Error: The code conversion tag to create the \"" + record_name + "\" record in the \"" + record_table + "\" table encountered an error while executing.")
            raise error
        
        return value
    else:
        return None



def compute_string_value(internal_data, record_table, record_name, attributes, silent=False):
    """"""
    
    ## required
    if required := attributes.get("required"):
        if required.lower() == "false":
            required = False
        else:
            required = True
    
    ## override
    if value := attributes.get("override"):
        return value
    
    ## code
    value = handle_code_tag(internal_data, record_table, record_name, attributes)
            
    if value is not None:
        if not isinstance(value, str):
            print("Error: The code conversion tag to create the \"" + record_name + "\" record in the \"" + record_table + "\" table did not return a string type value.")
            sys.exit()
        
        return value
    
    ## fields
    fields = [(field, True if re.match(r"^\"(.*)\"$", field) else False) for field in attributes["fields"]]
    has_test = False
    if test := attributes.get("test"):
        has_test = True
        split = test.split("=")
        test_field = split[0].strip()
        test_value = split[1].strip()
    
    ## for_each
    if for_each := attributes.get("for_each"):
        if for_each.lower() == "true":
            for_each = True
        else:
            for_each = False
    
    if for_each:
        delimiter = attributes.get("delimiter", "")
        
        records = [record_attributes for record, record_attributes in internal_data[attributes["table"]].items() if has_test and test_field in record_attributes and record_attributes[test_field] == test_value]
        if not records:
            if required:
                print("Error: The conversion tag to create the \"" + record_name + "\" record in the \"" + record_table + "\" table did not match any records in the input data.")
                sys.exit()
            else:
                return None
        
        if sort_by := attributes.get("sort_by"):                
            records = sorted(records, key = operator.itemgetter(*sort_by), reverse = attributes["sort_order"] == "descending")
        
        value_for_each_record = []
        for record_attributes in records:
            value = ""
            for field in fields:
                ## Is the field a literal?
                if not field[1]:
                    ## If the field is not a literal value and it's not in the record print an error.
                    if field[0] not in record_attributes:
                        if required:
                            print("Error: The conversion tag to create the \"" + record_name + "\" record in the \"" + record_table + "\" table matched a record in the input data that did not contain the \"" + field[0] + "\" field.")
                            sys.exit()
                        elif not silent:
                            print("Warning: The conversion tag to create the \"" + record_name + "\" record in the \"" + record_table + "\" table matched a record in the input data that did not contain the \"" + field[0] + "\" field.")
                            continue
                
                    value += str(record_attributes[field[0]])
                else:
                    value += field[0]
                    
            value_for_each_record.append(value)
            
        return delimiter.join(value_for_each_record)
    
    ## record_id
    if attributes.get("record_id"):
        record_attributes = internal_data[attributes["table"]][attributes["record_id"]]
    elif has_test:
        for record, record_attributes in internal_data[attributes["table"]].items():
            if test_field in record_attributes and record_attributes[test_field] == test_value:
                break
    else:
        record_attributes = list(internal_data[attributes["table"]].values())[0]
    
    value = ""
    for field in fields:
        ## Is the field a literal?
        if not field[1]:
            ## If the field is not a literal value and it's not in the record print an error.
            if field[0] not in record_attributes:
                if required:
                    print("Error: The indicated record_id for the conversion tag to create the \"" + record_name + "\" record in the \"" + record_table + "\" table does not contain the \"" + field[0] + "\" field.")
                    sys.exit()
                elif not silent:
                    print("Warning: The indicated record_id for the conversion tag to create the \"" + record_name + "\" record in the \"" + record_table + "\" table does not contain the \"" + field[0] + "\" field.")
                    continue
        
            value += str(record_attributes[field[0]])
        else:
            value += field[0]
            
    return value

                
                
    
def compute_matrix_value(internal_data, record_table, record_name, attributes):
    """"""
    
    value = handle_code_tag(internal_data, record_table, record_name, attributes)
            
    if value is not None:
        if not isinstance(value, list) or not all([isinstance(record, dict) for record in value]):
            print("Error: The code conversion tag to create the \"" + record_name + "\" record in the \"" + record_table + "\" table did not return a matrix type value.")
            sys.exit()
        
        return value
    
    
    ## fields_to_headers
    if fields_to_headers := attributes.get("fields_to_headers"):
        if fields_to_headers.lower() == "true":
            fields_to_headers = True
        else:
            fields_to_headers = False
    
    exclusion_headers = attributes.get("optional_headers", [])
    
    ## TODO Should there be an option so that headers are not required to be in the input data?
    headers = []
    if attributes.get("headers"):
        for pair in attributes["headers"]:
            split = pair.split("=")
            output_key = split[0].strip()
            input_key = split[1].strip()
            
            if new_output_key := re.match(r"^\"(.*)\"$", output_key):
                output_key = new_output_key.group(1)
                output_key_is_literal = True
            else:
                output_key_is_literal = False
            
            if new_input_key := re.match(r"^\"(.*)\"$", input_key):
                input_key = new_input_key.group(1)
                input_key_is_literal = True
            else:
                input_key_is_literal = False
            
            headers.append({"output_key":output_key, "output_key_is_literal": output_key_is_literal, 
                            "input_key":input_key, "input_key_is_literal": input_key_is_literal})
    
    ## TODO think about changing optional_headers to inclusion_headers and having an option about printing warnings if the headers aren't there.
    optional_headers = attributes.get("optional_headers", [])
        
    if collate := attributes.get("collate"):
        ## TODO think about whether to do collate.strip() here to remove spaces.
        if new_collate := re.match(r"^\"(.*)\"$", collate):
            collate_is_literal = True
            collate = new_collate.group(1)
        else:
            collate_is_literal = False
        ## collate has to match an output_key in the headers, and the corresponding input_key cannot be literal.
        ## TODO make sure there is validation that checks that headers are unique, that collate exists in it, and it's input key is not literal.
        collate_input_header = [header["input_key"] for header in headers if header["output_key"] == collate and header["output_key_is_literal"] == collate_is_literal][0]
            
        records = {}
        for record, record_attributes in internal_data[attributes["table"]].items():
            collate_key = record_attributes[collate_input_header]
            
            if collate_key not in records:
                records[collate_key] = {}
            
            for header in headers:
                if header["output_key_is_literal"] and header["input_key_is_literal"]:
                    records[collate_key][header["output_key"]] = header["input_key"]
                elif header["output_key_is_literal"] and not header["input_key_is_literal"]:
                    if header["input_key"] not in record_attributes:
                        print("Error: The headers conversion tag to create the \"" + record_name + "\" matrix in the \"" + record_table + "\" table has an input key, \"" + header["input_key"] + "\", that does not exist in the record, \"" + record + "\", of the input table, \"" + attributes["table"] + "\".")
                        sys.exit()
                    if header["output_key"] in records[collate_key] and record_attributes[header["input_key"]] != records[collate_key][header["output_key"]]:
                        print("Warning: When creating the \"" + record_name + "\" matrix for the \"" + record_table + "\" table different values for the output key, \"" + header["output_key"] + "\", were found. Only the last value will be used.")
                    records[collate_key][header["output_key"]] = record_attributes[header["input_key"]]
                elif not header["output_key_is_literal"] and header["input_key_is_literal"]:
                    if header["output_key"] not in record_attributes:
                        print("Error: The headers conversion tag to create the \"" + record_name + "\" matrix in the \"" + record_table + "\" table has an output key, \"" + header["output_key"] + "\", that does not exist in the record, \"" + record + "\", of the input table, \"" + attributes["table"] + "\".")
                        sys.exit()
                    records[collate_key][record_attributes[header["output_key"]]] = header["input_key"]
                elif not header["output_key_is_literal"] and not header["input_key_is_literal"]:
                    if header["input_key"] not in record_attributes:
                        print("Error: The headers conversion tag to create the \"" + record_name + "\" matrix in the \"" + record_table + "\" table has an input key, \"" + header["input_key"] + "\", that does not exist in the record, \"" + record + "\", of the input table, \"" + attributes["table"] + "\".")
                        sys.exit()
                    if header["output_key"] not in record_attributes:
                        print("Error: The headers conversion tag to create the \"" + record_name + "\" matrix in the \"" + record_table + "\" table has an output key, \"" + header["output_key"] + "\", that does not exist in the record, \"" + record + "\", of the input table, \"" + attributes["table"] + "\".")
                        sys.exit()
                    if record_attributes[header["output_key"]] in records[collate_key] and record_attributes[header["input_key"]] != records[collate_key][record_attributes[header["output_key"]]]:
                        print("Warning: When creating the \"" + record_name + "\" matrix for the \"" + record_table + "\" table different values for the output key, \"" + record_attributes[header["output_key"]] + "\", were found. Only the last value will be used.")
                    records[collate_key][record_attributes[header["output_key"]]] = record_attributes[header["input_key"]]
            
            if fields_to_headers:
                records[collate_key].update({field:value for field, value in record_attributes.items() if field not in exclusion_headers})
            else:
                for header in optional_headers:
                    if header in record_attributes:
                        records[collate_key][header] = record_attributes[header]
                    
        records = list(records.values())
    
    else:
        records = []
        for record, record_attributes in internal_data[attributes["table"]].items():
            temp_dict = {}            
            for header in headers:
                if header["output_key_is_literal"] and header["input_key_is_literal"]:
                    temp_dict[header["output_key"]] = header["input_key"]
                elif header["output_key_is_literal"] and not header["input_key_is_literal"]:
                    if header["input_key"] not in record_attributes:
                        print("Error: The headers conversion tag to create the \"" + record_name + "\" matrix in the \"" + record_table + "\" table has an input key, \"" + header["input_key"] + "\", that does not exist in the record, \"" + record + "\", of the input table, \"" + attributes["table"] + "\".")
                        sys.exit()
                    temp_dict[header["output_key"]] = record_attributes[header["input_key"]]
                elif not header["output_key_is_literal"] and header["input_key_is_literal"]:
                    if header["output_key"] not in record_attributes:
                        print("Error: The headers conversion tag to create the \"" + record_name + "\" matrix in the \"" + record_table + "\" table has an output key, \"" + header["output_key"] + "\", that does not exist in the record, \"" + record + "\", of the input table, \"" + attributes["table"] + "\".")
                        sys.exit()
                    temp_dict[record_attributes[header["output_key"]]] = header["input_key"]
                elif not header["output_key_is_literal"] and not header["input_key_is_literal"]:
                    if header["input_key"] not in record_attributes:
                        print("Error: The headers conversion tag to create the \"" + record_name + "\" matrix in the \"" + record_table + "\" table has an input key, \"" + header["input_key"] + "\", that does not exist in the record, \"" + record + "\", of the input table, \"" + attributes["table"] + "\".")
                        sys.exit()
                    if header["output_key"] not in record_attributes:
                        print("Error: The headers conversion tag to create the \"" + record_name + "\" matrix in the \"" + record_table + "\" table has an output key, \"" + header["output_key"] + "\", that does not exist in the record, \"" + record + "\", of the input table, \"" + attributes["table"] + "\".")
                        sys.exit()
                    temp_dict[record_attributes[header["output_key"]]] = record_attributes[header["input_key"]]
            
            if fields_to_headers:
                temp_dict.update({field:value for field, value in record_attributes.items() if field not in exclusion_headers})
            else:
                for header in optional_headers:
                    if header in record_attributes:
                        temp_dict[header] = record_attributes[header]
                    
            records.append(temp_dict)
    
    
    if sort_by := attributes.get("sort_by"):                
        records = sorted(records, key = operator.itemgetter(*sort_by), reverse = attributes["sort_order"] == "descending")
        
    return records



    



def create_sample_lineages(internal_data, entity_table_name="entity", parent_key="parentID") -> dict:
    """
    {entity_id:{"ancestors":[ancestor0, ancestor1, ...],
                "siblings":[sibling0, sibling1, ...]}
     ...
    }
    """
    
    lineages = {}
    for entity_name, entity_attributes in internal_data[entity_table_name].items():
        ancestors = []
        while parent_name := entity_attributes.get(parent_key):
            ancestors.append(parent_name)
            entity_attributes = internal_data[entity_table_name][parent_name]
        ancestors.reverse()
        lineages[entity_name] = {"ancestors":ancestors}
        
    for entity_name in lineages:
        siblings = []
        if not lineages[entity_name]["ancestors"]:
            continue
        parent_name = lineages[entity_name]["ancestors"][0]
        for sibling_name, entity_attributes in internal_data[entity_table_name].items():
            if (sibling_parent_name := entity_attributes.get(parent_key)) and sibling_parent_name == parent_name:
                siblings.append(sibling_name)
            
        lineages[entity_name]["siblings"] = siblings

    return lineages



def create_subject_sample_factors(internal_data, 
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
                                  lineage_field_exclusion_list: list[str]|tuple[str] =("study.id", "project.id", "parentID")) -> dict:
    """"""
    
    samples = []
    for measurement_name, measurement_attributes in internal_data[measurement_table_name].items():
        if sample_id := measurement_attributes.get(sample_id_key):
            samples.append(sample_id)
            
    lineages = create_sample_lineages(internal_data, entity_table_name=entity_table_name, parent_key=parent_key)
    
    factor_fields = {factor_attributes[factor_field_key]:{"name":factor, "allowed_values":factor_attributes[factor_allowed_values_key]} for factor, factor_attributes in internal_data[factor_table_name].items()}
    
    ss_factors = []
    for sample in samples:
        if sample not in lineages:
            print("Error: The sample, \"" + sample + "\", pulled from the \"" + measurement_table_name + "\" table is not in the \"" + entity_table_name + "\". Thus the subject-sample-factors cannot be determined.")
            sys.exit()
        
        additional_sample_data = {}
        factors = {}
        subject_id = ""
        lineage_count = 0
        ## Loop over all of the sample's ancestors and add them to additional data as well find all the factors, and the closest subject.
        for ancestor in lineages[sample]["ancestors"]:
            for field, field_value in internal_data[entity_table_name][ancestor].items():
                if field in lineage_field_exclusion_list:
                    continue
                additional_sample_data["lineage" + str(lineage_count) + "_" + field] = field_value
                
                if field in factor_fields and factor_fields[field]["name"] not in factors:
                    if isinstance(field_value,str) and field_value in factor_fields[field]["allowed_values"]:
                        factors[factor_fields[field]["name"]] = field_value
                    elif isinstance(field_value,list) and (field_values := [value for value in field_value if value in factor_fields[field]["allowed_values"]]):
                        factors[factor_fields[field]["name"]] = field_values
                    
                if not subject_id and field == entity_type_key and field_value == subject_type_value:
                    subject_id = ancestor
                    
            lineage_count += 1
        
        ## Look for siblings to add to additional data if sibling_match_field is given.
        if sibling_match_field and sibling_match_value:
            for sibling in lineages[sample]["siblings"]:
                if sibling_match_field in internal_data[entity_table_name][sibling] and \
                   sibling_match_value == internal_data[entity_table_name][sibling][sibling_match_field]:
                       for field, field_value in internal_data[entity_table_name][sibling].items():
                           if field in lineage_field_exclusion_list:
                               continue
                           additional_sample_data["lineage" + str(lineage_count) + "_" + field] = field_value
                
                lineage_count += 1
        
        ## Look for factors on the sample itself.
        for field, field_value in internal_data[entity_table_name][sample].items():            
            if field in factor_fields and factor_fields[field]["name"] not in factors:
                if isinstance(field_value,str) and field_value in factor_fields[field]["allowed_values"]:
                    factors[factor_fields[field]["name"]] = field_value
                elif isinstance(field_value,list) and (field_values := [value for value in field_value if value in factor_fields[field]["allowed_values"]]):
                    factors[factor_fields[field]["name"]] = field_values
        
        ss_factors.append({"Subject ID":subject_id, "Sample ID":sample, "Factors":factors, "Additional sample data":additional_sample_data})
        
    ## Run some error checking on factors found.
    found_factors = {factor for ss_factor in ss_factors for factor in ss_factor["Factors"]}
    missing_factors = found_factors - set(internal_data[factor_table_name])
    if missing_factors:
        print("Warning: There are factors in the \"" + factor_table_name + "\" table that were not found when determining the subject-sample-factors. These factors are: " + ", ".join(missing_factors))
    
    samples_without_all_factors = [ss_factor["Sample ID"] for ss_factor in ss_factors if found_factors - set(ss_factor["Factors"])]
    if samples_without_all_factors:
       print("Warning: The following samples do not have the full set of factors:" + "\n".join(samples_without_all_factors))
        
    return ss_factors




# internal_data["entity"] = {}
# for sample_name, sample_attributes in internal_data["sample"].items():
#     internal_data["entity"][sample_name] = sample_attributes
#     internal_data["entity"][sample_name]["type"] = "sample"
# for subject_name, subject_attributes in internal_data["subject"].items():
#     internal_data["entity"][subject_name] = subject_attributes
#     internal_data["entity"][subject_name]["type"] = "subject"

# internal_data["factor"] = \
# {'Treatment': {
#   'allowed_values': ['naive', 'syngenic', 'allogenic'],
#   'id': 'Treatment',
#   'field': 'protocol.id',
#   'project.id': 'GH_Spleen',
#   'study.id': 'GH_Spleen'},
#  'Time Point': {
#   'allowed_values': ['0', '7', '42'],
#   'id': 'Time Point',
#   'field': 'time_point',
#   'project.id': 'GH_Spleen',
#   'study.id': 'GH_Spleen'}}





