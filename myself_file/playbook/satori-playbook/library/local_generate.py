#!/bin/env python
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: collect_conf
version_added: "beta"
short_description: Do not rely on
description:
    - get group ipv4 addr
options:
  role:
    description:
      - consul
      - consul-replicate
      - less-server
      - less-logger
    required: False
    default: all
    aliases: []
author: 79
update: 2017-12-51
'''

EXAMPLES = '''
get infomation of container named example

- hosts: upyun_host
  tasks:
  - name: get group ipv4 addr
    local_action: collect_conf groups={{ group_names }} lists={{ inventory_file }} 
'''

import json
import re
from ansible.module_utils.basic import *
from ansible.module_utils.facts import *

class UpyunLocalConf:
    def __init__(self,module):
        self.module = module
        self.groups = self.module.params.get('groups')
        self.lists = self.module.params.get('lists')
        self.addr = self.module.params.get('addr')

    def get_group_names(self):
        groups = self.groups.split("'")[1]
        return groups

    def get_group_list(self,g):
        s = re.compile(str(g) + '-')
	groups = []
        temp_groups = []
        with open(self.lists,'r') as f:
            for lines in f.readlines():
                m = s.search(lines)
                if m != None:
                    temp_groups.append(lines)
	n = re.compile("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
        for l in temp_groups:
		e = n.search(l)
		if e != None:
			vl = l.split()[0]
			groups.append(vl.strip('\n'))
			
        return groups

    def get_private_list(self,groups):
        private = []
        pr = self.addr.split('.')
        for ips in groups:
            pa = ips.split('-')
            i = "%s.%s.%s.%s" % (pr[0],pr[1],pr[2],int(pa[3]))
            private.append(i)
        return private

    def get_group_numbers(self,g):
        return len(g)

    def run(self):
        vars = dict()
        g = self.get_group_names()
	groups = self.get_group_list(g)
        vars['datacenter_dc'] = g.lower()
        vars['consul_join'] = self.get_private_list(groups)
	vars['datacenter_number'] = self.get_group_numbers(groups)
       
        return vars


def main():
    module = AnsibleModule(
        argument_spec = dict(
            groups = dict(default='', type='str'),
            lists = dict(default='', type='str'),
            addr = dict(default='', type='str'),
        ),
        supports_check_mode=True
    )

    try:
        facter = UpyunLocalConf(module)
        facts = facter.run()
        module.exit_json(changed=False, ansible_facts=facts)

    except Exception, e:
        module.fail_json(changed=False, msg=repr(e))

if __name__ == "__main__":
    main()
