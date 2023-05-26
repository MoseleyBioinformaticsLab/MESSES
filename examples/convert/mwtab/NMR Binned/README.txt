To reproduce the outputs from the input run the following command:

    messes convert mwtab nmr_binned NMR_binned_base_input.json NMR_binned_output

Note that there are some default settings that are likely to need changed between each run, such as 
the analysis ID and study ID or the sibling match value.

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
  },
"SUBJECT_SAMPLE_FACTORS": {
    "no_id_needed": {
      "code": "mwtab_functions.create_subject_sample_factors(input_json, sibling_match_value="some_protocol_id")",
      "id": "no_id_needed",
      "value_type": "section"
    }
  }
}


To run with these new settings:

   messes convert mwtab nmr_binned NMR_binned_base_input.json NMR_binned_output --update update_directives.json


Input Files:
NMR_binned_base_input.json

Output Files:
NMR_binned_output.json
NMR_binned_output.txt