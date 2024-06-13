from ast import mod
from desk.mongodb_client import MongoDBClient
from xmlrpc.client import ServerProxy
import os
from threading import Thread
import copy
from utils.ws_client import *
import json
import socket
import struct

import time
import copy


###################################################################################
list_block_1 = ["001", #"002", 
                "003", "004", "005", 
                "006", "007", "008", "010", 
                "011", "012"]
list_block_2 = ["009","013","014","015","016","017",
                # "018",#"020",
                "041",
                "021","022"]
list_U = ["023", "024", "025","026", "027", "029"] #, "026", "028",
list_external = ["050"]
def get_ips(module_list):
    with open("ip.json", "r") as jsonfile:
        data = json.load(jsonfile)        
        ips = [data[i] for i in module_list]
        print(ips)
    
    return ips
###################################################################################

modules = list_block_1+list_block_2+list_U  # +list_external

second_ushape = [   "collective-016.rsi.ei.tum.de","collective-021.rsi.ei.tum.de","collective-022.rsi.ei.tum.de",
                    "collective-018.rsi.ei.tum.de","collective-017.rsi.ei.tum.de","collective-015.rsi.ei.tum.de",
                    "collective-014.rsi.ei.tum.de","collective-013.rsi.ei.tum.de","collective-009.rsi.ei.tum.de",
                    "collective-020.rsi.ei.tum.de"]
hostnames = []
for m in modules:
    hostnames.append("collective-"+m+".rsi.ei.tum.de")
print(hostnames)


class Task:
    def __init__(self, robot, port=12000):
        self.skill_names = []
        self.skill_types = []
        self.skill_context = dict()
        self.context = {
            "parameters": {
                "skill_names": [],
                "skill_types": [],
                "as_queue": False
            },
            "skills": self.skill_context
        }

        self.robot = robot
        self.port = port
        self.task_uuid = "INVALID"
        self.t_0 = 0

    def add_skill(self, name, skill_class, context):
        self.skill_names.append(name)
        self.skill_types.append(skill_class)
        self.skill_context[name] = context

        self.context["parameters"]["skill_names"] = self.skill_names
        self.context["parameters"]["skill_types"] = self.skill_types
        self.context["skills"] = self.skill_context

    def start(self, queue: bool = False):
        self.t_0 = time.time()
        self.context["parameters"]["as_queue"] = queue
        response = start_task(self.robot, "GenericTask", parameters=self.context, port=self.port)
        self.task_uuid = response["result"]["task_uuid"]

    def wait(self):
        result = wait_for_task(self.robot, self.task_uuid, port=self.port)
        #print("Task execution took " + str(time.time() - self.t_0) + " s.")
        return result

    def stop(self):
        result = stop_task(self.robot, port=self.port)
        #print("Task execution took " + str(time.time() - self.t_0) + " s.")
        return result


def command_collective(cmd: str, args: dict = {}):
    threads = []
    for r in get_ips(modules):
        print(r)
        threads.append(Thread(target=call_method, args=(r, 12000, cmd, args,)))
        threads[-1].start()
        threads.append(Thread(target=call_method, args=(r, 13000, cmd, args,)))
        threads[-1].start()
    for t in threads:
        t.join()

def set_grasped_objects():
    ips = get_ips(modules)
    for ip,m in zip(ips,modules):
        call_method(ip,12000,"set_grasped_object",{"object":m+"_left"})

def command_some(robots:list, cmd: str, args: dict = {}):
    threads = []
    for r in robots:
        print(r)
        threads.append(Thread(target=call_method, args=(r, 12000, cmd, args,)))
        threads[-1].start()
        threads.append(Thread(target=call_method, args=(r, 13000, cmd, args,)))
        threads[-1].start()
    for t in threads:
        t.join()

def automatica_wave_small(robot, port=12000, min_time = 10):
    result = False
    speed = [1.5,5]
    while not result:
        result = move_joint(robot, "wave_high", port=port, speed=speed)["result"]["task_result"]["success"]
        speed = [s*0.8 for s in speed]
    pi = 3.14159265359
    wiggle_context1 = {
        "skill": {
            "dX_fourier_a_a": [0.0, 0.02, 0., 0, 0, 0.25],
            "dX_fourier_a_phi": [0, pi/2, 0, pi/2, 0, pi/2],
            "dX_fourier_a_f": [0, 1.25, 0, 0.6125, 0, 1.25],
            "dX_fourier_b_a": [0, 0, 0, 0, 0, 0],
            "dX_fourier_b_f": [0, 0, 0, 0, 0, 0],
            "use_EE": True,
            "time_max": min_time
        },
        "control": {
            "control_mode": 0
        }
    }
    t1 = time.time()

    c = 0
    while time.time() - t1 < min_time:
        c+=1
        move_joint(robot, "wave_high",port=port, speed=[1.5,5])
        t = Task(robot,port)
        t.add_skill("wiggle"+str(c), "GenericWiggleMotion", wiggle_context1)
        t.start(False)
        t.wait()

def automatica_wave_big(robot, port=12000, min_time = 10):
    result = False
    speed = [1.5,5]
    while not result:
        result = move_joint(robot, "wave_high", port=port, speed=speed)["result"]["task_result"]["success"]
        speed = [s*0.8 for s in speed]

    pi = 3.14159265359
    speed = 0.36
    wiggle_context = {
        "skill": {
            "dX_fourier_a_a": [0.05,        0.1,    0.,      0.1,       0.1,        0.5],
            "dX_fourier_a_phi": [0,         pi/2,   0,       3*pi/2,         pi/2,       pi/2],
            "dX_fourier_a_f": [2*speed,     speed,  2*speed, speed,   2*speed,    speed],
            "dX_fourier_b_a": [0, 0, 0, 0, 0, 0],
            "dX_fourier_b_f": [0, 0, 0, 0, 0, 0],
            "use_EE": True,
            "time_max": min_time
        },
        "control": {
            "control_mode": 0
        }
    }
    t1 = time.time()
    c = 0
    while time.time() - t1 < min_time:
        c+=1
        move_joint(robot, "wave_high", port=port, speed=[1.5,5])
        t = Task(robot,port)
        t.add_skill("wiggle"+str(c), "GenericWiggleMotion", wiggle_context)
        t.start(False)
        t.wait()

def automatica_waving(banner=False):
    waving_time = 25
    if banner:
        big_flags = [("collective-016.rsi.ei.tum.de", 13000),("collective-021.rsi.ei.tum.de", 12000),("collective-021.rsi.ei.tum.de", 13000),
                 ("collective-022.rsi.ei.tum.de", 12000),("collective-022.rsi.ei.tum.de", 13000),("collective-017.rsi.ei.tum.de", 12000),
                 ("collective-014.rsi.ei.tum.de", 13000),("collective-020.rsi.ei.tum.de", 13000),("collective-015.rsi.ei.tum.de", 12000),
                 ("collective-015.rsi.ei.tum.de", 13000)]  # with banner
        small_flags = [("collective-018.rsi.ei.tum.de", 12000),("collective-018.rsi.ei.tum.de", 13000),
                ("collective-014.rsi.ei.tum.de", 12000),("collective-009.rsi.ei.tum.de", 12000),("collective-009.rsi.ei.tum.de", 13000),
                ("collective-013.rsi.ei.tum.de", 13000),("collective-016.rsi.ei.tum.de", 12000)]  # with banner
    else:
        big_flags = [("collective-016.rsi.ei.tum.de", 13000),("collective-021.rsi.ei.tum.de", 12000),("collective-021.rsi.ei.tum.de", 13000),
                 ("collective-022.rsi.ei.tum.de", 12000),("collective-022.rsi.ei.tum.de", 13000),("collective-017.rsi.ei.tum.de", 12000),
                 ("collective-014.rsi.ei.tum.de", 13000),("collective-020.rsi.ei.tum.de", 13000),("collective-015.rsi.ei.tum.de", 12000),
                 ("collective-015.rsi.ei.tum.de", 13000),("collective-020.rsi.ei.tum.de", 12000)] # without banner
        small_flags = [("collective-018.rsi.ei.tum.de", 12000),("collective-018.rsi.ei.tum.de", 13000),
                ("collective-014.rsi.ei.tum.de", 12000),("collective-009.rsi.ei.tum.de", 12000),("collective-009.rsi.ei.tum.de", 13000),
                ("collective-013.rsi.ei.tum.de", 13000),("collective-016.rsi.ei.tum.de", 12000),("collective-013.rsi.ei.tum.de", 12000)]   # without banner
  
    threads = []
    for robot, port in small_flags:
        threads.append(Thread(target=automatica_wave_small, args=(robot,port,waving_time)))
    for robot, port in big_flags:
        print(robot,port)
        threads.append(Thread(target=automatica_wave_big, args=(robot,port,waving_time)))
    for t in threads:
        t.start()
    time_1 = time.time()
    if banner:
        raise_banner()
    while time.time() - time_1 < waving_time+10:
        time.sleep

    big_flags.extend(small_flags)

    for i,t in enumerate(threads):
        print("waiting for ", big_flags[i])
        command_some(second_ushape, "stop_task")
        t.join()


    

def raise_banner():
    threads = []
    for r in ["collective-013.rsi.ei.tum.de","collective-020.rsi.ei.tum.de"]:
        threads.append(Thread(target=move_joint, args=(r, "banner_high", 12000, True)))
        threads[-1].start()
    for t in threads:
        t.join()
def lower_banner():
    threads = []
    for r in ["collective-013.rsi.ei.tum.de","collective-020.rsi.ei.tum.de"]:
        threads.append(Thread(target=move_joint, args=(r, "wave_low", 12000, True)))
        threads[-1].start()
    for t in threads:
        t.join()

def get_ip(hostname: str):
    print("hostname: ",hostname)
    return socket.gethostbyname(hostname)

def populate_database(host, db, ip, user_name="franka", user_pw="frankaRSI"):
    try:
        client = MongoDBClient(host)
        new_params = {"desk_name":user_name, "desk_pwd":user_pw,"robot_ip":ip, "spoc_token":"","spoc_in_control":False}
        client.update(db,"parameters",{"name":"system"}, new_params)
        print("updated ", host,": ",db)
    except:
            print(host, " not updated")
def populate_databases(db, ip, user_name="franka", user_pw="frankaRSI"):
    for host in get_ips(modules):
        populate_database(host,db,ip,user_name,user_pw)

def populate_all():
    threads = []
    for host in get_ips(modules):
        threads.append(Thread(target=populate_database, args=(host,"miosL","192.168.3.100","franka","frankaRSI",)))
        threads[-1].start()
        threads.append(Thread(target=populate_database, args=(host,"miosR","192.168.4.100","franka","frankaRSI",)))
        threads[-1].start()
    
    for t in threads:
        t.join()


def copy_object(source:str, destinations:list, object_name:str, robot_arm="left"):
    def _send_object(destination, db, collection, document):
        if "_id" in document:
            document.pop("_id")
        client = MongoDBClient(destination)
        if len(client.read(db, collection, {"name": document["name"]})):
            client.remove(db, collection, {"name":document["name"]})
        client.write(db, collection, document)
    if destinations == "all":
        destinations = get_ips(modules)
        if source in destinations:
            destinations.remove(source)
    client = MongoDBClient(source)
    obj = None
    if robot_arm == "left":
        obj = client.read("miosL","environment",{"name":object_name})
    else:
        obj = client.read("miosR","environment",{"name":object_name})
    if len(obj) != 1:
        print("Failure: Found ", len(obj), " objects on ", source, " with name ", object_name)
        return "error"
    else:
        obj = obj[0]
    threads = []
    for destination in destinations:
        if robot_arm == "left":
            threads.append(Thread(target=_send_object, args=(destination, "miosL", "environment", obj)))
        else:
            threads.append(Thread(target=_send_object, args=(destination, "miosR", "environment", obj)))
        threads[-1].start()
    for t in threads:
        t.join()
    print("sending completed. Restart cluster!")

def move_to_contact(robot, location, port = 12000, wait=True):
    context = {
                "skill": {
                    "speed": 0.5,
                    "objects": {
                        "goal_pose": location
                    }
                },
                "control": {
                    "control_mode": 2
                },
                "user":{
                    "F_ext_contact": [10,5]
                }

            }
    t = Task(robot, port=port)
    t.add_skill("contact", "MoveToContact", context)
    t.start()
    if wait:
        return t.wait()

def move(robot, location, offset = [0,0,0], port=12000, wait = True,f_ext = [10,5]):
    context = {
        "skill": {
            "p0":{
                "dX_d": [0.3, 0.8],
                "ddX_d": [0.5, 1],
                "K_x": [2000, 2000, 2000, 250, 250, 250],
                "T_T_EE_g_offset": [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, offset[0], offset[1], offset[2], 1]

            },
            "time_max":10,
            "objects": {
                    "GoalPose": location
                }
        },
        "control": {
            "control_mode": 0
        },
        "user":{
            "F_ext_max": f_ext,
            #"env_X": [0.002, 0.002, 0.002, 0.0175, 0.0175, 0.0175]  #[0.001, 0.001, 0.001, 0.001, 0.001, 0.001]
        }
    }
    t = Task(robot, port=port)
    t.add_skill("move", "TaxMove", context)
    t.start()
    if wait:
        return t.wait()

    #print("Result: " + str(result))

def move_joint(robot, location, port=12000, offset=[0,0,0,0,0,0,0], wait=True, speed = []):
    path_to_default_context = os.getcwd() + "/taxonomy/default_contexts/"
    f = open(path_to_default_context + "move_joint.json")
    move_context = json.load(f)
    move_context["skill"]["objects"]["goal_pose"] = location
    move_context["skill"]["time_max"] = 10
    move_context["skill"]["q_g_offset"] = offset
    move_context["user"]["env_X"] = [0.001, 0.001, 0.001, 0.001, 0.001, 0.001]
    move_context["user"]["F_ext_max"] = [12,12]
    if speed:
        move_context["skill"]["speed"] = speed[0]
        move_context["skill"]["acc"] = speed[1]
    t0 = Task(robot, port=port)
    t0.add_skill("move", "MoveToPoseJoint", move_context)
    t0.start()
    if wait:
        return t0.wait()

def wink_thread(robot, port, duration=False):
    stop_services([robot])
    call_method(robot,port, "stop_task")
    #while call_method(robot,port,"get_state")["result"]["current_task"] != "IdleTask":
    #    call_method(robot,port, "stop_task")
    #    print("is not IdleTask")
    #    time.sleep(1)
#
    path_to_default_context = os.getcwd() + "/../python/taxonomy/default_contexts/"
    f = open(path_to_default_context + "move_joint.json")
    
    move1_context = json.load(f)
    move1_context["skill"]["speed"] = 1
    move1_context["skill"]["acc"] = 2
    
    t0 = Task(robot, port=port)
    #move1_context["skill"]["objects"]["goal_pose"] = "reset"
    #move1_context["skill"]["time_max"] = 10
    #t0.add_skill("reset_move", "MoveToPoseJoint", move1_context)
    for i in range(100):
        move2_context = copy.deepcopy(move1_context)
        move2_context["skill"]["objects"]["goal_pose"] = "wink"
        t0.add_skill("wink_move", "MoveToPoseJoint", move2_context)

        move3_context = copy.deepcopy(move1_context)
        move3_context["skill"]["objects"]["goal_pose"] = "wink2"
        t0.add_skill("wink2_move", "MoveToPoseJoint", move3_context)

        move4_context = copy.deepcopy(move1_context)
        move4_context["skill"]["objects"]["goal_pose"] = "wink3"
        t0.add_skill("wink3_move", "MoveToPoseJoint", move4_context)

        move5_context = copy.deepcopy(move1_context)
        move5_context["skill"]["objects"]["goal_pose"] = "wink2"
        t0.add_skill("wink2_move_again", "MoveToPoseJoint", move5_context)

    #move6_context = copy.deepcopy(move1_context)
    #move6_context["skill"]["objects"]["goal_pose"] = "reset"
    #t0.add_skill("reset_again", "MoveToPoseJoint", move6_context)

    t0.start()
    result = t0.wait()
    

def move_all(pose = "default_pose"):
    threads = []
    for host in get_ips(modules):
        threads.append(Thread(target=move_joint, args=(host, pose, 12000, True)))
        threads[-1].start()
        threads.append(Thread(target=move_joint, args=(host, pose, 13000, True)))
        threads[-1].start()
    for t in threads:
        t.join()
    print("finished")

def move_some(robots:list, pose):
    threads = []
    for host in robots:
        threads.append(Thread(target=move_joint, args=(host, pose, 12000, True)))
        threads[-1].start()
        threads.append(Thread(target=move_joint, args=(host, pose, 13000, True)))
        threads[-1].start()
    for t in threads:
        t.join()
    print("finished moving to ",pose)

def move_all_cart(pose = "default_pose"):
    threads = []
    for host in get_ips(modules):
        threads.append(Thread(target=move, args=(host, pose,[0,0,0], 12000, True)))
        threads[-1].start()
        threads.append(Thread(target=move, args=(host, pose,[0,0,0], 13000, True)))
        threads[-1].start()
    for t in threads:
        t.join()
    print("finished")

def telepresence_udp_test(module = "013"):
    robot_ip = copy.deepcopy(get_ips([module]))[0]
    current_state = call_method(robot_ip,12000,"get_state")
    if current_state is None:
        return "cannot call robot at "+str(robot_ip)
    current_q = current_state["result"]["q"]
    telepresence_slave_context_left = {
        "skill": {
            "is_master": False,
            "remote_event_protocol":"udp",
            "ip_dst": "10.0.2.35",
            "remote_event_port":8888,
            "port_dst": 8888,
            "port_src": 8888,
            "telepresence_mode": "DirectJoint",
            "multicast": False,
            "direct_joint": {
                "alpha": [0, 0, 0, 0, 0, 0, 0]
            }
        },
        "control": {
            "control_mode": 1,
            "joint_imp": {
                "K_theta": [1500,1200,800,600,300,200,50]
            }
        }
    }
    t_left = Task(robot_ip)
    t_left.add_skill("telepresence", "Telepresence", telepresence_slave_context_left)
    t_left.start()
    current_q[-3] = current_q[-3] - 0.1
    print(current_q)
    call_method(robot_ip,12000,"post_event",{"name":"handshake","content":{"q_master":current_q}})
    result, addr = udp_receive_message("10.0.2.35", 8888)
    print("handshake: ", result)
    udp_send_message(addr[0], addr[1], {"result":True})
    increase_angle = True
    counter = 0
    try:
        while True:
            if increase_angle:
                current_q[-1] += 0.0005
            else:
                current_q[-1] -= 0.0005
            if current_q[-1] > 1 and increase_angle:
                increase_angle = False
            if current_q[-1] < -1 and not increase_angle:
                increase_angle = True
            udp_send_message_teleformat(robot_ip, 8888, current_q, counter=counter)
            time.sleep(0.001)
            #counter += 1
            #if counter > 255:
            #    counter = 0
            #print(current_q)
    except KeyboardInterrupt:
        print("stop sending...")
        call_method(robot_ip,12000,"stop_task")
    t_left.wait()


def lltest(module = "013"):
    robot_ip = copy.deepcopy(get_ips([module]))[0]
    own_ip = "10.0.2.35"
    move_joint(robot_ip, "test")
    current_state = get_current_percept(robot_ip, "10.0.2.35", 12345,["tau"])["tau"]
    llInterface_context = {
        "skill": {
            "ip_dst": own_ip,  # IP to send answers to
            "port_dst": 8888,  # port to send answers to
            "port_src": 8888,  # receiving port
            "LLInterface_mode": "Torque", #CartPose  Torque  JointPose
            "twist": {"static_frame": True}
        },
        "control": {
            "control_mode": 0,
            #"joint_imp": {
            #    "K_theta": [2500,2200,2800,2600,2300,2200,250]
            #},
            #"cart_imp": {
            #    "K_x": [2000, 2000, 2000, 250, 250, 250]
            #}
        },
        "user":{
            "F_ext_max": [30, 15]
        }
    }   
    t = Task(robot_ip)
    t.add_skill("test_llInterface", "LLInterface", llInterface_context)
    t.start()
    current_q = get_current_percept(robot_ip, "10.0.2.35", 12345,["q"])["q"]
    call_method(robot_ip,12000,"post_event",{"name":"handshake","content":{"q_init":current_q}})
    result, addr = udp_receive_message("10.0.2.35", 8888)
    print("handshake: ", result)
    udp_send_message(addr[0], addr[1], {"result":True})
    increase_angle = True
    counter = 0
    try:
        while True:
            if increase_angle:
                current_state[-2] += 0.5
            else:
                current_state[-2] -= 0.5
            if current_state[-2] > 10 and increase_angle:
                increase_angle = False
            if current_state[-2] < -10 and not increase_angle:
                increase_angle = True
            #current_state[0] = 0.05
            udp_send_message_teleformat(robot_ip, 8888, current_state, counter=counter)
            print(current_state)
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("stop sending...")
        call_method(robot_ip,12000,"stop_task")
    except:
        call_method(robot_ip,12000,"stop_task")
    t.wait()

def subscrib_telemetry(robot_ip, receiving_ip, receiving_port, data:list):
    call_method(robot_ip,12000, "subscribe_telemetry",{"subscribe":data,"ip":receiving_ip,"port":receiving_port})
    if udp_receiver(receiving_ip,receiving_port):
        print("unsubscribe...")
        call_method(robot_ip,12000, "unsubscribe_telemetry",{"subscribe":data,"ip":receiving_ip,"port":receiving_port})

def get_current_percept(robot_ip,receiving_ip,receiving_port, percepts:list):
    call_method(robot_ip,12000, "subscribe_telemetry",{"subscribe":percepts,"ip":receiving_ip,"port":receiving_port})
    result, _ = udp_receive_message(receiving_ip,receiving_port)
    call_method(robot_ip,12000, "unsubscribe_telemetry",{"subscribe":percepts,"ip":receiving_ip,"port":receiving_port})
    return result

def udp_send_message_teleformat(ip,port,payload:list,counter=0):
    sock = socket.socket(socket.AF_INET, # Internet
                        socket.SOCK_DGRAM) # UDP
    format = "<6b"+str(len(payload))+"f4b"  # 127,127,127,127,package counter, payload size, payload (4 bytes/value), 126,126,126,126
    message = struct.pack(format, 127,127,127,127, counter, len(payload)*4,*payload, 126,126,126,126)
    sock.sendto(message, (ip, port))

def udp_send_message(ip, port, message):
    sock = socket.socket(socket.AF_INET, # Internet
                        socket.SOCK_DGRAM) # UDP
    sock.sendto(json.dumps(message).encode(), (ip, port))

def udp_receive_message(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  
    s.bind((ip, port)) 
    try: 
        data, adrr = s.recvfrom(8192)
        s.close()
    except KeyboardInterrupt:
        s.close()
        return False, (False, False)
    return json.loads(data.decode("utf-8")), adrr

def udp_receiver(ip, port):
    #receiver
    import pprint
    def write_incomming_udp(ip, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  
        s.bind((ip, port)) 
        try:
            print("listening at ", ip, ":", port,"\n")
            print("   --- Interrupt writing ctrl+c ---")
            while True: 
                data, adrr = s.recvfrom(8192) 
                data_dict = json.loads(data.decode("utf-8"))
                for key, value in data_dict.items():
                    if type(value) == list:
                        print(key, ": ", [float("{0:0.2f}".format(v)) for v in value])
                    else: 
                        print(key, ": ", value)
        except KeyboardInterrupt:
            s.close()
        return True
    return write_incomming_udp(ip,port)


def demo_part_left(master="008",wait=True):
    robots = copy.deepcopy(get_ips(modules))
    for host in robots:
        stop_task(host)
    for host in robots:
        if host.find(master) != -1:
            master = host
            break
    robots.remove(master)
    print("master is ", master)
    master = get_ip(master)
    result_left = start_task(master, "MoveToJointPose", {
        "parameters": {
            "pose": "reset",
            "speed": 1,
            "acc": 2
        }
    })
    result_left = wait_for_task(master, result_left["result"]["task_uuid"])
    if not result_left["result"]["task_result"]["success"]:
        print("master could not move to default pose")
        return "error"


    ip_slaves = []
    threads = []
    for i in range(0, len(robots)):
        ip_slaves.append(get_ip(robots[i]))
        threads.append(Thread(target=start_task_and_wait, args=(ip_slaves[-1], "MoveToJointPose",{
        "parameters": {
            "pose": "reset",
            "speed": 1,
            "acc": 2
        }
        })))
        threads[-1].start()
    for t in threads:
        t.join()
    time.sleep(2)

    print(ip_slaves)

    telepresence_master_context_left = {
        "skill": {
            "is_master": True,
            "ip_dst": "0.0.0.0",
            "port_dst": 8888,
            "port_src": 8888,
            "telepresence_mode": "DirectJoint",
            "multicast": True,
            "multicast_group": ip_slaves,
            "multicast_ip":"225.0.0.1",
            "host": master,
            "direct_joint": {
                "alpha": [15, 15, 10, 10, 8, 6, 3]#[0, 0, 0, 0, 0, 0, 0]
            }
        },
        "control": {
            "control_mode": 1
        }
    }
    telepresence_slave_context_left = {
        "skill": {
            "is_master": False,
            "ip_dst": "0.0.0.0",
            "port_dst": 8888,
            "port_src": 8888,
            "telepresence_mode": "DirectJoint",
            "multicast": True,
            "multicast_ip":"225.0.0.1",
            "direct_joint": {
                "alpha": [0, 0, 0, 0, 0, 0, 0]
            }
        },
        "control": {
            "control_mode": 1,
            "joint_imp": {
                "K_theta": [1500,1200,800,600,300,200,50]
            }
        }
    }
    print(telepresence_master_context_left)
    t_left = Task(master)
    t_left.add_skill("telepresence", "Telepresence", telepresence_master_context_left)
    t_left.start()
    for i in range(0, len(robots)):
        try:
            t_left = Task(robots[i])
            telepresence_slave_context_left["skill"]["host"] = robots[i]
            t_left.add_skill("telepresence", "Telepresence", telepresence_slave_context_left)
            print(robots[i])
            t_left.start()
        except TypeError:
            print(robots[i], " is not working.")
            pass
    if wait:
        input("Press key to stop.")
        for ip in ip_slaves:
            stop_task(ip)

        stop_task(master)

def demo_part_right(master = "008", wait = True):
    robots = copy.deepcopy(get_ips(modules))
    for host in robots:
        stop_task(host,port=13000)
    for host in robots:
        if host.find(master) != -1:
            master = host
            break
    robots.remove(master)
    print("master is ", master)
    master = get_ip(master)
    result_right = start_task(master, "MoveToJointPose", {
        "parameters": {
            "pose": "reset",
            "speed": 1,
            "acc": 2
        }
    },port=13000)
    result_right = wait_for_task(master, result_right["result"]["task_uuid"],port=13000)
    if not result_right["result"]["task_result"]["success"]:
        print(result_right)
        print("master could not move to default pose")
        return "error"


    ip_slaves = []
    threads = []
    for i in range(0, len(robots)):
        ip_slaves.append(get_ip(robots[i]))
        threads.append(Thread(target=start_task_and_wait, args=(ip_slaves[-1], "MoveToJointPose",{
        "parameters": {
            "pose": "reset",
            "speed": 1,
            "acc": 2
        }
        }),kwargs={"port":13000}))
        threads[-1].start()
    for t in threads:
        t.join()
    time.sleep(2)

    print(ip_slaves)

    telepresence_master_context_right = {
        "skill": {
            "is_master": True,
            "ip_dst": "0.0.0.0",
            "port_dst": 8886,
            "port_src": 8886,
            "telepresence_mode": "DirectJoint",
            "multicast": True,
            "multicast_group": ip_slaves,
            "multicast_ip":"225.0.0.3",
            "remote_event_port":13000,
            "host": master,
            "direct_joint": {
                "alpha": [15, 15, 10, 10, 8, 6, 3]#[0, 0, 0, 0, 0, 0, 0]
            }
        },
        "control": {
            "control_mode": 1
        }
    }
    telepresence_slave_context_right = {
        "skill": {
            "is_master": False,
            "ip_dst": "0.0.0.0",
            "port_dst": 8886,
            "port_src": 8886,
            "telepresence_mode": "DirectJoint",
            "multicast": True,
            "multicast_ip":"225.0.0.3",
            "remote_event_port":13000,
            "direct_joint": {
                "alpha": [0, 0, 0, 0, 0, 0, 0]
            }
        },
        "control": {
            "control_mode": 1,
            "joint_imp": {
                "K_theta": [1500,1200,800,600,300,200,50]
            }
        }
    }
    print(telepresence_master_context_right)
    t_right = Task(master,13000)
    t_right.add_skill("telepresence","Telepresence", telepresence_master_context_right)
    t_right.start()
    for i in range(0, len(robots)):
        try:
            t_right = Task(robots[i],13000)
            telepresence_slave_context_right["skill"]["host"] = robots[i]
            t_right.add_skill("telepresence", "Telepresence", telepresence_slave_context_right)
            print(robots[i])
            t_right.start()
        except TypeError:
            print(robots[i], " is not working.")
            pass

    if wait:
        input("Press key to stop.")
        for ip in ip_slaves:
            stop_task(ip,port=13000)

        stop_task(master,port=13000)

def teleop_dualarm(master = "008"):
    demo_part_left(master,wait=False)
    demo_part_right(master,wait=False)
    input("Press Key to stop")
    threads = []
    for ip in get_ips(modules):
        if master in ip:
            continue
        threads.append(Thread(target=stop_task, args=(ip,),kwargs={"port":13000}))
        threads[-1].start()
        threads.append(Thread(target=stop_task, args=(ip,),kwargs={"port":12000}))
        threads[-1].start()
    
    stop_task(master,port=13000)
    stop_task(master,port=12000)

def direct_joint_mode(master: str, slave: str):
    master_context = {
        "skill": {
            "is_master": True,
            "ip_dst": get_ip(slave),
            "port_dst": 8888,
            "port_src": 8888,
            "telepresence_mode": "DirectJoint",
            "direct_joint": {
                "alpha": [15, 15, 10, 10, 8, 6, 3]
            }
        },
        "control": {
            "control_mode": 1
        }
    }
    slave_context = {
        "skill": {
            "is_master": False,
            "ip_dst": get_ip(master),
            "port_dst": 8888,
            "port_src": 8888,
            "telepresence_mode": "DirectJoint",
            "direct_joint": {
                "alpha": [0, 0, 0, 0, 0, 0, 0]
            }
        },
        "control": {
            "control_mode": 1,
            "joint_imp": {
                "K_theta": [1500,1200,800,600,300,200,50]
            }
        }
    }
    t_m = Task(master)
    t_s = Task(slave)
    t_m.add_skill("telepresence", "Telepresence", master_context)
    t_s.add_skill("telepresence", "Telepresence", slave_context)

    t_m.start()
    t_s.start()
    input("Press Enter to stop...")
    t_m.stop()
    t_s.stop()


def restart_collective():
    client =ServerProxy("http://collective-009.rsi.ei.tum.de:"+str(8008), allow_none=True)
    client.reboot_robots()

def get_status():
    print(len(modules))
    for number,host in zip(modules,get_ips(modules)):
        #print("\ncollective-%03d"%(number+1))
        print("collective-",number)
        result = call_method(host,12000,"get_state")
        if result is not None:
            if result["result"]["current_task"] == "IdleTask":
                if result["result"]["status"] == "Idle":
                    print(host," -left- everything is good.")
                elif result["result"]["status"] == "Reflex":
                    print(host," -left- Non-upright-mounting Reflex.")
                else:
                    print(host, " -left- unknown status")
            else:
                print(host, " -left- Not in IdleTask")
        else:
            print(host, " -left- Not reachable!")

        result = call_method(host,13000,"get_state")
        if result is not None:
            if result["result"]["current_task"] == "IdleTask":
                if result["result"]["status"] == "Idle":
                    print(host," -right- everything is good.")
                elif result["result"]["status"] == "Reflex":
                    print(host," -right- Non-upright-mounting Reflex.")
                else:
                    print(host, " -right- unknown status")
            else:
                print(host, " -right- Not in IdleTask")
        else:
            print(host, " -right- Not reachable!")


def hold_pose(robot, duration, port, control="joint"):
    hold_context = {
        "skill": {
            "t_max": duration,
        },
        "control": {
            "control_mode": 1,
            "joint_imp":{
                "K_theta":[10000,10000,10000,10000,10000,10000,10000]
            }
            
        },
        "user": {"F_ext_max": [100, 50]}
    }
    if control == "cart":
        hold_context["control"] = { "control_mode": 0,
                                    "cart_imp": {
                                        "K_x": [3000, 3000, 3000, 200, 200, 200]
                                        }
                                    }
    t = Task(robot, port)
    t.add_skill("hold","HoldPose",hold_context)
    t.start(queue=False)


def extract(robot, extractable, extractTo, container, port=12000):
    path_to_default_context = os.getcwd() + "/taxonomy/default_contexts/"
    f = open(path_to_default_context + "extraction.json")
    move_context = json.load(f)
    move_context["skill"]["objects"]["Container"] = container
    move_context["skill"]["objects"]["ExtractTo"] = extractTo
    move_context["skill"]["objects"]["Extractable"] = extractable
    move_context["skill"]["time_max"] = 10
    #move_context["user"]["env_X"] = [0, 0, 1, 1, 1, 1]
    t = Task(robot, port)
    t.add_skill("extraction","TaxExtraction",move_context)
    t.start(queue=False)
    return t.wait()

def insert(robot, insertable, approach, container, deltaX =[0,0,0,0,0,0], port=12000):
    path_to_default_context = os.getcwd() + "/taxonomy/default_contexts/"
    f = open(path_to_default_context + "insertion.json")
    move_context = json.load(f)
    move_context["skill"]["objects"]["Container"] = container
    move_context["skill"]["objects"]["Approach"] = approach
    move_context["skill"]["objects"]["Insertable"] = insertable
    move_context["skill"]["time_max"] = 7
    move_context["skill"]["p2"]["f_push"][2] = 25
    move_context["skill"]["p0"]["DeltaX"] = deltaX
    #move_context["user"]["env_X"] = [0, 0, 1, 1, 1, 1]
    t = Task(robot, port)
    t.add_skill("insertion","TaxInsertion",move_context)
    t.start(queue=False)
    return t.wait()

def insert2(robot, insertable, approach, container, deltaX =[0,0,0,0,0,0], port=12000):
    path_to_default_context = os.getcwd() + "/taxonomy/default_contexts/"
    f = open(path_to_default_context + "insertion2.json")
    move_context = json.load(f)
    move_context["skill"]["objects"]["Container"] = container
    move_context["skill"]["objects"]["Approach"] = approach
    move_context["skill"]["objects"]["Insertable"] = insertable
    move_context["skill"]["time_max"] = 6.5
    move_context["skill"]["p2"]["search_c"] = [0,0,20,0,0,0]
    move_context["skill"]["p2"]["search_a"] = [5,5,0,0,0,0]
    move_context["skill"]["p2"]["search_f"] = [0.75,1,0,0,0,0]
    move_context["skill"]["p2"]["delta_a"] = [.0,.0,0,0,0,0.1]
    move_context["skill"]["p2"]["delta_f"] = [0.75,0,0,0,0,0.5]
    move_context["skill"]["p2"]["t_d"] = 4
    move_context["skill"]["p2"]["K_X"] = [2000, 2000, 1000, 200, 200, 200],
    
    
    # move_context["skill"]["p2"]["search_a"] = [0,0,0,0,0,0]
    # move_context["skill"]["p2"]["search_f"] = [0,0,0,0,0,0]
    # move_context["skill"]["p2"]["search_phi"] = [0,0,0,0,0,0]
    # move_context["skill"]["p2"]["delta_a"] = [0,0,0,0,0,0]
    # move_context["skill"]["p2"]["delta_f"] = [0,0,0,0,0,0]
    # move_context["skill"]["p2"]["delta_phi"] = [0,0,0,0,0,0]
    move_context["skill"]["p0"]["DeltaX"] = deltaX
    #move_context["user"]["env_X"] = [0, 0, 1, 1, 1, 1]
    t = Task(robot, port)
    t.add_skill("insertion","Insertion2",move_context)
    t.start(queue=False)
    return t.wait()

def gear_full():
    gear_grasp()
    gear_insertion()
    gear_reset(True)

def gear_place_ring():
    result = gear_unmount_ring()
    if not result["result"]["success"]:
        return False
    move_joint("10.157.175.135","026_left_pre")
    move("10.157.175.135","ring",[0,0,0])
    call_method("10.157.175.135",12000,"move_gripper",{"speed":1,"force":1,"width":0})
    move("10.157.175.135","026_left_pre",[0,0,0])
    #gear_insertion()

def gear_unmount_ring():
    move_joint("10.157.175.135","026_left_start")
    move_joint("10.157.175.135","026_left_container_above")
    call_method("10.157.175.135",12000,"move_gripper",{"speed":1,"force":1,"width":0})
    move("10.157.175.135","026_left_container_approach",[0,0,0])
    move("10.157.175.135","026_left_container",[0,0,0])
    call_method("10.157.175.135",12000,"grasp",{"speed":0.1,"width":0.04,"force":0.2,"epsilon_inner":1,"epsilon_outer":1})
    return gear_reset(False)
    

def gear_grasp():
    move_joint("10.157.175.135","026_left_pre")
    call_method("10.157.175.135",12000,"move_gripper",{"speed":1,"force":1,"width":0})
    move("10.157.175.135","ring",[0,0,0])
    call_method("10.157.175.135",12000,"grasp",{"speed":0.1,"width":0.04,"force":0.2,"epsilon_inner":1,"epsilon_outer":1})
    move("10.157.175.135","026_left_pre",[0,0,0])

def gear_reset(ring_inside = False):
    #call_method("10.157.175.135",12000,"move_gripper",{"force":100,"speed":0.08,"width":0.0,"espilon_inner":1,"epsilon_outer":1})
    if ring_inside:
        call_method("10.157.175.135",12000,"move_gripper",{"speed":1,"force":1,"width":0})
    result = extract("10.157.175.135","026_left","026_left_container_approach","026_left_container",12000)
    #move("10.157.175.135","026_left_container_approach",[0,0,0],12000,True)
    if not result["result"]["success"]:
        return False
    move("10.157.175.135","026_left_container_above",[0,0,0],12000,True)
    move_joint("10.157.175.135","026_left_start",12000,True)
    move_joint("10.157.175.135","026_left_pre")
    return True

def gear_insertion():
    call_method("10.157.175.135",12000,"set_grasped_object",{"object":"026_left"})
    move_joint("10.157.175.135","026_left_pre")

    move_joint("10.157.175.135","hold",13000,True)
    move_joint("10.157.175.135","026_left_start",12000,True)
    move_joint("10.157.175.135","026_left_container_above",12000,True)
    move("10.157.175.135","026_left_container_approach",[0,0,0],12000,True)

    content = {
        "skill": {
            "objects": {
                "Container": "026_left_container",
                "Approach": "026_left_container_approach",
                "Insertable": "026_left"
            },
            "time_max": 17,
            "p0": {
                "dX_d": [0.1, 1],
                "ddX_d": [0.5, 4],
                "DeltaX": [0, 0, 0, 0, 0, 0],
                "K_x": [1500, 1500, 1500, 600, 600, 600]
            },
            "p1": {
                "dX_d": [0.03, 0.1],
                "ddX_d": [0.5, 0.1],
                "K_x": [500, 500, 500, 600, 600, 600]
            },
            "p2": {
                "search_a": [1, 1, 0, 0, 0, 0],
                "search_f": [1, 1, 0, 1.2, 1.2, 0],
                "search_phi": [0, 3.14159265358979323846/2, 0, 3.14159265358979323846/2, 0, 0],
                "K_x": [500, 500, 500, 800, 800, 800],
                "f_push": [0, 0, 10, 0, 0, 0],
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1]
            },
            "p3": {
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
                "f_push": 7,
                "K_x": [500, 500, 0, 800, 800, 800]
            }
        },
        "control": {
            "control_mode": 0
        },
        "user": {
            "env_X": [0.01, 0.01, 0.002, 0.05, 0.05, 0.05],
            "env_dX": [0.001, 0.001, 0.001, 0.005, 0.005, 0.005],
            "F_ext_contact": [3.0, 2.0]
        }
    }
    t = Task("10.157.175.135")
    t.add_skill("insertion", "TaxInsertion", content)
    t.start()
    result = t.wait()
    print("Result: " + str(result))

def move_left(pose):
    threads = []
    for r in get_ips(modules):
        threads.append(Thread(target=move_joint, args=(r, pose, 12000, True)))
        threads[-1].start()

    for t in threads:
        t.join()
        
def move_right(pose):
    threads = []
    for r in get_ips(modules):
        threads.append(Thread(target=move_joint, args=(r, pose, 13000, True)))
        threads[-1].start()

    for t in threads:
        t.join()
                
    
def testrun():
    while True:
        move_joint("collective-019","019_left_container")
        move_joint("collective-019","019_left_container_approach")
        move_joint("collective-019","019_left_container_above")
        move_joint("collective-019","019_left")
        move_joint("collective-019","reset")

def stop_services(robots:list):
    for r in robots:
        s = ServerProxy("http://" + r + ":8000", allow_none=True)
        try:
            s.stop_service()
        except Exception as e:
            print("Error with robot ",r)
            print(e)

def attention(modules):
    for m in ["006","020","017"]:  #skip some modules
        try:
            index = modules.index(m)
            modules.pop(index)
        except ValueError:
            continue
    ips = get_ips(modules)
    move_some(ips, "reset")
    threads = []
    keep_running = True
    def wink(robot):
        while keep_running:
            left_arm = Thread(target=wink_thread,args=(robot, 12000))
            right_arm = Thread(target=wink_thread,args=(robot, 13000))
            left_arm.start()
            right_arm.start()
            left_arm.join()
            right_arm.join()
    print("press Crtl + c to stop waving")
    for r in ips:
        call_method(r, 12000, "stop_task")
        call_method(r, 13000, "stop_task")
        if r == "10.157.175.135":
            continue
        #threads.append(Thread(target=wink_thread, args=(r, 12000)))
        #threads.append(Thread(target=wink_thread, args=(r, 13000)))
        threads.append(Thread(target=wink, args=(r,)))
        #threads[-2].start()
        threads[-1].start()
    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        keep_running = False
        command_some(ips,"stop_task")
        time.sleep(1)
    move_some(ips,"reset")
    return "finished"  
    move_all("reset")
    move_all("wink")
    move_all("wink2")
    move_all("wink3")
    move_all("wink2")
    move_all("reset")

def move_to_approach_poses():
    threads = []
    c = 0
    all_modules = list_U+list_block_2+list_block_1
    print(all_modules)
    ips = get_ips(all_modules)
    for ip,m in zip(ips,all_modules):
        c += 1
        print(c, ": move collective-",m, " (",ip,")")
        threads.append(Thread(target=move_joint, args=(ip,"hold",13000,)))
        threads[-1].start()
        threads.append(Thread(target=move_joint, args=(ip,m+"_left_container_approach",12000,)))
        threads[-1].start()

    for t in threads:
        t.join()

def home_grippers(modules:list):
    ips = get_ips(modules)
    for robot in ips:
        call_method(robot,12000,"home_gripper",silent=True)
        call_method(robot,13000,"home_gripper", silent=True)

def grasp_all():
    threads = []
    for m in modules:
        threads.append(Thread(target=grasp, args=(m,None)))
        threads[-1].start()
    for t in threads:
        t.join()

def grasp(module, object=None, wait=False, side=None):
    t = Thread(target=grasp_thread, args=(module, object, side))
    t.start()
    if wait:
        t.join()

def grasp_thread(module, object=None, side=None):
    ip = get_ips([module])[0]
    
    insertable = object
    if not insertable:
        insertable = module+"_left"
    if module == "026":
        call_method(ip, 12000, "move_gripper",{"width":0.01,"speed":1,"force":1})
    if side == "left":
        call_method(ip,12000,"home_gripper")
        call_method(ip, 12000, "release_object")
        call_method(ip, 12000, "grasp", {"force":100, "speed":0.5, "width":0, "epsilon_inner":1, "epsilon_outer":1})
        call_method(ip, 12000, "set_grasped_object", {"object":insertable})
    elif side == "right":
        call_method(ip,13000,"home_gripper")
        call_method(ip, 13000, "release_object")
        call_method(ip, 13000, "grasp", {"force":100, "speed":0.5, "width":0, "epsilon_inner":1, "epsilon_outer":1})
    else:
        try:
            call_method(ip, 12000, "release_object",timeout=2)
        except TimeoutError:
            pass
        try:
            call_method(ip, 13000, "release_object",timeout=2)
        except TimeoutError:
            pass
        try:
            call_method(ip, 12000, "grasp", {"force":100, "speed":0.5, "width":0, "epsilon_inner":1, "epsilon_outer":1},timeout=4)
        except TimeoutError:
            pass
        try:
            call_method(ip, 13000, "grasp", {"force":100, "speed":0.5, "width":0, "epsilon_inner":1, "epsilon_outer":1})
        except TimeoutError:
            pass
        call_method(ip, 13000, "set_grasped_object", {"object":insertable})
        call_method(ip, 12000, "set_grasped_object", {"object":insertable})
    move_joint(ip, insertable+"_container_approach", 12000)
    if insertable[-4:] == "left":
        move_joint(ip, "hold",13000)
    else:
        move_joint(ip, "hold_"+insertable, 13000)

def release_objects(module):
    robot = get_ips([module])[0]
    call_method(robot,13000,"release_object")
    threads = []
    port = 12000
    for i in range(0,2):
        port += i*1000
        threads.append(Thread(target=call_method, args=(robot, port, "release_object",{},"mios/core",2)))
        threads[-1].start()
    for t in threads:
        t.join()


def get_objects(module,side = "left"):
    robot = get_ips([module])[0]
    client = MongoDBClient(robot)
    if side == "left":
        data = client.read("miosL","environment",{})
    else:
        data = client.read("miosR","environment",{})
    for d in data:
        print(d["name"])
    print("currently grasped: ", call_method(robot,12000, "get_state")["result"]["grasped_object"])

def approach_pose(module, object):
    robot = get_ips([module])[0]
    result1 = move_joint(robot, object+"_container_approach", port=12000)
    result2 = move_joint(robot, "hold_"+object,port=13000)
    return result1["result"]["task_result"]["success"] and result2["result"]["task_result"]["success"]

def teach_dualarm(module:str, object_name:str):
    insertable = object_name
    robot = get_ips([module])[0]
    print("\nteaching ",insertable, "for ", robot,"\n")
    input("teach hold position of right arm")
    call_method(robot, 13000, "teach_object",{"object":"hold_"+insertable})
    input("Press key to start teaching. [Pose above container, without object]")
    call_method(robot,12000,"release_object")
    call_method(robot, 12000, "teach_object", {"object": insertable+"_container_above"})
    input("Teach where to grab object")
    call_method(robot, 12000, "grasp", {"width":0,"speed":1,"force":100})
    call_method(robot, 12000, "teach_object", {"object": insertable, "teach_width":True})
    current_finger_width = call_method(robot,12000,"get_state")["result"]["gripper_width"]
    call_method(robot,12000,"move_gripper",{"speed":1,"force":100,"width":current_finger_width+0.005})
    #call_method(robot, mios_port, "grasp", {"width":0,"speed":1,"force":100,"epsilon_outer":1})
    #call_method(robot, mios_port, "set_grasped_object", {"object": insertable})
    time.sleep(1)
    print("closing gripper")
    print(call_method(robot, 12000, "grasp_object", {"object": insertable}))
    input("Teach approach [with object]")
    call_method(robot, 12000, "teach_object", {"object": insertable+"_container_approach"})
    input("Teach container [with object]")
    call_method(robot, 12000, "teach_object", {"object": insertable+"_container"})
    # print(call_method(robot, 12000, "grasp_object", {"object": insertable}))
    
    print(call_method(robot, 12000, "set_grasped_object",{"object":insertable}))      


def test_auto_object_exchange():
    pass

def teach_dualarm_without_homing(module:str, object_name:str):
    insertable = object_name
    robot = get_ips([module])[0]
    print("\nteaching ",insertable, "for ", robot,"\n")

    input("insert objects")
    call_method(robot, 13000, "teach_object",{"object":insertable})
    call_method(robot, 13000, "grasp", {"width":0,"speed":1,"force":100,"epsilon_outer":1})
    call_method(robot, 13000, "set_grasped_object",{"object":insertable})
    call_method(robot, 12000, "teach_object",{"object":insertable})
    call_method(robot, 12000, "grasp", {"width":0,"speed":1,"force":100,"epsilon_outer":1})
    call_method(robot, 12000, "set_grasped_object",{"object":insertable})

    input("teach hold position of right arm")
    call_method(robot, 13000, "teach_object",{"object":"hold_"+insertable})

    input("Press key to start teaching. [Pose above container, without object]")
    call_method(robot, 12000, "teach_object", {"object": insertable+"_container_above"})

    input("Teach approach [with object]")
    call_method(robot, 12000, "teach_object", {"object": insertable+"_container_approach"})

    input("Teach container [with object]")
    call_method(robot, 12000, "teach_object", {"object": insertable+"_container"})
   
