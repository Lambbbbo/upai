#!/usr/bin/env python
#-*- coding:utf8 -*-

import os
import sys
import json
import time
import errno
import select
import random
import socket
import logging
import requests
import threading
import subprocess
from multiprocessing.pool import ThreadPool

sys.path.append(os.getenv('PRISM_PYTHON_UTILS'))
from prism.ipaddress import IPv6Address

hogback_report = {
    'addr': 'hogback.x.upyun.com',
    'port': 80,
    'get':  'api/get_job',
    'post': 'api/upload_result'
}

kong_auth = {
    'auth_field': 'apikey',
    'auth_value': 'bElTNe2z5LKm0v3lmnZ8VH9hhD3xUrGe'
}

ipv6_global = False


# get target IPs from hogback.
def get_job(startup_timestamp, mode):

    global hogback_report, kong_auth

    url = 'http://%s:%d/%s' % (hogback_report['addr'],
                               hogback_report['port'],
                               hogback_report['get'])

    params = {'timestamp': startup_timestamp}

    hostname = socket.gethostname()
    nodename = hostname[0: hostname.rfind('-')]
    headers = {'X-HOGBACK-NODE': nodename,
               'X-HOGBACK-HOST': hostname,
               'X-HOGBACK-MODE': mode}

    headers.update({kong_auth['auth_field']: kong_auth['auth_value']})

    jobs = []
    try:
        hb_log.info('fetching job from %s...', url)

        res = requests.get(url,
                           params = params,
                           headers = headers,
                           timeout = 3)

        if res != None and res.status_code == 200:
            json_data = res.json()
            jobs     = json_data.get('job')
            status   = json_data.get('status')
            msg      = json_data.get('msg')
            addition = json_data.get('addition')
        else:
            hb_log.error('failed to get job from %s: %s', url, res)
            return jobs

    except requests.exceptions.Timeout:
        hb_log.error('failed to get job from %s: ConnectionTimeout', url)

    except requests.exceptions.ConnectionError:
        hb_log.error('failed to get job from %s: ConnectionError', url)

    except:
        hb_log.exception('failed to get job from %s:', url)

    else:
        hb_log.info('fetch job done: %s status: %s msg: %s addition: %s',
                jobs, status, msg, addition)

    return jobs


# upload scan result to hogback.
def upload_result(results, startup_timestamp):

    global hogback_report, kong_auth, ipv6_global

    url = 'http://%s:%d/%s' % (hogback_report['addr'],
                               hogback_report['port'],
                               hogback_report['post'])

    results = {'status': results}
    results.update({'hostname': socket.gethostname()})
    results.update({'timestamp': startup_timestamp})

    try:
        _header = {'Content-Type':'application/json'}
        _header.update({kong_auth['auth_field']: kong_auth['auth_value']})

        if ipv6_global:
            _header.update({'X-NETTYPE':'ipv6'})
        else:
            _header.update({'X-NETTYPE':'ipv4'})

        res = requests.post(url,
                            headers = _header,
                            data = json.dumps(results),
                            timeout = 3)

        if res.status_code == 200:
            hb_log.info('upload to hogback succ: %s',
                         json.dumps(res.json()))
        else:
            hb_log.error('upload to hogback failde: %s', res)

    except requests.exceptions.Timeout:
        hb_log.error('upload to hogback failed.')

    except requests.exceptions.ConnectionError:
        hb_log.error('upload to hogback failed: ConnectionError')

    except:
        hb_log.exception('upload to hogback failed.')


# log init
def log_dump():

    log_formatter = logging.Formatter(
            "%(asctime)s %(name)-10s %(levelname)-8s %(message)s")

    file_handler = logging.StreamHandler()
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(logging.INFO)

    _log = logging.getLogger("hogback")
    _log.setLevel(logging.INFO)
    _log.addHandler(file_handler)

    return _log


# @ip_type: ipv4/ipv6/all
def local_ipaddrs(ip_type):

    try:
        if_output = subprocess.check_output('ifconfig',
                                             shell = True,
                                             stderr = subprocess.STDOUT,
                                             env = {'PATH': '/sbin:/bin'})

    except subprocess.CalledProcessError as e:
        hb_log.error('Command \'%s\' failed, Output: %s', e.cmd, e.output)
        return None

    except:
        hb_log.exception('exec ifconfig failed.')
        return None

    outs = if_output.splitlines()

    if ip_type == 'ipv4':
        filter_str = "inet addr"
    elif ip_type == 'ipv6':
        filter_str = "inet6 addr"
    else:
        filter_str = "addr:"

    addrs = filter(lambda line: filter_str in line, outs)

    stripped_addrs = list()
    for addr in addrs:

        tmp = addr.split('addr:')[1]
        tmp = tmp.split()[0]
        stripped_addrs.append(tmp)

    return stripped_addrs


# filter vip refer to local node
def filter_local(jobs):

    result = list(jobs)
    addrs = local_ipaddrs('all')

    for job in jobs:

        ip = job['ip']
        if ip in addrs:
            result.remove(job)
            hb_log.info('ip %s refers to local node, skip it.', ip)
        else:
            continue

    return result


# test if ipv6 addr is private or not.
def is_private(raw_ip_str):

    ip_str = raw_ip_str.split('/')[0]
    return IPv6Address(unicode(ip_str)).is_private


# exclude ipv6 addrs if neccesarry.
def filter_ipv6(jobs):

    global ipv6_global

    result = list(jobs)
    addrs = local_ipaddrs('ipv6')

    ipv6_global = False
    for addr in addrs:

        if not is_private(addr):
            ipv6_global = True
            hb_log.info('ipv6 addr: %s', addr)
            break
        else:
            hb_log.info('ipv6 addr: %s, leave it.', addr)
            continue

    if not ipv6_global:
        hb_log.info('host type: ipv4, excluding ipv6 targets.')
        for job in jobs:
            ip = job['ip']
            if ip.find(':') > -1:
                result.remove(job)
                hb_log.info('ip %s refers to ipv6, skip it.', ip)
    else:
        hb_log.info('host type: ipv6, including ipv6 targets')

    return result


# wait for random seconds before fire
def random_wait():

    try:
        hostname = socket.gethostname()
        index = hostname.split('-')[3]
        interval = int(index) % 10
    except:
        interval = random.randint(0, 9)

    hb_log.info('sleep %d seconds.', interval)
    time.sleep(interval)


# decompose jobs from hogback into separate target.
def decompose_job(jobs):

    targets = []

    for job in jobs:

        ips   = job['ip']
        for ip in ips:

            target = {}
            target['ip'] = ip
            target['port'] = job['port']
            target['host'] = job['host']
            target['path'] = job['path']
            target['status_code'] = job['status_code']
            target['detect_way_id'] = job['detect_way_id']

            targets.append(target)

    return targets


# connect to target host:port in non-blocking way.
def hb_connect(host, port):

    s = None

    try:
        socks = socket.getaddrinfo(host, port,
                                   socket.AF_UNSPEC,
                                   socket.SOCK_STREAM)
    except socket.gaierror as se:
        hb_log.error('getaddrinfo(\'%s\', %d) --- %s', host, port, se)
        return ('err', s)

    for af, socktype, proto, canonname, sa in socks:

        try:
            s = socket.socket(af, socktype, proto)
            s.setblocking(0)
        except:
            hb_log.exception('failed to open socket to (%s:%d)', host, port)
            s = None
            continue

        try:
            s.connect(sa)
            return ('succ', s)
        except socket.error as se:
            if se.errno == errno.EINPROGRESS:
                return ('connecting', s)
            else:
                return ('err', s)
        except:
            hb_log.exception('failed connecting to (%s:%d)', host, port)
            return ('err', s)

    if s is None:
        return ('err', s)


# construct HTTP request.
def get_conent(Host, path):

    request_line = 'GET %s HTTP/1.1' % path
    headers = 'Host: %s' % Host
    return '%s\r\n%s\r\n\r\n' % (request_line, headers)


# classify targets info different types: http/port.
def classify(items):

    http_set = []
    port_set = []

    for item in items:
        if item['path']:
            http_set.append(item['ip'])
        else:
            port_set.append(item['ip'])

    return http_set, port_set


def main(mode):

    startup_timestamp = int(time.time())

    # get target IPs to scan
    targets = get_job(startup_timestamp, mode)
    if not targets:
        return

    targets = decompose_job(targets)
    targets = filter_local(targets)
    targets = filter_ipv6(targets)

    # instead of request burst, we scatter.
    random_wait()

    ##################### IO multiplex start ###########################

    http_set, port_set = classify(targets)

    # ready for reading
    inputs     = dict()
    # ready for write
    connecting = dict()

    host_socket  = dict()
    host_status  = dict()
    host_content = dict()
    host_check   = dict()
    host_connect = dict()

    hg_poll = select.poll()

    for target in targets:

        host = target['ip']
        port = target['port']
        detect_way_id = target["detect_way_id"]
        tg = ','.join([host, str(detect_way_id)])

        host_check[tg] = target['status_code']
        host_status[tg] = 'down'

        err, fd = hb_connect(host, port)
        if fd:

            fileno = fd.fileno()
            host_socket[fileno] = tg
            host_content[tg] = get_conent(target['host'], target['path'])

            local_host, local_port = fd.getsockname()[0:2]
            host_connect[tg] = (local_host, local_port, host, port)

            if err == 'err':
                fd.close()
                continue

            if err == 'connecting':
                hg_poll.register(fileno, select.POLLOUT)
                connecting[fileno] = fd

            if err == 'succ':
                fd.send(host_content[tg])
                hg_poll.register(fileno, select.POLLIN)
                inputs[fileno] = fd

    while True:
        '''
        in python, we need deal 6 poll event

        1. POLLIN: ready for read
        2. POLLOUT: ready for write
        3. POLLPRI: out-of-band (ignored there)
        4. POLLERR: error condition
        5. POLLHUP: hang up
        6. POLLINVAL: fd not open
        '''
        events = hg_poll.poll(1000) # milliseconds

        if not events:
            break

        for fileno, event in events:

            if event & select.POLLIN:

                ready_for_read_fd = inputs[fileno]

                try:
                    data = ready_for_read_fd.recv(15)

                    tg = host_socket[fileno]
                    need_value = "HTTP/1.1"
                    if host_check[tg] >= 100:
                        need_value = "%s %s" % (need_value, host_check[tg])

                    if str(data).startswith(need_value):
                        host_status[tg] = 'up'
                    else:
                        host_status[tg] = 'down'

                except:
                    tg = host_socket[fileno]
                    local_host, local_port, peer_host, peer_port \
                            = host_connect[tg]
                    hb_log.exception('%s:%d -> %s:%d recv err!',
                            local_host, local_port, peer_host, peer_port)

                ready_for_read_fd.close()
                del inputs[fileno]
                hg_poll.unregister(fileno)

            elif event & select.POLLOUT:

                ready_for_write_fd = connecting[fileno]
                tg = host_socket[fileno]
                host = tg.split(',', 1)[0]
                local_host, local_port, peer_host, peer_port = host_connect[tg]

                if ready_for_write_fd.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR) == 0:

                    hb_log.info('%s:%d -> %s:%d connected!',
                            local_host, local_port, peer_host, peer_port)

                    # update 'port scan' status
                    if host in port_set:
                        host_status[tg] = 'up'
                        ready_for_write_fd.close()
                        hg_poll.unregister(fileno)
                    else:
                        try:
                            ready_for_write_fd.send(host_content[tg])
                            inputs[fileno] = ready_for_write_fd
                            hg_poll.modify(fileno, select.POLLIN)
                        except:
                            ready_for_write_fd.close()
                            del connecting[fileno]
                            hg_poll.unregister(fileno)

                            hb_log.exceptions('%s:%d -> %s:%d send err!',
                                local_host, local_port, peer_host, peer_port)

                else:
                    hb_log.info('%s:%d -> %s:%d conn err!',
                            local_host, local_port, peer_host, peer_port)
                    ready_for_write_fd.close()

                del connecting[fileno]

            elif (event & select.POLLERR) or (event & select.POLLHUP)\
                    or (event & select.POLLNVAL):

                local_host, local_port, peer_host, peer_port = host_connect[tg]
                hb_log.info('%s:%d -> %s:%d conn exception!',
                        local_host, local_port, peer_host, peer_port)

                hg_poll.unregister(fileno)

                if fileno in connecting:
                    connecting[fileno].close()
                    del connecting[fileno]

                if fileno in inputs:
                    inputs[fileno].close()
                    del inputs[fileno]

    ##################### IO multiplex end ###########################

    hb_log.info('scaning all done. target num: %d', len(targets))

    for host, status in host_status.items():
        hb_log.info('service: %s status: %s', host, status)

    upload_result(host_status, startup_timestamp)


if __name__ == '__main__':

    hb_log = log_dump()

    # (for debug purpose, manually set @mode to 'debug')
    main(mode = 'release')

