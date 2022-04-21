#!/usr/bin/python
# jsonCommentRemover.py

"""
Module to remove single line and multiple line comments from JSON

Original JSON.minify () v0.1. function written by Kyle Simpson @ MIT

Defines function for removing specific comment formats within a JSON file.
    - Acceptible Formats:
        Single Line:
            // ...
        or
        Multiple Line:
            /*
            ...
            */
    - Caveats:
        Comments must be within the JSON format and not outside of it, else they will not be removed. 

The JSON file needs to be opened as a string and then passed into the function. 

Example: Code specific to 'exampleJson.json' file included in git commit. 
with open('exampleJson.json') as f: #opens json file and stores it as a string
        content = ''.join(f.readlines())

json_minify(content)
"""

import re

def json_minify(string, strip_space=True):
    """
    PARAMETERS:
        string - JSON string 

    RETURNS:
        JSON string w/o comments
    """
    tokenizer = re.compile('"|(/\*)|(\*/)|(//)|\n|\r')
    end_slashes_re = re.compile(r'(\\)*$')

    in_string = False
    in_multi = False
    in_single = False

    new_str = []
    index = 0

    for match in re.finditer(tokenizer, string):

        if not (in_multi or in_single):
            tmp = string[index:match.start()]
            if not in_string and strip_space:
                # replace white space as defined in standard
                tmp = re.sub('[ \t\n\r]+', '', tmp)
            new_str.append(tmp)

        index = match.end()
        val = match.group()

        if val == '"' and not (in_multi or in_single):
            escaped = end_slashes_re.search(string, 0, match.start())

            # start of string or unescaped quote character to end string
            if not in_string or (escaped is None or len(escaped.group()) % 2 == 0):
                in_string = not in_string
            index -= 1 # include " character in next catch
        elif not (in_string or in_multi or in_single):
            if val == '/*':
                in_multi = True
            elif val == '//':
                in_single = True
            elif not strip_space and val in '\r\n': #Revised by H. Moseley - July 11, 2014
                new_str.append(val) #Revised by H. Moseley - July 11, 2014
        elif val == '*/' and in_multi and not (in_string or in_single):
            in_multi = False
        elif val in '\r\n' and not (in_multi or in_string) and in_single:
            in_single = False
            if not strip_space: #Revised by H. Moseley - July 11, 2014
                new_str.append(val) #Revised by H. Moseley - July 11, 2014
        elif not ((in_multi or in_single) or (val in '\r\n' and strip_space)):
            new_str.append(val)

    new_str.append(string[index:])
    return ''.join(new_str)

