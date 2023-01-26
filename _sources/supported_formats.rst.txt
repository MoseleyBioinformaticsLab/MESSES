Supported Formats
=================
mwTab
~~~~~
mwTab is the name of the format used by the `Metabolomics Workbench`_, and there are some slight differences depending on what 
type of data you wish to upload. Metabolomics Workbench accepts 3 kinds of data, mass spec (MS), binned nuclear magnetic resonance (NMR binned), 
and labeled NMR (will be referred to as just NMR). Accordingly, MESSES convert has a sub-command for each type (ms, nmr, and nmr_binned). 
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
    
The next is that convert assumes the input JSON is following the table schema as described in the :doc:`table_schema` section, 
so if your JSON has different table names or a different structure then you will need to override the directives. You may also 
need to change the SUBJECT_SAMPLE_FACTORS directive. The SUBJECT_SAMPLE_FACTORS are built using a function that has the same 
assumptions as convert, but also some additional ones. It assumes when building lineages for a sample that some siblings will 
also want to be included, and to find these siblings it looks for a specific field and value for that field in the entity records. 
The default field and value are "protocol.id" and "protein_extraction", respectively. You may need to change these values if you 
want to identify siblings in a different way or leave them out.

Changing SUBJECT_SAMPLE_FACTORS Example:

.. code:: console
    
    # Change the value to look for in protocol.id.
    {
    "SUBJECT_SAMPLE_FACTORS": {
        "no_id_needed": {
          "code": "mwtab_functions.create_subject_sample_factors(input_json, sibling_match_value="some_protocol_id")",
          "id": "no_id_needed",
          "value_type": "section"
        }
      }
    }
    
    # Change the value and field.
    {
    "SUBJECT_SAMPLE_FACTORS": {
        "no_id_needed": {
          "code": "mwtab_functions.create_subject_sample_factors(input_json, sibling_match_field="some_field", sibling_match_value="some_value")",
          "id": "no_id_needed",
          "value_type": "section"
        }
      }
    }
    
    # Don't look for siblings.
    {
    "SUBJECT_SAMPLE_FACTORS": {
        "no_id_needed": {
          "code": "mwtab_functions.create_subject_sample_factors(input_json, sibling_match_value=None)",
          "id": "no_id_needed",
          "value_type": "section"
        }
      }
    }

Lastly, the built-in directives for the mwTab format only construct a minimum required version. There are more records that can 
be added to the tables, and you can use the same update method as previously shown to add them in if desired. You can view the 
full specification for the format here: https://www.metabolomicsworkbench.org/data/tutorials.php

How SUBJECT_SAMPLE_FACTORS (SSF) Are Determined
-----------------------------------------------
The SUBJECT_SAMPLE_FACTORS section is created by first finding all of the samples associated with measurement records. Then 
lineages for each sample are determined. Siblings are added to the lineages if they meet the right user determined conditions. 
By default it is if the "protocol.id" field is "protein_extraction". Then for each sample associated with a measurement record 
the factors and nearest subject ancestor are determined. All ancestors, the sample itself, and any siblings that were added 
to the lineages are searched for raw files and are added into the SSF if found. The function used to create this section is 
called create_subject_sample_factors and it can be found in the :doc:`api` section of the documentation. If the preferred 
table schema and controlled vocabulary are followed then there is likely very little you might need to change here, but if you 
do all of the parameters for the function are in the API documentation.



.. _Metabolomics Workbench: http://www.metabolomicsworkbench.org