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
            "sort_by": ["analysis_type"],
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
the string value. If the for_each field is false, this is used to find the first record that matches. 
The test field is also aware of boolean logic, so the "and", "or", "&", and "|" operators can be used to create more 
complex tests. For example, "field1=value1 and field2=value2" or "field1=value1 or field1=value2". 
Note that the "and" and "&" operators behave exactly the same, they are just aliases of each other for 
convenience. The "or" and "|" operators are similarly aliased.

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

**silent** - a boolean or string value ("True" or "False") that indicates whether or not to print 
errors and warnings encountered while executing the directive. Takes precedence over the --silent 
option.








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
string value. Use this as a filter to filter out records that should not be used to build 
the string value. If the for_each field is false, this is used to find the first record that matches. 
The test field is also aware of boolean logic, so the "and", "or", "&", and "|" operators can be used to create more 
complex tests. For example, "field1=value1 and field2=value2" or "field1=value1 or field1=value2". 
Note that the "and" and "&" operators behave exactly the same, they are just aliases of each other for 
convenience. The "or" and "|" operators are similarly aliased.

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

**silent** - a boolean or string value ("True" or "False") that indicates whether or not to print 
errors and warnings encountered while executing the directive. Takes precedence over the --silent 
option.









section Directives
~~~~~~~~~~~~~~~~~~
Originally, the "section" type directive was simply a catch all to implement functionality 
that "str" and "matrix" directives could not. It only had "code" and "import" fields 
to provide Python code to eval and produce output. While that functionality is still 
there it has evolved to behave more like the "str" directive as well and shares many 
of its fields. How the "section" type directive determines what records to execute 
on in the input data is exactly the same as how a "str" type determines it. The difference 
is that instead of having a "fields" attribute to indicate how to build a string from 
the record values, the "section" type directive has an "execute" attribute. 

The "execute" 
attribute is expected to have a form like "function_name(args1, arg2, ...)", where the 
"function_name" is a built-in function with predefined behavior, and the arguments 
can be either a literal value ("asdf"), a record attribute name (attribute1), or a 
calling record attribute name (^.attribute1). The available built-in functions are 
described in the :doc:`built_ins` section of the documentation, but a user can create 
their own built-in functions and import them with the "import" field of any directive. By default all 
functions imported with the "import" field are added to the list of built-in functions. 
Most built-in functions are used to transform strings formatted a specific way into 
more complex data structures. For example, to_dict() will transform a string formatted 
like "key1:value1, key2:value2" into a Python dictionary/JSON object like {"key1": "value1", "key2": "value2"}. 
If "for_each" is specified, then the function in "execute" is called for each record and 
a list of the return values is returned by the directive, otherwise the return value 
of the function is returned by the directive.

There are also other Python functions that are available to the user through directives, 
but are categorically different from built-in functions and cannot be accessed through 
the "execute" field. These are functions specific to :doc:`supported_formats`, and 
were developed for use in creating complex sections of supported formats. They appear 
in the built-in directives for each format, but were mostly developed for internal 
use to handle niche situations. They are made available to the user 
so modifications can be made if necessary, but it should be clear that these are 
categorically different from built-in functions available in the "execute" field. 
They are mentioned here just to differentiate them and hopefully avoid confusion. 
They can be called through the "code" field, and there is an example of doing so 
below.

Note that if any "section" type directives are in the directive table, there should 
be no other directives in the same table.

Code
----

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
    
    

Record ID
---------
Use the "record_id" field to operate only on a specific record.

Directive as JSON
+++++++++++++++++

.. code:: console

    {
    "directive1": {
        "name1": {
            "value_type": "section",
            "table": "table1",
            "record_id": "record1",
            "execute": "to_dict(attribute1)"
            }
        }
    }

Tagged Equivalent
+++++++++++++++++

+-------+----------------+---------------------+-------------+---------+--------------+
| #tags | #directive1.id | #.execute           | #.record_id | #.table | #.value_type |
+=======+================+=====================+=============+=========+==============+
|       | name1          | to_dict(attribute1) | record1     | table1  | section      |
+-------+----------------+---------------------+-------------+---------+--------------+


Input JSON
++++++++++

.. code:: console

    {
    "table1": {
        "record1": {
            "attribute1": "key1:value1, key2:value2"
            }
        }
    }

Output JSON
+++++++++++

.. code:: console

    {
      "directive1": {
        "key1": "value1",
        "key2": "value2"
      }
    }


First Record
------------
Similar to specifying a record ID, if you want to execute on a record 
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
    "directive1": {
        "name1": {
            "value_type": "section",
            "table": "table1",
            "execute": "to_dict(attribute1)",
            "test": "sort_field=2"
            }
        }
    }
    
    # Using sort.
    {
    "directive1": {
        "name1": {
            "value_type": "section",
            "table": "table1",
            "execute": "to_dict(attribute1)",
            "sort_by": ["sort_field"],
            "sort_order": "descending"
            }
        }
    }

Tagged Equivalent
+++++++++++++++++

+-------+----------------+---------------------+---------+--------------+--------------+
| #tags | #directive1.id | #.execute           | #.table | #.test       | #.value_type |
+=======+================+=====================+=========+==============+==============+
|       | name1          | to_dict(attribute1) | table1  | sort_field=2 | section      |
+-------+----------------+---------------------+---------+--------------+--------------+


+-------+----------------+---------------------+-------------+---------------+---------+--------------+
| #tags | #directive1.id | #.execute           | *#.sort_by  | #.sort_order  | #.table | #.value_type |
+=======+================+=====================+=============+===============+=========+==============+
|       | name1          | to_dict(attribute1) | sort_field  | descending    | table1  | section      |
+-------+----------------+---------------------+-------------+---------------+---------+--------------+


Input JSON
++++++++++

.. code:: console

    {
    "table1": {
        "record1": {
            "sort_field": "1",
            "attribute1": "key1:value1, key2:value2"
            },
        "record2": {
            "sort_field": "2",
            "attribute1": "key3:value3, key4:value4"
            }
        }
    }
    
    # After sorting.
    {
    "table1": {
        "record2": {
            "sort_field": "2",
            "attribute1": "key3:value3, key4:value4"
            },
        "record1": {
            "sort_field": "1",
            "attribute1": "key1:value1, key2:value2"
            }
        }
    }

Output JSON
+++++++++++

.. code:: console

    {
      "directive1": {
        "key3": "value3",
        "key4": "value4"
      }
    }


For Each
--------
If a list of return values from a built-in function executed with many records is 
desired, then use the "for_each" attribute. The function in "execute" will be called 
for each record determined by the "table" and "test" attributes, and a list of the 
return values will be returned by the directive.

Directive as JSON
+++++++++++++++++

.. code:: console

    {
    "directive1": {
        "name1": {
            "for_each": "True",
            "execute": "to_dict(attribute1)",
            "sort_by": ["sort_field"],
            "sort_order": "descending",
            "table": "table1",
            "value_type": "section"
            }
        }
    }

Tagged Equivalent
+++++++++++++++++

+-------+----------------+---------------------+------------+------------+--------------+---------+--------------+
| #tags | #directive1.id | #.execute           | #.for_each | *#.sort_by | #.sort_order | #.table | #.value_type |
+=======+================+=====================+============+============+==============+=========+==============+
|       | name1          | to_dict(attribute1) | TRUE       | sort_field | descending   | table1  | section      |
+-------+----------------+---------------------+------------+------------+--------------+---------+--------------+


Input JSON
++++++++++

.. code:: console

    {
    "table1": {
        "record1": {
            "sort_field": "1",
            "attribute1": "key1:value1, key2:value2"
            },
        "record2": {
            "sort_field": "2",
            "attribute1": "key3:value3, key4:value4"
            }
        }
    }

Output JSON
+++++++++++

.. code:: console

    {
      "directive1": [
          {
            "key3": "value3",
            "key4": "value4"
          },
          {
            "key1": "value1",
            "key2": "value2"
          }
      ]
    }





Meaningful Fields
-----------------
**code** - a string of valid Python code to be delivered to eval(). The entire table is assigned 
the value returned by eval() with no type checking, unlike the other directives which are type 
checked.

**import** - a string that is a filepath to a Python file to be imported. Typically to be used 
to import functions to run with the code field.

**table** - a string that is the name of the table in the input JSON to pull from to build the 
list of records to run "execute" with.

**execute** - a string of the form "function_name(arg1, arg2, ...)", where "function_name" is 
an imported or built-in function and the arguments can be either a literal value ("asdf"), 
a record attribute name (attribute1), or a calling record attribute name (^.attribute1).

**for_each** - a boolean or string value ("True" or "False") that indicates "execute" is to be 
run for each record in the indicated table in the input JSON. Takes priority over record_id.

**test** - a string of the form "field=value" where field is a field in the records being 
iterated over and value is what the field must be equal to in order to be used to build the 
string value. Use this as a filter to filter out records that should not be used to build 
the string value. If the for_each field is false, this is used to find the first record that matches. 
The test field is also aware of boolean logic, so the "and", "or", "&", and "|" operators can be used to create more 
complex tests. For example, "field1=value1 and field2=value2" or "field1=value1 or field1=value2". 
Note that the "and" and "&" operators behave exactly the same, they are just aliases of each other for 
convenience. The "or" and "|" operators are similarly aliased.

**sort_by** - a list of fields to sort the input JSON records by before running "execute" on them.

**sort_order** - a string value that is either "ascending" or "descending" to indicate how to sort 
the input JSON records.

**record_id** - a string value that is the specific record name in the indicated input JSON table 
to run "execute" with.

**required** - a boolean or string value ("True" or "False") that indicates if the directive is 
required. If true, then errors encountered will stop the program. If false, a warning will be 
printed and the directive will either use a default value or be skipped.

**default** - a string value to default to if the directive cannot be built and is not required. 
If getting specific sequences in the table software used to construct the directive is difficult, 
you can put the value between double quotes. Ex. " " will be a single space and "asdf" will be asdf.

**silent** - a boolean or string value ("True" or "False") that indicates whether or not to print 
errors and warnings encountered while executing the directive. Takes precedence over the --silent 
option.









Advanced Usage
~~~~~~~~~~~~~~
In response to a need for more complex logic to construct new output formats, new features 
were added to the conversion directives. This section shows how these new features come into 
play for each directive type.


section_str and section_matrix
------------------------------
Although technically new value_types, the "section_matrix" and "section_str" type directives 
behaves exactly like a "matrix" and "str" type directive, respectively,  except that the record 
name is ignored and the entire table's value is set to the output of this directive. This is 
the same output behavior as the "section" type directive, but with the "matrix" or "str" type 
construction logic. Note that if any "section" type directives are in the directive table 
there should be no other directives in the same table.

section_str Example
+++++++++++++++++++

Directive as JSON
#################

.. code:: console

    {
    "ANALYSIS": {
        "name_is_ignored": {
            "value_type": "section_str",
            "override": "MS"
            }
        }
    }

Tagged Equivalent
#################

+--------+-----------------+-------------+---------------+
| #tags  | #ANALYSIS.id    | #.override  | #.value_type  |
+========+=================+=============+===============+
|        | name_is_ignored | MS          | section_str   |
+--------+-----------------+-------------+---------------+

Output JSON
###########

.. code:: console

    {
    "ANALYSIS": "MS"
    }


section_matrix Example
++++++++++++++++++++++

Directive as JSON
#################

.. code:: console

    {
    "ANALYSIS": {
        "name_is_ignored": {
            "value_type": "section_matrix",
            "headers": ["\"key1\"=\"value1\""]
            }
        }
    }

Tagged Equivalent
#################

+-------+-----------------+-----------------+----------------+
| #tags | #ANALYSIS.id    | *#.headers      | #.value_type   |
+=======+=================+=================+================+
|       | name_is_ignored | "key1"="value1" | section_matrix |
+-------+-----------------+-----------------+----------------+


Output JSON
###########

.. code:: console

    {
    "ANALYSIS": {"key1": "value1"}
    }
    



Calling Record Attributes
-------------------------
The concept of nested directives is fully explained in the `Nested Directives`_ section, 
but this section shows some examples of directives being called by other directives 
in order to illustrate where calling record attributes can be used. To simplify, just 
understand that when a nested directive is called, it should have a record from the 
input associated with it (the calling record), and the directive can access the attributes 
from this record. The syntax to access the calling record's attributes instead of 
accessing a record's attributes normally is to add "^." to the beginning of the 
attribute name.

Directives can use calling record attributes only through certain fields that vary by directive 
type. The following table lists the fields where a calling record attribute can be used:

+----------+----------------+---------------------------------------------------------------------+
| Field    | Directive Type | Notes                                                               |
+==========+================+=====================================================================+
| test     | All            |                                                                     |
+----------+----------------+---------------------------------------------------------------------+
| override | str            | Non-string values will be coerced to strings.                       |
+----------+----------------+---------------------------------------------------------------------+
| fields   | str            | Non-string values will be coerced to strings.                       |
+----------+----------------+---------------------------------------------------------------------+
| headers  | matrix         | Non-string values will be coerced to strings for header key values. |
+----------+----------------+---------------------------------------------------------------------+
| execute  | section        |                                                                     |
+----------+----------------+---------------------------------------------------------------------+


test Example
++++++++++++
Directive as JSON
#################

.. code:: console

    {
      "directive1": {
        "name1": {
          "headers": [
              "\"parent\"=directive1%key_value()",
              "\"child\"=attribute1"
              ],
          "table": "table1",
          "value_type": "matrix",
          "test": "id=record1"
        }
      },
      "directive1%key_value": {
        "name2": {
          "fields": ["attribute1"],
          "value_type": "section_str",
          "test": "id=^.parent_id"
        }
      }
    }

Tagged Equivalent
#################

+-------+--------------------------+----------------------------------------------------+----------------+--------------+--------------+
| #tags | #directive1.id           | *#.headers                                         | #.table        | #.test       | #.value_type |
+=======+==========================+====================================================+================+==============+==============+
|       | name1                    | "parent"=directive1%key_value(),"child"=attribute1 | table1         | id=record1   | matrix       |
+-------+--------------------------+----------------------------------------------------+----------------+--------------+--------------+
|       |                          |                                                    |                |              |              |
+-------+--------------------------+----------------------------------------------------+----------------+--------------+--------------+
| #tags | #directive1%key_value.id | *#.fields                                          | #.test         | #.value_type |              |
+-------+--------------------------+----------------------------------------------------+----------------+--------------+--------------+
|       | name2                    | attribute1                                         | id=^.parent_id | section_str  |              |
+-------+--------------------------+----------------------------------------------------+----------------+--------------+--------------+

Input JSON
##########

.. code:: console

    {
    "table1": {
        "record1": {
            "attribute1": "value1",
            "parent_id": "record2"
            },
        "record2": {
            "attribute1": "value2"
            }
        }
    }

Output JSON
###########

.. code:: console

    {
      "directive1": {
          "name1": [{"parent": "value2", "child": "value1"}]
          }
    }

This example shows grabbing a parent_id from a record to look up its parent and grab 
a value from the parent record.


override Example
++++++++++++++++
Directive as JSON
#################

.. code:: console

    {
      "directive1": {
        "name1": {
          "fields": ["directive1%field_value()"],
          "table": "table1",
          "value_type": "str"
        }
      },
      "directive1field_value%": {
        "name2": {
          "override": "^.attribute1",
          "value_type": "str"
        }
      }
    }

Tagged Equivalent
#################

+-------+----------------------------+--------------------------+--------------+--------------+
| #tags | #directive1.id             | *#.fields                | #.table      | #.value_type |
+=======+============================+==========================+==============+==============+
|       | name1                      | directive1%field_value() | table1       | str          |
+-------+----------------------------+--------------------------+--------------+--------------+
|       |                            |                          |              |              |
+-------+----------------------------+--------------------------+--------------+--------------+
| #tags | #directive1field_value%.id | #.override               | #.value_type |              |
+-------+----------------------------+--------------------------+--------------+--------------+
|       | name2                      | ^.attribute1             | str          |              |
+-------+----------------------------+--------------------------+--------------+--------------+


Calling Record
##############

.. code:: console

    {
    "table1": {
        "record1": {
            "attribute1": "value1",
            "attribute2": "value2",
            ...
            }
        }
    }


Output JSON
###########

.. code:: console

    {
      "directive1": {
        "name1": "{'name2': 'value1'}"
      }
    }

Note that this example uses "str" types, but the nested directive returns a dictionary 
that was represented as a string in the result, "{'name2': 'value1'}". This is because 
a nested directive is the whole table and not just one individual directive. This is 
precisely why the "section_str" type was created. If "directive1%field_value" was a "section_str" 
type instead, the output would be:

.. code:: console

    {
      "directive1": {
        "name1": "value1"
      }
    }


fields Example
++++++++++++++
Directive as JSON
#################

.. code:: console

    {
      "directive1": {
        "name1": {
          "fields": ["directive1%field_value()"],
          "table": "table1",
          "value_type": "str"
        }
      },
      "directive1%field_value": {
        "name2": {
          "fields": ["\"begin \"", "^.attribute1", "\" end\""],
          "value_type": "str"
        }
      }
    }

Tagged Equivalent
#################

+-------+----------------------------+------------------------------+--------------+--------------+
| #tags | #directive1.id             | *#.fields                    | #.table      | #.value_type |
+=======+============================+==============================+==============+==============+
|       | name1                      | directive1%field_value()     | table1       | str          |
+-------+----------------------------+------------------------------+--------------+--------------+
|       |                            |                              |              |              |
+-------+----------------------------+------------------------------+--------------+--------------+
| #tags | #directive1%field_value.id | *#.fields                    | #.value_type |              |
+-------+----------------------------+------------------------------+--------------+--------------+
|       | name2                      | "begin ",^.attribute1," end" | str          |              |
+-------+----------------------------+------------------------------+--------------+--------------+

Calling Record
##############

.. code:: console

    {
    "table1": {
        "record1": {
            "attribute1": "value1",
            "attribute2": "value2",
            ...
            }
        }
    }


Output JSON
###########

.. code:: console

    {
      "directive1": {
        "name1": "{'name2': 'begin value1 end'}"
      }
    }

Note that this example uses "str" types, but the nested directive returns a dictionary 
that was represented as a string in the result, "{'name2': 'begin value1 end'}". This is because 
a nested directive is the whole table and not just one individual directive. This is 
precisely why the "section_str" type was created. If "directive1%field_value" was a "section_str" 
type instead, the output would be:

.. code:: console

    {
      "directive1": {
        "name1": "begin value1 end"
      }
    }


headers Example
+++++++++++++++
Directive as JSON
#################

.. code:: console

    {
      "directive1": {
        "name1": {
          "headers": ["\"key\"=directive1%key_value()"],
          "table": "table1",
          "value_type": "matrix"
        }
      },
      "directive1%key_value": {
        "name2": {
          "headers": ["\"key2\"=^.attribute1"],
          "value_type": "matrix"
        }
      }
    }

Tagged Equivalent
#################

+-------+--------------------------+------------------------------+--------------+--------------+
| #tags | #directive1.id           | *#.headers                   | #.table      | #.value_type |
+=======+==========================+==============================+==============+==============+
|       | name1                    | "key"=directive1%key_value() | table1       | matrix       |
+-------+--------------------------+------------------------------+--------------+--------------+
|       |                          |                              |              |              |
+-------+--------------------------+------------------------------+--------------+--------------+
| #tags | #directive1%key_value.id | *#.headers                   | #.value_type |              |
+-------+--------------------------+------------------------------+--------------+--------------+
|       | name2                    | "key2"=^.attribute1          | matrix       |              |
+-------+--------------------------+------------------------------+--------------+--------------+

Calling Record
##############

.. code:: console

    {
    "table1": {
        "record1": {
            "attribute1": "value1",
            "attribute2": "value2",
            ...
            }
        }
    }


Output JSON
###########

.. code:: console

    {
      "directive1": {
        "name1": [
          {
            "key": {
              "name2": [
                {
                  "key2": "value1"
                }
              ]
            }
          }
        ]
      }
    }

Note that this example uses "matrix" types, but the nested directive returns a dictionary 
, "{'name2': [{"key2": "value1' }]}". This is because 
a nested directive is the whole table and not just one individual directive. This is 
precisely why the "section_matrix" type was created. If "directive1%key_value" was a "section_matrix" 
type instead, the output would be:

.. code:: console

    {
      "directive1": {
        "name1": [
          {
            "key": [
              {
                "key2": "value1"
              }
            ]
          }
        ]
      }
    }

Note that calling record attributes can be used as keys or values for headers, but 
keys must be strings, so they will be forced into a string if the value is not a 
string and a warning will be printed.


execute Example
+++++++++++++++
Directive as JSON
#################

.. code:: console

    {
      "directive1": {
        "name1": {
          "headers": ["\"key\"=directive1%key_value()"],
          "table": "table1",
          "value_type": "matrix",
          "test": "id=record1"
        }
      },
      "directive1%key_value": {
        "name2": {
          "execute": "to_dict(^.attribute1)",
          "value_type": "section"
        }
      }
    }

Tagged Equivalent
#################

+-------+--------------------------+------------------------------+--------------+------------+--------------+
| #tags | #directive1.id           | *#.headers                   | #.table      | #.test     | #.value_type |
+=======+==========================+==============================+==============+============+==============+
|       | name1                    | "key"=directive1%key_value() | table1       | id=record1 | matrix       |
+-------+--------------------------+------------------------------+--------------+------------+--------------+
|       |                          |                              |              |            |              |
+-------+--------------------------+------------------------------+--------------+------------+--------------+
| #tags | #directive1%key_value.id | #.execute                    | #.value_type |            |              |
+-------+--------------------------+------------------------------+--------------+------------+--------------+
|       | name2                    | to_dict(^.attribute1)        | section      |            |              |
+-------+--------------------------+------------------------------+--------------+------------+--------------+

Calling Record
##############

.. code:: console

    {
    "table1": {
        "record1": {
            "id": "record1",
            "attribute1": "key1:value1, key2:value2",
            "attribute2": "value2",
            ...
            }
        }
    }


Output JSON
###########

.. code:: console

    {
      "directive1": {
        "name1": [
          {
            "key": {
              "key1": "value1",
              "key2": "value2"
            }
          }
        ]
      }
    }




Call Signature
--------------
Directives were initially created with the assumption that the user would want to do 
some operations in the context of an input record or list of records. The assumption 
was that each directive would first need to assemble a set of records and then filter 
and/or sort them down to the desired set before proceeding to do its operations. With 
the addition of `Nested Directives`_, it became clear this assumption would not 
always be true. Before the addition of `Nested Directives`_ the "table" field could 
be required if certain other fields ("fields", "headers", "execute") were present, 
but now it is entirely conceivable that a user would want to run a directive with 
only combinations of literal values ("asdf"), nested directives (directive1%field_value()), and 
calling record attributes (^.attribute1). Due to this change, the "table" field is 
not always required for a directive and the inputs to certain fields are analyzed 
for what types of values they have to determine if the directive can be executed without 
first building a set of records. This results in a few different call signatures 
and examples are shown below.


Execute With Record Attributes
++++++++++++++++++++++++++++++
This is the traditional way to call a directive. The example is minimal and requires 
"table" to be present, but other fields like "test", "sort_by", etc. can 
also be included. 

str
###
The example only shows record attributes in "fields", but these 
could also be a combination of literal values, calling record attributes, and nested 
directives.

.. code:: console

    {
      "directive1": {
        "name1": {
          "fields": ["record_attribute1", "record_attribute2", ...],
          "table": "table1",
          "value_type": "str"
        }
      }
    }
    

matrix
######
The example only shows record attributes in "headers", but these 
could also be a combination of literal values, calling record attributes, and nested 
directives.

.. code:: console

    {
      "directive1": {
        "name1": {
          "headers": ["\"key1\"=record_attribute1", "\"key2\"=record_attribute2", ... ],
          "table": "table1",
          "value_type": "matrix"
        }
      }
    }
    

section
#######

.. code:: console

    {
      "directive1": {
        "name1": {
          "execute": "function_name(record_attribute1, record_attribute2, ...)",
          "table": "table1",
          "value_type": "section"
        }
      }
    }


Execute Without Record Attributes
+++++++++++++++++++++++++++++++++
This is only possible if there are no record attribute fields in "fields". The "table" field 
is not required, and a set of records won't be determined. The directive will be executed
with the given values.

str
###

.. code:: console

    {
      "directive1": {
        "name1": {
          "fields": ["^.calling_attribute1", "\"literal_value\"", ...],
          "value_type": "str"
        }
      }
    }
    

matrix
######

.. code:: console

    {
      "directive1": {
        "name1": {
          "headers": [
              "\"key1\"=^.calling_attribute", 
              "\"key2\"=\"literal_value\"", 
              "\"key3\"=directive1%key3_value()",
               ... ],
          "value_type": "matrix"
        }
      }
    }


section
#######
Note that nested directives cannot be used as arguments in "execute".

.. code:: console

    {
      "directive1": {
        "name1": {
          "execute": "function_name(^.calling_attribute1, "literal_value", ...)",
          "value_type": "section"
        }
      }
    }




Header Optionality
------------------
Although the "optional_headers" attribute exists, it is limited to having the output 
key names be the same as the attribute names on the records. Using a combination of 
nested directives and the "required" attribute, we can turn every header into an optional 
header. If the "required" field on a nested directive is False, then if it has an error 
it will not return a value. If that happens while creating a key value pair in a 
matrix directive, it will drop the pair.

Example
+++++++
Directive as JSON
#################

.. code:: console

    {
      "directive1": {
        "name1": {
          "headers": [
              "\"key1\"=directive1%attribute1()", 
              "\"key2\"=directive1%attribute2()"
              ],
          "table": "table1",
          "value_type": "matrix"
        }
      },
      "directive1%attribute1": {
        "name2": {
          "fields": ["^.attribute1"],
          "value_type": "section_str",
          "required": "False",
          "silent": "True"
        }
      },
      "directive1%attribute2": {
        "name3": {
          "fields": ["^.attribute2"],
          "value_type": "section_str",
          "required": "False",
          "silent": "True"
        }
      }
    }

Tagged Equivalent
#################

+-------+---------------------------+---------------------------------------------------------------+------------+--------------+--------------+
| #tags | #directive1.id            | *#.headers                                                    | #.table    | #.value_type |              |
+=======+===========================+===============================================================+============+==============+==============+
|       | name1                     | "key1"=directive1%attribute1(),"key2"=directive1%attribute2() | table1     | matrix       |              |
+-------+---------------------------+---------------------------------------------------------------+------------+--------------+--------------+
|       |                           |                                                               |            |              |              |
+-------+---------------------------+---------------------------------------------------------------+------------+--------------+--------------+
| #tags | #directive1%attribute1.id | *#.fields                                                     | #.required | #.silent     | #.value_type |
+-------+---------------------------+---------------------------------------------------------------+------------+--------------+--------------+
|       | name2                     | ^.attribute1                                                  | FALSE      | TRUE         | section_str  |
+-------+---------------------------+---------------------------------------------------------------+------------+--------------+--------------+
|       |                           |                                                               |            |              |              |
+-------+---------------------------+---------------------------------------------------------------+------------+--------------+--------------+
| #tags | #directive1%attribute2.id | *#.fields                                                     | #.required | #.silent     | #.value_type |
+-------+---------------------------+---------------------------------------------------------------+------------+--------------+--------------+
|       | name3                     | ^.attribute2                                                  | FALSE      | TRUE         | section_str  |
+-------+---------------------------+---------------------------------------------------------------+------------+--------------+--------------+


Calling Record
##############

.. code:: console

    {
    "table1": {
        "record1": {
            "attribute1": "value1",
            "attribute2": "value2"
            },
        "record2": {
            "attribute2": "value3"
            }
        }
    }


Output JSON
###########

.. code:: console

    {
      "directive1": {
        "name1": [
          {
            "key1": "value1",
            "key2": "value2"
          },
          {
            "key2": "value3"
          }
        ]
      }
    }

Note how the second dictionary in the list does not have a "key1". This is because the record 
"record2" did not have an "attribute1".






Nested Directives
~~~~~~~~~~~~~~~~~
In order to support the creation of more deeply nested formats, directives were 
extended to be nested as well. The basic idea is that directives can call other 
directives to fill in some values. For example, a matrix directive can call another 
directive table to fill in a value for one of its headers. This allows for more 
data structures to be created, using more complex logic if needed.

Note that nested directive tables do not include the table name in their return 
value. It executes like a standalone directive table, but where a standalone table 
would have its name in the resulting output, ex "directive1": {value}, a nested 
directive table will only return its value to the parent directive.

Along with nested directives came some features that were natural outgrowths from 
them:

1. The ability to indicate that a directive table is not a standalone directive table, and is 
   only meant to be executed in a nested way.
   
   * This is accomplished through directive table naming.
   * Directive tables with '%' in the name will not be executed as standalone directives and will be skipped over in the main loop of convert.
   * Nested directive tables are recommended to be named like: 'parent_name%descriptive_name' so it is easy to track down the root.
   * An example might be 'studies%assays', where studies is a section_matrix with an 'assays' 
     header whose value will be filled in by the 'studies%assays' directive table.
   * For multiple layers of nesting, use multiple '%' characters. For example, 'studies%assays%files'
   
2. The extension of the "section" type return style to the other directive types.

   * To get the most out of nested table directives, it is necessary to be able to return a 
     single string value or matrix instead of a dictionary.
   * The "section_str" and "section_matrix" types were thus created which behave 
     exactly as "str" and "matrix" types, respectively, but the value determined by 
     the directives is set to the whole directive table like the "section" type directive.
   
3. The ability to easily access the attributes of the record the parent directive had in its context 
   when it called the nested directive table.
   
   * One of the main use cases for nested directive tables is to do some more complicated 
     parsing or logic on a record's attribute than can be done in a single directive.
   * For example, a record's attribute could be a string of the form "key1:value1, key2:value2" 
     and you want to parse this into a dictionary.
   * It would be great if you could easily access that attribute from the nested directive 
     table without having to rebuild a set of records in the same way the parent directive 
     did.
   * This was implemented by adding "^." to the beginning of an attribute name in the nested 
     directive to indicate that the attribute value should come from the record that was in 
     the parent directive's context when it called the nested directive table.
   * For example, say a parent "str" type directive calls a nested directive table to 
     fill in one element for its "fields" attribute. The record at the time of the call 
     is "record1": {"attribute1": "value1"}. The nested directive table called is 
     a single "section_str" type directive that has an "override" value of "^.attribute1". 
     The override value would then look up the value of "attribute1" in the record, "value1", 
     and "value1" is used as the value for "override". The nested directive then returns 
     this value to the parent directive so it can finish executing normally.
   * This example is contrived for simplicity, but there are more examples in the Advanced 
     Usage section.
     
4. The ability to pass arguments into nested directive tables when called to overwrite attribute values.

   * Arguments can have 2 forms: "directive_name.attribute_name=new_value" or "attribute_name=new_value"
   * The first form will only overwrite the attribute for the given directive name.
   * For example, "directive1.override=value1" will overwrite the value of the "override" attribute 
     in the "directive1" directive with "value1".
   * The second form, "attribute_name=new_value", will overwrite ALL directives in the table that 
     have the given attribute.
   * For example, "override=value1" will overwrite the value of the "override" attribute for ALL 
     directives in the called directive table that have an "override" attribute with "value1".
   * The "attribute_name" must be in the directive in order to override the value. If a directive 
     does not have the given attribute then it will NOT be given it.
   * For example, a directive that does not have an "override" attribute will not be given one 
     if the "override=value1" argument is passed with the directive table.
   * Named arguments, i.e. arguments of the form "directive_name.attribute_name=new_value", will 
     take precedence over unnamed arguments.
   * For example, if both "directive1.override=value1" and "override=value2" are passed with a 
     nested directive table the "override" attribute of the "directive1" directive will be 
     "value1" not "value2".
   * The value on the right side of the "=" character can be a field to a record, a literal value ("asdf"), or 
     a field to a calling record (^.attribute).



Directives can call other directives only through certain fields that vary by directive 
type. The following table lists the fields where a directive can be called from:

+----------+----------------+--------------------------------------------------------------------------------------------+
| Field    | Directive Type | Notes                                                                                      |
+==========+================+============================================================================================+
| test     | All            |                                                                                            |
+----------+----------------+--------------------------------------------------------------------------------------------+
| override | str            | Directives that return non-string values will be coerced to strings.                       |
+----------+----------------+--------------------------------------------------------------------------------------------+
| fields   | str            | Directives that return non-string values will be coerced to strings.                       |
+----------+----------------+--------------------------------------------------------------------------------------------+
| headers  | matrix         | Directives that return non-string values will be coerced to strings for header key values. |
+----------+----------------+--------------------------------------------------------------------------------------------+


Examples
--------

test
++++
Directive as JSON
#################

.. code:: console

    {
    "directive1": {
        "name1": {
            "fields": ["attribute1"],
            "table": "table1",
            "test": "sort_field=directive1%test_value()",
            "value_type": "str"
            }
        },
    "directive1%test_value": {
        "name2": {
            "override": "2",
            "value_type": "section_str"
            }
        }
    }

Tagged Equivalent
#################

+-------+---------------------------+------------+--------------+------------------------------------+--------------+
| #tags | #directive1.id            | *#.fields  | #.table      | #.test                             | #.value_type |
+=======+===========================+============+==============+====================================+==============+
|       | name1                     | attribute1 | table1       | sort_field=directive1%test_value() | str          |
+-------+---------------------------+------------+--------------+------------------------------------+--------------+
|       |                           |            |              |                                    |              |
+-------+---------------------------+------------+--------------+------------------------------------+--------------+
| #tags | #directive1%test_value.id | #.override | #.value_type |                                    |              |
+-------+---------------------------+------------+--------------+------------------------------------+--------------+
|       | name2                     | 2          | section_str  |                                    |              |
+-------+---------------------------+------------+--------------+------------------------------------+--------------+


Input JSON
##########

.. code:: console

    {
    "table1": {
        "record1": {
            "sort_field": "1",
            "attribute1": "key1:value1, key2:value2"
            },
        "record2": {
            "sort_field": "2",
            "attribute1": "key3:value3, key4:value4"
            }
        }
    }

Output JSON
###########

.. code:: console

    {
      "directive1": {
          "name1": "key3:value3, key4:value4"
          }
    }

This example is somewhat contrived, but it should be easy to follow. directive1 
calls directive1%test_value to fill in the test value, and directive1%test_value 
is a simple "section_str" type directive that returns the value "2". Then directive1 
can subset the input down to one record and construct its value as normal.



override
++++++++
Directive as JSON
#################

.. code:: console

    {
    "directive1": {
        "name1": {
            "override": "directive1%override_value()",
            "value_type": "str"
            }
        },
    "directive1%override_value": {
        "name2": {
            "override": "2",
            "value_type": "section_str"
            }
        }
    }

Tagged Equivalent
#################

+-------+-------------------------------+-----------------------------+--------------+
| #tags | #directive1.id                | #.override                  | #.value_type |
+=======+===============================+=============================+==============+
|       | name1                         | directive1%override_value() | str          |
+-------+-------------------------------+-----------------------------+--------------+
|       |                               |                             |              |
+-------+-------------------------------+-----------------------------+--------------+
| #tags | #directive1%override_value.id | #.override                  | #.value_type |
+-------+-------------------------------+-----------------------------+--------------+
|       | name2                         | 2                           | section_str  |
+-------+-------------------------------+-----------------------------+--------------+


Input JSON
##########

.. code:: console

    {
     This example doesn't need input.
    }

Output JSON
###########

.. code:: console

    {
      "directive1": {
          "name1": "2"
          }
    }

Although contrived, this example was made simple on purpose so that it is easy to follow. directive1 
calls directive1%override_value to fill in the override value, and directive1%override_value 
is a simple "section_str" type directive that returns the value "2". Then directive1 
uses "2" as its override value and executes normally.



fields
++++++
Directive as JSON
#################

.. code:: console

    {
    "directive1": {
        "name1": {
            "fields": ["attribute1", "\" \"", "directive1%field_value()"],
            "table": "table1",
            "value_type": "str"
            }
        },
    "directive1%field_value": {
        "name2": {
            "override": "3",
            "value_type": "section_str"
            }
        }
    }

Tagged Equivalent
#################

+-------+----------------------------+-----------------------------------------+--------------+--------------+
| #tags | #directive1.id             | *#.fields                               | #.table      | #.value_type |
+=======+============================+=========================================+==============+==============+
|       | name1                      | attribute1," ",directive1%field_value() | table1       | str          |
+-------+----------------------------+-----------------------------------------+--------------+--------------+
|       |                            |                                         |              |              |
+-------+----------------------------+-----------------------------------------+--------------+--------------+
| #tags | #directive1%field_value.id | #.override                              | #.value_type |              |
+-------+----------------------------+-----------------------------------------+--------------+--------------+
|       | name2                      | 3                                       | section_str  |              |
+-------+----------------------------+-----------------------------------------+--------------+--------------+


Input JSON
##########

.. code:: console

    {
    "table1": {
        "record1": {
            "attribute1": "key1:value1, key2:value2"
            }
        }
    }

Output JSON
###########

.. code:: console

    {
      "directive1": {
          "name1": "key1:value1, key2:value2 3"
          }
    }

This example is purposefully contrived so that it is easy to follow. directive1 
calls directive1%field_value to fill in one of the values in fields, and directive1%field_value 
is a simple "section_str" type directive that returns the value "3". Then directive1 
uses "3" for the appropriate element in fields and executes normally.



headers
+++++++
Directive as JSON
#################

.. code:: console

    {
    "directive1": {
        "name1": {
            "headers": ["\"key1\"=attribute1", "\"key2\"=directive1%header_value()"],
            "table": "table1",
            "value_type": "matrix"
            }
        },
    "directive1%header_value": {
        "name2": {
            "override": "3",
            "value_type": "section_str"
            }
        }
    }

Tagged Equivalent
#################

+-------+-----------------------------+----------------------------------------------------+--------------+--------------+
| #tags | #directive1.id              | *#.headers                                         | #.table      | #.value_type |
+=======+=============================+====================================================+==============+==============+
|       | name1                       | "key1"=attribute1,"key2"=directive1%header_value() | table1       | matrix       |
+-------+-----------------------------+----------------------------------------------------+--------------+--------------+
|       |                             |                                                    |              |              |
+-------+-----------------------------+----------------------------------------------------+--------------+--------------+
| #tags | #directive1%header_value.id | #.override                                         | #.value_type |              |
+-------+-----------------------------+----------------------------------------------------+--------------+--------------+
|       | name2                       | 3                                                  | section_str  |              |
+-------+-----------------------------+----------------------------------------------------+--------------+--------------+


Input JSON
##########

.. code:: console

    {
    "table1": {
        "record1": {
            "attribute1": "value1"
            }
        }
    }

Output JSON
###########

.. code:: console

    {
      "directive1": {
          "name1": [
              {"key1": "value1", "key2": "3"}
              ]
          }
    }

This example is purposefully contrived so that it is easy to follow. directive1 
calls directive1%header_value to fill in the value for key2, and directive1%header_value 
is a simple "section_str" type directive that returns the value "3". Then directive1 
uses "3" for the value of key2 and executes normally. If there were 
more records, directive1%header_value would have been called for each record.


Directive as JSON
#################

.. code:: console

    {
    "directive1": {
        "name1": {
            "headers": ["\"key1\"=attribute1", "\"key2\"=directive1%header_value()"],
            "table": "table1",
            "value_type": "matrix"
            }
        },
    "directive1%header_value": {
        "name2": {
            "override": "3",
            "value_type": "str"
            }
        }
    }

Tagged Equivalent
#################

+-------+-----------------------------+----------------------------------------------------+--------------+--------------+
| #tags | #directive1.id              | *#.headers                                         | #.table      | #.value_type |
+=======+=============================+====================================================+==============+==============+
|       | name1                       | "key1"=attribute1,"key2"=directive1%header_value() | table1       | matrix       |
+-------+-----------------------------+----------------------------------------------------+--------------+--------------+
|       |                             |                                                    |              |              |
+-------+-----------------------------+----------------------------------------------------+--------------+--------------+
| #tags | #directive1%header_value.id | #.override                                         | #.value_type |              |
+-------+-----------------------------+----------------------------------------------------+--------------+--------------+
|       | name2                       | 3                                                  | str          |              |
+-------+-----------------------------+----------------------------------------------------+--------------+--------------+


Input JSON
##########

.. code:: console

    {
    "table1": {
        "record1": {
            "attribute1": "value1"
            }
        }
    }

Output JSON
###########

.. code:: console

    {
      "directive1": {
          "name1": [
              {"key1": "value1", "key2": {"name2": "3"}}
              ]
          }
    }

This example is the same as the previous, but the nested directive table is a str 
type instead of a section_str type. Note how the directive table name for the nested 
table is automatically ignored, but the entire value of the directive table is now 
a dictionary instead of a string.



argument passing
++++++++++++++++
Directive as JSON
#################

.. code:: console

    {
      "directive1": {
        "name1": {
          "headers": [
            "\"header1\"=directive1%header_value(override=\"value1\", name3.override = attribute1)"
          ],
          "table": "table1",
          "value_type": "matrix"
        }
      },
      "directive1%header_value": {
        "name2": {
          "override": "value2",
          "value_type": "str"
        },
        "name3": {
          "override": "value3",
          "value_type": "str"
        }
      }
    }

Tagged Equivalent
#################

+-------+-----------------------------+-----------------------------------------------------------------------------------+--------------+--------------+
| #tags | #directive1.id              | *#.headers                                                                        | #.table      | #.value_type |
+=======+=============================+===================================================================================+==============+==============+
|       | name1                       | "header1"=directive1%header_value(override="value1", name3.override = attribute1) | table1       | matrix       |
+-------+-----------------------------+-----------------------------------------------------------------------------------+--------------+--------------+
|       |                             |                                                                                   |              |              |
+-------+-----------------------------+-----------------------------------------------------------------------------------+--------------+--------------+
| #tags | #directive1%header_value.id | #.override                                                                        | #.value_type |              |
+-------+-----------------------------+-----------------------------------------------------------------------------------+--------------+--------------+
|       | name2                       | value2                                                                            | str          |              |
+-------+-----------------------------+-----------------------------------------------------------------------------------+--------------+--------------+
|       | name3                       | value3                                                                            | str          |              |
+-------+-----------------------------+-----------------------------------------------------------------------------------+--------------+--------------+

Input JSON
##########

.. code:: console

    {
    "table1": {
        "record1": {
            "attribute1": "value4"
            }
        }
    }

Output JSON
###########

.. code:: console

    {
      "directive1": {
        "name1": [
          {
            "header1": {
              "name2": "value1",
              "name3": "value4"
            }
          }
        ]
      }
    }
    
Note how the original "override" values are overwritten in the "directive1%header_value". 
"name2" is overwritten with "value1", but "name3" is overwritten with "value4" because 
the named argument takes precedence over the unnamed argument, and the value for the 
"attribute1" attribute of the record is used instead.








Validation
~~~~~~~~~~
Conversion directives are validated before use in the convert command using JSON Schema.

Validation Schema:

.. literalinclude:: ../src/messes/convert/convert_schema.py
    :start-at: { 
    :end-before: #
    :language: none




.. _Metabolomics Workbench: http://www.metabolomicsworkbench.org