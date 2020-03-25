import pymongo
from pymongo import MongoClient
import requests
import json
import os
from os import listdir
from os.path import isfile, join
import subprocess

server_url = 'tueirsi-nc-032.local'


def rpc_call(url, method, params=None):
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
        response = requests.post(url, data=json.dumps(payload), headers=headers).json()
    except requests.Timeout:
        print('Timeout, server has terminated or does not exist.')
        response = None
    except requests.ConnectionError:
        print('Connection error, target url not reachable.')
        response = None

    return response


def ping_host(hostname):
    return subprocess.call('ping -c 2 ' + hostname, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)


def create_knowledge_base(db_url):
    print("Setting up default knowledge base.")
    print("---------------------------------")
    print("Setting up parameters...",end=" ")
    upload_default_parameters(db_url, True)
    print("done.")
    print("Setting up skills...",end=" ")
    upload_default_skills(db_url, True)
    print("done.")
    print("Setting up tasks...",end=" ")
    upload_default_tasks(db_url, True)
    print("done.")
    print("Setting up objects...",end=" ")
    upload_default_objects(db_url, True)
    print("done.")
    print("Setting up reference frames...",end=" ")
    upload_default_reference_frames(db_url,True)
    print("done.")
    print("---------------------------------")
    print("Knowledge base is ready.")


def create_knowledge_base_for_collective():
    response = rpc_call('http://' + server_url + ':8390', "get_collective")
    robots = response["result"]

    for r in robots:
        response_r = rpc_call('http://' + server_url + ':8390', "get_hostname", {'alias': r})
        if response_r["result"]["hostname"] is None:
            print("Could not reach robot " + r)
            continue

        hostname = response_r["result"]["hostname"]
        create_knowledge_base(hostname)


def upload_default_reference_frames(db_url,overwrite=False):
    client = MongoClient('mongodb://' + db_url + ':27017')
    parameters = {
        "dummy": "dummy"
    }
    client.mios.reference_frames.insert_one(parameters)
    client.mios.reference_frames.delete_one({'dummy': 'dummy'})


def upload_default_parameters(db_url, overwrite=False):
    client = MongoClient('mongodb://' + db_url + ':27017')

    doc = client.mios.parameters.find_one({"type": 'control'})
    if doc is not None:
        if overwrite is False:
            print('Control parameter file already exists in database. '
                  'To overwrite set the overwrite flag of this function to True.')
            return
        else:
            client.mios.parameters.delete_one({'type': 'control'})

    parameters = {
        'type': 'control',

        # Adaptive Cartesian impedance controller
        'alpha': [0, 0, 0, 0, 0, 0],
        'beta': [0, 0, 0, 0, 0, 0],
        'gamma_a': [0, 0, 0, 0, 0, 0],
        'gamma_b': [0, 0, 0, 0, 0, 0],
        'K_0': [1500, 1500, 1500, 150, 150, 150],
        'F_ff_0': [0, 0, 0, 0, 0, 0],
        'L': [0, 0, 0, 0, 0, 0],
        'xi': [0.7, 0.7, 0.7, 0.7, 0.7, 0.7],
        'kappa': 5,
        'K_max': [2000, 2000, 2000, 200, 200, 200],
        'dK_max': [5000, 5000, 5000, 500, 500, 500],
        'F_ff_max': [30, 30, 30, 10, 10, 10],
        'dF_ff_max': [300, 300, 300, 100, 100, 100],

        # Joint impedance controller
        'K_theta': [500, 500, 500, 500, 300, 250, 200],
        'xi_theta': [0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7],

        # Force controller
        'f_cntr_k_p': [0, 0, 0, 0, 0, 0],
        'f_cntr_k_i': [0, 0, 0, 0, 0, 0],
        'f_cntr_k_d': [0, 0, 0, 0, 0, 0],
        'f_cntr_k_d_N': [0, 0, 0, 0, 0, 0],
        'f_cntr_d_max': [0, 0, 0],
        'f_cntr_phi_max': [0],
        'f_cntr_sf_on': False,
        'F_c_max': [30, 30, 30, 10, 10, 10],
        'dF_c_max': [300, 300, 300, 100, 100, 100],
        'f_cntr_active': [0, 0, 0, 0, 0, 0],

        # Virtual cube
        'virt_cube_damp': [0],
        'virt_cube_damp_dist': [0],
        'virt_cube_eta': [0],
        'virt_cube_rho_min': [0],
        'virt_cube_walls': [0, 0, 0, 0, 0, 0],
        "virt_cube_f_max": [20],
        'virt_cube_on': False,

        # Virtual joint walls
        'virt_walls_joint_damp': [0,0,0,0,0,0,0],
        'virt_walls_joint_damp_dist': [0,0,0,0,0,0,0],
        'virt_walls_joint_eta': [0,0,0,0,0,0,0],
        'virt_walls_joint_rho_min': [0,0,0,0,0,0,0],
        'virt_walls_joint_walls': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        'virt_walls_joint_tau_max': [20,20,20,20,12,12,12],
        'virt_walls_joint_on': False,

        # Nullspace controller
        'nullspace_cntr_on': False,
        'nullspace_cntr_K': [1000, 1000, 1000, 700, 500, 200, 100],
        'nullspace_cntr_xi': [0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7],
        'nullspace_cntr_q': [0, 0, 0, 0, 0, 0, 0],

        # General options
        'TF_control': True,
        'tau_c_max': [80, 80, 80, 80, 12, 12, 12],
        'dtau_c_max': [950, 950, 950, 950, 950, 950, 950]
    }

    client.mios.parameters.insert_one(parameters)

    # frames
    doc = client.mios.parameters.find_one({"type": 'frames'})
    if doc is not None:
        if overwrite is False:
            print('Frames parameter file already exists in database. '
                  'To overwrite set the overwrite flag of this function to True.')
            return
        else:
            client.mios.parameters.delete_one({'type': 'frames'})

    parameters = {
        'type': 'frames',
        'O_R_TF': [1, 0, 0, 0, 1, 0, 0, 0, 1],
        'F_T_EE': [0.7071, -0.7071, 0, 0, 0.7071, 0.7071, 0, 0, 0, 0, 1, 0, 0, 0, 0.1034, 1],
        'EE_T_K': [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
        'EE_T_TCP': [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
        'EE_T_C': [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]
    }
    client.mios.parameters.insert_one(parameters)

    # general
    doc = client.mios.parameters.find_one({"type": 'general'})
    if doc is not None:
        if overwrite is False:
            print('General parameter file already exists in database. '
                  'To overwrite set the overwrite flag of this function to True.')
            return
        else:
            client.mios.parameters.delete_one({'type': 'general'})

    parameters = {
        'type': 'general',
        'safe_mode': False,
        'instant_recovery': False,
        'logging': False,
        'control_mode': 0,
        'command_mode': 0
    }
    client.mios.parameters.insert_one(parameters)

    # system
    doc = client.mios.parameters.find_one({"type": 'system'})
    if doc is not None:
        if overwrite is False:
            print('System parameter file already exists in database. '
                  'To overwrite set the overwrite flag of this function to True.')
            return
        else:
            client.mios.parameters.delete_one({'type': 'system'})

    parameters = {
        'type': 'system',
        'ip_robot': 'none',
        "id_robot": "none",
        "location": "none",
        'ip_simulation': 'none',
        'port_simulation': 0,
        'logging': False,
        'desk_name': 'franka',
        'desk_pwd': 'frankaRSI',
        'has_robot': True,
        'has_gripper': True,
        'has_simulation': False,
        'has_led': False,
        'has_sound': False,
        'telemetry_on': False,
        'telemetry_udp_ip': 'none',
        'telemetry_udp_port': 0,
        'telemetry_udp_frequency': 1000
    }
    client.mios.parameters.insert_one(parameters)

    # user
    doc = client.mios.parameters.find_one({"type": 'user'})
    if doc is not None:
        if overwrite is False:
            print('User parameter file already exists in database. '
                  'To overwrite set the overwrite flag of this function to True.')
            return
        else:
            client.mios.parameters.delete_one({'type': 'user'})

    parameters = {
        'type': 'user',
        'neighborhood_X': [1000, 1000],
        'neighborhood_dX': [1000, 1000],
        'neighborhood_F': [1000, 1000],
        'neighborhood_dF': [1000, 1000],
        'neighborhood_q': [1000],
        'neighborhood_dq': [1000],

        "x_limits": [-2, 2, -2, 2, -2, 2],

        'dX_max': [0.5, 1],
        'ddX_max': [1.5, 4],
        'dq_max': [2],
        'ddq_max': [5],

        'F_contact': [5, 5, 5, 2, 2, 2],
        'tau_contact': [2, 2, 2, 2, 2, 2, 2],
        'F_max': [10, 10, 10, 5, 5, 5],
        'tau_max': [5, 5, 5, 5, 5, 5, 5],

        'e_x_max': [0.01, 0.1],
        'e_q_max': [0.1],

        'load_m': 0,
        'load_com': [0, 0, 0],
        'load_I': [0, 0, 0, 0, 0, 0, 0, 0, 0]
    }
    client.mios.parameters.insert_one(parameters)


def upload_default_objects(db_url, overwrite=False):
    client = MongoClient('mongodb://' + db_url + ':27017')

    doc = client.mios.environment.find_one({"name": 'none'})
    if doc is not None:
        if overwrite is False:
            print('Object none already exists in database. '
                  'To overwrite set the overwrite flag of this function to True.')
            return
        else:
            client.mios.environment.delete_one({'name': 'none'})

    object = {
        'EE_T_O': [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
        'EE_ob_com': [0, 0, 0],
        'name': 'none',
        'mass': 0,
        'ob_I': [0, 0, 0, 0, 0, 0, 0, 0, 0]
    }
    client.mios.environment.insert_one(object)
    object = {
        'EE_T_O': [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
        "O_T_o": [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
        'EE_ob_com': [0, 0, 0],
        'name': 'test_object_1',
        'mass': 0,
        'ob_I': [0, 0, 0, 0, 0, 0, 0, 0, 0]
    }
    client.mios.environment.insert_one(object)


def upload_default_skills(db_url, overwrite=False):
    upload_skill(db_url, 'extraction', overwrite)
    upload_skill(db_url, 'gesture_haptic', overwrite)
    upload_skill(db_url, 'hand_guiding', overwrite)
    upload_skill(db_url, 'hold_pose', overwrite)
    upload_skill(db_url, 'insertion', overwrite)
    upload_skill(db_url, 'motions_generic_wiggle', overwrite)
    upload_skill(db_url, 'move_to_contact', overwrite)
    upload_skill(db_url, 'move_to_pose', overwrite)
    upload_skill(db_url, 'move_to_pose_joint', overwrite)
    upload_skill(db_url, 'polish', overwrite)
    upload_skill(db_url, 'push', overwrite)
    upload_skill(db_url, 'telepresence_master', overwrite)
    upload_skill(db_url, 'telepresence_slave', overwrite)
    upload_skill(db_url, 'test_skill_1', overwrite)
    upload_skill(db_url, 'turn', overwrite)
    upload_skill(db_url, 'learner_test_skill', overwrite)
    upload_skill(db_url, 'follow_trajectory', overwrite)


def upload_default_tasks(db_url, overwrite=False):
    upload_task(db_url, 'idle_task', overwrite)
    upload_task(db_url, 'extract_object', overwrite)
    upload_task(db_url, 'feature_collision_detection', overwrite)
    upload_task(db_url, 'feature_force_control', overwrite)
    upload_task(db_url, 'feature_impedance', overwrite)
    upload_task(db_url, 'fetch_object', overwrite)
    upload_task(db_url, 'guiding_mode', overwrite)
    upload_task(db_url, 'learner_test', overwrite)
    upload_task(db_url, 'react_to_event', overwrite)
    upload_task(db_url, 'handover_object', overwrite)
    upload_task(db_url, 'insert_object', overwrite)
    upload_task(db_url, 'move_to_cart_pose', overwrite)
    upload_task(db_url, 'move_to_joint_pose', overwrite)
    upload_task(db_url, 'move_to_location', overwrite)
    upload_task(db_url, 'place_object', overwrite)
    upload_task(db_url, 'polish_object', overwrite)
    upload_task(db_url, 'telepresence', overwrite)
    upload_task(db_url, 'move_trajectory', overwrite)
    upload_task(db_url, 'move_until_contact', overwrite)
    upload_task(db_url, 'test_task_1', overwrite)
    upload_task(db_url, 'test_task_2', overwrite)
    upload_task(db_url, 'test_task_3', overwrite)


def download_object(db_url, object, check_url=True):
    if check_url:
        if ping_host(db_url) != 0:
            print('Could not reach host at ' + db_url)
            return
    try:
        client = MongoClient('mongodb://' + db_url + ':27017')
        objects = client.mios.environment

        path_descr = os.getcwd() + '/../../environment/descriptions/'
        if not os.path.isdir(path_descr):
            os.makedirs(path_descr)

        doc = objects.find_one({'name': object})
        if doc is None:
            print('Object with name ' + object + ' does not exist in knowledge base.')
            return
        del doc["_id"]
        with open(path_descr + object + '.json', 'w') as file:
            json.dump(doc, file)
    except (pymongo.errors.ServerSelectionTimeoutError):
        print('Could not reach database on url ' + db_url)


def upload_object(db_url, object, overwrite=False, check_url=True):
    if check_url:
        if ping_host(db_url) != 0:
            print('Could not reach host at ' + db_url)
            return
    try:
        client = MongoClient('mongodb://' + db_url + ':27017')
        objects = client.mios.environment

        path_descr = os.getcwd() + '/../../environment/descriptions/'
        if not os.path.isdir(path_descr):
            print('Did not find folder mios/environment/descriptions/ .')
            return

        if not os.path.isfile(path_descr + object + '.json'):
            print('Can not find object file ' + object + '.json. '
                                                       'Descriptions files must be stored in mios/environment/descriptions/ .')
            return

        with open(path_descr + object + '.json', 'r') as file:
            data = json.load(file)

        doc = objects.find_one({"name": data['name']})
        if doc is not None:
            if overwrite is False:
                print('Object with name ' + data['name'] + ' already exists in knowledge base. '
                                                         'To overwrite set the overwrite flag of this function to True.')
                return
            else:
                objects.delete_one({'name': data['name']})

        objects.insert_one(data)
    except (pymongo.errors.ServerSelectionTimeoutError):
        print('Could not reach url ' + db_url)


def upload_object_to_collective(object, overwrite=False):
    response = rpc_call('http://' + server_url + ':8390', "get_collective")
    robots = response["result"]

    for r in robots:
        response_r = rpc_call('http://' + server_url + ':8390', "get_hostname", {'alias': r})
        if response_r["result"]["hostname"] is None:
            print("Could not reach robot " + r)
            continue

        hostname = response_r["result"]["hostname"]
        upload_object(hostname, object, overwrite)


def download_skill(db_url, skill, check_url=True):
    if check_url:
        if ping_host(db_url) != 0:
            print('Could not reach host at ' + db_url)
            return
    try:
        client = MongoClient('mongodb://' + db_url + ':27017')
        skills = client.mios.skills

        path_descr = os.getcwd() + '/../../skill/descriptions/'
        if not os.path.isdir(path_descr):
            os.makedirs(path_descr)

        doc = skills.find_one({'name': skill})
        if doc is None:
            print('Skill with name ' + skill + ' does not exist in knowledge base.')
            return
        del doc["_id"]
        with open(path_descr + skill + '.json', 'w') as file:
            json.dump(doc, file)
    except (pymongo.errors.ServerSelectionTimeoutError):
        print('Could not reach database on url ' + db_url)


def upload_skill(db_url, skill, overwrite=False, check_url=True):
    if check_url:
        if ping_host(db_url) != 0:
            print('Could not reach host at ' + db_url)
            return
    try:
        client = MongoClient('mongodb://' + db_url + ':27017')
        skills = client.mios.skills

        path_descr = os.getcwd() + '/../../skill/descriptions/'
        if not os.path.isdir(path_descr):
            print('Did not find folder mios/skill/descriptions/ .')
            return

        if not os.path.isfile(path_descr + skill + '.json'):
            print('Can not find skill file ' + skill + '.json. '
                                                       'Descriptions files must be stored in mios/skill/descriptions/ .')
            return

        with open(path_descr + skill + '.json', 'r') as file:
            data = json.load(file)

        doc = skills.find_one({"name": data['name']})
        if doc is not None:
            if overwrite is False:
                print('Skill with id ' + data['name'] + ' already exists in knowledge base. '
                                                         'To overwrite set the overwrite flag of this function to True.')
                return
            else:
                skills.delete_one({'name': data['name']})

        skills.insert_one(data)
    except (pymongo.errors.ServerSelectionTimeoutError):
        print('Could not reach url ' + db_url)


def download_all_skills(db_url):
    if ping_host(db_url) != 0:
        print('Could not reach host at ' + db_url)
        return
    try:
        client = MongoClient('mongodb://' + db_url + ':27017')
        skills = client.mios.skills
        cursor = skills.find({})
        for doc in cursor:
            download_skill(db_url, doc['name'], False)
    except (pymongo.errors.ServerSelectionTimeoutError):
        print('Could not reach url ' + db_url)


def upload_skill_to_collective(skill, overwrite=False):
    response = rpc_call('http://' + server_url + ':8390', "get_collective")
    robots = response["result"]

    for r in robots:
        response_r = rpc_call('http://' + server_url + ':8390', "get_hostname", {'alias': r})
        if response_r["result"]["hostname"] is None:
            print("Could not reach robot " + r)
            continue

        hostname = response_r["result"]["hostname"]
        upload_skill(hostname, skill, overwrite)


def upload_all_skills_to_collective(overwrite=False):
    response = rpc_call('http://' + server_url + ':8390', "get_collective")
    robots = response["result"]

    for r in robots:
        response_r = rpc_call('http://' + server_url + ':8390', "get_hostname", {'alias': r})
        if response_r["result"]["hostname"] is None:
            print("Could not reach robot " + r)
            continue

        hostname = response_r["result"]["hostname"]
        print('Uploading skills to ' + hostname)
        upload_all_skills(hostname, overwrite)


def upload_all_skills(db_url, overwrite=False):
    if ping_host(db_url) != 0:
        print('Could not reach host at ' + db_url)
        return
    path_descr = os.getcwd() + '/../../skill/descriptions/'
    if not os.path.isdir(path_descr):
        print('Did not find folder mios/skill/descriptions/ .')
        return

    skills = [f for f in listdir(path_descr) if isfile(join(path_descr, f))]
    for s in skills:
        filename = s.split('.')
        if filename[1] != 'json':
            print(s + ' is not a valid description file.')
            continue
        upload_skill(db_url, filename[0], overwrite, False)


def download_task(db_url, task, check_url=True):
    if check_url:
        if ping_host(db_url) != 0:
            print('Could not reach host at ' + db_url)
            return
    try:
        client = MongoClient('mongodb://' + db_url + ':27017')
        tasks = client.mios.tasks

        path_descr = os.getcwd() + '/../../task/descriptions/'
        if not os.path.isdir(path_descr):
            os.makedirs(path_descr)

        doc = tasks.find_one({'name': task})
        if doc is None:
            print('Task with name ' + task + ' does not exist in knowledge base.')
            return
        del doc["_id"]
        with open(path_descr + task + '.json', 'w') as file:
            json.dump(doc, file)
    except (pymongo.errors.ServerSelectionTimeoutError):
        print('Could not reach url ' + db_url)


def upload_task(db_url, task, overwrite=False, check_url=True):
    if check_url:
        if ping_host(db_url) != 0:
            print('Could not reach host at ' + db_url)
            return
    try:
        client = MongoClient('mongodb://' + db_url + ':27017')
        tasks = client.mios.tasks

        path_descr = os.getcwd() + '/../../task/descriptions/'
        if not os.path.isdir(path_descr):
            print('Did not find folder mios/task/descriptions/ .')
            return

        if not os.path.isfile(path_descr + task + '.json'):
            print('Can not find task file ' + task + '.json. '
                                                     'Descriptions files must be stored in mios/task/descriptions/ .')
            return

        with open(path_descr + task + '.json', 'r') as file:
            data = json.load(file)

        doc = tasks.find_one({"name": data['name']})
        if doc is not None:
            if overwrite is False:
                print('Task with name ' + data['name'] + ' already exists in knowledge base. '
                                                       'To overwrite set the overwrite flag of this function to True.')
                return
            else:
                tasks.delete_one({'name': data['name']})

        tasks.insert_one(data)
    except (pymongo.errors.ServerSelectionTimeoutError):
        print('Could not reach url ' + db_url)


def download_all_tasks(db_url):
    if ping_host(db_url) != 0:
        print('Could not reach host at ' + db_url)
        return
    try:
        client = MongoClient('mongodb://' + db_url + ':27017')
        tasks = client.mios.tasks
        cursor = tasks.find({})
        for doc in cursor:
            download_task(db_url, doc['name'], False)
    except (pymongo.errors.ServerSelectionTimeoutError):
        print('Could not reach url ' + db_url)


def upload_all_tasks(db_url, overwrite=False):
    if ping_host(db_url) != 0:
        print('Could not reach host at ' + db_url)
        return
    path_descr = os.getcwd() + '/../../task/descriptions/'
    if not os.path.isdir(path_descr):
        print('Did not find folder mios/task/descriptions/ .')
        return

    tasks = [f for f in listdir(path_descr) if isfile(join(path_descr, f))]
    for t in tasks:
        filename = t.split('.')
        if filename[1] != 'json':
            print(t + ' is not a valid description file.')
            continue
        upload_task(db_url, filename[0], overwrite, False)


def upload_task_to_collective(task, overwrite=False):
    response = rpc_call('http://' + server_url + ':8390', "get_collective")
    robots = response["result"]

    for r in robots:
        response_r = rpc_call('http://' + server_url + ':8390', "get_hostname", {'alias': r})
        if response_r["result"]["hostname"] is None:
            print("Could not reach robot " + r)
            continue

        hostname = response_r["result"]["hostname"]
        upload_task(hostname, task, overwrite)


def upload_all_tasks_to_collective(overwrite=False):
    response = rpc_call('http://' + server_url + ':8390', "get_collective")
    robots = response["result"]

    for r in robots:
        response_r = rpc_call('http://' + server_url + ':8390', "get_hostname", {'alias': r})
        if response_r["result"]["hostname"] is None:
            print("Could not reach robot " + r)
            continue

        hostname = response_r["result"]["hostname"]
        print('Uploading tasks to ' + hostname)
        upload_all_tasks(hostname, overwrite)


def set_parameter(db_url,category,parameter,val):
    if ping_host(db_url) != 0:
        print('Could not reach host at ' + db_url)
        return
    try:
        client = MongoClient('mongodb://' + db_url + ':27017')
        doc = client.mios.parameters.find_one({"type": category})
        if parameter not in doc:
            print('Parameter ',parameter,' does not exist.')
            return

        doc[parameter]=val
        client.mios.parameters.delete_one({'type': category})
        client.mios.parameters.insert_one(doc)
    except (pymongo.errors.ServerSelectionTimeoutError):
        print('Could not reach database on url ' + db_url)


def set_parameter_collective(category,parameter,val):
    response = rpc_call('http://' + server_url + ':8390', "get_collective")
    robots = response["result"]

    for r in robots:
        response_r = rpc_call('http://' + server_url + ':8390', "get_hostname", {'alias': r})
        if response_r["result"]["hostname"] is None:
            print("Could not reach robot " + r)
            continue

        hostname = response_r["result"]["hostname"]
        print('Setting parameter on ' + hostname)
        set_parameter(hostname, category,parameter,val)


def wipe_results(db_url, problem_id):
    client = MongoClient('mongodb://' + db_url + ':27017')
    client.mi_results["results_" + problem_id].drop()


def wipe_all_results(db_url):
    client = MongoClient('mongodb://' + db_url + ':27017')
    for c in client.mi_results.list_collection_names():
        client.mi_results[c].drop()
