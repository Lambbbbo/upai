#!/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import copy
from ansible.module_utils.basic import AnsibleModule

ENERU_API = "http://eneru.x.upyun.com/v1/inventory/"
ApiKey = "ertsBIgtWqgieH4gdHzOMrthRjZUsuGh"

class get_var(object):
	def __init__(self, module, metadata):
		self.module = module
		self.facts = metadata
		self.action = self.module.params["action"]
		self.hostid = self.module.params["hostid"]
		self.clusterid = self.module.params["clusterid"]
		self.cluster_API = ENERU_API + "clusters/" + self.clusterid + "/hosts"

	def upstream(self):
		facts = {}
		host_list = self.hostid.split(",")
		headers = {"x-eneru-apikey": ApiKey}
		req_allhost = requests.get(self.cluster_API, headers=headers)
		
		p_ip = []
		for host in host_list:
			host_API = ENERU_API + "hosts/" + host
			req_host = requests.get(host_API, headers=headers)
			res = json.loads(req_host.content)
			p_ip.append(res["private_ipaddrs"])
		facts["target_host"] = p_ip 					#获取target_host的私网ip
		
		result = json.loads(req_allhost.content)
		p_ips = []
		for host in result["items"]:
			private_ip = host["private_ipaddrs"]
			p_ips.append(private_ip)					#获取当前集群内机器的私网ip
		
		NGINX_UPSTREAM = copy.copy(p_ips)
		for i in p_ip:
			if self.action == "del":
				try:
					NGINX_UPSTREAM.remove(i)					
				except ValueError:
					return dict(failed=True, msg='target_host %s not in upstream now' % (i))
			elif self.action == "add":
				if i not in p_ips:
					NGINX_UPSTREAM.append(i)					
		
			
		facts["NGINX_UPSTREAM"] = NGINX_UPSTREAM

		return facts
	
	def lvs(self):
		facts = {}
		host_list = self.hostid.split(",")	
		headers = {"x-eneru-apikey": ApiKey}
		cluster_info = ENERU_API + "clusters/" + self.clusterid
		req_vip = requests.get(cluster_info, headers=headers)
		
		pub_ips = []
		for host in host_list:
			host_API = ENERU_API + "hosts/" + host
			req_host = requests.get(host_API, headers=headers)
			res = json.loads(req_host.content)
			for public_ip in res["public_ipaddrs"]:
				pub_ips.append(public_ip["addr"]) 		#获取target_host的公网ip
		facts["PUBLIC_IP"] = pub_ips 		  	
		
		req_hosts = requests.get(self.cluster_API, headers=headers)
		result = json.loads(req_hosts.content)
		r_ips = []
		
		for host in result["items"]:
			for h in host["public_ipaddrs"]:
				r_ips.append(h["addr"])			#获取当前集群内机器的公网ip
		facts["REAL_HOSTS"] = r_ips
		
		res_vip = json.loads(req_vip)
		vip_list = {}
		for vip in res_vip["public_ipaddrs"]:
			vip_list[vip[addr]] = vip[netmask]
		facts["VIP"] = vip_list
		
		return facts
			
		
class Fetch(object):
	def __init__(self, module):
		self.module = module
		self.facts = {}
		self.info = self.module.params["info"]
		
	def run(self):
		meta = get_var(self.module, self.facts)
		if hasattr(meta, self.info):
			self.facts.update(**getattr(meta, self.info)())

def main():
	module = AnsibleModule(argument_spec=dict(
		hostid=dict(required=True),
		clusterid=dict(required=True),
		action=dict(default=None),
		info=dict(required=True)))
	
	fetch = Fetch(module)
	fetch.run()

	module.exit_json(changed=False, ansible_facts=fetch.facts)

if __name__ == '__main__':
	main()
