#!/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import copy
import socket
import os
from ansible.module_utils.basic import AnsibleModule

ENERU_API = "http://eneru.x.upyun.com/v1/inventory/"
ApiKey = "ertsBIgtWqgieH4gdHzOMrthRjZUsuGh"
headers = {"x-eneru-apikey": ApiKey}

class fetch_meta(object):
	def __init__(self, module, content, metadata):
		self.module = module
		self.content = content
		self.facts = metadata

	def default(self):
		'''
		#获取target_host的基础信息，如ip信息，
		'''
		facts = {}
		data = self.content
		facts["NGINX_UPSTREAM"] = [ data.get('private_ipaddrs', '') ]
		facts["PUBLIC_IP"] = [
			i["addr"] for i in data.get('public_ipaddrs', '')
		]
		for k,v in data["vars"].items():
			facts[k] = v
		return facts
	
	def marco(self):
		facts = self.default()
		data = self.content
		roomid = data["roomid"]
		platformid = data["platformid"]
		ROOMURL = "{0}rooms/{1}".format(ENERU_API,roomid)
		res = requests.get(ROOMURL, headers=headers)
		resp = json.loads(res.content)
		if resp["country"]["id"] == 1:
			country_name = resp["country"]["country_name"][:2]
		facts["COUNTRY"] = country_name

		if resp["isp"]["id"] in [1,2,3]:
			isp_name = resp["isp"]["isp_name"][-2:]
		else:
			isp_name = resp["isp"]["isp_name"]

		facts["PROVINCE"] = resp["province"]["province_name"]
		facts["ISP"] = isp_name
		if resp["country"]["id"] == 1:
			if platformid == 20:
				facts["ISP_ABBR"] = "SCNR"
			elif platformid == 22:
				facts["ISP_ABBR"] = "SCND"
			else:
				if resp["isp"]["id"] == 1:
					facts["ISP_ABBR"] = "CTC"
				elif resp["isp"]["id"] == 2:
					facts["ISP_ABBR"] = "CMC"
				elif resp["isp"]["id"] == 3:
					facts["ISP_ABBR"] = "CNC"
				else:
					facts["ISP_ABBR"] = "ORG"
		else:
			facts["ISP_ABBR"] = "ABROAD"

		
		def _read_speed(sf):
			s = 20000 * 1024 * 1024 / 8
			try:
				with open(sf) as f:
					speed = int(f.read())
					if speed > 0:
						s = speed * 1024 * 1024 / 8
				return s
			except Exception as e:
				return s

		speed_file = "/sys/class/net/bond0/speed"
		if os.path.exists(speed_file):
			facts['NIC_SPEED'] = _read_speed(speed_file)
			return facts

		eth0 = 0
		eth1 = 0
		speed_file = "/sys/class/net/eth0/speed"
		if os.path.exists(speed_file):
			eth0 = _read_speed(speed_file)

		speed_file = "/sys/class/net/eth1/speed"
		if os.path.exists(speed_file):
			eth1 = _read_speed(speed_file)

		if eth0 or eth1:
			facts['NIC_SPEED'] = eth0 + eth1

		
		return facts

class Fetch(object):
	def __init__(self, module):
		self.module = module
		self.facts = {'HOSTNAME': socket.gethostname()}
		self.project = self.module.params["project"]

	def get_info(self):
		HOSTNAME = socket.gethostname()
		HOSTURL = "{0}hosts?page=1&filter_by=hostname%2C{1}".format(ENERU_API,HOSTNAME)
		req = requests.get(HOSTURL, headers=headers)
		resp = json.loads(req.content)
		hostid = str(resp["items"][0]["id"])
		roomid = str(resp["items"][0]["room"]["id"])
		host_API = ENERU_API + "hosts/" + hostid
		req_host = requests.get(host_API, headers=headers)
		result = json.loads(req_host.content)
		result["roomid"] = roomid
		platformid = resp["items"][0]["platform"]["id"]
		result["platformid"] = platformid
		return result

	def run(self):
		data = self.get_info()
		meta = fetch_meta(self.module, data, self.facts)
		if hasattr(meta, self.project):
			self.facts.update(**getattr(meta, self.project)())

def main():
	module = AnsibleModule(argument_spec=dict(
		project=dict(required=True),
		mode=dict(default=None)))

	fetch = Fetch(module)
	fetch.run()

	module.exit_json(changed=False, ansible_facts=fetch.facts)

if __name__ == '__main__':
	main()
