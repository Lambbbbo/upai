#!/bin/env python
# -*- coding: utf-8 -*-

import json
import base64
import requests
import sys
import os
import time
import datetime
from ast import literal_eval

url = "http://play.domain.yximgs.com/getdomain"
alert_url = "http://argus.x.upyun.com/api/alarm"
date = time.strftime("%Y-%m-%d", time.localtime())

if sys.getdefaultencoding() != 'utf-8':
	reload(sys)
	sys.setdefaultencoding('utf-8')


def get_iplist():
	ip_list = set()
	req = requests.get(url)
	resp = json.loads(req.content)
	for ips in resp["data"].values():
		for ip in ips:
			ip_list.add(ip)
	return ip_list


def Compare(c_iplist):
	if not os.path.exists('/root/vipcheck/ip.txt'):
		file = open('/root/vipcheck/ip.txt', 'w')
		file.close()
	with open("/root/vipcheck/ip.txt" , "r+") as f:
		old_iplist = f.read()
		if old_iplist:
			old_iplist = set(literal_eval(old_iplist))
			change_add = c_iplist - old_iplist
			change_del = old_iplist - c_iplist
			f.seek(0)
			f.truncate()
			f.write(str(list(c_iplist)))
			return change_add,change_del
		else:
			f.write(str(list(c_iplist)))
			return


def write_to_file(add, delete, full):
	with open("/root/vipcheck/record.html", 'r') as f:
		data = f.readlines()
		for i in data:
			if '新增' in i:
				idxa = data.index(i) + 2
				for a in add:
					data.insert(idxa, a + '\n')
			if '删除' in i:
				idxd = data.index(i) + 2
				for d in delete:
					data.insert(idxd, d + '\n')
			if '全部' in i:
				idxf = data.index(i) + 2
				for f in full:
					data.insert(idxf, f + '\n')

	with open("/root/vipcheck/ip.html", 'w') as fd:
		fd.writelines(data)


def upload(f):
	operator = 'ahern'
	bucket = 'ahern-file'
	password = 'ahern123123'
	cdn_url = 'http://v0.api.upyun.com/' + bucket + '/007/ip.html'
	strs = operator + ':' + password
	token = base64.b64encode(strs)
	GMT_FORMAT =  '%a, %d %b %Y %H:%M:%S GMT'
	GMT_TIME = datetime.datetime.utcnow().strftime(GMT_FORMAT)
	file_size = os.path.getsize(f)
	file_size = str(file_size)

	header = {"Authorization": "Basic " + token, "Date": GMT_TIME, "Content-Length": file_size}
	with open(f, 'rb') as f:
		req = requests.put(cdn_url, headers=header, data=f)
	print "upload code: " + str(req.status_code)


def alert(ip):
	ctime = int(time.time())
	payload = {
		"hostname": "vip_check",
		"type": "other",
		"tag": "ip",
		"name": "007_ip_change",
		"priority": 0,
		"timestamp": ctime,
		"secret_id": "9b3bff4060bd6225b8b7e4d8b30c1c68",
		"version": "v1",
		"value": ip,
		"detail": "快手调度ip发生改变，请通知各广电及时修改"
		}

	req = requests.post(alert_url, data=json.dumps(payload))
	print "alert code: " + str(req.status_code)


def main():
	c_iplist = get_iplist()
	change_add, change_del = Compare(c_iplist)
	if len(change_add) > 0:
			CIP = list(change_add)
			CIP = sorted(CIP)
			print "ip changed, add ip " + str(CIP)
			alert(CIP)
	else:
		print "no add"
	if len(change_del) > 0:
			CIP = list(change_del)
			CIP = sorted(CIP)
			print "ip changed, del ip " + str(CIP)
			alert(CIP)
	else:
		print "no del"

	c_iplist = sorted(c_iplist, reverse=True)
	write_to_file(change_add, change_del, c_iplist)	
	upload('/root/vipcheck/ip.html')


if __name__ == '__main__':
	main()
