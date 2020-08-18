#!/bin/env python
# -*- coding: utf-8 -*-

import subprocess
import socket
import struct
import fcntl
import array
import hashlib
import os
import json
import requests

from copy import deepcopy
from ansible.module_utils.basic import AnsibleModule

SIOCGIFCONF = 0x8912
SIOCGIFADDR = 0x8915

ENERU_API = "http://eneru.x.upyun.com/v1/inventory/"
ApiKey = "ertsBIgtWqgieH4gdHzOMrthRjZUsuGh"

def disable_bcache():
    return True


class NetInterface(object):
    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def get_interfaces(self):
        ifreq_size = 24 + 2 * len(struct.pack('P', 0))
        max_possible = 128
        byte = max_possible * ifreq_size

        ifreq_buf = array.array('B', '\0' * byte)
        ifconf = struct.pack('iP', byte, ifreq_buf.buffer_info()[0])
        result = fcntl.ioctl(self.socket.fileno(), SIOCGIFCONF, ifconf)
        ifc_len, _ = struct.unpack('iP', result)

        devs = []
        for i in range(0, ifc_len, ifreq_size):
            ifr_name = (ifreq_buf.tostring()[i:i + ifreq_size])[:16]
            name = ifr_name.split('\0', 1)[0]
            devs.append(name)
        return devs

    def get_ip(self, ifname):
        ifreq = struct.pack('16sH14s', ifname, 0, '')
        ret = fcntl.ioctl(self.socket.fileno(), SIOCGIFADDR, ifreq)
        addr = struct.unpack('16sH14B', ret)[4:8]
        ipaddr = "%d.%d.%d.%d" % (addr)
        return ipaddr

    def get_netmask(self, ifname):
        ifreq = struct.pack('256s', ifname)
        ret = fcntl.ioctl(self.socket, 35099, ifreq)
        netmask = socket.inet_ntoa(ret[20:24])
        return netmask

    @classmethod
    def bits_to_netmask(cls, bits):
        # return '.'.join([str((0xffffffff << (32 - bits) >> i) & 0xff) for i in [24, 16, 8, 0]])
        return socket.inet_ntoa(
            struct.pack(">I", (0xffffffff << (32 - bits)) & 0xffffffff))

    @classmethod
    def netmask_to_bits(cls, netmask):
        return sum([bin(int(x)).count('1') for x in netmask.split('.')])

    @classmethod
    def is_private(cls, ipaddr):
        fpack = struct.unpack('!I', socket.inet_pton(socket.AF_INET,
                                                     ipaddr))[0]
        private = ([2130706432, 4278190080],  # 127.0.0.0,   255.0.0.0
                   [3232235520, 4294901760],  # 192.168.0.0, 255.255.0.0
                   [2886729728, 4293918720],  # 172.16.0.0,  255.240.0.0
                   [167772160, 4278190080])  # 10.0.0.0,    255.0.0.0

        for net in private:
            if (fpack & net[1]) == net[0]:
                return True
        return False

    @classmethod
    def ip_address(cls, ipaddr):
        pass

    @classmethod
    def is_netmask(cls, netmask):
        pass

    def collect(self):
        data = {}
        for ifname in self.get_interfaces():
            ipaddr = self.get_ip(ifname)
            netmask = self.get_netmask(ifname)

            data[ifname] = {
                'ip': ipaddr,
                'private': self.is_private(ipaddr),
                'netmask': netmask,
                'netmask_bits': self.netmask_to_bits(netmask)
            }

        return data


class BepoMeta(object):
    def __init__(self, module, content, machine_meta):
        self.module = module
        self.content = content
        self.machine_meta = machine_meta


    def upstream(self):
        ups = self.content['CACHE_PEER']
        pri_ip = self.machine_meta['PRIVATE_IP'][0]

        ups = [x.split(':')[0] for x in ups]

        port = ups[0].split(':')[-1]


        ups = deepcopy(ups)
        if pri_ip in ups:
            ups.remove(pri_ip)
            ups.insert(0, pri_ip)

        return ups

    @property
    def metadata(self):
        facts = { }
        facts['upstream'] = self.upstream()
        facts['port']     = self.content['CACHE_PEER'][0].split(':')[-1]
        facts['bindip']   = self.machine_meta['PRIVATE_IP'][0]

        mode = self.module.params.get("mode")
        if not mode:
            path = "/usr/local/bepo/etc/disk"
            if os.path.isfile(path):
                mode = open(path).read().strip()

                if mode in ['bcache', 'cio']:
                    mode = 'cio'
                elif mode in ['double', 'fork']:
                    mode = 'fork'
                elif mode in ['ssd', 'single', 'sata']:
                    mode = 'single'
                else:
                    mode = None


        facts['mode'] = mode or 'None'

        return facts


class Meta(object):
    def __init__(self, module, content, machine_meta):
        self.module = module
        self.content = content
        self.machine_meta = machine_meta

    def upstream(self, metadata):
        nginx_upstream = metadata['NGINX_UPSTREAM']
        if self.machine_meta['HOSTNAME'].startswith('CTN-ZJ-LNA2'):
            nginx_upstream = ['192.168.24.28', '192.168.24.29',
                              '192.168.24.34', '192.168.24.35',
                              '192.168.24.36']
        elif self.machine_meta['HOSTNAME'].startswith('CMN-SN-SIA1'):
            nginx_upstream = ['192.168.250.11', '192.168.250.12',
                              '192.168.250.13', '192.168.250.14',
                              '192.168.250.15']
        elif self.machine_meta['HOSTNAME'].startswith('CTN-SN-TOC1'):
            nginx_upstream = ['192.168.41.90', '192.168.41.91',
                              '192.168.41.92', '192.168.41.93',
                              '192.168.41.94']
        elif self.machine_meta['HOSTNAME'].startswith('CMN-JS-CZX1'):
            nginx_upstream = ['192.168.165.139', '192.168.165.140',
                              '192.168.165.141', '192.168.165.142',
                              '192.168.165.143']
        elif self.machine_meta['HOSTNAME'].startswith('CMN-SC-CTU1'):
            nginx_upstream = ['192.168.246.40', '192.168.246.41',
                              '192.168.246.42', '192.168.246.43',
                              '192.168.246.44']
        return nginx_upstream

    @property
    def metadata(self):
        facts = {}
        data = self.content

        facts['TCPCOPY'] = True if data.get('TCPCOPY', '') == 'Y' else False
        facts['OVERSEAS'] = True if data.get('OVERSEAS', '') == 'Y' else False
        facts['IPV6_SUPPORT'] = True if data.get('IPV6_SUPPORT',
                                                 '') == 'Y' else False
        facts['DIRECT_TRANSFER'] = True if data.get('DIRECT_TRANSFER',
                                                    '') == 'Y' else False
        facts['MIX_MARCO'] = True if data.get('MIX_MARCO',
                                                    '') == 'Y' else False
        facts['NGINX_UPSTREAM'] = [
            i.split('#')[-2] for i in data.get('NGINX_UPSTREAM', '').split()
        ]
        if data.get('REDIS_UPSTREAM','') != '':
            facts['REDIS_UPSTREAM'] = [
                i.split('#')[-2] for i in data.get('REDIS_UPSTREAM','').split()
            ]
        else:
            facts['REDIS_UPSTREAM'] = [
                i.split('#')[-2] for i in data.get('NGINX_UPSTREAM', '').split()
            ]
        if data.get('ZICOGO_UPSTREAM','') != '':
            facts['ZICOGO_UPSTREAM'] = [
                i.split('#')[-2] for i in data.get('ZICIGO_UPSTREAM','').split()
            ]
        else:
            facts['ZICOGO_UPSTREAM'] = [
                i.split('#')[-2] for i in data.get('NGINX_UPSTREAM', '').split()
            ]
        facts['NGINX_UPSTREAM_WEIGHT'] = [
            (i.split('#')[-2],i.split('#')[-1])
            for i in data.get('NGINX_UPSTREAM_WEIGHT', '').split()
        ]
        facts['NGINX_UPSTREAM_DOWN'] = [
            i.split('#')[1] for i in data.get('NGINX_UPSTREAM', '').split()
            if i.startswith('#')
        ]
        facts['NGINX_UPSTREAM_EXTENSION'] = [
            (i.split('#')[-2],i.split('#')[-1])
            for i in data.get('NGINX_UPSTREAM_EXTENSION', '').split()
        ]
        facts['NGINX_UPSTREAM_EXTENSION_DOWN'] = [
            i.split('#')[1] for i in data.get('NGINX_UPSTREAM_EXTENSION', '').split()
            if i.startswith('#')
        ]
        return facts

    def marco(self):
        facts = self.metadata
        data = self.content
        headers = {"x-eneru-apikey": ApiKey}
        facts['REDIS_MARCO_PORT'] = data.get('REDIS_MARCO_PORT', 1020)
        facts['NGINX_LOG_DEV'] = data.get('NGINX_LOG_DEV', '')
        facts['DISABLE_BCACHE'] = disable_bcache()
        facts['NIC_SPEED'] = 20000 * 1024 * 1024 / 8  # Mbps to bytes
	facts['NETWORK'] = data.get('NETWORK', '')
        HOSTNAME = self.machine_meta["HOSTNAME"]

        HOSTURL = "{0}hosts?page=1&filter_by=hostname%2C{1}".format(ENERU_API,HOSTNAME)
        req = requests.get(HOSTURL, headers=headers) 
        resp = json.loads(req.content)
        roomid = resp["items"][0]["room"]["id"]
        platformid = resp["items"][0]["platform"]["id"]
        ROOMURL = "{0}rooms/{1}".format(ENERU_API,roomid)
        res = requests.get(ROOMURL, headers=headers)
        result = json.loads(res.content)
        if result["country"]["id"] == 1:
            country_name = result["country"]["country_name"][:2]
        else:
            country_name = result["country"]["country_name"]
        facts["COUNTRY"] = country_name
        
        if result["isp"]["id"] in [1,2,3]:
            isp_name = result["isp"]["isp_name"][-2:]
        else:
            isp_name = result["isp"]["isp_name"]

        facts["PROVINCE"] = result["province"]["province_name"]
        facts["ISP"] = isp_name
        if result["country"]["id"] == 1:
            if platformid == 20:
                facts["ISP_ABBR"] = "SCNR"
            elif platformid == 22:
                facts["ISP_ABBR"] = "SCND"
            else:
                if result["isp"]["id"] == 1:
                    facts["ISP_ABBR"] = "CTC"
                elif result["isp"]["id"] == 2:
                    facts["ISP_ABBR"] = "CMC"
                elif result["isp"]["id"] == 3:
                    facts["ISP_ABBR"] = "CNC"
                else:
                    facts["ISP_ABBR"] = "ORG"
        else:
            facts["ISP_ABBR"] = "ABROAD"
        

        def _read_speed(sf):
            s = 20000 * 1024 * 1024 / 8
            try:
                with open(sf) as f:
                    speed = int(f.read())
                    if speed > 0:
                        s = speed * 1024 * 1024 / 8
                return s
            except Exception as e:
                return s

        speed_file = "/sys/class/net/bond0/speed"
        if os.path.exists(speed_file):
            facts['NIC_SPEED'] = _read_speed(speed_file)
            return facts

        eth0 = 0
        eth1 = 0
        speed_file = "/sys/class/net/eth0/speed"
        if os.path.exists(speed_file):
            eth0 = _read_speed(speed_file)

        speed_file = "/sys/class/net/eth1/speed"
        if os.path.exists(speed_file):
            eth1 = _read_speed(speed_file)

        if eth0 or eth1:
            facts['NIC_SPEED'] = eth0 + eth1

        return facts

    def shanks(self):
        facts = self.metadata
        data = self.content
        net_map = {'CTC': 'CTN', 'CNC': 'CUN'}
        facts['NETWORK'] = net_map[data.get('NETWORK')]
        facts['VIP_CTC'] = data.get('LVS_VIP_CTC',self.machine_meta['PUBLIC_IP'][0])
        facts['VIP_CMC'] = data.get('LVS_VIP_CMN',self.machine_meta['PUBLIC_IP'][0])
        facts['VIP_CNC'] = data.get('LVS_VIP_CNC',self.machine_meta['PUBLIC_IP'][0])
        facts['REDIS_SHANKS_PORT'] = data.get('REDIS_SHANKS_PORT', 1021)
        facts['NGINX_405_SRC_UPSTREAM'] = [
            i for i in data.get('NGINX_405_SRC_UPSTREAM', '').split()
            if not i.startswith('#')
        ]
        facts['NGINX_405_IMG_UPSTREAM'] = [{
            'host': i.split(":")[0],
            'port': i.split(":")[1]
        } for i in data.get('NGINX_405_IMG_UPSTREAM', '').split()]
        watermark = data.get('NGINX_405_WATERMARK_UPSTREAM', ':').split(':')
        facts['NGINX_405_WATERMARK_UPSTREAM'] = {
            "host": watermark[0],
            "port": watermark[1]
        }
        return facts

    def zicogo(self):
        facts = self.metadata
        facts['IS_NODE_FIRST'] = False
        facts['NGINX_LOG_DEV'] = self.content.get('NGINX_LOG_DEV', '')

        nginx_upstream = self.upstream(facts)

        if set(self.machine_meta['PRIVATE_IP']) & set(nginx_upstream[0:2]):
            facts['IS_NODE_FIRST'] = True
        return facts

    def mirror(self):
        facts = self.metadata
        data = self.content
        facts['REDIS_SHANKS_PORT'] = data.get('REDIS_SHANKS_PORT', 1021)
        return facts

    def vista(self):
        facts = self.metadata
        data = self.content
        facts['VISTA_CACHE1_UPSTREAM'] = [
            (i.split('#')[-2],i.split('#')[-1]) for i in data.get('VISTA_CACHE1_UPSTREAM', '').split()
        ]
        facts['VISTA_CACHE1_UPSTREAM_DOWN'] = [
            i.split('#')[1] for i in data.get('VISTA_CACHE1_UPSTREAM', '').split()
            if i.startswith('#')
        ]
        facts['DISABLE_BCACHE'] = disable_bcache()
        return facts

    def bepo(self):
        facts = self.metadata
        facts['CACHE_PEER'] = [
            i
            for i in self.content.get('CACHE_PEER').split()[0].split('#')[1]
            .split('@')
        ]
        facts['bepo'] = BepoMeta(self.module, facts,
                                 self.machine_meta).metadata
        return facts

    def stunnel(self):
        facts = self.metadata

        nginx_upstream = self.upstream(facts)
        # set default value, so that no error happen
        facts['HOST_NODE_IDX'] = 1000
        for ip in self.machine_meta['PRIVATE_IP']:
            if ip in nginx_upstream:
                facts['HOST_NODE_IDX'] = nginx_upstream.index(ip)
        return facts

    def keepalived(self):
        facts = self.metadata
        data = self.content

        facts['IS_NODE_FIRST'] = False

        nginx_upstream = self.upstream(facts)
        if set(self.machine_meta['PRIVATE_IP']) & set(nginx_upstream[0:2]):
            facts['IS_NODE_FIRST'] = True

        for k in ['LVS_DEV', 'LVS_MASTER']:
            facts[k] = data.get(k)

        lvs_groups = [{
            "vip": data.get("LVS_VIP_" + i, "").split(","),
            "real_ip": data.get("LVS_HOSTS_" + i, "").split(","),
            "mask": data["LVS_MASK_" + i],
            "port": int("858" + i[-1])
        } for i in data.get("LVS_GROUPS", "").split(",")]

        facts['LVS_GROUPS'] = lvs_groups
        facts['LVS_VIRTUAL_ID'] = 100
        if len(lvs_groups) > 0:
            vips = sorted(lvs_groups[0]["vip"])
            s = hashlib.sha1(vips[0].encode()).hexdigest()
            facts['LVS_VIRTUAL_ID'] = int(s, 16) % (10**2)

        lvs_ports = list(set(data.get('LVS_PORTS').split(",")))

        facts['LVS_FWMARK'] = True if "0" in lvs_ports else False
        facts['LVS_FWMARK_ONLY'] = True if ["0"] == lvs_ports else False


        [lvs_ports.remove(p) for p in ['21'] if lvs_ports.count(p) == 1]
        facts['LVS_PORTS'] = lvs_ports
        return facts

    def gobgp(self):
        facts = self.metadata

        cmd1 = [ "awk -F '|' 'NR==1{print $4}' /network.info" ]
        cmd2 = [ "awk -F '|' 'NR==1{print $6}' /network.info" ]
        proc1 = subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
        proc2 = subprocess.Popen(cmd2, stdout=subprocess.PIPE, shell=True)
        facts['REAL_IP'] = proc1.stdout.read().strip('\n')
        facts['REAL_GATEWAY'] = proc2.stdout.read().strip('\n')
        return facts
    

class Fetch(object):
    def __init__(self, module):
        self.facts = {'HOSTNAME': socket.gethostname()}
        self.module = module
        self.project = module.params['project']

    def _parser_cfg(self, cfg):
        content = {}

        mlines = ''
        command = ['bash', '-c', 'set -a && source %s && env' % (cfg)]

        proc = subprocess.Popen(command, stdout=subprocess.PIPE)
        for line in proc.stdout:
            line = line.strip('\n')

            if '=' in line:
                if mlines:
                    (key, _, value) = mlines.partition("=")
                    content[key] = value.strip()
                    mlines = ''

                (key, _, value) = line.partition("=")
                if value:
                    content[key] = value.strip()
                else:
                    mlines += line + ' '
            else:
                mlines += line + ' '

        proc.communicate()

        return content

    def metadata(self, cfg):
        # parse metadata config
        data = self._parser_cfg(cfg)
        meta = Meta(self.module, data, self.facts)
        if hasattr(meta, self.project):
            self.facts.update(**getattr(meta, self.project)())

    def machine(self):
        # machine & node info
        net_if = NetInterface()
        net_interface = net_if.collect()

        self.facts['NET_INTERFACE'] = net_interface
        self.facts['PUBLIC_IP'] = [
            ip['ip'] for ip in net_interface.values() if not ip['private']
        ]
        self.facts['PRIVATE_IP'] = [
            ip['ip'] for ip in net_interface.values()
            if ip['private'] and ip['ip'].startswith('192.168.') or ip['ip'].startswith('10.')
        ]
        if not self.facts['PUBLIC_IP']:
            self.facts['PUBLIC_IP'] = [
                ip['ip'] for ip in net_interface.values()
                if ip['private'] and ip['ip'].startswith('172.')
            ]
            self.facts['PRIVATE_IP'] = [
                ip['ip'] for ip in net_interface.values()
                if ip['private'] and ip['ip'].startswith('172.')
            ]

        hostname = self.facts["HOSTNAME"]
        self.facts['IS_HONGKONG'] = False
        if hostname.startswith('NTT-CN-HKG') or hostname.startswith('PCW-CN-HKG'):
            self.facts['IS_HONGKONG'] = True

    def populate(self):
        self.machine()
        self.metadata('/etc/upyun.cfg')


def main():
    module = AnsibleModule(argument_spec=dict(
        project=dict(required=True),
        mode=dict(default=None)))

    fetch = Fetch(module)
    fetch.populate()
    # self.module.fail_json(changed=False, msg=meta.bepo)
    module.exit_json(changed=False, ansible_facts=fetch.facts)


if __name__ == "__main__":
    main()
