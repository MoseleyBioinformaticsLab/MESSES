# -*- coding: utf-8 -*-

#cython: language_level=3
import re
import sys

import numpy
cimport numpy

from messes.extract import extract

COLUMN_ORDER_CONSTANT = 16000
COLUMN_ORDER_CONSTANT_PLUS = COLUMN_ORDER_CONSTANT + 1

headerSplitter = re.compile(r'[+]|(r?\"[^\"]*\"|r?\'[^\']*\')')
def tagSheet(taggingDirectives, str[:,:] worksheet, silent):
    """Add tags to the worksheet using the given tagging directives.

    Args:
        taggingDirectives (list): List of dictionaries. One dictionary for each tagging group.
        worksheet (memoryview): cython memoryview to a 2d numpy array of strings (objects).
        silent (bool): if True don't print warnings.
        
    Returns:
        (tuple): tuple where the first value is the worksheet memoryview turned into a numpy array and the second value is a list of bools indicating which tagging directives in taggingDirectives were used.
    """
    cdef Py_ssize_t rowIndex = 0
    cdef Py_ssize_t endingRowIndex = 0
    cdef Py_ssize_t tdIndex = 0
    wasTaggingDirectiveUsed = []
    if taggingDirectives != None:
        wasTaggingDirectiveUsed = [False for directive in taggingDirectives]

        if not any([cell == "#tags" for cell in worksheet[:, 0]]) and not all([cell == '' for cell in worksheet[:, 0]]):
            worksheet = numpy.insert(worksheet, 0, "", axis=1)

        usedRows = set()
        # Process each tagging group.
        for i, taggingGroup in enumerate(taggingDirectives):
            if "header_tag_descriptions" not in taggingGroup:
                # Insert at the beginning of the sheet
                if "insert" in taggingGroup and len(taggingGroup["insert"]):
                    temp_array = numpy.array(taggingGroup["insert"], dtype=object)
                    temp_array_columns = temp_array.shape[1]
                    worksheet_columns = len(worksheet[0,:])
                    if temp_array_columns < worksheet_columns:
                        temp_array = numpy.concatenate((temp_array, numpy.full((temp_array.shape[0],worksheet_columns-temp_array_columns), "", dtype=object)), axis=1, dtype=object)
                    elif temp_array_columns > worksheet_columns:
                        worksheet = numpy.concatenate((worksheet, numpy.full((len(worksheet[:,0]),temp_array_columns-worksheet_columns), "", dtype=object)), axis=1, dtype=object)
                    worksheet = numpy.concatenate((temp_array, worksheet), axis=0, dtype=object)
                    usedRows = set(row + len(temp_array) for row in usedRows)
                    usedRows.update(range(len(temp_array)))
                    wasTaggingDirectiveUsed[i] = True
                continue

            ## Loop through the header tag descriptions and determine the required headers and tests for them.
            ## This is just setting up some data structures to make modifying worksheet easier later.
            headerTests = {}
            requiredHeaders = set()
            newColumnHeaders = set()
            for headerTagDescription in taggingGroup["header_tag_descriptions"]:
                ## If the added tag is an eval() tag create the header test differently.
                if (reMatch := extract.Evaluator.isEvalString(headerTagDescription["header"])):
                    evaluator = extract.Evaluator(reMatch.group(1), False, True)
                    headerTagDescription["field_maker"] = evaluator
                    headerTagDescription["header_list"] = []
                    headerTagDescription["header_tests"] = evaluator.fieldTests.copy()
                    headerTagDescription["header_tests"].update({ headerString : re.compile("^" + headerString + "$") for headerString in evaluator.requiredFields if headerString not in evaluator.fieldTests })
                    headerTests.update(headerTagDescription["header_tests"])

                    if headerTagDescription["required"]:
                        requiredHeaders.update(headerTagDescription["header_tests"].keys())
                    newColumnHeaders.update(headerTagDescription["header_tests"].keys())
                else:
                    headerTagDescription["header_list"] = [strippedToken for token in re.split(headerSplitter, headerTagDescription["header"]) if token != None and (strippedToken := token.strip()) != ""]
                    headerTagDescription["header_tests"] = {}
                    fieldMaker = extract.FieldMaker(headerTagDescription["header"])
                    for headerString in headerTagDescription["header_list"]:
                        if (reMatch := re.match(extract.TagParser.reDetector, headerString)):
                            fieldMaker.operands.append(extract.VariableOperand(headerString))
                            headerTagDescription["header_tests"][headerString] = re.compile(reMatch.group(1))
                            headerTests[headerString] = headerTagDescription["header_tests"][headerString]
                        elif (reMatch := re.match(extract.TagParser.stringExtractor, headerString)):
                            fieldMaker.operands.append(extract.LiteralOperand(reMatch.group(1)))
                        else:
                            fieldMaker.operands.append(extract.VariableOperand(headerString))
                            headerTagDescription["header_tests"][headerString] = re.compile("^" + headerString + "$")
                            headerTests[headerString] = headerTagDescription["header_tests"][headerString]

                    if headerTagDescription["required"]:
                        requiredHeaders.update(headerTagDescription["header_tests"].keys())

                    if len(headerTagDescription["header_list"]) > 1 or len(headerTagDescription["header_list"]) != len(headerTagDescription["header_tests"]):
                        headerTagDescription["field_maker"] = fieldMaker
                        newColumnHeaders.update(headerTagDescription["header_tests"].keys())


            if "exclusion_test" in taggingGroup:
                testString = taggingGroup["exclusion_test"]
                if (reMatch := re.match(extract.TagParser.reDetector, testString)):
                    exclusionTest = re.compile(reMatch.group(1))
                else:
                    exclusionTest = re.compile("^" + testString + "$")
            else:
                exclusionTest = None

            ## Actually modify worksheet.
            insert = False
            rowIndex = 0
            while rowIndex < len(worksheet[:, 0]):
                if rowIndex in usedRows:
                    rowIndex += 1
                    continue

                row = worksheet[rowIndex, :]
                
                if exclusionTest:
                    exclusionIndeces = [ columnIndex for columnIndex in range(1,len(row)) if re.search(exclusionTest, extract.xstr(row[columnIndex]).strip()) ]
                    if len(exclusionIndeces) > 0:
                        rowIndex += 1
                        continue
                
                header2ColumnIndex = {}
                columnIndex2Header = {}
                for headerString, headerTest in headerTests.items():
                    columnIndeces = [ columnIndex for columnIndex in range(1,len(row)) if re.search(headerTest, extract.xstr(row[columnIndex]).strip()) ]
                    if len(columnIndeces) == 1: # must be unique match
                        header2ColumnIndex[headerString] = columnIndeces[0]
                        if columnIndeces[0] in columnIndex2Header:
                            columnIndex2Header[columnIndeces[0]].append(headerString)
                        else:
                            columnIndex2Header[columnIndeces[0]] = [headerString]
                    elif len(columnIndeces) > 1 and not silent:
                        print("Warning: The header, " + headerString + ", in automation group, " + str(i) + ", was matched to more than 1 column near or on row, " + str(rowIndex) + ", in the tagged export.", file=sys.stderr)

                ## If 2 tests match to the same header it is not always a collision to be skipped.
                ## The same header is not tagged twice
                collidingHeaders = False
                for columnIndex, headers in columnIndex2Header.items():
                    count = 0
                    for header in headers:
                        if not header in newColumnHeaders:
                            count += 1
                    if count > 1:
                        collidingHeaders = True
                        break
                
                ## At least 1 header is found, all required headers found, and the same one isn't tagged twice.
                if header2ColumnIndex and all([headerString in header2ColumnIndex for headerString in requiredHeaders]) and not collidingHeaders:
                    found = False
                    endingRowIndex = rowIndex+1
                    for endingRowIndex in range(rowIndex+1, len(worksheet[:, 0])):
                        if extract.TagParser._isEmptyRow(worksheet[endingRowIndex, :]) or re.match('#tags$', extract.xstr(worksheet[endingRowIndex,0]).strip()) or endingRowIndex in usedRows:
                            found = True
                            break

                    if not found:
                        endingRowIndex = len(worksheet[:, 0])

                    if endingRowIndex != rowIndex+1: # Ignore header row with empty line after it.
                        if "insert" in taggingGroup and len(taggingGroup["insert"]) and (not insert or taggingGroup["insert_multiple"]):
                            insert = True
                            insertNum = len(taggingGroup["insert"])
                            temp_array = numpy.array(taggingGroup["insert"], dtype=object)
                            temp_array_columns = temp_array.shape[1]
                            worksheet_columns = len(worksheet[0,:])
                            if temp_array_columns < worksheet_columns:
                                temp_array = numpy.concatenate((temp_array, numpy.full((temp_array.shape[0],worksheet_columns-temp_array_columns), "", dtype=object)), axis=1, dtype=object)
                            elif temp_array_columns > worksheet_columns:
                                worksheet = numpy.concatenate((worksheet, numpy.full((len(worksheet[:,0]),temp_array_columns-worksheet_columns), "", dtype=object)), axis=1, dtype=object)
                            worksheet = numpy.concatenate((worksheet[0:rowIndex, :], temp_array, worksheet[rowIndex:, :]), axis=0, dtype=object)
                            usedRows = set(index if index < rowIndex else index+insertNum for index in usedRows)
                            usedRows.update(range(rowIndex,rowIndex+insertNum))
                            rowIndex += insertNum
                            endingRowIndex += insertNum

                        # Insert #tags row and the #tags and #ignore tags.
                        worksheet = numpy.concatenate((worksheet[0:rowIndex+1,:], worksheet[rowIndex:,:]), axis=0, dtype=object)
                        worksheet[rowIndex+1,:] = ""
                        worksheet[rowIndex,0] = "#ignore"
                        worksheet[rowIndex+1,0] = "#tags"
                        endingRowIndex += 1

                        usedRows = set(index if index < rowIndex+1 else index+1 for index in usedRows)
                        usedRows.update(range(rowIndex,endingRowIndex))

                        # Create correct relative column order.
                        originalTDColumnIndeces = [ COLUMN_ORDER_CONSTANT for x in range(len(taggingGroup["header_tag_descriptions"])) ]
                        for tdIndex in range(len(taggingGroup["header_tag_descriptions"])):
                            ## If the header tag has a field_maker and all of the header_tests are in the header row it needs a new column.
                            if "field_maker" in taggingGroup["header_tag_descriptions"][tdIndex] and \
                                    all( headerString in header2ColumnIndex for headerString in taggingGroup["header_tag_descriptions"][tdIndex]["header_tests"] ):
                                originalTDColumnIndeces[tdIndex] = COLUMN_ORDER_CONSTANT_PLUS
                            ## If the header tag does not have a field_maker and has an empty header_list it needs a new column.
                            elif "field_maker" not in taggingGroup["header_tag_descriptions"][tdIndex] and not taggingGroup["header_tag_descriptions"][tdIndex]["header_list"]:
                                originalTDColumnIndeces[tdIndex] = COLUMN_ORDER_CONSTANT_PLUS
                            ## If the header tag does not have a field_maker and the first element of its header list is in the header row then it needs a new column.
                            elif "field_maker" not in taggingGroup["header_tag_descriptions"][tdIndex] and taggingGroup["header_tag_descriptions"][tdIndex]["header_list"][0] in header2ColumnIndex:
                                originalTDColumnIndeces[tdIndex] = header2ColumnIndex[taggingGroup["header_tag_descriptions"][tdIndex]["header_list"][0]]

                        newTDColumnIndeces = originalTDColumnIndeces.copy()
                        for tdIndex in range(len(taggingGroup["header_tag_descriptions"])):
                            # insert new column if needed
                            ## The COLUMN_ORDER_CONSTANT_PLUS values always need a new column for themselves, but the values less than COLUMN_ORDER_CONSTANT only need a new column if they need to be reordered.
                            ## The second condition looks to see if the header tag under study needs to be reordered by seeing if there are any header tags that have a column index less than it. 
                            ## If a header tag has an index less than the one under study then it means it needs to move to the right because the other header tag needs to be before the one under study.
                            if (newTDColumnIndeces[tdIndex] == COLUMN_ORDER_CONSTANT_PLUS or newTDColumnIndeces[tdIndex] < COLUMN_ORDER_CONSTANT) and (minColumnIndex := min(newTDColumnIndeces[tdIndex+1:]+[len(worksheet[0,:])])) < newTDColumnIndeces[tdIndex]:
                                worksheet = numpy.insert(worksheet, minColumnIndex, "", axis=1)
                                header2ColumnIndex = { headerString:(index+1 if index >= minColumnIndex else index) for headerString, index in header2ColumnIndex.items() } # must be done before the next if, else statement
                                if originalTDColumnIndeces[tdIndex] != COLUMN_ORDER_CONSTANT_PLUS: # copy normal columns
                                    worksheet[rowIndex:endingRowIndex, minColumnIndex] = worksheet[rowIndex:endingRowIndex, newTDColumnIndeces[tdIndex]+1]
                                    header2ColumnIndex[taggingGroup["header_tag_descriptions"][tdIndex]["header_list"][0]] = minColumnIndex

                                newTDColumnIndeces[tdIndex] = minColumnIndex
                                newTDColumnIndeces[tdIndex+1:] = [ index+1 if index >= minColumnIndex and index < COLUMN_ORDER_CONSTANT else index for index in newTDColumnIndeces[tdIndex+1:] ]

                        # Add tags.
                        for tdIndex in range(len(taggingGroup["header_tag_descriptions"])):
                            if originalTDColumnIndeces[tdIndex] != COLUMN_ORDER_CONSTANT:
                                worksheet[rowIndex+1, newTDColumnIndeces[tdIndex]] = taggingGroup["header_tag_descriptions"][tdIndex]["tag"]

                        # Compose new columns.
                        makerIndeces = [ tdIndex for tdIndex in range(len(taggingGroup["header_tag_descriptions"])) if originalTDColumnIndeces[tdIndex] == COLUMN_ORDER_CONSTANT_PLUS ]
                        for rIndex in range(rowIndex + 2, endingRowIndex):
                            row = worksheet[rIndex, :]
                            record = { headerString:extract.xstr(row[cIndex]).strip() for headerString, cIndex in header2ColumnIndex.items() }
                            for tdIndex in makerIndeces:
                                if "field_maker" in taggingGroup["header_tag_descriptions"][tdIndex]:
                                    if type(taggingGroup["header_tag_descriptions"][tdIndex]["field_maker"]) == extract.FieldMaker:
                                        worksheet[rIndex, newTDColumnIndeces[tdIndex]] = taggingGroup["header_tag_descriptions"][tdIndex]["field_maker"].create(record, row)
                                    else:
                                        worksheet[rIndex, newTDColumnIndeces[tdIndex]] = taggingGroup["header_tag_descriptions"][tdIndex]["field_maker"].evaluate(record)
                                        
                        wasTaggingDirectiveUsed[i] = True
                else:
                        rowIndex += 1

    return numpy.array(worksheet), wasTaggingDirectiveUsed




























