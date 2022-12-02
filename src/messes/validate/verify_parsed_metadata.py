#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
 verify_parsed_metadata.py
    Verify metadata parsed by extract_metadata.py by confirming the required attributes and their types.
    
 Usage: verify_parsed_metadata.py <parsed_metadata_json> <controlled_vocabulary_json> [options]
 
	parsed_metadata_json - json file output from extract_metadata, extracted from a metadata file.
	controlled_vocabulary_json - json file output from extract_metadata, extracted from a controlled vocabulary file.
    options:
        -s - Silent mode. Warnings are not printed.
        -c output_filename - Clean the input JSON of any records with errors and output a new JSON to output_filename.
    
"""


import json
import sys
import re
import copier
import itertools
import copy
from io import StringIO



## Tables required in the controlled vocabulary.
cv_required_tables = ("parent_protocol", "tagfield", "tagfield_scope", "tagfield_attribute")
## Tables required in the parsed metadata.
pm_required_tables = ("subject", "sample", "factor", "project", "study", "protocol")

## Set options to false initially.
silent_mode = False
clean_output = False

## Create a dictionary of records to remove from the input JSON.
records_to_remove = {}



def indexes_of_duplicates_in_list(list_of_interest, value_to_find):
    """Returns a list of all of the indexes in list_of_interest where the value equals value_to_find."""

    current_index = 0
    indexes = []

    while True:
        try:
            next_index = list_of_interest.index(value_to_find, current_index)            
    
        except ValueError:
            break
        
        else:
            indexes.append(next_index)
            current_index = next_index + 1
        
    return indexes



def iterate_string_or_list(str_or_list):
    """If str_or_list is a string then make it into a list and return the items for looping. 
    If str_or_list is a list then return the items for looping."""
    if isinstance(str_or_list, list):
        return str_or_list
    else:
        return [str_or_list]




def is_it_a_num(possible_num) :
    """ Determines whether the input string is a number or not. Returns True if it is, False otherwise. """
    try :
        float(possible_num)
        
    except ValueError :
        return False
    
    return True


def record_error_handler(JSON_name, table_name, record_name, message):
    """Prints message to the screen and adds the record to the dictionary of records to delete for 
    the clean up option. The record is only added if the message is an error message and the record 
    is from the metadata JSON.
    If message has "Warning" in it and silent_mode is on (True) then message won't be printed."""
    
    global records_to_remove
    
    ## Don't print the message if silent mode is on and the message is a warning.
    if silent_mode and re.match("Warning", message):
        return
    
    print(message)
    
    ## If the record is from the metadata then it needs to be added to the list of records to remove.
    ## If the table is already in the dictionary of records to remove then just add the record, 
    ## else add the table name as a key and the record as a list to that key.
    if JSON_name == "metadata":
        if table_name in records_to_remove:
            if not record_name in records_to_remove[table_name]:
                records_to_remove[table_name].append(record_name)
        else:
            records_to_remove[table_name] = [record_name]
            
            
            
            
            
def JSON_clean_up(parsed_metadata, controlled_vocabulary):
    """Removes all of the records that produced an error and checks the resulting metadata again.
    If the resulting metadata produces errors then it cannot be cleaned. Returns False if resulting
    metadata is not clean and True if it is."""
    
    global silent_mode
    
    for table_name, records_list in records_to_remove.items():
        for record_name in records_list:
            del parsed_metadata[table_name][record_name]
            
            
    ## Redirect the output so the user doesn't see extra error messages, and run the checks on inheritance again.
    ## Run the checks with silent mode enabled so they don't print warnings.
    ## If the functions produce any messages then there were errors and the metadata cannot be cleaned.
    silent_mode = True
    real_stdout = sys.stdout
    redirect_stdout = StringIO()
    try:
        sys.stdout = redirect_stdout
        JSON_id_check(parsed_metadata, "metadata")
        protocol_lineage_check(parsed_metadata, controlled_vocabulary)
        
    finally:
        sys.stdout = real_stdout
        output_string = redirect_stdout.getvalue()
        redirect_stdout.close()
        silent_mode = False
        
        
    if len(output_string) > 0:
        print("The metadata could not be cleaned since removing malformed records removed the parents of some protocols or sample/subjects.")
        return False
    else:
        return True




def table_fields_and_allowed_values_check(JSON_file, JSON_name, table_name, fields_and_allowed_values):
    """Loops over the table named by the table parameter in the JSON_file and checks that each record in
    the table has the fields in the dictionary fields_and_allowed_values, depending on the scope_type of the field.
    Also checks to make sure the field value is the correct type according to its validationCode.
    
    fields_and_allowed_values is a dictionary where the keys are required fields and the values are
    a dictionary with the allowed values, validationCode, and scope_type of those fields. The key to the 
    allowed values is "allowed_values", the key to the validationCode is "validationCode", and the key to 
    the scope_type is "scope_type". 
    
    scope_type - list with possible values of "ignore", "optional", "warning", and "blank". "ignore" requires 
                 the record to have the field. "optional" indicates that the record doesn't have to have the
                 field. If both "ignore" and "optional" are in the list then "ignore" takes precedent. 
                 "warning" indicates that messages pertaining to this field should be printed as warnings
                 instead of errors. "blank" indicates that the record can have blank values.
                 
    allowed_values - list of all possible values the field can be. If the range of values are not finite or 
                     you do not want to check against allowed_values then leave the list empty.
                 
    validationCode - list with possible values of "text", "numeric", "list_optional" and "list". "text" 
                     indicates that the field value's type should be text, or not a number. "numeric" 
                     indicates that the field value's type should be a number. If both "text" and "numeric" 
                     are in the list then "text" takes precedent. If the value can be both types then neither 
                     "text" nor "numeric" should be in the list. "list_optional" indicates that the field can 
                     be either a list field or a regular field. "list" indicates that the field should be a 
                     list field. If neither "list" nor "list_optional" are present then the field can not be a 
                     list field.
    
    Ex.
    
    fields_and_allowed_values = {"validationCode" : {"allowed_values" : ["text", "numeric"],
                                                     "validationCode" : ["text", "list"],
                                                     "scope_type" : ["ignore"]}, 
                                 "protocol.id" : {"allowed_values" : [],
                                                  "validationCode : ["text"],
                                                  "scope_type" : ["ignore"]},
                                 "parentID" : {"allowed_values" : [],
                                               "validationCode" : ["text"],
                                               "scope_type" : ["ignore", "blank"]}}
    
    To print a warning instead of an error include "warning" in the scope_type.
    
    JSON_name is the name of the JSON so the error message is informative."""
    
    if not table_name in JSON_file:
        return
    
    for record_name, record_fields in JSON_file[table_name].items():
        for field_name, AV_VC_ST in fields_and_allowed_values.items():
            
            allowed_values = AV_VC_ST["allowed_values"]
            scope_type = AV_VC_ST["scope_type"]
            validationCode = AV_VC_ST["validationCode"]
            
            
            ## Look for the possible flags in the list of allowed values.
            if "warning" in scope_type:
                Warn_or_Error = "Warning"
            else:
                Warn_or_Error = "Error"
                
            if "blank" in scope_type:
                blanks_allowed = True
            else:
                blanks_allowed = False
                
            if len(allowed_values) > 0:
                ## If allowed values is a list of 1  and that value is blank then the allowed_values field is actually blank,
                ## so this record doesn't actually have allowed values.
                if len(allowed_values) == 1 and "".join(allowed_values[0].split()) == "":
                    has_AV = False
                else:
                    has_AV = True
            else:
                has_AV = False
                
            
            if field_name in record_fields:
                field_value = record_fields[field_name]
            elif "ignore" in scope_type:
                record_error_handler(JSON_name, table_name, record_name, Warn_or_Error + ":  The record " + record_name + " in the " + table_name + " table of the " + JSON_name + " does not have a field for \"" + field_name + "\".")
                continue
            else:
                continue

    ## If blank is not in the list of allowed values then check if there are any blank values, 
        ## If the value of the field is a list it has to be handled special.
            if isinstance(field_value, list) :
                
                if not "list" in validationCode and not "list_optional" in validationCode:
                    record_error_handler(JSON_name, table_name, record_name, Warn_or_Error + ":  The record " + record_name + " in the " + table_name + " table of the " + JSON_name + " has a field, " + field_name + ", that is a list field, but it should not be according to its validationCode.")

                
                if "text" in validationCode and any(is_it_a_num(value) for value in field_value):
                    record_error_handler(JSON_name, table_name, record_name, Warn_or_Error + ":  The record " + record_name + " in the " + table_name + " table of the " + JSON_name + " has one or more numerical values in the list for field, " + field_name + ", but they should all be text values.")
            
                elif "numeric" in validationCode and any(not is_it_a_num(value) and not "".join(value.split()) == "" for value in field_value):
                    record_error_handler(JSON_name, table_name, record_name, Warn_or_Error + ":  The record " + record_name + " in the " + table_name + " table of the " + JSON_name + " has one or more text values in the list for field, " + field_name + ", but they should all be numerical values.")

            ## Since the field value is a list type we have to be able to print a message if 
            ## there are blank values and incorrect values at the same time.
                if not blanks_allowed and any("".join(value.split()) == "" for value in field_value) :
                    record_error_handler(JSON_name, table_name, record_name, Warn_or_Error + ":  The record " + record_name + " in the " + table_name + " table of the " + JSON_name + " has at least one blank entry for its \"" + field_name + "\" field.")
                        
                if has_AV and not all((value in allowed_values or "".join(value.split()) == "") for value in field_value):
                    record_error_handler(JSON_name, table_name, record_name, Warn_or_Error + ":  The record " + record_name + " in the " + table_name + " table of the " + JSON_name + " has at least one entry for its \"" + field_name + "\" field that is not in the list of allowed values for this field. \nThe allowed values are:  \n" + '\n'.join(allowed_values))
            
        ## If the value of the field is not a list.
            else:
                
                if "list" in validationCode :
                    record_error_handler(JSON_name, table_name, record_name, Warn_or_Error + ":  The record " + record_name + " in the " + table_name + " table of the " + JSON_name + " has a field, " + field_name + ", that is not a list field, but it should be according to its validationCode.")

                
                if "".join(field_value.split()) == "" :
                    if not blanks_allowed:
                        record_error_handler(JSON_name, table_name, record_name, Warn_or_Error + ":  The record " + record_name + " in the " + table_name + " table of the " + JSON_name + " has a blank entry for \"" + field_name + "\".")
                
                else: 
                    if has_AV and not field_value in allowed_values :
                        record_error_handler(JSON_name, table_name, record_name, Warn_or_Error + ":  The record " + record_name + " in the " + table_name + " table of the " + JSON_name + " has an entry for its \"" + field_name + "\" field that is not in the list of allowed values for this field. \nThe allowed values are:  \n" + '\n'.join(allowed_values))
                
                    if "text" in validationCode and is_it_a_num(field_value):
                        record_error_handler(JSON_name, table_name, record_name, Warn_or_Error + ":  The record " + record_name + " in the " + table_name + " table of the " + JSON_name + " has a numerical value for the field, " + field_name + ", but it should be a text value.")
                
                    elif "numeric" in validationCode and not is_it_a_num(field_value) :
                        record_error_handler(JSON_name, table_name, record_name, Warn_or_Error + ":  The record " + record_name + " in the " + table_name + " table of the " + JSON_name + " has a text value for the field, " + field_name + ", but it should be a numerical value.")
                
                
                







def JSON_id_check(JSON_file, JSON_name):
    """Loops over JSON_file and makes sure each field with a period in the name is an id, that each id points to an 
    existing id in another table that exists in JSON_file, that each "parentID" field points to another record that exists 
    in the same table, and that each "id" field  has a value that is the same as the name of the record.
    
    There are special cases for the subject and sample tables. Their parentID's can point to other tables, so they are 
    handled special. As of now protocol.id is also handled special since it can be a list."""
    
    reCopier = copier.Copier()
    
    for table_name, table_records in JSON_file.items():
        for record_name, record_fields in table_records.items():
            for field_name, field_value in record_fields.items():
                
                ## When there is a tagfield_scope table in the metadata, fields for project.id and study.id are added to the records
                ## automatically. Those tables are not in the controlled vocabulary so create an exception and just ignore those fields.
                ## TODO This was a result of how extract_metadata functioned and was a bug that has been fixed. This can probbaly be removed.
                if JSON_name == "controlled vocabulary" and (field_name == "study.id" or field_name == "project.id"):
                    continue
            
                if reCopier(re.match("(.*)\.(.*)", field_name)):
                        if reCopier.value.group(2) != "id":
                            record_error_handler(JSON_name, table_name, record_name, "Error:  In the " + table_name + " table of the " + JSON_name + ", the record " + record_name + " has a field, " + field_name + ", with a period in the name, but it is not an id.")
                           
                        elif not reCopier.value.group(1) in JSON_file:
                            record_error_handler(JSON_name, table_name, record_name, "Error:  In the " + table_name + " table of the " + JSON_name + ", the record " + record_name + " has a field, " + field_name + ", that is an id to another table, but that table is not in the " + JSON_name + ".")

                        elif isinstance(field_value, list) and not all(value in JSON_file[reCopier.value.group(1)] for value in field_value):
                            record_error_handler(JSON_name, table_name, record_name, "Error:  In the " + table_name + " table of the " + JSON_name + ", the record " + record_name + " has a field, " + field_name + ", that has id's to another table, but at least one of the id's is not in the " + reCopier.value.group(1) + " table.")
                        
                        elif isinstance(field_value, str) and not field_value in JSON_file[reCopier.value.group(1)]:
                            record_error_handler(JSON_name, table_name, record_name, "Error:  In the " + table_name + " table of the " + JSON_name + ", the record " + record_name + " has a field, " + field_name + ", that is an id to another table, but that id is not in the " + reCopier.value.group(1) + " table.")

                elif reCopier(re.match("parentID", field_name)) :
                    
                    ## parentID and lineage of protocols is checked more rigoroursly in another function. Just ignore it here.
                    if table_name == "protocol" :
                        continue
                    
                    ## If a subject has a parentID it can't be blank and it must be from the sample table.
                    if table_name == "subject" :
                        
                        if "".join(field_value.split()) == "":
                            record_error_handler(JSON_name, table_name, record_name, "Error:  In the " + table_name + " table of the " + JSON_name + ", the record " + record_name + " has a parentID, but there is no value.")
                        
                        elif field_value not in JSON_file["sample"]:
                            record_error_handler(JSON_name, table_name, record_name, "Error:  In the " + table_name + " table of the " + JSON_name + ", the record " + record_name + " has a parentID, " + field_value + ", but this parent is not in the sample table.")
                    
                    ## A sample parentID can be blank because it is a required field and another function checks for blanks in 
                    ## required fields, but it must be from the subject or sample tables not just the sample table.
                    elif table_name == "sample" :
                        if not "".join(field_value.split()) == "" and not field_value in table_records and not field_value in JSON_file["subject"]:
                            record_error_handler(JSON_name, table_name, record_name, "Error:  In the " + table_name + " table of the " + JSON_name + ", the record " + record_name + " has a parentID, " + field_value + ", but this parent is not in the subject or sample table.")
                    
                    ## For anything not a subject, sample, or protocol the parentID can be blank and must be from the same table.
                    elif not field_value in table_records and not "".join(field_value.split()) == "":
                        record_error_handler(JSON_name, table_name, record_name, "Error:  In the " + table_name + " table of the " + JSON_name + ", the record " + record_name + " has a parentID, " + field_value + ", but this parent is not in the " + table_name + " table.")

                elif reCopier(re.match("id", field_name)) and not "".join(field_value.split()) == "" and not field_value == record_name:
                    record_error_handler(JSON_name, table_name, record_name, "Error:  In the " + table_name + " table of the " + JSON_name + ", the record " + record_name + " has an id, " + field_value + ", but this is not the same as its own name.")








def table_fields_check(record_fields_by_protocol, parsed_metadata, table_name, controlled_vocabulary, protocol_CV_ancestor, default_protocol_fields):
    """Checks the sample, subject, or measurement table in parsed_metadata depending on what the value of table_name is, and 
    makes sure that each record in the table has all of the fields required by its protocols. It also checks 
    that each field is either an "id" field or is a field allowed by its protocols. In other words if a record 
    contains a field that is not in the controlled vocabulary for one of its protocols or is not an "id" field then an 
    error message is printed to the screen. Messages will also be printed if a field contains a blank value or if the 
    value is supposed to be numeric but is text and vice versa. If a field is associated with a protocol and it has 
    allowed_values, min, or max defined for it then the field value is also checked against those definitions. In other 
    words the field must be an allowed value, greater than or equal to the min, and less than or equal to the max."""
    
    
    
    if not "protocol" in parsed_metadata or not "parent_protocol" in controlled_vocabulary:
        return
        
    ## Determine whether we are checking the subject or sample table so the messages are correct.    
    if table_name == "sample":
        ## If there is no sample table in parsed metadata then return.
        if not "sample" in parsed_metadata :
            return
        
        capitalize_table_name = "Sample "
    elif table_name == "subject":
        ## if there is no subject table in parsed_metadata then return.
        if not "subject" in parsed_metadata :
            return
        
        capitalize_table_name = "Subject "
    elif table_name == "measurement":
        ## if there is no subject table in parsed_metadata then return.
        if not "measurement" in parsed_metadata :
            return
        
        capitalize_table_name = "Measurement "
    else:
        print("table_name must be one of \"sample\", \"subject\", or \"measurement\".")
        return
    
   
    reCopier = copier.Copier()
    
    ## Keep track of which record this error has been printed for, so it isn't printed twice.
    last_record_to_have_overlapping_fields = ""
    

    for record_name, record_fields in parsed_metadata[table_name].items() :
        ## Make sure the subject/sample has a protocol.id.
        if "protocol.id" in record_fields:
            
            if table_name in default_protocol_fields:
                all_possible_fields = copy.deepcopy(default_protocol_fields[table_name])

            else:
                all_possible_fields = {}
                
            for protocol_name in iterate_string_or_list(record_fields["protocol.id"]):                
                ## If the protocol for the sample is not in the protocol table from the metadata or in the controlled vocabulary
                ## then there is no way to check the required fields.
                if not protocol_name in parsed_metadata["protocol"] and not protocol_name in controlled_vocabulary["parent_protocol"]:
                    record_error_handler("metadata", table_name, record_name, "Error:  The protocol, " + protocol_name + ", for " + table_name + " " + record_name + " is not in the metadata protocol table or the controlled vocabulary parent_protocol table.")
                    continue
                                
                ## If the protocol is not in the dictionary of protocols with an ancestor in the controlled vocabulary then
                ## there are no fields to check so skip to the next protocol.
                if not protocol_name in protocol_CV_ancestor:
                    continue
                else:
                    protocol_ancestor = protocol_CV_ancestor[protocol_name]
                
                ## If the protocol of the sample is not in the record_fields_by_protocol dictionary then it has no fields to check.
                ## This shouldn't happen, but if the CV is malformed then it could be in the CV, but not have all of the 
                ## fields necessary to be in the record_fields_by_protocol dictionary.
                if protocol_ancestor in record_fields_by_protocol:
                    
                    ## Add fields to the list of all possible fields only if the field is for the table being checked.
                    for record_field, field_type in record_fields_by_protocol[protocol_ancestor].items():
                        if table_name in field_type["table"]:
                            
                            ## If a field is already in all_possible_fields then this record has multiple protocols
                            ## that specify the same field, so it is impossible to know which protocol is being satisfied.
                            if record_field in all_possible_fields:
                                if record_name != last_record_to_have_overlapping_fields:
                                    last_record_to_have_overlapping_fields = record_name
                                    record_error_handler("metadata", table_name, record_name, "Warning:  " + capitalize_table_name + record_name + " has protocols with overlapping fields.")
                            else:
                                all_possible_fields.update({record_field:field_type})
                    ## For each field the protocol could have see if the sample has it if it is a required field, 
                    ## and check that the types match if the sample has the field.
                    for field, field_type in record_fields_by_protocol[protocol_ancestor].items() :
                        
                        ## If the table field is subject-sample and we are checking the sample or subject table, or 
                        ## if the table field is measurement and we are checking the measurement table then proceed.
                        ## Basically only check the field if it is required for the table that is currently being worked on.
                        if table_name in field_type["table"] :
                            
                            field_scope_type = field_type["scope_type"]
                            
                            if "warning" in field_scope_type:
                                Warn_or_Error = "Warning"
                            else:
                                Warn_or_Error = "Error"
                            
                            if not field in record_fields :
                                if "ignore" in field_scope_type:
                                    record_error_handler("metadata", table_name, record_name, Warn_or_Error + ":  " + capitalize_table_name + record_name + " does not have an entry for the field, " + field + ", required by its protocol, " + protocol_name + ".")
                            
                            ## If the value is a list field it needs to be checked in a special way.
                            ## Since it is a list it can also have blank values and values of the wrong type at the same time,
                            ## so we need to be able to print all of the errors if that happens.
                            elif isinstance(record_fields[field], list) :
                                
                                if not "list" in field_type["validationCode"] and not "list_optional" in field_type["validationCode"]:
                                    record_error_handler("metadata", table_name, record_name, Warn_or_Error + ":  " + capitalize_table_name + record_name + " has a field, " + field + ", that is a list field, but it should not be according to its validationCode.")

                                if any("".join(value.split()) == "" for value in record_fields[field]) and not "blank" in field_scope_type:
                                    record_error_handler("metadata", table_name, record_name, Warn_or_Error + ":  " + capitalize_table_name + record_name + " has one or more blank values in the list for field, " + field + ".")
                                    
                                if "text" in field_type["validationCode"] and any(is_it_a_num(value) for value in record_fields[field]):
                                    record_error_handler("metadata", table_name, record_name, Warn_or_Error + "::  " + capitalize_table_name + record_name + " has one or more numerical values in the list for field, " + field + ", but they should all be text values.")
                                    
                                elif "numeric" in field_type["validationCode"] and any(not is_it_a_num(value) and not "".join(value.split()) == "" for value in record_fields[field]):
                                    record_error_handler("metadata", table_name, record_name, Warn_or_Error + ":  " + capitalize_table_name + record_name + " has one or more text values in the list for field, " + field + ", but they should all be numerical values.")
                                    
                                if "allowed_values" in field_type:
                                    if any(not value in field_type["allowed_values"] and not "".join(value.split()) == "" for value in record_fields[field]):
                                        record_error_handler("metadata", table_name, record_name, Warn_or_Error + ":  " + capitalize_table_name + record_name + " has one or more values in the list for field, " + field + ", that are not an allowed value for the field based on the allowed_values for the protocol in the tagfield_scope table.")
                                                                            
                                if "min" in field_type:
                                    if any(value < field_type["min"] for value in record_fields[field]):
                                        record_error_handler("metadata", table_name, record_name, Warn_or_Error + ":  " + capitalize_table_name + record_name + " has one or more values in the list for field, " + field + ", that are less than the minimum allowed value for the field based on the min for the protocol in the tagfield_scope table.")

                                if "max" in field_type:
                                    if any(value > field_type["max"] for value in record_fields[field]):
                                        record_error_handler("metadata", table_name, record_name, Warn_or_Error + ":  " + capitalize_table_name + record_name + " has one or more values in the list for field, " + field + ", that are greater than the maximum allowed value for the field based on the max for the protocol in the tagfield_scope table.")
    
    
                                
                            else:
                                if "list" in field_type["validationCode"]:
                                    record_error_handler("metadata", table_name, record_name, Warn_or_Error + ":  " + capitalize_table_name + record_name + " has a field, " + field + ", that is not a list field, but should be according to its validationCode.")

                                if "".join(record_fields[field].split()) == "" :
                                    if not "blank" in field_scope_type:
                                        record_error_handler("metadata", table_name, record_name, Warn_or_Error + ":  " + capitalize_table_name + record_name + " does not have a value for the field, " + field + ".")
        
                                else:
                                    
                                    if "allowed_values" in field_type and not record_fields[field] in field_type["allowed_values"] :
                                        record_error_handler("metadata", table_name, record_name, Warn_or_Error + ":  " + capitalize_table_name + record_name + " has a value in the field, " + field + ", that is not an allowed value for the field based on the allowed_values for the protocol in the tagfield_scope table.")
                                                                                
                                    if "min" in field_type and record_fields[field] < field_type["min"]:
                                        record_error_handler("metadata", table_name, record_name, Warn_or_Error + ":  " + capitalize_table_name + record_name + " has a value in the field, " + field + ", that is less than the minimum allowed value for the field based on the min for the protocol in the tagfield_scope table.")
    
                                    if "max" in field_type and record_fields[field] > field_type["max"]:
                                        record_error_handler("metadata", table_name, record_name, Warn_or_Error + ":  " + capitalize_table_name + record_name + " has a value in the field, " + field + ", that is greater than the maximum allowed value for the field based on the max for the protocol in the tagfield_scope table.")

                                    ## If the field type is text, but the value is a number then print a message.
                                    if "text" in field_type["validationCode"] and is_it_a_num(record_fields[field]) :
                                        record_error_handler("metadata", table_name, record_name, Warn_or_Error + ":  " + capitalize_table_name + record_name + " has a numerical value for the field, " + field + ", but it should be a text value.")
                                    
                                    ## If the field_type is numeric, but value of is not numeric print a message.
                                    ## Must also be not blank. If it is blank here then we know that blanks are 
                                    ## allowed because if they weren't then a previous check would have caught it.
                                    elif "numeric" in field_type["validationCode"] and not is_it_a_num(record_fields[field]) :
                                        record_error_handler("metadata", table_name, record_name, Warn_or_Error + ":  " + capitalize_table_name + record_name + " has a text value for the field, " + field + ", but it should be a numerical value.")
                                        
                                                                        
        
        ## After we have checked that each field for each protocol is present and compiled a list 
        ## of all of the possible fields from each protocol we can check whether any of the fields in the record don't belong.
            for field_name, field_value in record_fields.items() :
                
                ## If a field is an id then go to the next field, another function checks id's more rigorously.
                if reCopier(re.match("(.*)\.(id)|id|parentID", field_name)):
                    continue
                ## If there is a % in the field name then the first part must be in the 
                ## allowed fields since it should be an attribute of an allowed field.
                elif reCopier(re.match("(.*)%(.*)", field_name)):
                    
                    ## Check that the attribute's field is allowed.
                    if not reCopier.value.group(1) in all_possible_fields:
                        record_error_handler("metadata", table_name, record_name, "Error:  " + capitalize_table_name + record_name + " has a field, " + field_name + ", that should be an attribute to an allowed field, but can't be matched to an allowed field from the controlled vocabulary.")
                    
                    ## Check that the record has the field that the attribute belongs to.
                    if not reCopier.value.group(1) in record_fields:
                        record_error_handler("metadata", table_name, record_name, "Error:  " + capitalize_table_name + record_name + " has a field, " + field_name + ", that should be an attribute to a field, but the record doesn't have that field.")
                
                    
                    if "tagfield_attribute" in controlled_vocabulary:
                        ## Check that the attribute is in the tagfield_attribute table.
                        if not field_name in controlled_vocabulary["tagfield_attribute"]:
                            record_error_handler("metadata", table_name, record_name, "Error:  " + capitalize_table_name + record_name + " has a field, " + field_name + ", that should be an attribute to a field, but is not in the tagfield_attribute table of the controlled vocabulary.")

                        ## Check that the value of the attribute has the right type.
                        elif "validationCode" in controlled_vocabulary["tagfield_attribute"][field_name]:
                            
                            validationCode = controlled_vocabulary["tagfield_attribute"][field_name]["validationCode"]
                            
                            if isinstance(field_value, list) :
                                if not "list" in validationCode and not "list_optional" in validationCode:
                                    record_error_handler("metadata", table_name, record_name, "Error:  " + capitalize_table_name + record_name + " has a field, " + field + ", that is a list field, but should not be according to its validationCode.")
                                
                                if any("".join(value.split()) == "" for value in field_value) :
                                    record_error_handler("metadata", table_name, record_name, "Warning:  " + capitalize_table_name + record_name + " has one or more blank values in the list for field, " + field + ".")
                                    
                                if "text" in validationCode and any(is_it_a_num(value) for value in field_value):
                                    record_error_handler("metadata", table_name, record_name, "Error:  " + capitalize_table_name + record_name + " has one or more numerical values in the list for field, " + field + ", but they should all be text values.")
                                    
                                elif "numeric" in validationCode and any(not is_it_a_num(value) and not "".join(value.split()) == "" for value in field_value):
                                    record_error_handler("metadata", table_name, record_name, "Error:  " + capitalize_table_name + record_name + " has one or more text values in the list for field, " + field + ", but they should all be numerical values.")
                                        
                            else:
                                
                                if "list" in validationCode:
                                    record_error_handler("metadata", table_name, record_name, "Error:  " + capitalize_table_name + record_name + " has a field, " + field + ", that is not a list field, but should be according to its validationCode.")

                                
                                if "".join(field_value.split()) == "":
                                    record_error_handler("metadata", table_name, record_name, "Warning:  " + capitalize_table_name + record_name + " does not have a value for the field, " + field + ".")
        
                                ## If the field type is text, but the value is a number then print a message.
                                elif "text" in validationCode and is_it_a_num(field_value) :
                                    record_error_handler("metadata", table_name, record_name, "Error:  " + capitalize_table_name + record_name + " has a numerical value for the field, " + field + ", but it should be a text value.")
                                
                                ## If the field_type is numeric, but value of is not numeric print a message.
                                elif "numeric" in validationCode and not is_it_a_num(field_value) :
                                    record_error_handler("metadata", table_name, record_name, "Error:  " + capitalize_table_name + record_name + " has a text value for the field, " + field + ", but it should be a numerical value.")

                
                
                
                elif not field_name in all_possible_fields:
                    record_error_handler("metadata", table_name, record_name, "Error:  " + capitalize_table_name + record_name + " has a field, " + field_name + ", that is neither an id nor an allowed field based on its protocols.")








def SS_protocol_check(parsed_metadata, sample_or_subject, controlled_vocabulary):
    """Loops over the sample or subject table in parsed_metadata depending on the value of sample_or_subject
    and makes sure that each sample/subject has protocols of the correct type depending on its inheritance. 
    Samples that have a sample parent must have a sample_prep type protocol.
    Samples that have a subject parent must have a collection type protocol.
    Subjects must have a treatment type protocol."""

    if not "parent_protocol" in controlled_vocabulary:
        return
        
    ## Determine whether we are checking the subject or sample table so the messages are correct.    
    if sample_or_subject == "sample":
        ## If there is no sample table in parsed metadata then return.
        if not "sample" in parsed_metadata :
            return
        
    elif sample_or_subject == "subject":
        ## if there is no subject table in parsed_metadata then return.
        if not "subject" in parsed_metadata :
            return
        
    else:
        print("sample_or_subject must be either \"sample\" or \"subject\".")
        return
    
        
    
    
    for sample_name, sample_fields in parsed_metadata[sample_or_subject].items() :
        
        if "prototocol.id" in sample_fields:
            has_type_sample_prep = False 
            has_type_collection = False
            has_type_treatment = False
            
            for protocol_name in iterate_string_or_list(sample_fields["protocol.id"]):
                            
                ## Find the closest ancestor to the protocol with a type and use that type as the type of the protocol.
                if protocol_name in parsed_metadata["protocol"]:
                    while not "type" in parsed_metadata["protocol"][protocol_name]:
                        if "parentID" in parsed_metadata["protocol"][protocol_name]:
                            protocol_name = parsed_metadata["protocol"][protocol_name]["parentID"]
                        elif protocol_name in controlled_vocabulary["parent_protocol"]:
                            break
                        else:
                            break
                        
            ## See if the protocol's closest ancestor with a type has any of the types required.
                if protocol_name in parsed_metadata["protocol"] and "type" in parsed_metadata["protocol"][protocol_name] :
                    if parsed_metadata["protocol"][protocol_name]["type"] == "sample_prep":
                        has_type_sample_prep = True
                    elif parsed_metadata["protocol"][protocol_name]["type"] == "collection":
                        has_type_collection = True
                    elif parsed_metadata["protocol"][protocol_name]["type"] == "treatment":
                        has_type_treatment = True
                    
                elif protocol_name in controlled_vocabulary["parent_protocol"] and "type" in controlled_vocabulary["parent_protocol"][protocol_name] :
                    if controlled_vocabulary["parent_protocol"][protocol_name]["type"] == "sample_prep":
                        has_type_sample_prep = True
                    if controlled_vocabulary["parent_protocol"][protocol_name]["type"] == "collection":
                        has_type_collection = True
                    if controlled_vocabulary["parent_protocol"][protocol_name]["type"] == "treatment":
                        has_type_treatment = True
                    

                                    
                                    
            if "parentID" in sample_fields and sample_or_subject == "sample":
                parent = sample_fields["parentID"]
                
                ## If the sample has a parent and it is a sample then it must have a sample_prep type protocol.
                if parent in parsed_metadata["sample"] and has_type_sample_prep == False:                                    
                    record_error_handler("metadata", sample_or_subject, sample_name, "Error:  Sample " + sample_name + " came from a sample, but does not have a sample_prep protocol.")
                        
                ## If the sample has a parent and it is a subject then it must have a collection type protocol.        
                elif parent in parsed_metadata["subject"] and has_type_collection == False:
                    record_error_handler("metadata", sample_or_subject, sample_name, "Error:  Sample " + sample_name + " came from a subject, but does not have a collection protocol.")                
                                    
                    
            ## Check that each subject has a treatment type protocol.            
            if sample_or_subject == "subject" and has_type_treatment == False:
                record_error_handler("metadata", sample_or_subject, sample_name, "Error:  Subject " + sample_name + " does not have a treatment type protocol.")







def measurement_protocol_check(parsed_metadata, controlled_vocabulary):
    """Loops over the measurement table in parsed_metadata and makes sure that each measurement 
    has at least one measurement type protocol."""

    if not "parent_protocol" in controlled_vocabulary:
        return
        
    if not "measurement" in parsed_metadata :
        return
        
    
        
    
    
    for measurement_name, measurement_fields in parsed_metadata["measurement"].items() :
        
        if "prototocol.id" in measurement_fields:
            has_type_measurement = False
            
            for protocol_name in iterate_string_or_list(measurement_fields["protocol.id"]):
                            
                ## Find the closest ancestor to the protocol with a type and use that type as the type of the protocol.
                if protocol_name in parsed_metadata["protocol"]:
                    while not "type" in parsed_metadata["protocol"][protocol_name]:
                        if "parentID" in parsed_metadata["protocol"][protocol_name]:
                            protocol_name = parsed_metadata["protocol"][protocol_name]["parentID"]
                        elif protocol_name in controlled_vocabulary["parent_protocol"]:
                            break
                        else:
                            break
                        
            ## See if the protocol's closest ancestor with a type has the type required.
                if protocol_name in parsed_metadata["protocol"] and "type" in parsed_metadata["protocol"][protocol_name] :
                    if parsed_metadata["protocol"][protocol_name]["type"] == "measurement":
                        has_type_measurement = True
                        break
                    
                elif protocol_name in controlled_vocabulary["parent_protocol"] and "type" in controlled_vocabulary["parent_protocol"][protocol_name] :
                    if controlled_vocabulary["parent_protocol"][protocol_name]["type"] == "measurement":
                        has_type_measurement = True
                        break
                    

                                    
            if not has_type_measurement:
                record_error_handler("metadata", "measurement", measurement_name, "Error:  Measurement " + measurement_name + " does not have a measurement type protocol.")











## Taken care of in the JSON_id_check function for now. Might come back to this.
#def subject_inheritance_check(parsed_metadata):
#    """Loops over the  subject table in parsed_metadata and makes sure each subject with a parentID 
#     inherits from a sample. This means the parentID cannot be blank and must be found in the sample table."""
#    
#    if not "sample" in parsed_metadata or not "subject" in parsed_metadata :
#        return
#
#
#    for subject_name, subject_fields in parsed_metadata["subject"].items() :
#        
#        if "parentID" in subject_fields:
#            parent = subject_fields["parentID"]
#            
#            if "".join(parent.split()) == "" :
#                record_error_handler("metadata", "subject", subject_name, "Error:  The subject " + subject_name + " in the subject table of the metadata has a blank value for \"parentID\".")
#            ## If a subject has a parentID then it must be a sample.                        
#            elif not parent in parsed_metadata["sample"] :
#                record_error_handler("metadata", "subject", subject_name, "Error:  The subject " + subject_name + " in the subject table of the metadata has parentID, " + parent + ", but this parent is not in the sample table.")
                    
                    




def protocol_fields_check(parsed_metadata, protocol_fields_by_protocol, protocol_CV_ancestor, controlled_vocabulary, default_protocol_fields):
    """Loops over the protocol table in parsed_metadata, and for every protocol that is in 
    protocol_fields_by_protocol, or has an ancestor from the controlled vocabulary in protocol_fields_by_protocol, 
    (ancestors are in protocol_CV_ancestor) checks that the protocol has the required fields 
    in protocol_fields_by_protocol and that they are not blank and have the correct type."""
    
    
    if not "protocol" in parsed_metadata:
        return
    
    ## If "protocol" is not in default_protocol_fields then add an empty dict so that later checks do not cause an error.
    if not "protocol" in default_protocol_fields:
        default_protocol_fields["protocol"] = {}
    
    reCopier = copier.Copier()
    
    ## Get only the required fields.
    required_fields_by_protocol_for_protocol = {}
    for protocol_name, fields in protocol_fields_by_protocol.items():
        for field_name, field_attributes in fields.items():
            if "ignore" in field_attributes["scope_type"] :
                if not protocol_name in required_fields_by_protocol_for_protocol:
                    required_fields_by_protocol_for_protocol[protocol_name] = {}
                
                required_fields_by_protocol_for_protocol[protocol_name].update({field_name : field_attributes})
                
                
    for protocol_name, protocol_fields in parsed_metadata["protocol"].items():
        
    ## If the protocol from the metadata is in the controlled vocabulary and it has required fields then make sure it has those fields.
    ## Use the protocol's closest ancestor from the controlled vocabulary to look for required fields, because the protocol itself 
    ## obviously won't have any required fields from the metadata.
        
        ## If the protocol has an ancestor then do the rest of the checks, otherwise go to the next protocol.
        if protocol_name in protocol_CV_ancestor:
            protocol_ancestor = protocol_CV_ancestor[protocol_name]
            
        else:
            continue
            
            
        if protocol_ancestor in required_fields_by_protocol_for_protocol:
            required_fields = required_fields_by_protocol_for_protocol[protocol_ancestor]
            
            ## For every required field make sure the protocol has that field, it is not blank, 
            ## and that the value of the field is of the correct type, text or numeric.
            for field_name, field_attributes in required_fields.items():
                
                if "warning" in field_attributes["scope_type"]:
                    Warn_or_Error = "Warning"
                else:
                    Warn_or_Error = "Error"
                
                if not field_name in protocol_fields:
                    record_error_handler("metadata", "protocol", protocol_name, Warn_or_Error + ":  The protocol " + protocol_name + " in the protocol table of the metadata does not have a field for the required field " + field_name + ".")
                
                elif isinstance(protocol_fields[field_name], list):
                    
                    if not "list" in field_attributes["validationCode"] and not "list_optional" in field_attributes["validationCode"]:
                        record_error_handler("metadata", "protocol", protocol_name, Warn_or_Error + ":  The protocol " + protocol_name + " in the protocol table of the metadata has a field, " + field_name + ", that is a list field, but should not be according to its validationCode.")
                    
                ## Since the value is a list there can be blank values and values of the wrong type at the same time.
                ## We have to be able to print multiple messages if this happens.
                    if not "blank" in field_attributes["scope_type"] and any("".join(value.split()) == "" for value in protocol_fields[field_name]):
                        record_error_handler("metadata", "protocol", protocol_name, Warn_or_Error + ":  The protocol " + protocol_name + " in the protocol table of the metadata has at least one blank value for the required field " + field_name + ".")
                    
                    if "text" in field_attributes["validationCode"] and any(is_it_a_num(value) for value in protocol_fields[field_name]):
                        record_error_handler("metadata", "protocol", protocol_name, Warn_or_Error + ":  The protocol " + protocol_name + " in the protocol table of the metadata has at least one value that is a number, but should be a text value for the required field " + field_name + ".")
                    
                    elif "numeric" in field_attributes["validationCode"] and any(not is_it_a_num(value) and not "".join(value.split()) == "" for value in protocol_fields[field_name]):
                        record_error_handler("metadata", "protocol", protocol_name, Warn_or_Error + ":  The protocol " + protocol_name + " in the protocol table of the metadata has at least one value that is a text value, but should be a number for the required field " + field_name + ".")

                else:
                    
                    if "list" in field_attributes["validationCode"]:
                        record_error_handler("metadata", "protocol", protocol_name, Warn_or_Error + ":  The protocol " + protocol_name + " in the protocol table of the metadata has a field, " + field_name + ", that is not a list field, but should be according to its validationCode.")
                    
                    if "".join(protocol_fields[field_name].split()) == "":
                        if not "blank" in field_attributes["scope_type"]:
                            record_error_handler("metadata", "protocol", protocol_name, Warn_or_Error + ":  The protocol " + protocol_name + " in the protocol table of the metadata has a blank value for the required field " + field_name + ".")
                        
                    elif "text" in field_attributes["validationCode"] and is_it_a_num(protocol_fields[field_name]):
                        record_error_handler("metadata", "protocol", protocol_name, Warn_or_Error + ":  The protocol " + protocol_name + " in the protocol table of the metadata has a text value for the required field " + field_name + ", but it should be a number.")
                        
                    elif "numeric" in field_attributes["validationCode"] and not is_it_a_num(protocol_fields[field_name]):
                        record_error_handler("metadata", "protocol", protocol_name, Warn_or_Error + ":  The protocol " + protocol_name + " in the protocol table of the metadata has a number for the required field " + field_name + ", but it should be a text value.")


        
    ## After we have checked that each field for each protocol is present and compiled a list 
    ## of all of the possible fields from each protocol we can check whether any of the fields in the protocol don't belong.
        for field_name, field_value in protocol_fields.items() :
            
            ## If a field is an id then go to the next field, another function checks id's more rigorously.
            if reCopier(re.match("(.*)\.(id)|id|parentID", field_name)):
                continue
            ## If there is a % in the field name then the first part must be in the 
            ## allowed fields since it should be an attribute of an allowed field.
            elif reCopier(re.match("(.*)%(.*)", field_name)):
                if not protocol_ancestor in protocol_fields_by_protocol or not reCopier.value.group(1) in protocol_fields_by_protocol[protocol_ancestor]:
                    record_error_handler("metadata", "protocol", protocol_name, "Error:  The protocol " + protocol_name + " has a field, " + field_name + ", that should be an attribute to an allowed field, but can't be matched to an allowed field.")
            
                if "tagfield_attribute" in controlled_vocabulary:
                    ## Check that the attribute is in the tagfield_attribute table.
                    if not field_name in controlled_vocabulary["tagfield_attribute"]:
                        record_error_handler("metadata", "protocol", protocol_name, "Error:  The protocol " + protocol_name + " has a field, " + field_name + ", that should be an attribute to a field, but is not in the tagfield_attribute table of the controlled vocabulary.")
    
                    ## Check that the value of the attribute has the right type.
                    elif "validationCode" in controlled_vocabulary["tagfield_attribute"][field_name]:
                        
                        validationCode = controlled_vocabulary["tagfield_attribute"][field_name]["validationCode"]
                        
                        if isinstance(field_value, list) :
                            if not "list" in validationCode and not "list_optional" in validationCode:
                                record_error_handler("metadata", "protocol", protocol_name, "Error:  The protocol " + protocol_name + " has a field, " + field_name + ", that is a list field, but should not be according to its validationCode.")
                            
                            if any("".join(value.split()) == "" for value in field_value) :
                                record_error_handler("metadata", "protocol", protocol_name, "Warning:  The protocol " + protocol_name + " has one or more blank values in the list for field, " + field_name + ".")
                                
                            if "text" in validationCode and any(is_it_a_num(value) for value in field_value):
                                record_error_handler("metadata", "protocol", protocol_name, "Error:  The protocol " + protocol_name + " has one or more numerical values in the list for field, " + field_name + ", but they should all be text values.")
                                
                            elif "numeric" in validationCode and any(not is_it_a_num(value) and not "".join(value.split()) == "" for value in field_value):
                                record_error_handler("metadata", "protocol", protocol_name, "Error:  The protocol " + protocol_name + " has one or more text values in the list for field, " + field_name + ", but they should all be numerical values.")
                                    
                        else:
                            
                            if "list" in validationCode:
                                record_error_handler("metadata", "protocol", protocol_name, "Error:  The protocol " + protocol_name + " has a field, " + field_name + ", that is not a list field, but should be according to its validationCode.")
    
                            
                            if "".join(field_value.split()) == "":
                                record_error_handler("metadata", "protocol", protocol_name, "Warning:  The protocol " + protocol_name + " does not have a value for the field, " + field_name + ".")
    
                            ## If the field type is text, but the value is a number then print a message.
                            elif "text" in validationCode and is_it_a_num(field_value) :
                                record_error_handler("metadata", "protocol", protocol_name, "Error:  The protocol " + protocol_name + " has a numerical value for the field, " + field_name + ", but it should be a text value.")
                            
                            ## If the field_attributes is numeric, but value of is not numeric print a message.
                            elif "numeric" in validationCode and not is_it_a_num(field_value) :
                                record_error_handler("metadata", "protocol", protocol_name, "Error:  The protocol " + protocol_name + " has a text value for the field, " + field_name + ", but it should be a numerical value.")

            
            
            
            elif not protocol_ancestor in protocol_fields_by_protocol or (not field_name in protocol_fields_by_protocol[protocol_ancestor] and not field_name in default_protocol_fields["protocol"]):
                record_error_handler("metadata", "protocol", protocol_name, "Error:  The protocol " + protocol_name + " has a field, " + field_name + ", that is neither an id nor an allowed field from the controlled vocabulary.")










def protocol_lineage_check(parsed_metadata, controlled_vocabulary):
    """Loops over the protocol table in parsed_metadata and checks that each protocol has an ancestor in the parent_protocol table
    of the controlled_vocabulary. Also checks that each protocol has the same type as its parent and its ancestor in the 
    parent_protocol table of the controlled_vocabulary. """
    
    ## A message is already given to the user about which tables are present or not.
    if not "protocol" in parsed_metadata or not "parent_protocol" in controlled_vocabulary:
        return


    for protocol_name, protocol_fields in parsed_metadata["protocol"].items():
        protocol_has_type = True
        cv_has_type = True
        
        if "parentID" in protocol_fields:
            parentID = protocol_fields["parentID"]
                        
        ## Trace the protocol's lineage and make sure it inherits from a protocol in the controlled vocabulary.
        
            if parentID in controlled_vocabulary["parent_protocol"]:
                
                if not "type" in protocol_fields:
                    record_error_handler("metadata", "protocol", protocol_name, "Warning:  The protocol, " + protocol_name + ", in the protocol table of the metadata does not have a field for \"type\".")
                    protocol_has_type = False
                                
                if protocol_has_type and not "type" in controlled_vocabulary["parent_protocol"][parentID] and (controlled_vocabulary["parent_protocol"][parentID]["type"] != protocol_fields["type"] or controlled_vocabulary["parent_protocol"][parentID]["type"] != "master"):
                    record_error_handler("metadata", "protocol", protocol_name, "Error:  The protocol, " + protocol_name + ",  in the protocol table of the metadata does not have the same type as its parent in the parent_protocol table of the controlled vocabulary.")
            
            ## If the parentID is in the protocol table of the metadata then we check that it has the same type
            ## and go up the inheritance tree until we find an ancestor in the controlled vocabulary.
            ## The type of ancestors past the parent and before the ancestor in the CV is not checked. This is 
            ## because they are assumed to be in the protocol table and will be checked against their parent later.
            ## It is an attempt to avoid displaying the same error twice.
            elif parentID in parsed_metadata["protocol"]:
                
                if not "type" in protocol_fields:
                    record_error_handler("metadata", "protocol", protocol_name, "Warning:  The protocol, " + protocol_name + ", in the protocol table of the metadata does not have a field for \"type\".")
                    protocol_has_type = False
                
                if not "type" in parsed_metadata["protocol"][parentID]:
                    record_error_handler("metadata", "protocol", parentID, "Warning:  The protocol, " + parentID + ",  in the protocol table of the metadata does not have a field for \"type\".")
                    table_has_type = False
                
                if protocol_has_type and table_has_type and (parsed_metadata["protocol"][parentID]["type"] != protocol_fields["type"] or parsed_metadata["protocol"][parentID]["type"] != "master"):
                    record_error_handler("metadata", "protocol", protocol_name, "Error:  The protocol, " + protocol_name + ", in the protocol table of the metadata does not have the same type as its parent.")

                
                ancestor_name = parentID
                ancestor_fields = parsed_metadata["protocol"][parentID]
                while not ancestor_name in controlled_vocabulary["parent_protocol"]:
                    if "parentID" in ancestor_fields:
                        ancestorID = ancestor_fields["parentID"]
                        if ancestorID in controlled_vocabulary["parent_protocol"]:
                            if not "type" in controlled_vocabulary["parent_protocol"][ancestorID]:
                                record_error_handler("controlled vocabulary", "parent_protocol", ancestorID, "Error:  The protocol, " + ancestorID + ", does not have a field for \"type\" in the parent_protocol table of the controlled vocabulary.")
                            
                            elif "type" in protocol_fields and (controlled_vocabulary["parent_protocol"][ancestorID]["type"] != protocol_fields["type"] or controlled_vocabulary["parent_protocol"][ancestorID]["type"] != "master"):
                                record_error_handler("controlled vocabulary", "parent_protocol", protocol_name, "Error:  The protocol, " + protocol_name + ", does not have the same type as its ancestor in the parent_protocol table of the controlled vocabulary.")
                                
                            break
                                
                        elif ancestorID in parsed_metadata["protocol"]:
                            ancestor_name = ancestorID
                            ancestor_fields = parsed_metadata["protocol"][ancestorID]
                            
                        else:
                            record_error_handler("metadata", "protocol", protocol_name, "Error:  The protocol, " + protocol_name + ", does not have an ancestor in the controlled vocabulary.")
                            break
                    else:
                        record_error_handler("metadata", "protocol", protocol_name, "Error:  The protocol, " + protocol_name + ", does not have an ancestor in the controlled vocabulary.")
                        break
                
            else:
                record_error_handler("metadata", "protocol", protocol_name, "Error: The parentID of the protocol, " + protocol_name + ", in the metadata protocol table does not appear in either the metadata protocol table or the controlled vocabulary.")
                
        
        ## If the protocol does not have a parent and is not in the controlled vocabulary then this is a major error.                
        elif not protocol_name in controlled_vocabulary["parent_protocol"]:
            record_error_handler("metadata", "protocol", protocol_name, "Error: The protocol, " + protocol_name + ", in the metadata protocol table is not in the controlled vocabulary nor does it have a parentID.")
            
        ## If the protocol has no parentID, but is in the controlled vocabulary 
        ## then its type needs to be compared with its type in the controlled vocabulary.
        else:
            if not "type" in protocol_fields:
                record_error_handler("metadata", "protocol", protocol_name, "Warning:  The protocol, " + protocol_name + ", does not have a field for \"type\" in the protocol table of the metadata.")
                protocol_has_type = False
            
            if not "type" in controlled_vocabulary["parent_protocol"][protocol_name]:
                record_error_handler("controlled vocabulary", "parent_protocol", protocol_name, "Error:  The protocol, " + protocol_name + ", does not have a field for \"type\" in the parent_protocol table of the controlled vocabulary.")
                cv_has_type = False
            
            if protocol_has_type and cv_has_type and controlled_vocabulary["parent_protocol"][protocol_name]["type"] != protocol_fields["type"]:
                record_error_handler("metadata", "protocol", protocol_name, "Error:  The protocol, " + protocol_name + ", does not have the same type as it does in the parent_protocol table of the controlled vocabulary.")







def protocol_all_used_check(parsed_metadata):
    """Compiles a list of all of the protocols used by the subjects, samples, and measurements in the subject and sample table 
    of the parsed_metadata and checks that every protocol in the protocol table is in that list. For any protocols 
    that appear in the protocol table, but are not used by a subject, sample, or measurement a warning is printed."""
    
    if not "protocol" in parsed_metadata or not "subject" in parsed_metadata or not "sample" in parsed_metadata:
        return
    
    used_protocols = set()
    
    ## Loop over the measurement table if it exists to get a list of the protocols used by them.
    if "measurement" in parsed_metadata:
        for measurement_name, measurement_fields in parsed_metadata["measurement"].items():
                if "protocol.id" in measurement_fields:
                    for protocol_name in iterate_string_or_list(measurement_fields["protocol.id"]):
                        used_protocols.add(protocol_name)
    
    ## Loop over the samples and subject tables to compile a unique list of all of the protocols used by the subject/samples.
    for table_name in ["sample", "subject"]:
        for sample_name, sample_fields in parsed_metadata[table_name].items():
            if "protocol.id" in sample_fields:
                for protocol_name in iterate_string_or_list(sample_fields["protocol.id"]):
                    used_protocols.add(protocol_name)
                    
    
    ## For every protocol that is in the protocol table but is not used print a warning.             
    for protocol_name in set(parsed_metadata["protocol"]) - used_protocols:
        record_error_handler("metadata", "protocol", protocol_name, "Warning:  The protocol, " + protocol_name + ", in the protocol table of the metadata is not used by any of the subjects, samples, or measurements.")







def protocol_description_check(parsed_metadata):
    """Checks that every description field for the protocols in the protocol table of the metadata are unique."""
    
    if not "protocol" in parsed_metadata:
        return
    
    protocols_with_descriptions = [protocol_name for protocol_name, protocol_fields in parsed_metadata["protocol"].items() if "description" in protocol_fields]
    descriptions = [protocol_fields["description"] for protocol_name, protocol_fields in parsed_metadata["protocol"].items() if "description" in protocol_fields]
    protocols_with_matching_descriptions = [indexes_of_duplicates_in_list(descriptions, description) for description in descriptions]
    
    protocols_with_matching_descriptions.sort()
    protocols_with_matching_descriptions = list(group for group,_ in itertools.groupby(protocols_with_matching_descriptions))
    
    
    for i in range(len(protocols_with_matching_descriptions)):
        if len(protocols_with_matching_descriptions[i]) > 1:
            protocols_to_print = [protocols_with_descriptions[index] for index in protocols_with_matching_descriptions[i]]
            
            if not silent_mode:
                print("Warning: The protocols: \n\n" + "\n".join(protocols_to_print) + "\n\nhave the exact same descriptions.")
            






def factor_all_used_check(parsed_metadata):
    """Checks that every factor in the factor table is used at least once by a subject or sample."""

    if not "factor" in parsed_metadata:
        return
    
    reCopier = copier.Copier()
    
    subject_factors = {}
    for factor_name, factor_fields in parsed_metadata["factor"].items():
        if "allowed_values" in factor_fields and reCopier(re.match(r"(subject)\.(.*)", factor_name)):
            subject_factors[reCopier.value.group(2)] = iterate_string_or_list(factor_fields["allowed_values"])
            
            
    sample_factors = {}
    for factor_name, factor_fields in parsed_metadata["factor"].items():
        if "allowed_values" in factor_fields and reCopier(re.match(r"(sample)\.(.*)", factor_name)):
            sample_factors[reCopier.value.group(2)] = iterate_string_or_list(factor_fields["allowed_values"])
    

    if "subject" in parsed_metadata:
                
        all_subject_fields = {}
        for subject_name, subject_fields in parsed_metadata["subject"].items():
            for field_name, field_value in subject_fields.items():
                if field_name in all_subject_fields.keys():
                    all_subject_fields[field_name].update(iterate_string_or_list(field_value))
                else:
                    all_subject_fields[field_name] = set(iterate_string_or_list(field_value))
        
        #all_subject_fields = {field for name, fields in parsed_metadata["subject"].items() for field in fields.keys()}
        if not set(subject_factors.keys()).issubset(all_subject_fields.keys()) :
            unused_factors = set(subject_factors.keys()) - set(all_subject_fields.keys())
            for factor_name in unused_factors:
                record_error_handler("metadata", "factor", "subject." + factor_name, "Warning:  The factor, subject." + factor_name + ", in the factor table of the metadata is not used by any of the subjects.")
        
        for factor_name, allowed_values in subject_factors.items():
            if factor_name in all_subject_fields.keys():
                unused_allowed_values = set(allowed_values) - set(all_subject_fields[factor_name])
                for allowed_value in unused_allowed_values:
                    record_error_handler("metadata", "factor", "subject." + factor_name, "Warning:  The allowed value, " + allowed_value + ", for the factor, subject." + factor_name + ", in the factor table of the metadata is not used by any of the subjects.")

        
    if "sample" in parsed_metadata:
        
        all_sample_fields = {}
        for sample_name, sample_fields in parsed_metadata["sample"].items():
            for field_name, field_value in sample_fields.items():
                if field_name in all_sample_fields.keys():
                    all_sample_fields[field_name].update(iterate_string_or_list(field_value))
                else:
                    all_sample_fields[field_name] = set(iterate_string_or_list(field_value))
        
        #all_sample_fields = {field for name, fields in parsed_metadata["sample"].items() for field in fields.keys()}
        if not set(sample_factors.keys()).issubset(all_sample_fields.keys()) :
            unused_factors = set(sample_factors.keys()) - set(all_sample_fields.keys())
            for factor_name in unused_factors:
                record_error_handler("metadata", "factor", "sample." + factor_name, "Warning:  The factor, sample." + factor_name + ", in the factor table of the metadata is not used by any of the samples.")

        for factor_name, allowed_values in sample_factors.items():
            if factor_name in all_sample_fields.keys():
                unused_allowed_values = set(allowed_values) - set(all_sample_fields[factor_name])
                for allowed_value in unused_allowed_values:
                    record_error_handler("metadata", "factor", "sample." + factor_name, "Warning:  The allowed value, " + allowed_value + ", for the factor, sample." + factor_name + ", in the factor table of the metadata is not used by any of the samples.")





def compile_fields_by_protocol(controlled_vocabulary) :
    """ Returns 2 dictionaries where the keys are the protocols in the parent_protocol table of the controlled_vocabulary JSON,
    and the values are a dictionary of the fields. One dictionary is fields for protocols and the other dictionary is fields for 
    subjects, samples, and measurements. The values of the field dictionary are the scope_type, table, and validationCode of the fields.
    The values may also include allowed_values, min, and max if those fields are provided for the record in the tagfield_scope table."""
    
    
    if not "parent_protocol" in controlled_vocabulary or not "tagfield_scope" in controlled_vocabulary or not "tagfield" in controlled_vocabulary:
        return
        
    ## Final dictionary of protocols and fields to return at the end for subjects, samples, and measurements.
    record_fields_by_protocol = {}
    ## Dictionary of protocols and fields to return for protocols.
    protocol_fields_by_protocol = {}
    ## Dictionary of protocols. The keys are the protocols and the values are a list of protocols in its family tree (ancestors).
    protocol_family_tree = {}
    
    ## Iterate through the protocol table to determine all of the protocols and their family tree.
    for protocol, protocol_values in controlled_vocabulary["parent_protocol"].items():
        parent_ids = []
        parent_id = protocol
        parent_protocol_values = protocol_values
        ## Keep looking for parents until you can't find anymore.
        while parent_id != "":
            if not "parentID" in parent_protocol_values:
                break
            else :
                parent_id = parent_protocol_values["parentID"]
                if parent_id != "":
                    if parent_id in controlled_vocabulary["parent_protocol"]:
                        parent_ids.append(parent_id)
                        parent_protocol_values = controlled_vocabulary["parent_protocol"][parent_id]
                    else:
                        break
                else:
                    protocol_family_tree[protocol] = parent_ids
        
        
    ## Iterate through each entry in the tagfield_scope table and pull out the fields.
    ## Fields are found by matching the parent_protocol.id field to a protocol in protocol_family_tree.
    ## If the scope_type of a match is "ignore" then it is a required field.
    for scope_id, scope_values in controlled_vocabulary["tagfield_scope"].items() :
        
        required_fields = ["parent_protocol.id", "scope_type", "tagfield.id", "table"]


        if all(r_field in scope_values for r_field in required_fields) and scope_values["parent_protocol.id"] in protocol_family_tree:
            ## Find the required field in the tagfield table and get its type.
            field = {}
            parent_protocol = scope_values["parent_protocol.id"]
            scope_type = scope_values["scope_type"]
            tagfield_id = scope_values["tagfield.id"]
            table = scope_values["table"]
            
            if tagfield_id in controlled_vocabulary["tagfield"]:
                if "validationCode" in controlled_vocabulary["tagfield"][tagfield_id] :
                    
                    field[tagfield_id] = {"validationCode" : controlled_vocabulary["tagfield"][tagfield_id]["validationCode"], 
                                          "scope_type" : scope_type,
                                          "table" : table}
                    
                    
                    ## If the field has values for allowed_values, min, or max then add them to the dictionary.
                    if "allowed_values" in scope_values and scope_values["allowed_values"] != "" and scope_values["allowed_values"] != []:
                        field[tagfield_id].update({"allowed_values" : scope_values["allowed_values"]})
                        
                    if "min" in scope_values and scope_values["min"] != "" and is_it_a_num(scope_values["min"]) :
                        field[tagfield_id].update({"min" : scope_values["min"]})
                        
                    if "max" in scope_values and scope_values["max"] != "" and is_it_a_num(scope_values["max"]):
                        field[tagfield_id].update({"max" : scope_values["max"]})
                        
                                        
                    if parent_protocol in record_fields_by_protocol:
                        record_fields_by_protocol[parent_protocol].update(field)
                    else:
                        record_fields_by_protocol[parent_protocol] = field
                    
                    
                    if "protocol" in table:
                        
                        ## This was really stupid to debug, but if you don't explicitly copy 
                        ## then when record_fields_by_protocol does an update it will change
                        ## the value in protocol_fields_by_protocol as well.
                        field_copy = copy.deepcopy(field)
                        
                        if parent_protocol in protocol_fields_by_protocol:
                            protocol_fields_by_protocol[parent_protocol].update(field_copy)
                        else:
                            protocol_fields_by_protocol[parent_protocol] = field_copy
                            
                    
                        
    ## Each protocol in record_fields_by_protocol and protocol_fields_by_protocol now has its own fields, 
    ## but not the ones it inherits from its family tree.
    ## Iterate over the family tree and add the fields from each ancestor to each protocol.
    for protocol, ancestors in protocol_family_tree.items() :
        for ancestor in ancestors:
            
            if ancestor in record_fields_by_protocol:
                if protocol in record_fields_by_protocol:
                    ## If the protocol already has a field that its ancestor has then don't overwrite it.
                    ## Only add fields from the ancestor that the protocol doesn't have.
                    for field_name, field_values in record_fields_by_protocol[ancestor].items():
                        if not field_name in record_fields_by_protocol[protocol]:
                            record_fields_by_protocol[protocol][field_name] = field_values
                else:
                    record_fields_by_protocol[protocol] = record_fields_by_protocol[ancestor]
                    
                    
            if ancestor in protocol_fields_by_protocol:
                if protocol in protocol_fields_by_protocol:
                    ## If the protocol already has a field that its ancestor has then don't overwrite it.
                    ## Only add fields from the ancestor that the protocol doesn't have.
                    for field_name, field_values in protocol_fields_by_protocol[ancestor].items():
                        if not field_name in protocol_fields_by_protocol[protocol]:
                            protocol_fields_by_protocol[protocol][field_name] = field_values
                else:
                    protocol_fields_by_protocol[protocol] = protocol_fields_by_protocol[ancestor]
                    
    return record_fields_by_protocol, protocol_fields_by_protocol






                    
                    
def compile_protocol_parents(parsed_metadata, controlled_vocabulary):
    """Loop over the protocol table in parsed_metadata and compile a dictionary where the keys are the protocols in the protocol table 
    and the values are that protocol's parent."""
    
    ## A message is already given to the user about which tables are present or not.
    if not "protocol" in parsed_metadata:
        return

    metadata_protocol_parents = {}
                    

    for protocol_name, protocol_fields in parsed_metadata["protocol"].items():
        if "parentID" in protocol_fields:
            metadata_protocol_parents[protocol_name] = protocol_fields["parentID"]


    return metadata_protocol_parents




def compile_protocol_CV_ancestor(parsed_metadata, controlled_vocabulary):
    """Loops over the protocol table in parsed_metadata and finds the closest 
    ancestor in each protocol's lineage that is in the controlled vocabulary. 
    Returns a dictionary where the keys are the protocols that have an ancestor 
    in the controlled vocabulary, and the value is that ancestor. If the protocol 
    itself is in the controlled vocabulary then its value is itself. If a protocol 
    has no ancestor in the controlled vocabulary then it will not be in the dictionary."""
    
    protocol_CV_ancestor = {}
    
    if not "protocol" in parsed_metadata or not "parent_protocol" in controlled_vocabulary:
        return protocol_CV_ancestor
    
    for protocol_name, protocol_fields in parsed_metadata["protocol"].items():
        original_protocol_name = protocol_name
        while not protocol_name in controlled_vocabulary["parent_protocol"]:
            if "parentID" in protocol_fields:
                protocol_name = protocol_fields["parentID"]
                if protocol_fields["parentID"] in parsed_metadata["protocol"]:
                    protocol_fields = parsed_metadata["protocol"][protocol_name]
                    
                else:
                    break
            else:
                break
                    
                    
        if protocol_name in controlled_vocabulary["parent_protocol"]:
            protocol_CV_ancestor[original_protocol_name] = protocol_name
            
            
    return protocol_CV_ancestor





def subject_species_check(parsed_metadata):
    """Checks that at least one subject has fields for taxonomy_id, species, and species_type."""
    
    if not "subject" in parsed_metadata:
        return


    species_fields = ["taxonomy_id", "species", "species_type"]


    for subject_name, fields in parsed_metadata["subject"].items():
            
        ## Determine which of the species fields are missing.
        missing_fields = set(species_fields) - set(fields)
        
        ## Determine which of the species fields are blank.
        blank_fields = [field_name for field_name, values in fields.items() if field_name in species_fields and all(["".join(value.split()) == "" for value in iterate_string_or_list(values)])]
        
        if len(missing_fields) == 0 and len(blank_fields) == 0:
            return
        
    ## If the function never returned there are no fields with all of the species fields.        
    print("There are no subjects with every species fields. Those fields are:\n\t" + "\n\t".join(species_fields) + "\n")





def obsolete_tag_replace(parsed_metadata, controlled_vocabulary):
    """Loop over every record in the parsed_metadata and look for obsolete fields. The list of obsolete fields 
    and their current version are in the obsolete_tag table of the controlled_vocabulary. If one is found 
    replace it with the current version."""
    
    if not "obsolete_tag" in controlled_vocabulary:
        return

    reCopier = copier.Copier()
    old_ids = controlled_vocabulary["obsolete_tag"]

    obsolete_tag_replaced = False

    for table in parsed_metadata:
        for record, fields in parsed_metadata[table].items():
            ## Replace obsolete tags.
            shared_ids = set(fields) & set(old_ids)
            if len(shared_ids) > 0:
                for tag_id in shared_ids:
                    fields[controlled_vocabulary["obsolete_tag"][tag_id]["replacement"]] = fields.pop(tag_id)
                obsolete_tag_replaced = True
                
            ## Replace attributes of obsolete tags.
            attributes = [(field_name, reCopier.value.group(1), reCopier.value.group(2)) for field_name in fields if reCopier(re.match("(.*)%(.*)", field_name)) and reCopier.value.group(1) in old_ids]
            if len(attributes) > 0:
                for tag_id in attributes:
                    fields[controlled_vocabulary["obsolete_tag"][tag_id[1]]["replacement"] + "%" + tag_id[2]] = fields.pop(tag_id[0])
                obsolete_tag_replaced = True
                
                
    return obsolete_tag_replaced 




#def compile_default_protocol_fields(controlled_vocabulary):
#    """Loop over the tagfield_scope table and find all of the records with a blank parent_protocol.id or 
#    an id of \"default_protocol\". Build a dictionary where the keys are the tables that each tagfield is for, 
#    and the values are a list of the tagfields in that table under the default_protocol."""
#    
#
#    if not "tagfield_scope" in controlled_vocabulary:
#        return
#
#    default_protocol_fields = {}
#            
#    for record_name, fields in controlled_vocabulary["tagfield_scope"]:
#        ## Make sure the record has the fields we need to access before accessing them.
#        ## Find records with a blank parent_protocol or one that is "default_protocol".
#        if "parent_protocol.id" in fields and (fields["parent_protocol.id"] == "default_protocol" or fields["parent_protocol.id"].strip() == ""):
#            if "table" in fields and "tagfield" in fields:
#                ## table should be a list field so for each table add the table to the dict if it isn't there
#                ## and add the field to the list in the dict if it isn't there.
#                for table in fields["table"]:
#                    if not table in default_protocol_fields:
#                        default_protocol_fields[table] = []
#                    if not fields["tagfield"] in default_protocol_fields[table]:
#                        default_protocol_fields[table].append(fields["tagfield"])







def main(argv) :
    global silent_mode
    global clean_output
    ## TODO Use docopt.
    ## Get the arguments given to the program.
    if len(argv) < 3:
        print(__doc__)
        exit(0)
    elif len(argv) < 4:
        argv.pop(0)
        parsed_metadata_filename = argv.pop(0)
        controlled_vocabulary_filename = argv.pop(0)
    else:
        argv.pop(0)
        parsed_metadata_filename = argv.pop(0)
        controlled_vocabulary_filename = argv.pop(0)
        while len(argv):
            if re.match("-s", argv[0]):
                argv.pop(0)
                silent_mode = True
            elif re.match("-c", argv[0]):
                argv.pop(0)
                if len(argv) > 0:
                    output_filename = argv.pop(0)
                else:
                    print("No filename given for clean output file.")
                    print(__doc__)
                    exit(0)
                clean_output = True
            else:
                print("Error in command line arguments")
                print(__doc__)
                exit(0)
        
    
    ## Read in the JSON files.
    if controlled_vocabulary_filename != "" :
        with open(controlled_vocabulary_filename,'r') as jsonFile :
            controlled_vocabulary = json.load(jsonFile)
            jsonFile.close()

    ## Check that the controlled vocabulary json has the required tables.
    if not set(cv_required_tables).issubset(controlled_vocabulary) :
        missing_tables = set(cv_required_tables) - set(controlled_vocabulary)
        print("Error:  The controlled vocabulary JSON file does not have all of the required tables. The table(s): \n\n" + '\n'.join(missing_tables) + "\n\nare missing.")

    
    if parsed_metadata_filename != "" :
        with open(parsed_metadata_filename,'r') as jsonFile :
            parsed_metadata = json.load(jsonFile)
            jsonFile.close()
            
    ## Check that the parsed metadata json has the required tables.
    if not set(pm_required_tables).issubset(parsed_metadata) :
        missing_tables = set(pm_required_tables) - set(parsed_metadata)
        print("Error:  The metadata JSON file does not have all of the required tables. The table(s): \n\n" + '\n'.join(missing_tables) + "\n\nare missing.")



    ## If the metadata has a tagfield_scope table then add its records to the controlled vocabulary.
    ## This will overwrite CV records with the ones in the metadata if they have records with the same id.
    pm_tagfield_scope_table = None
    if "tagfield_scope" in parsed_metadata and "tagfield_scope" in controlled_vocabulary:
        controlled_vocabulary["tagfield_scope"].update(parsed_metadata["tagfield_scope"])
        print("Records from the tagfield_scope table in the metadata were added to the tagfield_scope table of the controlled vocabulary.")
        ## Remove the tagfield_scope table from parsed_metadata now that it is in the CV, so that it doesn't cause problems later.
        pm_tagfield_scope_table = parsed_metadata.pop("tagfield_scope", None)



    ## Check all of the id fields for records in all tables of each JSON file to make sure the ids make sense.
    JSON_id_check(controlled_vocabulary, "controlled vocabulary")
    JSON_id_check(parsed_metadata, "metadata")
    
    ## Look for obsolete tags in the metadata and replace them with the current version.
    ## Function returns true if tags were replaced.
    tags_replaced = obsolete_tag_replace(parsed_metadata, controlled_vocabulary)
    ## If tags were replaced then overwrite the metadata JSON file.
    if tags_replaced:
        print("Obsolete tags were replaced in the metadata.")
        if pm_tagfield_scope_table != None:
            parsed_metadata["tagfield_scope"] = pm_tagfield_scope_table
        with open(parsed_metadata_filename,'w') as jsonFile :
            jsonFile.write(json.dumps(parsed_metadata, sort_keys=True, indent=2, separators=(',', ': ')))
            jsonFile.close()
    
    
    ## Check that each record in each table of the controlled vocabulary has all of its required fields.
    fields_and_allowed_values = {"type" : {"allowed_values" : ["sample_prep", "treatment", "collection", "storage", "master", "measurement", "default"],
                                           "validationCode" : ["text"],
                                           "scope_type" : ["ignore"]}, 
                                 "parentID" : {"allowed_values" : [],
                                               "validationCode" : ["text"],
                                               "scope_type" : ["ignore", "blank"]}}
    table_fields_and_allowed_values_check(controlled_vocabulary, "controlled vocabulary", "parent_protocol", fields_and_allowed_values)
    fields_and_allowed_values = {"validationCode": {"allowed_values" : ["text", "numeric", "list", "list_optional"],
                                                    "validationCode" : ["text", "list"],
                                                    "scope_type" : ["ignore", "blank"]}}
    table_fields_and_allowed_values_check(controlled_vocabulary, "controlled vocabulary", "tagfield", fields_and_allowed_values)
    fields_and_allowed_values = {"table" : {"allowed_values" : ["subject", "sample", "measurement", "factor", "project", "study", "protocol"],
                                            "validationCode" : ["text", "list"],
                                            "scope_type" : ["ignore"]}, 
                                 "scope_type" : {"allowed_values" : ["ignore", "optional", "blank", "warning", "tracking"],
                                                 "validationCode" : ["text", "list"],
                                                 "scope_type" : ["ignore"]},
                                 "tagfield.id" : {"allowed_values" : [],
                                                  "validationCode" : ["text"],
                                                  "scope_type" : ["ignore"]},
                                 "parent_protocol.id" : {"allowed_values" : [],
                                                         "validationCode" : ["text"],
                                                         "scope_type" : ["ignore", "blank"]},
                                 "allowed_values" : {"allowed_values" : [],
                                                     "validationCode" : ["list"],
                                                     "scope_type" : ["optional", "blank"]},
                                 "min" : {"allowed_values" : [],
                                          "validationCode" : ["numeric"],
                                          "scope_type" : ["optional"]},
                                 "max" : {"allowed_values" : [],
                                          "validationCode" : ["numeric"],
                                          "scope_type" : ["optional"]},}
    table_fields_and_allowed_values_check(controlled_vocabulary, "controlled vocabulary", "tagfield_scope", fields_and_allowed_values)
    fields_and_allowed_values = {"validationCode" : {"allowed_values" : ["text", "numeric", "list", "list_optional"],
                                                     "validationCode" : ["text", "list"],
                                                     "scope_type" : ["ignore", "blank"]}}
    table_fields_and_allowed_values_check(controlled_vocabulary, "controlled vocabulary", "tagfield_attribute", fields_and_allowed_values)


    ## Build required fields for metadata from controlled vocabulary.
    if "tagfield_scope" in controlled_vocabulary and "tagfield" in controlled_vocabulary:
        metadata_required_fields_and_allowed_values = {}
        for record_id, fields in controlled_vocabulary["tagfield_scope"].items():
            if "parent_protocol.id" in fields and (fields["parent_protocol.id"].strip() == "" or fields["parent_protocol.id"] == "default_protocol"):
                
                if "scope_type" in fields:
                    scope_type = fields["scope_type"]
                else:
                    scope_type = []
                    
                if "allowed_values" in fields:
                    allowed_values = fields["allowed_values"]
                else:
                    allowed_values = []
                
                if "tagfield.id" in fields :
                    
                    if fields["tagfield.id"] in controlled_vocabulary["tagfield"] and "validationCode" in controlled_vocabulary["tagfield"][fields["tagfield.id"]]:
                        validationCode = controlled_vocabulary["tagfield"][fields["tagfield.id"]]["validationCode"]
                    else:
                        validationCode = []
                    
                    if "table" in fields:
                        tables = fields["table"]
                        
                        for table in tables:
                            if table in metadata_required_fields_and_allowed_values:
                                metadata_required_fields_and_allowed_values[table].update({fields["tagfield.id"] : {"allowed_values" : allowed_values, "validationCode" : validationCode, "scope_type" : scope_type}})
                            else:
                                metadata_required_fields_and_allowed_values[table] = {fields["tagfield.id"] : {"allowed_values" : allowed_values, "validationCode" : validationCode, "scope_type" : scope_type}}
                    
        
        ## Check that each record in each table of the metadata has all of its required fields.
        for table, fields_and_allowed_values in metadata_required_fields_and_allowed_values.items():
            table_fields_and_allowed_values_check(parsed_metadata, "metadata", table, fields_and_allowed_values)
        



    ## Compile of list of fields for each protocol in the controlled vocabulary.
    record_fields_by_protocol = {}
    protocol_fields_by_protocol = {}
    record_fields_by_protocol, protocol_fields_by_protocol = compile_fields_by_protocol(controlled_vocabulary)
    
    ## Get the anestor in the controlled vocabulary for each protocol in the parsed metadata.
    protocol_CV_ancestor = {}
    protocol_CV_ancestor = compile_protocol_CV_ancestor(parsed_metadata, controlled_vocabulary)
    
    ## Compile all of the default_protocol fields for each table.
    default_protocol_fields = metadata_required_fields_and_allowed_values
    
    
    ## Check all of the subjects and samples to make sure all of their fields are allowed.
    table_fields_check(record_fields_by_protocol, parsed_metadata, "sample", controlled_vocabulary, protocol_CV_ancestor, default_protocol_fields)
    table_fields_check(record_fields_by_protocol, parsed_metadata, "subject", controlled_vocabulary, protocol_CV_ancestor, default_protocol_fields)
    table_fields_check(record_fields_by_protocol, parsed_metadata, "measurement", controlled_vocabulary, protocol_CV_ancestor, default_protocol_fields)
    
    ## Check all of the subjects and samples to make sure they have the correct protocols based on their ancestry.
    SS_protocol_check(parsed_metadata, "sample", controlled_vocabulary)
    SS_protocol_check(parsed_metadata, "subject", controlled_vocabulary)
    
    ## Check that every measurement record has at least one protocol of the measurement type.
    measurement_protocol_check(parsed_metadata, controlled_vocabulary)
    
    
#    ## Check that all subjects have a sample for a parent if they have a parent.
#    subject_inheritance_check(parsed_metadata)
    
    ## Check that each protocol in the metadata has an ancestor in the controlled vocabulary and that they are the same type.
    protocol_lineage_check(parsed_metadata, controlled_vocabulary)
    ## Check that each protocol has the required fields and that they are the right type.
    protocol_fields_check(parsed_metadata, protocol_fields_by_protocol, protocol_CV_ancestor, controlled_vocabulary, default_protocol_fields)
    ## Check that every protocol in the protocol table is used by a subject or sample.
    protocol_all_used_check(parsed_metadata)
    ## Check that every protocol has a unique description.
    protocol_description_check(parsed_metadata)
    
    
    ## Check that all factors are used by at least one subject or sample.
    factor_all_used_check(parsed_metadata)
    
    
    ## Check that subjects with no parents (root subjects) have taxonomy_id, species, and species_type.
    subject_species_check(parsed_metadata)
        
    ## If the option is set and the metadata can be cleaned then clean it and save it to the filepath entered by the user.
    if clean_output:
        if JSON_clean_up(parsed_metadata, controlled_vocabulary):
            if pm_tagfield_scope_table != None:
                parsed_metadata["tagfield_scope"] = pm_tagfield_scope_table
            # save to json
            with open(output_filename,'w') as jsonFile :
                jsonFile.write(json.dumps(parsed_metadata, sort_keys=True, indent=2, separators=(',', ': ')))
                jsonFile.close()

        
        
if __name__ == "__main__":
	main(sys.argv)
    
