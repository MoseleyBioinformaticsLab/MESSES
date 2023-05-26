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
