This continues from the example started in the extract folder, and should be done after the validation 
step. The convert command produces both a JSON file and text file that are in the mwtab format. If you 
run the command below under Run Command you should see no errors or warnings printed. 

Note that this uses the default study and analysis ID of 000000, but you would need to change this to the 
correct ones given to you by the Metabolomics Workbench either manually after running the conversion or 
using the update option.

Example Update Directives:

{
"METABOLOMICS WORKBENCH": {
    "ANALYSIS_ID": {
      "id": "ANALYSIS_ID",
      "override": "AN001234",
      "value_type": "str"
    },
    "STUDY_ID": {
      "id": "STUDY_ID",
      "override": "ST005678",
      "value_type": "str"
    }
  }
}


To run with these new settings:

   messes convert mwtab ms extracted_result.json output --update update_directives.json

Note that you will see errors about "FLOW_RATE" and "COLUMN_TEMPERATURE" in the output, but they should be ignored.
FLOW_GRADIENT, FLOW_RATE, COLUMN_TEMPERATURE,SOLVENT_A, and SOLVENT_B are all newly required fields 
that were added after depositing this dataset, so please ignore any warnings or errors associated with those fields.

Input Files:
extracted_result.json

Otuput Files:
output.json
output.txt

Run Command:
messes convert mwtab ms extracted_result.json output