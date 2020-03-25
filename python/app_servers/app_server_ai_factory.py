#!/usr/bin/python3 -u
import sys, os
sys.path.append(os.path.abspath(os.path.join('..', "..")))

from werkzeug.wrappers import Request, Response
from werkzeug.serving import run_simple

from jsonrpc import JSONRPCResponseManager, dispatcher

from threading import Thread
import time
import netifaces as ni
import socket
import copy
import random

from python.utils.ws_client import *
from python.utils.rpc_client import rpc_call
from python.utils.rpc_client import learn_task

server_url = 'http://tueirsi-nc-032.local:8390'
screen_url = 'http://192.168.5.15:4000'
camera_url = 'http://10.162.15.69:8910'
visualizer_url = 'http://192.168.5.15:4000'

flag_knowledge = False
flag_view = False


cluster_msrm = {'msrm-1': {'hostname': 'collective-panda-001.local',
  'ip': '192.168.5.7',
  'online': True},
 'msrm-10': {'hostname': 'collective-panda-010.local',
  'ip': '192.168.5.43',
  'online': True},
 'msrm-11': {'hostname': 'collective-panda-011.local',
  'ip': '192.168.5.13',
  'online': True},
 'msrm-12': {'hostname': 'collective-panda-012.local',
  'ip': '192.168.5.34',
  'online': True},
 'msrm-2': {'hostname': 'collective-panda-002.local',
  'ip': '192.168.5.31',
  'online': True},
 'msrm-3': {'hostname': 'collective-panda-003.local',
  'ip': '192.168.5.26',
  'online': True},
 'msrm-4': {'hostname': 'collective-panda-004.local',
  'ip': '192.168.5.4',
  'online': True},
 'msrm-5': {'hostname': 'collective-panda-005.local',
  'ip': '192.168.5.41',
  'online': True},
 'msrm-6': {'hostname': 'collective-panda-006.local',
  'ip': '192.168.5.17',
  'online': True},
 'msrm-7': {'hostname': 'collective-panda-007.local',
  'ip': '192.168.5.16',
  'online': True},
 'msrm-8': {'hostname': 'collective-panda-008.local',
  'ip': '192.168.5.5',
  'online': True},
 'msrm-9': {'hostname': 'collective-panda-009.local',
  'ip': '192.168.5.30',
  'online': True}}



def check_collective():
    rtn = rpc_call(server_url, 'get_collective')
    collective = []
    for key, val in rtn['result'].items():
        if val['online'] is True:
            collective.append(key)
    return collective


def get_cluster(cluster):
    rtn = rpc_call(server_url, 'get_cluster',{'cluster': cluster}, timeout=1)
    if rtn is None:
        if cluster == "msrm":
            cluster = cluster_msrm
        else:
            return None
    else:
        cluster = rtn['result']
    own_id = get_own_id()
    if own_id in cluster:
        del cluster[own_id]

    cluster_online = dict()
    for key, val in cluster.items():
        if val["online"] is True:
            cluster_online[key] = copy.deepcopy(val)

    return cluster_online


def get_clusters():
    own_id = get_own_id()

    clusters = ["msrm"]

    clusters_online = dict()

    for c in clusters:
        rtn = rpc_call(server_url, 'get_cluster', {'cluster': c}, timeout=1)
        if rtn is None:
            if c == "msrm":
                cluster = cluster_msrm
            else:
                print("Failed to get cluster " + c)
                continue
        else:
            cluster = rtn['result']
        if cluster is None:
            continue
        if own_id in cluster:
            cluster.remove(own_id)
        cluster_online = dict()
        for key, val in cluster.items():
            if val["online"] is True:
                cluster_online[key] = copy.deepcopy(val)

        clusters_online[c] = cluster_online
    return clusters_online


def get_collective():
    own_id = get_own_id()

    clusters = ["msrm"]

    collective_online = dict()

    for c in clusters:
        rtn = rpc_call(server_url, 'get_cluster', {'cluster': c}, timeout=1)
        if rtn is None:
            if c == "msrm":
                cluster = cluster_msrm
            else:
                print("Failed to get cluster " + c)
                continue
        else:
            cluster = rtn['result']
        if cluster is None:
            continue
        if own_id in cluster:
            cluster.remove(own_id)
        for key, val in cluster.items():
            if val["online"] is True:
                collective_online[key] = copy.deepcopy(val)

    return collective_online


def get_own_id():
    hostname = socket.gethostbyaddr(get_ip_address('tap0'))[0]
    hostname = hostname.lower() + '.local'

    id = 'extern_tmp'
    rtn = rpc_call(server_url, 'who_am_i', {'hostname': hostname})
    if rtn is None:
        return 'none'
    if rtn['result']['id'] == 'none':
        rpc_call(server_url, 'remove_robot', {'alias': 'extern_tmp'})
        rtn = rpc_call(server_url, 'add_robot', {'hostname':hostname,'alias': id})
    else:
        id = rtn['result']['id']

    return id


def get_ip_address(ifname):
    return ni.ifaddresses(ifname)[ni.AF_INET][0]['addr']


def short_teach_insertion(hostname, object, hole):
    call_method(hostname, "grasp_object",
                {"object": "none", "width": 0., "speed": 0.05, "force": 60., "check_width": False})
    call_method(hostname, "teach_object", {"object": object, "teach_width": True,
                                                              "reference_frame": "none", "is_reference_frame": False})
    call_method(hostname, "release_object", {"width": 0.05, "speed": 0.2})
    call_method(hostname, "grasp_object", {"object": object,"width":0.,"speed":0.05,"force":60.,"check_width":False})
    call_method(hostname, "teach_object", {"object": hole, "teach_width": False,
                                                              "reference_frame": "none", "is_reference_frame": False})
    call_method(hostname, "release_object",{"width":0.05,"speed":0.2})


def start_task_robot(task, robot, params=None, queue=False, ):
    params = {
        'method': 'start_task',
        'alias': robot,
        'parameters': {
            'task_id': task,
            'queue_task': queue,
            'parameters': params
        }
    }
    rpc_call(server_url, 'relay_command_to_robot', params)


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
    return call_method('http://' + hostname + ':8383', "get_state")


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


def set_grasped_object_cluster(o, cluster):
    robots = get_cluster(cluster)
    for key, val in robots.items():
        t = Thread(target=call_method, args=(val["hostname"], "set_grasped_object", {"object": o},))
        t.start()


def grasp_object_cluster(o, cluster):
    robots = get_cluster(cluster)
    for key, val in robots.items():
        t = Thread(target=rpc_call, args=("http://" + val["hostname"] + ":8383", "grasp_object", {"object": o,
                                                                                                  "width":0., "speed": 0.2, "force": 50, "check_width": True},))
        t.start()


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
    def c_telepresence_bi(**kwargs):
        master = socket.gethostbyaddr(get_ip_address('tap0'))[0]
        master = master.lower() + '.local'
        rtn = call_method(server_url, "get_hostname", {'alias': kwargs["slave"]})
        slave = rtn["result"]["hostname"]
        master = "tueirsi-nc-030.local"
        slave = "tueirsi-nc-015.local"

        if master == slave:
            print('Master and slave must not be identical.')
            return

        params = {
            'parameters': {
                'master': True,
                'alias_peer': slave,
                'joint_mode': True
            }
        }
        print(master)
        print(slave)
        start_task(master, "telepresence", parameters=params)
        response_state = call_method(master, "get_state")
        print(response_state["result"]["q"])
        # input("Sync others")
        params = {
            'parameters': {
                'master': False,
                'q_0': response_state["result"]["q"],
                'alias_peer': master,
                'joint_mode': True
            }
        }
        start_task(slave, "telepresence", parameters=params)

    @dispatcher.add_method
    def c_telepresence_uni_master(**kwargs):
        master = socket.gethostbyaddr(get_ip_address('tap0'))[0]
        master = master.lower() + '.local'

        rtn = start_task(master, "move_to_joint_pose", {'parameters': {'pose': 'feature_default'}})
        print(rtn)
        if rtn['result'] is False:
            return
        wait_for_task(master, rtn['result']['task_uuid'])

        params = {
            'parameters': {
                'master': True,
                'alias_peer': '225.0.0.1',
                'bilateral': False,
                'repeater': False,
                'joint_mode': True
            }
        }
        start_task(master, "telepresence", params, True)

    @dispatcher.add_method
    def c_telepresence_uni_add(**kwargs):

        if 'slave' not in kwargs:
            return

        master = socket.gethostbyaddr(get_ip_address('tap0'))[0]
        master = master.lower() + '.local'

        response_state = call_method(master, "get_state")

        params = {
            'method': 'start_task',
            'alias': kwargs['slave'],
            'parameters': {
                'task_id': 'telepresence',
                'parameters': {
                    'master': False,
                    'q_0': response_state["result"]["q"],
                    'alias_peer': '225.0.0.1',
                    'repeater': False,
                    'joint_mode': True
                }
            }
        }
        rpc_call(server_url, 'relay_command_to_robot', params)

    @dispatcher.add_method
    def c_telepresence_uni_remove(**kwargs):
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

    @dispatcher.add_method
    def c_unlock_brakes(**kwargs):
        if "cluster" not in kwargs:
            cluster = "msrm"
        else:
            cluster = kwargs["cluster"]
        robots = get_cluster(cluster)
        for key, val in robots.items():
            t = Thread(target=call_method, args=(val["hostname"], 'unlock_brakes',))
            t.start()

    @dispatcher.add_method
    def c_lock_brakes(**kwargs):
        if "cluster" not in kwargs:
            cluster = "msrm"
        else:
            cluster = kwargs["cluster"]
        robots = get_cluster(cluster)
        for key, val in robots.items():
            t = Thread(target=call_method, args=(val["hostname"], 'lock_brakes',))
            t.start()

    @dispatcher.add_method
    def c_shutdown(**kwargs):
        if "cluster" not in kwargs:
            cluster = "msrm"
        else:
            cluster = kwargs["cluster"]
        robots = get_cluster(cluster)
        for key, val in robots.items():
            t = Thread(target=call_method, args=(val["hostname"], 'shutdown',))
            t.start()

    @dispatcher.add_method
    def c_pack_pose(**kwargs):
        if "cluster" not in kwargs:
            cluster = "msrm"
        else:
            cluster = kwargs["cluster"]
        robots = get_cluster(cluster)
        for key, val in robots.items():
            t = Thread(target=call_method, args=(val["hostname"], 'pack_pose',))
            t.start()

    @dispatcher.add_method
    def c_open_gripper(**kwargs):
        if "cluster" not in kwargs:
            cluster = "msrm"
        else:
            cluster = kwargs["cluster"]
        robots = get_cluster(cluster)
        for key, val in robots.items():
            t = Thread(target=call_method, args=(val["hostname"], 'release_object',))
            t.start()

    @dispatcher.add_method
    def c_close_gripper(**kwargs):
        if "cluster" not in kwargs:
            cluster = "msrm"
        else:
            cluster = kwargs["cluster"]
        robots = get_cluster(cluster)
        for key, val in robots.items():
            t = Thread(target=call_method, args=(val["hostname"], 'release_object',))
            t.start()

    @dispatcher.add_method
    def c_home_gripper(**kwargs):
        if "cluster" not in kwargs:
            cluster = "msrm"
        else:
            cluster = kwargs["cluster"]
        robots = get_cluster(cluster)
        for key, val in robots.items():
            t = Thread(target=call_method, args=(val["hostname"], 'home_gripper',))
            t.start()

    @dispatcher.add_method
    def open_gripper(**kwargs):
        call_method('http://localhost:8383', 'release_object')

    @dispatcher.add_method
    def close_gripper(**kwargs):
        call_method('http://localhost:8383', 'grasp_object', {'object': 'none', "width": 0.0, "speed": 1.0, "force": 40, "check_width": False})

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
        stop_task("localhost", True)

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
    def l_features_highImp(**kwargs):
        start_task("localhost", "feature_impedance", {'parameters': {'K': [1500, 1500, 1500, 150, 150, 150]}})

    @dispatcher.add_method
    def l_features_lowImp(**kwargs):
        start_task("localhost", "feature_impedance", {'parameters': {'K': [200, 200, 200, 20, 20, 20]}})

    @dispatcher.add_method
    def l_features_colDet(**kwargs):
        start_task("localhost", "feature_collision_detection", {'parameters': {'pose_init': 'feature_default'}})

    @dispatcher.add_method
    def l_features_force(**kwargs):
        start_task("localhost", "feature_force_control", {'parameters': {'pose_init': 'feature_default'}})

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
    def l_teach_pose(**kwargs):
        rpc_call('http://localhost:8383', 'teach_object', {'id': kwargs['object']})

    @dispatcher.add_method
    def c_teach_pose(**kwargs):
        teach_object_collective(kwargs['id'])

    @dispatcher.add_method
    def c_aifactory_giveKey(**kwargs):
        global flag_knowledge
        flag_knowledge=False
        rpc_call(visualizer_url, 'robot_connect', {'on': False})
        rpc_call('http://10.162.15.69:8889', 'set_window', {'window': 'Google Chrome'})
        master = socket.gethostbyaddr(get_ip_address('tap0'))[0]
        master = master.lower() + '.local'
        start_task(master, 'move_to_joint_pose', {'pose': 'feature_default'})
        start_task(master, 'handover_object', {'object': 'key_abus_e30'}, True)
        # call tracking

    @dispatcher.add_method
    def c_aifactory_guide(**kwargs):
        master = socket.gethostbyaddr(get_ip_address('tap0'))[0]
        master = master.lower() + '.local'
        start_task(master, 'guiding_mode', {"parameters": {'mode': [0, 0, 0, 1, 1, 1]}})
        #rpc_call('http://10.162.15.69:8889', 'set_window', {'window': 'COLLECTIVE'})
        #rpc_call('http://10.162.15.69:8910','set_id',{'ID':28})
        # call tracking

    @dispatcher.add_method
    def c_aifactory_teach(**kwargs):
        master = socket.gethostbyaddr(get_ip_address('tap0'))[0]
        master = master.lower() + '.local'
        stop_task(master)
        # save lock pose

    @dispatcher.add_method
    def c_aifactory_insert(**kwargs):
        start_task("localhost", "open_lock", {'parameters': {'key': 'key_abus_e30', 'lock': 'lock_abus_e30'}})

    @dispatcher.add_method
    def c_aifactory_cinsert(**kwargs):
        start_task_cluster('insert_object', 'msrm', {'object': 'key', 'hole': 'lock', 'joint': True, 'release': False},
                           True)

    @dispatcher.add_method
    def c_aifactory_login_collective(**kwargs):
        collective = get_collective()
        print(collective)
        for key, val in collective.items():
            print("Login " + val["hostname"])
            t = Thread(target=call_method, args=(val["hostname"], "login_digital_twin"))
            t.start()
            # rpc_call("http://" + val["hostname"] + ":8383", "login_digital_twin")


    @dispatcher.add_method
    def c_aifactory_logout_collective(**kwargs):
        collective = get_collective()
        for key, val in collective.items():
            print("Logout " + val["hostname"])
            t = Thread(target=call_method, args=(val["hostname"], "logout_digital_twin"))
            t.start()
            # rpc_call("http://" + val["hostname"] + ":8383", "logout_digital_twin")

    @dispatcher.add_method
    def set_grasped_object(**kwargs):
        if "cluster" not in kwargs:
            cluster = "msrm"
        else:
            cluster = kwargs["cluster"]
        if "object" not in kwargs:
            object = "key"
        else:
            object = kwargs["object"]
        set_grasped_object_cluster(object, cluster)

    @dispatcher.add_method
    def c_aifactory_learn(**kwargs):

        print("LEARN")
        #rpc_call(visualizer_url, 'set_window', {'window': 'Franka'})
        #rpc_call(screen_url, 'set_window', {'window': 'FrankaPandaMobile'})
        set_grasped_object_cluster("key","msrm")
        #grasp_object_cluster("key", "irt")
        #grasp_object_cluster("key", "gap")
        #grasp_object_cluster("key", "vodafone")

        me = get_own_id()
        # collective = get_collective()
        collective = cluster_msrm
        host2alias = dict()
        for key, val in collective.items():
            host2alias[val["hostname"]] = key

        robots = []
        for key, val in collective.items():
            robots.append(val["hostname"])

        learn_task("localhost", "insertion", [0.1, 0.1, 0.1, 1, 0], "cmaes", robots, hosts=host2alias, setup=False)
        global flag_knowledge
        flag_knowledge=True

    @dispatcher.add_method
    def c_aifactory_teach_keys(**kwargs):
        if "cluster" not in kwargs:
            print("No cluster has been specified.")
            return
        robots = get_cluster(kwargs["cluster"])
        for key, val in robots.items():
            short_teach_insertion(val["hostname"], "key", "lock")

    @dispatcher.add_method
    def c_aifactory_stop(**kwargs):
        rpc_call("http://localhost:9002", 'stop_learn')
        robots = get_collective()
        stop_task("localhost", True)
        for key, val in robots.items():
            t = Thread(target=stop_task, args=(val["hostname"], True,))
            t.start()

    @dispatcher.add_method
    def c_aifactory_disconnect(**kwargs):
        master = socket.gethostbyaddr(get_ip_address('tap0'))[0]
        master = master.lower() + '.local'
        stop_task(master)

    @dispatcher.add_method
    def c_aifactory_connect_slave(**kwargs):
        if 'slaves' not in kwargs:
            return

        #print('Connecting slave ' + kwargs["slave"])
        master = socket.gethostbyaddr(get_ip_address('tap0'))[0]
        master = master.lower() + '.local'

        response_state = rpc_call('http://' + master + ':8383', "get_state")
        slaves = kwargs["slaves"]
        print('SLAVES')
        print(slaves)

        host2alias={
            "tueirsi-nc-005.local":"msrm-6",
            "tueirsi-nc-012.local": "msrm-2",
            "tueirsi-nc-014.local": "msrm-7",
            "tueirsi-nc-015.local": "msrm-1",
            "tueirsi-nc-016.local": "msrm-4",
            "tueirsi-nc-018.local": "msrm-5",
            "tueirsi-nc-024.local": "msrm-8",
            "tueirsi-nc-026.local": "msrm-12",
            "tueirsi-nc-030.local": "msrm-9",
            "tueirsi-nc-031.local": "msrm-10",
            "tueirsi-nc-033.local": "msrm-11",
            "tueirsi-nc-013.local": "msrm-3",
        }
        for i in range(len(slaves)):
            params = {
                'method': 'start_task',
                'alias': host2alias[slaves[i]],
                'parameters': {
                    'task_id': 'telepresence',
                    'parameters': {
                        'master': False,
                        'q_0': response_state["result"]["q"],
                        'alias_peer': '225.0.0.1',
                        'repeater': False,
                        'joint_mode': True
                    }
                }
            }
            t = Thread(target=rpc_call, args=(server_url, 'relay_command_to_robot', params,))
            t.start()

        # params = {
        #     'method': 'start_task',
        #     'alias': kwargs['slave'],
        #     'parameters': {
        #         'task_id': 'telepresence',
        #         'parameters': {
        #             'master': False,
        #             'q_0': response_state["result"]["q"],
        #             'alias_peer': '225.0.0.1',
        #             'repeater': False,
        #             'joint_mode': True
        #         }
        #     }
        # }
        # rpc_call(server_url, 'relay_command_to_robot', params)

    @dispatcher.add_method
    def c_aifactory_wipe_knowledge(**kwargs):
        pass


    @dispatcher.add_method
    def l_aifactory_learn_key(**kwargs):

        master = socket.gethostbyaddr(get_ip_address('tap0'))[0]
        master = master.lower() + '.local'

        response = rpc_call('http://' + master + ':8383', 'stop_task', {"nominal": True})
        if response is None:
            print("Could not stop master.")
            return

        time.sleep(1)

        rpc_call("http://" + master + ":8383", "grasp_object", {"id": "key_abus_e30"})

        learn_task(master, "insert_key_fail", "cmaes", ["http://" + master + ":8383"], terminate=False)

    @dispatcher.add_method
    def c_aifactory_disconnect_slave(**kwargs):
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
        print(params)
        r=rpc_call(server_url, 'relay_command_to_robot', params)
        print(r)

    @dispatcher.add_method
    def c_aifactory_stop2(**kwargs):
        rpc_call('http://localhost:8383', 'stop_task', {'nominal': True})

    @dispatcher.add_method
    def c_aifactory_vision_reinit(**kwargs):
        start_task_cluster('move_to_joint_pose','msrm',{'pose':'camera'})
        start_task('tueirsi-nc-028.local','move_to_joint_pose',{'pose':'camera'})
        time.sleep(2)
        rpc_call(camera_url, 'reinit')

    @dispatcher.add_method
    def c_aifactory_test(**kwargs):
        master = socket.gethostbyaddr(get_ip_address('tap0'))[0]
        master = master.lower() + '.local'
        response = stop_task(master, True)
        if response is None:
            print("Could not stop master.")
            return

        call_method(master, "set_grasped_object", {"object": "key_abus_e30"})

        time.sleep(1)
        global flag_knowledge
        #rpc_call('http://10.162.15.69:8889', 'set_window', {'window': 'Google Chrome'})
        rpc_call('http://localhost:8383','grasp_object',{'object':'key_abus_e30',"width":0.,"speed":0.1,"force":50.,"check_width":False})
        if flag_knowledge is True:
            start_task('localhost', 'open_lock',{'parameters': {'key': 'key_abus_e30', 'lock': 'lock_abus_e30'},
                                                             'subtasks':
                                                                 {
                                                                     'insert_object':{
                                                                         'skills':{
                                                                             'approach_joint': {
                                                                                 'skill': {
                                                                                     'q_g_offset': [0, -0.6, 0, -0.0, 0,
                                                                                                    -0.2, 0]
                                                                                 }
                                                                             }
                                                                         }
                                                                     }
                                                                 }})
            start_task('localhost', 'react_to_event', {'parameters': {'event': 'inserted'}}, True)
        else:
            start_task('localhost', 'insert_object',{'parameters': {'object': 'key_abus_e30',
                                                                            'hole': 'lock_abus_e30', 'joint': True,
                                                                            'emotions': True}, 'skills': {
                    'insertion': {
                        'skill': {
                            'speed': [0.04, 0.1],
                            'wiggle_a_r': [1]
                        },
                        'control': {
                            'K_0': [100, 100, 50, 10, 10, 10],
                            'F_ff_0': [0, 0, 2, 0, 0, 0]
                        }
                    },
                    'approach_joint': {
                        'skill': {
                            'q_g_offset': [0,-0.6,0,-0.0,0,-0.2,0]
                        }
                    }
                }})
            start_task('localhost', 'extract_object', {'parameters': {'object': 'key_abus_e30',
                                                                            'hole': 'lock_abus_e30'}}, True)
            start_task('localhost','react_to_event', {'parameters': {'event': 'inserted'}}, True)

    @dispatcher.add_method
    def c_aifactory_search(**kwargs):
        # switch to camera view
        #r = rpc_call(screen_url,'set_window',{'window':'Video'})
        r = rpc_call(screen_url, 'set_window', {'window': 'msrm-MS'})
        robots = get_cluster("msrm").copy()
        for key, val in robots.items():
            params = {
                'method': 'start_task',
                'alias': key,
                'parameters': {
                    'task_id': 'locate_object',
                    'parameters': {
                        'object': 'lock',
                        'search_poses': ['lock_search_pose_1','lock_search_pose_2','lock_search_pose_3','lock_search_pose_4',
                                         'lock_search_pose_5','lock_search_pose_6'],
                        'pose_failsafe': 'lock_search_failsafe'
                    },
                    "skills": {
                        "move": {
                            "skill":{
                                "acc": [0.1],
                                "speed": [0.2]
                            }
                        }
                    }
                }
            }
            t = Thread(target=rpc_call, args=(server_url, 'relay_command_to_robot', params,))
            t.start()

    @dispatcher.add_method
    def c_aifactory_connect(**kwargs):
        cluster_d = "msrm"
        if "cluster" in kwargs:
            cluster_d = kwargs["cluster"]

        # switch to digital twin

        master = socket.gethostbyaddr(get_ip_address('tap0'))[0]
        master = master.lower() + '.local'

        response = stop_task(master, True)
        if response is None:
            print("Could not stop master.")
            return

        time.sleep(1)

        cluster = get_cluster(cluster_d)

        if not cluster:
            print("Cluster " + cluster_d + " has no available robots.")
            return

        repeaters = []
        repeaters.append(random.choice(list(cluster.keys())))

        # for key, val in clusters.items():
        #     if not val:
        #         continue
        #     slaves.extend(val.keys())
        #     repeaters.append(random.choice(list(val.keys())))

        rtn = start_task(master, "move_to_joint_pose",{'parameters': {'pose': 'feature_default'}})

        if rtn is None or rtn['result'] is False or "task_uuid" not in rtn["result"]:
            return
        wait_for_task(master, rtn['result']['task_uuid'])
        if response is None:
            print("Master did not respond.")
            return

        repeaters_hostnames = []

        for r in repeaters:
            repeaters_hostnames.append(cluster[r]["hostname"])

        params = {
            'parameters': {
                'master': True,
                'alias_peer': repeaters_hostnames,
                'bilateral': False,
                'repeater': False,
                'joint_mode': True
            }
        }
        response = start_task(master, "telepresence", params)
        if response is None:
            print("Failed to call master.")
            return

        # response = rpc_call('http://tueirsi-nc-032.local:8380', 'reset')
        # if response is None:
        #     print("Failed to reset telepresence relay.")
        #     return
        #
        # for r in repeaters:
        #     response = rpc_call('http://tueirsi-nc-032.local:8380', 'add_receiver', {"receiver": r})
        #     if response is None:
        #         return
        #
        # response = rpc_call('http://tueirsi-nc-032.local:8380', 'start')
        # if response is None:
        #     print("Failed to call telepresence relay.")
        #     return

        response_state = call_method(master, "get_state")
        if response_state is None:
            print("Failed to call master for state.")
            return
        params = {
            'parameters': {
                'master': False,
                'q_0': response_state["result"]["q"],
                'alias_peer': [master],
                'repeater': True,
                'joint_mode': True
            }
        }
        for r in repeaters_hostnames:
            response_repeater = start_task(r, "telepresence", params)
            if response_repeater is None:
                print("Failed to call repeater " + r)
                return

        for key, val in cluster.items():
            if key in repeaters:
                continue
            params = {
                'parameters': {
                    'master': False,
                    'q_0': response_state["result"]["q"],
                    'alias_peer': ['225.0.0.1'],
                    'repeater': False,
                    'joint_mode': True
                }
            }
            print(val["hostname"])
            t = Thread(target=start_task, args=(val["hostname"], 'telepresence', params,))
            t.start()
        #rpc_call(visualizer_url,'robot_connect',{'on':True})

    @dispatcher.add_method
    def c_aifactory_reset(**kwargs):
        global flag_knowledge
        flag_knowledge = False

    @dispatcher.add_method
    def c_aifactory_idle(**kwargs):
        master = socket.gethostbyaddr(get_ip_address('tap0'))[0]
        master = master.lower() + '.local'
        rpc_call("http://" + master + ":8383", "login_digital_twin")
        start_task(master, 'observe', {"parameters": {'watch_poses': ['pose_sleep']},
                                       "skills": {
                                           "watch": {
                                               "skill": {
                                                   "tap_to_finish": True
                                               },
                                               "user": {
                                                   "F_max": [20, 20, 20, 15, 15, 15],
                                                   "tau_max": [15, 15, 15, 15, 10, 10, 10]
                                               }
                                           }
                                       }})
        start_task(master, 'move_to_joint_pose', {"parameters": {'pose': "pose_attention"}}, queue=True)
        start_task(master, 'guiding_mode', queue=True)

    @dispatcher.add_method
    def b_aifactory_toggle_view(**kwargs):
        if 'view' not in kwargs:
            return

        if kwargs['view'] is True:
            rpc_call('http://10.162.15.69:8889', 'set_window', {'window': 'COLLECTIVE'})
            rpc_call('http://10.162.15.69:8910', 'set_id', {'ID': 0})
        else:
            rpc_call('http://10.162.15.69:8889', 'set_window', {'window': 'Google Chrome'})

    @dispatcher.add_method
    def c_aifactory_pdf(**kwargs):
        rpc_call('http://10.162.15.69:8889', 'set_window', {'window': 'Gesundheitssektor'})

    @dispatcher.add_method
    def c_aifactory_down(**kwargs):
        rpc_call('http://10.162.15.69:8889', 'key_stroke', {'key': 'n'})

    @dispatcher.add_method
    def c_aifactory_handshake(**kwargs):

        if "slave" not in kwargs:
            alias_slave = "vodafone-2"
        else:
            alias_slave = kwargs["slave"]

        master = socket.gethostbyaddr(get_ip_address('tap0'))[0]
        master = master.lower() + '.local'
        rtn = rpc_call(server_url, "get_hostname", {'alias': alias_slave})
        slave = rtn["result"]["hostname"]

        if master == slave:
            print('Master and slave must not be identical.')
            return

        params = {
            'parameters': {
                'master': True,
                'alias_peer': [slave],
                'bilateral': True,
                'repeater': False,
                'joint_mode': True
            }
        }
        print(alias_slave)
        print(master)
        start_task(master, 'telepresence', params)
        response_state = call_method(master, "get_state")
        print(response_state["result"]["q"])
        # input("Sync others")
        params = {
            'parameters': {
                'master': False,
                'q_0': response_state["result"]["q"],
                'alias_peer': [master],
                'bilateral': True,
                'repeater': False,
                'joint_mode': True
            }
        }
        start_task(slave, 'telepresence', params)

    @dispatcher.add_method
    def telepresence_bilateral(**kwargs):

        if "slave" not in kwargs:
            print("No slave determined.")
        else:
            alias_slave = kwargs["slave"]

        master = socket.gethostbyaddr(get_ip_address('tap0'))[0]
        master = master.lower() + '.local'
        rtn = rpc_call(server_url, "get_hostname", {'alias': alias_slave})
        slave = rtn["result"]["hostname"]

        if master == slave:
            print('Master and slave must not be identical.')
            return

        params = {
            'parameters': {
                'master': True,
                'alias_peer': ["tueirsi-nc-032.local"],
                'bilateral': True,
                'repeater': False,
                'joint_mode': True
            },
            "skills":{
                "master":{
                    "skill":{
                        "port_t": [8001]
                    }
                }
            }
        }
        print(alias_slave)
        print(master)
        start_task(master, 'telepresence', params)
        response_state = call_method(master, "get_state")
        print(response_state["result"]["q"])
        # input("Sync others")
        params = {
            'parameters': {
                'master': False,
                'q_0': response_state["result"]["q"],
                'alias_peer': ["tueirsi-nc-032.local"],
                'bilateral': True,
                'repeater': False,
                'joint_mode': True
            },
            "skills": {
                "slave": {
                    "skill": {
                        "port_t": 8002
                    }
                }
            }
        }
        start_task(slave, 'telepresence', params)

    @dispatcher.add_method
    def l_aifactory_grasp_key(**kwargs):
        start_task("localhost", "extract_object", {"parameters": {"object": "key_abus_e30", "hole": "lock_abus_e30", "joint": True}})

    @dispatcher.add_method
    def c_aifactory_grasp_keys(**kwargs):
        if "cluster" not in kwargs:
            print("No cluster defined.")
            return
        robots = get_cluster(kwargs["cluster"])
        for key, val in robots.items():
            t = Thread(target=start_task, args=(val["hostname"], "extract_object", {"parameters": {"object": "key", "hole": "lock", "joint": True}},))
            t.start()

    @dispatcher.add_method
    def c_aifactory_insert_keys(**kwargs):
        if "cluster" not in kwargs:
            print("No cluster defined.")
            return
        robots = get_cluster(kwargs["cluster"])
        for key, val in robots.items():
            t = Thread(target=start_task, args=(val["hostname"], "insert_object", {"parameters": {"object": "key", "hole": "lock", "joint": True, "release": True}},))
            t.start()


if __name__ == '__main__':
    A = AppServer()
    A.init(9003)
