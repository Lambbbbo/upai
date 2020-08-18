#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) UPYUN, Inc.

from ansible.plugins.action import ActionBase
import os
import requests
import json
import random
import string

# ENERU API
# ENERU_API = "http://eneru.test.s.upyun.com"
ENERU_API = "http://eneru.x.upyun.com"

# Config
CONFIG = {
    "bucket": "harmless",
    "secret": "4wE7gDGejkbQCD",
    "internal_endpoint": [
        "kuzan.upyun.local:3110"
    ]
}

class ActionModule(ActionBase):
    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=None):
        new_module_args = self._task.args.copy()
        new_module_args.update(CONFIG)

        #get personal token
        upssh_file = os.environ['HOME'] + "/.upssh.json"
        try:
            with open(upssh_file, 'r') as f:
                content = f.read()
            E_Token = json.loads(content)['token']
        except IOError:
            return dict(failed=True, msg='file %s not exist!' % (upssh_file))

        if E_Token == '-':
            E_Token = os.getenv('UPSSH_TOKEN')

        #get libenc.so and store to /tmp/
        headers = {"X-Eneru-Token": E_Token}
        c_project = new_module_args['project']
        component = new_module_args['component']
        version = new_module_args['version']
        ran_str = ''.join(random.sample(string.ascii_letters + string.digits, 8))
        so_name = c_project + "-" + component + "-" + ran_str + ".so"
        file_path = os.path.join("/tmp/",so_name)

        ver = component + '_version'
        md5 = component + '_md5'

        tag_name = version[ver]
        app_md5 = version[md5]
        url = ENERU_API + '/v1/release/decrypt/so?project_name=' + c_project + '&component_name=' + component + '&tag_name=' + tag_name + '&md5=' + app_md5

        res = requests.get(url, headers=headers)
        if res.status_code // 100 != 2:
            return dict(failed=True, msg="fetch so file Failed! code: %s" % (res.status_code))
        else:
            with open(file_path, 'wb+') as f:
                f.write(res.content)

        #transfer local libenc.so to remote tmp directory
        if tmp is None or "-tmp-" not in tmp:
            tmp = self._make_tmp_path()

        tmp_src = self._connection._shell.join_path(tmp, so_name)
        self._transfer_file(file_path, tmp_src)
        new_module_args.update(dict(sofile=tmp_src, ))

        result = self._execute_module(
            module_name='fetch_pack',
            module_args=new_module_args,
            tmp=tmp,
            task_vars=task_vars)

        #cleanup libenc.so both on local and remote
        self._remove_tmp_path(tmp)
        os.remove(file_path)
        return result
