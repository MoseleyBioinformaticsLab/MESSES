# -*- coding: utf-8 -*-
"""
Code for processing MWTab conversion.
"""

import sys

import mwtab


def preprocessing(input_json: dict) -> dict:
    """
    """
    return input_json


def postprocessing(output_json: dict, input_json_filepath: str, output_filename: str, sub_command: str) -> None:
    """
    """
    
    ## Optional way to do things compared to the code block below this.
    # with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as tp:
    #     tp.write(json.dumps(output_json))
    #     tp.seek(0)
    #     mwfile = mwtab.mwtab.MWTabFile("")
    #     mwfile.read(tp)
    # with open(args["<output-name>"], 'w', encoding="utf-8") as outfile:
    #     mwfile.write(outfile, file_format="mwtab")
    
    mwtab_key_order = {'METABOLOMICS WORKBENCH':['STUDY_ID', 'ANALYSIS_ID', 'VERSION', 'CREATED_ON'], 
                       'PROJECT':[], 
                       'STUDY':[], 
                       'SUBJECT':[], 
                       'SUBJECT_SAMPLE_FACTORS':[], 
                       'COLLECTION':[], 
                       'TREATMENT':[], 
                       'SAMPLEPREP':[], 
                       'CHROMATOGRAPHY':[], 
                       'ANALYSIS':[], 
                       }
            
    extended_key_order = {"ms":{'MS':[], 
                                'MS_METABOLITE_DATA':['Units', 'Data', 'Metabolites', 'Extended']},
                          "nmr":{'NM':[], 
                                 'NMR_METABOLITE_DATA':['Units', 'Data', 'Metabolites', 'Extended']},
                          "nmr_binned":{'NM':[], 
                                        'NMR_BINNED_DATA':['Units', 'Data']}}
    
    mwtab_key_order.update(extended_key_order[sub_command])
    
    
    mwtabfile = mwtab.mwtab.MWTabFile(input_json_filepath)
    
    ## The mwtab package doesn't ensure correct ordering itself, so we have to make sure everything is ordered correctly.
    for key, sub_keys in mwtab_key_order.items():
        if key in output_json:
            mwtabfile[key] = {}
            for sub_key in sub_keys:
                if sub_key in output_json[key]:
                    mwtabfile[key][sub_key] = output_json[key][sub_key]
            if isinstance(output_json[key], dict):
                mwtabfile[key].update(output_json[key])
            else:
                mwtabfile[key] = output_json[key]
    
    ## If you just update the dict then things can be out of order, so switched to the above method until mwtab is improved.
    # mwtabfile.update(output_json)
    mwtabfile.header = " ".join(
        ["#METABOLOMICS WORKBENCH"]
        + [item[0] + ":" + item[1] for item in mwtabfile["METABOLOMICS WORKBENCH"].items() if item[0] not in ["VERSION", "CREATED_ON"]]
    )            
    
    validated_file, errors = mwtab.validate_file(mwtabfile)
    
    if "Status: Passing" in errors:
        mwtab_save_name = output_filename + ".txt"
        with open(mwtab_save_name, 'w', encoding='utf-8') as outfile:
            mwtabfile.write(outfile, file_format="mwtab")
    else:
        print("Error:  An error occured when validating the mwtab file.", file=sys.stderr)
        print(errors, file=sys.stderr)
        sys.exit()



