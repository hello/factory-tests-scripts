from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, F
from datetime import datetime
import time
import json
import argparse
import sys
import re
import requests
import os
import logging
import tempfile
from logging.handlers import RotatingFileHandler

def setupParser():
    """Setup the command line arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--processed_file",               help="File that lists records that have already been processed, so things are repeated every time")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print words")

    return parser.parse_args()

class StructuredMessage(object):
    """Class to make logging look pretty"""
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def __str__(self):
        totalDict = {"event": self.kwargs}
        totalDict["event"]["time"] = datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        return json.dumps(totalDict)

_ = StructuredMessage #easier to read

def main():
    """Main things"""
    arguments = setupParser()

    if not arguments.processed_file:
        print "Must provide processed_file"
        sys.exit(-1)

    try:#the instance this was originally installed on required sudo to access the data drive
        with tempfile.TemporaryFile(dir=os.path.dirname(arguments.processed_file)) as f:
            pass
    except:
        print "\nMust have permissions on folder for processed_file. Try running as sudo as data folder has restricted permissions\n"
        raise


    rootLogDir = os.path.join('/','ubuntu','home','data','logs')#ubuntu server
    if not os.path.exists(rootLogDir):#debugging
        rootLogDir = os.path.join(os.path.expanduser("~"),"tmp","helloLogs")
        try:
            os.makedirs(rootLogDir)
        except:
            pass
    rootLogPath = os.path.join(rootLogDir, "dustOffsetProcessor.txt")

    try:#the instance this was originally installed on required sudo to access the data drive
        with tempfile.TemporaryFile(dir=rootLogDir) as f:
            pass
    except:
        print "\nMust have permissions on folder. Try running as sudo as data folder has restricted permissions\n"
        raise
    fileHandler = RotatingFileHandler(rootLogPath, mode='a', maxBytes=100000000, backupCount=20)#avoids super giant log files
    formatter = logging.Formatter('{"%(levelname)s": %(message)s}')
    fileHandler.setFormatter(formatter)
    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG)#suggest info for regular usage, debug for ...
    logger.addHandler(fileHandler)
    logger.propagate = False

    #es = Elasticsearch("54.164.33.1", timeout=600)
    es = Elasticsearch("localhost", timeout=600)

    search = Search(using=es, index='sensedata-*')

    productFilter = F("term", Product="Morpheus")
    search = search.filter(productFilter)

    goodTestNames = ["dust_calibration_value",#current value as of 1-15-16
        "dust_sensor"]#old value, includes good and bad units, need date filter also
    testNameFilter = F("terms", Test_Name=goodTestNames)
    search = search.filter(testNameFilter)

    dateFilter = F("range", ** {"Start_Time":{"gte":"2015-07-16T00:00:00"}})#when good dust values started
    search = search.filter(dateFilter)

    passFilter = F("term", Test_Result="PASS")
    search = search.filter(passFilter)

    upperLimitFilter = ~F("term", Upper_Limit=300)
    search = search.filter(upperLimitFilter)
    try:
        with open(arguments.processed_file, 'r') as f:
            ids = f.read().splitlines()
    except IOError:
        ids = []

    if ids:
        idFilter = ~F("ids", values=ids)
        search = search.filter(idFilter)

    search = search[0:100000]
    results = search.execute()

    idCheckNames = ["top_id_format_check", "ID_check"]#new name and old name for getting top board ID
    for result in results:
        idValue = ""
        for idName in idCheckNames:
            subSearch = Search(using=es, index='sensedata-*')

            runIDFilter = F("term", Test_Run_ID=result["Test_Run_ID"])
            subSearch = subSearch.filter(runIDFilter)

            topIdFilter =  F("term", Test_Name=idName)
            subSearch = subSearch.filter(topIdFilter)

            idResults = subSearch.execute()

            try:
                if ":" in idResults[0]["Measurement"]:
                    idValue = re.sub(r'(^|:)(?![A-Z0-9][A-Z0-9])([A-Z0-9])',r'\g<1>0\g<2>',
                        idResults[0]["Measurement"].upper()).replace(":","")
                    #makes capital, fills in missing zeroes and removes semicolons, trust me
                else:
                    idValue = idResults[0]["Measurement"].upper().replace(":","")
                break
            except IndexError:
                pass

        if not idValue:
            message = "Couldn't find top board ID from run ID"
            logger.error(_(message=message, result=str(result)))
            if arguments.verbose:
                print message
            continue

        if not isinstance(result['Measurement_num'], float):
            message = "Measurement_num isn't a float"
            logger.error(_(message=message, result=str(result)))
            if arguments.verbose:
                print message
            continue

        timeTestedObj = datetime.strptime(result["Start_Time"],"%Y-%m-%dT%H:%M:%S")
        timeTestedInt = 1000*int((timeTestedObj-datetime(1970,1,1)).total_seconds())#miliseconds from epoch

        payload = '{"tested_at": %d, "sense_id": "%s", "dust_offset": %d}' % (timeTestedInt,
            idValue, int(result['Measurement_num']))

        headers = {
            'authorization': "Bearer %s" % os.environ['SURIPU_PROD'],
            'content-type': "application/json",
            'x-hello-admin': "postman@sayhello.com"
            }

        url = "https://admin-api.hello.is/v1/calibration"
        response = requests.request("PUT", url, data=payload, headers=headers)
        responseStr = str(response)
        if "204" in responseStr or "400" in responseStr:
            with open(arguments.processed_file, 'a') as f:
                f.write(str(result.meta.id)+'\n')
            if "204" in responseStr:
                logger.info(_(message="Result added successfully", response=responseStr, result=str(result)))
                if arguments.verbose:
                    print "Added result successfully: %s" % str(result.meta.id)
            if "400" in responseStr:
                if arguments.verbose:
                    print "Added denied: %s" % str(result.meta.id)
                logger.info(_(message="Result denied", response=responseStr, result=str(result)))
        else:
            if arguments.verbose:
                print "%s Generated unknown response: %s" % (str(result.meta.id), responseStr)
            logger.error(_(message="Unknown response", response=responseStr, result=str(result)))

if __name__ == '__main__':
    main()
