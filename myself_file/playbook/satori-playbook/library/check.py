#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import AnsibleModule
import os
import re
import json
import requests
import subprocess
import time


class Check(object):
    def __init__(self, module):
        self.module = module
        self.role = self.module.params['role']
        self.app_version = self.module.params['app_version']
        self.conf_hash = self.module.params['conf_hash']
        self.msg = ""

        self._res = [
            re.compile(r"Lua entry thread aborted"),
            re.compile(r"worker process \d+ exited on signal 11")
        ]

    def getlastline(self, fname, n=1):
        text = []
        with open(fname) as f:
            text = f.readlines()[-n:]
        return text

    def _get_status(self, port):
        try:
            resp = requests.get(
                'http://{}:{}/status'.format("127.0.0.1", port), timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "app_version": data["{0}_version".format(self.role)],
                    "conf_hash": data['conf_hash'],
                    "redis": data.get('cls:redis', [])
                }
            return
        except Exception:
            return

    def status_check(self):
        ports = {"marco": 80, "shanks": 1993, "vista": 1994}
        port = ports.get(self.role)
        if not port:
            return True
        s = self._get_status(port)
        if s is None:
            self.msg = "request {} port fail".format(port)
            return False
        if 'v{}'.format(s["app_version"]) != self.app_version:
            self.msg = "app_version is not equal"
            return False
        if s["conf_hash"] != self.conf_hash:
            self.msg = "conf_hash is not equal"
            return False
        return self.redis_check(s["redis"])

    def log_check(self):
        error_log = "/disk/ssd1/logs/{}_error.log".format(self.role)
        if not os.path.exists(error_log):
            return True
        for line in self.getlastline(error_log, 15):
            for r in self._res:
                if r.search(line):
                    self.msg = "There are error in error_log"
                    return False
        lines = int(
            subprocess.check_output(["wc", "-l", error_log]).split(" ")[0])
        time.sleep(3)
        if int(subprocess.check_output(["wc", "-l", error_log
                                        ]).split(" ")[0]) - lines > 20:
            self.msg = "There are many error logs"
            return False
        return True

    def redis_check(self, redis):
        for r in redis:
            server = r[0].get("server", "")
            if r[0].get("status", "ok") != "ok":
                self.msg = "redis {0} status is not ok".format(server)
                return False
        return True

    def nginx_check(self):
        try:
            subprocess.check_output(
                ["/usr/local/{0}/nginx/sbin/nginx".format(self.role), "-t"])
            return True
        except Exception as e:
            self.msg = "nginx -t check fail: {0}".format(str(e))
            return False

    def check(self):
        if not self.nginx_check():
            return False
        if not self.status_check():
            return False
        if not self.log_check():
            return False
        return True


def main():
    module = AnsibleModule(
        argument_spec=dict(
            role=dict(required=True),
            app_version=dict(required=True),
            conf_hash=dict(required=True)))

    c = Check(module)
    if not c.check():
        return module.fail_json(changed=False, msg=c.msg)
    return module.exit_json(changed=False)


if __name__ == "__main__":
    main()
