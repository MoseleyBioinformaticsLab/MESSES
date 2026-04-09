This continues from the example started in the extract folder. Since we have already dealt with any 
issues to give you a working example the validation is not terribly illustrative. For your own data 
this step would be more important. The workflow is to tag your data, extract it, and then validate, 
but once in the validate step you would repeat the procedure to fix any errors in validation until 
you get no more errors. If you run the command below under Run Command you should see no errors or 
warnings printed. If you remove the '--silent nuisance' portion you will see many warnings that are 
safe to ignore for this dataset. The 'nuisance' level of the silent option was specifically created 
to silence warnings that are known to be ignorable in certain circumstances.

Input Files:
extracted_result.json
protocol-dependent_schema.json

Run Command:
messes validate json extracted_result.json --pds protocol-dependent_schema.json --format mwtab --silent nuisance