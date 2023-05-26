Protocol-Dependent Schema
=========================
The protocol-dependent schema (PDS) represents an entity-attribute-value model used to validate the intermediate JSON based on the protocols present.

Protocol-Dependent Schema - JSON
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If the protocol-dependent schema is given in the form of a JSON file, it is expected to follow a certain 
schema. The general format is shown below:

.. code:: console

    {
    "parent_protocol":{
        "protocol_1":{
            "type":"<protocol_type>",
            "description":"<protocol_description>",
            "parentID":"<protocol_parent_id>"
            }
        ...
        },
    "protocol_1":{
        "field_1":{
            "type":"<field_type>",
            "required":"True",
            "table":"<table_field_is_applied_to>"
            }
        ...
        }
    ...
    }

The first table shown is the "parent_protocol" table, named so it will not be confused with the "protocol" table in :doc:`experiment_description_specification`. 
The parent_protocol is required to specify the types of the protocols in the JSON, but 
also allows you to specify inheritance of protocols. The children of a protocol 
inherit all of the required fields of not only its parent, but all of its ancestors. 
This makes it so that you don't have to specify the same field multiple times for 
each protocol.

All other tables in the JSON should be protocols with specifications for their fields. 
The table name is the name of the protocol, and each record of the table is the name 
of a field associated with the protocol. The fields in each record describe the requirements 
the record must meet. Most fields are taken from `JSON Schema <https://json-schema.org/understanding-json-schema/>`_, 
and will be directly translated into the JSON schema that is built from the protocol-dependent 
schema. Let's look at an example.

.. code:: console

    {
    "master_measurement": {
        "instrument": {
          "minLength": "1",
          "required": "True",
          "table": "protocol",
          "type": "string"
        },
        "instrument_type": {
          "minLength": "1",
          "required": "False",
          "table": "protocol",
          "type": "string"
        },
        "entity.id": {
          "minLength": "1",
          "required": "True",
          "table": "measurement",
          "type": "string"
        }
      }
    }

The "instrument" record has the fields "minLength", "required", "table", and "type". 
"minLength", "required", and "type" are all keywords in `JSON Schema <https://json-schema.org/understanding-json-schema/>`_. 
"minLength" and "type" will be copied as is into the JSON schema for the "instrument" property, 
but "required" will be used to build the "required" attribute for "master_measurement". 
The "table" field should be one of "protocol", "measurement", or "entity" and indicates which 
table the record is associated with. For "instrument" and "instrument_type", the table is 
"protocol", which means that records in the "protocol" table of the input JSON that 
have the same name as "master_measurement" or inherit from it must comply with the 
"instrument" and "instrument_type" specifications. For example, a protocol that inherits 
from "master_measurement" must have a field called "instrument" that has a string value 
that is at least 1 character long, but is not required to have a "instrument_type" field 
since its "required" field is "False". The "measurement" and "entity" tables are similar, 
but a record in those tables has to have a "protocol.id" field with the protocol or 
one that inherits from it. For example, if a measurement record had the "master_measurement" 
protocol it would be required to have a "entity.id" field that is a string with at least 
one character.

PDS JSON to JSON Schema
-----------------------
The above example would translate to JSON Schema as shown below:

.. code:: console

    # protocol table properties
    {
    "properties":{
        "instrument": {"type":"string", "minLength":1},
        "instrument_type": {"type":"string", "minLength":1},
      },
      "required": [
        "instrument"
      ]
    }
    
    # entity table properties
    {
    "properties":{
        "entity.id": {"type":"string", "minLength":1},
      },
      "required": [
        "entity.id"
      ]
    }
    
These are then placed in larger conditional schema as follows:

.. code:: console

    {
    "type":"object",
    "properties":{
        "protocol":{
            "type":"object",
            "additionalProperties":{
                "type":"object",
                "properties":{
                    "id": {"type":"string", "minLength":1},
                    "parentID": {"type":["string", "array"]},
                    "type": {"type":"string", "enum":["sample_prep", "treatment", "collection", "storage", "measurement"]},
                    "description": {"type":"string"},
                    "filename": {"type":"string"}
                    },
                "required": ["id"],
                "allOf":[
                    {
                    "if":{
                          "anyOf":[
                              {"properties":{"id":{"const":"master_measurement"}},
                              "required":["id"]},
                              {"properties":{"parentID":{"anyOf":[
                                                          {"const":"master_measurement"}, 
                                                          {"type":"array", "contains":{"const":"master_measurement"}}
                                                          ]}},
                              "required":["parentID"]}
                              ]
                        },
                    "then":{
                        "properties":{
                            "instrument": {"type":"string", "minLength":1},
                            "instrument_type": {"type":"string", "minLength":1},
                          },
                          "required": [
                            "instrument"
                          ]
                        }
                    },
                    ]
                }
            },
        "measurement":{
                 "type": "object",
                 "minProperties":1,
                 "additionalProperties":{
                         "type":"object",
                         "properties":{
                             "id": {"type":"string", "minLength":1},
                             "entity.id": {"type":"string", "minLength":1},
                             "protocol.id": {"type":["string", "array"], "minItems":1, "items":{"type":"string", "minLength":1}, "minLength":1}
                             },
                         "required": ["id", "entity.id", "protocol.id"],
                         "allOf":[
                             {
                             "if":{
                                 "properties":{"protocol.id":{"anyOf":[
                                                             {"const":"master_measurement"}, 
                                                             {"type":"array", "contains":{"const":"master_measurement"}}
                                                             ]}}
                                 },
                             "then":{
                                 "properties":{
                                     "entity.id": {"type":"string", "minLength":1}
                                   },
                                   "required": [
                                     "entity.id"
                                   ]
                                 }
                             },
                             ]
                         }
                }
        }
    }
    
The protocol name is used inside the "if" subschema of the "allOf" properties to 
conditionally apply the "properties" in the "then" subschema to records in the "protocol" 
and "measurement" tables.

Attributes such as "type", which correspond to keywords in `JSON Schema <https://json-schema.org/understanding-json-schema/>`_ 
will be copied as is into the JSON schema that will be used to validate the field 
for the protocol, but with some caveats. It has already been mentioned that the 
"required" property will be used to build the "required" array in the JSON schema, 
but there are some other keywords in `JSON Schema <https://json-schema.org/understanding-json-schema/>`_ 
that have special translations as well. For example, the "items" keyword must be an 
object type or boolean type to be valid in `JSON Schema <https://json-schema.org/understanding-json-schema/>`_. 
But due to the limitations of the export part of the tagging system, there is not a way to specify 
an "items" property of this type. To get around this limitation, if properties such 
as "items" are a string type, they will first be put through the eval() function before 
being copied into the JSON schema. Let's see an example.

.. code:: console

    {
    "master_measurement": {
        "filenames": {
          "type": "array",
          "items":"{\"type\":\"string\", \"minLength\":1}"
          "table": "protocol",
        }
      }
    }
    
This translates to JSON Schema properties as:

.. code:: console

    {
    "properties":{
        "filenames": {"type":"array", "items":{"type":"string", "minLength":1}},
      }
    }

Just know that for most keywords in `JSON Schema <https://json-schema.org/understanding-json-schema/>`_, 
it is acceptable to put a string value in place of the proper type. This 
is done to support the tabular form of the protocol-dependent schema as described below. 
A best attempt has been made to support most of the features of JSON Schema, but 
not everything has been tested or is guaranteed to work. If you find an error or 
something you would like to be added, then please open an `issue <https://github.com/MoseleyBioinformaticsLab/MESSES/issues>`_ on GitHub.

Protocol-Dependent Schema - Table
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The above JSON representation can be specified in tabular form using the export tags 
described in :doc:`tagging`. The general format is shown below:

+--------+----------------------------+-------------------------------------------+-------------------------+-----------------------+
| #tags  | #parent_protocol.id        | #.type                                    | #.description           | #.parentID            |
+========+============================+===========================================+=========================+=======================+
|        | <protocol_name>            | <protocol_type>                           | <protocol_description>  | <protocol_parent_id>  |
+--------+----------------------------+-------------------------------------------+-------------------------+-----------------------+
|        |                            |                                           |                         |                       |
+--------+----------------------------+-------------------------------------------+-------------------------+-----------------------+
| #tags  | #<protocol_name>.id        | #.table                                   | #.<field_1>             |                       |
+--------+----------------------------+-------------------------------------------+-------------------------+-----------------------+
|        | <field_name_for_protocol>  | <"protocol", "measurement", or "entity">  | <field_value>           |                       |
+--------+----------------------------+-------------------------------------------+-------------------------+-----------------------+

An extended example that includes the "master_measurement" as well as some additional 
protocols to illustrate inheritance is shown below:

+--------+------------------------------------+--------------+---------------------+-------------+--------------------------------------------------------+-----------+
| #tags  | #parent_protocol.id                | #.type       | #.parentID          | #.filename  | #.description                                          |           |
+========+====================================+==============+=====================+=============+========================================================+===========+
|        | master_measurement                 | measurement  |                     |             | master measurement protocol                            |           |
+--------+------------------------------------+--------------+---------------------+-------------+--------------------------------------------------------+-----------+
|        | MS_measurement                     | measurement  | master_measurement  |             | Measurements made using mass spec                      |           |
+--------+------------------------------------+--------------+---------------------+-------------+--------------------------------------------------------+-----------+
|        | Chromatography_MS_measurement      | measurement  | MS_measurement      |             | Measurements made using mass spec with chromatography  |           |
+--------+------------------------------------+--------------+---------------------+-------------+--------------------------------------------------------+-----------+
|        |                                    |              |                     |             |                                                        |           |
+--------+------------------------------------+--------------+---------------------+-------------+--------------------------------------------------------+-----------+
| #tags  | #master_measurement.id             | #.type       | #.minLength         | #.required  | #.table                                                |           |
+--------+------------------------------------+--------------+---------------------+-------------+--------------------------------------------------------+-----------+
|        | instrument                         | string       | 1                   | TRUE        | protocol                                               |           |
+--------+------------------------------------+--------------+---------------------+-------------+--------------------------------------------------------+-----------+
|        | instrument_type                    | string       | 1                   | FALSE       | protocol                                               |           |
+--------+------------------------------------+--------------+---------------------+-------------+--------------------------------------------------------+-----------+
|        |                                    |              |                     |             |                                                        |           |
+--------+------------------------------------+--------------+---------------------+-------------+--------------------------------------------------------+-----------+
| #tags  | #master_measurement.id             | #.type       | #.minLength         | #.required  | #.table                                                |           |
+--------+------------------------------------+--------------+---------------------+-------------+--------------------------------------------------------+-----------+
|        | entity.id                          | string       | 1                   | TRUE        | measurement                                            |           |
+--------+------------------------------------+--------------+---------------------+-------------+--------------------------------------------------------+-----------+
|        |                                    |              |                     |             |                                                        |           |
+--------+------------------------------------+--------------+---------------------+-------------+--------------------------------------------------------+-----------+
| #tags  | #MS_measurement.id                 | #.type       | #.minLength         | #.required  | #.table                                                |           |
+--------+------------------------------------+--------------+---------------------+-------------+--------------------------------------------------------+-----------+
|        | ion_mode                           | string       | 1                   | TRUE        | protocol                                               |           |
+--------+------------------------------------+--------------+---------------------+-------------+--------------------------------------------------------+-----------+
|        | ionization                         | string       | 1                   | TRUE        | protocol                                               |           |
+--------+------------------------------------+--------------+---------------------+-------------+--------------------------------------------------------+-----------+
|        |                                    |              |                     |             |                                                        |           |
+--------+------------------------------------+--------------+---------------------+-------------+--------------------------------------------------------+-----------+
| #tags  | #MS_measurement.id                 | #.type       | #.minLength         | #.required  | #.table                                                | #.format  |
+--------+------------------------------------+--------------+---------------------+-------------+--------------------------------------------------------+-----------+
|        | assignment                         | string       | 1                   | TRUE        | measurement                                            |           |
+--------+------------------------------------+--------------+---------------------+-------------+--------------------------------------------------------+-----------+
|        | assignment%method                  | string       | 1                   | TRUE        | measurement                                            |           |
+--------+------------------------------------+--------------+---------------------+-------------+--------------------------------------------------------+-----------+
|        | compound                           | string       | 1                   | FALSE       | measurement                                            |           |
+--------+------------------------------------+--------------+---------------------+-------------+--------------------------------------------------------+-----------+
|        | intensity                          | string       | 1                   | TRUE        | measurement                                            | numeric   |
+--------+------------------------------------+--------------+---------------------+-------------+--------------------------------------------------------+-----------+
|        | intensity%type                     | string       | 1                   | FALSE       | measurement                                            |           |
+--------+------------------------------------+--------------+---------------------+-------------+--------------------------------------------------------+-----------+
|        | intensity%units                    | string       | 1                   | FALSE       | measurement                                            |           |
+--------+------------------------------------+--------------+---------------------+-------------+--------------------------------------------------------+-----------+
|        | isotopologue                       | string       | 1                   | FALSE       | measurement                                            |           |
+--------+------------------------------------+--------------+---------------------+-------------+--------------------------------------------------------+-----------+
|        | isotopologue%type                  | string       | 1                   | FALSE       | measurement                                            |           |
+--------+------------------------------------+--------------+---------------------+-------------+--------------------------------------------------------+-----------+
|        |                                    |              |                     |             |                                                        |           |
+--------+------------------------------------+--------------+---------------------+-------------+--------------------------------------------------------+-----------+
| #tags  | #Chromatography_MS_measurement.id  | #.type       | #.minLength         | #.required  | #.table                                                |           |
+--------+------------------------------------+--------------+---------------------+-------------+--------------------------------------------------------+-----------+
|        | chromatography_description         | string       | 1                   | FALSE       | protocol                                               |           |
+--------+------------------------------------+--------------+---------------------+-------------+--------------------------------------------------------+-----------+
|        | chromatography_instrument_name     | string       | 1                   | TRUE        | protocol                                               |           |
+--------+------------------------------------+--------------+---------------------+-------------+--------------------------------------------------------+-----------+
|        | chromatography_type                | string       | 1                   | TRUE        | protocol                                               |           |
+--------+------------------------------------+--------------+---------------------+-------------+--------------------------------------------------------+-----------+
|        | column_name                        | string       | 1                   | TRUE        | protocol                                               |           |
+--------+------------------------------------+--------------+---------------------+-------------+--------------------------------------------------------+-----------+
|        |                                    |              |                     |             |                                                        |           |
+--------+------------------------------------+--------------+---------------------+-------------+--------------------------------------------------------+-----------+
| #tags  | #Chromatography_MS_measurement.id  | #.type       | #.minLength         | #.required  | #.table                                                | #.format  |
+--------+------------------------------------+--------------+---------------------+-------------+--------------------------------------------------------+-----------+
|        | retention_time                     | string       | 1                   | FALSE       | measurement                                            | numeric   |
+--------+------------------------------------+--------------+---------------------+-------------+--------------------------------------------------------+-----------+
|        | retention_time%units               | string       | 1                   | FALSE       | measurement                                            |           |
+--------+------------------------------------+--------------+---------------------+-------------+--------------------------------------------------------+-----------+

The above table then translates to JSON:

.. code:: console

    {
      "Chromatography_MS_measurement": {
        "chromatography_description": {
          "id": "chromatography_description",
          "minLength": "1",
          "required": "False",
          "table": "protocol",
          "type": "string"
        },
        "chromatography_instrument_name": {
          "id": "chromatography_instrument_name",
          "minLength": "1",
          "required": "True",
          "table": "protocol",
          "type": "string"
        },
        "chromatography_type": {
          "id": "chromatography_type",
          "minLength": "1",
          "required": "True",
          "table": "protocol",
          "type": "string"
        },
        "column_name": {
          "id": "column_name",
          "minLength": "1",
          "required": "True",
          "table": "protocol",
          "type": "string"
        },
        "retention_time": {
          "format": "numeric",
          "id": "retention_time",
          "minLength": "1",
          "required": "False",
          "table": "measurement",
          "type": "string"
        },
        "retention_time%units": {
          "format": "",
          "id": "retention_time%units",
          "minLength": "1",
          "required": "False",
          "table": "measurement",
          "type": "string"
        }
      },
      "MS_measurement": {
        "assignment": {
          "format": "",
          "id": "assignment",
          "minLength": "1",
          "required": "True",
          "table": "measurement",
          "type": "string"
        },
        "assignment%method": {
          "format": "",
          "id": "assignment%method",
          "minLength": "1",
          "required": "True",
          "table": "measurement",
          "type": "string"
        },
        "compound": {
          "format": "",
          "id": "compound",
          "minLength": "1",
          "required": "False",
          "table": "measurement",
          "type": "string"
        },
        "intensity": {
          "format": "numeric",
          "id": "intensity",
          "minLength": "1",
          "required": "True",
          "table": "measurement",
          "type": "string"
        },
        "intensity%type": {
          "format": "",
          "id": "intensity%type",
          "minLength": "1",
          "required": "False",
          "table": "measurement",
          "type": "string"
        },
        "intensity%units": {
          "format": "",
          "id": "intensity%units",
          "minLength": "1",
          "required": "False",
          "table": "measurement",
          "type": "string"
        },
        "ion_mode": {
          "id": "ion_mode",
          "minLength": "1",
          "required": "True",
          "table": "protocol",
          "type": "string"
        },
        "ionization": {
          "id": "ionization",
          "minLength": "1",
          "required": "True",
          "table": "protocol",
          "type": "string"
        },
        "isotopologue": {
          "format": "",
          "id": "isotopologue",
          "minLength": "1",
          "required": "False",
          "table": "measurement",
          "type": "string"
        },
        "isotopologue%type": {
          "format": "",
          "id": "isotopologue%type",
          "minLength": "1",
          "required": "False",
          "table": "measurement",
          "type": "string"
        }
      },
      "master_measurement": {
        "instrument": {
          "id": "instrument",
          "minLength": "1",
          "required": "True",
          "table": "protocol",
          "type": "string"
        },
        "instrument_type": {
          "id": "instrument_type",
          "minLength": "1",
          "required": "False",
          "table": "protocol",
          "type": "string"
        },
        "entity.id": {
          "id": "entity.id",
          "minLength": "1",
          "required": "True",
          "table": "measurement",
          "type": "string"
        }
      },
      "parent_protocol": {
        "Chromatography_MS_measurement": {
          "description": "Measurements made using mass spec with chromatography",
          "filename": "",
          "id": "Chromatography_MS_measurement",
          "parentID": "MS_measurement",
          "type": "measurement"
        },
        "MS_measurement": {
          "description": "Measurements made using mass spec",
          "filename": "",
          "id": "MS_measurement",
          "parentID": "master_measurement",
          "type": "measurement"
        },
        "master_measurement": {
          "description": "master measurement protocol",
          "filename": "",
          "id": "master_measurement",
          "parentID": "",
          "type": "measurement"
        }
      }
    }




