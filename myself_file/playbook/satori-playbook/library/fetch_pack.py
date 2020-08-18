#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) UPYUN, Inc.

import os
import time
import socket
import shutil
import hashlib
import ctypes
import json

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: fetch_pack

short_description: fetch release package

version_added: "2.4"

description:
    - "fetch release package from upyun with token secret"

options:
    name:
        description:
            - This is the message to send to the sample module
        required: true
    new:
        description:
            - Control to demo if the result of this module is changed or not
        required: false

extends_documentation_fragment:
    - azure

author:
    - Xuefeng Ding (@fengidri)
    - Monkey Zhang (@timebug)
'''

EXAMPLES = '''
- name: fetch package
  fetch_pack: "project=ohm tar=ohm-v1.0.0-2d4d00b.tar.gz dest=/tmp/ansible/"
'''

RETURN = '''
original_message:
    description: The original name param that was passed in
    type: str
message:
    description: The output message that the sample module generates
'''

class GoString(ctypes.Structure):
    _fields_ = [("p", ctypes.c_char_p), ("n", ctypes.c_longlong)]

def decrypt(dest, sofile):
    lib = ctypes.cdll.LoadLibrary(sofile)
    lib.PackDecrypt.argtypes = [GoString]
    lib.PackDecrypt.restype = GoString
    encfile = GoString(dest, len(dest))
    output = lib.PackDecrypt(encfile)
    return output.p[:int(output.n)]

def get_token_args(path, secret):
    etime = str(int(time.time()) + 86400)
    secret = secret + '&' + etime + '&' + path
    token = hashlib.md5(secret).hexdigest()[12:20] + etime
    return '?_upt=' + token

def run_module():
    # define the available arguments/parameters that a user can pass to
    # the module
    module_args = dict(
        cdn=dict(type='bool', default=False),
        dest=dict(type='str', default="/tmp/ansible"),
        project=dict(type='str', required=True),
        sofile=dict(type='str', required=True),
        bucket=dict(type='str', required=True),
        secret=dict(type='str', required=True),
        version=dict(type='str', required=True),
        component=dict(type='str', required=True),
        internal_endpoint=dict(type='list', required=True)
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        dest=''
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        return result

    cdn = module.params['cdn']
    project = module.params['project']
    dest = os.path.expanduser(module.params['dest'])

    sofile = module.params['sofile']
    bucket = module.params['bucket']
    secret = module.params['secret']
    internal_endpoint = module.params['internal_endpoint']
    component = module.params['component']
    version = module.params['version']
    version = json.loads(version.replace("'",'"'))

    ver = component + '_version'
    md5 = component + '_md5'
    
    comp_version = version[ver]
    comp_md5 = version[md5][0:7]
    tar = '{0}-{1}-{2}-{3}.tar.gz'.format(project, component, comp_version, comp_md5)

    if os.path.exists(dest):
        if os.path.isdir(dest):
            dest = os.path.join(dest, tar)
        elif os.path.isfile(dest):
            os.remove(dest)
            os.mkdir(dest)
            dest = os.path.join(dest, tar)
    else:
        os.mkdir(dest)
        dest = os.path.join(dest, tar)

    dest = dest + '.enc'
    result['dest'] = dest

    path = '/v2/%s/%s.enc' % (project, tar)

    server_domain = bucket + '.b0.upaiyun.com'
    server_ip = internal_endpoint
    args = ''

    hostname = socket.gethostname()
    if hostname.startswith('403'):
        cdn = False

    if cdn:
        args = get_token_args(path, secret)

        addr = socket.gethostbyname(server_domain)
        addr = addr + ':80'

        if hostname.startswith("MIX"):
            server_ip = [addr]
        else:
            server_ip = [addr, '183.131.178.91:80']

    result['server_ip'] = server_ip
    result['server_domain'] = server_domain

    headers = {'Host': server_domain}
    for addr in server_ip:
        url = 'http://' + addr + path + args
        result['fetch_url'] = url

        rsp, info = fetch_url(module, url, timeout=10, headers=headers)
        result['fetch_status'] = info['status']
        if info['status'] != 200:
            if addr == server_ip[-1]:
                module.fail_json(msg='Failed to fetch package', **result)
            continue

        with open(dest, 'wb') as target:
            try:
                shutil.copyfileobj(rsp, target)
            except shutil.Error as err:
                if os.path.exists(dest):
                    os.remove(dest)
                module.fail_json(msg='Failed to create target file: %s' % str(err), **result)

        rsp.close()

        if info:
            break

    output = decrypt(dest, sofile)
    if output != dest[0:-4]:
        module.fail_json(msg="Failed to decrypt package: %s" % output, **result)

    result['decrypt_output'] = output
    result['tar'] = tar
    result[ver] = comp_version

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()

