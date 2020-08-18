#!/bin/env python
# -*- coding: utf-8 -*-

import socket
import json
import struct
import fcntl
import array
import time

from ansible.module_utils.basic import AnsibleModule

SIOCGIFCONF = 0x8912
SIOCGIFADDR = 0x8915


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

    def getisp(self,ip):
        host='ip.taobao.com'
        data = ''
        parts = []
        ctn = u'\u7535\u4fe1'
        cun = u'\u8054\u901a'
        cmn = u'\u79fb\u52a8'
        
        uri = 'GET /service/getIpInfo.php?ip=' + str(ip) + ' HTTP/1.1'
        hheader='Host: ' + str(host)
        accp='Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
        ua='User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36'
        
        parts.append(uri)
        parts.append(hheader)
        parts.append(accp)
        parts.append(ua)
        
        data = '\r\n'.join(parts) + '\r\n\r\n'
        try:
            s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            s.connect((host,80))
            s.send(data)
            buffer_size = 1024
            response = b''
            while True:
                r = s.recv(buffer_size)
                if len(r) == 0:
                    break
                response = response + r
            header, html = response.split('\r\n\r\n',1)
            lines = html.split('\n')
            return json.loads(lines[1])
        except:
            return 
        finally:
            s.close()



class Fetch(object):
    def __init__(self, module):
        self.module = module
        self.facts = {'HOSTNAME': socket.gethostname().lower()}
        self.types = self.module.params.get('types')

    def machine(self):
        # machine & node info
        net_if = NetInterface()
        net_interface = net_if.collect()

        self.facts['NET_INTERFACE'] = net_interface
        self.facts['PUBLIC_IP'] = [
            ip['ip'] for ip in net_interface.values() if not ip['private']
        ]
        if not self.facts['PUBLIC_IP']:
            self.facts['PUBLIC_IP'] = [
                ip['ip'] for ip in net_interface.values()
                if ip['private'] and ip['ip'].startswith('172.')
            ]
        self.facts['PRIVATE_IP'] = [
            ip['ip'] for ip in net_interface.values()
            if ip['private'] and ip['ip'].startswith('192.168.')
        ]
        self.facts['NETWORK'] = self.network()
        if self.types == "origin":
            self.getispaddr()

    def network(self):
        network = self.facts['HOSTNAME'].split('-')[0]
        return network.upper()

    def getisp(self,ip):
        host='freeapi.ipip.net'
        buffer_size = 1024
        data = ''
        parts = []

        uri = 'GET /' + str(ip) + ' HTTP/1.1'
        hheader='Host: ' + str(host)
        accp='Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
        ua='User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36'
        keep = 'Connection: close'

        parts.append(uri)
        parts.append(hheader)
        parts.append(accp)
        parts.append(ua)
        parts.append(keep)

        data = '\r\n'.join(parts) + '\r\n\r\n'
        try:
            s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            s.connect((host,80))
            s.send(data)
            response = b''
            while True:
                r = s.recv(buffer_size)
                if len(r) == 0:
                    break
                response = response + r
            s.close()
            header, html = response.split('\r\n\r\n',1)
            lines = json.loads(html)
            return lines
        except:
            return

    def getispaddr(self):
        ctn = u'\u7535\u4fe1'
        cun = u'\u8054\u901a'
        cmn = u'\u79fb\u52a8'
        existip = '0.0.0.0'

        for ip in self.facts['PUBLIC_IP']:
            m = 5
            while m:
                data = self.getisp(ip)
                if data:
                    if data[-1] == ctn:
                        self.facts['PUBLIC_IP_CTN'] = ip
                    elif data[-1] == cun:
                        self.facts['PUBLIC_IP_CUN'] = ip
                    elif data[-1] == cmn:
                        self.facts['PUBLIC_IP_CMN'] = ip
                    else:
                        self.facts['PUBLIC_IP_ORG'] = ip
                    m -= 1
                else:
                    time.sleep(2)
        if not self.facts.get('PUBLIC_IP_CTN'):
            self.facts['PUBLIC_IP_CTN'] = existip
        if not self.facts.get('PUBLIC_IP_CUN'):
            self.facts['PUBLIC_IP_CUN'] = existip
        if not self.facts.get('PUBLIC_IP_CMN'):
            self.facts['PUBLIC_IP_CMN'] = existip
        if not self.facts.get('PUBLIC_IP_ORG'):
            self.facts['PUBLIC_IP_ORG'] = existip

def main():
    module = AnsibleModule(
        argument_spec = dict(
            types = dict(default='', type='str')
        ),
        supports_check_mode=True
    )
    fetch = Fetch(module)
    fetch.machine()
    module.exit_json(changed=False, ansible_facts=fetch.facts)


if __name__ == "__main__":
    main()
