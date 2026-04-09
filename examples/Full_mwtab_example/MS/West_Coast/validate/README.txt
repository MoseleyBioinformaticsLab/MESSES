Since we have already dealt with any issues to give you a working example the validation is not terribly illustrative. 
For your own data this step would be more important. The workflow is to tag your data, extract it, and then validate, 
but once in the validate step you would repeat the procedure to fix any errors in validation until you get no more errors. 
If you run the commands below under Run Command you should see no errors or warnings printed.


Biogenic Amines Pos:
Input Files:
biogenic_amines_pos_extraction.json
protocol-dependent_schema.xlsx

Run Command:
messes validate json biogenic_amines_pos_extraction.json --pds protocol-dependent_schema.xlsx --format mwtab

Biogenic Amines Neg:
Input Files:
biogenic_amines_neg_extraction.json
protocol-dependent_schema.xlsx

Run Command:
messes validate json biogenic_amines_neg_extraction.json --pds protocol-dependent_schema.xlsx --format mwtab


Lipids Pos:
Input Files:
lipids_pos_extraction.json
protocol-dependent_schema.xlsx

Run Command:
messes validate json lipids_pos_extraction.json --pds protocol-dependent_schema.xlsx --format mwtab

Lipids Neg:
Input Files:
lipids_neg_extraction.json
protocol-dependent_schema.xlsx

Run Command:
messes validate json lipids_neg_extraction.json --pds protocol-dependent_schema.xlsx --format mwtab


Metabolism:
Input Files:
metabolism_extraction.json
protocol-dependent_schema.xlsx

Run Command:
messes validate json metabolism_extraction.json --pds protocol-dependent_schema.xlsx --format mwtab
