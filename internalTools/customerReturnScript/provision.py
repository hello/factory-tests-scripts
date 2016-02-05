import sys
import re
import json
import requests

testkey = "C3871429299E6E8DF475AA1C8943E7888E82158A08B6042516821A8715C38415AF1A941502DF6BD40412C6435F011D20FA0F950050BE2031F7E5E658EDF01EBEC3CFBB5C251C127E4C949B7632CF8C416232530AA7CF96D86DF7148DCFF74A3ADDC76DAE6D297EAC713A284DAC50DFAF82F2C7B84F77400114159EBFE5571B96"

testdevice = "2824EFFEAA492BB7"
auth = "20.d36a0205969b462ca8872b06c29d915a"

def write_result(devid, sn, key, result = "FAIL"):
	with open("result.txt", "w+") as fw:
		fw.write( "%s\n%s\n%s"%(result, sn, key) )
	print result

def provision(sn, key):
	res = requests.post("https://provision.hello.is/v1/provision/%s"%(sn), data = key)
	if res.status_code == 200:
		return True
	return False

def _extract_sn(text):
	KEY_REGEX = u"\d{8}[WB](\w{1})\d{11}"
	attri = json.loads(text)
	sn = attri['metadata']
	match = re.search(KEY_REGEX, sn)
	if match:
		idx = match.start(1)
		return sn[:idx] + "R" + sn[idx+1:]
	return None

def get_new_sn(devid):
	r = requests.get('https://admin-api.hello.is/v1/key_store/sense/%s'%(devid), headers = {'Authorization': 'Bearer %s'%(auth)})
	if r.status_code == 200:
		sn = _extract_sn(r.text)
		return sn
	else:
		return None

def verify_key(k):
	PATTERN = u"^[0-9A-F]{256}$"
	if re.match(PATTERN, k):
		return k
	return None


test = False
if len(sys.argv) > 2 or test == True:
	new_dev = ""
	if test:
		new_dev = testdevice
		new_sn = get_new_sn(new_dev)
		new_key = verify_key(testkey)
	else:
		new_dev = sys.argv[1].strip()
		new_sn = get_new_sn(new_dev).strip()
		new_key = verify_key(sys.argv[2])
	if new_sn and new_key and provision(new_sn, new_key):
		write_result(new_dev, new_sn, new_key, "PASS")
		exit(0)

write_result(new_dev, sys.argv, "", result ="FAIL")
exit(1)
	
