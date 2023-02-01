Table Schema
============

Terminology
~~~~~~~~~~~
* **record/entry** - collection of data points with a unique identifer organized together. 

   * Example: "sample_01": {"type":"tissue", "weight":"30", "units":"grams"}
   
* **field/attribute/property** - piece of data with a unique identifer associated with a record. 

   * Example: weight for a sample record.



Overview of (Relational) Tables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The data model that was developed for LIMS was designed to capture generalized experimental data in an abstract way. 
   * It is an `entity-attribute-value model <https://en.wikipedia.org/wiki/Entity%E2%80%93attribute%E2%80%93value_model>`__, and almost all experimental data should be able to be comprehensively described using this model.
   * This model has the following tables:
      * entity
      * protocol
      * measurement
      * factor
      * project
      * study
   * Although the tables have been generally described below, there are more details and logic needed to explain the framework.


project
-------
**A project generally describes the hypothesis being tested, or the information being sought.**
   * Generally there is one project per published paper, but a project can cover multiple publications. 
   * It is somewhat arbitrary how to categorize a project, but defining one project per paper is a good start. 

study
-----
**A study is generally one experiment inside of the project.**
   * For instance, if you are testing the effectiveness of a treatment on lung cancer and you try the treatment on both cell lines and mice, the cell line would be one study and the mouse another.

protocol
--------
**A protocol describes an operation or set of operations done on a subject or sample.**
   * For example, if mouse organs are frozen in liquid nitrogen and then ground into powder this could be either 1 protocol to describe both operations or 2 to separate the freezing step and grinding step. 
   * How to break operations up can be an arbitrary decision, but some good rules of thumb are to make operations with significant time between them separate protocols, or if there are measurements associated with an operation. 
   * For example, if the tissue is weighed before and after freezing and before and after grinding it might be a good idea to have the operations in separate protocols so the weights are clearly associated with each operation.

entity
------
**Entities are either subjects or samples which are similar to each other and interconnected.**
   * A subject is something that receives a treatment, or is subjected to different experimental factors. 
      * For example, if you are testing a treatment on a cell line with a line in 6 different dishes (1 treatment with 3 replicates and 1 null with 3 replicates), the line in each dish would be a separate subject. 
   * Samples are collected from subjects. 
      * For example, if we revisit the previous example and assume that media is collected from the lines every so often each media collection would be a separate sample. 
      * Samples can also come from other samples. For example, if you take the media samples from the previous example and then perform several steps before measuring something, such as adding a solvent or some other preparation step then the sample technically becomes a new sample that was derived from the original sample. 
      * Samples can also become subjects if they are subjected to a treatment. 
         * For example, when a cancer sample is extracted from a person and then pieces are implanted in mice for treatment testing the mice are subjects with sample parents. 
      * Determining what is a sample and a subject can be confusing, but largely the key is whether or not the thing in question underwent a treatment or has an experimental factor of interest. 
    
measurement
-----------
**A measurement is typically the results acquired after putting a sample through a sophisticated machine such as a mass spec or NMR, as well as any calculations on these results that is used for analysis.**
   * This is what people will typically think of as data while the information in the other tables would be metadata.

factor
------
**A factor is an experimental factor of the experiment.**
   * For example, if there are different treatments done to cell lines this would be a factor. 
   * Each treatment would be a separate protocol, but the different protocols would be 1 factor. 
   * If an experiment also looks at age, race, gender, etc. then these would each be separate factors.



Additional Rules
~~~~~~~~~~~~~~~~

Table-Specific Rules
--------------------
   * The project, study, and factor tables are straightforward and records will generally have the same fields regardless of the experiment, but records in the subject, sample, measurement, and protocol tables may have different fields depending on the experiment. 
   * The way this model handles that is through the use of inheritance and context. 
   * Records in the subject, sample, and measurement tables have different fields based on the protocol id the record has. 
      * In other words, the records have different fields based on the context of the protocol. 
   * Records in the protocol table have the fields set in the protocol plus the fields of their ancestors.

ID Fields
---------
**Any field for any record that ends in ".id" must be an id to an existing record in that field's table.**
   * For instance, if the field "protocol.id" : "tissue_extraction" is in a sample record then the protocol table must contain a record with the id "tissue_extraction". 
   * Similarly, if a record has the "parentID" field the value must be an existing id in the same table as that record. For example, if "parentID" : "tissue_extraction" is in a record in the protocol table then the protocol table must containe a record with the id "tissue_extraction". 
   * The exception to this rule is the subject and sample tables. Subject records must have a parent in the sample table, and sample records could have a parent in either the subject or sample tables. 

Subject/Sample Inheritance Rules
--------------------------------
   * If a sample comes from a sample it must have a sample_prep type protocol.
   * If a sample comes from a subject it must have a collection type protocol.
   * Subjects should have a treatment type protocol.



Overview of Protocol Types
~~~~~~~~~~~~~~~~~~~~~~~~~~
**There are currently 5 different types of protocols:**
   * treatment
   * collection
   * sample_prep
   * measurement
   * storage
    
treatment
---------
**A treatment protocol is used to describe the experimental factors done to subjects.**
   * For example, if a cell line is given 2 different media solutions to observe the different growth behavior between the 2 then this would be a treatment type protocol. 
   * Each treatment would be a separate protocol that describes the specifics of the solution or other factors.

collection
----------
**A collection protocol is used to describe how samples are collected from subjects.**
   * For example, if media is taken out of a cell culture at various time points this would be a collection protocol. 
   * Details such as the time of collection and the weight or volume of collection may be some of the attributes associated with the protocol.

sample_prep
-----------
**A sample_prep protocol is used to describe operations done to samples.**
   * Typically, these operations would be done or are necessary in preparation for going into a measuring device. 
   * For example, once the cells in a culture are collected they may be spun in a centrifuge or have solvents added to separate out protein, lipids, etc. 
   * These steps would be a sample_prep protocol. 
   * How to organize such operations into protocols can be arbitrary and is left to the discretion of the creator. 
   * Details such as the concentration of solvents, speed of the centrifuge, or weight of the spearated parts may be some attributes associated with the protocol.

measurement
-----------
**A measurement protocol is used to describe operations done on samples to measure features about them.**
   * For example, if a sample is put through a mass spectrometer or into an NMR. 
   * Typically, the results of the measurement will be attributes associated with the protocol. 
   * This is also the protocol type used for any analysis or calculations done on the data generated by instruments such as a mass spec.

storage
-------
**A storage protocol is used to describe where things are stored.**
   * This was created mostly to help keep track of where samples were physically stored in freezers or where measurement data files were located on a share drive.
   * But this protocol should include other storage details like temperature for the physical storage of samples.
