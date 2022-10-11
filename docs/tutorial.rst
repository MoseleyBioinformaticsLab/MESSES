Tutorial
========
MESSES is intended to be used solely as a command line program. This 
tutorial describes each command and its options.

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
.. literalinclude:: ../src/messes/extract.py
    :start-at: Usage:
    :end-before: """
    :language: none

The extract command is used to extract tabular data in an Excel workbook or CSV file to JSON. It has several hard to describe options 
and functionality.

Options
-------
**--output** - This option is used to specify the name of the JSON file that will be output. If this option is not specified there will be no output file.

**--compare** - This option allows you to compare the resulting JSON file with the one provided with this option. It will show differences such as missing and extra tables and fields.

**--modify** - This option is used to specify the Excel worksheet name, the Excel file and worksheet name, or the CSV or JSON file name that contains the modification tags. 
The default assumption for MESSES is that the input file is an Excel workbook, so the default sheet name for the modify option is '#modify'. Be sure any input Excel 
files do not have a worksheet with this name if it does not contain modification tags. To specify a separate Excel file and sheet name as the location of modification 
tags the file name/path and sheet name need to be separated by a semicolon. Ex. Modification_tags.xlsx:sheet1. The sheet name can also be a regular expression. 
Ex. Modification_tags.xlsx:r'.*dify'  or just  r'.*dify'  to specify a regex for a sheetname in the input data file. File types other than Excel are specified as 
normal. If multiple input data files are given the specified file or sheet name given to --modify is used for all of them. Details about modification tags are 
in the doc`tagging` section.

**--end-modify** - The same as --modify, but modifications are done at the end after all input data files have been parsed and merged into one JSON file. There is 
no default value.

**--automate** - The same as --modify, but for automation tags. The default sheet name is '#automate'. Details about automation tags are in the doc`tagging` section.

**--save-directives** - This option allows you to save any modification or automation directives as JSON to the specified file path. Note that --end-modify directives 
will overwrite --modify directives so only --end-modify directives will be in the output if specified.

**--save-export** - This option lets you save the version of the data that has all automations applied just before parsing into JSON. It can be useful in debugging. 
The export file will be saved with the same name as the input file with '_export' added to the end. Choose 'csv' to save as a CSV file, and 'xlsx' to save as 
an Excel file. Note that this file will likely not look pretty.

**--show** - This option allows you to see tables or lineages in the input data. Specify 'tables' to see tables, 'lineages' to see lineages, or 'all' to see both.

**--delete** - Use this option to delete tables, records, or fields from the JSONized input. Note that fields can also be deleted using modification tags. This 
option is limited and only allows the deletion of one table, record, or field at a time. Ex. --delete protocol  will delete the protocol table. Tables, records, 
and fields can also be specified with regular expressions. Ex. --delete r'.*tocol' will delete all tables that match the regular expression.

**--keep** - Use this option to keep only the indicated tables in the JSONized output. These are tables only, but multiple tables can be specified. 
Ex. --keep protocol,measurement  will keep only the protocol and measurement tables. Tables can also specified with regular expressions Ex. --keep r'.*tocl',r'measure.*'  
will keep all the tables that match the regular expressions.

**--silent** - This option will silence all warning messages. Errors will still be printed.


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

