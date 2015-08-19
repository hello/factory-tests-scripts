import re
import os
import csv
import time
import json
import shutil
import math
import argparse
import tarfile
import tempfile
from copy import deepcopy
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import RequestError
from elasticsearch.client import IndicesClient

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

def setupParser(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("-t","--tags",      help="tags to add to the data to make it easier to find in elasticsearch",
            nargs="+")
    parser.add_argument("-f","--tag_file",  help="file with a list of tags for mass processing data",
            default="tagfile.txt")
    parser.add_argument("-r","--recursive", help="recursively navigate the directory structure",
            action="store_true")
    parser.add_argument("-v","--verbose",   help="Wall of text crits you for 1000. You die.",
            action="store_true")
    parser.add_argument("-o","--organize",  help="target directory to organize files by product and date, no arg defaults to ~/proddata",
            const="~/proddata", nargs="?")
    parser.add_argument("-s","--s3_out",    help="root directory to output in the s3 storage format (folder paths and manifest files), no arg defaults to ~/s3SyncDir",
            const="~/s3SyncDir", nargs="?")
    parser.add_argument("directory",        help="directory of files to process")

    if args:
        arguments = parser.parse_args(args)
    else:
        arguments = parser.parse_args()

    return arguments

def parseFile(filePath,verbose):
    numValuesPerLine = 4
    allFilesData = []
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
    with open(filePath,'r') as f:
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
                else:
                    print "Unknown handler for %s\n" % str(trigger(2))
                    exit
                fileData = addToDict(fileData,obj,trigger[0])
                break
            else:
                i += 1
    if i == len(lines):
        print "Could only match these top triggers:\n%s\n" % str(fileData)
        return None

    #Find table header
    while i < len(lines):
        reObj = re.search("TABLE",lines[i])
        if not reObj:
            i += 1
        else:
            break

    if i == len(lines):
        print "Could not find TABLE header\n"
        return None

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
            k = 0
            if lines[i].endswith('\r\n'):
                k = 1
                lines[i] = lines[i].strip()
                while lines[i+k].endswith('\r\n'):
                    lines[i+k] = lines[i+k].strip()
                    k += 1
                stringToSearch = "".join(lines[i:i+k+1])
            else:
                stringToSearch = lines[i]
            reObj = re.search(tableEntryRE, stringToSearch)
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
            i += k
            if reObj:
                break
            else:
                i += 1

        dataValues.append(testDict)

    if not len(dataValues):
        if verbose:
            print "Nothing found in %s" % filePath
        return None

    return dataValues

def indexValues(testData, existingTags, fileName, es, ic):
    timeObj = time.strptime(testData[0]['Start_Time'], "%Y-%m-%dT%H:%M:%S")
    idName = time.strftime('%Y%m%d%H%M%S',timeObj)+'_'+testData[0]['Serial_Number']
    indexName = "proddata-" + time.strftime('%Y.%m.%d',timeObj)
    try:#to create instance and mapping
        ic.create(index=indexName)
        ic.put_mapping(index=indexName, doc_type=mapName, body=mapping) #if this errors it shouldn't get caught and bad things should happen
    except RequestError:#this happens when the index is already created, which is fine, just don't need to remap it
        pass

    for i in range(0,len(testData)):
        testData[i]['Test_Run_ID'] = idName
        tags = ""
        if existingTags:
            try:
                tags = " ".join(existingTags[fileName])
            except KeyError:
                pass

        tagableValues = [testData[i]['Test_Name'],
                         testData[i]['Test_Group'],
                         testData[i]['Measurement']]

        for tag in tagableValues:
            try:
                tags += " " + tag.replace("_"," ")
            except AttributeError:
                pass
        testData[i]['tags'] = tags.strip()
        try:
            res = es.index(index=indexName, id=idName+"_%d"%(i+1), doc_type=mapName, body=testData[i])
        except Exception as e:
            print "IDNAME: %s\n%s" % (idName+"_"+str(i+1),testData[i])
            raise

def moveFile(rootDirectory,dataValue,sourceDir,fileName,verbose):
    try:
        timeObj = time.strptime(dataValue['Start_Time'], "%Y-%m-%dT%H:%M:%S")
        destPath = os.path.join(rootDirectory,dataValue['Product'],time.strftime("%Y",timeObj),time.strftime("%m",timeObj),time.strftime("%d",timeObj))
        os.makedirs(destPath)
    except OSError:
        pass

    if destPath == sourceDir:
        if verbose:
            print "In place: %s" % fileName
        return os.path.join(destPath,fileName)#moving in place might take time when you do it a bajillion times?

    shutil.move(os.path.join(sourceDir,fileName),os.path.join(destPath,fileName))
    if verbose:
        print "Moved: %s" % fileName
    return os.path.join(destPath,fileName)

def readInTagFile(filePath):
    tags = {}
    with open(filePath,'r') as f:
        csvr = csv.reader(f)
        for row in csvr:
            if len(row) < 2:
                print "Weird row in tag file: %s" % str(row)
            else:
                tags[row[0]] = row[1:]
    return tags

def updateTags(fileName, newTags, existingTags):
    tagList = []
    try:
        tagList = existingTags[fileName]
    except KeyError:
        pass
    for tag in newTags:
        tagList.append(tag)
    existingTags[fileName] = tagList
    return existingTags

def formatForS3(dirsToTar, outDir, verbose):
    productLookup ={'Bottom Board':'bottomBoard',
                    'LED Board':'ledBoard',
                    'Middle Board':'middleBoard',
                    'Morpheus':'morpheus',
                    'Pill':'pill',
                    'Pill Board':'pillBoard',
                    'Top Board':'topBoard'}
    for directory in dirsToTar.keys():
        remains, day     = os.path.split(directory)
        remains, month   = os.path.split(remains)
        remains, year    = os.path.split(remains)
        remains, product = os.path.split(remains)

        outputFolder = os.path.join(os.path.expanduser(outDir),year,month,day)
        tarPath = os.path.join(outputFolder,"%s%s%s_%s.tar.gz" % (year,month,day,productLookup[product]))
        manifestPath = os.path.join(outputFolder,"%s%s%s_%s.manifest" % (year,month,day,productLookup[product]))

        try:
            os.makedirs(outputFolder)
        except OSError:
            pass

        newFiles = False
        with tempfile.NamedTemporaryFile(delete=False) as tarFP:
            with tarfile.open(fileobj=tarFP,mode='w:gz') as tar:
                with tempfile.NamedTemporaryFile(delete=False) as mani:
                    if os.path.exists(manifestPath):
                        with open(manifestPath) as existingMani:
                            lines = existingMani.read().splitlines()
                    else:
                        lines = []
                    filesInDir = os.listdir(directory)
                    for fileName in lines:
                        if not fileName.endswith(".htm"):
                            continue
                        if not fileName in filesInDir:
                            print "%s MISSING FROM %s" % (fileName,directory)
                            return
                        else:# do this here to keep added order to manifest. makes diffing way easier, but alphabetical not as easy for directories with diff add dates
                            tar.add(os.path.join(directory,fileName),arcname=os.path.join(product,year,month,day,fileName))
                            mani.write(fileName+'\n')
                            if verbose:
                                print "%s added to %s" % (fileName, os.path.split(tarPath)[1])
                    for fileName in filesInDir:
                        if not fileName.endswith(".htm"):
                            continue
                        if fileName in lines:#already added, move on. should only be new files
                            continue
                        newFiles = True
                        tar.add(os.path.join(directory,fileName),arcname=os.path.join(product,year,month,day,fileName))
                        mani.write(fileName+'\n')
                        if verbose:
                            print "%s added to %s" % (fileName, os.path.split(tarPath)[1])

        if newFiles:
            shutil.copy(os.path.join(tempfile.tempdir,tarFP.name),tarPath)
        os.remove(os.path.join(tempfile.tempdir,tarFP.name))
        if newFiles:
            shutil.copy(os.path.join(tempfile.tempdir,mani.name),manifestPath)
        os.remove(os.path.join(tempfile.tempdir,mani.name))


    return

def navigateDirectoryAndProcess(directory, arguments, es, ic, existingTags, changedPaths):
    if arguments.verbose:
        print "Entering: %s" % directory
    for fileName in os.listdir(directory)[::-1]:
        if arguments.recursive and os.path.isdir(os.path.join(directory,fileName)):
            existingTags, changedPaths = navigateDirectoryAndProcess(os.path.join(directory,fileName), arguments, es, ic, existingTags, changedPaths)
        if not fileName.endswith('.htm') or os.path.isdir(os.path.join(directory,fileName)):
            continue
        filePath = os.path.join(directory,fileName)
        fileData = parseFile(filePath,arguments.verbose)
        if not fileData:
            if arguments.verbose:
                print "No data from %s" % os.path.split(filePath)[1]
            continue

        if arguments.tags:
            existingTags = updateTags(fileName, arguments.tags, existingTags)

        indexValues(fileData, existingTags, fileName, es, ic)

        if arguments.organize:
            filePath = moveFile(os.path.expanduser(arguments.organize),fileData[0],directory,fileName,arguments.verbose)

        changedPaths[str(os.path.split(filePath)[0])] = True

    return existingTags, changedPaths

def main(*args):
    arguments = setupParser(args)
    if not os.path.exists(arguments.directory):
        print "Directory must exist\n"
        return

    existingTags = {}
    if os.path.isfile(arguments.tag_file):
        existingTags = readInTagFile(arguments.tag_file)

    es = Elasticsearch()
    ic = IndicesClient(es)
    changedPaths = {}
    newTagDict, changedPaths = navigateDirectoryAndProcess(arguments.directory, arguments, es, ic, existingTags, changedPaths)
    if arguments.tags:
        with open(arguments.tag_file,'w') as f:
            csvw = csv.writer(f)
            for key in newTagDict.keys():
                row = newTagDict[key]
                row.insert(0,key)
                csvw.writerow(row)

    if arguments.s3_out:
        formatForS3(changedPaths, arguments.s3_out, arguments.verbose)

if __name__ == "__main__":
    main()
