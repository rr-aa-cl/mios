import json
from math import dist
import os
from unittest.util import _count_diff_all_purpose
import numpy as np
import time

import socket
from utils.ws_client import call_method
from mongodb_client.mongodb_client import MongoDBClient
from utils.taxonomy_utils import Task


def get_ip(hostname: str):
    print("hostname: ",hostname)
    return socket.gethostbyname(hostname)

def delete_experiment_data(robots: list, tags: list, task_class: str ="insertion", db: str ="ml_results", min_size: int =0):
    for robot in robots:
        mongo_client = MongoDBClient(robot)
        documents = mongo_client.read(db, task_class, {"meta.tags":tags})
        if len(documents) == 0:
            print("Not found documents on ", robot)
        ids = []
        for d in documents:
            if len(d) > min_size:
                ids.append(d["_id"])
        
        for id in ids:
            mongo_client.remove(db, task_class, {"_id":id})

def move(robot, location, offset, port=12000, wait = True):
    context = {
        "skill": {
            "p0":{
                "dX_d": [0.1, 0.5],
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
            "control_mode": 2
        }
    }
    t = Task(robot, port=port)
    t.add_skill("move", "TaxMove", context)
    t.start()
    if wait:
        return t.wait()

    #print("Result: " + str(result))

def move_joint(robot, location,port=12000, wait=True):
    path_to_default_context = os.getcwd() + "/../python/taxonomy/default_contexts/"
    f = open(path_to_default_context + "move_joint.json")
    move_context = json.load(f)
    move_context["skill"]["objects"]["goal_pose"] = location
    move_context["skill"]["time_max"] = 10
    t0 = Task(robot, port=port)
    t0.add_skill("move", "MoveToPoseJoint", move_context)
    t0.start()
    if wait:
        result = t0.wait()

def check_location(robot, pose_name, port=12000):
    client = MongoDBClient(robot)
    pose_object = client.read("mios","environment",{"name":pose_name})[0]
    if not pose_object:
        return False
    cart_coordinates_g = pose_object["O_T_OB"][12:15]
    cart_coordinates_current = call_method(robot,port,"get_state")["result"]["O_T_EE"][12:15]
    cart_coordinates_current = np.array(cart_coordinates_current) + np.array(pose_object["OB_T_TCP"][12:15])
    distance = np.sqrt(np.sum((cart_coordinates_current - cart_coordinates_g)**2, axis=0))
    #print(distance)
    if distance < 0.004:  # 4mm distance is ok I guess
        return True
    else:
        return False

def place_current_insertable(robot):
    current_object = call_method(robot, 12000, "get_state")["result"]["grasped_object"]
    print(current_object)
    if current_object != "NullObject":
        place_insertable(robot, current_object, current_object+"_container", current_object+"_container_approach", current_object+"_container_above")


def place_insertable(robot, insertable="generic_insertable", container="generic_container", approach="generic_container_approach", above = None, port=12000):
    count = 0
    while True:
        if call_method(robot,port,"get_state")["result"]['grasped_object'] == 'NullObject':
            call_method(robot, port, "set_grasped_object", {"object": insertable})
        path_to_default_context = os.getcwd() + "/../python/taxonomy/default_contexts/"
        t0 = Task(robot, port=port)
        t1 = Task(robot, port=port)
        t2 = Task(robot, port=port)
        if above is None:
            move(robot, approach, [0,0,0.1],port=port)
        else:
            move_joint(robot, above, port=port)
        f = open(path_to_default_context + "insertion.json")
        insertion_context = json.load(f)
        insertion_context["skill"]["objects"]["Insertable"] = insertable
        insertion_context["skill"]["objects"]["Container"] = container
        insertion_context["skill"]["objects"]["Approach"] = approach

        insertion_context["skill"]["p2"]["search_a"]= [10, 10, 0, 2, 2, 0]
        insertion_context["skill"]["p2"]["search_f"] = [1, 0.75, 0, 1, 0.75, 0]
        if robot[:18] != "collective-dev-002":
            if insertable == "HDMI_plug" or insertable == "cylinder_50":
                insertion_context["skill"]["p2"]["f_push"] = [0, 0, 13, 0, 0, 0]
            elif insertable == "cylinder_10" or insertable == "cylinder_20" or insertable == "cylinder_30" or insertable[:3] == "key":
                insertion_context["skill"]["p2"]["f_push"] = [0, 0, 15, 0, 0, 0]
            elif insertable == "cylinder_40":
                insertion_context["skill"]["p2"]["f_push"] = [0, 0, 7, 0, 0, 0]
            elif insertable == "key_door":
                insertion_context["skill"]["p2"]["f_push"] = [0, 0, 25, 0, 0, 0]
            else:
                insertion_context["skill"]["p2"]["f_push"] = [0, 0, 20, 0, 0, 0]
        else:
            if insertable == "cylinder_10" or insertable == "cylinder_20" or insertable == "cylinder_30" or insertable[:3] == "key":
                insertion_context["skill"]["p2"]["f_push"] = [0, 0, 25, 0, 0, 0]
        insertion_context["skill"]["time_max"] = 15
        result = False
        while result == False:
            f = open(path_to_default_context + "move_joint.json")
            t0 = Task(robot)
            move_context = json.load(f)
            move_context["skill"]["objects"]["goal_pose"] = approach
            move_context["skill"]["time_max"] = 10
            t0.add_skill("move", "MoveToPoseJoint", move_context)
            t0.start()
            result = t0.wait()["result"]["task_result"]["success"]

        t1.add_skill("insertion", "TaxInsertion", insertion_context)
        t1.start()
        result = t1.wait()

        if result["result"]["task_result"]["success"] == True:
            if not call_method(robot, port, "release_object")["result"]["result"]:
                call_method(robot,port,"home_gripper")
                time.sleep(10)
            if above is None:
                move(robot, approach, [0,0,0.1], port=port)
            else:
                move_joint(robot, above, port=port)
            #call_method(robot, 12000, "home_gripper")
            return True
        else:
            if check_location(robot, insertable):
                if not call_method(robot, port, "release_object")["result"]["result"]:
                    call_method(robot,port,"home_gripper")
                    time.sleep(10)
                if above is None:
                    move(robot, approach, [0,0,0.1], port=port)
                else:
                    move_joint(robot, above, port=port)
                #call_method(robot, 12000, "home_gripper")
                return True
        if count > 10:
            break
    return False

def grasp_insertable(robot:str, insertable = "generic_insertable", container = "generic_container", approach = "generic_container_approach", above = None, port=12000):
    count = 0
    alternation = -1
    while True:
        alternation=alternation*(-1)
        #print("current object grasped: ", call_method(robot,12000,"get_state")["result"]['grasped_object'] )
        if call_method(robot,port,"get_state")["result"]['grasped_object'] == 'NullObject':
            call_method(robot, port, "release_object")
        else:
            print("I am already grasping something")
            call_method(robot, port, "release_object")
            #return 0
        if above is None:
            move(robot, approach, [0,0,0.1])
        else:
            move_joint(robot, above)
        #call_method(robot,12000,"move_gripper",{"width":0.06,"force":100,"epsilon_outer":1,"speed":100})
        call_method(robot,port,"home_gripper")
        path_to_default_context = os.getcwd() + "/../python/taxonomy/default_contexts/"
        t1 = Task(robot, port=port)
        t2 = Task(robot, port=port)
        f = open(path_to_default_context + "move_cart.json")
        move_fine_context = json.load(f)
        move_fine_context["skill"]["objects"]["GoalPose"] = insertable
        move_fine_context["skill"]["p0"]["K_x"] = [2000, 2000, 2000, 200, 200, 200]
        move_fine_context["skill"]["time_max"] = 10
        f = open(path_to_default_context + "extraction.json")
        extraction_context = json.load(f)
        extraction_context["skill"]["objects"]["Extractable"] = insertable
        extraction_context["skill"]["objects"]["Container"] = container
        extraction_context["skill"]["objects"]["ExtractTo"] = approach
        #execution
        t1.add_skill("move_fine", "TaxMove", move_fine_context)
        success_moving = False
        success_grasping = False
        grasp_count = 0
        while success_grasping == False:
            count = 0
            while success_moving == False:
                #call_method(robot, 12000, "move_gripper",{"width":0.07,"speed":1,"force":100})
                t1.start()
                success_moving = t1.wait()["result"]["task_result"]["success"]
                if not success_moving:
                    print(robot, ": moving success = ", success_moving)
                count += 1
                if count > 2:
                    break
            success_moving = False
            result = call_method(robot, port, "grasp_object", {"object": insertable}) # call_method(robot,12000,"grasp",{"width":0,"force":100,"epsilon_outer":1,"speed":100}) #
            #call_method(robot,12000,"set_grasped_object",{"object":insertable})
            if result:
                success_grasping  = result["result"]["result"]
            else:
                success_grasping = False  # return from mios is None --> waiting for mios-restart
                time.sleep(32)
                break
            if not success_grasping:
                call_method(robot, port, "move_gripper",{"width":1,"speed":1,"force":50})
                print(robot, " grasping success for ", insertable," = ", success_grasping)
            if grasp_count > 3:
                break
            grasp_count += 1
        if not success_grasping:
            continue
        result = False
        t2.add_skill("extraction", "TaxExtraction", extraction_context)
        t2.start()
        result = t2.wait()["result"]["result"]
        if not result:
            if check_location(robot, approach, port=port) and call_method(robot,port,"get_state")["result"]["grasped_object"] == insertable:
                return True
            grasping_result = call_method(robot,port,"grasp",{"width":0,"force":100,"epsilon_outer":1,"speed":100})["result"]["result"] #call_method(robot, 12000, "grasp_object", {"object": "generic_insertable"})
            call_method(robot,port,"set_grasped_object",{"object":insertable})
            if not grasping_result:
                call_method(robot,port,"home_gripper")
                move(robot, "EndEffector", [0,0,0.03])
                call_method(robot,port,"grasp",{"width":0,"force":100,"epsilon_outer":1,"speed":100})["result"]["result"]
                move(robot,"EndEffector",[0,0,-0.03])
        else:
            return True
        print("grabbing not successful: ",insertable, count)
        if count > 10:
            break
    print("abort grabbing ", insertable)
    return False
    
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

