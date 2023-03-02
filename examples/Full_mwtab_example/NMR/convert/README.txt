This continues from the example started in the extract folder, and should be done after the validation 
step. The convert command produces both a JSON file and text file that are in the mwtab format. If you 
run the command below under Run Command you should see no errors or warnings printed. If you remove the 
'--silent' portion you will see many warnings that are safe to ignore for this dataset.

Input Files:
extracted_result.json

Otuput Files:
output.json
output.txt

Run Command:
messes convert mwtab nmr extracted_result.json output --silent