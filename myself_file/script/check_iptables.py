#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import commands

def get_lvs(U_CONF):
    LVS = {}

    with open(U_CONF,'r') as f:
        contents = f.readlines()
        for line in contents:
           if line.startswith("LVS"):
               KEY = line.split('=')[0]
               VALUE = line.split('=')[1].split()[0].strip('"').split(',')
               LVS[KEY] = VALUE  
    return LVS

def get_master(K_CONF):
    
    with open(K_CONF ,'r') as f:
        for line in f.readlines():
            if re.search("state",line):
                master = line.split()[-1]
    return master

def conversion(values):
    ips = []
    if values:
        for a in values.split('\n'):
            v = a.split()
            ips.append([v[4],v[-1]])

    return ips

def exec_comm(comm):
    values = commands.getoutput(comm)
    return values

def make_comm(rules,dip=None,mask=None):
    com = ''
    dc = { "comm": "/sbin/iptables", 
            "table": "mangle",
            "chain": "PREROUTING",
            "rules": "-p tcp  -j MARK --set-mark" }

    if rules == "A":
        com = "%s -t %s -A %s -d %s %s %s" % (dc['comm'],dc['table'],dc['chain'],str(dip),dc['rules'],str(mask))
    elif rules == "D":
        com = "%s -t %s -D %s -d %s %s %s" % (dc['comm'],dc['table'],dc['chain'],str(dip),dc['rules'],str(mask))
    elif rules == "F":
        com = "%s -t %s -F" % (dc['comm'],dc['table'])
    elif rules == 'L':
        com = '%s -L -n -t mangle | grep -Ev "target|Chain|^$" ' % dc['comm']

    return com

def calculate(allip):
    abnormal = []
    tempip = []
    lackip = {}
    com = make_comm('L')
    values = exec_comm(com)
    ips = conversion(values)
    print "ips:",ips 

    for ip in ips:
        if allip.has_key(ip[0]):
            if ip[-1] == hex(allip[str(ip[0])]):
                if ip[0] in tempip:
                    abnormal.append([ip[0],ip[1]])
                else:
                    tempip.append(ip[0])
            else:
                abnormal.append([ip[0],ip[1]])
        else:
            abnormal.append([ip[0],ip[1]])

    for lk,lv in allip.items():
        if str(lk) not in tempip:
            lackip[lk] = lv

    print "abnormal:",abnormal,"lackip:",lackip,"tempip:",tempip
    return abnormal,lackip

def detection_iptables(U_CONF):
    LVS=get_lvs(U_CONF)
    m = 8580
    allip = {}

    for a in LVS['LVS_GROUPS']:
        for b in LVS['LVS_VIP_' + str(a)]:
            allip[b] = m
        m += 1
    print "allip:",allip
    abnormal,lackip = calculate(allip)
    
    for d_key in abnormal:
        com = make_comm('D',dip=d_key[0],mask=d_key[1])
        _v = exec_comm(com)
    for a_key in lackip.keys():
        com = make_comm('A',dip=a_key,mask=lackip[a_key])
        _v = exec_comm(com)

def main():
    U_CONF = "/etc/upyun.cfg"
    K_CONF = "/usr/local/keepalived/etc/keepalived.conf"

    master = get_master(K_CONF)

    if master == "MASTER":
        detection_iptables(U_CONF)
    else:
        com = make_comm('F','none','none')
        _v = exec_comm(com)

if __name__ == '__main__':
    main()
