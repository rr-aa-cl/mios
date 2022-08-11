#!/usr/bin/python3 -u
import requests
from http.client import HTTPSConnection
import base64
import hashlib
import json
import ssl
import sys
import socket
import time

from mongodb_client import MongoDBClient

from urllib.parse import urlencode, quote_plus




class FrankaAPI:
    def __init__(self, hostname, user, password):
        self._hostname = hostname
        self._user = user
        self._password = password
        self._spoc_token = False
        self._token = False
        self._in_control = False
        self.mongodb_client = MongoDBClient()
        self._in_control = self.mongodb_client.read("mios", "parameters", {"name":"system"})[0]["spoc_in_control"]
        if self._in_control:
            self._spoc_token = self.mongodb_client.read("mios", "parameters", {"name":"system"})[0]["spoc_token"]

    def __enter__(self):
        self._client = HTTPSConnection(self._hostname, context=ssl._create_unverified_context())
        self._client.connect()
        self._client.request('POST', '/admin/api/login',
                             body=json.dumps({'login': self._user,
                                              'password': self.encode_password(self._user, self._password)}),
                             headers={'content-type': 'application/json'})
        self._token = self._client.getresponse().read().decode('utf8')
        return self

    def __exit__(self, type, value, traceback):
        self._client.close()

    def start_task(self, task):
        self._client.request('POST', '/desk/api/execution',
                             body='id=%s' % task,
                             headers={'content-type': 'application/x-www-form-urlencoded',
                                      'Cookie': 'authorization=%s' % self._token})
        return self._client.getresponse().read()

    def stop_task(self):
        self._client.request('DELETE', '/desk/api/execution',
                             headers={'content-type': 'application/x-www-form-urlencoded',
                                      'Cookie': 'authorization=%s' % self._token})
        return self._client.getresponse().read()
        
    def clear_position_error(self, forever=True):
        self._client.request('GET', '/desk/api/robot/shutdown-position-error',
                             headers={'content-type': 'application/x-www-form-urlencoded',
                                      'Cookie': 'authorization=%s' % self._token, 'X-Control-Token': self._spoc_token})
        response = self._client.getresponse()
        response_content = response.read()
        response_status = response.status
        if response_status == 200 and forever==True:
            self._client.request('DELETE', '/desk/api/robot/shutdown-position-error/0',
                             headers={'content-type': 'application/x-www-form-urlencoded',
                                      'Cookie': 'authorization=%s' % self._token, 'X-Control-Token': self._spoc_token})
            self._client.request('DELETE', '/desk/api/robot/shutdown-position-error/1',
                             headers={'content-type': 'application/x-www-form-urlencoded',
                                      'Cookie': 'authorization=%s' % self._token, 'X-Control-Token': self._spoc_token})
            self._client.request('DELETE', '/desk/api/robot/shutdown-position-error/2',
                             headers={'content-type': 'application/x-www-form-urlencoded',
                                      'Cookie': 'authorization=%s' % self._token, 'X-Control-Token': self._spoc_token})
            self._client.request('DELETE', '/desk/api/robot/shutdown-position-error/3',
                             headers={'content-type': 'application/x-www-form-urlencoded',
                                      'Cookie': 'authorization=%s' % self._token, 'X-Control-Token': self._spoc_token})
            self._client.request('DELETE', '/desk/api/robot/shutdown-position-error/4',
                             headers={'content-type': 'application/x-www-form-urlencoded',
                                      'Cookie': 'authorization=%s' % self._token, 'X-Control-Token': self._spoc_token})
            self._client.request('DELETE', '/desk/api/robot/shutdown-position-error/5',
                             headers={'content-type': 'application/x-www-form-urlencoded',
                                      'Cookie': 'authorization=%s' % self._token, 'X-Control-Token': self._spoc_token})
            self._client.request('DELETE', '/desk/api/robot/shutdown-position-error/6',
                             headers={'content-type': 'application/x-www-form-urlencoded',
                                      'Cookie': 'authorization=%s' % self._token, 'X-Control-Token': self._spoc_token})
        return self._client.getresponse().read()


    def unlock_brakes(self):
        self._client.request('POST', '/desk/api/robot/open-brakes',
                             headers={'content-type': 'application/x-www-form-urlencoded',
                                      'Cookie': 'authorization=%s' % self._token, 'X-Control-Token': self._spoc_token})

    def unfold(self):
        self._client.request('POST', '/desk/api/robot/reset-errors',
                             headers={'content-type': 'application/x-www-form-urlencoded',
                                      'Cookie': 'authorization=%s' % self._token, 'X-Control-Token': self._spoc_token})
        return self._client.getresponse().read()

    def unlock_brakes(self): 
        payload = {'force':'false'}
        temp_body = urlencode(payload, quote_via=quote_plus)  # force=false
        self._client.request('POST', '/desk/api/robot/open-brakes', temp_body,
                             headers={'content-type': 'application/x-www-form-urlencoded',
                                      'Cookie': 'authorization=%s' % self._token, 'X-Control-Token': self._spoc_token})
        return self._client.getresponse().read()

    def lock_brakes(self):
        self._client.request('POST', '/desk/api/robot/close-brakes',
                             headers={'content-type': 'application/x-www-form-urlencoded',
                                      'Cookie': 'authorization=%s' % self._token})
        return self._client.getresponse().read()

    def shutdown(self):
        self._client.request('POST', '/admin/api/shutdown',
                             headers={'content-type': 'application/json'})

    def pack_pose(self):
        self._client.request('POST', '/desk/api/robot/fold',
                             headers={'content-type': 'application/x-www-form-urlencoded',
                                      'Cookie': 'authorization=%s' % self._token, 'X-Control-Token': self._spoc_token})
        return self._client.getresponse().read()

    def timeline_has_finished(self):
        self._client.request('GET', '/desk/api/execution',
                             headers={'content-type': 'application/x-www-form-urlencoded',
                                      'Cookie': 'authorization=%s' % self._token})
        str = self._client.getresponse().read().decode('utf-8')
        info = json.loads(str)
        result = dict()
        if info['lastActivePath'] is None:
            return False
        else:
            return True

    def encode_password(self, user, password):
        bs = ','.join(
            [str(b) for b in hashlib.sha256((password + '#' + user + '@franka').encode('utf-8')).digest()])
        return base64.encodestring(bs.encode('utf-8')).decode('utf-8')

    def reboot(self):
        self._client.request('POST', '/admin/api/reboot',
                             headers={})
        return self._client.getresponse().read()

    def take_control(self):
        if not self._in_control:
            response = -1
            temp_body = json.dumps({'requestedBy':'franka'})  #pinakothek
            self._client.request('POST', '/admin/api/control-token/request', temp_body,
                                 headers={'content-type': 'application/json',
                                          'Cookie': 'authorization=%s' % self._token})
            response = self._client.getresponse()
            response_content = response.read()
            response_status = response.status
            if response_status == 200:
                temp = json.loads(response_content)
                #print("1. request:",response_content)
                self._spoc_token = temp["token"]
                #print(test["token"])
                temp_body = json.dumps({'requestedBy':'franka'})  #pinakothek
                self._client.request('POST', '/admin/api/control-token/request?force=', temp_body,
                                 headers={'content-type': 'application/json',
                                          'Cookie': 'authorization=%s' % self._token})
                response = self._client.getresponse()
                response_content = response.read()
                response_status = response.status
                if response_status == 200:
                    temp = json.loads(response_content)
                    #print("2. request:",response_content)
                    self._spoc_token = temp["token"]
                    self._client.request('GET', '/admin/api/safety',
                                    headers={'content-type': 'application/json',
                                            'Cookie': 'authorization=%s' % self._token})
                    response = self._client.getresponse()
                    response_content = response.read()
                    response_status = response.status
                    if response_status == 200:
                        response = json.loads(response_content)
                        #print("3. request:",response_content)
                        response = response["tokenForceTimeout"]
                        self._in_control = True
                        self.mongodb_client.update("mios","parameters",{"name":"system"},{"spoc_token":self._spoc_token})
                        self.mongodb_client.update("mios","parameters",{"name":"system"},{"spoc_in_control":True})
                        print("verify your access to the robot. You have ",response," Seconds!")
                        return True

            return False
        print("Already in control")
        return False

    def release_control(self):
        if self._in_control:
            temp_body = json.dumps({'token':'%s' % self._spoc_token})
            self._client.request('DELETE', '/admin/api/control-token', temp_body,
                                 headers={'content-type': 'application/json',
                                 'Cookie': 'authorization=%s' % self._token})
            response = self._client.getresponse()
            response_content = response.read()
            response_status = response.status
            if response_status == 200:
                self._in_control = False
                self.mongodb_client.update("mios","parameters",{"name":"system"},{"spoc_in_control":False})
            return response_content
        print("Not in control, cannot release control")
        
    def activate_fci(self):
        temp_body = json.dumps({'token':'%s' % self._spoc_token})
        self._client.request('POST', '/admin/api/control-token/fci', temp_body,
                             headers={'content-type': 'application/json',
                                      'Cookie': 'authorization=%s' % self._token,
                                      "X-Control-Token":self._spoc_token})
        response = self._client.getresponse()
        response_status = response.status
        if response_status == 200:
            return True
        else:
            return False

    def deactivate_fci(self):
        temp_body = json.dumps({'token':'%s' % self._spoc_token})
        self._client.request('DELETE', '/admin/api/control-token/fci', temp_body,
                             headers={'content-type': 'application/json',
                                      'Cookie': 'authorization=%s' % self._token})
        return self._client.getresponse().read()



def shutdown(ip, user, pwd):
    try:
        with FrankaAPI(ip, user, pwd) as api:
            api.shutdown()
            return True
    except socket.error as e:
        print(e)
        print('Socket error, possibly no host with IP: ', ip, ', user: ', user, ' and password: ', pwd)
        return False


def unlock_brakes(ip, user, pwd):
    try:
        with FrankaAPI(ip, user, pwd) as api:
            api.unlock_brakes()
            return True
    except (socket.error):
        print('Socket error, possibly no host with IP: ', ip, ', user: ', user, ' and password: ', pwd)
        return False


def lock_brakes(ip, user, pwd):
    try:
        with FrankaAPI(ip, user, pwd) as api:
            api.lock_brakes()
            return True
    except socket.error as e:
        print(e)
        print('Socket error, possibly no host with IP: ', ip, ', user: ', user, ' and password: ', pwd)
        return False


def pack_pose(ip, user, pwd):
    try:
        with FrankaAPI(ip, user, pwd) as api:
            api.pack_pose()
            return True
    except socket.error as e:
        print(e)
        print('Socket error, possibly no host with IP: ', ip, ', user: ', user, ' and password: ', pwd)
        return False

def unfold(ip, user, pwd):
    try:
        with FrankaAPI(ip, user, pwd) as api:
            api.unfold()
            return True
    except socket.error as e:
        print(e)
        print('Socket error, possibly no host with IP: ', ip, ', user: ', user, ' and password: ', pwd)
        return False

def stop_task(ip, user, pwd):
    try:
        with FrankaAPI(ip, user, pwd) as api:
            api.stop_task()
    except (socket.error):
        print('Socket error, possibly no host with IP: ', ip, ', user: ', user, ' and password: ', pwd)


def is_busy(ip, name, pwd):
    try:
        with FrankaAPI(ip, name, pwd) as api:
            return api.check_timeline()
    except socket.error as e:
        print(e)
        print('Socket error, possibly no host with IP: ', ip, ', name: ', name, ' and password: ', pwd)


def start_task(ip, user, pwd, task):
    try:
        with FrankaAPI(ip, user, pwd) as api:
            api.start_task(task)
    except socket.error as e:
        print(e)
        print('Socket error, possibly no host with IP: ', ip, ', user: ', user, ' and password: ', pwd)


def check_task(ip, name, pwd):
    try:
        with FrankaAPI(ip, name, pwd) as api:
            return api.check_timeline()
    except (socket.error) as e:
        print(e)
        print('Socket error, possibly no host with IP: ', ip,', name: ', name,' and password: ', pwd)

def reboot(ip, user, pwd):
    try:
        with FrankaAPI(ip, user, pwd) as api:
            api.reboot()
    except socket.error as e:
        print(e)
        print('Socket error, possibly no host with IP: ', ip, ', user: ', user, ' and password: ', pwd)

def take_control(ip, user, pwd):
    try:
        with FrankaAPI(ip, user, pwd) as api:
            api.take_control()
    except socket.error as e:
        print(e)
        print('Socket error, possibly no host with IP: ', ip, ', user: ', user, ' and password: ', pwd)

def release_control(ip, user, pwd):
    try:
        with FrankaAPI(ip, user, pwd) as api:
            api.release_control()
    except socket.error as e:
        print(e)
        print('Socket error, possibly no host with IP: ', ip, ', user: ', user, ' and password: ', pwd)

def activate_fci(ip, user, pwd):
    try:
        with FrankaAPI(ip, user, pwd) as api:
            api.activate_fci()
    except socket.error as e:
        print(e)
        print('Socket error, possibly no host with IP: ', ip, ', user: ', user, ' and password: ', pwd)

def deactivate_fci(ip, user, pwd):
    try:
        with FrankaAPI(ip, user, pwd) as api:
            api.deactivate_fci()
    except socket.error as e:
        print(e)
        print('Socket error, possibly no host with IP: ', ip, ', user: ', user, ' and password: ', pwd)
