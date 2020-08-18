#!/bin/env python

import os
import json
import requests

ENERU_API = "http://eneru.x.upyun.com"

# ENERU_API = "http://127.0.0.1:8080"


class EneruServiceException(Exception):
    def __init__(self, status, msg):
        self.args = (status, msg)
        self.status = status
        self.msg = msg


class EneruClientException(Exception):
    def __init__(self, msg):
        self.msg = str(msg)
        super(EneruClientException, self).__init__(msg)


def exception(func):
    def wrapper(*args, **kwargs):
        try:
            status, ret = func(*args, **kwargs)
        except requests.exceptions.ConnectionError as e:
            raise EneruClientException(e)
        except requests.exceptions.RequestException as e:
            raise EneruClientException(e)
        except Exception as e:
            raise EneruClientException(e)

        if status == 404:
            return

        if status // 100 != 2:
            if ret:
                raise EneruServiceException(status, ret["error"])
            else:
                raise EneruServiceException(status, "unknown")

        return ret or 1

    return wrapper


class Eneru():
    def __init__(self):
        self.session = requests.Session()
        self.endpoint = ENERU_API + "/v1/inventory"

    def request(self, method, uri, playload=None):
        headers = {"X-Eneru-Token": os.getenv("ENERU_TOKEN")}
        req = getattr(self.session, method.lower())
        if method == "PUT":
            return req(self.endpoint + uri, headers=headers, json=playload)
        elif method in ["GET", "DELETE"]:
            return req(self.endpoint + uri, headers=headers)

    @exception
    def gethost(self, host, groupname):
        '''
        host is ansible_host, not hostname
        '''
        status, ret = None, None
        if host:
            resp = self.request("GET", "/hosts?host=" + host)
        elif groupname:
            resp = self.request("GET", "/hosts?groupname=" + groupname)

        status = resp.status_code
        if len(resp.text) > 0:
            ret = resp.json()
        return status, ret

    @exception
    def deletehost(self, host):
        '''
        host is ansible_host, not hostname
        '''
        status, ret = None, None
        resp = self.request("DELETE", "/hosts?host=" + host)
        status = resp.status_code
        if len(resp.text) > 0:
            ret = resp.json()
        return status, ret

    @exception
    def getgroup(self, groupname):
        status, ret = None, None
        resp = self.request("GET", "/groups?groupname=" + groupname)
        status = resp.status_code
        if len(resp.text) > 0:
            ret = resp.json()
        return status, ret

    @exception
    def getdirectgroup(self, groupname):
        status, ret = None, None
        resp = self.request("GET", "/groups/direct?groupname=" + groupname)
        status = resp.status_code
        if len(resp.text) > 0:
            ret = resp.json()
        return status, ret

    @exception
    def gettopgroup(self):
        status, ret = None, None
        resp = self.request("GET", "/groups/top")
        status = resp.status_code
        if len(resp.text) > 0:
            ret = resp.json()
        return status, ret

    @exception
    def gethostbygroup(self, groupname):
        status, ret = None, None
        resp = self.request("GET", "/hosts?groupname=" + groupname)
        status = resp.status_code
        if len(resp.text) > 0:
            ret = resp.json()
        return status, ret

    @exception
    def addhost(self,
                hostname,
                ssh_host,
                ssh_port=65422,
                variables={},
                force=False):
        if not force and self.gethost(hostname):
            return 404, None
        status, ret = None, None
        playload = {
            'hostname': hostname,
            'ssh_host': ssh_host,
            'ssh_port': ssh_port,
            'vars': variables
        }
        resp = self.request("PUT", "/hosts", playload)
        status = resp.status_code
        if len(resp.text) > 0:
            ret = resp.json()
        return status, ret

    @exception
    def addgroup(self, groupname, variables={}, force=False):
        if not force and self.getgroup(groupname):
            return 404, None
        status, ret = None, None
        playload = {'groupname': groupname, 'vars': variables}
        resp = self.request("PUT", "/groups", playload)
        status = resp.status_code
        if len(resp.text) > 0:
            ret = resp.json()
        return status, ret

    @exception
    def addhostgroups(self, groupname, hostname):
        status, ret = None, None
        playload = {'groupname': groupname, 'host': hostname}
        resp = self.request("PUT", "/groups/host", playload)
        status = resp.status_code
        status = resp.status_code
        if len(resp.text) > 0:
            ret = resp.json()
        return status, ret

    @exception
    def addchildgroups(self, groupname, childname):
        status, ret = None, None
        playload = {'groupname': groupname, 'childname': childname}
        resp = self.request("PUT", "/groups/child", playload)
        status = resp.status_code
        if len(resp.text) > 0:
            ret = resp.json()
        return status, ret
