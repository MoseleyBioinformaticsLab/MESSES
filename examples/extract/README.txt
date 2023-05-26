This example has 2 files. The metadata file that has had tags added manually and the measurements file that uses automation and modification 
tags heavily. The Run Commands show how you can extract each file individually into their own JSON file and how they can be merged together 
in one file. Note that the last 2 commands use the --silent option. This is because there are many compounds in the #modify sheet of the 
measurements file that do not match a measurement, so many "never matched" warnings are printed. This is okay to ignore for this example.


Input Files:
mouse_experiment_metadata.xlsx

MS_measurements_truncated.xlsx


Output Files:
metadata.json

measurements.json

metadata_and_measurements.json


Run Commands:
messes extract mouse_experiment_metadata.xlsx --output metadata

messes extract MS_colon_measurements_truncated.xlsx --output measurements --silent

messes extract mouse_experiment_metadata.xlsx MS_colon_measurements_truncated.xlsx --output metadata_and_measurements --silent