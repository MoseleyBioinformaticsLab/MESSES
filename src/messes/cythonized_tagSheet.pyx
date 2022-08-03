# -*- coding: utf-8 -*-

#cython: language_level=3
import re
import sys

import numpy
cimport numpy

import copier
from extract_metadata import Evaluator, FieldMaker, TagParser, VariableOperand, LiteralOperand, xstr



headerSplitter = re.compile(r'[+]|(r?\"[^\"]*\"|r?\'[^\']*\')|\s+')
def tagSheet(taggingDirectives, str[:,:] worksheet):
    """Add tags to the worksheet using the given tagging directives.

    Args:
        taggingDirectives (list): List of dictionaries. One dictionary for each tagging group.
        worksheet (memoryview): cython memoryview to a 2d numpy array of strings (objects).
        
    Returns:
        (tuple): tuple where the first value is the worksheet memoryview turned into a numpy array and the second value is a list of bools indicating which tagging directives in taggingDirectives were used.
    """
    cdef Py_ssize_t rowIndex = 0
    cdef Py_ssize_t endingRowIndex = 0
    cdef Py_ssize_t tdIndex = 0
    wasTaggingDirectiveUsed = [False for directive in taggingDirectives]
    if taggingDirectives != None:
        reCopier = copier.Copier()

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
                    # temp_df = pandas.DataFrame(taggingGroup["insert"], dtype=str)
                    # worksheet = pandas.concat([temp_df, worksheet]).fillna("")
                    usedRows = set(row + len(temp_array) for row in usedRows)
                    usedRows.update(range(len(temp_array)))
                    wasTaggingDirectiveUsed[i] = True
                continue

            ## Loop through the header tag descriptions and determine the required headers and tests for them.
            ## This is just setting up some data structures to make modifying worksheet easier later.
            headerTests = {}
            requiredHeaders = set()
            for headerTagDescription in taggingGroup["header_tag_descriptions"]:
                ## If the added tag is an eval() tag created the header test differently.
                if reCopier(Evaluator.isEvalString(headerTagDescription["header"])):
                    evaluator = Evaluator(reCopier.value.group(1), False, True)
                    headerTagDescription["field_maker"] = evaluator
                    headerTagDescription["header_list"] = []
                    headerTagDescription["header_tests"] = evaluator.fieldTests.copy()
                    headerTagDescription["header_tests"].update({ headerString : re.compile("^" + headerString + "$") for headerString in evaluator.requiredFields if headerString not in evaluator.fieldTests })
                    headerTests.update(headerTagDescription["header_tests"])

                    if headerTagDescription["required"]:
                        requiredHeaders.update(headerTagDescription["header_tests"].keys())
                else:
                    headerTagDescription["header_list"] = [ token for token in re.split(headerSplitter, headerTagDescription["header"]) if token != "" and token != None ]
                    headerTagDescription["header_tests"] = {}
                    fieldMaker = FieldMaker(headerTagDescription["header"])
                    for headerString in headerTagDescription["header_list"]:
                        if reCopier(re.match(TagParser.reDetector, headerString)):
                            fieldMaker.operands.append(VariableOperand(headerString))
                            headerTagDescription["header_tests"][headerString] = re.compile(reCopier.value.group(1))
                            headerTests[headerString] = headerTagDescription["header_tests"][headerString]
                        elif reCopier(re.match(TagParser.stringExtractor, headerString)):
                            fieldMaker.operands.append(LiteralOperand(reCopier.value.group(1)))
                        else:
                            fieldMaker.operands.append(VariableOperand(headerString))
                            headerTagDescription["header_tests"][headerString] = re.compile("^" + headerString + "$")
                            headerTests[headerString] = headerTagDescription["header_tests"][headerString]

                    if headerTagDescription["required"]:
                        requiredHeaders.update(headerTagDescription["header_tests"].keys())

                    if len(headerTagDescription["header_list"]) > 1 or len(headerTagDescription["header_list"]) != len(headerTagDescription["header_tests"]):
                        headerTagDescription["field_maker"] = fieldMaker


            if "exclusion_test" in taggingGroup:
                testString = taggingGroup["exclusion_test"]
                if reCopier(re.match(TagParser.reDetector, testString)):
                    exclusionTest = re.compile(reCopier.value.group(1))
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
                    exclusionIndeces = [ columnIndex for columnIndex in range(1,len(row)) if re.search(exclusionTest, xstr(row[columnIndex]).strip()) ]
                    if len(exclusionIndeces) > 0:
                        rowIndex += 1
                        continue
                
                header2ColumnIndex = {}
                for headerString, headerTest in headerTests.items():
                    columnIndeces = [ columnIndex for columnIndex in range(1,len(row)) if re.search(headerTest, xstr(row[columnIndex]).strip()) ]
                    if len(columnIndeces) == 1: # must be unique match
                        header2ColumnIndex[headerString] = columnIndeces[0]
                    elif len(columnIndeces) > 1:
                        print("Warning: The header, " + headerString + ", in tagging group, " + str(i) + ", was matched to more than 1 column near or on row, " + str(rowIndex) + ", in the tagged export.", file=sys.stderr)

                if header2ColumnIndex and len(set(header2ColumnIndex[headerString] for headerString in requiredHeaders if headerString in header2ColumnIndex)) == len(requiredHeaders): # found header row
                    found = False
                    endingRowIndex = rowIndex+1
                    for endingRowIndex in range(rowIndex+1, len(worksheet[:, 0])):
                        if TagParser._isEmptyRow(worksheet[endingRowIndex, :]) or re.match('#tags$', xstr(worksheet[endingRowIndex,0]).strip()) or endingRowIndex in usedRows:
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
                            # temp_df = pandas.DataFrame(taggingGroup["insert"], dtype=str)
                            # worksheet = pandas.concat([worksheet[0:rowIndex, :], temp_df, worksheet[rowIndex:, :]]).fillna("")
                            usedRows = set(index if index < rowIndex else index+insertNum for index in usedRows)
                            usedRows.update(range(rowIndex,rowIndex+insertNum))
                            rowIndex += insertNum
                            endingRowIndex += insertNum

                        # Insert #tags row and the #tags and #ignore tags.
                        worksheet = numpy.concatenate((worksheet[0:rowIndex+1,:], worksheet[rowIndex:,:]), axis=0, dtype=object)
                        # worksheet = pandas.concat([ worksheet[0:rowIndex+1,:], worksheet[rowIndex:,:] ])
                        worksheet[rowIndex+1,:] = ""
                        worksheet[rowIndex,0] = "#ignore"
                        worksheet[rowIndex+1,0] = "#tags"
                        endingRowIndex += 1

                        usedRows = set(index if index < rowIndex+1 else index+1 for index in usedRows)
                        usedRows.update(range(rowIndex,endingRowIndex))

                        # Create correct relative column order.
                        originalTDColumnIndeces = [ 1000 for x in range(len(taggingGroup["header_tag_descriptions"])) ]
                        for tdIndex in range(len(taggingGroup["header_tag_descriptions"])):
                            if "field_maker" in taggingGroup["header_tag_descriptions"][tdIndex] and \
                                    all( headerString in header2ColumnIndex for headerString in taggingGroup["header_tag_descriptions"][tdIndex]["header_tests"] ):
                                originalTDColumnIndeces[tdIndex] = 1001
                            elif "field_maker" not in taggingGroup["header_tag_descriptions"][tdIndex] and not taggingGroup["header_tag_descriptions"][tdIndex]["header_list"]:
                                originalTDColumnIndeces[tdIndex] = 1001
                            elif "field_maker" not in taggingGroup["header_tag_descriptions"][tdIndex] and taggingGroup["header_tag_descriptions"][tdIndex]["header_list"][0] in header2ColumnIndex:
                                originalTDColumnIndeces[tdIndex] = header2ColumnIndex[taggingGroup["header_tag_descriptions"][tdIndex]["header_list"][0]]

                        newTDColumnIndeces = originalTDColumnIndeces.copy()
                        for tdIndex in range(len(taggingGroup["header_tag_descriptions"])):
                            # insert new column if needed
                            if (newTDColumnIndeces[tdIndex] == 1001 or newTDColumnIndeces[tdIndex] < 1000) and reCopier(min(newTDColumnIndeces[tdIndex+1:]+[len(worksheet[0,:])])) < newTDColumnIndeces[tdIndex]:
                                worksheet = numpy.insert(worksheet, reCopier.value, "", axis=1)
                                # worksheet.insert(reCopier.value, "", "", True)
                                # worksheet.columns = range(worksheet.shape[1])
                                header2ColumnIndex = { headerString:(index+1 if index >= reCopier.value else index) for headerString, index in header2ColumnIndex.items() } # must be done before the next if, else statement
                                if originalTDColumnIndeces[tdIndex] != 1001: # copy normal columns
                                    worksheet[rowIndex:endingRowIndex, reCopier.value] = worksheet[rowIndex:endingRowIndex, newTDColumnIndeces[tdIndex]+1]
                                    header2ColumnIndex[taggingGroup["header_tag_descriptions"][tdIndex]["header_list"][0]] = reCopier.value

                                newTDColumnIndeces[tdIndex] = reCopier.value
                                newTDColumnIndeces[tdIndex+1:] = [ index+1 if index >= reCopier.value and index < 1000 else index for index in newTDColumnIndeces[tdIndex+1:] ]

                        # Add tags.
                        for tdIndex in range(len(taggingGroup["header_tag_descriptions"])):
                            if originalTDColumnIndeces[tdIndex] != 1000:
                                worksheet[rowIndex+1, newTDColumnIndeces[tdIndex]] = taggingGroup["header_tag_descriptions"][tdIndex]["tag"]

                        # Compose new columns.
                        makerIndeces = [ tdIndex for tdIndex in range(len(taggingGroup["header_tag_descriptions"])) if originalTDColumnIndeces[tdIndex] == 1001 ]
                        for rIndex in range(rowIndex + 2, endingRowIndex):
                            row = worksheet[rIndex, :]
                            record = { headerString:xstr(row[cIndex]).strip() for headerString, cIndex in header2ColumnIndex.items() }
                            for tdIndex in makerIndeces:
                                if "field_maker" in taggingGroup["header_tag_descriptions"][tdIndex]:
                                    if type(taggingGroup["header_tag_descriptions"][tdIndex]["field_maker"]) == FieldMaker:
                                        worksheet[rIndex, newTDColumnIndeces[tdIndex]] = taggingGroup["header_tag_descriptions"][tdIndex]["field_maker"].create(record, row)
                                    else:
                                        worksheet[rIndex, newTDColumnIndeces[tdIndex]] = taggingGroup["header_tag_descriptions"][tdIndex]["field_maker"].evaluate(record)
                                        
                        wasTaggingDirectiveUsed[i] = True
                else:
                    rowIndex += 1

    return numpy.array(worksheet), wasTaggingDirectiveUsed




























