#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import urllib2
import re
import sys
from itertools import cycle

def get_auth(API,HEADERS):
    AUTH = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "user.login",
            "params": {
                "user": "Admin",
                "password": "zabbix"
            },
            "id": 1
        })
    request = urllib2.Request(API,AUTH)
    for key in HEADERS:
        request.add_header(key,HEADERS[key])
    try:
        result = urllib2.urlopen(request)
    except URLError as e:
        print "Auth Failed, Please Check Account And Password:",e.code
    else:
        response = json.loads(result.read())
        result.close()
        authID = response['result']
        return authID

def get_all_host(lists):
    hosts = {}
    with open (lists,'r') as f:
        for line in f.readlines():
            if re.search('ansible_ssh_host',line):
                hostname = line.split()[0]
                hosts[hostname] = line.split('=')[1]
        return hosts

def get_host_info(API,HEADERS,NODE):
    authID = get_auth(API,HEADERS)
    data = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "host.get",
            "params": {
                "output": ["hostid"],
                "filter": {
                    "host": [NODE]
                    }
                },
            "id": 1,
            "auth": authID
        })
    request = urllib2.Request(API,data)
    for key in HEADERS:
        request.add_header(key,HEADERS[key])
    result = urllib2.urlopen(request)
    response = json.loads(result.read())
    result.close()
    hostid = response['result']
    return hostid

def get_proxyid(API,HEADERS):
    authID = get_auth(API,HEADERS)
    data = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "proxy.get",
            "params": {
                "output": ["proxyid"],
                "filter": {
                    "host": [
                        "DC-ZJ-HGH-12-15",
                        "DC-ZJ-HGH-12-16",
                        "DC-ZJ-HGH-12-17",
                        "DC-ZJ-HGH-12-18"
                    ]
                }
            },
            "id": 1,
            "auth": authID
        })
    request = urllib2.Request(API,data)
    for key in HEADERS:
        request.add_header(key,HEADERS[key])
    result = urllib2.urlopen(request)
    response = json.loads(result.read())
    result.close()
    proxyid = response['result']
    return proxyid

def get_templateid(API,HEADERS):
    authID = get_auth(API,HEADERS)
    data = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "template.get",
            "params": {
                "output": ["templateid"],
                "filter": {
                    "host": [
                        "Template CDN Bcache"
                    ]
                }
            },
            "id": 1,
            "auth": authID
        })
    request = urllib2.Request(API,data)
    for key in HEADERS:
        request.add_header(key,HEADERS[key])
    result = urllib2.urlopen(request)
    response = json.loads(result.read())
    result.close()
    templateid = response['result']
    return templateid

def get_groupid(API,HEADERS):
    authID = get_auth(API,HEADERS)
    data = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "hostgroup.get",
            "params": {
                "output": ["groupid"],
                "filter": {
                    "name": [
                        "CDN_edge_node"
                    ]
                }
            },
            "id": 1,
            "auth": authID
        })

    request = urllib2.Request(API,data)
    for key in HEADERS:
        request.add_header(key,HEADERS[key])
    result = urllib2.urlopen(request)
    response = json.loads(result.read())
    result.close()
    groupid = response['result']
    return groupid

def create_host(API,HEADERS,NODE,lists):
    hosts = {}
    authID = get_auth(API,HEADERS)
    with open (lists,'r') as f:
        for line in f.readlines():
            if re.search(NODE + "-",line):
                hostname = line.split()[0]
                hosts[hostname] = line.split('=')[1].split('\n')[0]      ##从list表单中，获取相应的主机名及ip

    nodes = []
    for host in hosts:
        hostid = get_host_info(API,HEADERS,host)
        if not hostid:
            nodes.append(host)      ##查询主机是否已添加，如果未添加，则记录list

    proxyid = get_proxyid(API,HEADERS)
    templateid = get_templateid(API,HEADERS)
    groupid = get_groupid(API,HEADERS)

    id = []
    for ids in proxyid:
        id.append(ids['proxyid'])     ##由于获取到的proxyid 是一个list列表，里面的每个元素是一个字典，这里将proxyid提取出来，放到id这个列表里

    p_id = cycle(id)
    p_host = {}
    for host in hosts:
        p_host[host] = next(p_id)     ##将主机平均的分配到不同的proxy上

    for node in nodes:             ##从list中遍历未添加的主机，通过api添加
        data = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "host.create",
                "params": {
                    "host": node,
                    "interfaces": [
                        {
                            "type": 1,
                            "main": 1,
                            "useip": 1,
                            "ip": hosts[node],
                            "dns": "",
                            "port": "10050"
                        }
                    ],
                    "proxy_hostid": p_host[node],
                    "groups": [
                        {
                            "groupid": groupid[0]["groupid"]
                        }
                    ],
                    "templates": [
                        {
                            "templateid": templateid[0]["templateid"]
                        }
                    ]
                },
                "auth": authID,
                "id": "1"
            })

        request = urllib2.Request(API,data)
        for key in HEADERS:
            request.add_header(key,HEADERS[key])
        try:
            result = urllib2.urlopen(request)
        except URLError as e:
            print "Error as ", e
        else:
            response = json.loads(result.read())
            print "host: %s is added, proxy by %s, hostid is %s\n" % (node,hosts[node],response['result']['hostids'][0])

def main():
    API = "http://10.0.2.52:8080/zabbix/api_jsonrpc.php"
    HEADERS = {"Content-type": "application/json"}
    METHOD = sys.argv[1]
    NODE = sys.argv[2]
    lists = "/root/lists"

    if METHOD == "add":
        if NODE == "all":
            pass
        else:
            create_host(API,HEADERS,NODE,lists)
    elif METHOD == "del":
        pass
            
if __name__ == '__main__':
    main()
