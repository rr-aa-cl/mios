from concurrent.futures import thread
from desk.mongodb_client import MongoDBClient
from xmlrpc.client import ServerProxy
import os
from threading import Thread
import copy
from utils.ws_client import *
import numpy as np
from numpy.linalg import inv
import json
import socket
import struct
from scipy.spatial.transform import Rotation
import math
import pprint

import time
import copy


###################################################################################
list_block_1 = ["001", #"002", 
                "003", "004", "005", 
                "006", "007", "033", "032", "008"]  #"044"->032
list_block_2 = ["035",
                "034","013","014", # -> 043 -> 034
                "015","042",
                "017", "016",  #041->017
                "021","022"]
list_U = ["023", "024", "025","026", "018","040","029"] # "028",  047 ->018
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

def command_some(robots:list, cmd: str, args: dict = {},robot_arm="all"):
    threads = []
    for r in robots:
        print(r)
        if robot_arm=="all" or robot_arm=="left":
            threads.append(Thread(target=call_method, args=(r, 12000, cmd, args,)))
            threads[-1].start()
        if robot_arm=="all" or robot_arm=="right":
            threads.append(Thread(target=call_method, args=(r, 13000, cmd, args,)))
            threads[-1].start()
    for t in threads:
        t.join()

def command_left(robots:list, cmd: str, args: dict = {}):
    threads = []
    for r in robots:
        print(r)
        threads.append(Thread(target=call_method, args=(r, 12000, cmd, args,)))
        threads[-1].start()
    for t in threads:
        t.join()

def command_right(robots:list, cmd: str, args: dict = {}):
    threads = []
    for r in robots:
        print(r)
        threads.append(Thread(target=call_method, args=(r, 13000, cmd, args,)))
        threads[-1].start()
    for t in threads:
        t.join()

def automatica_wave_small(robot, port=12000, min_time = 10, reverse=False):
    result = False
    speed = [1.5,5]
    while not result:
        result = move_joint(robot, "wave_high", port=port, speed=speed)["result"]["task_result"]["success"]
        speed = [s*0.8 for s in speed]
    pi = 3.14159265359
    if not reverse:
        wiggle_context1 = {
            "skill": {
                "dX_fourier_a_a": [0.2, 0.2, 0., 0, 0, 0.25],
                "dX_fourier_a_phi": [0, pi/2, 0, pi/2, 0, pi/2],
                "dX_fourier_a_f": [0.08, 0.08, 0, 0.6125, 0, 1.25],
                "dX_fourier_b_a": [0, 0, 0, 0, 0, 0],
                "dX_fourier_b_f": [0, 0, 0, 0, 0, 0],
                "use_EE": True,
                "time_max": min_time
            },
            "control": {
                "control_mode": 0
            }
        }
    else:
        wiggle_context1 = {
        "skill": {
            "dX_fourier_a_a": [0.2, 0.2, 0., 0, 0, 0.25],
            "dX_fourier_a_phi": [0, pi/2, 0, pi/2, 0, pi/2],
            "dX_fourier_a_f": [-0.08, -0.08, 0, 0.6125, 0, 1.25],
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

def automatica_wave_big(robot, port=12000, min_time = 10, reverse = False):
    result = False
    speed = [1.5,5]
    while not result:
        result = move_joint(robot, "wave_high", port=port, speed=speed)["result"]["task_result"]["success"]
        speed = [s*0.8 for s in speed]

    pi = 3.14159265359
    speed = 0.36
    if reverse:
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
    else:
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

def em_waving(robot="collective-026.rsi.ei.tum.de", duration=15):
    threads = []
    threads.append(Thread(target=automatica_wave_small, args=(robot, 12000, duration, False)))
    threads.append(Thread(target=automatica_wave_small, args=(robot, 13000, duration, True)))
    for t in threads:
        t.start()
    for t in threads:
        t.join()

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
        #big_flags = [("collective-016.rsi.ei.tum.de", 13000),("collective-021.rsi.ei.tum.de", 12000),("collective-021.rsi.ei.tum.de", 13000),
        #         ("collective-022.rsi.ei.tum.de", 12000),("collective-022.rsi.ei.tum.de", 13000),("collective-017.rsi.ei.tum.de", 12000),
        #         ("collective-014.rsi.ei.tum.de", 13000),("collective-020.rsi.ei.tum.de", 13000),("collective-015.rsi.ei.tum.de", 12000),
        #         ("collective-015.rsi.ei.tum.de", 13000),("collective-020.rsi.ei.tum.de", 12000)] # without banner
        big_flags = [("collective-023.rsi.ei.tum.de", 13000),("collective-023.rsi.ei.tum.de", 12000),("collective-024.rsi.ei.tum.de", 13000),
                 ("collective-024.rsi.ei.tum.de", 12000),("collective-025.rsi.ei.tum.de", 13000),("collective-025.rsi.ei.tum.de", 12000),
                 ("collective-026.rsi.ei.tum.de", 13000),("collective-026.rsi.ei.tum.de", 12000),("collective-027.rsi.ei.tum.de", 12000),
                 ("collective-027.rsi.ei.tum.de", 13000),("collective-029.rsi.ei.tum.de", 12000),("collective-029.rsi.ei.tum.de", 13000)]
        small_flags = []
        #small_flags = [("collective-018.rsi.ei.tum.de", 12000),("collective-018.rsi.ei.tum.de", 13000),
        #        ("collective-014.rsi.ei.tum.de", 12000),("collective-009.rsi.ei.tum.de", 12000),("collective-009.rsi.ei.tum.de", 13000),
        #        ("collective-013.rsi.ei.tum.de", 13000),("collective-016.rsi.ei.tum.de", 12000),("collective-013.rsi.ei.tum.de", 12000)]   # without banner
  
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

def grasp_lid():
    robot = "collective-036.rsi.ei.tum.de"
    move_joint(robot,"kitchen_top",port=13000)
    move(robot,"kitchen_pan",port=13000,f_ext=[15,10])
    call_method(robot,13000,"grasp",{"force":100,"width":0,"speed":1,"epsilon_inner":1,"epsilon_outer":1})
    move(robot,"EndEffector",offset=[0,0.05,-0.01],port=13000,f_ext=[100,50])
    move(robot,"kitchen_top",f_ext=[100,50],port=13000)
    move_joint(robot,"kitchen_top",port=13000)
    move_joint(robot,"kitchen_away",port=13000)

def grasp_whip():
    robot = "collective-036.rsi.ei.tum.de"
    move_joint(robot, "kitchen_top")
    move_joint(robot,"kitchen_whip")
    call_method(robot,12000,"grasp",{"force":100,"width":0,"speed":1,"epsilon_inner":1,"epsilon_outer":1})
    move_joint(robot, "kitchen_whip_up1")
    move_joint(robot, "kitchen_whip_up2")
    move_joint(robot, "kitchen_whip_up3")
    move_joint(robot, "kitchen_whip_over_pan")

def stir():
    robot = "collective-036.rsi.ei.tum.de"
    move_joint(robot, "kitchen_whip_pan")
    pi = 3.14159265359
    speed = 0.36
    wiggle_context1 = {
            "skill": {
                "dX_fourier_a_a": [0.01, 0, 0.01, 0, 0, 0],
                "dX_fourier_a_phi": [0, pi/2, 0, pi/2, 0, pi/2],
                "dX_fourier_a_f": [0.75, 0.08, 1, 0.6125, 0, 1.25],
                "dX_fourier_b_a": [0, 0, 0, 0, 0, 0],
                "dX_fourier_b_f": [0, 0, 0, 0, 0, 0],
                "use_EE": False,
                "time_max": 10
            },
            "control": {
                "control_mode": 0
            }
        }
    t = Task(robot,port=12000)
    t.add_skill("wiggle", "GenericWiggleMotion", wiggle_context1)
    t.start()
    t.wait()

def place_whip():
    robot = "collective-036.rsi.ei.tum.de"
    move(robot, "kitchen_whip_over_pan",f_ext=[15,10])
    move(robot, "kitchen_whip_wash",f_ext=[50,25])
    call_method(robot,12000,"release_object")
    move_joint(robot, "kitchen_top")

def place_lid():
    robot = "collective-036.rsi.ei.tum.de"  
    move(robot,"kitchen_pan",port=13000,f_ext=[15,10],offset=[0,0.05,-0.01])
    move(robot,"kitchen_pan",port=13000,f_ext=[15,10])
    call_method(robot,13000,"release_object")
    move(robot,"kitchen_pan",port=13000,f_ext=[15,10],offset=[0,0.05,-0.01])
    move(robot,"kitchen_top",f_ext=[100,50],port=13000)
    

def kitchen_aid():
    robot = "collective-036.rsi.ei.tum.de"
    #call_method(robot,12000,"home_gripper",{})
    #call_method(robot,13000,"home_gripper",{})
    #call_method(robot,12000,"move_gripper",{"force":100,"width":1,"speed":1,"epsilon_inner":1,"epsilon_outer":1})
    #call_method(robot,13000,"release_object",{"force":100,"width":0,"speed":1,"epsilon_inner":1,"epsilon_outer":1})
    move_joint(robot,"kitchen_default",port=13000)
    move_joint(robot,"kitchen_default",port=12000)
    grasp_lid()
    grasp_whip()
    stir()
    place_whip()
    move_joint(robot, "kitchen_default")
    place_lid()
    move_joint(robot,"kitchen_top",port=13000)
    move_joint(robot,"kitchen_default",port=13000)
    
def object_test(robot, object):
    call_method(robot, 12000, "set_grasped_object",{"object":object})
    wiggle_contextx = {
        "skill": {
            "dX_fourier_a_a": [-0, -0, -0, 0.15, 0, 0],
            "dX_fourier_a_phi": [0, 0, 0, 0, 0, 0],
            "dX_fourier_a_f": [0, -0, -0, 0.5, 0, 0],
            "dX_fourier_b_a": [0, 0, 0, 0, 0, 0],
            "dX_fourier_b_f": [0, 0, 0, 0, 0, 0],
            "use_EE": True,
            "time_max": 5
        },
        "control": {
            "control_mode": 0
        }
    }
    wiggle_contexty = {
        "skill": {
            "dX_fourier_a_a": [-0, -0, -0, 0, 0.15, 0],
            "dX_fourier_a_phi": [0, 0, 0, 0, 0, 0],
            "dX_fourier_a_f": [0, -0, -0, 0, 0.5, 0],
            "dX_fourier_b_a": [0, 0, 0, 0, 0, 0],
            "dX_fourier_b_f": [0, 0, 0, 0, 0, 0],
            "use_EE": True,
            "time_max": 5
        },
        "control": {
            "control_mode": 0
        }
    }
    wiggle_contextz = {
        "skill": {
            "dX_fourier_a_a": [-0, -0, -0, 0, 0, 0.15],
            "dX_fourier_a_phi": [0, 0, 0, 0, 0, 0],
            "dX_fourier_a_f": [0, -0, -0, 0, 0, 0.5],
            "dX_fourier_b_a": [0, 0, 0, 0, 0, 0],
            "dX_fourier_b_f": [0, 0, 0, 0, 0, 0],
            "use_EE": True,
            "time_max": 5
        },
        "control": {
            "control_mode": 0
        }
    }

    tr = Task(robot,12000)
    tr.add_skill("wigglex", "GenericWiggleMotion", wiggle_contextx)
    tr.add_skill("wiggley", "GenericWiggleMotion", wiggle_contexty)
    tr.add_skill("wigglez", "GenericWiggleMotion", wiggle_contextz)
    tr.start()
    try: 
        tr.wait()
    except KeyboardInterrupt:
        call_method(robot, 12000, "stop_task")

def log_test(ip = "collective-dev-001.rsi.ei.tum.de"):
    wiggle_contextx = {
        "skill": {
            "dX_fourier_a_a": [-0, -0, -0, 0, 0.15, 0],
            "dX_fourier_a_phi": [0, 0, 0, 0, 0, 0],
            "dX_fourier_a_f": [0, -0, -0, 0, 0.5, 0],
            "dX_fourier_b_a": [0, 0, 0, 0, 0, 0],
            "dX_fourier_b_f": [0, 0, 0, 0, 0, 0],
            "use_EE": True,
            "time_max": 7.2,
            "log_data":False,
            #"data_length":7200,
            "log_name":"log_test",
            "meta":{"description":"This is a log-test","tags":["this", "is", "a","test", "wiggle a bit"]},

        },
        "control": {
            "control_mode": 0,
            "cart_imp": {
                "K_x": [2000, 2000, 2000, 250, 25, 25]
            }
        }
    }
    tr = Task(ip,12000)
    tr.add_skill("wigglex", "GenericWiggleMotion", wiggle_contextx)
    tr.start(queue=False)
    call_method(ip,12000,"home_gripper")
    try: 
        print("Press <crl+c> for stopping.")
        tr.wait()
    except KeyboardInterrupt:
        call_method(ip, 12000, "stop_task")
    print(tr.wait()["result"]["task_result"]["skill_results"]["wigglex"]["cost"]["time"])

def log_test_without(ip = "collective-dev-001.rsi.ei.tum.de"):
    wiggle_contextx = {
        "skill": {
            "dX_fourier_a_a": [-0, -0, -0, 0.15, 0, 0],
            "dX_fourier_a_phi": [0, 0, 0, 0, 0, 0],
            "dX_fourier_a_f": [0, -0, -0, 0.5, 0, 0],
            "dX_fourier_b_a": [0, 0, 0, 0, 0, 0],
            "dX_fourier_b_f": [0, 0, 0, 0, 0, 0],
            "use_EE": True,
            "time_max": 5000,
            "log_data":True,
            "data_length":50000,
            "log_name":"wiggle_log_test",
            "log_to_file":True,
            "meta":{"description":"This is a log-test","tags":["this", "is", "a","test", "wiggle a bit"]},

        },
        "control": {
            "control_mode": 0
        }
    }
    tr = Task(ip,12000)
    tr.add_skill("wigglex", "GenericWiggleMotion", wiggle_contextx)
    tr.start(queue=False)
    try: 
        print("Press <crl+c> for stopping.")
        tr.wait()
    except KeyboardInterrupt:
        call_method(ip, 12000, "stop_task")

def move_to_object(module,obj,add_nullspace=True,f_ext=[40,20],port=12000,wait=True):
    ip = get_ips([module])[0]
    o = call_method(ip,12000,"download_object_context",{"object":obj})["result"]["context"]
    context = {
        "skill": {
            "p0":{
                "dX_d": [0.3, 0.8],
                "ddX_d": [0.5, 1],
                "K_x": [2000, 2000, 2000, 250, 250, 250],
                "T_T_EE_g":o["O_T_OB"]
                #"T_T_EE_g_offset": [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, offset[0], offset[1], offset[2], 1]
            },
            "time_max":10,
            "objects": {
                    "GoalPose": "NoneObject"
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
    if add_nullspace:
        context["control"]["nullspace"] = {
                                                    "K_theta": [20, 20, 15, 10, 7, 5, 2],
                                                    "xi_theta": [0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7],
                                                    "active": True
                                                    }
    t = Task(ip, port=port)
    t.add_skill("move", "TaxMove", context)
    t.start()
    if wait:
        return t.wait()

def delete_object(module, object):
    ip = get_ips([module])[0]

    o = call_method(ip,12000,"download_object_context",{"object":object})["result"]["context"]
    o["OB_T_TCP"] = [   1, 0,  0,  0,  # drehung um x-achse
                        0, 1,  0,  0,
                        0, 0,  1,  0,
                        0, 0,  0,  1]
    
    #o["OB_T_gp"] = copy.deepcopy(o["OB_T_TCP"])
    o["OB_T_gp"] = [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]
    o["mass"] = 0
    o["OB_I"] = [1,0,0, 0,1,0, 0,0,1]
    o["object"] = o["name"]
    call_method(ip,12000, "set_object", o)
    
def modify_object_transformations(module, object, z_mm, y_mm=0.0, x_mm=0.0, mass=0.0,y_ang=0, inertia = [1,0,0, 0,1,0, 0,0,1]):
    # old inertia (works)  [0.00684,-0.00279,0, -0.00279,0.00709,0, 0,0,0.00731]
    # new inertia: 
    ip = get_ips([module])[0]
    try:
        o = call_method(ip,12000,"download_object_context",{"object":object})["result"]["context"]
    except KeyError:
        call_method(ip,12000,"teach_object",{"object":object})
        o = call_method(ip,12000,"download_object_context",{"object":object})["result"]["context"]

    o["OB_T_TCP"] = [   np.cos(y_ang),   0,   -np.sin(y_ang),  0,  #drehung um y-achse
                        0,               1,   0,               0,
                        np.sin(y_ang),   0,   np.cos(y_ang),   0,
                        0,               0,   0,               1]
    o["OB_T_TCP"] = [   1, 0,                               0,  0,  # drehung um x-achse
                        0,  np.cos(y_ang),   -np.sin(y_ang),   0,
                        0,   np.sin(y_ang),   np.cos(y_ang),   0,
                        0,               0,   0,               1]
    
    #o["OB_T_gp"] = copy.deepcopy(o["OB_T_TCP"])
    o["OB_T_gp"] = [1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]
    o["OB_T_TCP"][14] = z_mm/2000
    o["OB_T_gp"][14] = -z_mm/2000

    o["OB_T_TCP"][13] = y_mm/2000
    o["OB_T_gp"][13] = -y_mm/2000

    o["OB_T_TCP"][12] = x_mm/2000
    o["OB_T_gp"][12] = -x_mm/2000

    o["mass"] = mass

    o["OB_I"] = inertia
    
    o["object"] = o["name"]
    call_method(ip,12000, "set_object", o)

def test_object_transformations(module, object, z_m):
    # old inertia (works)  [0.00684,-0.00279,0, -0.00279,0.00709,0, 0,0,0.00731]
    # new inertia: 
    ip = get_ips([module])[0]
    o = call_method(ip,12000,"download_object_context",{"object":object})["result"]["context"]

    o["OB_T_TCP"][14] = z_m
    #o["OB_T_gp"][14] = -z_m
    
    o["object"] = o["name"]
    call_method(ip,12000, "set_object", o)
    
def modify_object_kinematics(module, object,wrench_size=19,l_short=None,l_long=None, grasping_offset_mm=[0,0,0],angle_y=0.,angle_x=0.,mass=None):
        # Define the parameters for the calculation
    # Provide the measured total mass of the wrench in kilograms

    '''
        calculate_hex_wrench_inertia(
    total_mass: float,
    l_long: float,
    l_short: float,
    hex_size: float,
    grasp_offset_translation: tuple[float, float, float] = (0, 0, 0),
    grasp_offset_rotation_xyz_rad: tuple[float, float, float] = (0, 0, 0)
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculates the inertia matrix and transformation matrices for a hex wrench.

    The function models the hex wrench as an L-shape of two hexagonal prisms.
    The object frame is centered at the Center of Mass (CoM). Its z-axis points
    along the long handle, and its x-axis points along the negative short handle.

    Args:
        total_mass: The total mass of the hex wrench in kg.
        l_long: The length of the longer handle in meters.
        l_short: The length of the shorter handle in meters.
        hex_size: The size of the hex wrench (width across flats) in millimeters.
        grasp_offset_translation: (dx, dy, dz) translation of the grasping frame
            from the handle intersection, in meters.
        grasp_offset_rotation_xyz_rad: (rx, ry, rz) Euler angles in radians for the
            grasping frame's orientation relative to the object frame.

    Returns:
        A tuple containing:
        - inertia_matrix_obj (np.ndarray): The 3x3 inertia tensor in the object frame.
        - T_obj_to_grasp (np.ndarray): The 4x4 transformation from the object
          frame to the grasping frame.
        - T_obj_to_tip (np.ndarray): The 4x4 transformation from the object
          frame to the tip of the long handle.
    """
    '''
    kinematics = calculate_hex_wrench_inertia(mass,l_long,l_short,wrench_size, (grasping_offset_mm[0]/1000,grasping_offset_mm[1]/1000,grasping_offset_mm[2]/1000), (math.radians(angle_x),math.radians(angle_y),0))

    # Calculate the kinematics using the provided mass
    # kinematics = calculate_wrench_kinematics(
    #         hex_size_mm=wrench_size,
    #         grasp_offset_xy_mm=grasping_offset,
    #         grasp_angle_y_deg=angle_y,
    #         grasp_angle_x_deg=angle_x,
    #         total_mass_kg=mass,
    #         L_long_mm=l_short,
    #         L_short_mm=l_long
    #     )
  
    # --- Print the results in a readable format ---

    print("inertia_matrix_obj (np.ndarray): 3x3 inertia tensor in the object frame {O} (kg*m^2)")
    print(kinematics[0])
    print("\n" + "="*40 + "\n")

    print("T_grasp_in_obj (np.ndarray): 4x4 homogeneous transformation matrix from the object frame {O} to the grasping frame {F_grasp}.:")
    print(inv(kinematics[1]))
    print("\n" + "="*40 + "\n")

    print("T_tip_in_obj (np.ndarray): 4x4 homogeneous transformation matrix from the object frame {O} to the tip frame {F_tip} (tip at end of short handle, aligned with {O})")
    print(kinematics[2])
    print("\n" + "="*40 + "\n")

    # --- Export matrices to column-major lists as requested ---
    
    # Flattening with 'F' (Fortran) order gives column-major
    inertia_list = kinematics[0].flatten('F').tolist()
    T_grasp_com_list = kinematics[1].flatten('F').tolist()
    T_com_tip_list = kinematics[2].flatten('F').tolist()

    ip = get_ips([module])[0]
    try:
        o = call_method(ip,12000,"download_object_context",{"object":object})["result"]["context"]
    except KeyError:
        call_method(ip,12000,"teach_object",{"object":object})
        o = call_method(ip,12000,"download_object_context",{"object":object})["result"]["context"]
    o["OB_I"] = inertia_list
    o["OB_T_gp"] = T_grasp_com_list
    o["OB_T_TCP"] = T_com_tip_list
    o["mass"] = mass
    o["object"] = o["name"]
    call_method(ip,12000, "set_object", o)
    return kinematics

def skew_symmetric_matrix(v):
    """
    Creates a skew-symmetric matrix from a 3-element vector.
    This is used for cross-product operations in matrix form (e.g., in Parallel Axis Theorem).
    [v]x = [[0, -vz, vy], [vz, 0, -vx], [-vy, vx, 0]]
    """
    return np.array([
        [0, -v[2], v[1]],
        [v[2], 0, -v[0]],
        [-v[1], v[0], 0]
    ])

def calculate_wrench_kinematics_unused(
    hex_size_mm: float,
    grasp_offset_xy_mm: list,
    grasp_angle_y_deg: float,
    grasp_angle_x_deg: float,
    total_mass_kg: float = None,
    steel_density_kg_m3: float = 7850.0,
    L_long_mm: float = None,
    L_short_mm: float = None
):
    """
    Calculates the inertia matrix and transformation matrices for an L-shaped hex wrench.

    The function establishes a 'body frame' {B} for the wrench with:
    - Origin at the internal corner of the L-shape.
    - Z-axis aligned with the long handle.
    - X-axis aligned with the short handle.
    - Y-axis completing the right-handed system.
    
    A 'Center of Mass frame' {C} is defined at the CoM, with axes parallel to {B}.

    Args:
        hex_size_mm (float): The size of the wrench across the flats, in millimeters.
        grasp_offset_xy_mm (list): A list or tuple [x, y] for the grasping point offset
                                   from the wrench corner, in millimeters.
        grasp_angle_y_deg (float): The grasping orientation tilt around the Y-axis, in degrees.
        grasp_angle_x_deg (float): The grasping orientation tilt around the X-axis, in degrees.
        total_mass_kg (float, optional): The total measured mass of the wrench in kg.
                                         If provided, this is used instead of calculating
                                         mass from density. Defaults to None.
        steel_density_kg_m3 (float, optional): Density of the material. Only used if
                                               total_mass_kg is not provided. Defaults to steel.
        L_long_mm (float, optional): The length of the long handle in mm. If not provided,
                                     it's estimated from hex_size_mm.
        L_short_mm (float, optional): The length of the short handle in mm. If not provided,
                                      it's estimated from hex_size_mm.

    Returns:
        dict: A dictionary containing the calculated matrices and key properties:
              - 'inertia_matrix_com_in_body_frame': 3x3 inertia tensor about the center of mass,
                                                    oriented in the CoM/Body frame.
              - 'T_com_from_grasp': 4x4 transform from the grasp frame {G} to the CoM frame {C}.
              - 'T_com_from_tip': 4x4 transform from the tip frame {T} to the CoM frame {C}.
              - 'wrench_properties': A dict of calculated physical properties.
    """
    # 1. --- CONVERT INPUTS AND ESTIMATE GEOMETRY ---
    s = hex_size_mm / 1000.0
    grasp_offset = np.array([grasp_offset_xy_mm[0] / 1000.0, grasp_offset_xy_mm[1] / 1000.0, 0.0])
    angle_y_rad = np.deg2rad(grasp_angle_y_deg)
    angle_x_rad = np.deg2rad(grasp_angle_x_deg)
    
    if L_long_mm is not None and L_long_mm > 0:
        L_long = L_long_mm / 1000.0
    else:
        L_long = (10 * hex_size_mm + 30) / 1000.0
    
    if L_short_mm is not None and L_short_mm > 0:
        L_short = L_short_mm / 1000.0
    else:
        L_short = (4 * hex_size_mm + 12) / 1000.0

    # 2. --- CALCULATE MASS AND GEOMETRIC PROPERTIES ---
    A = (np.sqrt(3) / 2) * s**2
    J_area = (5 * np.sqrt(3) / 72) * s**4 

    if total_mass_kg is not None and total_mass_kg > 0:
        M_total = total_mass_kg
        total_length = L_long + L_short
        M_long = M_total * (L_long / total_length) if total_length > 0 else 0
        M_short = M_total * (L_short / total_length) if total_length > 0 else 0
        
        total_volume = A * total_length
        effective_density = M_total / total_volume if total_volume > 0 else 0
        J_mass_per_length = effective_density * J_area
    else:
        M_long = steel_density_kg_m3 * A * L_long
        M_short = steel_density_kg_m3 * A * L_short
        M_total = M_long + M_short
        J_mass_per_length = steel_density_kg_m3 * J_area

    # 3. --- CALCULATE INERTIA TENSOR IN BODY FRAME {B} ---
    I_cm_long = np.diag([(1/12)*M_long*L_long**2, (1/12)*M_long*L_long**2, J_mass_per_length*L_long])
    r_long = np.array([0, 0, L_long / 2])
    I_origin_long = I_cm_long - M_long * skew_symmetric_matrix(r_long) @ skew_symmetric_matrix(r_long)

    I_cm_short = np.diag([J_mass_per_length*L_short, (1/12)*M_short*L_short**2, (1/12)*M_short*L_short**2])
    r_short = np.array([L_short / 2, 0, 0])
    I_origin_short = I_cm_short - M_short * skew_symmetric_matrix(r_short) @ skew_symmetric_matrix(r_short)

    I_body = I_origin_long + I_origin_short

    # 4. --- CALCULATE CENTER OF MASS (CoM) ---
    P_com = (r_long * M_long + r_short * M_short) / M_total if M_total > 0 else np.zeros(3)
    
    # 5. --- CALCULATE INERTIA TENSOR AT CENTER OF MASS (CoM) ---
    I_com_in_body_frame = I_body + M_total * (skew_symmetric_matrix(P_com) @ skew_symmetric_matrix(P_com))

    # 6. --- CALCULATE TRANSFORMATION MATRICES ---
    cy, sy = np.cos(angle_y_rad), np.sin(angle_y_rad)
    cx, sx = np.cos(angle_x_rad), np.sin(angle_x_rad)
    Rot_y = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rot_x = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    R_B_G = Rot_y @ Rot_x # Rotation from Grasp frame {G} to Body frame {B}
    
    # Transformation from Grasp frame {G} to CoM frame {C}. P_C = T_C_G * P_G
    T_com_from_grasp = np.identity(4)
    T_com_from_grasp[:3, :3] = R_B_G # CORRECTED: Rotation from {G} to {C} is R_C_G = R_B_G
    translation_vector = grasp_offset - P_com # Vector from CoM origin to Grasp origin, in {C} coords
    T_com_from_grasp[:3, 3] = translation_vector

    # Transformation from Tip Frame {T} to CoM Frame {C}. P_C = T_C_T * P_T
    P_tip = np.array([0, 0, L_long])
    r_com_to_tip = P_tip - P_com
    T_com_from_tip = np.identity(4)
    T_com_from_tip[:3, 3] = r_com_to_tip

    # 7. --- COMPILE RESULTS ---
    results = {
        "inertia_matrix_com_in_body_frame": I_com_in_body_frame,
        "T_com_from_grasp": T_com_from_grasp,
        "T_com_from_tip": T_com_from_tip,
        "wrench_properties": {
            "hex_size_mm": hex_size_mm,
            "L_long_m": L_long,
            "L_short_m": L_short,
            "total_mass_kg": M_total,
            "com_in_body_frame_m": P_com,
            "grasp_point_in_body_frame_m": grasp_offset,
            "grasp_rotation_matrix_R_B_G": R_B_G,
        }
    }
    return results


def calculate_hex_wrench_inertia(
    total_mass: float,
    l_long: float,
    l_short: float,
    hex_size: float,
    grasp_offset_translation: tuple[float, float, float] = (0, 0, 0),
    grasp_offset_rotation_xyz_rad: tuple[float, float, float] = (0, 0, 0)
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calculates the inertia matrix and transformation matrices for a hex wrench.

    The function models the hex wrench as an L-shape of two hexagonal prisms.
    The object frame is centered at the Center of Mass (CoM). Its z-axis points
    along the long handle, and its x-axis points along the negative short handle.

    Args:
        total_mass: The total mass of the hex wrench in kg.
        l_long: The length of the longer handle in meters.
        l_short: The length of the shorter handle in meters.
        hex_size: The size of the hex wrench (width across flats) in millimeters.
        grasp_offset_translation: (dx, dy, dz) translation of the grasping frame
            from the handle intersection, in meters.
        grasp_offset_rotation_xyz_rad: (rx, ry, rz) Euler angles in radians for the
            grasping frame's orientation relative to the object frame.

    Returns:
        A tuple containing:
        - inertia_matrix_obj (np.ndarray): The 3x3 inertia tensor in the object frame.
        - T_obj_to_grasp (np.ndarray): The 4x4 transformation from the object
          frame to the grasping frame.
        - T_obj_to_tip (np.ndarray): The 4x4 transformation from the object
          frame to the tip of the long handle.
    """
    # 1. Geometric and Mass Properties
    # Convert hex size from mm to meters
    width_across_flats = hex_size / 1000.0
    # Side length 's' of the hexagon
    s = width_across_flats / np.sqrt(3)
    # Area of the hexagonal cross-section
    area = (3 * np.sqrt(3) / 2) * s**2

    # Mass distribution based on length
    total_length = l_long + l_short
    mass_long = total_mass * (l_long / total_length)
    mass_short = total_mass * (l_short / total_length)
    density = total_mass / (area * total_length)

    # 2. Center of Mass (CoM) Calculation
    # We define a "build" frame with the origin at the intersection of the handles.
    # The long handle is along the z-axis, the short handle is along the x-axis.
    # CoM of long handle in build frame
    com_long_build = np.array([0, 0, l_long / 2])
    # CoM of short handle in build frame
    com_short_build = np.array([l_short / 2, 0, 0])

    # Total CoM in the build frame
    p_com_build = (com_long_build * mass_long + com_short_build * mass_short) / total_mass
    x_com, y_com, z_com = p_com_build

    # 3. Inertia Tensors of Individual Handles
    # Inertia tensor for a hexagonal prism about its own CoM.
    # Ixx = Iyy for a regular hexagonal prism.
    Ixx_yy_component = (1/12) * (5 * s**2) + (1/3) * (0.5**2) # Simplified term for length
    Izz_component = (5/6) * s**2

    I_prism_long = mass_long * np.diag([
        Ixx_yy_component * l_long**2,
        Ixx_yy_component * l_long**2,
        Izz_component
    ])
    I_prism_short = mass_short * np.diag([
        Izz_component, # Main axis is now along x
        Ixx_yy_component * l_short**2,
        Ixx_yy_component * l_short**2
    ])


    # 4. Parallel Axis Theorem
    # Shift inertia of each handle to the total CoM of the wrench.
    # Vector from total CoM to long handle's CoM
    r_long = com_long_build - p_com_build
    R_long = np.array([[0, -r_long[2], r_long[1]], [r_long[2], 0, -r_long[0]], [-r_long[1], r_long[0], 0]])
    I_total_long = I_prism_long + mass_long * (R_long @ R_long.T)

    # Vector from total CoM to short handle's CoM
    r_short = com_short_build - p_com_build
    R_short = np.array([[0, -r_short[2], r_short[1]], [r_short[2], 0, -r_short[0]], [-r_short[1], r_short[0], 0]])
    I_total_short = I_prism_short + mass_short * (R_short @ R_short.T)

    # Total inertia tensor in the "build" frame orientation
    I_build = I_total_long + I_total_short

    # 5. Rotate to the Final Object Frame
    # The object frame has z_obj along long handle (+z_build) and x_obj along
    # negative short handle (-x_build). y_obj completes the right-hand system.
    # x_obj = [-1, 0, 0], z_obj = [0, 0, 1] -> y_obj = z_obj x x_obj = [0, -1, 0]
    R_obj_in_build = np.array([
        [-1, 0, 0],
        [0, -1, 0],
        [0, 0, 1]
    ])
    # To transform the tensor from build to obj frame: I_obj = R.T * I_build * R
    I_obj = R_obj_in_build.T @ I_build @ R_obj_in_build


    # 6. Calculate Transformation Matrices
    # --- Transformation to the Tip of the LONG Handle ---
    # Position of the tip in the "build" frame (end of the long handle)
    p_tip_build = np.array([0, 0, l_long])

    # Position of the tip relative to the object frame's origin (CoM)
    # Transform the vector (p_tip - p_com) from build frame to object frame
    p_tip_in_obj_translation = R_obj_in_build.T @ (p_tip_build - p_com_build)

    # Create the 4x4 transformation matrix from object frame to tip frame
    T_obj_to_tip = np.eye(4)
    T_obj_to_tip[:3, 3] = p_tip_in_obj_translation

    # --- Transformation to the Grasping Frame ---
    # Grasping point is at the intersection (origin of build frame) plus offset
    p_grasp_build = np.array(grasp_offset_translation)

    # Position of the grasp point relative to the object frame's origin (CoM)
    p_grasp_in_obj_translation = R_obj_in_build.T @ (p_grasp_build - p_com_build)

    # Create the rotation part of the transformation
    R_grasp_in_obj = Rotation.from_euler('xyz', grasp_offset_rotation_xyz_rad).as_matrix()

    # Create the 4x4 transformation matrix
    T_obj_to_grasp = np.eye(4)
    T_obj_to_grasp[:3, :3] = R_grasp_in_obj
    T_obj_to_grasp[:3, 3] = p_grasp_in_obj_translation

    return I_obj, T_obj_to_grasp, T_obj_to_tip


def calculate_hex_wrench_properties(
    total_mass_kg,
    length_long_handle_m,
    length_short_handle_m,
    hex_wrench_waf_m,  # Width Across Flats of the hexagonal cross-section, in meters
    grasp_offset_x_m,
    grasp_offset_y_m,
    grasp_offset_z_m,
    grasp_angle_x_rad, # Euler angle for rotation around X-axis of object frame
    grasp_angle_y_rad, # Euler angle for rotation around Y-axis of object frame
    grasp_angle_z_rad  # Euler angle for rotation around Z-axis of object frame
):
    """
    Calculates the inertia matrix and transformation matrices for an L-shaped hex wrench.

    The hex wrench is approximated as two rigidly connected hexagonal prisms.
    The object frame {O} is defined with its origin at the center of mass (COM) of the wrench.
    The zO-axis is along the long handle (positive ZG direction of initial setup).
    The xO-axis is along the negative of the short handle (negative XG direction of initial setup).
    The yO-axis completes a right-handed system (yO = zO x xO, which is negative YG).

    Args:
        total_mass_kg (float): Total mass of the hex wrench in kilograms.
        length_long_handle_m (float): Length of the long handle in meters.
        length_short_handle_m (float): Length of the short handle in meters.
        hex_wrench_waf_m (float): Width Across Flats of the hexagonal cross-section in meters.
        grasp_offset_x_m (float): Translational offset of the grasping point from the
                                   intersection of handles, along the XG-axis (meters).
        grasp_offset_y_m (float): Translational offset of the grasping point from the
                                   intersection of handles, along the YG-axis (meters).
        grasp_offset_z_m (float): Translational offset of the grasping point from the
                                   intersection of handles, along the ZG-axis (meters).
        grasp_angle_x_rad (float): Euler angle for the grasping frame's rotation about the
                                   object frame's X-axis (radians). Applied first.
        grasp_angle_y_rad (float): Euler angle for the grasping frame's rotation about the
                                   object frame's Y-axis (radians). Applied second.
        grasp_angle_z_rad (float): Euler angle for the grasping frame's rotation about the
                                   object frame's Z-axis (radians). Applied third.
                                   The rotation sequence is extrinsic XYZ.

    Returns:
        tuple: Contains:
            - inertia_matrix_obj (np.ndarray): 3x3 inertia tensor in the object frame {O} (kg*m^2).
            - T_grasp_in_obj (np.ndarray): 4x4 homogeneous transformation matrix from the
                                           object frame {O} to the grasping frame {F_grasp}.
            - T_tip_in_obj (np.ndarray): 4x4 homogeneous transformation matrix from the
                                         object frame {O} to the tip frame {F_tip}
                                         (tip at end of short handle, aligned with {O}).
    """

    # --- Input Validation ---
    if total_mass_kg <= 0:
        raise ValueError("Total mass must be positive.")
    if length_long_handle_m < 0 or length_short_handle_m < 0:
        raise ValueError("Handle lengths cannot be negative.")
    if hex_wrench_waf_m <= 0:
        raise ValueError("Hex wrench WAF must be positive.")
    if length_long_handle_m == 0 and length_short_handle_m == 0:
        raise ValueError("At least one handle must have a non-zero length.")

    # --- A. Preliminaries and COM Calculation ---

    # 1. Hexagon side length 'a' from WAF [2, 3]
    # WAF = a * sqrt(3)
    a_m = hex_wrench_waf_m / np.sqrt(3)

    # 2. Cross-sectional area A_hex (not directly needed for mass distribution if total_mass is given)
    # A_hex_m2 = (3 * np.sqrt(3) / 2) * a_m**2

    # 3. Masses of individual handles (M_l, M_s)
    # Assuming uniform density, mass is proportional to length if cross-section is constant.
    total_length = length_long_handle_m + length_short_handle_m
    if total_length == 0: # Should be caught by earlier check, but for safety
        mass_long_handle_kg = 0
        mass_short_handle_kg = 0
    else:
        mass_long_handle_kg = total_mass_kg * (length_long_handle_m / total_length)
        mass_short_handle_kg = total_mass_kg * (length_short_handle_m / total_length)

    # 4. COM of individual handles in a global frame {G}
    # {G} origin: inner corner of L-bend. Long handle along ZG, short handle along XG.
    com1_G = np.array([0, 0, length_long_handle_m / 2])  # Long handle (Prism 1)
    com2_G = np.array([length_short_handle_m / 2, 0, 0])  # Short handle (Prism 2)

    # 5. COM of the composite wrench (COM_total) in {G} [4, 5]
    if total_mass_kg == 0: # Avoid division by zero if mass is zero (though validated earlier)
        com_total_G = np.array([0.0, 0.0, 0.0])
    else:
        com_total_G = (mass_long_handle_kg * com1_G + mass_short_handle_kg * com2_G) / total_mass_kg
    
    x_com_total_G = com_total_G
    y_com_total_G = com_total_G[1] # Should be 0
    z_com_total_G = com_total_G[2]

    # --- B. Inertia Tensor Calculation ---

    # Inertia tensor for a hexagonal prism of mass m_p, length L_p, side a_m
    # Longitudinal (along L_p): I_long = (5/12) * m_p * a_m^2
    # Transverse: I_trans = m_p * (L_p^2/12 + (5/24)*a_m^2)
    # [6, 7, 8]

    # 6. Inertia tensor of Prism 1 (long handle) about its own COM (com1_G), axes parallel to {G}
    # Length L_p = length_long_handle_m, mass m_p = mass_long_handle_kg
    # Long handle is along ZG axis.
    I1_xx_local = mass_long_handle_kg * (length_long_handle_m**2 / 12 + (5/24) * a_m**2)
    I1_yy_local = mass_long_handle_kg * (length_long_handle_m**2 / 12 + (5/24) * a_m**2)
    I1_zz_local = (5/12) * mass_long_handle_kg * a_m**2
    I1_local_com_G = np.diag([I1_xx_local, I1_yy_local, I1_zz_local])

    # 7. Inertia tensor of Prism 2 (short handle) about its own COM (com2_G), axes parallel to {G}
    # Length L_p = length_short_handle_m, mass m_p = mass_short_handle_kg
    # Short handle is along XG axis.
    I2_xx_local = (5/12) * mass_short_handle_kg * a_m**2 # Longitudinal for Prism 2
    I2_yy_local = mass_short_handle_kg * (length_short_handle_m**2 / 12 + (5/24) * a_m**2)
    I2_zz_local = mass_short_handle_kg * (length_short_handle_m**2 / 12 + (5/24) * a_m**2)
    I2_local_com_G = np.diag([I2_xx_local, I2_yy_local, I2_zz_local])

    # 8. Displacement vectors for Parallel Axis Theorem (from COM_total to component COMs)
    d1_G = com1_G - com_total_G
    d2_G = com2_G - com_total_G

    # 9. Parallel Axis Theorem application [9, 10, 11]
    def parallel_axis_term(mass, d_vec):
        dx, dy, dz = d_vec
        term = np.array([[dy**2 + dz**2, -dx*dy,        -dx*dz],
            [-dx*dy,        dx**2 + dz**2, -dy*dz],
            [-dx*dz,        -dy*dz,        dx**2 + dy**2]])
        return mass * term

    I1_shifted_G_prime = I1_local_com_G + parallel_axis_term(mass_long_handle_kg, d1_G)
    I2_shifted_G_prime = I2_local_com_G + parallel_axis_term(mass_short_handle_kg, d2_G)

    # 10. Total inertia tensor in {G'} (origin at COM_total, axes parallel to {G}) [1]
    I_total_G_prime = I1_shifted_G_prime + I2_shifted_G_prime

    # 11. Rotation matrix from {G'} to Object Frame {O} (R_G_prime_to_O)
    # zO || ZG'  => k_O = _G'
    # xO || -XG' => i_O = [-1,0,0]_G'
    # yO = k_O x i_O = [0,-1,0]_G' (yO || -YG')
    R_G_prime_to_O = np.array([[-1, 0,  0],
        [ 0, -1, 0],
        [ 0, 0,  1]])

    # 12. Inertia tensor in Object Frame {O} (I_obj) [12, 13]
    inertia_matrix_obj = R_G_prime_to_O @ I_total_G_prime @ R_G_prime_to_O.T

    # --- C. Transformation Matrices --- [14, 15]

    # 13. Transformation from Object Frame {O} to Grasping Frame {F_grasp} (T_Fgrasp_in_O)
    # Grasping point base location in {G} (intersection of handles)
    P_grasp_base_G = np.array([0.0, 0.0, 0.0])
    # Apply user offset (assuming offset is in {G} coordinates from the intersection)
    P_grasp_offset_G = np.array([grasp_offset_x_m, grasp_offset_y_m, grasp_offset_z_m])
    P_grasp_final_G = P_grasp_base_G + P_grasp_offset_G

    # Position vector of P_grasp_final relative to COM_total (origin of {O}), expressed in {G'}
    P_grasp_final_G_prime = P_grasp_final_G - com_total_G
    
    # Position vector of P_grasp_final relative to origin of {O}, expressed in {O} components
    P_grasp_origin_in_O = R_G_prime_to_O @ P_grasp_final_G_prime

    # Rotation for grasping frame: R_Fgrasp_in_O
    # Euler angles (grasp_angle_x, y, z_rad) define orientation of F_grasp w.r.t. O
    # Applied as extrinsic XYZ: Rot(X,ax) then Rot(Y,ay) then Rot(Z,az)
    # This means R_Fgrasp_in_O = Rz(az) * Ry(ay) * Rx(ax)
    # Scipy's from_euler('XYZ', [ax,ay,az]) is Rx(ax)Ry(ay)Rz(az)
    # To get Rz Ry Rx, we can compose:
    rot_x = Rotation.from_euler('x', grasp_angle_x_rad, degrees=False)
    rot_y = Rotation.from_euler('y', grasp_angle_y_rad, degrees=False)
    rot_z = Rotation.from_euler('z', grasp_angle_z_rad, degrees=False)
    R_Fgrasp_in_O_obj = (rot_z * rot_y * rot_x).as_matrix()
    # Alternative using 'zyx' intrinsic which is equivalent to 'XYZ' extrinsic if order is reversed
    # R_Fgrasp_in_O_obj = Rotation.from_euler('zyx', 
    #                                     [grasp_angle_z_rad, grasp_angle_y_rad, grasp_angle_x_rad], 
    #                                     degrees=False).as_matrix()
    # Simpler: use 'XYZ' extrinsic, which is R = Rz Ry Rx if applied as Rz(angles[2])Ry(angles[1])Rx(angles)
    # No, scipy from_euler('XYZ', [ax,ay,az]) is R = Rx(ax)Ry(ay)Rz(az)
    # The most explicit way for Rz Ry Rx:
    # R_grasp_orientation_in_O = Rotation.from_euler('z', grasp_angle_z_rad).as_matrix() @ \
    #                            Rotation.from_euler('y', grasp_angle_y_rad).as_matrix() @ \
    #                            Rotation.from_euler('x', grasp_angle_x_rad).as_matrix()
    # Let's use the composition method for clarity on Rz*Ry*Rx
    R_Fgrasp_in_O_obj = (Rotation.from_euler('z', grasp_angle_z_rad) * \
                         Rotation.from_euler('y', grasp_angle_y_rad) * \
                         Rotation.from_euler('x', grasp_angle_x_rad)).as_matrix()


    T_grasp_in_obj = np.eye(4)
    T_grasp_in_obj[0:3, 0:3] = R_Fgrasp_in_O_obj
    T_grasp_in_obj[0:3, 3] = P_grasp_origin_in_O

    # 14. Transformation from Object Frame {O} to Tip Frame {F_tip} (T_Ftip_in_O)
    # Tip location in {G} (end of short handle)
    P_tip_G = np.array([length_short_handle_m, 0.0, 0.0])
    p_tip_build = np.array([0, 0, l_long])

    # Position vector of P_tip relative to COM_total (origin of {O}), expressed in {G'}
    P_tip_G_prime = P_tip_G - com_total_G

    # Position vector of P_tip relative to origin of {O}, expressed in {O} components
    P_tip_origin_in_O = R_G_prime_to_O @ P_tip_G_prime

    # Orientation of Tip Frame {F_tip} is assumed to be aligned with Object Frame {O}
    R_Ftip_in_O_obj = np.eye(3)

    T_tip_in_obj = np.eye(4)
    T_tip_in_obj[0:3, 0:3] = R_Ftip_in_O_obj
    T_tip_in_obj[0:3, 3] = P_tip_origin_in_O
    
    return inertia_matrix_obj, T_grasp_in_obj, T_tip_in_obj

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


def copy_object(source:str, destinations:list, object_name:str, from_arm="left",to_arm="same"):
    def _send_object(destination, port, obj):
        print(destination, ": ", call_method(destination,port,"set_object",obj))
    if destinations == "all":
        destinations = get_ips(modules)
        if source in destinations:
            destinations.remove(source)
    obj = None
    if from_arm == "left":
        obj = call_method(source,12000,"download_object_context",{"object":object_name})["result"]["context"]
    else:
        obj = call_method(source,13000,"download_object_context",{"object":object_name})["result"]["context"]
    
    obj["name"] = object_name
    obj["object"] = object_name
    pprint.pprint(obj)
    threads = []
    for destination in destinations:
        if to_arm == "same":
            to_arm = from_arm
        if to_arm == "left":
            threads.append(Thread(target=_send_object, args=(destination, 12000, obj)))
        else:
            threads.append(Thread(target=_send_object, args=(destination, 13000, obj)))
        threads[-1].start()
    for t in threads:
        t.join()

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

def move(robot, location, offset = [0,0,0], port=12000, wait = True,f_ext = [10,5], add_nullspace=False):
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
    if add_nullspace:
        context["control"]["nullspace"] = {
                                                    "K_theta": [20, 20, 15, 10, 7, 5, 2],
                                                    "xi_theta": [0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7],
                                                    "active": True
                                                    }
    t = Task(robot, port=port)
    t.add_skill("move", "TaxMove", context)
    t.start()
    if wait:
        return t.wait()

    #print("Result: " + str(result))

def init_position(robot):
    import math
    # move robot to start position
    M_PI_2 = math.pi / 2
    M_PI_4 = math.pi / 4
    initial_joint_pose = [0, -M_PI_4, 0, -3 * M_PI_4, 0, M_PI_2, M_PI_4]
    return start_task(robot, "MoveToJointPose", parameters={"parameters": {"q_g": initial_joint_pose, "pose":"NoneObject"}})


def move_joint(robot, location, port=12000, offset=[0,0,0,0,0,0,0], wait=True, speed = [], q_g=[],F_ext=[50,50]):
    path_to_default_context = os.getcwd() + "/taxonomy/default_contexts/"
    f = open(path_to_default_context + "move_joint.json")
    move_context = json.load(f)
    print(move_context)
    if not q_g:
        move_context["skill"]["objects"]["goal_pose"] = location
        move_context["skill"]["q_g_offset"] = offset
    else:
        #move_context["skill"].pop("objects")
        move_context["skill"]["q_g"] = q_g
        move_context["skill"]["objects"].pop("goal_pose")

    move_context["skill"]["time_max"] = 10
    move_context["user"]["env_X"] = [0.0001, 0.0001, 0.0001, 0.0001, 0.0001, 0.0001]
    move_context["user"]["F_ext_max"] = F_ext
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

def move_some(robots:list, pose, robot_arm="all"):
    threads = []
    for host in robots:
        if robot_arm == "all" or robot_arm == "left":
            threads.append(Thread(target=move_joint, args=(host, pose, 12000, True)))
            threads[-1].start()
        if robot_arm == "all" or robot_arm == "right":    
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


def lltest(robot_ip = "neuro-robot-pc.rsi.ei.tum.de"):
    #robot_ip = copy.deepcopy(get_ips([module]))[0]
    own_ip = "172.24.206.220"
    own_ip = "10.0.2.19"
    move_joint(robot_ip, "test")
    current_state = get_current_percept(robot_ip, own_ip, 12345,["tau"])["tau"]
    llInterface_context = {
        "skill": {
            "ip_dst": own_ip,  # IP to send answers to
            "port_dst": 8888,  # port to send answers to
            "port_src": 8888,  # receiving port
            "LLInterface_mode": "Twist",  #"Torque", #CartPose  Torque  JointPose
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
    current_q = get_current_percept(robot_ip, own_ip, 12345,["q"])["q"]
    call_method(robot_ip,12000,"post_event",{"name":"handshake","content":{"q_init":current_q}})
    current_q = get_current_percept(robot_ip, own_ip, 12345,["O_dX_EE"])["O_dX_EE"]
    result, addr = udp_receive_message(own_ip, 8888)
    print("handshake: ", result)
    udp_send_message(addr[0], addr[1], {"result":True})
    increase_angle = True
    counter = 0
    print(current_q)
    try:
        while True:
            if increase_angle:
                current_q[-1] += 0.05
            else:
                current_q[-1] -= 0.05
            if current_q[-1] > 0.5 and increase_angle:
                increase_angle = False
            if current_q[-1] < -0.5 and not increase_angle:
                increase_angle = True
            #current_state[0] = 0.05
            print(current_q)
            udp_send_message_teleformat(robot_ip, 8888, current_q, counter=counter)
            
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("stop sending...")
        call_method(robot_ip,12000,"stop_task")
    #except:
    #    call_method(robot_ip,12000,"stop_task")
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
    #print("here")
    sock = socket.socket(socket.AF_INET, # Internet
                        socket.SOCK_DGRAM) # UDP
    format = "<6b"+str(len(payload))+"f4b"  # 127,127,127,127,package counter, payload size, payload (4 bytes/value), 126,126,126,126
    message = struct.pack(format, 127,127,127,127, counter, len(payload)*4,*payload, 126,126,126,126)
    #print(message)
    sock.sendto(message, (ip, port))

def udp_send_message(ip, port, message):
    print("udp_send_message to ",ip, port, "\n",message)
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
                if "status" in result["result"]:
                    if result["result"]["status"] == "Idle":
                        print(host," -left- everything is good.")
                    elif result["result"]["status"] == "Reflex":
                        print(host," -left- Non-upright-mounting Reflex.")
                    else:
                        print(host, " -left- unknown status")
                else:
                    print("No key \"status\" in get_state result")
            else:
                print(host, " -left- Not in IdleTask")
        else:
            print(host, " -left- Not reachable!")

        # result = call_method(host,13000,"get_state")
        # if result is not None:
        #     if result["result"]["current_task"] == "IdleTask":
        #         if "status" in result["result"]:
        #             if result["result"]["status"] == "Idle":
        #                 print(host," -right- everything is good.")
        #             elif result["result"]["status"] == "Reflex":
        #                 print(host," -right- Non-upright-mounting Reflex.")
        #             else:
        #                 print(host, " -right- unknown status")
        #         else:
        #             print("No key \"status\" in get_state result")
        #     else:
        #         print(host, " -right- Not in IdleTask")
        # else:
        #     print(host, " -right- Not reachable!")


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
        #"user": {"F_ext_max": [100, 50]}
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
    for m in []:  #skip some modules
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
    call_method(robot, 12000, "teach_object",{"object":insertable, "teach_width":True})
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


def xmas_reset():
    move("collective-040.rsi.ei.tum.de","t0",port=13000,wait=False)
    move("0.0.0.0","t0")

def xmas_move_2():
    move("collective-040.rsi.ei.tum.de","t3",port=13000,wait=False,add_nullspace=True,f_ext=[25,25])
    move("0.0.0.0","t3",add_nullspace=True,f_ext=[25,25])

def xmas_move():
    move("collective-040.rsi.ei.tum.de","t1",port=13000,f_ext=[25,25],wait=False,add_nullspace=True)
    move("0.0.0.0","t1",f_ext=[25,25],add_nullspace=True)
    
    pi=3.1415
    wiggle_contextl = {
        "skill": {
            "dX_fourier_a_a": [0.1, 0, 0.1, 0, 0, 0],
            "dX_fourier_a_phi": [pi/2, pi/2, 0, pi/2, 0, 0],
            "dX_fourier_a_f": [-0.12, -0.08, -0.12, 0.6125, 0, 0],
            "dX_fourier_b_a": [0, 0, 0, 0, 0, 0],
            "dX_fourier_b_f": [0, 0, 0, 0, 0, 0],
            "use_EE": True,
            "time_max": 10
        },
        "control": {
            "control_mode": 0
        }
    }
    wiggle_contextr = {
        "skill": {
            "dX_fourier_a_a": [-0.1, -0, -0.1, 0, 0, 0],
            "dX_fourier_a_phi": [pi/2, pi/2, 0, pi/2, 0, 0],
            "dX_fourier_a_f": [-0.12, -0.08, -0.12, 0.6125, 0, 0],
            "dX_fourier_b_a": [0, 0, 0, 0, 0, 0],
            "dX_fourier_b_f": [0, 0, 0, 0, 0, 0],
            "use_EE": True,
            "time_max": 10
        },
        "control": {
            "control_mode": 0
        }
    }

    tr = Task("collective-040.rsi.ei.tum.de",13000)
    tr.add_skill("wiggle", "GenericWiggleMotion", wiggle_contextr)
    tl = Task("0.0.0.0",12000)
    tl.add_skill("wiggle", "GenericWiggleMotion", wiggle_contextl)

    tr.start()
    tl.start()
    tr.wait()
    tl.wait()


def handguiding(robot):
    context = {
        "skill": {
            "record_trajectory": False,
            #"recording_length": 1,
            #"recording_name": None,
            
        },
        "control": {
            "control_mode": 0
        }
    }
    t = Task(robot)
    t.add_skill("record_trajectory", "HandGuiding", context)
    t.start()
    input("stop now?")
    result = t.stop()
    print("Result: " + str(result))
   
