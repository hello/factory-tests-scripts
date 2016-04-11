import os
import csv
import requests
from datetime import datetime

f = open("dustCopyPartial1.csv")
reader = csv.DictReader(f)

#fo = open("cleanDust.csv",'w')
#writer = csv.DictWriter(fo,fieldnames=["ID","dust","time"])
#writer.writeheader()
#data = []
for row in reader:
    dateObj = datetime.strptime(row["Start_Time"],"%Y-%m-%dT%H:%M:%S")
    #params = {"ID":row["ID_check_Value"],"dust":row["dust_sensor_Value"],"time":(dateObj- datetime(1970,1,1)).total_seconds()}
    if not row["Test_Result"] == "PASS":
        continue

    url = "https://admin-api.hello.is/v1/calibration"

    payload = "{\"tested_at\": %s, \"sense_id\": \"%s\", \"dust_offset\": %s}" % (str(1000*int((dateObj- datetime(1970,1,1)).total_seconds())),str(row["ID_check_Value"]),str(int(float(row["dust_sensor_Value"]))))
    headers = {
            'authorization': "Bearer %s" % os.environ['SURIPU_PROD'],
            'content-type': "application/json",
            'x-hello-admin': "postman@sayhello.com"
            }

    response = requests.request("PUT", url, data=payload, headers=headers)

    if response.text == "":
        print "Added %s" % row["ID_check_Value"]
    else:
        print response.text


f.close()
#fo.close()

