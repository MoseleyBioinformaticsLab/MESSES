# -*- coding: utf-8 -*-
"""
Convert JSON data to another JSON format.

Usage:
    messes convert mwtab (ms | nmr | nmr_binned) <input_JSON> <output_name> [--update <conversion_directives> | --override <conversion_directives>] [--silent]
    messes convert isa <input_JSON> <output_name> [--update <conversion_directives> | --override <conversion_directives>] [--silent] [--json-config-dir <config_directory>] [--tab-config-dir <config_directory>]
    messes convert save-directives mwtab (ms | nmr | nmr_binned) <output_filetype> [<output_name>]
    messes convert save-directives isa <output_filetype> [<output_name>]
    messes convert generic <input_JSON> <output_name> <conversion_directives> [--silent]
    messes convert --help
    
    <conversion_directives> - can be a JSON, csv, xlsx, or Google Sheets file. If xlsx or Google Sheets the default sheet name to read in is #convert, 
                              to specify a different sheet name separate it from the file name with a colon ex: file_name.xlsx:sheet_name.
                              
    <output_filetype> - "json", "xlsx", or "csv"

Options:
    -h, --help                           - show this screen.
    -v, --version                        - show version.
    --silent                             - silence all warnings.
    --update <conversion_directives>     - conversion directives that will be used to update the built-in directives for the format.
                                           This is intended to be used for simple changes such as updating the value of 
                                           the analysis ID. You only have to specify what needs to change, any values 
                                           that are left out of the update directives won't be changed. If you need to remove 
                                           directives then use the override option.
    --override <conversion_directives>   - conversion directives that will be used to override the built-in directives for the format.
                                           The built-in directives will not be used and these will be used instead.
                                           
ISA Specific Options:
    --json-config-dir <config_directory> - the directory where configuration files are stored to run extra validation on the created ISAJSON.
    --tab-config-dir <config_directory>  - the directory where configuration files are stored to run extra validation on the created ISATab.
    
    

The general command structure for convert is convert <format> which will convert an input JSON file over to the supported format. 
The outputs of these commands will save both the JSON conversion and the final format file.

The generic command is the same as the supported formats except the user is required to input conversion directives specifying how to 
convert the input JSON to the desired output JSON. Only an output JSON is saved.

The save-directives command is used to print the default conversion directives used by convert for any of the supported formats. <output-filetype> 
can be one of "json", "xlsx", or "csv". The file is saved as "format_conversion_directives.ext" where ".ext" is replaced with ".json", ".xlsx", 
or ".csv" depending on the value of <output-format>, unless <output_name> is given.

"""

import re
import sys
import pathlib
import json
import io
import inspect
import os

import pandas
import docopt

from messes.extract import extract
from messes import __version__
from messes.convert import mwtab_conversion_directives
from messes.convert import isajson_conversion_directives
from messes.convert import directive_functions
from messes.convert import mwtab_functions
from messes.convert import isa_functions
from messes.convert import helper_functions
from messes.convert import user_input_checking
from messes.convert import convert_schema
from messes.convert import initializations
from messes.convert import finalizations


## Add some real examples of nested directives from ISA once that is done.

## Add measurement%transformation and measurement%normalization protocol types. Allows us to handle those for ISA. Require parents and that parent be a measurement type. Require the entity.id to be the same.
## Try just concatenating fields to condense a list of protocols into 1, look for protocol%order field to determine order, if not there assume the order is correct.
## For assays find the storage%measurement protocol and work backward to the first collection to find where to start the assay.
##   storage%measurement is simply a protocol that connects an entity to a measurement protocol. 
##   I can't remember now exactly what we said it should have. I know I just wanted to copy the measurement protocol wholesale, 
##   but I think we settled on having a protocol with some pointers instead, but I can't remember the exact details.
##   Changed this to the dummy measurements implementation described below.

## Dummy measurements for ISA. Create new proxy-ICMS etc. measurements and have 
## simple measurement entities that just have an entity.id and protocol.id.
## This is better than storage%measurement in my opinion because it at least stays 
## consistent with the workflow already developed for MESSES.

## Possibly add a protocol%sequence type protocol where you can specify protocols that are performed 
## together in a sequence. Would sort of replace or be another way to list protocols on an entity. 
## Hunter was more keen than I on this. I think it could be done through just the PDS, but I'm not sure. 
## I would need to take a swing at it and then get back with Hunter to flesh it out.

## Possibly add a "linked" field or some other name that would indicate whether a protocol 
## was being placed on the input or the output entity. Hunter was more keen on this than 
## me. Since it isn't a malleable property and is tied to the protocol type it only opens 
## up the user to be able to make a mistake and requires additional validation. I think 
## either putting inputs and output on the protocol or "to_protocol" "from_protocol" on 
## entitites is better.

## Should all of the .get() checks specifically check "is None"? A blank string or 
## empty list will seem like the field isn't there when it actually is. Specifically 
## for nested directive argument passing it is important because it specifically has 
## to not be in the directive to be ignored.

## All records might need to have study.id and/or assay.id fields for ISA. I think 
## this might also mean that study.id needs to be a list and then we need to modify 
## "test" field in directives so that list fields are converted to "in" instead of "==".
## For example, study.id=id would need to be "record["id"] in study.id".

## For ISA have 2 options: --compute_studies and --multiple_studies. The default will 
## assume that there is 1 study and 1 assay in the data. --multiple_studies indicates 
## that there are multiple studies/assays and that will change which set of directives to 
## use and require study and assay ID fields for records. If --compute_studies is used 
## then we will first compute assays and studies based on sample ancestry and add the 
## IDs to the records ourselves. We can determine studies and assays by computing sample 
## ancestries, determining protocol sequences from those, and then for each unique protocol 
## sequence that is 1 new assay. Then you remove the assay part of the protocol sequence 
## and for each unique truncated sequence that is 1 new study.

## Add a special calling record syntax to pass the while record dict "^.*".

## Double check that validation checks for loops in sample lineage, i.e. no sample is its own ancestor.

## Add documentation explaining how mwtab uses conversion directives to do the complicated 
## part (subject-sample-factors) as needed, but ISA does a preprocessing step to add 
## fields to the records first so simple conversion directives can be used.

## Add a check in validate to make sure measurements that have a parent_id have the same entity.id as their parent.
## For ISA specifically, also look for "assay_id" on measurements and make sure parents have the same ID.
## "assay_id" must be a string, not a list, measurements can't be in 2 assays.

## Modify validate to propagate ancestor attributes to children for each table, could be errors because someone relied on inheritance from ancestors.
## Can use _propagate_ancestor_attributes in isa_functions

## Add check in validate for ISA to make sure all entities have a study.id after progagting them from children to ancestors.
# message = (f"Error:  Not all entities in the \"{entity_table_name}\" table have a "
#            f"\"{study_key}\" attribute, even after progagating them through lineages. "
#            "The following entities are affected:")

## Add check to validate so study.id is required on factors, unless there is one study, then propagate it everywhere.

## implement assays into the study table by adding a "type" field and requiring a parent_id.
## "type" is not required, but will be added in convert initializations.

## Add checks in validate to check fields with %isa_fieldtype are the correct 
## values, parameter or component for protocol and characteristic or factor for entities.

## Add a check on studies and project to look for "filename" for ISA and check that it starts with "i_", "s_", "a_", etc.

## Make sure validate checks that "data_files" on protocol is a list and "data_files%entity_id" and "data_files$isa_type"
## make sure the lists are the same size as well. And "data_files$isa_type" is one of "Raw Data File", "Derived Data File", or "Image File"

## All of the built-ins that look for parameters, componenets, etc assume the field is a string, so add a check 
## that validates any fields pointed to by {field_name}%isa_fieldtype are strings.
## Add an example to show the user how they could modify the conversion directives to create a list of components, parameters, etc
## instead of adding attributes to fields. Maybe even create a whole new set that assumes they are in lists.

## Due to the initializations adding things to the input_json there should probably be 2 validations. 
## One validation if the user intends to use the initializations and another if they don't.
## Since the directives rely on certain fields that are added in the initializations if a user 
## intends not to use the initialization the validation needs to make sure those fields are there.

## Change the validation message for matrix directives. Instead of requiring "code" or "headers" 
## it has been changed to be "code", "headers", "optional_headers", or "fields_to_headers". 
## The validation message handler needs to look for the new error and print a better one if none of these 
## keywords are present.
## ValidationError: {'value_type': 'section_matrix', 'required': 'False', 'table': 'ontology_sources', 'default': []} is not valid under any of the given schemas
## Failed validating 'anyOf' in schema['additionalProperties']['additionalProperties']['allOf'][1]['then']:

## Add documentation explaining the extra people, pubication, and ontology_source tables for ISA.


BASE_DIR = os.path.dirname(__file__)
JSON_CONFIG_PATH = os.path.join(BASE_DIR, "isajson_configs")

def main() :
    args = docopt.docopt(__doc__, version=__version__)
    input_json_filepath = args["<input_JSON>"]
    silent = args["--silent"]
    isatab_config_dir = args["--tab-config-dir"] if args["--tab-config-dir"] else ""
    isajson_config_dir = args["--json-config-dir"] if args["--json-config-dir"] else ""
    
    ## Validate args.
    # user_input_checking.additional_args_checks(args)
    
    #####################
    ## Determine conversion format to set initializations, conversion_directives, and finalizations.
    #####################
    supported_formats_and_sub_commands = {"mwtab":{"ms": {"directives": mwtab_conversion_directives.ms_directives,
                                                          "initialization": initializations.mwtab.initialization,
                                                          "finalization": finalizations.mwtab.finalization},
                                                   "nmr": {"directives": mwtab_conversion_directives.nmr_directives,
                                                           "initialization": initializations.mwtab.initialization,
                                                           "finalization": finalizations.mwtab.finalization}, 
                                                   "nmr_binned": {"directives": mwtab_conversion_directives.nmr_binned_directives,
                                                                  "initialization": initializations.mwtab.initialization,
                                                                  "finalization": finalizations.mwtab.finalization}},
                                          "isa":{"": {"directives": isajson_conversion_directives.directives,
                                                      "initialization": initializations.isa.initialization,
                                                      "finalization": finalizations.isa.finalization}},
                                          "generic":{"": {"directives": {},
                                                          "initialization": initializations.generic.initialization,
                                                          "finalization": finalizations.generic.finalization}}}
    # conversion_directives = {}
    # format_under_operation = "generic"
    for supported_format, sub_commands in supported_formats_and_sub_commands.items():
        if args[supported_format]:
            format_under_operation = supported_format
            if len(sub_commands) > 1:
                sub_command = [sub_command for sub_command in sub_commands if args[sub_command]][0]
            else:
                sub_command = ""
            conversion_directives = sub_commands[sub_command]["directives"]
            initialization = sub_commands[sub_command]["initialization"]
            finalization = sub_commands[sub_command]["finalization"]
            ## The argument names must correspond to variables in main available when finalization is ran.
            finalization_argument_names = inspect.getfullargspec(finalization).args
            break
    
    ##########################
    ## Read in conversion directives from a file if necessary.
    ##########################
    if filepath := next((arg for arg in [args["<conversion_directives>"], args["--update"], args["--override"]] if arg is not None), False):
        if re.search(r".*(\.xls[xm]?|\.csv)", filepath) or extract.TagParser.isGoogleSheetsFile(filepath):
            default_sheet_name = False
            if (reMatch := re.search(r"^(.*\.xls[xm]?):(.*)$", filepath)):
                filepath = reMatch.group(1)
                sheet_name = reMatch.group(2)
            elif re.search(r"\.xls[xm]?$", filepath):
                sheet_name = "#convert"
                default_sheet_name = True
            elif (reMatch := re.search(r"docs.google.com/spreadsheets/d/([^/]*)/[^:]*$", filepath)):
                filepath = "https://docs.google.com/spreadsheets/d/" + reMatch.group(1) + "/export?format=xlsx"
                sheet_name = "#convert"
                default_sheet_name = True
            elif (reMatch := re.search(r"docs.google.com/spreadsheets/d/([^/]*)/.*:(.*)$", filepath)):
                filepath = "https://docs.google.com/spreadsheets/d/" + reMatch.group(1) + "/export?format=xlsx"
                sheet_name = reMatch.group(2)
            tagParser = extract.TagParser()
            ## In order to print error messages correctly we have to know if loadSheet printed a message or not, so temporarily replace stderr.
            old_stderr = sys.stderr
            sys.stderr = buffer = io.StringIO()
            try:
                if worksheet_tuple := tagParser.loadSheet(filepath, sheet_name, isDefaultSearch=default_sheet_name):
                    tagParser.parseSheet(*worksheet_tuple)
                    update_conversion_directives = tagParser.extraction
                    sys.stderr = old_stderr
                else:
                    sys.stderr = old_stderr
                    if buffer.getvalue():
                        ## Have to trim the extra newline off the end of buffer.
                        print(buffer.getvalue()[0:-1], file=sys.stderr)
                    elif default_sheet_name:
                        print("Error:  No sheet name was given for the file, so the default name "
                              "of #convert was used, but it was not found in the file.", file=sys.stderr)
                    sys.exit()
            except Exception as e:
                sys.stderr = old_stderr
                raise e
        
        elif re.match(r".*\.json$", filepath):
            with open(filepath, 'r') as jsonFile:
                update_conversion_directives = json.load(jsonFile)
        
        else:
            print("Error:  Unknown file type for the conversion directives file.", file=sys.stderr)
            sys.exit()
            
        if args["--update"]:
            helper_functions._update(conversion_directives, update_conversion_directives)
        else:
            conversion_directives = update_conversion_directives
    
    ##########################
    ## Handle save-directives command.
    ##########################
    if args["save-directives"]:
        if args["<output_name>"]:
            if re.match(r".*\." + args["<output_filetype>"] + "$", args["<output_name>"]):
                save_name = args["<output_name>"]
            else:
                save_name = args["<output_name>"] + "." + args["<output_filetype>"]
        else:
            if sub_command:
                save_name = format_under_operation + "_" + sub_command + "_conversion_directives." + args["<output_filetype>"]
            else:
                save_name = format_under_operation + "_conversion_directives." + args["<output_filetype>"]
        
        if args["<output_filetype>"] == "json":
            with open(save_name,'w') as jsonFile:
                jsonFile.write(json.dumps(conversion_directives, indent=2))
        elif args["<output_filetype>"] == "xlsx":
            table_to_save = directives_to_table(conversion_directives)
            table_to_save.to_excel(save_name, index=False, header=False)
        elif args["<output_filetype>"] == "csv":
            table_to_save = directives_to_table(conversion_directives)
            table_to_save.to_csv(save_name, index=False, header=False)
        else:
            print("Error:  Unknown output filetype.", file=sys.stderr)
            
        sys.exit()
        
    
    #######################
    ## Validate conversion directives.
    #######################
    user_input_checking.validate_conversion_directives(conversion_directives, convert_schema.directives_schema)
    
    
    ## Read in files.
    if not pathlib.Path(input_json_filepath).exists():
        print(f"Error:  The value entered for <input_JSON>, {input_json_filepath}, is not a valid file path or does not exist.", file=sys.stderr)
        sys.exit()
    try:
        with open(input_json_filepath, 'r') as jsonFile:
            input_json = json.load(jsonFile)
    except Exception as e:
        print(f"\nError:  An error was encountered when trying to read in the <input_JSON>, {input_json_filepath}.\n", file=sys.stderr)
        raise e
    
    
    #####################
    ## Run initializations
    #####################
    input_json = initialization(input_json)
    # with open('C:/Users/Sparda/Desktop/Moseley Lab/Code/MESSES/examples/Full_isa_example/MS/extract/initialization_output.json','w') as jsonFile:
    #     jsonFile.write(json.dumps(input_json, indent=2))
    
    
    #####################
    ## Generate new JSON.
    #####################
    output_json = {}
    for conversion_table, conversion_records in conversion_directives.items():
        
        if "%" in conversion_table:
            continue
        
        table_value = directive_functions._determine_directive_table_value(input_json, 
                                                                           conversion_table,  
                                                                           conversion_directives,
                                                                           None, 
                                                                           None, 
                                                                           None, 
                                                                           None,
                                                                           silent)
        
        output_json[conversion_table] = table_value
        
    
    
    #########################
    ## Save the generated json.
    #########################
    json_save_name = args["<output_name>"] + ".json"
    with open(json_save_name,'w') as jsonFile:
        jsonFile.write(json.dumps(output_json, indent=2))
    
    
    #####################
    ## Run finalizations
    #####################
    finalization_arguments = {}
    for variable_name in finalization_argument_names:
        finalization_arguments[variable_name] = locals()[variable_name]
    finalization(**finalization_arguments)
    




############################
## save-directives functions
############################
    
def directives_to_table(conversion_directives: dict) -> pandas.core.frame.DataFrame:
    """Convert conversion directives to a tagged table form.
    
    Args:
        conversion_directives: the conversion directives to transform.
        
    Returns:
        a pandas DataFrame that can be saved to csv or xlsx.
    """
    
    df_list = []
    for table, records in conversion_directives.items():
        ## For tables with no records add a simple header and blank row.
        if not records:
            rows = []
            rows.append(["#tags", "#" + table + ".id"])
            rows.append(["",""])
            df_list.append(pandas.DataFrame(rows))
        matched_keys = set()
        for record_name, record_fields in records.items():
            if record_name in matched_keys:
                continue
            records_with_matching_fields = [record_name2 for record_name2, record_fields2 in records.items() if record_fields.keys() == record_fields2.keys()]
            matched_keys.update(records_with_matching_fields)
            
            filtered_fields = record_fields.keys() - ["id"]
            filtered_fields = sorted(filtered_fields)
            rows = []
            rows.append(["#tags", "#" + table + ".id"])
            blank_row = ["",""]
            for field in filtered_fields:
                if isinstance(record_fields[field], list):
                    rows[0].append("*#." + field)
                else:
                    rows[0].append("#." + field)
                blank_row.append("")
                    
            for matched_record_name in records_with_matching_fields:
                row = ["", matched_record_name]
                for field in filtered_fields:
                    value = records[matched_record_name][field]
                    if isinstance(value, list):
                        row.append(",".join(value))
                    else:
                        row.append(value)
                        
                rows.append(row)
            rows.append(blank_row)
            df_list.append(pandas.DataFrame(rows))
            
    return pandas.concat(df_list).fillna("")
            
                    
                
                
# str_directive_fields = ["id", "value_type", "override", "code", "import", "table", "for_each", "fields", "test", "required", "delimiter", "sort_by", "sort_order", "record_id", "default"]
# matrix_directive_fields = ["id", "value_type", "code", "import", "table",  "test", "required", "sort_by", "sort_order", "headers", "collate", "exclusion_headers", "optional_headers", "fields_to_headers", "values_to_str", "default"]
# section_directive_fields = ["value_type", "code", "import", "required", "built-in", "table", "test", "for_each", "sort_by", "sort_order", "record_id", "default"]


