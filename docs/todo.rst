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


