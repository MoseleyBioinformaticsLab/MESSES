Extract CLI
===========

The extract command of MESSES supports turning tabular data into JSON. 
This is done by adding a layer of tags on top of the data. These tags tell 
extract how to construct the JSON tables and records. There are features 
for automatically applying tags to untagged data and features for modifying 
the names and values of data. extract can also be used to modify already 
JSONized data. There is also support for viewing the data in different ways, such 
as viewing the record lineages. For a more detailed explanation of the options 
with examples as to how they might be used see the :doc:`tutorial` page.

Usage
~~~~~

.. literalinclude:: ../src/messes/extract.py
    :start-at: Usage:
    :end-before: """
    :language: none
       









