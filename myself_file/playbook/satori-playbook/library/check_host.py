#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import AnsibleModule
import os
import re
import commands
import requests
import json
from collections import Counter

service_list = [
		"consul",
		"consul-replicate",
		"katakuri",
		"dnsmasq",
		"falcon-agent",
		"less-server",
		"less-server-access",
		"less-server-billing",
		"less-server-sender",
		"logger",
		"nsqd",
		"purge",
		"redis-marco",
		"redis-yupoo",
		"redis-zicogo",
		"stats",
		"stunnel",
		"usopp",
		"zabbix-agent",
		"zicogo"
	]

class Host_Check(object):
	def __init__(self, module):
		self.module = module
		self.result = dict(changed=False, stdout_lines="")
	
	def disk(self):
		disk_result = dict()
		stdout = dict()
		mount = "df -Th"
		fdisk = "fdisk -l"
		bepo = """/usr/local/bepo/bc/bin/bearcache status --dev | grep '/dev/bepo' | awk '{print $1,":",$NF}'"""
		result_m = commands.getstatusoutput(mount)[1].split('\n')
		result_f = commands.getstatusoutput(fdisk)[1].split("\n")
		disk = []
		dev = re.compile('Disk.*bytes')
		for lines in result_f:
			di = dev.search(lines)
			if di:
				line = lines.split()
				size = str(line[2]) + str(line[3].strip(','))
				disk.append(size)
		AllDisk = Counter(disk)
		result_b = commands.getstatusoutput(bepo)[1].split('\n')
		stdout["bepo"] = result_b
		stdout["mount"] = result_m
		stdout["fdisk"] = AllDisk
		disk_result["disk"] = stdout
		return disk_result
		
	def os(self):
		os_result = dict()
		stdout = dict()
		tmp_dir = "ls -l /tmp"
		log_dir = "ls -ld /disk/ssd1/logs/upyun.com"
		iommu = "cat /boot/grub/grub.cfg  | grep iommu &> /dev/null"
		result_iommu = commands.getstatusoutput(tmp_dir)[0]
		result_tmp = commands.getstatusoutput(tmp_dir)[1]
		result_tmp = " ".join(result_tmp.split()[-3:])
		
		result_log = commands.getstatusoutput(log_dir)[1].split()
		if result_iommu == 0:
			iommu_status = "ok"
		else:
			iommu_status = "err"
		if "rwxrwxrw" in result_log[0] and result_log[2] == "nobody":
			logdir_status = "ok"
		else:
			logdir_status = "err"
		if result_tmp == "/tmp -> /disk/ssd1/tmp":
			tmpdir_status = "ok"
		else:
			tmpdir_status = "err"
		
		stdout["soft link /disk/ssd1/tmp"] = logdir_status
		stdout["/disk/ssd1/logs/upyun.com"] = tmpdir_status
		stdout["iommu_off"] = iommu_status
		os_result["os"] = stdout
		return os_result
	
	def service(self):
		service_result = dict()
		stdout = dict()
		supervisor = "supervisorctl status | awk '{print $1,$2}'"
		result_s = 	commands.getstatusoutput(supervisor)[1].split('\n')
		res_s = dict()
		for i in result_s:
			res_s[i.split()[0]] = i.split()[1]
		for s in service_list:
			if res_s.has_key(s):
				if res_s[s] == "RUNNING":
					res_s[s] = "ok"
				else:
					res_s[s] = "err"
			else:
				res_s[s] = "err! no such process!"
				
		result = dict()
		lvs = "ipvsadm -ln | grep '-'"
		testfile = "ls /usr/local/marco/nginx/html/test.test"
		result_l = commands.getstatusoutput(lvs)[1].split('\n')
		result_t = commands.getstatusoutput(testfile)[0]
		if result_t == 0:
			result["/usr/local/marco/nginx/html/test.test"] = "ok"
		else:
			result["/usr/local/marco/nginx/html/test.test"] = "err"
		stdout["lvs"] = result_l
		stdout["marco_testfile"] = result
		
		url = "http://127.0.0.1/status"
		response = requests.get(url)
		response = json.loads(response.content)
		comp = dict()
	
		for item in response:
			status = dict()
			if item.startswith("cls"):
				if item == "cls:hot":
					for i in response[item][0]:
						status[i["server"]] = i["status"]
				else:
					for res in response[item]:
						status[res[0]["server"]] = res[0]["status"]
				comp[item] = status
			elif item == "dyn_parents": 
				comp[item] = response[item]["value"]
		stdout["curl_result"] = comp
		stdout["supervisor"] = res_s
		service_result["service"] = stdout
		return service_result
	
	def run(self):
		stdout_lines = list()
		stdout_lines.append(self.disk())
		stdout_lines.append(self.os())
		stdout_lines.append(self.service())
		self.result["stdout_lines"] = stdout_lines
			

def main():
	module = AnsibleModule(argument_spec=dict())
	
	res = Host_Check(module)
	res.run()
	module.exit_json(**res.result)

if __name__ == '__main__':
	main()
