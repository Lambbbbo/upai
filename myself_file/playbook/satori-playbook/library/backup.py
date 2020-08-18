#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json

from ansible.module_utils.basic import AnsibleModule

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: backup
short_description: get backup_version from /usr/local/{{ project }}/.version
version_added: "2.4"
author: lin.jiang
'''

EXAMPLES = '''
- name: get last version from .version
  backup: role={{ project }} version={{ app_version }}-{{ conf_hash }}
'''


class Backup(object):
    def __init__(self, module):
        self.module = module
        self.prefix_path = module.params['prefix_path']
        self.role = module.params['role']
        self.update = module.params['update']
        self.replace = module.params['replace']
        self.app_version = module.params['version']
        self.current_conf = module.params['conf_hash']
        self.last_version = None

    def set_fact(self):
        app_version = json.loads(self.app_version.replace("'",'"'))
        app_version = app_version['app_version']
        current_conf = self.current_conf[0:7]
        current_version = app_version + '-' + current_conf
        facts = {}
        version_file = '{0}/{1}/.version'.format(self.prefix_path, self.role)
        if not os.path.exists(version_file):
            facts['backup_version'] = None
            version = {'current_version': current_version}
            with open(version_file, 'w') as filefd:
                filefd.write(json.dumps(version, indent=2) + '\n')
            return facts
        with open(version_file, 'r+') as filefd:
            try:
                version = json.loads(filefd.read())
            except ValueError:
                version = {'current_version': current_version}
                self.write_to_file(filefd, version)
            cur_version = version.get('current_version')
            if cur_version != current_version:
                version['backup_version'] = cur_version
                version['current_version'] = current_version
                if self.update:
                    self.write_to_file(filefd, version)
            elif version.get('backup_version') and self.replace:
                version['backup_version'] = None
                version['current_version'] = version.get('backup_version')
                self.write_to_file(filefd, version)
            facts['backup_version'] = version.get('backup_version')
        return facts

    def write_to_file(self, filefd, version):
        filefd.seek(0)
        filefd.truncate()
        filefd.write(json.dumps(version, indent=2) + '\n')


def main():
    module_args = dict(
        prefix_path=dict(
            type='str', default='/usr/local'),
        role=dict(
            type='str', required=True),
        version=dict(
            type='str', required=True),
        conf_hash=dict(
            type='str', required=True),
        update=dict(
            type='bool', default=False),
        replace=dict(
            type='bool', default=False))
    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    facter = Backup(module)
    facts = facter.set_fact()
    module.exit_json(changed=False, ansible_facts=facts)


if __name__ == "__main__":
    main()
