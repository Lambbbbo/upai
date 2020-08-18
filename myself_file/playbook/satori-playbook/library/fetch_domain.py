#!/bin/env python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import AnsibleModule
import os

def fetch(module):
	facts = {}
	domain = []
	workdir = "/usr/local/coredns/etc/"
	for i in os.listdir(workdir):
		if not i == "coredns.conf":
			file = os.path.join(workdir,i)
			with open(file, "r+") as f:
				for line in f.read().splitlines():
					domain.append(line)
	
	facts["domain"] = domain
	return facts
	 
def main():
	module = AnsibleModule(argument_spec=dict())
	facts = fetch(module)	
	module.exit_json(changed=False, ansible_facts=facts)
	
if __name__ == '__main__':
	main()
