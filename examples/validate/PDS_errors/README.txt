Run the commands under Run Command to see validation errors when validating the protocol-dependent schema. Try manually 
fixing the errors and rerunning until there are no more errors.

Input Files:
PDS_base_bad_type.json

PDS_base_no_parent_table.json

PDS_base_parent_protocol_errors.json


Run Commands:
messes validate pds PDS_base_bad_type.json

messes validate pds PDS_base_no_parent_table.json

messes validate pds PDS_base_parent_protocol_errors.json