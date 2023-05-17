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

