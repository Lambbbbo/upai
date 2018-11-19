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
            if re.search('ansible_ssh_host',line) and not line.startswith('#'):
                hostname = line.split()[0]
                hosts[hostname] = line.split('=')[1].split('\n')[0].split()[0]
        return hosts

def get_host_info(API,HEADERS,host):
    authID = get_auth(API,HEADERS)
    data = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "host.get",
            "params": {
                "output": ["hostid"],
                "filter": {
                    "host": [host]
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
                "output": [
                    "proxyid"
                ],
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

def create_group(API,HEADERS,group_name):
    authID = get_auth(API,HEADERS)
    data = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "hostgroup.create",
            "params":{
                "name": group_name
            },
            "auth": authID,
            "id": 1
        })
        
    request = urllib2.Request(API,data)
    for key in HEADERS:
        request.add_header(key,HEADERS[key])
    result = urllib2.urlopen(request)
    response = json.loads(result.read())
    group_id = response["result"]["groupids"][0]
    return group_id

def get_groupid(API,HEADERS,group_name):
    authID = get_auth(API,HEADERS)
    data = json.dumps(
        {
            "jsonrpc": "2.0",
            "method": "hostgroup.get",
            "params": {
                "output": ["groupid"],
                "filter": {
                    "name": [
                        group_name 
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
    groupid = response['result']
    return groupid

def create_host(API,HEADERS,NODE,lists):
    authID = get_auth(API,HEADERS)

    if NODE == "all":
        hosts = get_all_host(lists)
    else:
        hosts = {}
        with open (lists,'r') as f:
            for line in f.readlines():
                if line.startswith(NODE + "-"):
                    hostname = line.split()[0]
                    hosts[hostname] = line.split('=')[1].split('\n')[0].split()[0]      ##从list表单中，获取相应的主机名及ip

    nodes = []
    for host in hosts:
        hostid = get_host_info(API,HEADERS,host)
        if not hostid:
            nodes.append(host)      ##查询主机是否已添加，如果未添加，则记录list

    proxyid = get_proxyid(API,HEADERS)
    templateid = get_templateid(API,HEADERS)

    id = []
    for ids in proxyid:
        id.append(ids['proxyid'])     ##由于获取到的proxyid 是一个list列表，里面的每个元素是一个字典，这里将proxyid提取出来，放到id这个列表里

    p_id = cycle(id)
    p_host = {}
    for host in hosts:
        p_host[host] = next(p_id)     ##将主机平均的分配到不同的proxy上

    for node in nodes:             ##从list中遍历未添加的主机，通过api添加
        group_name = re.search(r"\D{3}\-\D{2}\-\w{3,4}",node).group()
        groupid = get_groupid(API,HEADERS,group_name)
        if not groupid:
            group_id = create_group(API,HEADERS,group_name)
        else:
            group_id = groupid[0]['groupid']
        
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
                            "groupid": group_id
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
            print "host: %s is added, hostid is %s\n" % (node,response['result']['hostids'][0])

def disable_host(API,HEADERS,NODE,lists):
    authID = get_auth(API,HEADERS)
    hosts = {}
    with open (lists,'r') as f:
        for line in f.readlines():
            if re.search(NODE + "-",line):
                hostname = line.split()[0]
                hosts[hostname] = line.split('=')[1].split('\n')[0]

    for host in hosts:
        hostid = get_host_info(API,HEADERS,host)
        id = hostid[0]['hostid']
        data = json.dumps(
            {
                "jsonrpc": "2.0",
                "method": "host.update",
                "params": {
                    "hostid": id,
                    "status": 1
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
            print "host %s is disabled." % (host)

def main():
    API = "http://10.0.2.52:8080/zabbix/api_jsonrpc.php"
    HEADERS = {"Content-type": "application/json"}
    lists = sys.argv[1]
    METHOD = sys.argv[2]
    NODE = sys.argv[3]
#    lists = "/root/upai/inventory/machines/lists-cdn-edge"

    if METHOD == "add" :
        create_host(API,HEADERS,NODE,lists)
    elif METHOD == "del":
        pass
    elif METHOD == "disable":
        disable_host(API,HEADERS,NODE,lists)
    else:
        print "Wrong method!"
            
if __name__ == '__main__':
    main()
