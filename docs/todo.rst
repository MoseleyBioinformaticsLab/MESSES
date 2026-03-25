TODO List
=========


.. todolist::


Possible Improvements to MESSES
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Support the ISA-Tab format.

If the user says to read from stdin but does not supply a file, then it will run indefinitely. This is 
normal behavior for that situation in other programs, but we could add a timeout on waiting.


Possible Improvements to Extract
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Make it so the automation tags to add are ran through the parser before being exported to check for errors. If tags to add were validated 
as valid tags before being applied you might catch an error earlier and make it easier for the user to understand that the problem is in 
the automation and not in the export.

Either expand export tags to be able to pull in tables without an id for each record, or enumerate based on a base id name. Somehow enable the 
tags to let id be a base name and then increment a number at the end of the base name for each record. Simply allowing a table without ids 
might be better though. The result would be a list of dictionaries instead of a dictionary of dictionaries. This goes against best practice 
for SQL like tables, but it is possible to create SQL tables that have a 'rowid' or 'index' as the primary key.

Check to see if a record's id is already in use while parsing, and print warning to user that 2 records in Excel have same id. Currently if 
this happens fields are just updated with no warning. There are legitimate reasons to do this, so would warnings would be useful or mostly 
ignored? This is also complicated by the fact that child tags can add placeholder parents that will be updated later. The bottom of 
TagParser._parseRow is where this warning would go.

Allow input files to be URLs and fetch them from the internet.

Handle column based data. Most likely this will be a tag directly after #tags that indicates the data is in column format and it will be 
transposed and then processed as normal.

Add a #max-distance tag for levenshtein comparison to put a minimum distance that must be acheived to be considered a match.

Add an option not to print warnings about unused modification directives.

Add a "exact_assign" tag to modification tags that keeps the field type (list vs non list).

Add an option to not sort JSON output keys.

Add a way to filter the tables and records. This could probably be done with modification tags.


Possible Improvements to Validate
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Improve build_PD_schema function by supporting more JSON Schema keywords. dependentRequired could be done the same as required, 
but with a list value instead of boolean.

Have an option to check that fields with the same name in the same table have the same type.

Add an option similar to the --delete option for extract that would filter before validation, --exclude possibly. This would give the 
user more options to remove nuisance messages.


Possible Improvements to Convert
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Make it so save-directives can output to stdout if user supplies "-" for filename.

For matrix directives add an option so that fields in "headers" don't have to be in the records.



Add explanation in documentation that tags are read from left to right, so some things must be specified first. 
For example, a child tag must have it's parent ID specified on the left before it.

Do we want to force child tags to specify child.id always? 
This example:
#tags	#sample.id	#%child.id;#.field1=asdf	#%child.id;#.field1=qwer
	sample1	-child1	-child2

will create children with IDs "-child1" and "-child2" without having the parent ID prepended. There is not an example like this 
in the documentation though. If we want this to be an option, then we should add an example like this.

Currently, you can make child records that are in a different table from the parent. I think this is a relic from when 
we had subject and sample tables instead of an entity table with a required field for subject or sample. Double check with Hunter and fix.
Add to documentation that children must be in the same table, same with crecords.

For automation, check whether reordering occurs to match the order specified in automation, if not ask Hunter if we want it to.


Make sure modify tests still work and add tests that modify "id" list fields and list field attributes. 
For example, #tags	#entity.field1.value	*#entity.protocol.id.assign    and   #tags	#entity.field1.value	*#entity.field%attribute.assign
The modify tags were not working for id fields and field attributes if they were lists. This seemed to be intentional in the code, but 
it does not follow what is now allowed and required. You could construct list fields for ids and attributes when exporting, but for some 
reason can't assign, prepend, etc. Doesn't make sense. Changed the modifications so they can, add tests accordingly.

Add documentation for copy, filter, sort. 

Add MSI level description explanation to the documentation somewhere.

Add a feature to make replicates. Something like REPLICATES(column1, column2, ...) The idea is to tell the program which 
columns to filter down to, and then count the duplicates basically. df.groupby([column1, column2], dropna=False).cumcount() + 1

Add a feature to modification tags to pull values from other records. 
For instance, change the entity.id field in a measurement record by matching to a field in the entity records.
See the West Coast data for this example.

Finish adding example for crecord at the bottom of tagging documentation.

Look in the tagging documentation and see if it is said anywhere that you can use previously defined field values when building 
new values for new tags. Ex:
#tags	#entity.id	#.assignment	#.field1=#.assignment+"zxcv"
	A	asdf	
#.assignment is used in #.field.

Update the #INCREMENT# example in tagging.rst. It doesn't work that way anymore.

Add feature to create pooled smaples. Would look like child.id or crecord.id, but would create a record with parents for every row in the table.

Add non_biological type to entity table and propogate to validations. Make sure to document this new type well.

Check what documentation says about lineages for mwtab. Add to or change documentation to explain how lineages work now.
A level is computed based on the length of ancestors in an entities tree. Entities at the same level have thier ID and 
fields put into the same list for this level, so all entities at the same level are expected to have the same fields. 
If some reason entities at the same level don't have the same fields, then the lists won't line up. For now, only ID 
is used by default, so this isn't a problem when using default values. The lower the lineage level number, the higher 
it is in the inheritance tree. So 0 would be the original subject.

Recompute and update the mwtab examples.

Change factor warning slightly:
Warning: The following samples do not have the full set of factors:
Blank_1
Pool_2
Pool_1
Pool_3
Blank_2
Blank_3
Add exception for pool and blanks.
