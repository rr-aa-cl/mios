#!/usr/bin/python3 -u
from werkzeug.wrappers import Request, Response
from werkzeug.serving import run_simple

from jsonrpc import JSONRPCResponseManager, dispatcher

from threading import Thread
import sys
import requests
import json
import time
import netifaces as ni
import socket

server_url = 'http://tueirsi-nc-032.local:8390'

url_garmi_left  = 'http://tueirsi-nc-009.local:8383' #TODO
url_garmi_right = 'http://tueirsi-nc-027.local:8383' #TODO
url_parti_left  = 'http://tueirsi-nc-parti-l.local:8383' #TODO
url_parti_right = 'http://tueirsi-nc-parti-r.local:8383' #TODO
master_left = 'tueirsi-nc-parti-l.local';
master_right = 'tueirsi-nc-parti-r.local';
slave_left = 'tueirsi-nc-009.local';
slave_right = 'tueirsi-nc-027.local';




def check_collective():
    rtn = rpc_call(server_url, 'get_collective')
    collective = []
    for key, val in rtn['result'].items():
        if val['online'] is True:
            collective.append(key)
    return collective


def get_cluster():
    rtn = rpc_call(server_url, 'get_cluster',{'cluster':'msrm'})
    cluster = rtn['result']['robots']
    own_id = get_own_id()
    if own_id in cluster:
        cluster.remove(own_id)

    return cluster


def get_own_id():
    hostname = socket.gethostbyaddr(get_ip_address('tap0'))[0]
    hostname = hostname.lower() + '.local'

    id = 'extern_tmp'
    rtn = rpc_call(server_url, 'who_am_i', {'hostname': hostname})
    print(rtn)
    if rtn is None:
        return 'none'
    if rtn['result']['id'] == 'none':
        rpc_call(server_url, 'remove_robot', {'alias': 'extern_tmp'})
        rtn = rpc_call(server_url, 'add_robot', {'hostname':hostname,'alias': id})
        print(rtn)
    else:
        id = rtn['result']['id']

    return id


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


def start_task_cluster(task, cluster, params=None, queue=False, ):
    params = {
        'method': 'start_task',
        'cluster': cluster,
        'parameters': {
            'task_id': task,
            'queue_task': queue,
            'parameters': params
        }
    }
    rpc_call(server_url, 'relay_command_to_cluster', params)


def get_state(alias):
    response_host = rpc_call(server_url, "get_hostname", {'alias': alias})
    hostname = response_host["result"]["hostname"]
    return rpc_call('http://' + hostname + ':8383', "get_state")


def teach_object_collective(o):
    params = {
        'method': 'teach_object',
        'parameters': {
            'id': o
        }
    }
    rpc_call(server_url, 'relay_command_to_collective', params)


def teach_object_cluster(o, cluster):
    params = {
        'method': 'teach_object',
        'cluster': cluster,
        'parameters': {
            'id': o
        }
    }
    rpc_call(server_url, 'relay_command_to_cluster', params)


def teach_object_robot(o, alias):
    params = {
        'method': 'teach_object',
        'alias': alias,
        'parameters': {
            'id': o
        }
    }
    rpc_call(server_url, 'relay_command_to_robot', params)


def grasp_object_cluster(o, cluster):
    params = {
        'method': 'grasp_object',
        'cluster': cluster,
        'parameters': {
            'id': o
        }
    }
    rpc_call(server_url, 'relay_command_to_cluster', params)


def grasp_object_robot(o, alias):
    params = {
        'method': 'grasp_object',
        'alias': alias,
        'parameters': {
            'id': o
        }
    }
    rpc_call(server_url, 'relay_command_to_robot', params)


def release_object_cluster(cluster):
    params = {
        'method': 'release_object',
        'cluster': cluster
    }
    rpc_call(server_url, 'relay_command_to_cluster')


def release_object_robot(alias):
    params = {
        'method': 'release_object',
        'alias': alias
    }
    rpc_call(server_url, 'relay_command_to_robot')


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
    def c_telepresence_hand_shake(**kwargs):
        master = socket.gethostbyaddr(get_ip_address('tap0'))[0]
        master = master.lower() + '.local'
        rtn = rpc_call(server_url, "get_hostname", {'alias': kwargs['slave']})
        slave = rtn["result"]["hostname"]

        if master == slave:
            print('Master and slave must not be identical.')
            return

        rtn = rpc_call('http://' + master + ':8383', 'start_task',
                       {'task_id': 'move_to_joint_pose', 'parameters': {'pose': 'shake_hand'}})
        rpc_call('http://' + master + ':8383', 'wait_for_task', {'unique_task_id': rtn['result']['unique_task_id']})

        params = {
            'task_id': 'telepresence',
            'parameters': {
                'master': True,
                'alias_peer': slave
            }
        }
        rpc_call('http://' + master + ':8383', 'start_task', params)
        response_state = rpc_call('http://' + master + ':8383', "get_state")
        # input("Sync others")
        params = {
            'task_id': 'telepresence',
            'parameters': {
                'master': False,
                'q_0': response_state["result"]["q"],
                'alias_peer': master
            }
        }
        rpc_call('http://' + slave + ':8383', 'start_task', params)

    @dispatcher.add_method
    def c_telepresence_bi(**kwargs):
        master = socket.gethostbyaddr(get_ip_address('tap0'))[0]
        master = master.lower() + '.local'
        rtn = rpc_call(server_url, "get_hostname", {'alias': kwargs["slave"]})
        slave = rtn["result"]["hostname"]
        #slave = 'tueirsi-nc-027.local'

        if master == slave:
            print('Master and slave must not be identical.')
            return

        params = {
            'task_id': 'telepresence',
            'parameters': {
                'master': True,
                'alias_peer': slave
            }
        }
        print(master)
        print(slave)
        rpc_call('http://' + master + ':8383', 'start_task', params)
        response_state = rpc_call('http://' + master + ':8383', "get_state")
        print(response_state["result"]["q"])
        # input("Sync others")
        params = {
            'task_id': 'telepresence',
            'parameters': {
                'master': False,
                'q_0': response_state["result"]["q"],
                'alias_peer': master
            }
        }
        rpc_call('http://' + slave + ':8383', 'start_task', params)

    @dispatcher.add_method
    def c_telepresence_bi_cart(**kwargs):
        master = socket.gethostbyaddr(get_ip_address('tap0'))[0]
        master = master.lower() + '.local'
        rtn = rpc_call(server_url, "get_hostname", {'alias': kwargs["slave"]})
        slave = rtn["result"]["hostname"]
        slave = 'tueirsi-nc-027.local'

        if master == slave:
            print('Master and slave must not be identical.')
            return

        params = {
            'task_id': 'telepresence',
            'parameters': {
                'master': True,
                'alias_peer': slave
            }
        }
        print(master)
        print(slave)
        rpc_call('http://' + master + ':8383', 'start_task', params)
        response_state = rpc_call('http://' + master + ':8383', "get_state")
        # input("Sync others")
        params = {
            'task_id': 'telepresence',
            'parameters': {
                'master': False,
                'TF_T_EE_0': response_state["result"]["O_T_EE"],
                'alias_peer': master
            }
        }
        rpc_call('http://' + slave + ':8383', 'start_task', params)

    @dispatcher.add_method
    def c_telepresence_uni(**kwargs):

        master = socket.gethostbyaddr(get_ip_address('tap0'))[0]
        master = master.lower() + '.local'
        slaves = get_cluster().copy()

        slaves=['msrm-2','msrm-4','msrm-8']

        own_id = get_own_id()
        if own_id in slaves:
            slaves.remove(own_id)

        rtn = rpc_call('http://' + master + ':8383', 'start_task',
                       {'task_id': 'move_to_joint_pose', 'parameters': {'pose': 'feature_default'}})
        if rtn['result'] is False:
            return
        rpc_call('http://' + master + ':8383', 'wait_for_task', {'unique_task_id': rtn['result']['unique_task_id']})

        rtn = rpc_call(server_url, "get_hostname", {'alias': slaves[0]})
        repeater = rtn["result"]["hostname"]

        params = {
            'task_id': 'telepresence',
            'parameters': {
                'master': True,
                'alias_peer': repeater,
                'bilateral': False
            }
        }
        rpc_call('http://' + master + ':8383', 'start_task', params)
        response_state = rpc_call('http://' + master + ':8383', "get_state")
        # input("Sync others")
        params = {
            'task_id': 'telepresence',
            'parameters': {
                'master': False,
                'q_0': response_state["result"]["q"],
                'alias_peer': master,
                'repeater': True
            }
        }
        rpc_call('http://' + repeater + ':8383', 'start_task', params)

        rpc_call(server_url, 'relay_command_to_robot', params)
        for i in range(len(slaves)):
            if i==0:
                continue
            params = {
                'method': 'start_task',
                'alias': slaves[i],
                'parameters': {
                    'task_id': 'telepresence',
                    'parameters': {
                        'master': False,
                        'q_0': response_state["result"]["q"],
                        'alias_peer': '225.0.0.1',
                        'repeater': False
                    }
                }
            }
            t = Thread(target=rpc_call, args=(server_url, 'relay_command_to_robot', params,))
            t.start()


    @dispatcher.add_method
    def c_telepresence_uni_add(**kwargs):

        if 'slave' not in kwargs:
            return

        master = socket.gethostbyaddr(get_ip_address('tap0'))[0]
        master = master.lower() + '.local'

        response_state = rpc_call('http://' + master + ':8383', "get_state")

        params = {
            'method': 'start_task',
            'alias': kwargs['slave'],
            'parameters': {
                'task_id': 'telepresence',
                'parameters': {
                    'master': False,
                    'q_0': response_state["result"]["q"],
                    'alias_peer': '225.0.0.1',
                    'repeater': False
                }
            }
        }
        rpc_call(server_url, 'relay_command_to_robot', params)


    @dispatcher.add_method
    def c_telepresence_uni_remove(**kwargs):
        print(kwargs)
        if 'slave' not in kwargs:
            return
        params = {
            'method': 'stop_task',
            'alias': kwargs['slave'],
            'parameters':{
                None:None
            }
        }
        r=rpc_call(server_url, 'relay_command_to_robot', params)
        print(r)


    @dispatcher.add_method
    def c_learnKey(**kwargs):
        me = get_own_id()
        robots = [me] + get_cluster()

        print(me)
        print(robots)
        params = {
            'agent': me,
            'aliases': robots,
            'task': 'insert_key_ext_collective_demo',
            'method': 'cmaes'
        }
        rpc_call(server_url, 'learn_task', params)

    @dispatcher.add_method
    def c_unlock_brakes(**kwargs):
        robots = get_cluster()
        for r in robots:
            params = {
                'method': 'unlock_brakes',
                'alias': r,
                'parameters': {
                    None: None
                }
            }
            rpc_call(server_url, 'relay_command_to_robot', params)

    @dispatcher.add_method
    def c_lock_brakes(**kwargs):
        robots = get_cluster()
        for r in robots:
            params = {
                'method': 'lock_brakes',
                'alias': r,
                'parameters': {
                    None: None
                }
            }
            rpc_call(server_url, 'relay_command_to_robot', params)

    @dispatcher.add_method
    def c_shutdown(**kwargs):
        robots = get_cluster()
        for r in robots:
            params = {
                'method': 'shutdown',
                'alias': r,
                'parameters': {
                    None: None
                }
            }
            rpc_call(server_url, 'relay_command_to_robot', params)

    @dispatcher.add_method
    def c_pack_pose(**kwargs):
        robots = get_cluster()
        for r in robots:
            params = {
                'method': 'shutdown',
                'alias': r,
                'parameters': {
                    None: None
                }
            }
            rpc_call(server_url, 'pack_pose', params)

    @dispatcher.add_method
    def c_open_gripper(**kwargs):
        robots = get_cluster()
        for r in robots:
            params = {
                'method': 'release_object',
                'alias': r,
                'parameters': {
                    None: None
                }
            }
            rpc_call(server_url, 'relay_command_to_robot', params)

    @dispatcher.add_method
    def c_close_gripper(**kwargs):
        robots = get_cluster()
        for r in robots:
            params = {
                'method': 'grasp_object',
                'alias': r,
                'parameters': {
                    'id': 'none'
                }
            }
            rpc_call(server_url, 'relay_command_to_robot', params)

    @dispatcher.add_method
    def c_home_gripper(**kwargs):
        robots = get_cluster()
        for r in robots:
            params = {
                'method': 'home_gripper',
                'alias': r,
                'parameters': {
                    None: None
                }
            }
            rpc_call(server_url, 'relay_command_to_robot', params)

    @dispatcher.add_method
    def open_gripper(**kwargs):
        rpc_call('http://localhost:8383', 'release_object')

    @dispatcher.add_method
    def close_gripper(**kwargs):
        rpc_call('http://localhost:8383', 'grasp_object', {'id': 'none'})

    @dispatcher.add_method
    def c_stop(**kwargs):
        me = get_own_id()
        robots = [me] + get_cluster()

        params = {
            'agent': me,
        }
        rpc_call(server_url, 'stop_learning', params)
        params = {
            'method': 'stop_task',
            'alias': robots,
            'parameters': {
                'nominal': True
            }
        }
        rpc_call(server_url, 'relay_command_to_collective', params)

    @dispatcher.add_method
    def l_stop(**kwargs):
        rpc_call('http://localhost:9002', 'stop_learn')
        rpc_call('http://localhost:8383', 'stop_task', {'nominal': True})

    @dispatcher.add_method
    def c_getKey(**kwargs):
        start_task_cluster('extract_object', 'msrm', {'object': 'key', 'hole': 'lock', 'joint': True}, True)

    @dispatcher.add_method
    def c_insertKey(**kwargs):
        start_task_cluster('insert_object', 'msrm', {'object': 'key', 'hole': 'lock', 'joint': True, 'release': True},
                           True)

    @dispatcher.add_method
    def c_teachKey(**kwargs):
        robots = get_cluster()

        for r in robots:
            response_r = rpc_call(server_url, "get_hostname", {'alias': r})
            if response_r["result"]["hostname"] is None:
                print("Could not reach robot " + r)
                continue

            hostname = response_r["result"]["hostname"]
            print('Teaching robot ' + hostname)

            rpc_call('http://' + hostname + ':8383', 'teach_object', {'id': kwargs['object']})
            rpc_call('http://' + hostname + ':8383', 'grasp_object', {'id': kwargs['object']})
            rpc_call('http://' + hostname + ':8383', 'teach_object', {'id': kwargs['hole']})
            rpc_call('http://' + hostname + ':8383', 'release_object')

    @dispatcher.add_method
    def c_goodbye(**kwargs):
        start_task_cluster('move_to_joint_pose', 'msrm', {'pose': 'goodbye'})
        rpc_call('http://localhost:8383', 'start_task',
                 {'task_id': 'move_to_joint_pose', 'parameters': {'pose': 'goodbye'}})

    @dispatcher.add_method
    def l_features_highImp(**kwargs):
        rpc_call('http://localhost:8383', 'start_task',
                 {'task_id': 'feature_impedance', 'parameters': {'K': [1500, 1500, 1500, 150, 150, 150]}})

    @dispatcher.add_method
    def l_features_lowImp(**kwargs):
        rpc_call('http://localhost:8383', 'start_task',
                 {'task_id': 'feature_impedance', 'parameters': {'K': [200, 200, 200, 20, 20, 20]}})

    @dispatcher.add_method
    def l_features_colDet(**kwargs):
        rpc_call('http://localhost:8383', 'start_task',
                 {'task_id': 'feature_collision_detection', 'parameters': {'pose_init': 'feature_default'}})

    @dispatcher.add_method
    def l_features_force(**kwargs):
        rpc_call('http://localhost:8383', 'start_task',
                 {'task_id': 'feature_force_control', 'parameters': {'pose_init': 'feature_default'}})

    @dispatcher.add_method
    def l_learning_teachObject(**kwargs):

        if "object" not in kwargs:
            print('Object parameter missing.')
            return

        object = kwargs["object"]
        hole = 'none'
        if object == 'key_abus_e30':
            hole = 'lock_abus_e30'

        if object == 'key_latch':
            hole = 'lock_latch'

        if object == 'key_old':
            hole = 'lock_old'

        if object == 'key':
            hole = 'lock'

        if hole == 'none':
            print(object + 'is not a valid object.')
            return

        rpc_call('http://localhost:8383', 'teach_object', {'id': object})
        rpc_call('http://localhost:8383', 'grasp_object', {'id': object})
        rpc_call('http://localhost:8383', 'teach_object', {'id': hole})
        rpc_call('http://localhost:8383', 'release_object')

    @dispatcher.add_method
    def l_learning_learnInsertion(**kwargs):

        if "object" not in kwargs:
            print('Object parameter missing.')
            return

        object = kwargs["object"]
        task = 'insert_' + object

        params = {
            'task': task,
            'method': 'cmaes',
            'overwrite': True,
            'url': ['http://localhost:8383']
        }
        rpc_call('http://localhost:9002', 'learn_task', params)

    @dispatcher.add_method
    def l_learning_insert_object(**kwargs):

        if "object" not in kwargs:
            print('Object parameter missing.')
            return

        object = kwargs["object"]
        hole = 'none'
        if object == 'key_abus_e30':
            hole = 'lock_abus_e30'

        if object == 'key_latch':
            hole = 'lock_latch'

        if object == 'key_old':
            hole = 'lock_old'

        if object == 'key':
            hole = 'lock'

        if hole == 'none':
            print(object + 'is not a valid object.')
            return

        rpc_call('http://localhost:8383', 'start_task', {'task_id': 'insert_object',
                                                         'parameters': {'object': object, 'hole': hole, 'joint': True,
                                                                        'emotions': True}})
    @dispatcher.add_method
    def c_teach_pose(**kwargs):
        teach_object_collective(kwargs['id'])

    #---------------------Merkel Demo Stuff-------------------------

    @dispatcher.add_method
    def kill_task(**kwargs):
        rpc_call(url_garmi_left, 'stop_task', {'nominal': True})
        rpc_call(url_garmi_right, 'stop_task', {'nominal': True})
        rpc_call(url_parti_left, 'stop_task', {'nominal': True})
        rpc_call(url_parti_right, 'stop_task', {'nominal': True})

    @dispatcher.add_method
    def release_garmi(**kwargs):
        rpc_call(url_garmi_left, 'release_object')
        rpc_call(url_garmi_right, 'release_object')

    @dispatcher.add_method
    def home(**kwargs):
        rpc_call(url_garmi_left, 'start_task',
                    {'task_id': 'move_to_cart_pose', 'parameters': {'pose': 'goodbye'}}) #TODO cart pose
        rpc_call(url_garmi_right, 'start_task',
                    {'task_id': 'move_to_cart_pose', 'parameters': {'pose': 'goodbye'}}) #TODO cart pose
        rpc_call(url_parti_left, 'start_task',
                    {'task_id': 'move_to_cart_pose', 'parameters': {'pose': 'goodbye'}}) #TODO cart pose
        rpc_call(url_parti_right, 'start_task',
                    {'task_id': 'move_to_cart_pose', 'parameters': {'pose': 'goodbye'}}) #TODO cart pose

    @dispatcher.add_method
    def telepresence(**kwargs):

        # Left side
        params = {
            'task_id': 'telepresence',
            'parameters': {
                'master': True,
                'alias_peer': slave_left
            }
        }
        print(master_left)
        print(slave_left)
        rpc_call(url_parti_left, 'start_task', params)
        response_state = rpc_call(url_parti_left, "get_state")
        
        print(response_state["result"]["q"])
        # input("Sync others")
        params = {
            'task_id': 'telepresence',
            'parameters': {
                'q_0': response_state["result"]["q"],
                'master': False,
                'alias_peer': master_left
            }
        }
        rpc_call(url_garmi_left, 'start_task', params)

        #Right side
        params = {
            'task_id': 'telepresence',
            'parameters': {
                'master': True,
                'alias_peer': slave_right
            }
        }
        print(master_right)
        print(slave_right)
        rpc_call(url_parti_right, 'start_task', params)
        response_state = rpc_call(url_parti_right, "get_state")
        print(response_state["result"]["q"])
        # input("Sync others")
        params = {
            'task_id': 'telepresence',
            'parameters': {
                'master': False,
                'q_0': response_state["result"]["q"],
                'alias_peer': master_right
            }
        }
        rpc_call(url_garmi_right, 'start_task', params)

    @dispatcher.add_method
    def grasp_garmi(**kwargs):
        rpc_call(url_garmi_left, 'grasp_object')
        rpc_call(url_garmi_right, 'grasp_object')

    @dispatcher.add_method
    def hold_position(**kwargs):
        rpc_call(url_garmi_left, 'start_task',
                 {'task_id': 'feature_impedance', 'parameters': {'K': [1500, 1500, 1500, 150, 150, 150],'pose_init': 'diagnostic_pose'}})
        rpc_call(url_garmi_right, 'start_task',
                 {'task_id': 'feature_impedance', 'parameters': {'K': [1500, 1500, 1500, 150, 150, 150],'pose_init': 'diagnostic_pose'}})
                 
    @dispatcher.add_method
    def l_teach_pose_garmi_parti(**kwargs):
        rpc_call(url_garmi_left, 'teach_object', {'id': kwargs['object']})
        rpc_call(url_garmi_right, 'teach_object', {'id': kwargs['object']})
        rpc_call(url_parti_left, 'teach_object', {'id': kwargs['object']})
        rpc_call(url_parti_right, 'teach_object', {'id': kwargs['object']})
        
    @dispatcher.add_method
    def l_teach_pose(**kwargs):
        rpc_call(url_garmi_left, 'teach_object', {'id': kwargs['object']})
        rpc_call(url_garmi_right, 'teach_object', {'id': kwargs['object']})
        
    @dispatcher.add_method
    def l_teach_pose_tele(**kwargs):
        rpc_call(url_garmi_left, 'teach_object', {'id': kwargs['object']})
        rpc_call(url_garmi_right, 'teach_object', {'id': kwargs['object']})
    
    @dispatcher.add_method
    def l_rehab_init(**kwargs):
        rpc_call(url_garmi_right, 'start_task', 
                 {'task_id':'move_to_joint_pose', "parameters" : {"pose" : "pose_init_rehab", "q_g" : [2.85879,1.2852,-2.55731,-1.93035,-1.1531,1.19087,0.0213086]}})

    @dispatcher.add_method
    def l_rehab_start(**kwargs):
        stiffness = kwargs["stiffness"]
        speed = kwargs["speed"]
        motion = kwargs["motion"]
        rpc_call(url_garmi_right, 'start_task', {'task_id':'rehab_task', "parameters" : {"speed" : speed, "stiffness" : stiffness, "motion" : motion}}) 
        
    @dispatcher.add_method
    def l_rehab_stop(**kwargs):
        rpc_call(url_garmi_right, 'stop_task', {'nominal': True})
        rpc_call(url_garmi_right, 'release_object')

    @dispatcher.add_method
    def l_init(**kwargs):
        rpc_call(url_garmi_right, 'start_task',
                 {'task_id':'move_to_joint_pose', "parameters" : {"pose" : "diagnostic_goal"}})
        rpc_call(url_garmi_left, 'start_task',
                 {'task_id':'move_to_joint_pose', "parameters" : {"pose" : "diagnostic_goal"}})
        rpc_call(url_parti_right, 'start_task',
                 {'task_id':'move_to_joint_pose', "parameters" : {"pose" : "diagnostic_goal"}})
        rpc_call(url_parti_left, 'start_task',
                 {'task_id':'move_to_joint_pose', "parameters" : {"pose" : "diagnostic_goal"}})



if __name__ == '__main__':
    A = AppServer()
    A.init(9003)
