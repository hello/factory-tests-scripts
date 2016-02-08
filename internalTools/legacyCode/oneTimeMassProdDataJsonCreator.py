import re
import os
import csv
import time
import json
import shutil
import math
import argparse
from copy import deepcopy
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import RequestError
from elasticsearch.client import IndicesClient

rootOut = '/Users/brandon/testData'
mapName = "testResult"

mapping = {mapName:{"properties":{"Stop_Time":{"type":"date","format":"dateOptionalTime"},"Test_Script":{"type":"string","index":"not_analyzed"},"Elapsed_Time":{"type":"long"},"Test_Cell":{"type":"long"},"Start_Time":{"type":"date","format":"dateOptionalTime"},"Test_Station":{"type":"string","index":"not_analyzed"},"Serial_Number":{"type":"string","index":"not_analyzed"},"Total_Execution_Time":{"type":"long"},"Test_Result":{"type":"string","index":"not_analyzed"},"Test_Script_Validation_Hash":{"type":"string","index":"not_analyzed"},"Lower_Limit":{"type":"double"},"Measurement_Unit":{"type":"string","index":"not_analyzed"},"Elapsed_Time_result":{"type":"double"},"Measurement_num":{"type":"double"},"Execution_Time":{"type":"double"},"Upper_Limit":{"type":"double"},"Test_Name":{"type":"string","index":"not_analyzed"},"Measurement":{"type":"string","index":"not_analyzed"},"Test_Status":{"type":"string","index":"not_analyzed"},"Is_Measurement":{"type":"boolean"},"Test_Group":{"type":"string","index":"not_analyzed"},"Parametric_Test":{"type":"boolean"},"Color":{"type":"string","index":"not_analyzed"},"Product":{"type":"string","index":"not_analyzed"},"Calc_runtime":{"type":"double"},"Test_Run_ID":{"type":"string","index":"not_analyzed"},"tags":{"type":"string"}}}}

def addToDict(dic, value, name):
    try:#some duplicate names in test results table and top of file
        dic[name.replace(" ","_")]
        name = name+"_result"
    except KeyError:
        pass
    try:
        newVal = float(value)
        if newVal == float('Inf') or newVal == -float('Inf') or name == "Serial Number" or math.isnan(newVal):
            raise ValueError
        if name == "Measurement":
            dic[name] = None
            name += "_num"
        if (name == "Total Execution Time" or name == "Elapsed Time" or name == "Elapsed Time_result") and newVal > 1000000:
            newVal = newVal / 10000000
    except ValueError as e:
        if name == "Measurement":
            dic[name+"_num"] = None
        newVal = value.strip()
        if name == "Is Measurement" or name == "Parametric Test":
            newVal = value == "&#149;"
        if name == "Upper Limit" or name == "Lower Limit":
            return dic
        if value == "&nbsp":
            newVal = None
        if name == "Serial Number":
            if value.upper().startswith("91000008B"):
                dic['Color'] = "Black"
            elif value.upper().startswith("91000008W"):
                dic['Color'] = "White"
            else:
                dic['Color'] = None

            if value.startswith("91000008"):
                dic['Product'] = "Morpheus"
            elif value.startswith("90500005"):
                dic['Product'] = "Bottom Board"
            elif value.startswith("90500006"):
                dic['Product'] = "LED Board"
            elif value.startswith("90500004"):
                dic['Product'] = "Middle Board"
            elif value.startswith("90500003"):
                dic['Product'] = "Top Board"
            elif value.startswith("90500007"):
                dic['Product'] = "Pill Board"
            elif value.startswith("91000009"):
                dic['Product'] = "Pill"
            else:
                dic['Product'] = "Unknown"

        if name == "Measurement Unit" and value.lower() == "string" and dic['Measurement_num'] != None:
            dic['Measurement'] = str(dic['Measurement_num'])
            dic['Measurement_num'] = None

    dic[name.replace(" ","_")] = newVal
    return dic

def setupParser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t","--tags",      help="tags to add to the data to make it easier to find", nargs="+")
    parser.add_argument("directory",        help="directory of files to process")

    arguments = parser.parse_args()

    if not os.path.exists(arguments.directory):
        print "Directory must exist\n"
        exit

    return arguments

arguments = setupParser()

topTriggers = [
        ("Serial Number",r'Serial Number:(.*)</h3>',str),
        ("Start Time",r'Start Time:(.*)</h3>',time.time),
        ("Stop Time",r'Stop Time:(.*)</h3>',time.time),
        ("Test Station",r'Test Station:(.*)</h3>',str),
        ("Test Cell",r'Test Cell:(.*)</h3>',int),
        ("Test Result",r'Test Result:.*>(.*)</FONT>',str),
        ("Test Script",r'Test Script:(.*)</h3>',str),
        ("Test Script Validation Hash",r'Test Script Validation Hash:(.*)</h3>',str),
        ("Elapsed Time",r'Elapsed Time:(.*)</h3>',int),
        ("Total Execution Time",r'Total Execution Time:(.*)</h3>',int)]

numValuesPerLine = 4
allFilesData = []
es = Elasticsearch()
ic = IndicesClient(es)

for fileName in os.listdir(arguments.directory):
    if not fileName.endswith("htm"):
        continue
    with open(os.path.join(arguments.directory,fileName),'r') as f:
        lines = f.readlines()
    fileData = {}
    i = 0
    for trigger in topTriggers:
        while i < len(lines):
            reObj = re.search(trigger[1],lines[i])
            if reObj:
                if trigger[2] == str:
                    obj = reObj.group(1).strip()
                elif trigger[2] == int:
                    obj = int(reObj.group(1).strip())
                elif trigger[2] == time.time:
                    timeObj = time.strptime(reObj.group(1).strip(), "%A, %B %d, %Y %I:%M:%S %p")
                    obj = time.strftime("%Y-%m-%dT%H:%M:%S",timeObj)
                    if trigger[0] == "Start Time":
                        startTime=timeObj
                else:
                    print "Unknown handler for %s\n" % str(trigger(2))
                    exit
                fileData = addToDict(fileData,obj,trigger[0])
                break
            else:
                i += 1
    if i == len(lines):
        print "Could only match these top triggers:\n%s\n" % str(fileData)
        continue

    #Find table header
    while i < len(lines):
        reObj = re.search("TABLE",lines[i])
        if not reObj:
            i += 1
        else:
            break

    if i == len(lines):
        print "Could not find TABLE header\n"
        continue

    #find table title
    while i < len(lines):
        titleRE = '<TR.*?><TD.*?>(?:<.+?>)*(.*?)(?:<.*?>)*?</TD></TR>'
        reObj = re.search(titleRE, lines[i])
        i += 1
        if not reObj:
            continue
        else:
            tableTitle = reObj.group(1).strip()
            break

    #find column headers
    while i < len(lines):
        reObj = re.search('<TR.*?>',lines[i])
        if not reObj:
            i += 1
        else:
            break

    #read column headers
    headers = []
    tableEntryRE = ''
    for j in range(0,numValuesPerLine):
        tableEntryRE += '(?:(?:<TD.*?>)(?:<.+?>)*(.*?)(?:<.*?>)*?</TD>)?'

    #read first line out of loop to avoid <TR>
    reObj = re.search(tableEntryRE, lines[i])
    if reObj:
        for j in range(0,numValuesPerLine):
            if reObj.group(j+1) is not None:
                headers.append(reObj.group(j+1))
            else:
                break

    i += 1

   #read the rest of the column header values, break on TR
    while i < len(lines):
        reObj = re.search(tableEntryRE, lines[i])
        if reObj:
            for j in range(0,numValuesPerLine):
                if reObj.group(j+1) is not None:
                    headers.append(reObj.group(j+1).strip())
                else:
                    break
        reObj = re.search('<TR.*?>',lines[i])
        if reObj:
            break
        else:
            i += 1

    elapsedTime = 0
    dataValues = []
    while i < len(lines):
        testDict = deepcopy(fileData)
        columnNumber = 0
        #read first line out of loop to avoid <TR>
        reObj = re.search(tableEntryRE, lines[i])
        if reObj:
            for j in range(0,numValuesPerLine):
                if reObj.group(j+1) is not None:
                    testDict = addToDict(testDict,reObj.group(j+1).strip(),headers[columnNumber])
                    if headers[columnNumber] == "Elapsed Time":
                        testDict = addToDict(testDict,float(reObj.group(j+1).strip())-elapsedTime,"Calc_runtime")
                        elapsedTime=float(reObj.group(j+1).strip())
                    columnNumber += 1
                else:
                    break

        i += 1

        while i < len(lines):
            reObj = re.search(tableEntryRE, lines[i])
            if reObj:
                for j in range(0,numValuesPerLine):
                    if reObj.group(j+1) is not None:
                        testDict = addToDict(testDict,reObj.group(j+1).strip(),headers[columnNumber])
                        if headers[columnNumber] == "Elapsed Time":
                            testDict = addToDict(testDict,float(reObj.group(j+1).strip())-elapsedTime,"Calc_runtime")
                            elapsedTime=float(reObj.group(j+1).strip())
                        columnNumber += 1
                    else:
                        break
            reObj = re.search('<TR.*?>',lines[i])
            if reObj:
                break
            else:
                i += 1

        dataValues.append(testDict)

    if not len(dataValues):
        print "Nothing found in %s" % fileName
        continue

    idName = time.strftime('%Y%m%d%H%M%S',startTime)+'_'+fileData['Serial_Number']
    indexName = "proddata-" + time.strftime('%Y.%m.%d',startTime)
    try:#to create instance and mapping
        ic.create(index=indexName)
        ic.put_mapping(index=indexName, doc_type=mapName, body=mapping) #if this errors it shouldn't get caught and bad things should happen
    except RequestError:
        pass

    for i in range(0,len(dataValues)):
        dataValues[i]['Test_Run_ID'] = idName
        tags = ""
        if arguments.tags:
            tags = " ".join(arguments.tags)

        tagableValues = [dataValues[i]['Test_Name'],
                         dataValues[i]['Test_Group'],
                         dataValues[i]['Measurement']]

        for tag in tagableValues:
            try:
                tags += " " + tag.replace("_"," ")
            except AttributeError:
                pass
        dataValues[i]['tags'] = tags.strip()
        try:
            res = es.index(index=indexName, id=idName+"_%d"%(i+1), doc_type=mapName, body=dataValues[i])
        except Exception as e:
            print "IDNAME: %s\n%s" % (idName+"_"+str(i+1),dataValues[i])
            raise

    try:
        destPath = os.path.join(rootOut,dataValues[i]['Product'],time.strftime("%Y",startTime),time.strftime("%m",startTime),time.strftime("%d",startTime))
        os.makedirs(destPath)
    except OSError:
        pass

    if destPath == sys.argv[1]:
        print "COMPLETE: %s" % fileName
        continue#moving in place might take time when you do it a bajillion times?

    shutil.move(os.path.join(sys.argv[1],fileName),os.path.join(destPath,fileName))

    #print "COMPLETE: %s" % fileName


