import csv
import argparse
import datetime
from datetime import date
import sys
from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q, F, A

def setupParser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-b","--begin_date",    help="beginning date (optional time) of results",
            type=mkdate)
    parser.add_argument("-e","--end_date",      help="date (optional time) of result end",
            type=mkdate)
    parser.add_argument("-l","--list_tests",    help="command to list all the test names",
            action="store_true")
    parser.add_argument("-s","--serial_numbers",help="specific serial numbers to search for",
            nargs="+")
    parser.add_argument("-t","--test_names",    help="names of tests to pull records for",
            nargs="+")
    parser.add_argument("-g","--test_groups",   help="names of test groups to pull records for",
            nargs="+")
    parser.add_argument("-p","--products",      help="Morpheus, \"Top Board\", Middle Board, \"LED Board\", \"Bottom Board\", \"Pill Board\", Pill",
            nargs="+")
    parser.add_argument("--hashes",             help="for getting results from a specific test hash",
            nargs="+")
    parser.add_argument("-r","--enable_regexp", help="enable regular expressions for products, test names, test groups",
            action="store_true")
    parser.add_argument("-m","--enable_limits", help="add limits to output",
            action="store_true")
    parser.add_argument("-c","--enable_calc_t", help="add the calculated time for each test to the output",
            action="store_true")
    parser.add_argument("-n","--num_results",   help="max number of returned rows (default: 500000)",
            type=int, default=500000)
    parser.add_argument("-o","--output_file",   help="output file name (default: csvResults.csv, no arg for stdout)",
            nargs="?", type=argparse.FileType('w'), const=sys.stdout, default="csvResults.csv")
    parser.add_argument("-a","--tags",          help="search for tests, groups, results that you don't know the exact format of",
            nargs="+")
    parser.add_argument("-d","--detailed",      help="give detailed test results, helps separate tests that may differ with the same name, but also noisy",
            action="store_true")
    parser.add_argument("-v","--very_detailed", help="give very detailed test results, tests separated by checksum, very noisy",
            action="store_true")
    parser.add_argument("-q","--print_query",   help="print the json query instead of actually running it.",
            action="store_true")


    arguments = parser.parse_args()

    return arguments

def mkdate(datestr):
    try:
        return datetime.datetime.strptime(datestr, '%Y-%m-%d')
    except ValueError:
        try:
            return datetime.datetime.strptime(datestr, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            raise argparse.ArgumentTypeError(datestr + ' is not formatted correctly.\nFormat: 2015-06-21 or "2015-06-21 15:24:42"')

def buildCommonSearch(arguments, search=None, size=0):
    if not search:
        search = Search()
    toFilter = []
    if arguments.tags:
        query = Q("query_string", query=" ".join(arguments.tags), analyze_wildcard=True)
        search = search.query(query)

    filters = [["Product",      arguments.products],
               ["Test_Name",    arguments.test_names],
               ["Test_Group",   arguments.test_groups],
               ["Serial_Number",arguments.serial_numbers],
               ["Test_Script_Validation_Hash",arguments.hashes]]

    for filt in filters:
        if filt[1]:
            toFilter.append(generalQFBuilder(filt[0], filt[1], arguments.enable_regexp, F))

    if arguments.begin_date or arguments.end_date:
        toFilter.append(dateFilter("Start_Time", arguments.begin_date, arguments.end_date))

        begin = arguments.begin_date
        if arguments.begin_date == None:
            begin = date(2015,12,22)#start of testing "epoch"
        else:
            begin = begin.date()#strip time if present
        end = arguments.end_date
        if arguments.end_date == None:#not end is preferable, but doesn't work?
            end = date.today() + datetime.timedelta(days=2)#time change potential weirdness
        else:
            end = end.date()

        indexList = []
        while begin <= end:
            indexList.append("proddata-%s" % begin.strftime("%Y.%m.%d"))
            begin += datetime.timedelta(days=1)

        if toFilter:
            newBool = F("bool", must=toFilter)
        else:
            newBool = F()

        search = search.filter(F("indices",indices=indexList,no_match_filter="none",filter=newBool))

    else:
        for toFilt in toFilter:
            search = search.filter(toFilt)

    if size:
        search = search[0:size]

    return search


def generalQFBuilder(term, items, enable_regexp, method):
    if items:
        if enable_regexp:
            shoulds = []
            for item in items:
                shoulds.append(method("regexp", ** {term:item}))
            return method("bool", should=shoulds)
        else:
            return method("terms", ** {term:items})
    else:
        return method()

def dateFilter(dateField, begin_date, end_date):
    if begin_date or end_date:
        created_at = {}
        if begin_date:
            created_at['gte'] = begin_date.strftime("%Y-%m-%dT%H:%M:%S")
        if end_date:
            created_at['lte'] = end_date.strftime("%Y-%m-%dT%H:%M:%S")
        return F("range", ** {dateField:created_at})
    else:
        return F()

def listTests(arguments,es):
    search = Search(using=es)
    search = buildCommonSearch(arguments, search=search)

    productAggName = "Product_List"
    productAgg = A("terms", field="Product")
    search.aggs.bucket(productAggName,productAgg)

    testGroupAggName = "Test_Group_List"
    testGroupAgg = A("terms", field="Test_Group", size=arguments.num_results)
    search.aggs.bucket(testGroupAggName,testGroupAgg)

    testNameAggName = "Test_Name_List"
    testNameAgg = A("terms", field="Test_Name", size=arguments.num_results)
    search.aggs.bucket(testNameAggName,testNameAgg)#operates in place

    if arguments.print_query:
        print str(search.to_dict()).replace("'",'"')
        return
    else:
        results = search.execute()

    if arguments.output_file == sys.stdout:
        formatString = '{0:16}{1:24}{2}\n'#pretty output
    else:
        formatString = '{0},{1},{2}\n'#concise output

    arguments.output_file.write(formatString.format("Product","Test_Group","Test_Name"))
    for productBucket in getattr(results.aggregations,productAggName).buckets:
        for groupBucket in getattr(productBucket,testGroupAggName).buckets:
            for nameBucket in getattr(groupBucket,testNameAggName).buckets:
                arguments.output_file.write(formatString.format(productBucket.key, groupBucket.key, nameBucket.key))

def getStuff(arguments,es):
    search = Search(using=es, index='proddata-*')
    search = buildCommonSearch(arguments, search=search, size=arguments.num_results)

    if arguments.print_query:
        print str(search.to_dict()).replace("'",'"')
        return
    else:
        results = search.execute()

    data = {}
    headers = ["Serial_Number",
               "Start_Time",
               "Test_Station",
               "Test_Cell",
               "Test_Script",
               "Test_Script_Validation_Hash",
               "Total_Execution_Time",
               "Test_Result"]

    headerHash = {
            "Serial_Number":True,
               "Start_Time":True,
               "Test_Station":True,
               "Test_Cell":True,
               "Test_Script":True,
               "Test_Script_Validation_Hash":True,
               "Total_Execution_Time":True,
               "Test_Result":True}


    for result in results.hits:
        try:
            try:
                data[result['Test_Run_ID']]
            except KeyError:
                data[result['Test_Run_ID']] = {}

            data[result['Test_Run_ID']]['Serial_Number'] =                  result['Serial_Number']
            data[result['Test_Run_ID']]['Start_Time'] =                     result['Start_Time']
            data[result['Test_Run_ID']]['Test_Station'] =                   result['Test_Station']
            data[result['Test_Run_ID']]['Test_Cell'] =                      result['Test_Cell']
            data[result['Test_Run_ID']]['Test_Result'] =                    result['Test_Result']
            data[result['Test_Run_ID']]['Test_Script'] =                    result['Test_Script']
            data[result['Test_Run_ID']]['Test_Script_Validation_Hash'] =    result['Test_Script_Validation_Hash']
            data[result['Test_Run_ID']]['Total_Execution_Time'] =           result['Total_Execution_Time']

            testNum = result.meta['id'].split("_")[2]
            if arguments.very_detailed:
                nameNum = "%s_%s_%s_" % (result['Test_Name'], result['Test_Script_Validation_Hash'][-5:], testNum)
            elif arguments.detailed:
                nameNum = "%s_%s_" % (result['Test_Name'], testNum)
            else:
                nameNum = "%s_" % (result['Test_Name'])

            data[result['Test_Run_ID']][nameNum+"Status"] =                 result['Test_Status']

            try:
                headerHash[nameNum+"Status"]
            except KeyError:
                headers.append(nameNum+"Status")
                headerHash[nameNum+"Status"] = True

            if result['Measurement'] == None:
                data[result['Test_Run_ID']][nameNum+"Value"] =              result['Measurement_num']
            else:
                data[result['Test_Run_ID']][nameNum+"Value"] =              result['Measurement'].encode('utf-8')

            try:
                headerHash[nameNum+"Value"]
            except KeyError:
                headers.append(nameNum+"Value")
                headerHash[nameNum+"Value"] = True

            if arguments.enable_limits:
                try:
                    data[result['Test_Run_ID']][nameNum+"ULimit"] =             result['Upper_Limit']
                    try:
                        headerHash[nameNum+"ULimit"]
                    except KeyError:
                        headers.append(nameNum+"ULimit")
                        headerHash[nameNum+"ULimit"] = True
                except KeyError:
                    pass

                try:
                    data[result['Test_Run_ID']][nameNum+"LLimit"] =             result['Lower_Limit']
                    try:
                        headerHash[nameNum+"LLimit"]
                    except KeyError:
                        headers.append(nameNum+"LLimit")
                        headerHash[nameNum+"LLimit"] = True
                except KeyError:
                    pass

            if arguments.enable_calc_t:
                try:
                    data[result['Test_Run_ID']][nameNum+"CalcT"] =             result['Calc_runtime']
                    try:
                        headerHash[nameNum+"CalcT"]
                    except KeyError:
                        headers.append(nameNum+"CalcT")
                        headerHash[nameNum+"CalcT"] = True
                except KeyError:
                    pass
        except KeyError as e:
            print "Expected field missing in %s" % (result.meta['id'])

    csvw = csv.DictWriter(arguments.output_file, headers)
    csvw.writeheader()

    for runID in data.keys():
        csvw.writerow(data[runID])

    arguments.output_file.close()

def main():
    arguments = setupParser()
    es = Elasticsearch("54.164.33.1",timeout=600)
    if arguments.list_tests:
        listTests(arguments,es)
    else:
        getStuff(arguments,es)


if __name__ == "__main__":
    main()


