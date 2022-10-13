Tagging
=======

Terminology
~~~~~~~~~~~
* **header** - a descriptive label at the top of a column in a table of data.

    * Example: SampleID
    
* **tag** - used to describe fields in a record of data. They are a semantic descriptive header used to parse a column (field) of data from a table.

    * Example: #measurement.compound
    
* **table** - in this section table can refer to either a table in a data file or a SQL style table in the output. Often there are many small tables in a data file that are combined into a larger one in the extract output.

Introduction
~~~~~~~~~~~~
In order to extract data from arbitrary tables programmatically, some kind of system has to be devised. 
This could be something as simple as requiring a table be on the very first row and for the starting 
row to have column names for every column, but a system such as that would then be fragile. We decided 
to create a more robust system that could handle more complicated data arrangements and reduce the 
verbosity to a minimum. The system that was devised was an extra layer of tags added on top of existing 
tables that tell the extract command how to transform the tabular data into key based record data similar 
to JSON or SQL databases. The specific table schema this system was designed for is covered in the 
:doc:`table_schema` section, but it is general enough that it can be used with most table schema.

This initial system served its function well, but it became clear that more functionality was sorely needed. 
Namely, both a way to add tags programmatically to data and a way to modify record values was needed, so the 
system was expanded to give facilities to both. Ultimately there are 3 parts to the tagging system that are 
distinct from one another but have similar syntax and ideas. The "export" part is the system used to add 
directly on top of existing tabular data. It is the base system that must be used for the extraction to 
work at all. The "automation" part that is used to automate adding "export" tags to tabular data. Based on 
the header values in your data you can use "automation" tags to add the "export" tags automatically. A good 
use case for this is when you have data output by a program in a consistent way. Instead of manually adding 
export tags to the program output each time you can create an "automation" page that will add the "export" 
tags for you. The last part is the "modification" part which is the system used to modify record values. 
It can be used to prepend, append, delete, overwrite, or regex substitute values. An example use case would 
be to update old naming conventions.

Each of the 3 tagging systems has to be in their own sheet or file for the extract command. By default 
export tags are expected to be in a sheet named '#export' if given an Excel file without specifying a sheet 
name. If given a CSV file then it is expected to have export tags. Modification tags are expected to be in 
a sheet named '#modify' by default, but can be specified using the --modify option. The option can be used 
to specify either a different sheet name in the given Excel file, a different Excel file, a different Excel 
file with a different sheet name, a JSON file, or a CSV file. Automation tags are similarly specified, but 
using the --automate option.

Each of the 3 tagging systems are explained below with examples. Examples using them with the extract 
command are in the :doc:`tutorial` section and there are full run examples in the "examples" folder of the 
GitHub_.


Export Tags
~~~~~~~~~~~
* Tag rows are identified by putting **'#tags'** in the left most column of the data file.

    * Typically, there will be nothing underneath of **'#tags'** except **'#ignore'** for rows to ignore.
    * You may need to add a blank column to the left of your data to accomodate this.
    * **'#tags'** always needs to be on the very left most column, even if your table has several blank columns before it starts.
    
* Cells on this row will have tags over the columns to be exported.
* Subsequent non-blank rows are interpreted as data unless the tag **'#ignore'** is used in the left most column.

Basic Example:

+---------+--------------+----------------------+---------------+
| #tags   | #sample.id   | #.weight;#%units="g" | #.protocol.id |
+=========+==============+======================+===============+
| #ignore | Sample ID    | Weight               | Treatment     |
+---------+--------------+----------------------+---------------+
|         | ...          | ...                  | ...           |
+---------+--------------+----------------------+---------------+


Keyword Tags
------------
* **#tags** - identifies tag header rows. Must be in the first column of a row.

   * Additional tag-value pairs in a cell with #tags are applied to all child records in this section, but are ignored for non child records.

* **#ignore** - ignore this row. Must be put in the first column of a row.

   * Use this to ignore additional header explanation rows and unused data records within a block of records.

* **#table** - change the working table to the indicated table name.


Column Field Format
-------------------
* Tags begin with a '#' symbol and identify a specific relational database table, field, and optionally a field-attribute.

   * Format: **#table_name.field_name**
   
      * Example: #sample.dry_weight
      
         * sample - the sample data relational table (workbench worksheet)
         * dry_weight - the field name.
   
   * Format: **#table**
      
      * Example: #sample
         
         * sample - the sample data relational table (workbench worksheet)
   
   * Format: **#.field_name**
      
      * Example: #.dry_weight
         
         * dry_weight - the field name, for the table last identified.
   
   * Format: **#table_name.field_name%attribute_name**
      
      * Example: #sample.dry_weight%units
         
         * sample - the sample data relational table (workbench worksheet)
         
         * dry_weight - the field name.
         
         * units - units attribute for the field.
   
   * Format: **#.field_name%attribute_name**
      
      * Example: #.dry_weight%units
         
         * dry_weight - the field name, for the last table identified.
         
         * units - units attribute for the field.
   
   * Format: **#%attribute_name**
      
      * Example: #%units
         
         * units - units attribute for a field previously identified in a table previously identified.


Value Field Format
------------------
* Values for a tag field can be specified directly using an equal sign "=".
   
   * Format: **#table_name.field_name=field_value**
      
      * Example: #study.title="labeled mouse study 278"
         
         * study - the study table.
         * "labeled mouse study 278" - value for the study title field.
         
   * Note that there is a special case for "id" fields. "id" fields cannot be set with an "=".
   
   * Format: **#table_name.field_name%attribute_name=attribute_value**
      
      * Example: #sample.dry_weight%units=g
         
         * sample - sample table
         * dry_weight - dry_weight field
         * units - attribute for dry weight with a value of "g".

* Multiple tags can be specified in a single cell using a semicolon ";".
   
   * However, only one tag can be left without a direct value for unambiguous interpretation of a column.
   * Format: **#table_name.field_name;#table_name.field_name=field_value;...**
      
      * Example: #sample.dry_weight;#.dry_weight%units=mg
         
         * sample - the sample data table.
         * dry_weight - field for the column interpretation
         * units - field with a direct value of "mg".

* Values can be combined into a single value using a plus sign "+".
   
   * Format: **#table_name.field_name;#table_name.field_name=field_value+field_value**
      
      * Example: #study.title="labeled mouse study 278 "+#.type
         
         * study - the study table.
         * "labeled mouse study 278 " - part of value for the study title field.
         * #.type - part of value of the study title field taken from the study type field.


ID Field Format
---------------
* ID tags indicate an identifier for a record in a table. 
* The ID must uniquely identify a record.
* There must be an ID tag in every tag row.
* Using the same ID in multiple tag rows will add to the existing record.
    
    * Fields with the same name for the same ID across multiple tag rows will automatically become list fields, and new values will be added to the list.
    
* Records can have record IDs from other tables or the same table as fields.
   
    * Format: **#table.id**
      
       * Example: #sample.id
         
          * sample - type of id tag. This often is a table name.
          * id - indicates that this is an id tag.
   
    * Format: **#.id**
      
       * Short format can be used when the table is already specified.


List Field Format
-----------------
* List field tags begin with **'\*#'** (**asterisk followed by the pound sign**) and identify a specific relational database table, field, and optionally a field-attribute that has multiple values.
* They have the same format as normal column field tags.
   
   * Format: ***#table_name.field_name**
      
      * Example: \*#sample.dry_weight
         
         * sample - the sample data relational table (workbench worksheet)
         * dry_weight - the field name.

* Individual values are separated by commas "," both in the column cells or in the column tag value.
   
   * Format: ***#table_name.field_name=field_value,field_value,...**
      
      * Example: \*#study.labeling=13C,15N
         
         * study - the study table.
         * 13C,15N - two values for the study labeling field.

* List field tags can be listed multiple times in a record, with each value(s) appended.


Child Tag Format
----------------
* Child record tags provides a mechanism for indicating parent-child relationships between records in the same table or between tables.
   
   * The child tag indicates the creation of a new record.
   * Subsequent normal tags identify fields in the new child record.
   * A special parentID field is added using the first ID tag indicated in the header row.
   * Format: **#%child.id=id_sub_string**
      
      * The value for id_sub_string will be appended to the ID of the child's parent (parentID) to create the child ID.
      
Example:

+-------+---------------+---------------------------------------------------------+---------------------------------------------------------+
| #tags | #sample.id    | #%child.id=-media-0h;#.dry_weight;#.dry_weight%units=mg | #%child.id=-media-3h;#.dry_weight;#.dry_weight%units=mg |
+-------+---------------+---------------------------------------------------------+---------------------------------------------------------+
|       | KO labelled_1 | 4.2                                                     | 8.5                                                     |
+-------+---------------+---------------------------------------------------------+---------------------------------------------------------+
|       | KO labelled_2 | 4.7                                                     | 9.7                                                     |
+-------+---------------+---------------------------------------------------------+---------------------------------------------------------+
|       | ...           | ...                                                     | ...                                                     |
+-------+---------------+---------------------------------------------------------+---------------------------------------------------------+

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


Field Tracking Tags
-------------------
* Field tracking tags provide a mechanism for copying the latest field value from one table into the records of another.
   
   * The tag indicates which table's records to add to and which field to track from another table.
   * The latest value for the field seen while parsing will be added.
   * Useful for adding project and study ids to records in a document with multiple projects or studies.
   * Format: **#table%track=table.field**
   * Example: **#sample%track=project.id**   
       
       * will add the project.id field to every sample record.
   
   * A list format can also be used:  
       
       * **#table%track=table.field1,table.field2,...**
   
   * Example: **#sample%track=project.id,study.id**
   * Fields can also be untracked after tracking to stop adding the field to records.
   * Format: **#table%untrack=table.field**
   * The list format also works for untrack.
   * If a tracked field is specifically given in a table the given value is used over the tracked value.

Example:
   
+---------+----------------------------------------------+
| #tags   | #sample%track=project.id                     |
+---------+----------------------------------------------+
|         |                                              |
+---------+----------------------------------------------+
| #tags   | #project.id                                  |
+---------+----------------------------------------------+
|         | Project 1                                    |
+---------+----------------------------------------------+
|         |                                              |
+---------+----------------------------------------------+
| #tags   | #sample.id                                   |
+---------+----------------------------------------------+
|         | 01_A0_Spleen_naive_0days_170427_UKy_GCH_rep1 |
+---------+----------------------------------------------+
|         | 02_A1_Spleen_naive_0days_170427_UKy_GCH_rep2 |
+---------+----------------------------------------------+

Output JSON:

.. code:: console

    {
      "project": {
        "Project 1": {
          "id": "Project 1"
        }
      },
      "sample": {
        "01_A0_Spleen_naive_0days_170427_UKy_GCH_rep1": {
          "id": "01_A0_Spleen_naive_0days_170427_UKy_GCH_rep1",
          "project.id": "Project 1",
        },
        "02_A1_Spleen_naive_0days_170427_UKy_GCH_rep2": {
          "id": "02_A1_Spleen_naive_0days_170427_UKy_GCH_rep2",
          "project.id": "Project 1",
        }
      }
    }


Modification Tags
~~~~~~~~~~~~~~~~~
Similar to export tags the modification tag rows are indicated by **#tags** in the left most column, and 
**#ignore** can be used to ignore rows. The general idea behind the modification system is that you 
first indicate a field in a table to match to using tags. Then underneath that tag indicate the value in 
that field to match to. Then another tag in the same row will indicate both what field to modify in the 
record that has the matching field and what modification to do. Underneath that tag will have the value 
to do the modification with. 

Basic Examples:

+---------+---------------------------------------------------------------+------------------------------------------------------+------------+
| #tags   | #measurement.compound.value                                   | #measurement.compound.assign                         | #match=all |
+=========+===============================================================+======================================================+============+
|         | (S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd | (S)-2-Acetolactate Glutaric acid Methylsuccinic acid |            |
+---------+---------------------------------------------------------------+------------------------------------------------------+------------+
|         | ...                                                           | ...                                                  |            |
+---------+---------------------------------------------------------------+------------------------------------------------------+------------+

This example replaces the "compound" field with value "(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd" in "measurement" table records with "(S)-2-Acetolactate Glutaric acid Methylsuccinic acid".

+---------+---------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------+------------+
| #tags   | #measurement.compound.value                                   | #measurement.id.regex                                                                                                      | #match=all |
+=========+===============================================================+============================================================================================================================+============+
|         | (S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd | r'\(S\)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd',r'(S)-2-Acetolactate Glutaric acid Methylsuccinic acid' |            |
+---------+---------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------+------------+
|         | ...                                                           | ...                                                                                                                        |            |
+---------+---------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------+------------+

This example does a regex substitution on the "id" field of records in the "measurement" table if their "compound" field matches "(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd".
In the "id" field "(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd" is substituted with "(S)-2-Acetolactate Glutaric acid Methylsuccinic acid".


Value Tag
---------
* All modification tag rows must start with a value tag after **#tags**. 
* This tag indicates which table and field to compare with. 
* The value underneath the tag will be compared with the value in indicated field for all of the records in the indicated table to determine if a match is made.

    * Signature: 
    
        * **#[table_name].field_name[%attribute].value**


Comparison Type
---------------
The comparison type is controlled through the **#comparison** tag. It can be used to specify the type for 
each row individually, or for the whole column by using the = sign. Ex. **#comparison=exact**

There are 4 comparison types, "exact", "regex", "levenshtein", and "regex|exact". 
    
    * exact is a simple exact comparison between the comparison value and field value. The given comparison value must be exactly what is in the field value (i.e. a "==" comparison).
    * regex expects a regex to be in the comparison value and will print a message if it is not. The given regex will be delivered to re.search() for matching with field values.
    * levenshtein calculates the levenshtein distance between the comparison value and record field values and matches to the field values with the minimum distance. 
       
        * This means it always matches to something even if the values seem wildly different, so be aware of possible unexpected results.
   
    * regex|exact is an intelligent combination of regex and exact. If a regex is specified for the comparison value it will be detected and the type will be regex for that comparison value only, otherwise the comparison type will be exact.
    * If a type is specified then that type is used regardless of the comparison value, so a regex string with an exact comparison type will try to match exactly.
    * If the comparison tag is not specified then the type defaults to "regex|exact".


Match Type
----------
Match behavior can be altered further using the **#match** tag. It can be used to specify the type for 
each row individually, or for the whole column by using the = sign. Ex. **#match=all**

There are 4 match types, "first", "first-nowarn", "unique", and "all".
    
    * "first" - the modification is performed only for the first record matched, additional matches beyond the first will print a warning.
    * "first-nowarn" - the same as first, but won't print warnings.
    * "unique" - the modification is only performed if 1 and only 1 record matched.
   
        * For levenshtein this means that only 1 field value can have the minimum distance, if 2 values share the minimum distance then the action won't take place.
   
    * "all" - the modification is done to every record that matches.
    * If the match tag is not specified then the type defaults to "first".
   

Modifications
-------------
There are 6 modifications that can be done, "assign", "append", "prepend", "regex", "delete", and "rename".

* **assign** - will overwrite whatever value is in the field with the indicated assignment value.

    * Signatures: 
    
        * **#[table_name].field_name[%attribute].assign**
        * ***#[table_name].field_name[%attribute].assign**
    
    * If the indicated assignment field does not exist in the record then it will be added to the record.
    * An eval function can be used in the form "eval(...)".

        * "#field_name#" and "#r'...'#" can be used to construct the assignment value for the record.
        * All Python language operators can be used.  But remember to use "float(#field_name#)" to convert strings to floating point numbers. 
        * Example: eval(float(#intensity#) / float(#normalization#) * 5)
        * evals that return a list of strings will convert the field to a list field.
    
    * Add an asterisk, '*', to the front of the tag to interpret the assignment value as a list and assign that list value to the field.
    
        * An eval function can be used, but it must return a list of strings.
        
    * The assign modification can be used to change list types to non list types and vice versa.
        
        * This can lead to an issue where some records have a list type for the field and some do not.
        * If that is not intended then be sure to construct the assign tag such that it matches the type of the field.
        * For instance make sure evals return a list if the field should be a list type.
        
    Example:
    
    +---------+---------------------------------------------------------------+------------------------------------------------------+
    | #tags   | #measurement.compound.value                                   | #measurement.compound.assign                         |
    +=========+===============================================================+======================================================+
    |         | (S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd | (S)-2-Acetolactate Glutaric acid Methylsuccinic acid | 
    +---------+---------------------------------------------------------------+------------------------------------------------------+
    |         | ...                                                           | ...                                                  |
    +---------+---------------------------------------------------------------+------------------------------------------------------+
     

* **append** - will append the indicated value to the value in the indicated field.

    * Signatures: 
    
        * **#[table_name].field_name[%attribute].append**
        * ***#[table_name].field_name[%attribute].append**
        
    * If the indicated append field does not exist in the record then it will be added to the record.
    * If the field value is a list and the append value is not a list then the append value will be appended to each value in the list.
    * Add an asterisk, '*', to the front of the tag to interpret the append value as a list.
    
        * When the append value is a list the behavior is more complicated.
        * For each value in the field value list the append value in the append list at the same index will be appended to the field value.
        * Examples:
            
            * field_value = ["a", "b"]  append_value = ["c", "d"]  result = ["ac", "bd"]
            * field_value = ["a", "b"]  append_value = ["c", "d", "e"]  result = ["ac", "bd"]
            * field_value = ["a", "b", "e"]  append_value = ["c", "d"]  result = ["ac", "bd", "e"]
    
    Example:
    
    +---------+---------------------------------------------------------------+------------------------------------------------------+
    | #tags   | #measurement.compound.value                                   | #measurement.sample.id.append                        |
    +=========+===============================================================+======================================================+
    |         | (S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd | (S)-2-Acetolactate Glutaric acid Methylsuccinic acid | 
    +---------+---------------------------------------------------------------+------------------------------------------------------+
    |         | ...                                                           | ...                                                  |
    +---------+---------------------------------------------------------------+------------------------------------------------------+
    

* **prepend** - will prepend the indicated value to the value in the indicated field.

    * Signatures: 
    
        * **#[table_name].field_name[%attribute].prepend**
        * ***#[table_name].field_name[%attribute].prepend**
        
    * If the indicated prepend field does not exist in the record then it will be added to the record.
    * If the field value is a list and the prepend value is not a list then the prepend value will be prepended to each value in the list.
    * Add an asterisk, '*', to the front of the tag to interpret the prepend value as a list.
    
        * When the prepend value is a list the behavior is more complicated.
        * For each value in the field value list the prepend value in the prepend list at the same index will be prepended to the field value.
        * Examples:
            
            * field_value = ["a", "b"]  prepend_value = ["c", "d"]  result = ["ca", "db"]
            * field_value = ["a", "b"]  prepend_value = ["c", "d", "e"]  result = ["ca", "db"]
            * field_value = ["a", "b", "e"]  prepend_value = ["c", "d"]  result = ["ca", "db", "e"]
    
    Example:
    
    +---------+---------------------------------------------------------------+------------------------------------------------------+
    | #tags   | #measurement.compound.value                                   | #measurement.sample.id.prepend                       |
    +=========+===============================================================+======================================================+
    |         | (S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd | (S)-2-Acetolactate Glutaric acid Methylsuccinic acid | 
    +---------+---------------------------------------------------------------+------------------------------------------------------+
    |         | ...                                                           | ...                                                  |
    +---------+---------------------------------------------------------------+------------------------------------------------------+
    

* **regex** - will do a regex substitution on the indicated field using the indicated values.

    * Signatures: 
    
        * **#[table_name].field_name[%attribute].regex**
        
    * If the indicated regex field does not exist in the record then a warning will be printed.
    * If the field value is a list then the regex substitution will be done on each element in the list.

    Example:
    
    +---------+---------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------+
    | #tags   | #measurement.compound.value                                   | #measurement.id.regex                                                                                                      |
    +=========+===============================================================+============================================================================================================================+
    |         | (S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd | r'\(S\)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd',r'(S)-2-Acetolactate Glutaric acid Methylsuccinic acid' | 
    +---------+---------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------+
    |         | ...                                                           | ...                                                                                                                        |
    +---------+---------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------------+


* **delete** - will remove the field from the record.

    * Signatures: 
    
        * **#[table_name].field_name[%attribute].delete**
        
    * "id" fields cannot be deleted. An error will be raised during parsing if it is attempted.
    * No value is needed under the tag.

    Example:
    
    +---------+---------------------------------------------------------------+---------------------------------+
    | #tags   | #measurement.compound.value                                   | #measurement.mol_formula.delete |
    +=========+===============================================================+=================================+
    |         | (S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd |                                 | 
    +---------+---------------------------------------------------------------+---------------------------------+
    |         | ...                                                           | ...                             |
    +---------+---------------------------------------------------------------+---------------------------------+
    
    
* **rename** - will remove the field from the record.

    * Signatures: 
    
        * **#[table_name].field_name[%attribute].rename.field_name[%attribute]**
        
    * "id" fields cannot be renamed. An error will be raised during parsing if it is attempted.
    * Fields cannot be renamed to the same name. An error will be raised during parsing if it is attempted.
    * No value is needed under the tag.

    Example:
    
    +---------+---------------------------------------------------------------+---------------------------------------------------+
    | #tags   | #measurement.compound.value                                   | #measurement.mol_formula.rename.molecular_formula |
    +=========+===============================================================+===================================================+
    |         | (S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd |                                                   | 
    +---------+---------------------------------------------------------------+---------------------------------------------------+
    |         | ...                                                           | ...                                               |
    +---------+---------------------------------------------------------------+---------------------------------------------------+


.. note::
    ID fields are special. 
    
    * Modifications to id fields will be propogated to the table key of that record.
    * They cannot be deleted or renamed.
    * They are the only time a period, '.', can appear in the field_name.
    
        * Ex. **#measurement.intensity.units.assign** is malformed, but **#measurement.sample.id.assign** is not.

    
Important Points:

* Tags in the same row must have the same table. An error will be raised during parsing if they don't.
* The value tag must be before the modification tags.
* Modifications are confined to the matched record, it is not possible to modify a record based on another record's fields or values.
* Modifications can be chained together, so that the same field can have multiple modifications.
    
    * This can be utilized effectively, but can also cause hard to diagnose unexpected output.
    * Some warnings are printed when fields are modified twice in a way that doesn't make sense, such as a delete modification after an assign modification, but all other chained modifications are assumed to be intended.


Tag Format Reference:

* **#table_name.field_name[%attribute].value** - identifies table_name containing field_name (with possible attribute name) and associated column with value to match. A regular expression can be given with r'...'.

* **#comparison** - identifies column with type of comparison (exact, regex, levenshtein, regex|exact). Default regex|exact.
* **#comparison=type** - type of comparison (exact, regex, levenshtein, regex|exact).
* **#match** - identifies column with type of match (first, first-nowarn, unique, all). Default first.
* **#match=type** - type of match (first, first-nowarn, unique, all).

* **#[table_name].field_name[%attribute].assign** identifies field to assign and associated column with its value. 
* ***#[table_name].field_name[%attribute].assign** identifies field to assign and that the associated column values are a list type.
* **#[table_name].field_name[%attribute].append** identifies field to append to and associated column with its value.
* ***#[table_name].field_name[%attribute].append** identifies field to append to and that the associated column values are a list type.
* ***#[table_name].field_name[%attribute].prepend** identifies field to prepend to and associated column with its value.
* ***#[table_name].field_name[%attribute].prepend** identifies field to prepend to and that the associated column values are a list type.
* **#[table_name].field_name[%attribute].regex** identifies field to apply regex substitution to and associated column with the pair of regex strings of the form r"...",r"...".
* **#[table_name].field_name[%attribute].delete** identifies field to delete.
* **#[table_name].field_name[%attribute].rename.field_name[%attribute]** identifies field to rename.
      


Automation Tags
~~~~~~~~~~~~~~~
Automation tag rows, like the other tag rows, are indicated by **#tags** in the left most column with
**#ignore** used to ignore rows, but **#insert** and **#end** tags are also introduced. There are 2 
main functions in the automation system. One is to specify a table of header-tag pairs that will be used 
to automatically add the tags associated with the headers underneath of the headers when it finds them 
in the data. The other is to specify a block of rows to add to the data exactly as is. This is what 
introduces the **#insert** and **#end** tags. 


Insert
------
The insertion functionality is easy to understand. You simply write whatever you want to add into the 
data and add **#insert** above it in the left most column and **#end** below it in the left most column. 
Everything in between **#insert** and **#end** is simply added as is into the data before it is parsed 
by the export tagging system. A good use case for this is when you have a standard protocol that always 
needs to be added to some data. Instead of copying it in manually you can add it to an automation 
sheet/file and deliver it to extract so it can add it for you. The thing to be careful of is to make 
sure everything in the insert block is valid under the export tag system. It can be tricky to debug 
a tagging error here because extract won't be able to tell you that the issue is in the insert block.

Example:

+---------+--------------+--------+-----------------+------------+--------------+-------------------+
| #insert |              |        |                 |            |              |                   |
+---------+--------------+--------+-----------------+------------+--------------+-------------------+
| #tags	  | #protocol.id | #.type | #.instrument    | #.ion_mode | #.ionization | #.instrument_type |
+---------+--------------+--------+-----------------+------------+--------------+-------------------+
|         | ICMS1        | MS     | Orbitrap Fusion | NEGATIVE   | ESI          | IC-FTMS           |
+---------+--------------+--------+-----------------+------------+--------------+-------------------+
|         |              |        |                 |            |              |                   |
+---------+--------------+--------+-----------------+------------+--------------+-------------------+
| #end    |              |        |                 |            |              |                   |
+---------+--------------+--------+-----------------+------------+--------------+-------------------+


Header Tagging
--------------
The header tagging allows you to automatically put export tags under a cell in tabular data based on 
the value in the cell. Typically, a table will already have descriptive human readable headers to identify 
what type of data is in the column. These headers are used to match to and put the associated export tags 
under them. Any row that has a header match where export tags are added is automatically ignored with the 
**#ignore** tag. Just like modification tags and export tags **#tags** is used to denote the start of a tag 
block. An entire block is matched as a whole to a row in the data, so if you have multiple tables to add 
tags to you should created multiple tag blocks. There are additional tags to help control how a black is 
matched, detailed below.

Example:
++++++++

Data:

+---------------------------------------------------------------+-------------+-----------+-------------------------------------------------------+-------------+-------------------+
| Compound                                                      | Mol_Formula | C_isomers | SamplID                                               | Intensity   | protein_mg        |
+---------------------------------------------------------------+-------------+-----------+-------------------------------------------------------+-------------+-------------------+
| (S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd | C5H8O4      | 0         | 01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench | 7989221.834 | 0.618176844244679 |
+---------------------------------------------------------------+-------------+-----------+-------------------------------------------------------+-------------+-------------------+
| (S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd | C5H8O4      | 1         | 01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench | 289287.7334 | 0.618176844244679 |
+---------------------------------------------------------------+-------------+-----------+-------------------------------------------------------+-------------+-------------------+

Header Tags:

+-------+---------------------------------------------------+---------------------------------------------------------------------------------------------------------------+
| #tags | #header                                           | #add                                                                                                          |
+-------+---------------------------------------------------+---------------------------------------------------------------------------------------------------------------+
|       | Compound+"-13C"+C_isomers+"-"+SamplID             | #measurement.id                                                                                               |
+-------+---------------------------------------------------+---------------------------------------------------------------------------------------------------------------+
|       | Compound+"-13C"+C_isomers                         | #measurement.assignment                                                                                       |
+-------+---------------------------------------------------+---------------------------------------------------------------------------------------------------------------+
|       | Compound                                          | #measurement.compound                                                                                         |
+-------+---------------------------------------------------+---------------------------------------------------------------------------------------------------------------+
|       | Mol_Formula                                       | #measurement.formula                                                                                          |
+-------+---------------------------------------------------+---------------------------------------------------------------------------------------------------------------+
|       | SamplID                                           | #sample.id                                                                                                    |
+-------+---------------------------------------------------+---------------------------------------------------------------------------------------------------------------+
|       | "13C"+C_isomers                                   | #measurement.isotopologue;#%type="13C"                                                                        |
+-------+---------------------------------------------------+---------------------------------------------------------------------------------------------------------------+ 
|       | Intensity                                         | #measurement.raw_intensity;#%type="spectrometer peak area"                                                    |
+-------+---------------------------------------------------+---------------------------------------------------------------------------------------------------------------+
|       | eval(float(#Intensity#) / float(#protein_mg#))    | #measurement.intensity;#%type="natural abundance corrected and protein normalized peak area";#%units="area/g" |
+-------+---------------------------------------------------+---------------------------------------------------------------------------------------------------------------+
|       |                                                   | #protocol.id=ICMS1                                                                                            |
+-------+---------------------------------------------------+---------------------------------------------------------------------------------------------------------------+

After Automation:

+---------+--------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------------------+---------------------------------------------------------------+----------------------+------------+-------------------------------------------------------+----------------------------------------+------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------+--------------------+
| #ignore |                                                                                                                          |                                                                    | Compound                                                      | Mol_Formula          | C_isomers  | SamplID                                               |                                        | Intensity                                                  |                                                                                                               |                    |
+---------+--------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------------------+---------------------------------------------------------------+----------------------+------------+-------------------------------------------------------+----------------------------------------+------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------+--------------------+
| #tags   | #measurement.id                                                                                                          | #measurement.assignment                                            | #measurement.compound                                         | #measurement.formula |            | #sample.id                                            | #measurement.isotopologue;#%type="13C" | #measurement.raw_intensity;#%type="spectrometer peak area" | #measurement.intensity;#%type="natural abundance corrected and protein normalized peak area";#%units="area/g" | #protocol.id=ICMS1 |
+---------+--------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------------------+---------------------------------------------------------------+----------------------+------------+-------------------------------------------------------+----------------------------------------+------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------+--------------------+
|         | (S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench | (S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0 | (S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd | C5H8O4               | 0          | 01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench | 13C0                                   | 7989221.834                                                | 12923845.19                                                                                                   |                    |
+---------+--------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------------------+---------------------------------------------------------------+----------------------+------------+-------------------------------------------------------+----------------------------------------+------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------+--------------------+
|         | (S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench | (S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1 | (S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd | C5H8O4               | 1          | 01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench | 13C1                                   | 289287.7334                                                | 467969.2165                                                                                                   |                    |
+---------+--------------------------------------------------------------------------------------------------------------------------+--------------------------------------------------------------------+---------------------------------------------------------------+----------------------+------------+-------------------------------------------------------+----------------------------------------+------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------+--------------------+

JSON Output:

.. code:: console

    {
      "measurement": {
        "(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench": {
          "assignment": "(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C0",
          "compound": "(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd",
          "formula": "C5H8O4",
          "id": "(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C0-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench",
          "intensity": "12923845.19",
          "intensity%type": "natural abundance corrected and protein normalized peak area",
          "intensity%units": "area/g",
          "isotopologue": "13C0",
          "isotopologue%type": "13C",
          "protocol.id": "ICMS1",
          "raw_intensity": "7989221.83386388",
          "raw_intensity%type": "spectrometer peak area",
          "sample.id": "01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"
        },
        "(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench": {
          "assignment": "(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd-13C1",
          "compound": "(S)-2-Acetolactate_Glutaric acid_Methylsuccinic acid_MP_NoStd",
          "formula": "C5H8O4",
          "id": "(S)-2-Acetolactate Glutaric acid Methylsuccinic acid-13C1-01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench",
          "intensity": "467969.2165",
          "intensity%type": "natural abundance corrected and protein normalized peak area",
          "intensity%units": "area/g",
          "isotopologue": "13C1",
          "isotopologue%type": "13C",
          "protocol.id": "ICMS1",
          "raw_intensity": "289287.733437356",
          "raw_intensity%type": "spectrometer peak area",
          "sample.id": "01_A0_Colon_T03-2017_naive_170427_UKy_GCB_rep1-quench"
        }
      }
    }


The Tags
++++++++
* **#header** - header value to match to. Can be a regular expression of the form r'...'.  
    
    * All tag blocks must contain a **#header** tag.
    * Additional column headers can be included with blank corresponding tags to help make header row identification unique.
    * Cell contents are stripped of leading and trailing white space before comparison with the header value.
    * A new column will be created if the headers and literals in quotes are combined with plus signs.
       
       * Example: Name+"-"+Isopotologue+"-"+r'^\d+\w+ Isotope$'
       * This functionality means that certain characters can't be used for literal matching outside of a regex.
       * For example if a header name in a data table is "protein+solvent" then you can't simply put protein+solvent under **#header** because it will be interpretted as a concatenation of a "protein" header and a separate "solvent" header.
       * The easist way to solve this issue is to use a regular expression. r'protein\+solvent' will match the header correctly.
       * In general if you are having difficulty matching a header try using a regex.
    
    * An eval function can be used in the form "eval(...)".
       
       * "#header_name#" and "#r'...'#" can be used to indicate specific columns in the row.
       * All Python language operators can be used.  But remember to use "float(#field_name#)" to convert strings to floating point numbers. 
       * Example: eval(float(#Intensity#) / float(#r'.*Normalization'#) * 5)
       * If the eval returns a list of items it is converted into a string separated by semicolons.
       
           * If the corresponding tag is a list tag then this will become a list.


* **#add** - tags to add in an inserted row below the column header row.

    * All tag blocks must contain a **#add** tag.
    * The actual value under **#add** does not have to be a valid tag, the value will be copied as is.
    * Leave this value blank to add headers that are required to match a block, but don't need tags.

         
* **#required** - true|false whether this header description is required. The default is that all header descriptions are required.

    * Example:
    
    +-------+---------------------------------------------------+-------------------------------------+
    | #tags | #header                                           | #add                    | #required |
    +-------+---------------------------------------------------+-------------------------------------+
    |       | Compound+"-13C"+C_isomers+"-"+SamplID             | #measurement.id         | true      |
    +-------+---------------------------------------------------+-------------------------------------+
    |       | Compound+"-13C"+C_isomers                         | #measurement.assignment | true      |
    +-------+---------------------------------------------------+-------------------------------------+
    |       | Compound                                          | #measurement.compound   | true      |
    +-------+---------------------------------------------------+-------------------------------------+
    |       | Mol_Formula                                       | #measurement.formula    | false     |
    +-------+---------------------------------------------------+-------------------------------------+
    |       | SamplID                                           | #sample.id              | true      |
    +-------+---------------------------------------------------+-------------------------------------+
    
    If the Mol_Formula header is not found the tags will still be added, but without the Mol_Formula ones.


* **#exclude=test_string** - test string or regular expression to use for excluding a given header row.

    * If a header matches the exclude string or regex then the tags are not inserted regardless of whether the headers match.
    * Example:
    
    +-------+---------------------------------------------------+---------------------------------------------------------------+
    | #tags | #header                                           | #add                    | #exclude=r'Cell Type|Mouse Species' |
    +-------+---------------------------------------------------+---------------------------------------------------------------+
    |       | Compound+"-13C"+C_isomers+"-"+SamplID             | #measurement.id         |                                     |
    +-------+---------------------------------------------------+---------------------------------------------------------------+
    |       | Compound+"-13C"+C_isomers                         | #measurement.assignment |                                     |
    +-------+---------------------------------------------------+---------------------------------------------------------------+
    |       | Compound                                          | #measurement.compound   |                                     |
    +-------+---------------------------------------------------+---------------------------------------------------------------+
    |       | Mol_Formula                                       | #measurement.formula    |                                     |
    +-------+---------------------------------------------------+---------------------------------------------------------------+
    |       | SamplID                                           | #sample.id              |                                     |
    +-------+---------------------------------------------------+---------------------------------------------------------------+
    
    If the "Cell Type" or "Mouse Species" headers are in the row then don't add the tags.


Insertions can be inside of header tag blocks, so they are inserted only when a match is made to the header rows. 
They function just like when they are on their own, except that there is an additional **#multiple** tag that 
can be used to control whether the insert happens every time the tag block matches or only the first time.

* **#multiple=true** - will insert on every match.
* **#multiple=false* - will only insert on the first match, this is the default behavior if **#multiple** is not specified.





Common Use Case Examples
~~~~~~~~~~~~~~~~~~~~~~~~







.. _GitHub: https://github.com/MoseleyBioinformaticsLab/messes