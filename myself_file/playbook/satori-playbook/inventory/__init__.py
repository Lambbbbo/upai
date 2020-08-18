#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .eneru import Eneru, EneruServiceException, EneruClientException

import argparse
import json


class InventoryCLI():
    def __init__(self, args):
        self.args = args
        self.options = None
        self.eneru = Eneru()

    def run(self):
        '''
        default print inventory list
        '''
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '-d',
            '--dump',
            dest='list_file',
            action="store",
            help="select a top group, example: CDN-EDGE or CDN-V406 ...")

        self.options = parser.parse_args()

        if self.options.list_file:
            self.fetch_topgroup(self.options.list_file)

    def fetch_topgroup(self, topgroup):
        if topgroup == "all":
            topgroups = self.eneru.gettopgroup()

            for topgroup in topgroups:
                self._fetch_topgroup(topgroup["groupname"])

        else:
            self._fetch_topgroup(topgroup)

    def _fetch_topgroup(self, topgroup):
        try:
            ret = None
            data = ""

            hosts = self.eneru.gethost(None, topgroup)
            direct_groups = self.eneru.getdirectgroup(topgroup)

            for direct_group in direct_groups:
                if not direct_group.get("virtual_ip"):
                    continue

                # add host info
                host_data = ""
                for host in hosts:
                    idx = host["hostname"].rindex("-")
                    if host["hostname"][:idx] == direct_group["groupname"]:
                        host_data += (host["hostname"] + " ansible_ssh_host=" + host["ssh_host"] + "\n")

                if host_data == "":
                    continue

                # add direct group info
                direct_group_data = ""
                direct_group_data += ('[' + direct_group["groupname"] + ']\n')
                for vip in direct_group["virtual_ip"]:
                    direct_group_data += ("#" + vip + " # VIP \n")

                # add vars info
                vars_data = ""
                if len(direct_group["vars"]) > 0:
                    for key in direct_group["vars"]:
                        vars_data += (key + "=" + str(direct_group["vars"][key]) + "\n")

                if vars_data != "":
                    vars_data =  "[" + direct_group["groupname"] + ":vars]\n" + vars_data

                data += (direct_group_data + host_data + "\n")
                if vars_data != "":
                    data += (vars_data + "\n")

            with open("./hosts/" + topgroup, 'w') as f:
                f.write(data)

        except EneruClientException as e:
            print("err - " + e.msg)
        except EneruServiceException as e:
            print("err - " + str(e.status) + " " + e.msg)
