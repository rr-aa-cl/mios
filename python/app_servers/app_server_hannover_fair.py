#!/usr/bin/python3 -u
from werkzeug.wrappers import Request, Response
from werkzeug.serving import run_simple

from jsonrpc import JSONRPCResponseManager, dispatcher

import requests
import json
import netifaces as ni

robot1 = 'tueirsi-nc-023.local'
robot2 = 'tueirsi-nc-008.local'


def rpc_call(rpc_url, method, params=None):
    headers = {'content-type': 'application/json'}
    if params is None:
        params = {None: None}

    payload = {
        u"method": method,
        u"params": params if params else u"",
        u"jsonrpc": u"2.0",
        u"id": 0,
    }
    try:
        response = requests.post(rpc_url, data=json.dumps(payload), headers=headers).json()
    except (requests.Timeout, requests.ConnectionError):
        print('RPC error')
        response = None

    return response


def get_ip_address(ifname):
    return ni.ifaddresses(ifname)[ni.AF_INET][0]['addr']


class AppServer:
    def __init__(self):
        pass

    def init(self, port):
        run_simple('0.0.0.0', port, self.start_server)

    @Request.application
    def start_server(self, request):
        response = JSONRPCResponseManager.handle(request.data, dispatcher)
        return Response(response.json, mimetype='application/json')

    @dispatcher.add_method
    def reset_demo(**kwargs):
        print('RESET DEMO')
        rpc_call('http://' + robot1 + ':8383', 'start_task',
                 {'task_id': 'hmi_script', 'parameters': {'reset': True, 'learn': False, 'connected': False}})

    @dispatcher.add_method
    def tactile(**kwargs):
        print('TACTILE')
        rpc_call('http://' + robot1 + ':8383', 'start_task',
                 {'task_id': 'hmi_script', 'parameters': {'reset': True, 'learn': True, 'connected': False}})

    @dispatcher.add_method
    def connect(**kwargs):
        print('CONNECT')
        rpc_call('http://' + robot1 + ':8383', 'start_task',
                 {'task_id': 'hmi_script', 'parameters': {'reset': True, 'learn': False, 'connected': True}})

    @dispatcher.add_method
    def perceive(**kwargs):
        print('PERCEIVE')
        rpc_call('http://' + robot1 + ':8383', 'start_task', {'task_id': 'dual_insert'})

    @dispatcher.add_method
    def grasp_left(**kwargs):
        print('GRASP LEFT')
        rpc_call('http://' + robot1 + ':8383', 'grasp_object', {'id': 'peg_hold_black'})

    @dispatcher.add_method
    def grasp_right(**kwargs):
        print('GRASP RIGHT')
        rpc_call('http://' + robot2 + ':8383', 'grasp_object', {'id': 'peg_insert3D'})

    @dispatcher.add_method
    def stop(**kwargs):
        print('STOP')
        rpc_call('http://' + robot1 + ':8383', 'stop_task', {'nominal': True})
        rpc_call('http://' + robot2 + ':8383', 'stop_task', {'nominal': True})

    @dispatcher.add_method
    def set_confidence(**kwargs):
        print('SET CONFIDENCE TO ' + kwargs['confidence'])


if __name__ == '__main__':
    A = AppServer()
    A.init(9004)
