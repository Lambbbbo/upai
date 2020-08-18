#!/bin/env python
# -*- coding: utf-8 -*-

import socket
import requests
import json
import copy
import hashlib
import struct
import array
import fcntl
from ansible.module_utils.basic import AnsibleModule

ENERU_API = "http://eneru.x.upyun.com/v1/inventory/"
ApiKey = "ertsBIgtWqgieH4gdHzOMrthRjZUsuGh"
SIOCGIFCONF = 0x8912
SIOCGIFADDR = 0x8915


class NetInterface(object):
	def __init__(self):
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

	def get_interfaces(self):
		ifreq_size = 24 + 2 * len(struct.pack('P', 0))
		max_possible = 128
		byte = max_possible * ifreq_size

		ifreq_buf = array.array('B', '\0' * byte)
		ifconf = struct.pack('iP', byte, ifreq_buf.buffer_info()[0])
		result = fcntl.ioctl(self.socket.fileno(), SIOCGIFCONF, ifconf)
		ifc_len, _ = struct.unpack('iP', result)

		devs = []
		for i in range(0, ifc_len, ifreq_size):
			ifr_name = (ifreq_buf.tostring()[i:i + ifreq_size])[:16]
			name = ifr_name.split('\0', 1)[0]
			devs.append(name)
		return devs

	def get_ip(self, ifname):
		ifreq = struct.pack('16sH14s', ifname, 0, '')
		ret = fcntl.ioctl(self.socket.fileno(), SIOCGIFADDR, ifreq)
		addr = struct.unpack('16sH14B', ret)[4:8]
		ipaddr = "%d.%d.%d.%d" % (addr)
		return ipaddr

	@classmethod
	def is_private(cls, ipaddr):
		fpack = struct.unpack('!I', socket.inet_pton(socket.AF_INET,
                                                     ipaddr))[0]
		private = ([2130706432, 4278190080],  # 127.0.0.0,   255.0.0.0
					[3232235520, 4294901760],  # 192.168.0.0, 255.255.0.0
					[2886729728, 4293918720],  # 172.16.0.0,  255.240.0.0
					[167772160, 4278190080])  # 10.0.0.0,    255.0.0.0

		for net in private:
			if (fpack & net[1]) == net[0]:
				return True
		return False


	def get_netmask(self, ifname):
		ifreq = struct.pack('256s', ifname)
		ret = fcntl.ioctl(self.socket, 35099, ifreq)
		netmask = socket.inet_ntoa(ret[20:24])
		return netmask

	@classmethod
	def bits_to_netmask(cls, bits):
		# return '.'.join([str((0xffffffff << (32 - bits) >> i) & 0xff) for i in [24, 16, 8, 0]])
		return socket.inet_ntoa(
			struct.pack(">I", (0xffffffff << (32 - bits)) & 0xffffffff))

	@classmethod
	def netmask_to_bits(cls, netmask):
		return sum([bin(int(x)).count('1') for x in netmask.split('.')])

	def collect(self):
		data = {}
		for ifname in self.get_interfaces():
			ipaddr = self.get_ip(ifname)
			netmask = self.get_netmask(ifname)

			data[ifname] = {
				'ip': ipaddr,
				'private': self.is_private(ipaddr),
				'netmask': netmask,
				'netmask_bits': self.netmask_to_bits(netmask)
			}

		return data


class get_var(object):
	def __init__(self, module, metadata ,hostids, cluster_id, net_interface):
		self.module = module
		self.facts = metadata
		self.action = self.module.params["action"]
		self.hostids = hostids
		self.cluster_id = cluster_id
		self.network = net_interface

	def get_current_hostinfo(self):
		facts = {}
		PRIVATE_IP = []
		headers = {"x-eneru-apikey": ApiKey}
		Current_Hostname = self.facts["HOSTNAME"]
		Current_URL = "{0}hosts?page=1&filter_by=hostname%2C{1}".format(ENERU_API,Current_Hostname)
		Current_Req = requests.get(Current_URL, headers=headers)
		Current_Resp = json.loads(Current_Req.content)
		PRIVATE_IP.append(Current_Resp['items'][0]["private_ipaddrs"])
		facts['LVS_MASTER'] = Current_Resp['items'][0].get('vars').get('LVS_MASTER','')
		facts["PRIVATE_IP"] = PRIVATE_IP
		facts['IS_HONGKONG'] = False
		facts['OVERSEAS'] = False
		if Current_Hostname.startswith('NTT-CN-HKG') or Current_Hostname.startswith('PCW-CN-HKG'):
			facts['IS_HONGKONG'] = True
		if Current_Resp['items'][0]['room']['CountryID'] != 1:
			facts['OVERSEAS'] = True
		facts["DIRECT_TRANSFER"] = True if Current_Resp['items'][0].get('vars').get('DIRECT_TRANSFER','') == 'Y' else False
		facts["REDIS_MARCO_PORT"] = Current_Resp['items'][0].get('vars').get('REDIS_MARCO_PORT',1020)
		roomid = Current_Resp["items"][0]["room"]["id"]
		ROOMURL = "{0}rooms/{1}".format(ENERU_API,roomid)
		res = requests.get(ROOMURL, headers=headers)
		result = json.loads(res.content)
		if result["country"]["id"] == 1:
			country_name = result["country"]["country_name"][:2]
		else:
			country_name = result["country"]["country_name"]
		facts["COUNTRY"] = country_name
		if result["isp"]["id"] in [1,2,3]:
			isp_name = result["isp"]["isp_name"][-2:]
		else:
			isp_name = result["isp"]["isp_name"]
		facts["PROVINCE"] = result["province"]["province_name"]
		facts["ISP"] = isp_name

		return facts

	def upstream(self):
		'''
		获取私网ip形成upstream，bepo for marco专用
		'''

		facts = self.get_current_hostinfo()
		headers = {"x-eneru-apikey": ApiKey}

		'''
		get target host private_ip
		'''
		p_ip = []
		for host in self.hostids:
			host_API = ENERU_API + "hosts/" + host
			req_host = requests.get(host_API, headers=headers)
			res = json.loads(req_host.content)
			p_ip.append(res["private_ipaddrs"])
		facts["target_host"] = p_ip

		p_ips = []
		'''
		get current cluster upstream
		'''
		CluInfoApi = "{0}clusters/{1}/hosts".format(ENERU_API,self.cluster_id)
		CluHostInfo = requests.get(CluInfoApi, headers=headers)
		resp_CluHostInfo = json.loads(CluHostInfo.content)
		p_ips = [
			i["private_ipaddrs"]
			for i in resp_CluHostInfo["items"] if i.get("vars").get('_Role_bearcache_','false') == 'true' or '-' in i.get("vars").get('_Role_bearcache_','false')
			]

		facts["OLD_NGINX_UPSTREAM"] = p_ips
		NGINX_UPSTREAM = copy.copy(p_ips)
		for i in p_ip:
			if self.action == "del":
				if len(NGINX_UPSTREAM) == 1:
					NGINX_UPSTREAM = [ i for i in self.facts["PRIVATE_IP"] ]
				else:
					try:
						NGINX_UPSTREAM.remove(i)
					except ValueError:
						return dict(failed=True, msg='target_host %s not in upstream now' % (i))
			elif self.action == "add":
				if i not in p_ips:
					NGINX_UPSTREAM.append(i)

		j = 1
		string = ""
		string1 = ""
		for x in NGINX_UPSTREAM:
			string += x + "#" + str(j) + " "
			string1 += x + "#" + str(50) + " "
			j += 1
		facts["NGINX_UPSTREAM"] = NGINX_UPSTREAM
		facts["NGINX_UPSTREAM_EXTENSION"] = ""
		facts["NGINX_UPSTREAM_DOWN"] = ""
		facts["STRING"] = string[:-1]
		facts["STRING1"] = string1[:-1]
		facts["NGINX_UPSTREAM_WEIGHT"] = [
			(i.split('#')[-2],i.split('#')[-1])
			for i in string1[:-1].split()
		]

		return facts

	def keepalived(self):
		'''
		获取公网ip及vip
		'''
		facts = self.get_current_hostinfo()
		headers = {"x-eneru-apikey": ApiKey}
		cluster_info = ENERU_API + "clusters/" + self.cluster_id

		'''
		get target host public ip
		'''
		pub_ip = []
		for host in self.hostids:
			host_API = ENERU_API + "hosts/" + host
			req_host = requests.get(host_API, headers=headers)
			res = json.loads(req_host.content)
			pub_ip.append(res["ssh_host"])
		facts["target_host"] = pub_ip

		'''
		get target cluster info like VIP,netmask,lvs_port
		'''
		vip_list = list()
		vip_mask = set()
		CluInfo = requests.get(cluster_info, headers=headers)
		RespCluInfo = json.loads(CluInfo.content)
		lvs_ports = RespCluInfo.get("vars").get("LVS_PORTS","0")
		for vip in RespCluInfo["public_ipaddrs"]:
			vip_list.append(vip["addr"])
			vip_mask.add(vip["netmask"])
		vip_mask = list(vip_mask)

		'''
		get vip bonding netcard
		'''
		ip_map = { x:self.network[x]['ip'] for x in self.network }
		vip_network = '.'.join(vip_list[0].split('.')[0:-1])
		for card,n in ip_map.items():
			if '.'.join(n.split('.')[0:-1]) == vip_network:
				if ':' not in card:
					facts['LVS_DEV'] = card

		'''
		get current host public ip address which is in the cluster
		'''
		CluInfoApi = "{0}clusters/{1}/hosts".format(ENERU_API,self.cluster_id)
		CluHostInfo = requests.get(CluInfoApi, headers=headers)
		resp_CluHostInfo = json.loads(CluHostInfo.content)
		pub_ips = []
		for pip in resp_CluHostInfo['items']:
			if pip.get('vars').get('_Role_marco_','false') == 'true' or '-' in pip.get('vars').get('_Role_marco_','false'):
				pub_ips.append(pip['ssh_host'])
		lvss = []
		for lvs in resp_CluHostInfo['items']:
			if lvs.get('vars').get('_Role_keepalived_','false') == 'true' or '-' in lvs.get('vars').get('_Role_keepalived_','false'):
				lvss.append(lvs['hostname'])

		'''
		generate new real ip list
		'''
		real_hosts = copy.copy(pub_ips)
		for i in pub_ip:
			if self.action == "del":
				try:
					real_hosts.remove(i)
				except ValueError:
					return dict(failed=True, msg='target_host %s not in lvs real hosts now' % (i))
			elif self.action == "add":
				if i not in pub_ips:
					real_hosts.append(i)

		lvs_groups = [{
			"vip": vip_list,
			"real_ip": real_hosts,
			"mask": vip_mask[0],
			"port": int("858" + lvs_ports)
		}]

		facts['LVS_GROUPS'] = lvs_groups
		facts['LVS_VIRTUAL_ID'] = 100
		j = 1
		x1 = ""
		y1 = ""
		for x in vip_list:
			if j < len(vip_list):
				x1 += x + ','
			else:
				x1 += x
			j += 1
		facts['LVS_VIP'] = x1
		z = 1
		for y in real_hosts:
			if z < len(real_hosts):
				y1 += y + ','
			else:
				y1 += y
			z += 1	
		facts['LVS_HOSTS'] = y1
		PRI = 300 - int(facts['PRIVATE_IP'][0].split('.')[-1])
		facts['FIRST_CONFIG'] = ""
		if len(lvss) == 0:
			facts['FIRST_CONFIG'] = "Y"
		facts['LVS_PRIORITY'] = PRI
		facts['LVS_MASK'] = vip_mask[0]
		if len(lvs_groups) > 0:
			vips = sorted(lvs_groups[0]["vip"])
			s = hashlib.sha1(vips[0].encode()).hexdigest()
			facts['LVS_VIRTUAL_ID'] = int(s, 16) % (10**2)

		facts['LVS_PORTS'] = list(lvs_ports)
		facts['LVS_FWMARK'] = True if "0" in lvs_ports else False
		facts['LVS_FWMARK_ONLY'] = True if ["0"] == list(lvs_ports) else False

		return facts

	def redis(self):
		'''
		获取私网ip形成upstream
		'''

		facts = self.get_current_hostinfo()
		headers = {"x-eneru-apikey": ApiKey}

		'''
		get target host private_ip
		'''
		p_ip = []
		for host in self.hostids:
			host_API = ENERU_API + "hosts/" + host
			req_host = requests.get(host_API, headers=headers)
			res = json.loads(req_host.content)
			p_ip.append(res["private_ipaddrs"])
		facts["target_host"] = p_ip
		
		'''
		get current redis cluster upstream
		'''
		CluInfoApi = "{0}clusters/{1}/hosts".format(ENERU_API,self.cluster_id)
		CluHostInfo = requests.get(CluInfoApi, headers=headers)
		resp_CluHostInfo = json.loads(CluHostInfo.content)
		p_ips = [
			i["private_ipaddrs"]
			for i in resp_CluHostInfo["items"] if i.get("vars").get('_Role_redis_','false') == 'true' or '-' in i.get("vars").get('_Role_redis_','false')
			]
		
		REDIS_UPSTREAM = copy.copy(p_ips)
		for i in p_ip:
			if self.action == "del":
				if len(REDIS_UPSTREAM) == 1:
					REDIS_UPSTREAM = [ i for i in self.facts["PRIVATE_IP"] ]
				else:
					try:
						REDIS_UPSTREAM.remove(i)
					except ValueError:
						return dict(failed=True, msg='target_host %s not in upstream now' % (i))
			elif self.action == "add":
				if i not in p_ips:
					REDIS_UPSTREAM.append(i)
		j = 1
		string = ""
		for x in REDIS_UPSTREAM:
			string += x + "#" + str(j) + " "
			j += 1
		facts['REDIS_UPSTREAM'] = REDIS_UPSTREAM
		facts["STRING"] = string[:-1]
		return facts

	def zicogo(self):
		'''
		获取私网ip形成upstream
		'''

		facts = self.get_current_hostinfo()
		headers = {"x-eneru-apikey": ApiKey}

		'''
		get target host private_ip
		'''
		p_ip = []
		for host in self.hostids:
			host_API = ENERU_API + "hosts/" + host
			req_host = requests.get(host_API, headers=headers)
			res = json.loads(req_host.content)
			p_ip.append(res["private_ipaddrs"])
		facts["target_host"] = p_ip
		
		'''
		get current redis cluster upstream
		'''
		CluInfoApi = "{0}clusters/{1}/hosts".format(ENERU_API,self.cluster_id)
		CluHostInfo = requests.get(CluInfoApi, headers=headers)
		resp_CluHostInfo = json.loads(CluHostInfo.content)
		p_ips = [
			i["private_ipaddrs"]
			for i in resp_CluHostInfo["items"] if i.get("vars").get('_Role_zicogo_','false') == 'true' or '-' in i.get("vars").get('_Role_zicogo_','false')
			]
		
		ZICOGO_UPSTREAM = copy.copy(p_ips)
		for i in p_ip:
			if self.action == "del":
				if len(ZICOGO_UPSTREAM) == 1:
					ZICOGO_UPSTREAM = [ i for i in self.facts["PRIVATE_IP"] ]
				else:
					try:
						ZICOGO_UPSTREAM.remove(i)
					except ValueError:
						return dict(failed=True, msg='target_host %s not in upstream now' % (i))
			elif self.action == "add":
				if i not in p_ips:
					ZICOGO_UPSTREAM.append(i)
		j = 1
		string = ""
		for x in ZICOGO_UPSTREAM:
			string += x + "#" + str(j) + " "
			j += 1
		facts['ZICOGO_UPSTREAM'] = ZICOGO_UPSTREAM
		facts["STRING"] = string[:-1]

		return facts

class Fetch(object):
	def __init__(self, module):
		self.module = module
		self.facts = {'HOSTNAME': socket.gethostname()}
		self.info = self.module.params["info"]

	def get_target_hostinfo(self):
		headers = {"x-eneru-apikey": ApiKey}
		hosts = self.module.params["host"]
		lists = hosts.split(',')
		cluster = self.module.params["cluster"]
		hostids = []
		for HOSTNAME in lists:
			HOSTURL = "{0}hosts?page=1&filter_by=hostname%2C{1}".format(ENERU_API,HOSTNAME)
			req = requests.get(HOSTURL, headers=headers)
			resp = json.loads(req.content)
			hostid = str(resp["items"][0]["id"])
			hostids.append(hostid)

		clu_url = "{0}clusters?page=1&filter_by=cluster_name%2C{1}".format(ENERU_API,cluster)
		r = requests.get(clu_url, headers=headers)
		re = json.loads(r.content)
		for i in re["items"]:
			if i["cluster_name"] == cluster:
				cluster_id = str(i["id"])
		return hostids,cluster_id

	def run(self):
		net_if = NetInterface()
		net_interface = net_if.collect()
		self.facts['NET_INTERFACE'] = net_interface
		hostids,clusterid = self.get_target_hostinfo()
		meta = get_var(self.module, self.facts, hostids, clusterid, net_interface)
		if hasattr(meta, self.info):
			self.facts.update(**getattr(meta, self.info)())

def main():
	module = AnsibleModule(argument_spec=dict(
		host=dict(required=True),
		cluster=dict(required=True),
		action=dict(required=True),
		info=dict(required=True)))

	fetch = Fetch(module)
	fetch.run()
	module.exit_json(changed=False, ansible_facts=fetch.facts)

if __name__ == '__main__':
	main()
