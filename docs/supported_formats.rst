Supported Conversion Formats
============================
mwTab
~~~~~
mwTab is the name of the format used by the `Metabolomics Workbench`_, and there are some slight differences depending on what 
type of data you wish to upload. Metabolomics Workbench accepts 3 kinds of data, mass spec (MS), binned nuclear magnetic resonance (NMR binned), 
and labeled NMR (will be referred to as just NMR). Accordingly, the convert command has a sub-command for each type (ms, nmr, and nmr_binned). 
Simply use the appropriate sub-command for whatever type of data you are trying to upload to the Metabolomics Workbench. 

There are a few things to be aware of. First, the default value for the analysis ID and study ID are AN000000 and ST000000, respectively. 
You will need to change these to the correct values that the Metabolomics Workbench gives you. You can do this manually after creating 
the files, or by using the update option:

update_directives.json:

.. code:: console

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
    
Command Line:

.. code:: console

    messes convert mwtab ms input_file.json my_output_name --update update_directives.json
    
Note that the built-in 
conversion creates a minimum submission based on the Metabolomics Workbench requirements, and optionally tries to add some information if 
available. Specifically, the "optional_headers" for the "Metabolites" sections of the conversion directives will add the extra fields listed 
there for metabolites if they exist. If you have fields that aren't in that list, you need to add them. Also add them to the "exclusion_headers" 
list in the "Extended" section so they don't get added twice to 2 different sections. The procedure is similar to the one above for changing 
the analysis and study IDs.

update_directives.json:

.. code:: console

    {
    "MS_METABOLITE_DATA": {
      "Extended": {
        "required": "False",
        "exclusion_headers": [
          "id",
          "intensity",
          "intensity%type",
          "intensity%units",
          "assignment",
          "assignment%method",
          "entity.id",
          "protocol.id",
          "formula",
          "compound",
          "isotopologue",
          "isotopologue%type",
          "new_field_1",
          "new_field_2"
        ],
        "fields_to_headers": "True",
        "headers": [
          "\"Metabolite\"=assignment",
          "\"sample_id\"=entity.id"
        ],
        "id": "Extended",
        "sort_by": [
          "assignment"
        ],
        "sort_order": "ascending",
        "table": "measurement",
        "value_type": "matrix",
        "values_to_str": "True"
      },
      "Metabolites": {
        "required": "True",
        "collate": "assignment",
        "headers": [
          "\"Metabolite\"=assignment"
        ],
        "optional_headers": [
            "assignment%method",
            "formula",
            "compound",
            "isotopologue",
            "isotopologue%type",
            "new_field_1",
            "new_field_2"
            ],
        "id": "Metabolites",
        "sort_by": [
          "assignment"
        ],
        "sort_order": "ascending",
        "table": "measurement",
        "value_type": "matrix",
        "values_to_str": "True"
      }
     }
    }

Convert assumes the input JSON is following the table schema as described in the :doc:`experiment_description_specification` section, 
so if your JSON has different table names or a different structure then you will need to override the directives. You may also 
need to change the SUBJECT_SAMPLE_FACTORS directive. The SUBJECT_SAMPLE_FACTORS are built using a function that has the same 
assumptions as convert, but also some additional ones. It assumes when building lineages for a sample that some siblings should be included. 
To find these siblings, it looks for a specific field and value for that field in the entity records. 
The default field and value are "protocol.id" and "protein_extraction", respectively. You may need to change these values, if you 
want to identify siblings in a different way or leave them out.

Changing SUBJECT_SAMPLE_FACTORS Example:

.. code:: console
    
    * Change the value to look for in protocol.id.
    {
    "SUBJECT_SAMPLE_FACTORS": {
        "no_id_needed": {
          "code": "mwtab_functions.create_subject_sample_factors(input_json, sibling_match_value="some_protocol_id")",
          "id": "no_id_needed",
          "value_type": "section"
        }
      }
    }
    
    * Change the value and field.
    {
    "SUBJECT_SAMPLE_FACTORS": {
        "no_id_needed": {
          "code": "mwtab_functions.create_subject_sample_factors(input_json, sibling_match_field="some_field", sibling_match_value="some_value")",
          "id": "no_id_needed",
          "value_type": "section"
        }
      }
    }
    
    * Don't look for siblings.
    {
    "SUBJECT_SAMPLE_FACTORS": {
        "no_id_needed": {
          "code": "mwtab_functions.create_subject_sample_factors(input_json, sibling_match_value=None)",
          "id": "no_id_needed",
          "value_type": "section"
        }
      }
    }
    
The SUBJECT section is filled out by selecting the first subject type entity, so make sure the first subject entity has the 
"species", "species_type", and "taxonomy_id" fields.

The SAMPLE_TYPE section is filled out by selecting the first collection type protocol, so make sure the first collection protocol 
has a "sample_type" field.

The CHROMATOGRAPHY, MS, and NM sections are filled out by selecting the first protocol with a machine_type field that has a value 
of either "MS" or "NMR". That protocol is expected to have certain fields that differ slightly based on whether the value is 
"MS" or "NMR". 
For a "MS" submission the "chromatography_type", "column_name", "chromatography_instrument_name", "instrument", 
"instrument_type", "ion_mode", and "ionization" fields are required on the protocol, and "description" and 
"chromatography_description" are optional.
For a "NMR" submission the "instrument", "instrument_type", "NMR_experiment_type", "spectrometer_frequency",
and "spectrometer_frequency%units" fields are required on the protocol, and "acquisition_time", "acquisition_time%units", 
"baseline_correction_method", "chemical_shift_ref_cpd", "NMR_probe", "NMR_solvent", "NMR_tube_size", "NMR_tube_size%units", 
"pulse_sequence", "relaxation_delay", "relaxation_delay%units", "shimming_method", "standard_concentration", 
"standard_concentration%units", "temperature", "temperature%units", and "water_suppression" are optional.

The SAMPLEPREP section is filled out by combining all of the sample_prep type protocols and sorts them using the "order" field 
on the protocols, so make sure each sample_prep type protocol has an "order" field.

Lastly, the built-in directives for the mwTab format only construct a minimum required version. There are more records that can 
be added to the tables, and you can use the same update method as previously shown to add them in if desired. You can view the 
full specification for the format here: https://www.metabolomicsworkbench.org/data/tutorials.php

How SUBJECT_SAMPLE_FACTORS (SSF) Are Determined
-----------------------------------------------
The SUBJECT_SAMPLE_FACTORS section is created by first finding all of the samples associated with measurement records. Then 
lineages for each sample are determined. Siblings are added to the lineages if they meet the right user determined conditions. 
By default, a sibling is included if the "protocol.id" field has "protein_extraction". Then for each sample associated with a measurement record, 
the factors and nearest subject ancestor are determined. Raw files are expected to be in a list on the measurement protocol as described 
in option 5 of the :ref:`raw-files-method` section in the documentation. The function used 
to create this section is called create_subject_sample_factors and it can be found in the :doc:`api` section of the documentation. 
If the preferred table schema and controlled vocabulary are followed, then there is likely very little you might need to change here. 
But if you do need to make a change, then all of the parameters for the function are in the API documentation.



.. _Metabolomics Workbench: http://www.metabolomicsworkbench.org