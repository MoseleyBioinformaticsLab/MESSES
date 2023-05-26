Conversion Directives
=====================

Introduction
~~~~~~~~~~~~
The convert command is used to convert extracted and validated data from it's intermediate JSON form to 
the final desired format. The command was largely created with the goal of putting data into its 
preferred format for deposition into an online data repository such as `Metabolomics Workbench`_. 
Many popular data formats have a unique text format specialized to their niche, but also have a 
JSON version of the format as well. It is often easier to go from the JSON version of the format 
to the specialized format and vice versa. It is also easier to go from one JSON format 
to another JSON format, so the convert command was designed to transform the JSON format described in the 
:doc:`experiment_description_specification` to the JSON version of any of the supported formats and then to the final 
niche format. The convert command also supports simple JSON-to-JSON conversion through the 
"generic" sub-command.

To support the JSON-to-JSON conversion a relatively simple set of directives were developed. The 
conversion directives file is expected to be a JSON or tagged tabular file with a certain structure. 
The general JSON structure is shown below.

.. code:: console

    {
    <table_name_1>: {
        <record_name_1>:{
            <field_name_1>: <field_value_1>,
            <field_name_2>: <field_value_2>,
            ...
            },
        ...
        },
    ...
    }

This structure can be mimicked using the export part of the tagging system mentioned in the :doc:`tagging` 
section of this documentation, and tagged tabular files are acceptable input for the 
conversion directives of the convert command. The JSON structure above is shown below using 
export tags.

+--------+---------------------+-------------------+-------------------+
| #tags  | #<table_name_1>.id  | #.<field_name_1>  | #.<field_name_2>  |
+========+=====================+===================+===================+
|        | <record_name_1>     | <field_value_1>   | <field_value_2>   |
+--------+---------------------+-------------------+-------------------+

Each table in the directives translates to a table of the same name in the converted JSON, 
and each record name translates to a record of the same name. The fields for each 
record control how each record is created from the input JSON. Only certain field names 
have any meaning. Every record must have a "value_type" field, and the value of this 
field determines the other required and meaningful fields the record can have. The 
allowed values for the "value_type" field are "str", "matrix", and "section". The "str" 
type produces a single string value for the record. The "matrix" type produces a list 
of dictionaries (aka an array of objects) for the record. The "section" type can produce 
anything, but what is produced is for the whole table. Examples and more detail for each 
value_type are given below.


str Directives
~~~~~~~~~~~~~~
The str directive assumes that you want to create a string value from information in the 
input JSON, and that that information is contained within a single table. The value can 
be built from a single record in the table or by iterating over all of them, and the 
records can be sorted and filtered before building. There are a few common patterns to 
building a str directive.

Override
--------
To simply specify the string value directly use the "override" field.

Directive as JSON
+++++++++++++++++

.. code:: console

    {
    "ANALYSIS": {
        "ANALYSIS_TYPE": {
            "value_type": "str",
            "override": "MS"
            }
        }
    }

Tagged Equivalent
+++++++++++++++++

+--------+---------------+-------------+---------------+
| #tags  | #ANALYSIS.id  | #.override  | #.value_type  |
+========+===============+=============+===============+
|        | ANALYSIS_TYPE | MS          | str           |
+--------+---------------+-------------+---------------+

Output JSON
+++++++++++

.. code:: console

    {
    "ANALYSIS": {
        "ANALYSIS_TYPE": "MS"
        }
    }


Code
----
If you need to generate a string value from the input JSON in a more complex way 
than can be done with the current supported directives, you can use the "code" field 
to give the program Python code directly to evaluate. What is in the code field will 
be delivered directly to eval(), and the name of the internal variable for the input 
JSON is "input_json". You can also use the "import" field to import any user created 
libraries into the program. The "import" value should be a path to the file to import.

Directive as JSON
+++++++++++++++++

.. code:: console

    {
    "METABOLOMICS WORKBENCH": {
        "CREATED_ON": {
            "value_type": "str",
            "code": "str(datetime.datetime.now().date())"
            }
        }
    }

Tagged Equivalent
+++++++++++++++++

+--------+-----------------------------+--------------------------------------+---------------+
| #tags  | #METABOLOMICS WORKBENCH.id  | #.code                               | #.value_type  |
+========+=============================+======================================+===============+
|        | CREATED_ON                  | str(datetime.datetime.now().date())  | str           |
+--------+-----------------------------+--------------------------------------+---------------+

Output JSON
+++++++++++

.. code:: console

    {
    "METABOLOMICS WORKBENCH": {
        "CREATED_ON": "2023-01-04"    # Will change to be date when the program is ran.
        }
    }


Record ID
---------
If the value is simply in a field or combination of fields in a record of the input 
JSON, use the "record_id" field to point to that record directly and build the value 
from its fields.

Directive as JSON
+++++++++++++++++

.. code:: console

    {
    "ANALYSIS": {
        "ANALYSIS_TYPE": {
            "value_type": "str",
            "table": "study",
            "record_id": "Study 1",
            "fields": ["analysis_type"]
            }
        }
    }

Tagged Equivalent
+++++++++++++++++

+--------+---------------+---------------+----------+-----------------+--------------+
| #tags  | #ANALYSIS.id  | #.value_type  | #.table  | *#.fields       | #.record_id  |
+========+===============+===============+==========+=================+==============+
|        | ANALYSIS_TYPE | str           | study    | analysis_type   | Study 1      |
+--------+---------------+---------------+----------+-----------------+--------------+

Input JSON
++++++++++

.. code:: console

    {
    "study": {
        "Study 1": {
            "analysis_type": "MS",
            "species": "mus musculus",
            "instrument": "Orbitrap",
            "ion_mode": "negative"
            }
        }
    }

Output JSON
+++++++++++

.. code:: console

    {
    "ANALYSIS": {
        "ANALYSIS_TYPE": "MS"
        }
    }


First Record
------------
Similar to specifying a record ID, if you want to build the string value from a record 
but do not know its ID, you can omit the "record_id" field and the first record in 
the specified table will be used. This alone is generally not enough though and it 
is recommended to either use the "sort_by" and "sort_order" fields to first sort the 
records before selecting the first one, or use the "test" field to select the first 
record that matches the test.

Directive as JSON
+++++++++++++++++

.. code:: console

    # Using test.
    {
    "ANALYSIS": {
        "INSTRUMENT": {
            "value_type": "str",
            "table": "study",
            "fields": ["instrument"],
            "test": "analysis_type=MS"
            }
        }
    }
    
    # Using sort.
    {
    "ANALYSIS": {
        "INSTRUMENT": {
            "value_type": "str",
            "table": "study",
            "fields": ["instrument"],
            "sort_by": "analysis_type",
            "sort_order": "ascending"
            }
        }
    }

Tagged Equivalent
+++++++++++++++++

+--------+---------------+---------------+----------+--------------+---------------------+
| #tags  | #ANALYSIS.id  | #.value_type  | #.table  | *#.fields    | #.test              |
+========+===============+===============+==========+==============+=====================+
|        | INSTRUMENT    | str           | study    | instrument   | analysis_type=MS    |
+--------+---------------+---------------+----------+--------------+---------------------+

+--------+---------------+---------------+----------+------------+----------------+---------------+
| #tags  | #ANALYSIS.id  | #.value_type  | #.table  | *#.fields  | *#.sort_by     | #.sort_order  |
+========+===============+===============+==========+============+================+===============+
|        | INSTRUMENT    | str           | study    | instrument | analysis_type  | ascending     |
+--------+---------------+---------------+----------+------------+----------------+---------------+

Input JSON
++++++++++

.. code:: console

    {
    "study": {
        "Study 1": {
            "analysis_type": "NMR",
            "species": "mus musculus",
            "instrument": "Agilent"
            },
        "Study 2": {
            "analysis_type": "MS",
            "species": "mus musculus",
            "instrument": "Orbitrap",
            "ion_mode": "negative"
            }
        }
    }
    
    # After sorting.
    {
    "study": {
        "Study 2": {
            "analysis_type": "MS",
            "species": "mus musculus",
            "instrument": "Orbitrap",
            "ion_mode": "negative"
            },
        "Study 1": {
            "analysis_type": "NMR",
            "species": "mus musculus",
            "instrument": "Agilent"
            }
        }
    }

Output JSON
+++++++++++

.. code:: console

    {
    "ANALYSIS": {
        "Instrument": "Orbitrap"
        }
    }


For Each
--------
If the information to build the value is spread across several records, then use the 
"for_each" field to loop over all the records in the table and build the value by 
concatenating the values with a delimiter. Use the "delimiter" field to specify the 
delimiter to use. The default is no delimiter aka the empty string. Generally, simply 
looping over all records is not enough, so use the "test" field to only use the records 
matching some test.

Directive as JSON
+++++++++++++++++

.. code:: console

    {
    "SAMPLEPREP": {
        "SAMPLEPREP_SUMMARY": {
            "delimiter": "\" \"",
            "fields": [
              "description"
            ],
            "for_each": "True",
            "id": "SAMPLEPREP_SUMMARY",
            "required": "True",
            "sort_by": [
              "id"
            ],
            "sort_order": "ascending",
            "table": "protocol",
            "test": "type=sample_prep",
            "value_type": "str"
            }
        }
    }

Tagged Equivalent
+++++++++++++++++

+--------+---------------------+--------------+--------------+-------------+-------------+-------------+---------------+----------+-------------------+---------------+
| #tags  | #SAMPLEPREP.id      | #.delimiter  | *#.fields    | #.for_each  | #.required  | *#.sort_by  | #.sort_order  | #.table  | #.test            | #.value_type  |
+========+=====================+==============+==============+=============+=============+=============+===============+==========+===================+===============+
|        | SAMPLEPREP_SUMMARY  | " "          | description  | True        |             | id          | ascending     | protocol | type=sample_prep  | str           |
+--------+---------------------+--------------+--------------+-------------+-------------+-------------+---------------+----------+-------------------+---------------+

Input JSON
++++++++++

.. code:: console

    {
    "protocol": {
        "3_IC-FTMS_preparation": {
          "description": "Before going into the IC-FTMS the frozen sample is reconstituted in water.",
          "filename": "",
          "id": "3_IC-FTMS_preparation",
          "type": "sample_prep"
          },
        "ICMS1": {
          "chromatography_description": "Targeted IC",
          "chromatography_instrument_name": "Thermo Dionex ICS-5000+",
          "chromatography_type": "Targeted IC",
          "column_name": "Dionex IonPac AS11-HC-4um 2 mm i.d. x 250 mm",
          "description": "ICMS Analytical Experiment with detection of compounds by comparison to standards. \nThermo RAW files are loaded into TraceFinder and peaks are manually curated. The area under the chromatograms is then exported to an Excel file. The area is then corrected for natural abundance. The natural abundance corrected area is then used to calculate the concentration of each compound for each sample. This calculation is done using standards. The first sample ran on the ICMS is a standard that has known concentrations of certain compounds. Then a number of samples are ran (typically 3-4) followed by another standard. The equation to calculate the concentration is \"intensity in sample\"/(\"intensity in first standard\" + ((\"intensity in second standard\" - \"intensity in first standard\")/# of samples) * \"known concentration in standard\", where the \"intensity\" is the aforementioned natural abundance corrected area, and the unlabeled intensity from the standard is used for all isotopologues of the compound. The reconstitution volume is simply the volume that the polar part of the sample was reconstituted to before going into the ICMS. The injection volume is how much of the reconstitution volume was injected into the ICMS. The protein is how much protein was in the entire sample (not only the small portion that was aliquoted for the ICMS). The polar split ratio is the fraction of the polar part of the sample that was aliquoted for the ICMS. This is calculated by dividing the weight of the polar aliquot for ICMS by the total weight of the polar portion of the sample. The protein normalized concentration is calculated using the equation, concentration * (reconstitution volume / 1000 / polar split ratio / protein).",
          "id": "ICMS1",
          "instrument": "Orbitrap Fusion",
          "instrument_type": "IC-FTMS",
          "ion_mode": "NEGATIVE",
          "ionization": "ESI",
          "parentID": "IC-FTMS_measurement",
          "type": "MS"
          },
        "4a_acetone_extraction": {
          "description": "acetone extraction of polar metabolites",
          "filename": "4A2_Media Extraction with acetone ppt step.pdf",
          "id": "4a_acetone_extraction",
          "type": "sample_prep"
          },
        "allogenic": {
          "description": "Mouse with allogenic bone marrow transplant. Fed with semi-liquid diet supplemented with fully labeled glucose for 24 hours before harvest.",
          "id": "allogenic",
          "parentID": "mouse_experiment",
          "type": "treatment",
          "filename": "study_treatments.pdf"
          },
        "2_frozen_tissue_grind": {
          "description": "Frozen tissue is ground in a SPEX grinder under liquid nitrogen to homogenize the sample.",
          "id": "2_frozen_tissue_grind",
          "type": "sample_prep"
          },
        "4b_lipid_extraction": {
          "description": "Lipid extraction from homogenate.",
          "filename": "4B_Extract_Polar_Lipid_Prot_Fan_070417.pdf",
          "id": "4b_lipid_extraction",
          "type": "sample_prep"
          },
        "mouse_tissue_collection": {
          "description": "Mouse is sacrificed and tissues are harvested.",
          "id": "mouse_tissue_collection",
          "sample_type": "mouse",
          "type": "collection",
          "filename": "mouse_tissue_procedure.pdf"
          },
        "naive": {
          "description": "Mouse with no treatment. Fed with semi-liquid diet supplemented with fully labeled glucose for 24 hours before harvest.",
          "id": "naive",
          "parentID": "mouse_experiment",
          "type": "treatment",
          "filename": "study_treatments.pdf"
          },
        "4c_polar_extraction": {
          "description": "Polar extraction from homogenate, lyophilized, and frozen.",
          "filename": "4B_Extract_Polar_Lipid_Prot_Fan_070417.pdf",
          "id": "4c_polar_extraction",
          "type": "sample_prep"
          },
        "4d_protein_extraction": {
          "description": "Protein extraction and quantification.",
          "filename": [
            "4D_17Jun4_Fan_Prot_Quant.pdf",
            "4B_Extract_Polar_Lipid_Prot_Fan_070417.pdf"
          ],
          "id": "4d_protein_extraction",
          "type": "sample_prep"
          },
        "syngenic": {
          "description": "Mouse with syngenic bone marrow transplant. Fed with semi-liquid diet supplemented with fully labeled glucose for 24 hours before harvest.",
          "id": "syngenic",
          "parentID": "mouse_experiment",
          "type": "treatment",
          "filename": "study_treatments.pdf"
          },
        "1_tissue_quench": {
          "description": "Tissue is frozen in liquid nitrogen to stop metabolic processes.",
          "id": "1_tissue_quench",
          "type": "sample_prep"
          }
        }
    }

Output JSON
+++++++++++

.. code:: console

    {
    "SAMPLEPREP": {
        "SAMPLEPREP_SUMMARY": "Tissue is frozen in liquid nitrogen to stop metabolic processes. Frozen tissue is ground in a SPEX grinder under liquid nitrogen to homogenize the sample. Before going into the IC-FTMS the frozen sample is reconstituted in water. acetone extraction of polar metabolites Lipid extraction from homogenate. Polar extraction from homogenate, lypholized, and frozen. Protein extraction and quantification."
        }
    }


General Output Format
---------------------

.. code:: console

    {
    <table_name>: {
        <record_name>: <string_value>
        }
    }


Meaningful Fields
-----------------
**override** - a string value that will be used as the value for the record directly. 
Takes priority over other fields. You can put the value between double quotes if it 
is difficult to get certain sequences in the table software used to construct the directive. 
Ex. " " will be a single space and "asdf" will be asdf.

**code** - a string of valid Python code to be delivered to eval() that must return a string type 
value. Takes priority after override.

**import** - a string that is a filepath to a Python file to be imported. Typically to be used 
to import functions to run with the code field.

**table** - a string that is the name of the table in the input JSON to pull from to build the 
string value for the record.

**fields** - a list of literals and fields in the input JSON records to concatenate together to 
build the string value for the record. It is assumed that all records in the input JSON will have 
these fields and an error will occur if one does not. To interpret a value in the list as a literal 
value and not a field, surround it in double quotes. Ex. [field1,"literal_value",field2]

**for_each** - a boolean or string value ("True" or "False") that indicates the string value is to be 
built by iterating over each record in the indicated table in the input JSON. Takes priority over 
record_id.

**test** - a string of the form "field=value" where field is a field in the records being 
iterated over and value is what the field must be equal to in order to be used to build the 
string value. Use this as a filter to filter out records that should not be used to build 
the string value. If for_each is false, this is used to find the first record that matches.

**delimiter** - a string value used to separate the strings built from each record when 
for_each is true. You can put the value between double quotes if it is difficult to get certain 
sequences in the table software used to construct the directive. Ex. " " will be a single 
space and "asdf" will be asdf.

**sort_by** - a list of fields to sort the input JSON records by before building the value from them.

**sort_order** - a string value that is either "ascending" or "descending" to indicate how to sort 
the input JSON records.

**record_id** - a string value that is the specific record name in the indicated input JSON table 
to build the value from.

**required** - a boolean or string value ("True" or "False") that indicates if the directive is 
required. If true, then errors encountered will stop the program. If false, a warning will be 
printed and the directive will either use a default value or be skipped.

**default** - a string value to default to if the directive cannot be built and is not required. 
If getting specific sequences in the table software used to construct the directive is difficult, 
you can put the value between double quotes. Ex. " " will be a single space and "asdf" will be asdf.



matrix Directives
~~~~~~~~~~~~~~~~~
The matrix directive assumes that you want to create a list of dictionaries (aka array of 
objects) from information in the input JSON, and that that information is contained within 
a single table. By default, this directive will loop over all records in the indicated table 
and build a dictionary for each record. The records can be sorted and filtered before iteration 
in the same way that the str directives can be, using the "sort_by", "sort_order", and "test" fields. 
The "collate" field can also be used to group data together across records. The below 
examples illustrate some common uses.

Code
----
If you need to generate a list of dictionaries from the input JSON in a more complex way 
than what is currently possible with the supported directives, you can use the "code" field 
to give the program Python code directly to evaluate. What is in the code field will 
be delivered directly to eval(), and the name of the internal variable for the input 
JSON is "input_json". You can also use the "import" field to import any user created 
libraries into the program. The "import" value should be a path to the file to import. 
For the matrix directive specifically, the "code" field is a good way to supply the 
value directly.

Directive as JSON
+++++++++++++++++

.. code:: console

    {
    "MS_METABOLITE_DATA": {
        "Data": {
            "value_type": "matrix",
            "code": "[{\"Metabolite\":\"Glucose\", \"Sample 1\":\"1234.5\"}]"
            }
        }
    }

Tagged Equivalent
+++++++++++++++++

+--------+-------------------------+---------------+--------------------------------------------------+
| #tags  | #MS_METABOLITE_DATA.id  | #.value_type  | #.code                                           |
+========+=========================+===============+==================================================+
|        | Data                    | matrix        | [{"Metabolite":"Glucose", "Sample 1":"1234.5"}]  |
+--------+-------------------------+---------------+--------------------------------------------------+

Output JSON
+++++++++++

.. code:: console

    {
    "MS_METABOLITE_DATA": {
        "Data": [{"Metabolite":"Glucose", "Sample 1":"1234.5"}]
        }
    }
    

Headers
-------
Similar to the "fields" field for str directives, the "headers" field is the backbone 
of most matrix directives. Use this field to specify how to build the dictionaries by 
supplying key-value pairs. The value should be a list of strings, "key=value", where 
the keys and values can be either the names of fields in the input records or literal 
values. Literal values need to be surrounded with double quotes.

Directive as JSON
+++++++++++++++++

.. code:: console

    {
    "MS_METABOLITE_DATA": {
        "Data": {
            "value_type": "matrix",
            "table": "measurement",
            "headers": [\"Metabolite\"=assignment,sample.id=intensity],
            "sort_by": ["assignment"],
            "sort_order": "ascending"
            }
        }
    }

Tagged Equivalent
+++++++++++++++++

+--------+-------------------------+---------------+--------------+----------------------------------------------+-------------+---------------+
| #tags  | #MS_METABOLITE_DATA.id  | #.value_type  | #.table      | *#.headers                                   | *#.sort_by  | #.sort_order  |
+========+=========================+===============+==============+==============================================+=============+===============+
|        | Data                    | matrix        | measurement  | "Metabolite"=assignment,sample.id=intensity  | assignment  | ascending     |
+--------+-------------------------+---------------+--------------+----------------------------------------------+-------------+---------------+

Input JSON
++++++++++

.. code:: console

    {
    "measurement": {
        "(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0-16_A0_Lung_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A": {
              "assignment": "(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0",
              "assignment%method": "database",
              "compound": "(S)-2-Acetolactate Glutaric acid Methylsuccinic acid",
              "concentration": "0",
              "concentration%type": "calculated from standard",
              "concentration%units": "uM",
              "corrected_raw_intensity": "10882632.3918",
              "corrected_raw_intensity%type": "natural abundance corrected peak area",
              "formula": "C5H8O4",
              "id": "(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0-16_A0_Lung_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A",
              "intensity": "16103434.00085152",
              "intensity%type": "natural abundance corrected and protein normalized peak area",
              "intensity%units": "area/g",
              "isotopologue": "13C0",
              "isotopologue%type": "13C",
              "normalized_concentration": "0",
              "normalized_concentration%type": "protein normalized",
              "normalized_concentration%units": "uMol/g",
              "protocol.id": "ICMS1",
              "raw_intensity": "10292474.4912643",
              "raw_intensity%type": "spectrometer peak area",
              "sample.id": "16_A0_Lung_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A"
              },
        "(S)-3-Sulfonatolactate-13C0-16_A0_Lung_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A": {
              "assignment": "(S)-3-Sulfonatolactate-13C0",
              "assignment%method": "database",
              "compound": "(S)-3-Sulfonatolactate",
              "concentration": "0",
              "concentration%type": "calculated from standard",
              "concentration%units": "uM",
              "corrected_raw_intensity": "29258.2204515",
              "corrected_raw_intensity%type": "natural abundance corrected peak area",
              "formula": "C3H6O6S1",
              "id": "(S)-3-Sulfonatolactate-13C0-16_A0_Lung_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A",
              "intensity": "43294.47187595062",
              "intensity%type": "natural abundance corrected and protein normalized peak area",
              "intensity%units": "area/g",
              "isotopologue": "13C0",
              "isotopologue%type": "13C",
              "normalized_concentration": "0",
              "normalized_concentration%type": "protein normalized",
              "normalized_concentration%units": "uMol/g",
              "protocol.id": "ICMS1",
              "raw_intensity": "28305.550843869",
              "raw_intensity%type": "spectrometer peak area",
              "sample.id": "16_A0_Lung_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A"
              }
        }
    }

Output JSON
+++++++++++

.. code:: console

    {
    "MS_METABOLITE_DATA": {
        "Data": [
                 {
                 "Metabolite": "(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0",
                 "16_A0_Lung_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A": "16103434.00085152"
                 },
                 {
                 "Metabolite": "(S)-3-Sulfonatolactate-13C0",
                 "16_A0_Lung_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A": "43294.47187595062"
                 }]
        }
    }


Collate
-------
The "headers" field will create a new dictionary for every record in the indicated table, 
but sometimes you might need to pull data from multiple records into a single new 
dictionary, and the "collate" field gives a mechanism for this. The value of the field 
is a string that needs to be one of the fields in the input records. If given, the 
record data will be grouped into dictionaries based on their field value.

Directive as JSON
+++++++++++++++++

.. code:: console

    {
    "MS_METABOLITE_DATA": {
        "Data": {
            "value_type": "matrix",
            "table": "measurement",
            "headers": [\"Metabolite\"=assignment,sample.id=intensity],
            "sort_by": ["assignment"],
            "sort_order": "ascending",
            "collate": "assignment"
            }
        }
    }

Tagged Equivalent
+++++++++++++++++

+--------+-------------------------+---------------+--------------+----------------------------------------------+-------------+---------------+-------------+
| #tags  | #MS_METABOLITE_DATA.id  | #.value_type  | #.table      | *#.headers                                   | *#.sort_by  | #.sort_order  | #.collate   |
+========+=========================+===============+==============+==============================================+=============+===============+=============+
|        | Data                    | matrix        | measurement  | "Metabolite"=assignment,sample.id=intensity  | assignment  | ascending     | assignment  |
+--------+-------------------------+---------------+--------------+----------------------------------------------+-------------+---------------+-------------+

Input JSON
++++++++++

.. code:: console

    {
    "measurement": {
        "(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0-16_A0_Lung_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A": {
              "assignment": "(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0",
              "assignment%method": "database",
              "compound": "(S)-2-Acetolactate Glutaric acid Methylsuccinic acid",
              "concentration": "0",
              "concentration%type": "calculated from standard",
              "concentration%units": "uM",
              "corrected_raw_intensity": "10882632.3918",
              "corrected_raw_intensity%type": "natural abundance corrected peak area",
              "formula": "C5H8O4",
              "id": "(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0-16_A0_Lung_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A",
              "intensity": "16103434.00085152",
              "intensity%type": "natural abundance corrected and protein normalized peak area",
              "intensity%units": "area/g",
              "isotopologue": "13C0",
              "isotopologue%type": "13C",
              "normalized_concentration": "0",
              "normalized_concentration%type": "protein normalized",
              "normalized_concentration%units": "uMol/g",
              "protocol.id": "ICMS1",
              "raw_intensity": "10292474.4912643",
              "raw_intensity%type": "spectrometer peak area",
              "sample.id": "16_A0_Lung_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A"
              },
        "(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0-17_A1_Lung_naive_0days_170427_UKy_GCH_rep2-polar-ICMS_A": {
              "assignment": "(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0",
              "assignment%method": "database",
              "compound": "(S)-2-Acetolactate Glutaric acid Methylsuccinic acid",
              "concentration": "0",
              "concentration%type": "calculated from standard",
              "concentration%units": "uM",
              "corrected_raw_intensity": "6408243.70722",
              "corrected_raw_intensity%type": "natural abundance corrected peak area",
              "formula": "C5H8O4",
              "id": "(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0-17_A1_Lung_naive_0days_170427_UKy_GCH_rep2-polar-ICMS_A",
              "intensity": "10483483.72051263",
              "intensity%type": "natural abundance corrected and protein normalized peak area",
              "intensity%units": "area/g",
              "isotopologue": "13C0",
              "isotopologue%type": "13C",
              "normalized_concentration": "0",
              "normalized_concentration%type": "protein normalized",
              "normalized_concentration%units": "uMol/g",
              "protocol.id": "ICMS1",
              "raw_intensity": "6060770.18227202",
              "raw_intensity%type": "spectrometer peak area",
              "sample.id": "17_A1_Lung_naive_0days_170427_UKy_GCH_rep2-polar-ICMS_A"
            },
        "(S)-3-Sulfonatolactate-13C0-16_A0_Lung_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A": {
              "assignment": "(S)-3-Sulfonatolactate-13C0",
              "assignment%method": "database",
              "compound": "(S)-3-Sulfonatolactate",
              "concentration": "0",
              "concentration%type": "calculated from standard",
              "concentration%units": "uM",
              "corrected_raw_intensity": "29258.2204515",
              "corrected_raw_intensity%type": "natural abundance corrected peak area",
              "formula": "C3H6O6S1",
              "id": "(S)-3-Sulfonatolactate-13C0-16_A0_Lung_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A",
              "intensity": "43294.47187595062",
              "intensity%type": "natural abundance corrected and protein normalized peak area",
              "intensity%units": "area/g",
              "isotopologue": "13C0",
              "isotopologue%type": "13C",
              "normalized_concentration": "0",
              "normalized_concentration%type": "protein normalized",
              "normalized_concentration%units": "uMol/g",
              "protocol.id": "ICMS1",
              "raw_intensity": "28305.550843869",
              "raw_intensity%type": "spectrometer peak area",
              "sample.id": "16_A0_Lung_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A"
              },
        "(S)-3-Sulfonatolactate-13C0-17_A1_Lung_naive_0days_170427_UKy_GCH_rep2-polar-ICMS_A": {
              "assignment": "(S)-3-Sulfonatolactate-13C0",
              "assignment%method": "database",
              "compound": "(S)-3-Sulfonatolactate",
              "concentration": "0",
              "concentration%type": "calculated from standard",
              "concentration%units": "uM",
              "corrected_raw_intensity": "12975.6343755",
              "corrected_raw_intensity%type": "natural abundance corrected peak area",
              "formula": "C3H6O6S1",
              "id": "(S)-3-Sulfonatolactate-13C0-17_A1_Lung_naive_0days_170427_UKy_GCH_rep2-polar-ICMS_A",
              "intensity": "21227.32186131077",
              "intensity%type": "natural abundance corrected and protein normalized peak area",
              "intensity%units": "area/g",
              "isotopologue": "13C0",
              "isotopologue%type": "13C",
              "normalized_concentration": "0",
              "normalized_concentration%type": "protein normalized",
              "normalized_concentration%units": "uMol/g",
              "protocol.id": "ICMS1",
              "raw_intensity": "12551.8799866885",
              "raw_intensity%type": "spectrometer peak area",
              "sample.id": "17_A1_Lung_naive_0days_170427_UKy_GCH_rep2-polar-ICMS_A"
            }
        }
    }

Output JSON
+++++++++++

.. code:: console

    {
    "MS_METABOLITE_DATA": {
        "Data": [
                 {
                 "Metabolite": "(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0",
                 "16_A0_Lung_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A": "16103434.00085152",
                 "17_A1_Lung_naive_0days_170427_UKy_GCH_rep2-polar-ICMS_A": "10483483.72051263"
                 },
                 {
                 "Metabolite": "(S)-3-Sulfonatolactate-13C0",
                 "16_A0_Lung_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A": "43294.47187595062",
                 "17_A1_Lung_naive_0days_170427_UKy_GCH_rep2-polar-ICMS_A": "21227.32186131077"
                 }]
        }
    }


Fields to Headers
-----------------
The "fields_to_headers" field changes the behavior of the matrix directive so that 
by default all fields from input records are copied as is into the dictionary. The 
"exclusion_headers" field can then be used to exclude fields from being added. 
The "values_to_str" field can also be used to convert all of the field values to strings.

Directive as JSON
+++++++++++++++++

.. code:: console

    {
    "MS_METABOLITE_DATA": {
        "Extended": {
            "value_type": "matrix",
            "table": "measurement",
            "headers": [\"Metabolite\"=assignment,\"sample.id\"=sample.id],
            "sort_by": ["assignment"],
            "sort_order": "ascending",
            "fields_to_headers": "True",
            "values_to_str": "True",
            "exclusion_headers": [id,intensity,intensity%type,intensity%units,assignment,sample.id,formula,compound,isotopologue,isotopologue%type]
            }
        }
    }

Tagged Equivalent
+++++++++++++++++

+--------+-------------------------+---------------+--------------+------------------------------------------------+-------------+---------------+----------------------+------------------+-------------------------------------------------------------------------------------------------------------------+
| #tags  | #MS_METABOLITE_DATA.id  | #.value_type  | #.table      | *#.headers                                     | *#.sort_by  | #.sort_order  | #.fields_to_headers  | #.values_to_str  | *#.exclusion_headers                                                                                              |
+========+=========================+===============+==============+================================================+=============+===============+======================+==================+===================================================================================================================+
|        | Extended                | matrix        | measurement  | "Metabolite"=assignment,"sample_id"=sample.id  | assignment  | ascending     | True                 | True             | id,intensity,intensity%type,intensity%units,assignment,sample.id,formula,compound,isotopologue,isotopologue%type  |
+--------+-------------------------+---------------+--------------+------------------------------------------------+-------------+---------------+----------------------+------------------+-------------------------------------------------------------------------------------------------------------------+

Input JSON
++++++++++

.. code:: console

    {
    "measurement": {
        "(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0-16_A0_Lung_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A": {
              "assignment": "(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0",
              "assignment%method": "database",
              "compound": "(S)-2-Acetolactate Glutaric acid Methylsuccinic acid",
              "concentration": "0",
              "concentration%type": "calculated from standard",
              "concentration%units": "uM",
              "corrected_raw_intensity": "10882632.3918",
              "corrected_raw_intensity%type": "natural abundance corrected peak area",
              "formula": "C5H8O4",
              "id": "(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0-16_A0_Lung_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A",
              "intensity": "16103434.00085152",
              "intensity%type": "natural abundance corrected and protein normalized peak area",
              "intensity%units": "area/g",
              "isotopologue": "13C0",
              "isotopologue%type": "13C",
              "normalized_concentration": "0",
              "normalized_concentration%type": "protein normalized",
              "normalized_concentration%units": "uMol/g",
              "protocol.id": "ICMS1",
              "raw_intensity": "10292474.4912643",
              "raw_intensity%type": "spectrometer peak area",
              "sample.id": "16_A0_Lung_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A"
              },
        "(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0-17_A1_Lung_naive_0days_170427_UKy_GCH_rep2-polar-ICMS_A": {
              "assignment": "(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0",
              "assignment%method": "database",
              "compound": "(S)-2-Acetolactate Glutaric acid Methylsuccinic acid",
              "concentration": "0",
              "concentration%type": "calculated from standard",
              "concentration%units": "uM",
              "corrected_raw_intensity": "6408243.70722",
              "corrected_raw_intensity%type": "natural abundance corrected peak area",
              "formula": "C5H8O4",
              "id": "(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0-17_A1_Lung_naive_0days_170427_UKy_GCH_rep2-polar-ICMS_A",
              "intensity": "10483483.72051263",
              "intensity%type": "natural abundance corrected and protein normalized peak area",
              "intensity%units": "area/g",
              "isotopologue": "13C0",
              "isotopologue%type": "13C",
              "normalized_concentration": "0",
              "normalized_concentration%type": "protein normalized",
              "normalized_concentration%units": "uMol/g",
              "protocol.id": "ICMS1",
              "raw_intensity": "6060770.18227202",
              "raw_intensity%type": "spectrometer peak area",
              "sample.id": "17_A1_Lung_naive_0days_170427_UKy_GCH_rep2-polar-ICMS_A"
            },
        "(S)-3-Sulfonatolactate-13C0-16_A0_Lung_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A": {
              "assignment": "(S)-3-Sulfonatolactate-13C0",
              "assignment%method": "database",
              "compound": "(S)-3-Sulfonatolactate",
              "concentration": "0",
              "concentration%type": "calculated from standard",
              "concentration%units": "uM",
              "corrected_raw_intensity": "29258.2204515",
              "corrected_raw_intensity%type": "natural abundance corrected peak area",
              "formula": "C3H6O6S1",
              "id": "(S)-3-Sulfonatolactate-13C0-16_A0_Lung_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A",
              "intensity": "43294.47187595062",
              "intensity%type": "natural abundance corrected and protein normalized peak area",
              "intensity%units": "area/g",
              "isotopologue": "13C0",
              "isotopologue%type": "13C",
              "normalized_concentration": "0",
              "normalized_concentration%type": "protein normalized",
              "normalized_concentration%units": "uMol/g",
              "protocol.id": "ICMS1",
              "raw_intensity": "28305.550843869",
              "raw_intensity%type": "spectrometer peak area",
              "sample.id": "16_A0_Lung_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A"
              },
        "(S)-3-Sulfonatolactate-13C0-17_A1_Lung_naive_0days_170427_UKy_GCH_rep2-polar-ICMS_A": {
              "assignment": "(S)-3-Sulfonatolactate-13C0",
              "assignment%method": "database",
              "compound": "(S)-3-Sulfonatolactate",
              "concentration": "0",
              "concentration%type": "calculated from standard",
              "concentration%units": "uM",
              "corrected_raw_intensity": "12975.6343755",
              "corrected_raw_intensity%type": "natural abundance corrected peak area",
              "formula": "C3H6O6S1",
              "id": "(S)-3-Sulfonatolactate-13C0-17_A1_Lung_naive_0days_170427_UKy_GCH_rep2-polar-ICMS_A",
              "intensity": "21227.32186131077",
              "intensity%type": "natural abundance corrected and protein normalized peak area",
              "intensity%units": "area/g",
              "isotopologue": "13C0",
              "isotopologue%type": "13C",
              "normalized_concentration": "0",
              "normalized_concentration%type": "protein normalized",
              "normalized_concentration%units": "uMol/g",
              "protocol.id": "ICMS1",
              "raw_intensity": "12551.8799866885",
              "raw_intensity%type": "spectrometer peak area",
              "sample.id": "17_A1_Lung_naive_0days_170427_UKy_GCH_rep2-polar-ICMS_A"
            }
        }
    }

Output JSON
+++++++++++

.. code:: console

    {
    "MS_METABOLITE_DATA": {
        "Extended": [
                  {
                    "Metabolite": "(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0",
                    "sample_id": "16_A0_Lung_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A",
                    "assignment%method": "database",
                    "concentration": "0",
                    "concentration%type": "calculated from standard",
                    "concentration%units": "uM",
                    "corrected_raw_intensity": "10882632.3918",
                    "corrected_raw_intensity%type": "natural abundance corrected peak area",
                    "normalized_concentration": "0",
                    "normalized_concentration%type": "protein normalized",
                    "normalized_concentration%units": "uMol/g",
                    "protocol.id": "ICMS1",
                    "raw_intensity": "10292474.4912643",
                    "raw_intensity%type": "spectrometer peak area"
                  },
                  {
                    "Metabolite": "(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0",
                    "sample_id": "17_A1_Lung_naive_0days_170427_UKy_GCH_rep2-polar-ICMS_A",
                    "assignment%method": "database",
                    "concentration": "0",
                    "concentration%type": "calculated from standard",
                    "concentration%units": "uM",
                    "corrected_raw_intensity": "6408243.70722",
                    "corrected_raw_intensity%type": "natural abundance corrected peak area",
                    "normalized_concentration": "0",
                    "normalized_concentration%type": "protein normalized",
                    "normalized_concentration%units": "uMol/g",
                    "protocol.id": "ICMS1",
                    "raw_intensity": "6060770.18227202",
                    "raw_intensity%type": "spectrometer peak area"
                  },
                  {
                    "Metabolite": "(S)-3-Sulfonatolactate-13C0",
                    "sample_id": "16_A0_Lung_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A",
                    "assignment%method": "database",
                    "concentration": "0",
                    "concentration%type": "calculated from standard",
                    "concentration%units": "uM",
                    "corrected_raw_intensity": "29258.2204515",
                    "corrected_raw_intensity%type": "natural abundance corrected peak area",
                    "normalized_concentration": "0",
                    "normalized_concentration%type": "protein normalized",
                    "normalized_concentration%units": "uMol/g",
                    "protocol.id": "ICMS1",
                    "raw_intensity": "28305.550843869",
                    "raw_intensity%type": "spectrometer peak area"
                  },
                  {
                    "Metabolite": "(S)-3-Sulfonatolactate-13C0",
                    "sample_id": "17_A1_Lung_naive_0days_170427_UKy_GCH_rep2-polar-ICMS_A",
                    "assignment%method": "database",
                    "concentration": "0",
                    "concentration%type": "calculated from standard",
                    "concentration%units": "uM",
                    "corrected_raw_intensity": "12975.6343755",
                    "corrected_raw_intensity%type": "natural abundance corrected peak area",
                    "normalized_concentration": "0",
                    "normalized_concentration%type": "protein normalized",
                    "normalized_concentration%units": "uMol/g",
                    "protocol.id": "ICMS1",
                    "raw_intensity": "12551.8799866885",
                    "raw_intensity%type": "spectrometer peak area"
                  }]
        }
    }


General Output Format
---------------------

.. code:: console

    {
    <table_name>: {
        <record_name>: [{<field_name>:<field_value>, ...}, ...]
        }
    }


Meaningful Fields
-----------------
**code** - a string of valid Python code to be delivered to eval() that must return a list of 
dictionaries. Takes priority over headers.

**import** - a string that is a filepath to a Python library to be imported. Typically to be used 
to import functions to run with the code field.

**table** - a string that is the name of the table in the input JSON to pull from to build the 
string value for the record.

**headers** - a list of key-value pairs in the form "key=value" where keys and values can be 
field names or literal values. Literal values must be surrounded by double quotes. 
Ex. ["Metabolite"=assignment,"sample.id"=sample.id]

**test** - a string of the form "field=value" where field is a field in the records being 
iterated over and value is what the field must be equal to in order to be used to build the 
value. Use this as a filter to filter out records that should not be used to build the value.

**sort_by** - a list of fields to sort the input JSON records by before building the value from them.

**sort_order** - a string value that is either "ascending" or "descending" to indicate how to sort 
the input JSON records.

**collate** - a string value that must be a field name in the input records. Used to group data 
across records.

**fields_to_headers** - a boolean or string value ("True" or "False") that indicates whether to 
copy all fields in the input records into the output.

**exclusion_headers** - a list of field names not to put into the output data when the "fields_to_headers" 
field is True.

**optional_headers** - a list of field names that will be copied into the output if they exist in the 
record. Use "values_to_str" to cast the values to a string.

**values_to_str** - a boolean or string value ("True" or "False") that causes field values to be converted 
into a string type in the output.

**required** - a boolean or string value ("True" or "False") that indicates if the directive is 
required. If true, then errors encountered will stop the program. If false, a warning will be 
printed and the directive will either use a default value or be skipped.

**default** - a string value to default to if the directive cannot be built and is not required. 
If getting specific sequences in the table software used to construct the directive is difficult, 
you can put the value between double quotes. Ex. " " will be a single space and "asdf" will be asdf.



section Directives
~~~~~~~~~~~~~~~~~~
When you need a more complex structure than is available through the other directives 
or if you need to specify the entire table at once, the section type directive is 
what you need. It only has the "code" and "import" fields because you have to supply 
Python code to tell MESSES how to build the section. One quirk of the directive is 
that you do still have to specify a record name for the directive, but it is ignored 
since whatever the code generates will be what the table's value is set to. There is 
currently one module built into MESSES that contains functions for building a part of 
the mwTab file, and that is used as the example here.

Example
-------

Directive as JSON
+++++++++++++++++

.. code:: console

    {
    "SUBJECT_SAMPLE_FACTORS": {
      "no_id_needed": {
        "code": "mwtab_tag_functions.create_subject_sample_factors(input_json)",
        "id": "no_id_needed",
        "value_type": "section"
        }
      }
    }

Tagged Equivalent
+++++++++++++++++

+--------+-----------------------------+----------------------------------------------------------------+---------------+
| #tags  | #SUBJECT_SAMPLE_FACTORS.id  | #.code                                                         | #.value_type  |
+========+=============================+================================================================+===============+
|        | no_id_needed                | mwtab_tag_functions.create_subject_sample_factors(input_json)  | section       |
+--------+-----------------------------+----------------------------------------------------------------+---------------+

Output JSON
+++++++++++

.. code:: console

    {
    "ANALYSIS": [
        {
          "Subject ID": "01_A0_naive_0days_UKy_GCH_rep1",
          "Sample ID": "16_A0_Lung_naive_0days_170427_UKy_GCH_rep1-polar-ICMS_A",
          "Factors": {
            "Treatment": "naive",
            "Time Point": "0"
          },
          "Additional sample data": {
            "lineage0_id": "01_A0_naive_0days_UKy_GCH_rep1",
            "lineage0_protocol.id": "['naive']",
            "lineage0_replicate": "1",
            "lineage0_species": "Mus musculus",
            "lineage0_species_type": "Mouse",
            "lineage0_taxonomy_id": "10090",
            "lineage0_time_point": "0",
            "lineage0_type": "subject",
            "lineage1_id": "16_A0_Lung_naive_0days_170427_UKy_GCH_rep1",
            "lineage1_protocol.id": "['mouse_tissue_collection', 'tissue_quench', 'frozen_tissue_grind']",
            "lineage1_type": "sample",
            "lineage2_id": "16_A0_Lung_naive_0days_170427_UKy_GCH_rep1-protein",
            "lineage2_protein_weight": "0.6757957582975501",
            "lineage2_protein_weight%units": "mg",
            "lineage2_protocol.id": "['protein_extraction']",
            "lineage2_type": "sample",
            "RAW_FILE_NAME": "16_A0_Lung_T032017_naive_ICMSA.raw"
          }
        },
        {
          "Subject ID": "02_A1_naive_0days_UKy_GCH_rep2",
          "Sample ID": "17_A1_Lung_naive_0days_170427_UKy_GCH_rep2-polar-ICMS_A",
          "Factors": {
            "Treatment": "naive",
            "Time Point": "0"
          },
          "Additional sample data": {
            "lineage0_id": "02_A1_naive_0days_UKy_GCH_rep2",
            "lineage0_protocol.id": "['naive']",
            "lineage0_replicate": "2",
            "lineage0_species": "Mus musculus",
            "lineage0_species_type": "Mouse",
            "lineage0_taxonomy_id": "10090",
            "lineage0_time_point": "0",
            "lineage0_type": "subject",
            "lineage1_id": "17_A1_Lung_naive_0days_170427_UKy_GCH_rep2",
            "lineage1_protocol.id": "['mouse_tissue_collection', 'tissue_quench', 'frozen_tissue_grind']",
            "lineage1_type": "sample",
            "lineage2_id": "17_A1_Lung_naive_0days_170427_UKy_GCH_rep2-protein",
            "lineage2_protein_weight": "0.6112704400619461",
            "lineage2_protein_weight%units": "mg",
            "lineage2_protocol.id": "['protein_extraction']",
            "lineage2_type": "sample",
            "RAW_FILE_NAME": "17_A1_Lung_T032017_naive_ICMSA.raw"
          }
        }
    }


General Output Format
---------------------

.. code:: console

    {
    <table_name>: <code_result>
    }


Meaningful Fields
-----------------
**code** - a string of valid Python code to be delivered to eval(). The entire table is assigned 
the value returned by eval() with no type checking, unlike the other directives which are type 
checked.

**import** - a string that is a filepath to a Python file to be imported. Typically to be used 
to import functions to run with the code field.


Validation
~~~~~~~~~~
Conversion directives are validated before use in the convert command using JSON Schema.

Validation Schema:

.. literalinclude:: ../src/messes/convert/convert_schema.py
    :start-at: { 
    :end-before: #
    :language: none




.. _Metabolomics Workbench: http://www.metabolomicsworkbench.org