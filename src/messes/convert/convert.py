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

from ..extract import extract


## Should all protocol types loop over all protocols and concat them or only certain ones? collection does not and treatment does currently.
## Should the MS metabolite Data be intensity or corrected_raw_intensity? There are submitted data using intensity, but the convert code is corrected_raw.
## natural abundance corrected and protein normalized peak area for intensity vs natural abundance corrected peak area for corrected_raw
## Currently the Treatment factor in SSF is a list, make sure this converts into mwTab text correctly.
## Optionally put non required fields as empty strings instead of not including them. This is done with default value.
## Should default value work if code is given but fails? Right now only works if field is not found.

def main() :
    args = docopt.docopt(__doc__)
    
    ## Validate args.
    
    ## Read in files.
    with open(args["<input-JSON>"], 'r') as jsonFile:
        input_json = json.load(jsonFile)
        
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
    for conversion_table, conversion_records in conversion_tags.items():
        for conversion_record_name, conversion_attributes in conversion_records.items():
            if required := conversion_attributes.get("required"):
                if required.lower() == "false":
                    required = False
                else:
                    required = True
                    
            default = conversion_attributes.get("default")
            if default and (literal_match := re.match(literal_regex, default)):
                default = literal_match.group(1)
            
            if conversion_attributes["value_type"] == "section":
                value = handle_code_tag(input_json, conversion_table, conversion_record_name, conversion_attributes)
                keys = [conversion_table]
            elif conversion_attributes["value_type"] == "matrix":
                value = compute_matrix_value(input_json, conversion_table, conversion_record_name, conversion_attributes)
                keys = [conversion_table, conversion_record_name]
            elif conversion_attributes["value_type"] == "str":
                value = compute_string_value(input_json, conversion_table, conversion_record_name, conversion_attributes)
                keys = [conversion_table, conversion_record_name]
            else:
                print("Warning: Unknown value_type for the conversion \"" + conversion_record_name + "\" in the \"" + conversion_table + "\" table. It will be skipped.")
            
            if value is None:
                if default is None:
                    if required:
                        print("Error: The conversion tag to create the \"" + conversion_record_name + "\" record in the \"" + conversion_table + "\" table did not return a value.")
                        sys.exit()
                    elif not args["--silent"]:
                        print("Warning: The non-required conversion tag to create the \"" + conversion_record_name + "\" record in the \"" + conversion_table + "\" table could not be created.")
                        continue
                else:
                    value = default
                    if not args["--silent"]:
                        print("The conversion tag to create the \"" + conversion_record_name + "\" record in the \"" + conversion_table + "\" table could not be created, and reverted to its given default value, \"" + default + "\".")
            
            # if value is None and required:
            #     print("Error: The conversion tag to create the \"" + conversion_record_name + "\" record in the \"" + conversion_table + "\" table did not return a value.")
            #     sys.exit()
            # elif value is None and not required:
            #     if not args["--silent"]:
            #         print("Warning: The non-required conversion tag to create the \"" + conversion_record_name + "\" record in the \"" + conversion_table + "\" table could not be created.")
            #     continue
            
            _nested_set(output_json, keys, value)
    
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
    
    mwtabfile.source = args["<input-JSON>"]
    validated_file, errors = mwtab.validator.validate_file(mwtabfile, verbose=True)
    
    json_save_name = args["<output-name>"] + ".json"
    with open(json_save_name,'w') as jsonFile:
        jsonFile.write(json.dumps(output_json, indent=2))
        
    mwtab_save_name = args["<output-name>"] + ".txt"
    with open(mwtab_save_name, 'w', encoding='utf-8') as outfile:
        mwtabfile.write(outfile, file_format="mwtab")




literal_regex = r"^\"(.*)\"$"


def _nested_set(dic, keys, value):
    for key in keys[:-1]:
        dic = dic.setdefault(key, {})
    dic[keys[-1]] = value


def _sort_by_getter(pair, keys):
    return [pair[1][key] for key in keys]


def handle_code_tag(input_json, conversion_table, conversion_record_name, conversion_attributes):
    """"""
    
    if import_path := conversion_attributes.get("import"):
        import_name = pathlib.Path(import_path).stem
        global_variables = globals()
        global_variables[import_name] = SourceFileLoader(import_name, import_path).load_module()
    
    if code := conversion_attributes.get("code"):
        try:
            value = eval(code)
        except Exception as error:
            print("Error: The code conversion tag to create the \"" + conversion_record_name + "\" record in the \"" + conversion_table + "\" table encountered an error while executing.")
            raise error
        
        return value
    else:
        return None



def _build_string_value(fields, conversion_table, conversion_record_name, record_name, record_attributes, required, silent):
    value = None
    for field in fields:
        ## Is the field a literal?
        if not field[1]:
            ## If the field is not a literal value and it's not in the record print an error.
            if field[0] not in record_attributes:
                if required:
                    print("Error: The conversion tag to create the \"" + conversion_record_name + "\" record in the \"" + conversion_table + "\" table matched a record in the input data, \"" + record_name + "\", that did not contain the \"" + field[0] + "\" field indicated by the tag.")
                    sys.exit()
                elif not silent:
                    print("Warning: The conversion tag to create the \"" + conversion_record_name + "\" record in the \"" + conversion_table + "\" table matched a record in the input data, \"" + record_name + "\", that did not contain the \"" + field[0] + "\" field indicated by the tag.")
                    continue
        
            if value:
                value += str(record_attributes[field[0]])
            else:
                value = str(record_attributes[field[0]])
        else:
            if value:
                value += field[0]
            else:
                value = field[0]
            
    return value




def compute_string_value(input_json, conversion_table, conversion_record_name, conversion_attributes, silent=False):
    """"""
    ## required
    if required := conversion_attributes.get("required"):
        if required.lower() == "false":
            required = False
        else:
            required = True
            
    ## default
    # default = conversion_attributes.get("default")
    # if default and (literal_match := re.match(literal_regex, default)):
    #     default = literal_match.group(1)
    
    ## override
    if value := conversion_attributes.get("override"):
        if literal_match := re.match(literal_regex, value):
            value = literal_match.group(1)
        return value
    
    ## code
    value = handle_code_tag(input_json, conversion_table, conversion_record_name, conversion_attributes)
            
    if value is not None:
        if not isinstance(value, str):
            print("Error: The code conversion tag to create the \"" + conversion_record_name + "\" record in the \"" + conversion_table + "\" table did not return a string type value.")
            sys.exit()
        
        return value
    
    ## fields
    fields = [(field, True if re.match(literal_regex, field) else False) for field in conversion_attributes["fields"]]
    has_test = False
    if test := conversion_attributes.get("test"):
        has_test = True
        split = test.split("=")
        test_field = split[0].strip()
        test_value = split[1].strip()
    
    ## for_each
    if for_each := conversion_attributes.get("for_each"):
        if for_each.lower() == "true":
            for_each = True
        else:
            for_each = False
    
    if for_each:
        delimiter = conversion_attributes.get("delimiter", "")
        if delimiter and (literal_match := re.match(literal_regex, delimiter)):
            delimiter = literal_match.group(1)
        
        if has_test:
            table_records = {record:record_attributes for record, record_attributes in input_json[conversion_attributes["table"]].items() if test_field in record_attributes and record_attributes[test_field] == test_value}
        else:
            table_records = input_json[conversion_attributes["table"]]
            
        if not table_records:
            if required:
                print("Error: The conversion tag to create the \"" + conversion_record_name + "\" record in the \"" + conversion_table + "\" table did not match any records in the input data.")
                sys.exit()
            else:
                return None
        
        if sort_by := conversion_attributes.get("sort_by"):
            table_records = dict(sorted(table_records.items(), key = lambda pair: _sort_by_getter(pair, sort_by), reverse = conversion_attributes["sort_order"] == "descending"))
            ## table_records used to be a list of dicts and this was the sort, leaving it here in case it is needed.
            # table_records = sorted(table_records, key = operator.itemgetter(*sort_by), reverse = conversion_attributes["sort_order"] == "descending")
        
        value_for_each_record = []
        for record_name, record_attributes in table_records.items():
            value = _build_string_value(fields, conversion_table, conversion_record_name, record_name, record_attributes, required, silent)
            if value:
                value_for_each_record.append(value)
        
        joined_string = delimiter.join(value_for_each_record)
        if joined_string:
            return joined_string
        else:
            return None
    
    ## record_id
    if conversion_attributes.get("record_id"):
        record_attributes = input_json[conversion_attributes["table"]][conversion_attributes["record_id"]]
        record_name = conversion_attributes["record_id"]
    elif has_test:
        for record_name, record_attributes in input_json[conversion_attributes["table"]].items():
            if test_field in record_attributes and record_attributes[test_field] == test_value:
                break
    else:
        record_name, record_attributes = list(input_json[conversion_attributes["table"]].items())[0]
    
    value = _build_string_value(fields, conversion_table, conversion_record_name, record_name, record_attributes, required, silent)
            
    return value

                
                
    
def compute_matrix_value(input_json, conversion_table, conversion_record_name, conversion_attributes):
    """"""
    
    value = handle_code_tag(input_json, conversion_table, conversion_record_name, conversion_attributes)
            
    if value is not None:
        if not isinstance(value, list) or not all([isinstance(record, dict) for record in value]):
            print("Error: The code conversion tag to create the \"" + conversion_record_name + "\" record in the \"" + conversion_table + "\" table did not return a matrix type value.")
            sys.exit()
        
        return value
        
    ## fields_to_headers
    if fields_to_headers := conversion_attributes.get("fields_to_headers"):
        if fields_to_headers.lower() == "true":
            fields_to_headers = True
        else:
            fields_to_headers = False
            
    has_test = False
    if test := conversion_attributes.get("test"):
        has_test = True
        split = test.split("=")
        test_field = split[0].strip()
        test_value = split[1].strip()
    
    exclusion_headers = conversion_attributes.get("exclusion_headers", [])
    
    ## TODO Should there be an option so that headers are not required to be in the input data?
    headers = []
    if conversion_attributes.get("headers"):
        for pair in conversion_attributes["headers"]:
            split = pair.split("=")
            output_key = split[0].strip()
            input_key = split[1].strip()
            
            if new_output_key := re.match(literal_regex, output_key):
                output_key = new_output_key.group(1)
                output_key_is_literal = True
            else:
                output_key_is_literal = False
            
            if new_input_key := re.match(literal_regex, input_key):
                input_key = new_input_key.group(1)
                input_key_is_literal = True
            else:
                input_key_is_literal = False
            
            headers.append({"output_key":output_key, "output_key_is_literal": output_key_is_literal, 
                            "input_key":input_key, "input_key_is_literal": input_key_is_literal})
    
    ## TODO think about changing optional_headers to inclusion_headers and having an option about printing warnings if the headers aren't there.
    optional_headers = conversion_attributes.get("optional_headers", [])
    
    if has_test:
        table_records = {record:record_attributes for record, record_attributes in input_json[conversion_attributes["table"]].items() if test_field in record_attributes and record_attributes[test_field] == test_value}
    else:
        table_records = input_json[conversion_attributes["table"]]
        
    if sort_by := conversion_attributes.get("sort_by"):                
        table_records = dict(sorted(table_records.items(), key = lambda pair: _sort_by_getter(pair, sort_by), reverse = conversion_attributes["sort_order"] == "descending"))

        
    if collate := conversion_attributes.get("collate"):
        ## TODO think about whether to do collate.strip() here to remove spaces.
        ## TODO make sure there is validation that checks that headers are unique.
        records = {}
        for record, record_attributes in table_records.items():
            collate_key = record_attributes[collate]
            
            if collate_key not in records:
                records[collate_key] = {}
            
            for header in headers:
                if header["output_key_is_literal"] and header["input_key_is_literal"]:
                    records[collate_key][header["output_key"]] = header["input_key"]
                elif header["output_key_is_literal"] and not header["input_key_is_literal"]:
                    if header["input_key"] not in record_attributes:
                        print("Error: The headers conversion tag to create the \"" + conversion_record_name + "\" matrix in the \"" + conversion_table + "\" table has an input key, \"" + header["input_key"] + "\", that does not exist in the record, \"" + record + "\", of the input table, \"" + conversion_attributes["table"] + "\".")
                        sys.exit()
                    if header["output_key"] in records[collate_key] and record_attributes[header["input_key"]] != records[collate_key][header["output_key"]]:
                        print("Warning: When creating the \"" + conversion_record_name + "\" matrix for the \"" + conversion_table + "\" table different values for the output key, \"" + header["output_key"] + "\", were found. Only the last value will be used.")
                    records[collate_key][header["output_key"]] = record_attributes[header["input_key"]]
                elif not header["output_key_is_literal"] and header["input_key_is_literal"]:
                    if header["output_key"] not in record_attributes:
                        print("Error: The headers conversion tag to create the \"" + conversion_record_name + "\" matrix in the \"" + conversion_table + "\" table has an output key, \"" + header["output_key"] + "\", that does not exist in the record, \"" + record + "\", of the input table, \"" + conversion_attributes["table"] + "\".")
                        sys.exit()
                    records[collate_key][record_attributes[header["output_key"]]] = header["input_key"]
                elif not header["output_key_is_literal"] and not header["input_key_is_literal"]:
                    if header["input_key"] not in record_attributes:
                        print("Error: The headers conversion tag to create the \"" + conversion_record_name + "\" matrix in the \"" + conversion_table + "\" table has an input key, \"" + header["input_key"] + "\", that does not exist in the record, \"" + record + "\", of the input table, \"" + conversion_attributes["table"] + "\".")
                        sys.exit()
                    if header["output_key"] not in record_attributes:
                        print("Error: The headers conversion tag to create the \"" + conversion_record_name + "\" matrix in the \"" + conversion_table + "\" table has an output key, \"" + header["output_key"] + "\", that does not exist in the record, \"" + record + "\", of the input table, \"" + conversion_attributes["table"] + "\".")
                        sys.exit()
                    if record_attributes[header["output_key"]] in records[collate_key] and record_attributes[header["input_key"]] != records[collate_key][record_attributes[header["output_key"]]]:
                        print("Warning: When creating the \"" + conversion_record_name + "\" matrix for the \"" + conversion_table + "\" table different values for the output key, \"" + record_attributes[header["output_key"]] + "\", were found. Only the last value will be used.")
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
        for record, record_attributes in table_records.items():
            temp_dict = {}            
            for header in headers:
                if header["output_key_is_literal"] and header["input_key_is_literal"]:
                    temp_dict[header["output_key"]] = header["input_key"]
                elif header["output_key_is_literal"] and not header["input_key_is_literal"]:
                    if header["input_key"] not in record_attributes:
                        print("Error: The headers conversion tag to create the \"" + conversion_record_name + "\" matrix in the \"" + conversion_table + "\" table has an input key, \"" + header["input_key"] + "\", that does not exist in the record, \"" + record + "\", of the input table, \"" + conversion_attributes["table"] + "\".")
                        sys.exit()
                    temp_dict[header["output_key"]] = record_attributes[header["input_key"]]
                elif not header["output_key_is_literal"] and header["input_key_is_literal"]:
                    if header["output_key"] not in record_attributes:
                        print("Error: The headers conversion tag to create the \"" + conversion_record_name + "\" matrix in the \"" + conversion_table + "\" table has an output key, \"" + header["output_key"] + "\", that does not exist in the record, \"" + record + "\", of the input table, \"" + conversion_attributes["table"] + "\".")
                        sys.exit()
                    temp_dict[record_attributes[header["output_key"]]] = header["input_key"]
                elif not header["output_key_is_literal"] and not header["input_key_is_literal"]:
                    if header["input_key"] not in record_attributes:
                        print("Error: The headers conversion tag to create the \"" + conversion_record_name + "\" matrix in the \"" + conversion_table + "\" table has an input key, \"" + header["input_key"] + "\", that does not exist in the record, \"" + record + "\", of the input table, \"" + conversion_attributes["table"] + "\".")
                        sys.exit()
                    if header["output_key"] not in record_attributes:
                        print("Error: The headers conversion tag to create the \"" + conversion_record_name + "\" matrix in the \"" + conversion_table + "\" table has an output key, \"" + header["output_key"] + "\", that does not exist in the record, \"" + record + "\", of the input table, \"" + conversion_attributes["table"] + "\".")
                        sys.exit()
                    temp_dict[record_attributes[header["output_key"]]] = record_attributes[header["input_key"]]
            
            if fields_to_headers:
                temp_dict.update({field:value for field, value in record_attributes.items() if field not in exclusion_headers})
            else:
                for header in optional_headers:
                    if header in record_attributes:
                        temp_dict[header] = record_attributes[header]
                    
            records.append(temp_dict)
    
    if not records:
        return None
    return records



    



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
                additional_sample_data["lineage" + str(lineage_count) + "_" + field] = str(field_value[0]) if isinstance(field_value, list) and len(field_value) == 1 else str(field_value)
                
                if field in factor_fields and factor_fields[field]["name"] not in factors:
                    if isinstance(field_value,str) and field_value in factor_fields[field]["allowed_values"]:
                        factors[factor_fields[field]["name"]] = field_value
                    elif isinstance(field_value,list) and (field_values := [value for value in field_value if value in factor_fields[field]["allowed_values"]]):
                        factors[factor_fields[field]["name"]] = field_values
                    
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
                           additional_sample_data["lineage" + str(lineage_count) + "_" + field] = str(field_value[0]) if isinstance(field_value, list) and len(field_value) == 1 else str(field_value)
                       
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
                    factors[factor_fields[field]["name"]] = field_values
                    
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




# input_json["entity"] = {}
# for sample_name, sample_attributes in input_json["sample"].items():
#     input_json["entity"][sample_name] = sample_attributes
#     input_json["entity"][sample_name]["type"] = "sample"
# for subject_name, subject_attributes in input_json["subject"].items():
#     input_json["entity"][subject_name] = subject_attributes
#     input_json["entity"][subject_name]["type"] = "subject"

# input_json["factor"] = \
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





