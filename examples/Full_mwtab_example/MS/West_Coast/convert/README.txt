The convert command produces both a JSON file and text file that are in the mwtab format. If you 
run the commands below under Run Command you will see some warnings and errors:
1. In the biogenic amines and lipids files, a warning about the "ion" column possibly having incorrect values.
    This is safe to ignore for this dataset. This warning is meant to catch instances when a column that should have only 1 value is missing that value, but 
    it can have false positives in cases like this where many values are the same, but some are different.
2. In the metabolism file, errors about FLOW_GRADIENT, COLUMN_TEMPERATURE, SOLVENT_A, and SOLVENT_B in the CHROMATOGRAPHY section being a null value.
    The error itself will tell you that you might need to ignore it, and that is the case here. These fields are required by Metabolomics Workbench, but don't 
    have coherent values for every possible experiment. Validate errs on the side of caution and prints these errors so users double check that they have correct values.

Note that this uses the default study and analysis ID of 000000, but you would need to change this to the 
correct ones given to you by the Metabolomics Workbench either manually after running the conversion or 
changing the mwtab_ms_conversion_directives.json to have the correct IDs.

Example Directives:

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



Biogenic Amines Pos:
Input Files:
biogenic_amines_pos_extraction.json
mwtab_ms_conversion_directives.json

Otuput Files:
biogenic_amines_pos_mwtab.json
biogenic_amines_pos_mwtab.txt

Run Command:
messes convert mwtab ms biogenic_amines_pos_extraction.json biogenic_amines_pos_mwtab --override mwtab_ms_conversion_directives.json


Biogenic Amines Neg:
Input Files:
biogenic_amines_neg_extraction.json
mwtab_ms_conversion_directives.json

Otuput Files:
biogenic_amines_neg_mwtab.json
biogenic_amines_neg_mwtab.txt

Run Command:
messes convert mwtab ms biogenic_amines_neg_extraction.json biogenic_amines_neg_mwtab --override mwtab_ms_conversion_directives.json



Lipids Pos:
Input Files:
lipids_pos_extraction.json
mwtab_ms_conversion_directives.json

Otuput Files:
lipids_pos_mwtab.json
lipids_pos_mwtab.txt

Run Command:
messes convert mwtab ms lipids_pos_extraction.json lipids_pos_mwtab --override mwtab_ms_conversion_directives.json


Lipids Neg:
Input Files:
lipids_neg_extraction.json
mwtab_ms_conversion_directives.json

Otuput Files:
lipids_neg_mwtab.json
lipids_neg_mwtab.txt

Run Command:
messes convert mwtab ms lipids_neg_extraction.json lipids_neg_mwtab --override mwtab_ms_conversion_directives.json



Metabolism:
Input Files:
metabolism_extraction.json
mwtab_ms_conversion_directives.json

Otuput Files:
metabolism_mwtab.json
metabolism_mwtab.txt

Run Command:
messes convert mwtab ms metabolism_extraction.json metabolism_mwtab --override mwtab_ms_conversion_directives.json



