Tutorial
========
MESSES is intended to be used solely as a command line program. This 
tutorial describes each command and its options. Before running the program you 
will likely want to review the :doc:`experiment_description_specification` page and the 
:doc:`tagging` page, as well as the examples in the examples folder on the GitHub_ 
repository.

Top-Level Usage

.. literalinclude:: ../src/messes/__main__.py
    :start-at: Usage:
    :end-before: """
    :language: none
    
    
MESSES is broken into 3 main commands, extract, validate, and convert, with convert broken up further for each supported conversion. 
The highest level usage is simply a gateway to the other commands and has very few options. You can see the version with the -v option, 
print the usage with -h option or print all of the commands usage's with the --full-help option.


Extract
~~~~~~~
.. literalinclude:: ../src/messes/extract/extract.py
    :start-at: Usage:
    :end-before: """
    :language: none

The extract command is used to extract tabular data in an Excel workbook or CSV file to JSON. It has several hard to describe options 
and functionality.

Options
-------

--silent  This option will silence all warning messages. Errors will still be printed.

--output  This option is used to specify the name of the JSON file that will be output. If this option is not specified there will be no output file.

--compare  This option allows you to compare the resulting JSON file with the one provided with this option. It will show differences such as missing and extra tables and fields.

--modify  This option is used to specify the Excel worksheet name, the Excel file and worksheet name, or the CSV or JSON file name that contains the modification tags. 
          The default assumption for MESSES is that the input file is an Excel workbook, so the default sheet name for the modify option is '#modify'. Be sure any input Excel 
          files do not have a worksheet with this name if it does not contain modification tags. To specify a separate Excel file and sheet name as the location of modification 
          tags, the file name/path and sheet name need to be separated by a semicolon. Ex. Modification_tags.xlsx:sheet1. The sheet name can also be a regular expression. 
          Ex. Modification_tags.xlsx:r'.*dify'  or just  r'.*dify'  to specify a regex for a sheetname in the input data file. File types other than Excel are specified as 
          normal. If multiple input data files are given, the specified file or sheet name given to --modify is used for all of them. Details about modification tags are 
          in the :doc:`tagging` section.

--end-modify  The same as --modify, but modifications are done at the end, after all input data files have been parsed and merged into one JSON file. There is 
              no default value.

--automate  The same as --modify, but for automation tags. The default sheet name is '#automate'. Details about automation tags are in the :doc:`tagging` section.

--save-directives  This option allows you to save any modification or automation directives as JSON to the specified file path. Note that --end-modify directives 
                   will overwrite --modify directives, so only --end-modify directives will be in the output if specified.

--save-export  This option lets you save the version of the data that has all automations applied just before parsing into JSON. It can be useful for debugging. 
               The export file will be saved with the same name as the input file with '_export' added to the end. Choose 'csv' to save as a CSV file, and 'xlsx' to save as 
               an Excel file. Note that this file will likely not look pretty.

--show  This option allows you to see tables or lineages in the input data. Specify 'tables' to see tables, 'lineages' to see lineages, or 'all' to see both.

--delete  Use this option to delete tables, records, or fields from the JSONized input. Note that fields can also be deleted using modification tags. This 
          option is limited and only allows the deletion of one table, record, or field at a time. Ex. --delete protocol  will delete the protocol table. Tables, records, 
          and fields can also be specified with regular expressions. Ex. --delete r'.*tocol' will delete all tables that match the regular expression. If 
          you would like to delete all records besides those that match a certain pattern you can use a more advanced regular expression. 
          Ex. entity,r'^(?!.*(-ICMS_A|-protein))' will delete all entities that do not have "-ICMS_A" or "-protein" in the id. The (?!...) special 
          grouping matches if the pattern inside is not found. You can see more complex examples of this option in the mwtab examples found in the 
          examples folder of the GitHub_ repository.

--keep  Use this option to keep only the indicated tables in the JSONized output. These are tables only, but multiple tables can be specified. 
        Ex. --keep protocol,measurement  will keep only the protocol and measurement tables. Tables can also specified with regular expressions Ex. --keep r'.*tocl',r'measure.*'  
        will keep all the tables that match the regular expressions.


Examples
--------
Basic Run
+++++++++
Input File:

+-------+---------------+---------------------------------------------------------+---------------------------------------------------------+
| #tags | #sample.id    | #%child.id=-media-0h;#.dry_weight;#.dry_weight%units=mg | #%child.id=-media-3h;#.dry_weight;#.dry_weight%units=mg |
+-------+---------------+---------------------------------------------------------+---------------------------------------------------------+
|       | KO labelled_1 | 4.2                                                     | 8.5                                                     |
+-------+---------------+---------------------------------------------------------+---------------------------------------------------------+
|       | KO labelled_2 | 4.7                                                     | 9.7                                                     |
+-------+---------------+---------------------------------------------------------+---------------------------------------------------------+
|       | ...           | ...                                                     | ...                                                     |
+-------+---------------+---------------------------------------------------------+---------------------------------------------------------+

Command Line:

.. code:: console

    messes extract input_file.csv --output output_file.json


Output JSON:

.. code:: console

    {
      "sample": {
        "KO labelled_1": {
          "id": "KO labelled_1"
        },
        "KO labelled_1-media-0h": {
          "dry_weight": "4.2",
          "dry_weight%units": "mg",
          "id": "KO labelled_1-media-0h",
          "parentID": "KO labelled_1"
        },
        "KO labelled_1-media-3h": {
          "dry_weight": "8.5",
          "dry_weight%units": "mg",
          "id": "KO labelled_1-media-3h",
          "parentID": "KO labelled_1"
        },
        "KO labelled_2": {
          "id": "KO labelled_2"
        },
        "KO labelled_2-media-0h": {
          "dry_weight": "4.7",
          "dry_weight%units": "mg",
          "id": "KO labelled_2-media-0h",
          "parentID": "KO labelled_2"
        },
        "KO labelled_2-media-3h": {
          "dry_weight": "9.7",
          "dry_weight%units": "mg",
          "id": "KO labelled_2-media-3h",
          "parentID": "KO labelled_2"
        }
      }
    }


Compare Option
++++++++++++++
Input File:

+--------+----------------+----------------------------------------------------------+----------------------------------------------------------+
| #tags  | #sample.id     | #%child.id=-media-0h;#.dry_weight;#.dry_weight%units=mg  | #%child.id=-media-3h;#.dry_weight;#.dry_weight%units=mg  |
+========+================+==========================================================+==========================================================+
|        | KO labelled_1  | 4.2                                                      | 8.5                                                      |
+--------+----------------+----------------------------------------------------------+----------------------------------------------------------+
|        | KO labelled_2  | 4.7                                                      | 9.7                                                      |
+--------+----------------+----------------------------------------------------------+----------------------------------------------------------+
|        |                |                                                          |                                                          |
+--------+----------------+----------------------------------------------------------+----------------------------------------------------------+
| #tags  | #protocol.id   | #.field2                                                 |                                                          |
+--------+----------------+----------------------------------------------------------+----------------------------------------------------------+
|        | protocol_1     | value1                                                   |                                                          |
+--------+----------------+----------------------------------------------------------+----------------------------------------------------------+
|        | protocol_2     | value2                                                   |                                                          |
+--------+----------------+----------------------------------------------------------+----------------------------------------------------------+
|        |                |                                                          |                                                          |
+--------+----------------+----------------------------------------------------------+----------------------------------------------------------+
| #tags  | #factor.id     | #.field1                                                 |                                                          |
+--------+----------------+----------------------------------------------------------+----------------------------------------------------------+
|        | factor_1       | value1                                                   |                                                          |
+--------+----------------+----------------------------------------------------------+----------------------------------------------------------+
|        | factor_2       | value2                                                   |                                                          |
+--------+----------------+----------------------------------------------------------+----------------------------------------------------------+

Comparison JSON:

.. code:: console

    {
      "measurement": {
        "measurement_1": {
          "field1": "value1",
          "id": "measurement_1"
        },
        "measurement_2": {
          "field1": "value2",
          "id": "measurement_2"
        }
      },
      "protocol": {
        "protocol_1": {
          "field1": "value1",
          "id": "protocol_1"
        },
        "protocol_2": {
          "field1": "value2",
          "id": "protocol_2"
        }
      },
      "sample": {
        "KO labelled_1": {
          "id": "KO labelled_1"
        },
        "KO labelled_1-media-0h": {
          "dry_weight": "4.2",
          "dry_weight%units": "mg",
          "id": "KO labelled_1-media-0h",
          "parentID": "KO labelled_1"
        },
        "KO labelled_1-media-3h": {
          "dry_weight": "8.5",
          "dry_weight%units": "mg",
          "id": "KO labelled_1-media-3h",
          "parentID": "KO labelled_1"
        },
        "KO labelled_3": {
          "id": "KO labelled_3"
        },
        "KO labelled_3-media-0h": {
          "dry_weight": "4.8",
          "dry_weight%units": "mg",
          "id": "KO labelled_3-media-0h",
          "parentID": "KO labelled_3"
        },
        "KO labelled_3-media-3h": {
          "dry_weight": "8.8",
          "dry_weight%units": "mg",
          "id": "KO labelled_3-media-3h",
          "parentID": "KO labelled_3"
        }
      }
    }

Command Line:

.. code:: console

    messes extract input_file.csv --compare comparison.json
    
Output:

.. code:: console

    Comparison
    Missing Tables: measurement
    Extra Tables: factor
    Table protocol id protocol_1 with different fields: field1, field2
    Table protocol id protocol_2 with different fields: field1, field2
    Table sample with missing records:
       KO labelled_3 KO labelled_3-media-0h KO labelled_3-media-3h
    Table sample with extra records:
       KO labelled_2 KO labelled_2-media-0h KO labelled_2-media-3h


Modify Option
+++++++++++++
#export Sheet:

+--------+----------------+----------------------------------------------------------+
| #tags  | #sample.id     | #%child.id=-media-0h;#.dry_weight;#.dry_weight%units=mg  |
+========+================+==========================================================+
|        | KO labelled_1  | 4.2                                                      |
+--------+----------------+----------------------------------------------------------+
|        | KO labelled_2  | 4.7                                                      |
+--------+----------------+----------------------------------------------------------+

#modify sheet:

+--------+-------------------+--------------------------------+
| #tags  | #sample.id.value  | #sample.id.regex               |
+========+===================+================================+
|        | r'KO labelled.*'  | r'KO labelled',r'KO_labelled'  |
+--------+-------------------+--------------------------------+

Command Line:

.. code:: console

    messes extract input_file.xlsx --output output.json

Output JSON:

.. code:: console

    {
      "sample": {
        "KO_labelled_1": {
          "dry_weight": "4.2",
          "dry_weight%units": "mg",
          "id": "KO_labelled_1"
        },
        "KO_labelled_3": {
          "dry_weight": "4.8",
          "dry_weight%units": "mg",
          "id": "KO_labelled_3"
        }
      }
    }
    

Automate Option
+++++++++++++++
#export Sheet:

+----------------+---------+
| Sample ID      | Weight  |
+================+=========+
| KO labelled_1  | 4.2     |
+----------------+---------+
| KO labelled_3  | 4.8     |
+----------------+---------+

#automate Sheet:

+--------+------------+-------------------------------------+
| #tags  | #header    | #add                                |
+========+============+=====================================+
|        | Sample ID  | #sample.id                          |
+--------+------------+-------------------------------------+
|        | Weight     | #.dry_weight;#.dry_weight%units=mg  |
+--------+------------+-------------------------------------+

Command Line:

.. code:: console

    messes extract input_file.xlsx --output output.json
    
Output JSON:

.. code:: console

    {
      "sample": {
        "KO labelled_1": {
          "dry_weight": "4.2",
          "dry_weight%units": "mg",
          "id": "KO labelled_1"
        },
        "KO labelled_3": {
          "dry_weight": "4.8",
          "dry_weight%units": "mg",
          "id": "KO labelled_3"
        }
      }
    }


Save Directives Option
++++++++++++++++++++++
#export Sheet:

+----------------+---------+
| Sample ID      | Weight  |
+================+=========+
| KO labelled_1  | 4.2     |
+----------------+---------+
| KO labelled_3  | 4.8     |
+----------------+---------+

#automate Sheet:

+--------+------------+-------------------------------------+
| #tags  | #header    | #add                                |
+========+============+=====================================+
|        | Sample ID  | #sample.id                          |
+--------+------------+-------------------------------------+
|        | Weight     | #.dry_weight;#.dry_weight%units=mg  |
+--------+------------+-------------------------------------+

#modify Sheet:

+--------+-------------------+--------------------------------+
| #tags  | #sample.id.value  | #sample.id.regex               |
+========+===================+================================+
|        | r'KO labelled.*'  | r'KO labelled',r'KO_labelled'  |
+--------+-------------------+--------------------------------+

Command Line:

.. code:: console

    messes extract input_file.xlsx --output output.json --save-directives directives.json

Output JSON:

.. code:: console

    {
      "sample": {
        "KO_labelled_1": {
          "dry_weight": "4.2",
          "dry_weight%units": "mg",
          "id": "KO_labelled_1"
        },
        "KO_labelled_3": {
          "dry_weight": "4.8",
          "dry_weight%units": "mg",
          "id": "KO_labelled_3"
        }
      }
    }

Output Directives:

.. code:: console

    {
      "automation": [
        {
          "header_tag_descriptions": [
            {
              "header": "Sample ID",
              "required": true,
              "tag": "#sample.id"
            },
            {
              "header": "Weight",
              "required": true,
              "tag": "#.dry_weight;#.dry_weight%units=mg"
            }
          ]
        }
      ],
      "modification": {
        "sample": {
          "id": {
            "regex-all": {
              "r'KO labelled.*'": {
                "regex": {
                  "id": [
                    "r'KO labelled'",
                    "r'KO_labelled'"
                  ]
                }
              }
            }
          }
        }
      }
    }


Save Export Option
++++++++++++++++++
#export Sheet:

+----------------+---------+
| Sample ID      | Weight  |
+================+=========+
| KO labelled_1  | 4.2     |
+----------------+---------+
| KO labelled_3  | 4.8     |
+----------------+---------+

#automate Sheet:

+--------+------------+-------------------------------------+
| #tags  | #header    | #add                                |
+========+============+=====================================+
|        | Sample ID  | #sample.id                          |
+--------+------------+-------------------------------------+
|        | Weight     | #.dry_weight;#.dry_weight%units=mg  |
+--------+------------+-------------------------------------+

Command Line:

.. code:: console

    messes extract input_file.xlsx --output output.json --save-export csv

Output JSON:

.. code:: console

    {
      "sample": {
        "KO labelled_1": {
          "dry_weight": "4.2",
          "dry_weight%units": "mg",
          "id": "KO labelled_1"
        },
        "KO labelled_3": {
          "dry_weight": "4.8",
          "dry_weight%units": "mg",
          "id": "KO labelled_3"
        }
      }
    }

Export Output:

+----------+----------------+-------------------------------------+
| #ignore  | Sample ID      | Weight                              |
+==========+================+=====================================+
| #tags    | #sample.id     | #.dry_weight;#.dry_weight%units=mg  |
+----------+----------------+-------------------------------------+
|          | KO labelled_1  | 4.2                                 |
+----------+----------------+-------------------------------------+
|          | KO labelled_3  | 4.8                                 |
+----------+----------------+-------------------------------------+


Show Option
+++++++++++

Input File:

+--------+----------------+----------------------------------------------------------+----------------------------------------------------------+
| #tags  | #sample.id     | #%child.id=-media-0h;#.dry_weight;#.dry_weight%units=mg  | #%child.id=-media-3h;#.dry_weight;#.dry_weight%units=mg  |
+========+================+==========================================================+==========================================================+
|        | KO labelled_1  | 4.2                                                      | 8.5                                                      |
+--------+----------------+----------------------------------------------------------+----------------------------------------------------------+
|        | KO labelled_2  | 4.7                                                      | 9.7                                                      |
+--------+----------------+----------------------------------------------------------+----------------------------------------------------------+
|        |                |                                                          |                                                          |
+--------+----------------+----------------------------------------------------------+----------------------------------------------------------+
| #tags  | #protocol.id   | #.field2                                                 |                                                          |
+--------+----------------+----------------------------------------------------------+----------------------------------------------------------+
|        | protocol_1     | value1                                                   |                                                          |
+--------+----------------+----------------------------------------------------------+----------------------------------------------------------+
|        | protocol_2     | value2                                                   |                                                          |
+--------+----------------+----------------------------------------------------------+----------------------------------------------------------+
|        |                |                                                          |                                                          |
+--------+----------------+----------------------------------------------------------+----------------------------------------------------------+
| #tags  | #factor.id     | #.field1                                                 |                                                          |
+--------+----------------+----------------------------------------------------------+----------------------------------------------------------+
|        | factor_1       | value1                                                   |                                                          |
+--------+----------------+----------------------------------------------------------+----------------------------------------------------------+
|        | factor_2       | value2                                                   |                                                          |
+--------+----------------+----------------------------------------------------------+----------------------------------------------------------+

Command Line:

.. code:: console

    messes extract input_file.csv --show tables

Output:

.. code:: console

    Tables:  sample protocol factor
    
Command Line:

.. code:: console

    messes extract input_file.csv --show lineage
    
Output:

.. code:: console

     sample :
       KO labelled_1 :
         KO labelled_1-media-0h, KO labelled_1-media-3h
       KO labelled_2 :
         KO labelled_2-media-0h, KO labelled_2-media-3h

Command Line:

.. code:: console

    messes extract input_file.csv --show all

Output:

.. code:: console

    Tables:  sample protocol factor
     sample :
       KO labelled_1 :
         KO labelled_1-media-0h, KO labelled_1-media-3h
       KO labelled_2 :
         KO labelled_2-media-0h, KO labelled_2-media-3h








Validate
~~~~~~~~
.. literalinclude:: ../src/messes/validate/validate.py
    :start-at: Usage:
    :end-before: """
    :language: none

Validation can be broken down into layers. The first layer is making sure the data is valid 
against the :doc:`experiment_description_specification`. This includes things such as making sure every protocol 
is one of the 5 types, making sure every sample entity has a parent, and all records have the 
required fields. This layer is built into the validate command and does not require any 
user input. The second layer is a layer that validates fields in table records based on 
their protocol(s). This layer does require the user to generate what is called a :doc:`protocol_dependent_schema` 
(PDS) that defines what fields are required for records with the protocols that are in it. 
The protocol-dependent schema can be a JSON file or a tagged tabular file detailed below. The 
protocol-dependent schema is not required, but it is highly recommended to minimize problems in 
the conversion step.

The validate command is used to validate extracted data. It is not guaranteed to catch everything wrong, but it makes a best attempt to check for 
common issues. This can be highly influenced by the user through the --pds and --additional options, which allow the user to specify a protocol-dependent 
schema and additional JSON schema, respectively. The protocol-dependent schema (PDS) is detailed in the :doc:`protocol_dependent_schema` section of the documentation, and allows 
users to specify additional validation based on the protocols of records. The additional JSON schema is any arbitrary valid `JSON schema <https://json-schema.org/understanding-json-schema/>`_ and it is 
simply used as is as additional validation.

While the "json" command is the reason validate was created the other commands were added to support it. The "save-schema" command was added so 
that users can see the JSON schema being created and used by the "json" command and possibly modify it for use with the --additional option. 
The "schema" command was added as an easy way for users to check that any JSON schemas they create are valid. Similarly, the "pds" command was 
added so users can check that the protocol-dependent schemas they create are valid. The "pds-to-table" command was created so that a JSONized 
protocol-dependent schema can be transformed into a tabular form that may be easier to edit and view. The "pds-to-json" command is the inverse 
of the "pds-to-table" command and will take a protocol-dependent schema in tabular form and convert it to JSON. Note that this is just the 
protocol-dependent schema in JSON form, and not the protocol-dependent schema built into a JSON Schema. To build the protocol-dependent schema 
into a JSON Schema and save it, use the "--save" option of the "pds" command. The "cd-to-json-schema" command will take a 
conversion directives file for the convert command and create a JSON Schema template from it that can be used as a start to creating a schema 
that can be used to validate data before those conversion directives are used on it. The command goes through the conversion directives and 
finds all fields used and required by the directives to create the JSON Schema template. The template alone is not enough and additional 
checks on the fields such as type checks need to be added manually to the template, but it is a good place to start.

Although the validate command uses JSON schema, it also introduces 4 new formats. The "integer" and "numeric" formats were introduced 
so that string type values can be treated as numeric type values. It allows you to use JSON schema keywords such as "minimum" even if 
the value is a string type. This is accomplished by converting the string value to an integer or floating point type before validating 
those keywords. As an example, say we have an "intensity" field whose value is "1234" as a string type. If you would like to validate 
that all intensity fields are greater than 0 you can use the "minimum" keyword in JSON schema. Normally, this wouldn't work as the value 
is a string type, but if you add a "format" keyword and set the format to "numeric" then the validate command will convert intensity fields 
to floats before doing the normal JSON schema validation. The import thing to be aware of here is NOT to set the "type" keyword to "string" 
for any field that you use the "integer" or "numeric" format on because it will throw a wrong type validation error after the conversion to 
a numeric type. If you need to enforce a string type and also want the benefits of the "integer" and "numeric" formats, then use the "str_integer" 
and "str_numeric" formats. They operate the same as their "integer" and "numeric" counterparts, but also validate that the value is a string 
type. Again, DO NOT set a "type" field equal to "string" at the same time when using any of these formats because it will throw a wrong type 
validation error. "string" can be included in a list of types, but cannot be the only type.

Options
-------

--silent  This option specifies what warnings should be printed. "full" will silence all warnings, "nuisance" will only silence warnings that 
          have been deemed to be a nuisance in some circumstances, and "none" will silence no warnings which is the default.

--pds  This option specifies that a protocol-dependent schema should be used with the command and where to read the file from. If "-" is given, 
       the PDS will be read from stdin, anything else is interpreted as a filepath. If the PDS is an Excel file, the default sheet name to read in is 
       #validate, to specify a different sheet name separate it from the file name with a colon ex: file_name.xlsx:sheet_name.

--csv  This option specifies that the PDS file is a CSV (comma delimited) file. If the PDS file is read from stdin, it is required to indicate 
       what type of file it is, otherwise it will be determined from the file extension if not specified.

--xlsx  This option specifies that the PDS file is an Excel file. This type of file cannot be read from stdin, but can still be specified to 
        indicate that the PDS file is an Excel file.

--json  This option specifies that the PDS file is a JSON file. If the PDS file is read from stdin, it is required to indicate what type of 
         file it is, otherwise it will be determined from the file extension if not specified.
         
--gs  This option specifies that the PDS file is a Google Sheets file. This type of file cannot be read from stdin, but can still be specified to 
        indicate that the PDS file is a Google Sheets file.

--additional  This option specifies that an additional JSON schema file should be used with the command and where to read the file from. 
              If "-" is given, the file will be read from stdin, anything else is interpreted as a filepath.

--format  This option specifies that additional validation should be done with the assumption that the input JSON is going to be converted 
          into the given format.

--no_base_schema  This option specifies that validation against the base schema should not be done. Use this along with the 
                  --no_extra_checks option to validate against only your own schema supplied with the --additional option.

--no_extra_checks  This option specifies that extra validation beyond the base schema should not be done. Use this along with the 
                   --no_base_schema option to validate against only your own schema supplied with the --additional option.

--input  This option specifies that an input JSON file should be used with the "save-schema" command and where to read the file from. 
         If "-" is given, the file will be read from stdin, anything else is interpreted as a filepath. If a PDS is given, protocols from the input 
         protocol table are added to the parent_protocol table in the PDS, which changes the final schema used for validation. So you may need to specify 
         an input JSON file to reproduce the schema from the "json" command exactly.
         
--save  This option specifies that the JSON Schema created from the PDS should be saved out to the indicated file path.


Examples
--------
The inputs and outputs are too large to demonstrate readily inline, but there are examples available in the examples folder on the GitHub_ repository.

Basic JSON Validation
+++++++++++++++++++++
Command Line:

.. code:: console

    messes validate json input.json


JSON Validation Against A Supported Format
++++++++++++++++++++++++++++++++++++++++++
Command Line:

.. code:: console

    messes validate json input.json --format mwtab_MS


JSON Validation With A Protocol-Dependent Schema
++++++++++++++++++++++++++++++++++++++++++++++++
Command Line:

.. code:: console

    messes validate json input.json --pds PDS_file.json


JSON Validation With Added User Schema
++++++++++++++++++++++++++++++++++++++
Command Line:

.. code:: console

    messes validate json input.json --additional user_schema.json


JSON Validation With Only Added User Schema
+++++++++++++++++++++++++++++++++++++++++++
Command Line:

.. code:: console

    messes validate json input.json --additional user_schema.json --no_base_schema --no_extra_checks
    

Read Input JSON From STDIN
++++++++++++++++++++++++++
Command Line:

.. code:: console

    messes validate json -


Read Protocol-Dependent Schema From STDIN
+++++++++++++++++++++++++++++++++++++++++
Command Line:

.. code:: console

    messes validate json input.json --pds - --json


Save Base Schema
++++++++++++++++
Command Line:

.. code:: console

    messes validate save-schema output_name.json


Save Composite Schema
+++++++++++++++++++++
Command Line:

.. code:: console

    messes validate save-schema output_name.json --pds PDS_file.json --input input.json


Save Format Schema
++++++++++++++++++
Command Line:

.. code:: console

    messes validate save-schema output_name.json --format mwtab_MS
    

Validate A JSON Schema
++++++++++++++++++++++
Command Line:

.. code:: console

    messes validate schema input_schema.json
    

Validate A Protocol-Dependent Schema
++++++++++++++++++++++++++++++++++++
Command Line:

.. code:: console

    messes validate pds PDS_file.json


Save The JSON Schema Created From The Protocol-Dependent Schema
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Command Line:

.. code:: console

    messes validate pds PDS_file.json --save PDS_JSON_Schema.json
    

Transform A JSONized Protocol-Dependent Schema To A Table
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Command Line:

.. code:: console

    messes validate pds-to-table PDS_file.json tabular_PDS_file.csv


Transform A Tabular Protocol-Dependent Schema To JSON
+++++++++++++++++++++++++++++++++++++++++++++++++++++
Command Line:

.. code:: console

    messes validate pds-to-json PDS_file.csv JSONized_PDS_file.json


Create A JSON Schema From Conversion Directives
+++++++++++++++++++++++++++++++++++++++++++++++
Command Line:

.. code:: console

    messes validate cd-to-json-schema directives.json directives_schema.json



Convert
~~~~~~~
.. literalinclude:: ../src/messes/convert/convert.py
    :start-at: Usage:
    :end-before: """
    :language: none

The convert command is used to convert extracted and validated data from it's intermediate JSON form to the final desired format. There are commands for 
each supported format, detailed in the :doc:`supported_formats` section, that use built-in conversion directives, and the "generic" command that requires 
the user supply conversion directives. The supported formats may have additional sub-commands depending on the complexity of the format. Details about 
each supported format are in the :doc:`supported_formats` section, and it is HIGHLY recommended to read through that section and look at examples before 
attempting a conversion.

Options
-------

--update  For supported formats, allows the user to specify a file of conversion directives that will be used to update the built-in directives for the format. 
          This is intended to be used for simple changes such as updating the value of the analysis ID. You only have to specify what 
          needs to change. Any values that are left out of the update directives won't be changed. If you need to remove directives, 
          then use the override option.

--override  For supported formats, allows the user to override the built-in directives for the format. The built-in directives 
            will not be used and these will be used instead.

--silent  This option will silence all warning messages. Errors will still be printed.


Examples
--------
The inputs and outputs are too large to demonstrate readily inline, but there are examples available in the examples folder on the GitHub_ repository.

Basic Supported Format Run
++++++++++++++++++++++++++
Command Line:

.. code:: console

    messes convert mwtab ms input_file.json my_output_name


Updating Built-In Directives For Supported Format Run 
+++++++++++++++++++++++++++++++++++++++++++++++++++++
Command Line:

.. code:: console

    messes convert mwtab ms input_file.json my_output_name --update directive_changes.json


Overriding Built-In Directives For Supported Format Run 
+++++++++++++++++++++++++++++++++++++++++++++++++++++++
Command Line:

.. code:: console

    messes convert mwtab ms input_file.json my_output_name --override new_directives.json


Save Built-In Directives For Supported Formats
++++++++++++++++++++++++++++++++++++++++++++++
Command Line:

.. code:: console

    messes convert save-directives ms json


Basic Generic Run
+++++++++++++++++
Command Line:

.. code:: console

    messes convert generic input_file.json my_output_name my_conversion_directives.json



.. _GitHub: https://github.com/MoseleyBioinformaticsLab/messes