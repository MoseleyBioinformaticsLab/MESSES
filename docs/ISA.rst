ISA and MESSES
==============
Investigation/Study/Assay (ISA) is a format developed as a general purpose framework to 
collect and communicate complex metadata. It is a format utilized by several repositories 
for data submission. This page will try to describe some of the details of the JSON version 
of the format and some of the issues in converting from the MESSES Experiment Description 
Specification (EDS) to ISA-JSON.


ISA-JSON Description
~~~~~~~~~~~~~~~~~~~~

.. thumbnail:: isa_model_1_ccoded.png
    :show_caption: True
    :title:

    Visual representation of the ISA Abstract Model provided by them. 
    https://isa-specs.readthedocs.io/en/latest/isamodel.html
    

.. thumbnail:: ISA_model.png
    :show_caption: True
    :title:

    Visual representation of the ISA-JSON data model created by us. The blocks are 
    JSON objects with the name of the object at the top and the elements of the object 
    listed underneath. The type of each element is right aligned next to it, and 
    any text in parentheses is additional information about the element, such as 
    if it has a certain format or is limited to certain values. The elements are ordered 
    in the list such that string or number types are first and more complicated 
    elements such as arrays of objects or objects are under the strings. Arrows go from each 
    element to its object representation for elements that are objects or arrays of 
    objects. To reduce the arrow complexity some elements are color coded instead. 
    "comments" and "onotologyAnnotation" are used repeatedly throughout ISA-JSON, so 
    fields that have the same object representation are colored yellow and blue, respectively. 
    "sources", "samples", "dataFiles", and "otherMaterials" also have a complex interplay, 
    so they are grouped together and arrows pointing to the grouping have text specifically 
    describing which objects of the group they are pointing to.
    

* ISA-JSON is very nested in comparison to the MESSES EDS. 
* ISA-JSON prefers to use an array of objects rather than an object of objects, despite having fields for unique IDs in their objects.
* ISA-JSON uses the JSON-LD concept of @id to reference many of its objects, so often an array of objects will just be objects with an @id field pointing to an object defined elsewhere.
   
   * ISA is agnostic on where to define an object and where to reference it or repeat it, so you won't always see a list of @id objects in the same place.
   * This is counter to the MESSES EDS which tries to centralize the locations of things and then provide references to them where needed.
   
* The description of the ISA model given on their website makes more sense when looking at the tabular version.
   
   * They describe graphs and nodes and describe them "following" each other.
   * In the tabular format this makes sense because the columns of data literally need to follow an order of appearance from left to right, but this doesn't translate as well in the JSON because the nodes are siloed away from each other.
   
* There is no measurement data in ISA, only pointers to the data files containing the measurement data.
* Processes that produce a measurement should be in an assay, while other processes go in the study.
   
   * A study is defined by things done on a subject, so if samples become subjects you make a new study I think. 
   * The problem is that you can't output a source, so I'm not sure how you indicate that a sample became a subject.
   
* Going from the examples provided, there can be more samples in a study than in all of its assays.
   
   * It appears that some samples were not assayed in the example study.
   
* ISA samples can't derive from other samples, it has to be a source, or at least the schema is the source schema.
   
   * It is not clear how you show a multiple sample inheritance due to this.
   * Since the minimum in the derivesFrom field is just an @id we can easily put a sample's @id there, but it isn't clear if that is okay.
   * In a processSequence you can easily put samples as inputs and outputs so it is clear there, but it is not clear if that is related to derivesFrom.
   * It might be that you are supposed to collapse the lineage for each sample all the way back to the source, so that derivesFrom is always the source rather than the most recent sample in the lineage.
      
      
* The example has an assay with many process events, but for our metabolomics data at least we usually have the measurement be 1 protocol.
* In assay tab files columns like "Protocol REF" indicate a new process node and so do other columns like <something> Name, that aren't "Sample" or "Source".

   * For example, "MS Assay Name", "Assay Name", "Data Transformation Name", "Normalization Name" are all new process nodes. There do exist some other special cases https://isa-specs.readthedocs.io/en/latest/isatab.html#special-cases.
   * It is not clear whether the <something> Name pattern is an actual pattern or only the specific examples given are okay. Need to test.
      

* Not all processes have to execute a protocol. The tab format has protocol processes and other special processes such as normalization and data transformation specifically for assays that don't have protocols associated with them.
      
      
Objects
-------
:investigation: top level object that mostly corresponds to an EDS project.
:study: object with the bulk of the data, mostly corresponds to an EDS study. processSequence describes only what happened to the subjects/sources.
:publication: object with fields for a publication associated with the investigation and/or study.
:person: object with fields to identify a person that worked on the investigation and/or study.
:ontology source reference: object to identify the source for ontology terms.
:ontology annotation: object to describe an ontology term.
:comment: object to leave a comment about the object housing the comment.
:protocol: object to generally describe a procedure, mostly corresponds to an EDS protocol.
:component: object that is essentially an ontology annotation object with an extra field. Is nested in a protocol, but there are no examples. May be where you describe hardware or software used with the protocol.
:parameter: object that is essentially an ontology annotation object with an extra field. A way to describe protocols fields in more detail, for example, sample_volume.
:process sequence: object to describe the order in which protocols were executed, by whom, the inputs and outputs, etc. Even though it says "sequence", there is not always a next and previous process. Parallel processes are simply added to the list together.
:parameter value: object that is essentially a parameter object but with "unit" and "value" fields added. Nested in process sequence, not protocol.
:assay: object to describe an assay of a study. Like a mini study object. processSequence describes what happened to the samples of the assay.
:source: object to describe a source of a process sequence or study. Mostly corresponds to subjects in the EDS.
:samples: object to describe a sample of a process sequence, study, or assay. Mostly corresponds to samples in the EDS.
:data files: object to describe a data file of a process sequence or assay.
:other material: object to describe all other materials in a process sequence, study, or assay. Must be an extract or labeled extract.
:characteristic: object used to describe characteristics of sources, samples, and other materials. Would be fields in the EDS, but each field can have more description. Pretty much a category object but with "unit" and "value" fields added.
:category: object to describe a category, pretty much just an ontology annotation with a different name.
:factor: object to describe the factors of a study. Mostly corresponds to factors in the EDS.
:factor value: object that is essentially a factor object but with "unit" and "value" fields added. Nested in a sample object.



Problems To Be Solved
~~~~~~~~~~~~~~~~~~~~~
As the EDS and conversion directives are now there are some issues with being able to go from 
the EDS to ISA-JSON. I will try to describe them here and provide possible solutions.

Flattening Data
---------------
Overall most of the problems with converting the EDS to ISA-JSON is an issue of how 
to flatten the ISA content to fit into the EDS. I will illustrate with an example.
The EDS does not have a specific place for the people involved in a project or study. 
There are only fields for PI information in projects and studies. ISA-JSON allows for 
individual people to be described under investigation and study as arrays of people 
objects, and these people objects can have more than 1 layer of nesting. There is also 
a field in process objects called "performer" that is a reference to a person.

This actually illustrates a recurring problem with some other fields as well, and I 
have a couple of possible solutions. The first somewhat obvious solution is to add a 
people table to the MESSES EDS. 

The second solution is to choose a prefix to add to fields 
in study and project that will indicate they are fields for a person. For instance, 
a field like "person1_firstname" would indicate that this is a field for a person's 
firstname and the numerical part would be used to create separate objects for each 
person. One issue with this is that people have more than 1 nesting, so you would need 
multiple prefixes. For instance, a person can have multiple roles, so you would need 
fields named like "person1_role1_termsource". A person's role can have "comments", which 
are an object, so you would also need something like "person1_role1_comment1_value". 
Some other objects have even more levels of nesting, so adding prefixes might be a solution 
that we limit to 1 prefix. It is a good solution for something like the measurementType 
field of an assay since it is a single object and not an array of them. New conversion 
directive behavior would have to be implemented to support this.

Another "solution" would be to simply limit some of the arrays to 1 element. For instance, 
instead of supporting a list of comments we only support being able to have 1 comment so 
that there is only 1 set of fields for the single allowable comment.

Objects that share this issue:
people
publications
ontologyReferences
components
parameters
otherMaterials
characteristics

Hunter suggested something like OBI:0500020:time series design:comment for ontologyAnnotations. 
We can use online resources to turn something like OBI:0500020 into a full ISA ontologyAnnotation.


Subject/Sample
--------------
Sample's can have multiple parents in ISA, but not in the EDS. It would be pretty 
easy to fix this by making parent_id a list field. Subjects are called sources in ISA.


Factors
-------
Factor values are put on samples in ISA, not subjects like in the EDS. We can either require 
factor values to be on samples for ISA specific submissions, or create a custom conversion directive 
that propagates factors through the subject/sample inheritance.


Data Files
----------
Files have to be individual objects in ISA whereas we have them in a list. The conversion 
directives have to be expanded to be able to create multiple objects from a single record. 
Currently, directives are expected to make 1 per table record and changing this will 
be a pretty significant change in the code.


Other Materials
---------------
otherMaterials are used as a generic structure to describe materials consumed or 
produced during an experimental workflow. It is hard to discern exactly what they 
mean though because the "type" field can only be "Extract Name" or "Labeled Extract 
Name". An example name from their example data sets is "labeledextract-NZ_2hrs_Vehicle_Sample_2_Labelled". 
This also has a characteristic label of "biotin". I don't think we have a place 
for something like this in the EDS. Based on where it is in ISA I think they 
would maybe be part of a protocol in the EDS, but it would face the nesting problem 
described above in Flattening Data.



Conversion Directive Improvements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
There are a few improvements to the conversion directives that I think will help 
us deal with some of the problems in converting ISA.


Nested Directives
-----------------
A directive being able to call another one to fill in some values would be helpful. 
The current directives only have the ability to create a dictionary or a matrix with 
no nesting. Nesting directives would allow for creating a nested output. There would 
need to be some changes to accommodate this. 

One is that we need to reserve a syntax for 
specifying a nested directive. I think starting with a forward slash is a good way 
to indicate that you need to go to another directive, but we also need a syntax so 
we know not to compute a nested directive on its own. I think using the percent sign 
like we do for attributes could do this. For example, "/new_table%nested_directive" 
would indicate to go and compute the "new_table%nested_directive" directive to fill 
in the value, and the "%" would indicate when looping over the directives and computing 
them to skip that one because it is nested somewhere else. This sort of combines 
the idea of a JSON Pointer (forward slash) and field attributes.

Another would be that we need to add at least 2 new "value_types" to the directives 
so the return values make sense. "section_matrix" and "section_str" would indicate 
that the entire section or table will be the value of the directive. It is similar 
to the "section" value_type but would return a matrix or string instead of relying 
on computed Python code.

I have included an example below illustrating what a nested directive could look like.


.. code:: console

    "new_table": {
         "new_field": {
             "value_type": "matrix",
             "headers": [
               "\"field1\"=value1",
               "\"field2\"=value2",
               "\"field3\"=/new_table%nested_directive"
             ],
             "table": "factor"
             }
         }
         
    "new_table%nested_directive": {
         "no_id_needed": {
             "value_type": "section_matrix",
             "headers": [
               "\"field4\"=value3",
               "\"field5\"=value4",
               "\"field6\"=value6"
             ],
             "table": "factor"
             }
         }
         

I don't think this would not be too difficult to implement in the code.


Passing Context
---------------
If we allow for nested directives then we are also likely to need to be able to 
pass context from the calling directive. Directives inherently start from the context 
of the entire input JSON and we use keywords like "table", "test", and "record_id" to 
get them to the correct context needed to create the new record(s). If we do nested 
directives then it is likely that the nested directive will need some information 
from the calling directive in order to set up its context correctly. I have 2 ideas 
for ways to do this.

The first is what I am going to call "caret syntax". Basically, when a nested directive 
is called it is going to have access to the fields of the record that called it by 
using the "^" character. Anywhere a field value could be, if "^" is in front then it 
will mean to use the field value of that name from the calling record. In the example 
below the nested directive would use the calling record's "id" field (a study record) to 
filter out factors that don't have that study's id in their "study.id" field.


.. code:: console

        "studies%factors": {
            "no_id_needed": {
                "value_type": "section_matrix",
                "required": "True",
                "test": "study.id=^id",
                "headers": [
                  "\"@id\"=\"#factor/\"id",
                  "\"factorName\"=id",
                  "\"factorType\"=/studies%factor%type",
                  "\"comments\"=/studies%factors%comments"
                ],
                "table": "factor"
                }
            }


The second way I think we can pass context is to allow arguments to be passed with 
nested directives that can be used to fill in values. These could go anywhere, not 
just as field values, and would be replaced with regex substitutions before the 
directive was evaluated. We would need a reserved syntax though. Something like 
"ARG1", "ARG2", etc. to indicate where to replace with the actual values passed in. 
I have an example below.

.. code:: console

    "new_table": {
         "new_field": {
             "value_type": "matrix",
             "headers": [
               "\"field1\"=value1",
               "\"field2\"=value2",
               "\"field3\"=/new_table%nested_directive value3 value4"
             ],
             "table": "factor"
             }
         }
         
    "new_table%nested_directive": {
         "no_id_needed": {
             "value_type": "section_matrix",
             "headers": [
               "\"field4\"=ARG1",
               "\"ARG2\"=value5",
               "\"field6\"=value6"
             ],
             "table": "factor"
             }
         }
         

I don't think either of these would be too difficult to implement in the code.


Concatenate Literal and Field Values
------------------------------------
This is needed for "@id" fields which need to be a unique ID. They have a known 
literal part depending on what object you are making, "#sample/" for instance, and 
a unique part that can be created by combining fields or using a single field. I 
feel like the best way to do this is to copy one of Python's syntaxes. Either allow 
plus signs (+) to indicate concatenation or use f strings. Ex. '"#sample/" + id' or 
'f"sample/{id}"'. The plus sign is probably easier to implement.

I don't think this would be too difficult to implement in the code.


Field Collate
-------------
This may be necessary to handle some of the flattening I mentioned in Flattening Data. 
Basically, we would add a keyword like "field_collate" that would indicate this 
directive is creating multiple new records from the fields of a single old record, 
as opposed to one new record for one old record as is typical. The headers would 
then have to have at least one regex to collate the fields with. An example is below.


.. code:: console

    "new_table":{
        "Data": {
          "required": "True",
          "field_collate": "True",
          "table": "factor",
          "test": "id=^id",
          "headers": [
              "\"name\"=r\"comment(.*)_name\""
              "\"value\"=r\"comment(.*)_value\""
              ],
          "id": "Data",
          "value_type": "matrix"
        }
    }


You can see that the headers have regexes for the values. The group would indicate 
where to look for values to collate by. Let's say a record had fields for "comment1_name" 
and "comment2_name". The regex "comment(.*)_name" would find 2 groups, "1" and "2", to 
collate by and would create a matrix with 2 objects, one for each group. I have illustrated 
below.


.. code:: console

    record_fields =\
    {
      "comment1_name" : "comment 1 name",
      "comment2_name" : "comment 2 name",
      "comment1_value" : "comment 1 value",
      "comment2_value" : "comment 2 value"
    }
      
    output =\
    [
      {
        "name": "comment 1 name",
        "value": "comment 1 value"
      },
      {
        "name": "comment 2 name",
        "value": "comment 2 value"
      }
   ]


This could be generalized to regexes with multiple groups by simply concatenating group 
values together. For instance, a regex like "factor(.*)_comment(.*)_name" would just 
concatenate the factor number and comment number together, and as long as the other 
headers followed the same pattern the groups should match up.

As I mentioned in Flattening Data, this would be a fairly significant endeavor to 
do I believe because of the inherent assumption of one record to one record in 
the original conception of conversion directives.




Tab to JSON Explanation
~~~~~~~~~~~~~~~~~~~~~~~
The ISA group provides some documentation at https://isa-specs.readthedocs.io/en/latest/isatab.html, but 
nowhere do they really lay out how to go from Tab to JSON.


Study Files to JSON Objects
---------------------------
Study columns denote nodes (source, sample, material, data, and process) and attributes to those nodes (characteristics, parameters, or factors). 
The first column must be a source node, and only one source node can be present. Process nodes must work on and produce samples. 
Columns with a pattern like "<something> Name" indicate a new node and the type of node depends on the value of <something>. "Protocol REF" 
also denotes a new process node. A pattern like "<something> File" indicates a new data node.



Given a study file like:

+-------------+------------------------------------------+-----------------+-----------------------+-------------------------+-----------------+-----------------------+----------------------------------------------------------------------------------+-----------------+-----------------------+-----------------+-----------------+---------------------------------+-----------------+-----------------------+--------------------+--------+-----------------+-----------------------+
| Source Name | Characteristics[organism]                | Term Source REF | Term Accession Number | Characteristics[strain] | Term Source REF | Term Accession Number | Characteristics[genotype]                                                        | Term Source REF | Term Accession Number | Protocol REF    | Sample Name     | Factor Value[limiting nutrient] | Term Source REF | Term Accession Number | Factor Value[rate] | Unit   | Term Source REF | Term Accession Number |
+=============+==========================================+=================+=======================+=========================+=================+=======================+==================================================================================+=================+=======================+=================+=================+=================================+=================+=======================+====================+========+=================+=======================+
| culture1    | Saccharomyces cerevisiae (Baker's yeast) | NEWT            |                       | FY1679                  |                 |                       | KanMx4 MATa/MATalpha ura3-52/ura3-52 leu2-1/+trp1-63/+his3-D200/+ hoD KanMx4/hoD |                 |                       | growth protocol | C-0.07-aliquot1 | carbon                          |                 |                       | 0.07               | l/hour |                 |                       |
+-------------+------------------------------------------+-----------------+-----------------------+-------------------------+-----------------+-----------------------+----------------------------------------------------------------------------------+-----------------+-----------------------+-----------------+-----------------+---------------------------------+-----------------+-----------------------+--------------------+--------+-----------------+-----------------------+
| culture1    | Saccharomyces cerevisiae (Baker's yeast) | NEWT            |                       | FY1679                  |                 |                       | KanMx4 MATa/MATalpha ura3-52/ura3-52 leu2-1/+trp1-63/+his3-D200/+ hoD KanMx4/hoD |                 |                       | growth protocol | C-0.07-aliquot2 | carbon                          |                 |                       | 0.07               | l/hour |                 |                       |
+-------------+------------------------------------------+-----------------+-----------------------+-------------------------+-----------------+-----------------------+----------------------------------------------------------------------------------+-----------------+-----------------------+-----------------+-----------------+---------------------------------+-----------------+-----------------------+--------------------+--------+-----------------+-----------------------+
| culture2    | Saccharomyces cerevisiae (Baker's yeast) | NEWT            |                       | FY1679                  |                 |                       | KanMx4 MATa/MATalpha ura3-52/ura3-52 leu2-1/+trp1-63/+his3-D200/+ hoD KanMx4/hoD |                 |                       | growth protocol | C-0.1-aliquot1  | carbon                          |                 |                       | 0.1                | l/hour |                 |                       |
+-------------+------------------------------------------+-----------------+-----------------------+-------------------------+-----------------+-----------------------+----------------------------------------------------------------------------------+-----------------+-----------------------+-----------------+-----------------+---------------------------------+-----------------+-----------------------+--------------------+--------+-----------------+-----------------------+
| culture2    | Saccharomyces cerevisiae (Baker's yeast) | NEWT            |                       | FY1679                  |                 |                       | KanMx4 MATa/MATalpha ura3-52/ura3-52 leu2-1/+trp1-63/+his3-D200/+ hoD KanMx4/hoD |                 |                       | growth protocol | C-0.1-aliquot2  | carbon                          |                 |                       | 0.1                | l/hour |                 |                       |
+-------------+------------------------------------------+-----------------+-----------------------+-------------------------+-----------------+-----------------------+----------------------------------------------------------------------------------+-----------------+-----------------------+-----------------+-----------------+---------------------------------+-----------------+-----------------------+--------------------+--------+-----------------+-----------------------+
| culture3    | Saccharomyces cerevisiae (Baker's yeast) | NEWT            |                       | FY1679                  |                 |                       | KanMx4 MATa/MATalpha ura3-52/ura3-52 leu2-1/+trp1-63/+his3-D200/+ hoD KanMx4/hoD |                 |                       | growth protocol | C-0.2-aliquot1  | carbon                          |                 |                       | 0.2                | l/hour |                 |                       |
+-------------+------------------------------------------+-----------------+-----------------------+-------------------------+-----------------+-----------------------+----------------------------------------------------------------------------------+-----------------+-----------------------+-----------------+-----------------+---------------------------------+-----------------+-----------------------+--------------------+--------+-----------------+-----------------------+
| culture3    | Saccharomyces cerevisiae (Baker's yeast) | NEWT            |                       | FY1679                  |                 |                       | KanMx4 MATa/MATalpha ura3-52/ura3-52 leu2-1/+trp1-63/+his3-D200/+ hoD KanMx4/hoD |                 |                       | growth protocol | C-0.2-aliquot2  | carbon                          |                 |                       | 0.2                | l/hour |                 |                       |
+-------------+------------------------------------------+-----------------+-----------------------+-------------------------+-----------------+-----------------------+----------------------------------------------------------------------------------+-----------------+-----------------------+-----------------+-----------------+---------------------------------+-----------------+-----------------------+--------------------+--------+-----------------+-----------------------+
| culture4    | Saccharomyces cerevisiae (Baker's yeast) | NEWT            |                       | FY1679                  |                 |                       | KanMx4 MATa/MATalpha ura3-52/ura3-52 leu2-1/+trp1-63/+his3-D200/+ hoD KanMx4/hoD |                 |                       | growth protocol | N-0.07-aliquot1 | nitrogen                        |                 |                       | 0.07               | l/hour |                 |                       |
+-------------+------------------------------------------+-----------------+-----------------------+-------------------------+-----------------+-----------------------+----------------------------------------------------------------------------------+-----------------+-----------------------+-----------------+-----------------+---------------------------------+-----------------+-----------------------+--------------------+--------+-----------------+-----------------------+
| culture4    | Saccharomyces cerevisiae (Baker's yeast) | NEWT            |                       | FY1679                  |                 |                       | KanMx4 MATa/MATalpha ura3-52/ura3-52 leu2-1/+trp1-63/+his3-D200/+ hoD KanMx4/hoD |                 |                       | growth protocol | N-0.07-aliquot2 | nitrogen                        |                 |                       | 0.07               | l/hour |                 |                       |
+-------------+------------------------------------------+-----------------+-----------------------+-------------------------+-----------------+-----------------------+----------------------------------------------------------------------------------+-----------------+-----------------------+-----------------+-----------------+---------------------------------+-----------------+-----------------------+--------------------+--------+-----------------+-----------------------+
| culture5    | Saccharomyces cerevisiae (Baker's yeast) | NEWT            |                       | FY1679                  |                 |                       | KanMx4 MATa/MATalpha ura3-52/ura3-52 leu2-1/+trp1-63/+his3-D200/+ hoD KanMx4/hoD |                 |                       | growth protocol | N-0.1-aliquot1  | nitrogen                        |                 |                       | 0.1                | l/hour |                 |                       |
+-------------+------------------------------------------+-----------------+-----------------------+-------------------------+-----------------+-----------------------+----------------------------------------------------------------------------------+-----------------+-----------------------+-----------------+-----------------+---------------------------------+-----------------+-----------------------+--------------------+--------+-----------------+-----------------------+
| culture5    | Saccharomyces cerevisiae (Baker's yeast) | NEWT            |                       | FY1679                  |                 |                       | KanMx4 MATa/MATalpha ura3-52/ura3-52 leu2-1/+trp1-63/+his3-D200/+ hoD KanMx4/hoD |                 |                       | growth protocol | N-0.1-aliquot2  | nitrogen                        |                 |                       | 0.1                | l/hour |                 |                       |
+-------------+------------------------------------------+-----------------+-----------------------+-------------------------+-----------------+-----------------------+----------------------------------------------------------------------------------+-----------------+-----------------------+-----------------+-----------------+---------------------------------+-----------------+-----------------------+--------------------+--------+-----------------+-----------------------+
| culture6    | Saccharomyces cerevisiae (Baker's yeast) | NEWT            |                       | FY1679                  |                 |                       | KanMx4 MATa/MATalpha ura3-52/ura3-52 leu2-1/+trp1-63/+his3-D200/+ hoD KanMx4/hoD |                 |                       | growth protocol | N-0.2-aliquot1  | nitrogen                        |                 |                       | 0.2                | l/hour |                 |                       |
+-------------+------------------------------------------+-----------------+-----------------------+-------------------------+-----------------+-----------------------+----------------------------------------------------------------------------------+-----------------+-----------------------+-----------------+-----------------+---------------------------------+-----------------+-----------------------+--------------------+--------+-----------------+-----------------------+
| culture6    | Saccharomyces cerevisiae (Baker's yeast) | NEWT            |                       | FY1679                  |                 |                       | KanMx4 MATa/MATalpha ura3-52/ura3-52 leu2-1/+trp1-63/+his3-D200/+ hoD KanMx4/hoD |                 |                       | growth protocol | N-0.2-aliquot2  | nitrogen                        |                 |                       | 0.2                | l/hour |                 |                       |
+-------------+------------------------------------------+-----------------+-----------------------+-------------------------+-----------------+-----------------------+----------------------------------------------------------------------------------+-----------------+-----------------------+-----------------+-----------------+---------------------------------+-----------------+-----------------------+--------------------+--------+-----------------+-----------------------+
| culture7    | Saccharomyces cerevisiae (Baker's yeast) | NEWT            |                       | FY1679                  |                 |                       | KanMx4 MATa/MATalpha ura3-52/ura3-52 leu2-1/+trp1-63/+his3-D200/+ hoD KanMx4/hoD |                 |                       | growth protocol | P-0.07-aliquot1 | phosphorus                      |                 |                       | 0.07               | l/hour |                 |                       |
+-------------+------------------------------------------+-----------------+-----------------------+-------------------------+-----------------+-----------------------+----------------------------------------------------------------------------------+-----------------+-----------------------+-----------------+-----------------+---------------------------------+-----------------+-----------------------+--------------------+--------+-----------------+-----------------------+
| culture7    | Saccharomyces cerevisiae (Baker's yeast) | NEWT            |                       | FY1679                  |                 |                       | KanMx4 MATa/MATalpha ura3-52/ura3-52 leu2-1/+trp1-63/+his3-D200/+ hoD KanMx4/hoD |                 |                       | growth protocol | P-0.07-aliquot2 | phosphorus                      |                 |                       | 0.07               | l/hour |                 |                       |
+-------------+------------------------------------------+-----------------+-----------------------+-------------------------+-----------------+-----------------------+----------------------------------------------------------------------------------+-----------------+-----------------------+-----------------+-----------------+---------------------------------+-----------------+-----------------------+--------------------+--------+-----------------+-----------------------+
| culture8    | Saccharomyces cerevisiae (Baker's yeast) | NEWT            |                       | FY1679                  |                 |                       | KanMx4 MATa/MATalpha ura3-52/ura3-52 leu2-1/+trp1-63/+his3-D200/+ hoD KanMx4/hoD |                 |                       | growth protocol | P-0.1-aliquot1  | phosphorus                      |                 |                       | 0.1                | l/hour |                 |                       |
+-------------+------------------------------------------+-----------------+-----------------------+-------------------------+-----------------+-----------------------+----------------------------------------------------------------------------------+-----------------+-----------------------+-----------------+-----------------+---------------------------------+-----------------+-----------------------+--------------------+--------+-----------------+-----------------------+
| culture8    | Saccharomyces cerevisiae (Baker's yeast) | NEWT            |                       | FY1679                  |                 |                       | KanMx4 MATa/MATalpha ura3-52/ura3-52 leu2-1/+trp1-63/+his3-D200/+ hoD KanMx4/hoD |                 |                       | growth protocol | P-0.1-aliquot2  | phosphorus                      |                 |                       | 0.1                | l/hour |                 |                       |
+-------------+------------------------------------------+-----------------+-----------------------+-------------------------+-----------------+-----------------------+----------------------------------------------------------------------------------+-----------------+-----------------------+-----------------+-----------------+---------------------------------+-----------------+-----------------------+--------------------+--------+-----------------+-----------------------+
| culture9    | Saccharomyces cerevisiae (Baker's yeast) | NEWT            |                       | FY1679                  |                 |                       | KanMx4 MATa/MATalpha ura3-52/ura3-52 leu2-1/+trp1-63/+his3-D200/+ hoD KanMx4/hoD |                 |                       | growth protocol | P-0.2-aliquot1  | phosphorus                      |                 |                       | 0.2                | l/hour |                 |                       |
+-------------+------------------------------------------+-----------------+-----------------------+-------------------------+-----------------+-----------------------+----------------------------------------------------------------------------------+-----------------+-----------------------+-----------------+-----------------+---------------------------------+-----------------+-----------------------+--------------------+--------+-----------------+-----------------------+
| culture9    | Saccharomyces cerevisiae (Baker's yeast) | NEWT            |                       | FY1679                  |                 |                       | KanMx4 MATa/MATalpha ura3-52/ura3-52 leu2-1/+trp1-63/+his3-D200/+ hoD KanMx4/hoD |                 |                       | growth protocol | P-0.2-aliquot2  | phosphorus                      |                 |                       | 0.2                | l/hour |                 |                       |
+-------------+------------------------------------------+-----------------+-----------------------+-------------------------+-----------------+-----------------------+----------------------------------------------------------------------------------+-----------------+-----------------------+-----------------+-----------------+---------------------------------+-----------------+-----------------------+--------------------+--------+-----------------+-----------------------+
| culture10   | Saccharomyces cerevisiae (Baker's yeast) | NEWT            |                       | FY1679                  |                 |                       | KanMx4 MATa/MATalpha ura3-52/ura3-52 leu2-1/+trp1-63/+his3-D200/+ hoD KanMx4/hoD |                 |                       | growth protocol | S-0.07-aliquot1 | sulphur                         |                 |                       | 0.07               | l/hour |                 |                       |
+-------------+------------------------------------------+-----------------+-----------------------+-------------------------+-----------------+-----------------------+----------------------------------------------------------------------------------+-----------------+-----------------------+-----------------+-----------------+---------------------------------+-----------------+-----------------------+--------------------+--------+-----------------+-----------------------+
| culture10   | Saccharomyces cerevisiae (Baker's yeast) | NEWT            |                       | FY1679                  |                 |                       | KanMx4 MATa/MATalpha ura3-52/ura3-52 leu2-1/+trp1-63/+his3-D200/+ hoD KanMx4/hoD |                 |                       | growth protocol | S-0.07-aliquot2 | sulphur                         |                 |                       | 0.07               | l/hour |                 |                       |
+-------------+------------------------------------------+-----------------+-----------------------+-------------------------+-----------------+-----------------------+----------------------------------------------------------------------------------+-----------------+-----------------------+-----------------+-----------------+---------------------------------+-----------------+-----------------------+--------------------+--------+-----------------+-----------------------+
| culture11   | Saccharomyces cerevisiae (Baker's yeast) | NEWT            |                       | FY1679                  |                 |                       | KanMx4 MATa/MATalpha ura3-52/ura3-52 leu2-1/+trp1-63/+his3-D200/+ hoD KanMx4/hoD |                 |                       | growth protocol | S-0.1-aliquot1  | sulphur                         |                 |                       | 0.1                | l/hour |                 |                       |
+-------------+------------------------------------------+-----------------+-----------------------+-------------------------+-----------------+-----------------------+----------------------------------------------------------------------------------+-----------------+-----------------------+-----------------+-----------------+---------------------------------+-----------------+-----------------------+--------------------+--------+-----------------+-----------------------+
| culture11   | Saccharomyces cerevisiae (Baker's yeast) | NEWT            |                       | FY1679                  |                 |                       | KanMx4 MATa/MATalpha ura3-52/ura3-52 leu2-1/+trp1-63/+his3-D200/+ hoD KanMx4/hoD |                 |                       | growth protocol | S-0.1-aliquot2  | sulphur                         |                 |                       | 0.1                | l/hour |                 |                       |
+-------------+------------------------------------------+-----------------+-----------------------+-------------------------+-----------------+-----------------------+----------------------------------------------------------------------------------+-----------------+-----------------------+-----------------+-----------------+---------------------------------+-----------------+-----------------------+--------------------+--------+-----------------+-----------------------+
| culture12   | Saccharomyces cerevisiae (Baker's yeast) | NEWT            |                       | FY1679                  |                 |                       | KanMx4 MATa/MATalpha ura3-52/ura3-52 leu2-1/+trp1-63/+his3-D200/+ hoD KanMx4/hoD |                 |                       | growth protocol | S-0.2-aliquot1  | sulphur                         |                 |                       | 0.2                | l/hour |                 |                       |
+-------------+------------------------------------------+-----------------+-----------------------+-------------------------+-----------------+-----------------------+----------------------------------------------------------------------------------+-----------------+-----------------------+-----------------+-----------------+---------------------------------+-----------------+-----------------------+--------------------+--------+-----------------+-----------------------+
| culture12   | Saccharomyces cerevisiae (Baker's yeast) | NEWT            |                       | FY1679                  |                 |                       | KanMx4 MATa/MATalpha ura3-52/ura3-52 leu2-1/+trp1-63/+his3-D200/+ hoD KanMx4/hoD |                 |                       | growth protocol | S-0.2-aliquot2  | sulphur                         |                 |                       | 0.2                | l/hour |                 |                       |
+-------------+------------------------------------------+-----------------+-----------------------+-------------------------+-----------------+-----------------------+----------------------------------------------------------------------------------+-----------------+-----------------------+-----------------+-----------------+---------------------------------+-----------------+-----------------------+--------------------+--------+-----------------+-----------------------+
| culture13   | Saccharomyces cerevisiae (Baker's yeast) | NEWT            |                       | FY1679                  |                 |                       | KanMx4 MATa/MATalpha ura3-52/ura3-52 leu2-1/+trp1-63/+his3-D200/+ hoD KanMx4/hoD |                 |                       | growth protocol | E-0.07-aliquot1 | ethanol                         |                 |                       | 0.07               | l/hour |                 |                       |
+-------------+------------------------------------------+-----------------+-----------------------+-------------------------+-----------------+-----------------------+----------------------------------------------------------------------------------+-----------------+-----------------------+-----------------+-----------------+---------------------------------+-----------------+-----------------------+--------------------+--------+-----------------+-----------------------+
| culture13   | Saccharomyces cerevisiae (Baker's yeast) | NEWT            |                       | FY1679                  |                 |                       | KanMx4 MATa/MATalpha ura3-52/ura3-52 leu2-1/+trp1-63/+his3-D200/+ hoD KanMx4/hoD |                 |                       | growth protocol | E-0.07-aliquot2 | ethanol                         |                 |                       | 0.07               | l/hour |                 |                       |
+-------------+------------------------------------------+-----------------+-----------------------+-------------------------+-----------------+-----------------------+----------------------------------------------------------------------------------+-----------------+-----------------------+-----------------+-----------------+---------------------------------+-----------------+-----------------------+--------------------+--------+-----------------+-----------------------+
| culture14   | Saccharomyces cerevisiae (Baker's yeast) | NEWT            |                       | FY1679                  |                 |                       | KanMx4 MATa/MATalpha ura3-52/ura3-52 leu2-1/+trp1-63/+his3-D200/+ hoD KanMx4/hoD |                 |                       | growth protocol | E-0.1-aliquot1  | ethanol                         |                 |                       | 0.1                | l/hour |                 |                       |
+-------------+------------------------------------------+-----------------+-----------------------+-------------------------+-----------------+-----------------------+----------------------------------------------------------------------------------+-----------------+-----------------------+-----------------+-----------------+---------------------------------+-----------------+-----------------------+--------------------+--------+-----------------+-----------------------+
| culture14   | Saccharomyces cerevisiae (Baker's yeast) | NEWT            |                       | FY1679                  |                 |                       | KanMx4 MATa/MATalpha ura3-52/ura3-52 leu2-1/+trp1-63/+his3-D200/+ hoD KanMx4/hoD |                 |                       | growth protocol | E-0.1-aliquot2  | ethanol                         |                 |                       | 0.1                | l/hour |                 |                       |
+-------------+------------------------------------------+-----------------+-----------------------+-------------------------+-----------------+-----------------------+----------------------------------------------------------------------------------+-----------------+-----------------------+-----------------+-----------------+---------------------------------+-----------------+-----------------------+--------------------+--------+-----------------+-----------------------+
| culture15   | Saccharomyces cerevisiae (Baker's yeast) | NEWT            |                       | FY1679                  |                 |                       | KanMx4 MATa/MATalpha ura3-52/ura3-52 leu2-1/+trp1-63/+his3-D200/+ hoD KanMx4/hoD |                 |                       | growth protocol | E-0.2-aliquot1  | ethanol                         |                 |                       | 0.2                | l/hour |                 |                       |
+-------------+------------------------------------------+-----------------+-----------------------+-------------------------+-----------------+-----------------------+----------------------------------------------------------------------------------+-----------------+-----------------------+-----------------+-----------------+---------------------------------+-----------------+-----------------------+--------------------+--------+-----------------+-----------------------+
| culture15   | Saccharomyces cerevisiae (Baker's yeast) | NEWT            |                       | FY1679                  |                 |                       | KanMx4 MATa/MATalpha ura3-52/ura3-52 leu2-1/+trp1-63/+his3-D200/+ hoD KanMx4/hoD |                 |                       | growth protocol | E-0.2-aliquot2  | ethanol                         |                 |                       | 0.2                | l/hour |                 |                       |
+-------------+------------------------------------------+-----------------+-----------------------+-------------------------+-----------------+-----------------------+----------------------------------------------------------------------------------+-----------------+-----------------------+-----------------+-----------------+---------------------------------+-----------------+-----------------------+--------------------+--------+-----------------+-----------------------+
| culture16   | Saccharomyces cerevisiae (Baker's yeast) | NEWT            |                       | FY1679                  |                 |                       | KanMx4 MATa/MATalpha ura3-52/ura3-52 leu2-1/+trp1-63/+his3-D200/+ hoD KanMx4/hoD |                 |                       | growth protocol | G-0.07-aliquot1 | glucose                         |                 |                       | 0.07               | l/hour |                 |                       |
+-------------+------------------------------------------+-----------------+-----------------------+-------------------------+-----------------+-----------------------+----------------------------------------------------------------------------------+-----------------+-----------------------+-----------------+-----------------+---------------------------------+-----------------+-----------------------+--------------------+--------+-----------------+-----------------------+
| culture16   | Saccharomyces cerevisiae (Baker's yeast) | NEWT            |                       | FY1679                  |                 |                       | KanMx4 MATa/MATalpha ura3-52/ura3-52 leu2-1/+trp1-63/+his3-D200/+ hoD KanMx4/hoD |                 |                       | growth protocol | G-0.07-aliquot2 | glucose                         |                 |                       | 0.07               | l/hour |                 |                       |
+-------------+------------------------------------------+-----------------+-----------------------+-------------------------+-----------------+-----------------------+----------------------------------------------------------------------------------+-----------------+-----------------------+-----------------+-----------------+---------------------------------+-----------------+-----------------------+--------------------+--------+-----------------+-----------------------+
| culture17   | Saccharomyces cerevisiae (Baker's yeast) | NEWT            |                       | FY1679                  |                 |                       | KanMx4 MATa/MATalpha ura3-52/ura3-52 leu2-1/+trp1-63/+his3-D200/+ hoD KanMx4/hoD |                 |                       | growth protocol | G-0.1-aliquot1  | glucose                         |                 |                       | 0.1                | l/hour |                 |                       |
+-------------+------------------------------------------+-----------------+-----------------------+-------------------------+-----------------+-----------------------+----------------------------------------------------------------------------------+-----------------+-----------------------+-----------------+-----------------+---------------------------------+-----------------+-----------------------+--------------------+--------+-----------------+-----------------------+
| culture17   | Saccharomyces cerevisiae (Baker's yeast) | NEWT            |                       | FY1679                  |                 |                       | KanMx4 MATa/MATalpha ura3-52/ura3-52 leu2-1/+trp1-63/+his3-D200/+ hoD KanMx4/hoD |                 |                       | growth protocol | G-0.1-aliquot2  | glucose                         |                 |                       | 0.1                | l/hour |                 |                       |
+-------------+------------------------------------------+-----------------+-----------------------+-------------------------+-----------------+-----------------------+----------------------------------------------------------------------------------+-----------------+-----------------------+-----------------+-----------------+---------------------------------+-----------------+-----------------------+--------------------+--------+-----------------+-----------------------+
| culture18   | Saccharomyces cerevisiae (Baker's yeast) | NEWT            |                       | FY1679                  |                 |                       | KanMx4 MATa/MATalpha ura3-52/ura3-52 leu2-1/+trp1-63/+his3-D200/+ hoD KanMx4/hoD |                 |                       | growth protocol | G-0.2-aliquot1  | glucose                         |                 |                       | 0.2                | l/hour |                 |                       |
+-------------+------------------------------------------+-----------------+-----------------------+-------------------------+-----------------+-----------------------+----------------------------------------------------------------------------------+-----------------+-----------------------+-----------------+-----------------+---------------------------------+-----------------+-----------------------+--------------------+--------+
| culture18   | Saccharomyces cerevisiae (Baker's yeast) | NEWT            |                       | FY1679                  |                 |                       | KanMx4 MATa/MATalpha ura3-52/ura3-52 leu2-1/+trp1-63/+his3-D200/+ hoD KanMx4/hoD |                 |                       | growth protocol | G-0.2-aliquot2  | glucose                         |                 |                       | 0.2                | l/hour |
+-------------+------------------------------------------+-----------------+-----------------------+-------------------------+-----------------+-----------------------+----------------------------------------------------------------------------------+-----------------+-----------------------+-----------------+-----------------+---------------------------------+-----------------+-----------------------+--------------------+--------+





Assay Files to JSON Objects
---------------------------
Assay columns denote nodes (sample, material, data, and process) and attributes to those nodes (characteristics, parameters, or factors). 
The first column must be a sample node, and only one sample node can be present. Process nodes must work on and produce extracts or labeled extracts. 
Columns with a pattern like "<something> Name" indicate a new node and the type of node depends on the value of <something>. "Protocol REF" 
also denotes a new process node. A pattern like "<something> File" indicates a new data node.

Factor values for samples can be specified in study files or assay files, but assay files will take precedent if the different values 
for the same sample are specified in both files.

Characteristics added in assay will be added to the assay's "characteristicCategories" object and not it's parent study.

Parameters are defined in the investigation file, so any parameter values added in the assay must match a parameter defined there.

Samples in the Sample Name column must be in the assay's parent study file.

Protocol names in "Protocol REF" columns must be defined in the investigation file, but values in other process nodes don't.

Process Node Names:
* Protocol REF
* Assay Name
* Data Transformation Name
* Normalization Name
* Other special case names https://isa-specs.readthedocs.io/en/latest/isatab.html#special-cases.

Material Node Names:
* Extract Name
* Labeled Extract Name

Data Node Names:
* Image File
* Raw Data File
* Derived Data File
* Other special case names https://isa-specs.readthedocs.io/en/latest/isatab.html#special-cases.



Given an assay file like:

+-----------------+--------------------+--------------+----------------+----------------------+-------------------+-----------------+-----------------------+---------------+--------------------------+-----------------------------------------+------------------------+--------------------+-------------------------+-------------------------+-------------------------------------------------+--------------------------+--------------------------------+---------------------------------+-----------------+-----------------------+--------------------+------+-----------------+-----------------------+
| Sample Name     | Protocol REF       | Extract Name | Protocol REF   | Labeled Extract Name | Label             | Term Source REF | Term Accession Number | MS Assay Name | Comment[PRIDE Accession] | Comment[PRIDE Processed Data Accession] | Raw Spectral Data File | Normalization Name | Protein Assignment File | Peptide Assignment File | Post Translational Modification Assignment File | Data Transformation Name | Derived Spectral Data File     | Factor Value[limiting nutrient] | Term Source REF | Term Accession Number | Factor Value[rate] | Unit | Term Source REF | Term Accession Number |
+=================+====================+==============+================+======================+===================+=================+=======================+===============+==========================+=========================================+========================+====================+=========================+=========================+=================================================+==========================+================================+=================================+=================+=======================+====================+======+=================+=======================+
| S-0.1-aliquot11 | protein extraction | S-0.1        | ITRAQ labeling | JC_S-0.1             | iTRAQ reagent 117 |                 |                       | 8761          | 8761                     | 8761                                    | spectrum.mzdata        | norm1              | proteins.csv            | peptides.csv            | ptms.csv                                        | datatransformation1      | PRIDE_Exp_Complete_Ac_8761.xml | sulphur                         |                 |                       | 0.1                | l/hr |                 |                       |
+-----------------+--------------------+--------------+----------------+----------------------+-------------------+-----------------+-----------------------+---------------+--------------------------+-----------------------------------------+------------------------+--------------------+-------------------------+-------------------------+-------------------------------------------------+--------------------------+--------------------------------+---------------------------------+-----------------+-----------------------+--------------------+------+-----------------+-----------------------+
| C-0.1-aliquot11 | protein extraction | C-0.1        | ITRAQ labeling | JC_C-0.1             | iTRAQ reagent 116 |                 |                       | 8761          | 8761                     | 8761                                    | spectrum.mzdata        | norm1              | proteins.csv            | peptides.csv            | ptms.csv                                        | datatransformation1      | PRIDE_Exp_Complete_Ac_8761.xml | carbon                          |                 |                       | 0.1                | l/hr |                 |                       |
+-----------------+--------------------+--------------+----------------+----------------------+-------------------+-----------------+-----------------------+---------------+--------------------------+-----------------------------------------+------------------------+--------------------+-------------------------+-------------------------+-------------------------------------------------+--------------------------+--------------------------------+---------------------------------+-----------------+-----------------------+--------------------+------+-----------------+-----------------------+
| N-0.1-aliquot11 | protein extraction | N-0.1        | ITRAQ labeling | JC_N-0.1             | iTRAQ reagent 115 |                 |                       | 8761          | 8761                     | 8761                                    | spectrum.mzdata        | norm1              | proteins.csv            | peptides.csv            | ptms.csv                                        | datatransformation1      | PRIDE_Exp_Complete_Ac_8761.xml | nitrogen                        |                 |                       | 0.1                | l/hr |                 |                       |
+-----------------+--------------------+--------------+----------------+----------------------+-------------------+-----------------+-----------------------+---------------+--------------------------+-----------------------------------------+------------------------+--------------------+-------------------------+-------------------------+-------------------------------------------------+--------------------------+--------------------------------+---------------------------------+-----------------+-----------------------+--------------------+------+-----------------+-----------------------+
| S-0.1-aliquot11 | protein extraction | S-0.1        | ITRAQ labeling | Pool1                | iTRAQ reagent 114 |                 |                       | 8761          | 8761                     | 8761                                    | spectrum.mzdata        | norm1              | proteins.csv            | peptides.csv            | ptms.csv                                        | datatransformation1      | PRIDE_Exp_Complete_Ac_8761.xml |                                 |                 |                       |                    | l/hr |                 |                       |
+-----------------+--------------------+--------------+----------------+----------------------+-------------------+-----------------+-----------------------+---------------+--------------------------+-----------------------------------------+------------------------+--------------------+-------------------------+-------------------------+-------------------------------------------------+--------------------------+--------------------------------+---------------------------------+-----------------+-----------------------+--------------------+------+-----------------+-----------------------+
| C-0.1-aliquot11 | protein extraction | C-0.1        | ITRAQ labeling | Pool1                | iTRAQ reagent 114 |                 |                       | 8761          | 8761                     | 8761                                    | spectrum.mzdata        | norm1              | proteins.csv            | peptides.csv            | ptms.csv                                        | datatransformation1      | PRIDE_Exp_Complete_Ac_8761.xml |                                 |                 |                       |                    | l/hr |                 |                       |
+-----------------+--------------------+--------------+----------------+----------------------+-------------------+-----------------+-----------------------+---------------+--------------------------+-----------------------------------------+------------------------+--------------------+-------------------------+-------------------------+-------------------------------------------------+--------------------------+--------------------------------+---------------------------------+-----------------+-----------------------+--------------------+------+-----------------+-----------------------+
| N-0.1-aliquot11 | protein extraction | N-0.1        | ITRAQ labeling | Pool1                | iTRAQ reagent 114 |                 |                       | 8761          | 8761                     | 8761                                    | spectrum.mzdata        | norm1              | proteins.csv            | peptides.csv            | ptms.csv                                        | datatransformation1      | PRIDE_Exp_Complete_Ac_8761.xml |                                 |                 |                       |                    | l/hr |                 |                       |
+-----------------+--------------------+--------------+----------------+----------------------+-------------------+-----------------+-----------------------+---------------+--------------------------+-----------------------------------------+------------------------+--------------------+-------------------------+-------------------------+-------------------------------------------------+--------------------------+--------------------------------+---------------------------------+-----------------+-----------------------+--------------------+------+-----------------+-----------------------+
| C-0.2-aliquot11 | protein extraction | C-0.2        | ITRAQ labeling | JC_C-0.2             | iTRAQ reagent 117 |                 |                       | 8762          | 8762                     | 8762                                    | spectrum.mzdata        | norm2              | proteins.csv            | peptides.csv            | ptms.csv                                        | datatransformation2      | PRIDE_Exp_Complete_Ac_8762.xml | carbon                          |                 |                       | 0.2                | l/hr |                 |                       |
+-----------------+--------------------+--------------+----------------+----------------------+-------------------+-----------------+-----------------------+---------------+--------------------------+-----------------------------------------+------------------------+--------------------+-------------------------+-------------------------+-------------------------------------------------+--------------------------+--------------------------------+---------------------------------+-----------------+-----------------------+--------------------+------+-----------------+-----------------------+
| N-0.2-aliquot11 | protein extraction | N-0.2        | ITRAQ labeling | JC_N-0.2             | iTRAQ reagent 116 |                 |                       | 8762          | 8762                     | 8762                                    | spectrum.mzdata        | norm2              | proteins.csv            | peptides.csv            | ptms.csv                                        | datatransformation2      | PRIDE_Exp_Complete_Ac_8762.xml | nitrogen                        |                 |                       | 0.2                | l/hr |                 |                       |
+-----------------+--------------------+--------------+----------------+----------------------+-------------------+-----------------+-----------------------+---------------+--------------------------+-----------------------------------------+------------------------+--------------------+-------------------------+-------------------------+-------------------------------------------------+--------------------------+--------------------------------+---------------------------------+-----------------+-----------------------+--------------------+------+-----------------+-----------------------+
| P-0.1-aliquot11 | protein extraction | P-0.1        | ITRAQ labeling | JC_P-0.1             | iTRAQ reagent 115 |                 |                       | 8762          | 8762                     | 8762                                    | spectrum.mzdata        | norm2              | proteins.csv            | peptides.csv            | ptms.csv                                        | datatransformation2      | PRIDE_Exp_Complete_Ac_8762.xml | phosphorus                      |                 |                       | 0.1                | l/hr |                 |                       |
+-----------------+--------------------+--------------+----------------+----------------------+-------------------+-----------------+-----------------------+---------------+--------------------------+-----------------------------------------+------------------------+--------------------+-------------------------+-------------------------+-------------------------------------------------+--------------------------+--------------------------------+---------------------------------+-----------------+-----------------------+--------------------+------+-----------------+-----------------------+
| C-0.2-aliquot11 | protein extraction | C-0.2        | ITRAQ labeling | Pool2                | iTRAQ reagent 114 |                 |                       | 8762          | 8762                     | 8762                                    | spectrum.mzdata        | norm2              | proteins.csv            | peptides.csv            | ptms.csv                                        | datatransformation2      | PRIDE_Exp_Complete_Ac_8762.xml |                                 |                 |                       |                    | l/hr |                 |                       |
+-----------------+--------------------+--------------+----------------+----------------------+-------------------+-----------------+-----------------------+---------------+--------------------------+-----------------------------------------+------------------------+--------------------+-------------------------+-------------------------+-------------------------------------------------+--------------------------+--------------------------------+---------------------------------+-----------------+-----------------------+--------------------+------+-----------------+-----------------------+
| N-0.2-aliquot11 | protein extraction | N-0.2        | ITRAQ labeling | Pool2                | iTRAQ reagent 114 |                 |                       | 8762          | 8762                     | 8762                                    | spectrum.mzdata        | norm2              | proteins.csv            | peptides.csv            | ptms.csv                                        | datatransformation2      | PRIDE_Exp_Complete_Ac_8762.xml |                                 |                 |                       |                    | l/hr |                 |                       |
+-----------------+--------------------+--------------+----------------+----------------------+-------------------+-----------------+-----------------------+---------------+--------------------------+-----------------------------------------+------------------------+--------------------+-------------------------+-------------------------+-------------------------------------------------+--------------------------+--------------------------------+---------------------------------+-----------------+-----------------------+--------------------+------+-----------------+-----------------------+
| P-0.1-aliquot11 | protein extraction | P-0.1        | ITRAQ labeling | Pool2                | iTRAQ reagent 114 |                 |                       | 8762          | 8762                     | 8762                                    | spectrum.mzdata        | norm2              | proteins.csv            | peptides.csv            | ptms.csv                                        | datatransformation2      | PRIDE_Exp_Complete_Ac_8762.xml |                                 |                 |                       |                    | l/hr |                 |                       |
+-----------------+--------------------+--------------+----------------+----------------------+-------------------+-----------------+-----------------------+---------------+--------------------------+-----------------------------------------+------------------------+--------------------+-------------------------+-------------------------+-------------------------------------------------+--------------------------+--------------------------------+---------------------------------+-----------------+-----------------------+--------------------+------+-----------------+-----------------------+
| P-0.2-aliquot11 | protein extraction | P-0.2        | ITRAQ labeling | JC_P-0.2             | iTRAQ reagent 116 |                 |                       | 8763          | 8763                     | 8763                                    | spectrum.mzdata        | norm3              | proteins.csv            | peptides.csv            | ptms.csv                                        | datatransformation3      | PRIDE_Exp_Complete_Ac_8763.xml | phosphorus                      |                 |                       | 0.2                | l/hr |                 |                       |
+-----------------+--------------------+--------------+----------------+----------------------+-------------------+-----------------+-----------------------+---------------+--------------------------+-----------------------------------------+------------------------+--------------------+-------------------------+-------------------------+-------------------------------------------------+--------------------------+--------------------------------+---------------------------------+-----------------+-----------------------+--------------------+------+-----------------+-----------------------+
| S-0.2-aliquot11 | protein extraction | S-0.2        | ITRAQ labeling | JC_S-0.2             | iTRAQ reagent 115 |                 |                       | 8763          | 8763                     | 8763                                    | spectrum.mzdata        | norm3              | proteins.csv            | peptides.csv            | ptms.csv                                        | datatransformation3      | PRIDE_Exp_Complete_Ac_8763.xml | sulphur                         |                 |                       | 0.2                | l/hr |                 |                       |
+-----------------+--------------------+--------------+----------------+----------------------+-------------------+-----------------+-----------------------+---------------+--------------------------+-----------------------------------------+------------------------+--------------------+-------------------------+-------------------------+-------------------------------------------------+--------------------------+--------------------------------+---------------------------------+-----------------+-----------------------+--------------------+------+-----------------+-----------------------+
| P-0.2-aliquot11 | protein extraction | P-0.2        | ITRAQ labeling | Pool3                | iTRAQ reagent 117 |                 |                       | 8763          | 8763                     | 8763                                    | spectrum.mzdata        | norm3              | proteins.csv            | peptides.csv            | ptms.csv                                        | datatransformation3      | PRIDE_Exp_Complete_Ac_8763.xml |                                 |                 |                       |                    | l/hr |                 |                       |
+-----------------+--------------------+--------------+----------------+----------------------+-------------------+-----------------+-----------------------+---------------+--------------------------+-----------------------------------------+------------------------+--------------------+-------------------------+-------------------------+-------------------------------------------------+--------------------------+--------------------------------+---------------------------------+-----------------+-----------------------+--------------------+------+-----------------+-----------------------+
| S-0.2-aliquot11 | protein extraction | S-0.2        | ITRAQ labeling | Pool3                | iTRAQ reagent 117 |                 |                       | 8763          | 8763                     | 8763                                    | spectrum.mzdata        | norm3              | proteins.csv            | peptides.csv            | ptms.csv                                        | datatransformation3      | PRIDE_Exp_Complete_Ac_8763.xml |                                 |                 |                       |                    | l/hr |                 |                       |
+-----------------+--------------------+--------------+----------------+----------------------+-------------------+-----------------+-----------------------+---------------+--------------------------+-----------------------------------------+------------------------+--------------------+-------------------------+-------------------------+-------------------------------------------------+--------------------------+--------------------------------+---------------------------------+-----------------+-----------------------+--------------------+------+-----------------+-----------------------+
| P-0.2-aliquot11 | protein extraction | P-0.2        | ITRAQ labeling | Pool3                | iTRAQ reagent 114 |                 |                       | 8763          | 8763                     | 8763                                    | spectrum.mzdata        | norm3              | proteins.csv            | peptides.csv            | ptms.csv                                        | datatransformation3      | PRIDE_Exp_Complete_Ac_8763.xml |                                 |                 |                       |                    | l/hr |                 |                       |
+-----------------+--------------------+--------------+----------------+----------------------+-------------------+-----------------+-----------------------+---------------+--------------------------+-----------------------------------------+------------------------+--------------------+-------------------------+-------------------------+-------------------------------------------------+--------------------------+--------------------------------+---------------------------------+-----------------+-----------------------+--------------------+------+
| S-0.2-aliquot11 | protein extraction | S-0.2        | ITRAQ labeling | Pool3                | iTRAQ reagent 114 |                 |                       | 8763          | 8763                     | 8763                                    | spectrum.mzdata        | norm3              | proteins.csv            | peptides.csv            | ptms.csv                                        | datatransformation3      | PRIDE_Exp_Complete_Ac_8763.xml |                                 |                 |                       |                    | l/hr |
+-----------------+--------------------+--------------+----------------+----------------------+-------------------+-----------------+-----------------------+---------------+--------------------------+-----------------------------------------+------------------------+--------------------+-------------------------+-------------------------+-------------------------------------------------+--------------------------+--------------------------------+---------------------------------+-----------------+-----------------------+--------------------+------+


The first column will not create any new sample objects since they are defined in the assay's 
parent study. Techinically, new sample "objects" will be added to the assay, but they are simple 
objects with only the "@id" fields of the samples filled in. They are more like a pointer or 
reference to the sample objects located in the parent study object. This list of sample object 
references will be added to the assay object in it's ["materials"]["samples"] property. Note 
that a reference is added for each unique sample in the column. An example "samples" property 
is shown below.

.. code:: console

    [{'@id': '#sample/sample-S-0.1-aliquot11'},
     {'@id': '#sample/sample-N-0.1-aliquot11'},
     {'@id': '#sample/sample-C-0.1-aliquot11'},
     {'@id': '#sample/sample-P-0.2-aliquot11'},
     {'@id': '#sample/sample-N-0.2-aliquot11'},
     {'@id': '#sample/sample-P-0.1-aliquot11'},
     {'@id': '#sample/sample-C-0.2-aliquot11'},
     {'@id': '#sample/sample-S-0.2-aliquot11'}]


The second column is a process node, so process objects will be created and added to the assay's 
"processSequence" property. How process objects are created depends on the nodes on either side 
of the process column. A process object will be created for each unique row of the column itself 
and the material node on the left. For example this column will create 8 process objects because 
the sample names and extract names repeat several times ("S-0.1-aliquot11" is repeated twice for 
example). The materials of the material node on the left side of the process column are added to the process object's 
"inputs" property, but similar to the sample column they are simply added as a list of references. 
Similarly, the materials of the material node on the right side of the process column are added to 
the process object's "outputs" property. A reference object to the protocol indicated in the column 
is added to the process object's "executesProtocol" property. If there is another process node 
to the right of this process then a reference object to it will be added to the process object's 
"nextProcess" property. Similarly, a process node to the left of this process will be added to the 
process object's "previousProcess" property. An example process object from this column is shown below.

.. code:: console

    {
      "@id": "#process/protein_extraction2",
      "comments": [],
      "date": "",
      "executesProtocol": {
        "@id": "#protocol/protein_extraction"
      },
      "inputs": [
        {
          "@id": "#sample/sample-C-0.1-aliquot11"
        }
      ],
      "nextProcess": {
        "@id": "#process/ITRAQ_labeling2"
      },
      "outputs": [
        {
          "@id": "#material/extract-C-0.1"
        }
      ],
      "parameterValues": [],
      "performer": ""
    }

Note that the "comments", "date", "parameterValues", and "performer" properties are empty. 
These can be filled in as needed using additional columns. It is also valid for a process 
object not to have these properties at all instead of leaving them empty.


The third column is a material node, and each unique material will be added to the assay's 
["material"]["otherMaterials"] property. An example is shown below.

.. code:: console

    {
        "@id": "#material/extract-S-0.1",
        "characteristics": [],
        "name": "extract-S-0.1",
        "type": "Extract Name"
    }

Characteristics can be added to the material using additional characteristic columns.


The fourth column is another protocol process column and process objects are created in 
the same way as previously described for the second column. An example process object 
for this column is shown below.

.. code:: console

    {
      "@id": "#process/ITRAQ_labeling4",
      "comments": [],
      "date": "",
      "executesProtocol": {
        "@id": "#protocol/ITRAQ_labeling"
      },
      "inputs": [
        {
          "@id": "#material/extract-C-0.2"
        }
      ],
      "nextProcess": {
        "@id": "#process/8762"
      },
      "outputs": [
        {
          "@id": "#material/labeledextract-JC_C-0.2"
        },
        {
          "@id": "#material/labeledextract-Pool2"
        }
      ],
      "parameterValues": [],
      "performer": "",
      "previousProcess": {
        "@id": "#process/protein_extraction4"
      }
    }


The fifth column is another material node similar to the third column, but this material 
node is a little special. It is a labeled node and has a "Label" column to the right of 
it describing the labels of each material. This is a special column in the ISA-Tab format, 
but in the ISA-JSON format the label simply becomes another characteristic like any other. 
An example of a material object created from this column is shown below.

.. code:: console

    {
      "@id": "#material/labeledextract-JC_N-0.1",
      "characteristics": [
        {
          "category": {
            "@id": "#characteristic_category/Label"
          },
          "value": {
            "annotationValue": "iTRAQ reagent 115",
            "termAccession": "",
            "termSource": ""
          }
        }
      ],
      "name": "labeledextract-JC_N-0.1",
      "type": "Labeled Extract Name"
    }


The sixth column as previously described is a special characteristic type column that 
will add a "Label" characteristic to the assay object's "characteristicCategories" 
property. An example is shown below.

.. code:: console

    {
      "@id": "#characteristic_category/Label",
      "characteristicType": {
        "annotationValue": "Label",
        "termAccession": "",
        "termSource": ""
      }
    }
   

The seventh and eighth columns are there so that the label characteristic could become 
an ontology annotation if desired, but they are empty. They could be removed entirely.

The ninth column is another process node, but is a special case name "MS Assay Name". 
It functionas the same as if it was named "Assay Name". This type of process node 
functions similarly to a protocol process node, but there are a few differences. One 
difference is that there is not a protocol associated with the process. Instead of the 
value in the column going into the process object's "executesProtocol" property it 
goes in the "name" property. The isatools converter will also create an "uknown" protocol 
to put in the "executesProtocol" property, but this property could simply be left out. 
Another difference is that the number of process objects created depends entirely on the 
unique names in the columns and not on the inputs like in a protocol process node.
An example process object from this node is shown below.

.. code:: console

    {
      "@id": "#process/8761",
      "comments": [
        {
          "name": "PRIDE Accession",
          "value": "8761"
        },
        {
          "name": "PRIDE Processed Data Accession",
          "value": "8761"
        }
      ],
      "date": "",
      "executesProtocol": {
        "@id": "#protocol/unknown"
      },
      "inputs": [
        {
          "@id": "#material/labeledextract-JC_S-0.1"
        },
        {
          "@id": "#material/labeledextract-JC_C-0.1"
        },
        {
          "@id": "#material/labeledextract-JC_N-0.1"
        },
        {
          "@id": "#material/labeledextract-Pool1"
        }
      ],
      "name": "8761",
      "nextProcess": {
        "@id": "#process/norm1"
      },
      "outputs": [
        {
          "@id": "#data/rawspectraldatafile-spectrum.mzdata"
        }
      ],
      "parameterValues": [],
      "performer": "",
      "previousProcess": {
        "@id": "#process/ITRAQ_labeling3"
      }
    }


The tenth and eleventh columns are simply comments that are added as such to the process 
node preceding them. 

The twelfth column is a data node. This node creates new data objects that are added 
in the assay object's "dataFiles" property, and are added as reference objects to 
the previous process object's "outputs" property (as seen above). An example object 
is shown below.

.. code:: console

    {
      "@id": "#data/rawspectraldatafile-spectrum.mzdata",
      "name": "spectrum.mzdata",
      "type": "Raw Spectral Data File"
    }


The thirteenth column is another process node, but is a normalization type. This node 
functions the same as the ninth column assay type process node. An example is shown 
below.

.. code:: console

    {
      "@id": "#process/norm1",
      "comments": [],
      "date": "",
      "executesProtocol": {
        "@id": "#protocol/unknown"
      },
      "inputs": [
        {
          "@id": "#data/rawspectraldatafile-spectrum.mzdata"
        }
      ],
      "name": "norm1",
      "nextProcess": {
        "@id": "#process/datatransformation1"
      },
      "outputs": [
        {
          "@id": "#data/proteinassignmentfile-proteins.csv"
        },
        {
          "@id": "#data/posttranslationalmodificationassignmentfile-ptms.csv"
        },
        {
          "@id": "#data/peptideassignmentfile-peptides.csv"
        }
      ],
      "parameterValues": [],
      "performer": "",
      "previousProcess": {
        "@id": "#process/8761"
      }
    }


The fourteenth, fifthteenth, and sixteenth columns are all data nodes that function 
the same as the aforementioned twelfth node. Examples are shown below.

.. code:: console

    {
      "@id": "#data/proteinassignmentfile-proteins.csv",
      "name": "proteins.csv",
      "type": "Protein Assignment File"
    }
    
    {
      "@id": "#data/peptideassignmentfile-peptides.csv",
      "name": "peptides.csv",
      "type": "Peptide Assignment File"
    }
    
    {
      "@id": "#data/posttranslationalmodificationassignmentfile-ptms.csv",
      "name": "ptms.csv",
      "type": "Post Translational Modification Assignment File"
    }


The seventeenth column is another process node, but is a data transformation type. This node 
functions the same as the ninth column assay type process node. An example is shown 
below.

.. code:: console

    {
      "@id": "#process/datatransformation1",
      "comments": [],
      "date": "",
      "executesProtocol": {
        "@id": "#protocol/unknown"
      },
      "inputs": [
        {
          "@id": "#data/proteinassignmentfile-proteins.csv"
        },
        {
          "@id": "#data/posttranslationalmodificationassignmentfile-ptms.csv"
        },
        {
          "@id": "#data/peptideassignmentfile-peptides.csv"
        }
      ],
      "name": "datatransformation1",
      "outputs": [
        {
          "@id": "#data/derivedspectraldatafile-PRIDE_Exp_Complete_Ac_8761.xml"
        }
      ],
      "parameterValues": [],
      "performer": "",
      "previousProcess": {
        "@id": "#process/norm1"
      }
    }


The eighteenth column is a data node that functions the same as the 
aforementioned twelfth node. An example is shown below.

.. code:: console

    {
      "@id": "#data/derivedspectraldatafile-PRIDE_Exp_Complete_Ac_8761.xml",
      "name": "PRIDE_Exp_Complete_Ac_8761.xml",
      "type": "Derived Spectral Data File"
    }


The nineteenth column is a factor value node. These specify factor values for the 
samples listed way over on the first column. Generally you shouldn't see these in 
an assay file as they should be in the study file, but if specified in an assay file 
they will take precedent and overwrite the value that was specified in the study file. 
The node creates a factorValue object that will go in the "factorValues" property of 
the sample. An example is shown below.

.. code:: console

    {
      "category": {
        "@id": "#factor/limiting_nutrient"
      },
      "value": {
        "annotationValue": "phosphorus",
        "termAccession": "",
        "termSource": ""
      }
    }


The twentieth and twenty-first columns are part of the factor value node so it could 
be an ontology annotation if desired and would fill in the "termAcession" and "termSource" 
properties in the example above. 

The twenty-second column is another factor value node and works the same way as the 
aforementioned nineteenth column. An example is shown below.

.. code:: console

    {
      "category": {
        "@id": "#factor/rate"
      },
      "unit": {
        "@id": "#Unit/l/hour"
      },
      "value": 0.1
    }
    

The twenty-third column is a special characteristic node similar to the "Layer" column. 
It will create a reference object to the unit in the factor value object's "unit" property, 
as seen above, and will create a unit object in the assay object's "unitCategories" property. 
This will not be added to the parent study object's "unitCategories" property. The best practice 
is not to add factors in the assay and put them all in the study.
An example unit object is shown below.

.. code:: console

    {
      "@id": "#Unit/l/hour",
      "annotationValue": "l/hour",
      "termAccession": "",
      "termSource": ""
    }
    
The twenty-fourth and twenty-fifth columns are the same as the twentieth and twenty-first columns, 
but for the Unit node. These would fill in the "termAccession" and "termSource" properties 
in the above example.

