import sys
import requests

testkey = "C3871429299E6E8DF475AA1C8943E7888E82158A08B6042516821A8715C38415AF1A941502DF6BD40412C6435F011D20FA0F950050BE2031F7E5E658EDF01EBEC3CFBB5C251C127E4C949B7632CF8C416232530AA7CF96D86DF7148DCFF74A3ADDC76DAE6D297EAC713A284DAC50DFAF82F2C7B84F77400114159EBFE5571B96"

def write_result(txt="Fail"):
    with open("result.txt", "w+") as fw:
        fw.write(txt)
def provision(key):
    host = "https://provision.hello.is"
    path = "/v1/provision/"+key
    """
    post = ("POST /v1/provision/"+key+" HTTP/1.0\r\n\"
            "Host: provision.hello.is\r\n"
            "Content-type: text/plain\r\n"
            "Content-length: "+str(len(key))+"\r\n"
            "\r\n"
            )
            """
    resp = requests.post(host + path,
                         data = {"Host":"provision.hello.is",
                                 "Content-type":"text/plain",
                                 "Content-length":str(len(key))
                                 }
                         )
    print resp.text
    #write_result(key)


provision(testkey)
"""
if len(sys.argv) > 1:
    for arg in sys.argv:
        if len(arg.strip()) >= 256:
            provision(arg[0:256])
            exit(0)
write_result()
exit(1)

"""
