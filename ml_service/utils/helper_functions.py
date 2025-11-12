import json
import os
import numpy as np
import time
import copy
import socket
import collections.abc
from numpy.linalg import inv
from scipy.spatial.transform import Rotation
import math

from utils.ws_client import call_method
from mongodb_client.mongodb_client import MongoDBClient
from utils.taxonomy_utils import Task
from plotting.data_acquisition import *


def get_ip(hostname: str):
    print("hostname: ",hostname)
    return socket.gethostbyname(hostname)

def udpate_dict(d,u):  # updates a dict (d) with values of dict (u) recursively
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = udpate_dict(d.get(k, {}), v)
        else:
            d[k] = v
    return d

def lowest_results(robot:str, tags:list):
    data = get_multiple_experiment_data(robot, "insertion", "ml_results", {"meta.tags":tags})
    lowerst_cost = 100
    for result in data:
        cost_tmp = result.get_lowest_cost()
        if cost_tmp != cost_tmp:  # is NaN
            print("no cost found")
            continue
        print("lowest cost of ",cost_tmp, "at index ",result.costs.index(cost_tmp))
        if lowerst_cost > cost_tmp:
            lowerst_cost = cost_tmp
    print("lowest_cost for", tags ," on ", robot,":  ",lowerst_cost)
    return lowerst_cost

def mean_results(robot:str, tags:list):
    data = get_multiple_experiment_data(robot, "insertion", "ml_results", {"meta.tags":tags})
    lowerst_cost = 100
    results = []
    for result in data:
        cost_tmp = result.get_lowest_cost()
        if cost_tmp != cost_tmp:  # is NaN
            print("no cost found")
            continue
        #print(tags, " - lowest cost of ",cost_tmp, "at index ",result.costs.index(cost_tmp))
        results.append(cost_tmp)
    return np.mean(results)

def learned_successfull(robot, tags):
    data = get_multiple_experiment_data(robot, "insertion","ml_results",{"meta.tags":tags})
    if len(data)>1:
        print("multiple results found")
    found_knoweldge = []
    for result in data:
        success = False
        if sum(result.get_successes_per_trial()) < 1:
            success = False
        else:
            if len(get_multiple_knowledge_data(robot,"insertion","local",{"meta.tags":tags}))>0:
                success = True
        found_knoweldge.append(success)
    return found_knoweldge
        

def n_trial_until(robot, tags, cutoff):
    data = get_multiple_experiment_data(robot, "insertion", "ml_results", {"meta.tags":tags})
    lowerst_cost = 100
    for result in data:
        lowest_index = float("inf")
        index_tmp = float("inf")
        for i,cost in enumerate(result.costs):
            if cost < cutoff:
                print("lower cost than ",cutoff, "at index ",i)
                index_tmp = i
                break
        if index_tmp<lowest_index:
            lowest_index = index_tmp
    return lowest_index
        

def delete_experiment_data(robots: list, tags: list, task_class: str ="insertion", db: str ="ml_results", min_size: int =0):
    for robot in robots:
        mongo_client = MongoDBClient(robot)
        try:
            documents = mongo_client.read(db, task_class, {"meta.tags":tags})
        except:
            continue
        if len(documents) == 0:
            print("Not found documents on ", robot)
        ids = []
        for d in documents:
            if len(d) > min_size:
                ids.append(d["_id"])
        for id in ids:
            mongo_client.remove(db, task_class, {"_id":id})
        

def nested_get(input_dict, nested_key):
    internal_dict_value = input_dict
    for k in nested_key:
        internal_dict_value = internal_dict_value.get(k, None)
        if internal_dict_value is None:
            return None
    return internal_dict_value

def get_nested_parameter(dic, keys):
    key_list = keys.split(".")
    parameter = key_list.pop(-1)
    parameter = parameter.split("-")
    key_list.append(parameter[0])
    if len(parameter) == 1:
        return nested_get(dic, key_list)
    if len(parameter) == 2:
        if nested_get(dic, key_list) is not None: 
            return nested_get(dic, key_list)[int(parameter[1])-1]
        else:
            return None


def set_nested_parameter(dic, keys, value):
    # logger.debug("BaseService.set_nested_parameter(dic: " + str(dic) + ", " + "keys: " + str(keys) + ")")
    for key in keys[:-1]:
        dic = dic.setdefault(key, {})
    tmp = keys[-1].split("-")
    if len(tmp) == 1:
        dic[keys[-1]] = value
    elif len(tmp) == 2:
        p_name = tmp[0]
        p_dim = int(tmp[1])
        if p_name not in dic:
            dic[p_name] = []
        if len(dic[p_name]) < p_dim:
            dic[p_name].extend([0] * (p_dim - len(dic[p_name])))
        dic[p_name][p_dim - 1] = value

def move(robot, location, offset = [0,0,0], port=12000, wait = True,speed=False, log_name="CartMove",context="Move to cartesian pose",folder="",logging=True):
    try:
        o = call_method(robot,port,"download_object_context",{"object":location})["result"]["context"]["O_T_OB"]
    except KeyError:
        print("Object "+location," not existent on "+robot)
        return False
    context = {
        "skill": {
            "p0":{
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.1, 0.5],
                "K_x": [2000, 2000, 2000, 250, 250, 250],
                "T_T_EE_g_offset": [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, offset[0], offset[1], offset[2], 1],
                "T_T_EE_g":o

            },
            "time_max":10,
            "log_data":logging,
            "data_length":100000,
            "log_to_file":True,
            "log_name":folder+log_name,
            "meta":{
                    "description":context,
                    "tags":["TaxMove","CartMove",location,log_name, "offset="+str(offset)],
                    "time":time.time(),
                    "O_T_OB":o
                    },
            "objects": {
                    "GoalPose": location
                }
        },
        "control": {
            "control_mode": 2,
            "nullspace":
            {
                "K_theta": [50, 50, 50, 50, 20, 20, 20],
                "xi_theta": [0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7],
                "active": True              
            }
        },
        "user":{
            "env_X": [0.005, 0.005, 0.005, 0.0175, 0.0175, 0.0175]
        }
    }
    if speed:
        context["skill"]["p0"]["dX_d"] = [1, 2]
        context["skill"]["p0"]["ddX_d"] = [2, 2]
        context["user"]["env_X"] = [0.01, 0.01, 0.01, 0.03, 0.03, 0.03]
    
    context["skill"]["meta"]["context"] = copy.deepcopy(context)
    t = Task(robot, port=port)
    t.add_skill("move", "TaxMove", context)
    t.start()
    if wait:
        return t.wait()

    #print("Result: " + str(result))

def move_joint(robot, location,port=12000, wait=True,speed=False, log_name = "JointMove", context="Move to a joint position",folder="",logging=True):
    path_to_default_context = os.getcwd() + "/../python/taxonomy/default_contexts/"
    f = open(path_to_default_context + "move_joint.json")
    move_context = json.load(f)
    move_context["skill"]["objects"]["goal_pose"] = location
    move_context["skill"]["time_max"] = 10
    if speed:
        move_context["skill"]["speed"] = 5
        move_context["skill"]["acc"] = 2
        move_context["user"]["env_X"] = [0.005, 0.005, 0.005, 0.0175, 0.0175, 0.0175]

    #move_context["user"]["F_ext_max"] = [25,25]
    move_context["user"]["tau_ext_max"] = [40,40,40,40,8,8,8]
    move_context["skill"]["time_max"] = 7.2
    move_context["skill"]["scaling_divisor"] = 1
    move_context["skill"]["log_data"] = logging
    move_context["skill"]["log_name"] = folder+log_name
    move_context["skill"]["log_to_file"] = True
    try:
        o = call_method(robot,port,"download_object_context",{"object":location})["result"]["context"]["q"]
    except KeyError:
        print("Object "+location," not existent on "+robot)
        return False
    move_context["skill"]["meta"] = {
                                    "description":context,
                                    "tags":["MoveToPoseJoint","JointMove",location,log_name],
                                    "time":time.time(),
                                    "q_d":o
                                    }
    move_context["skill"]["meta"]["context"] = copy.deepcopy(move_context)
    t0 = Task(robot, port=port)
    t0.add_skill("move", "MoveToPoseJoint", move_context)
    t0.start()
    if wait:
        return t0.wait()

def check_location(robot, pose_name, port=12000,precision=0.004,offset = [0,0,0],only_z=False):
    client = MongoDBClient(robot)
    try:
        pose = call_method(robot, port, "download_object_context",{"object":pose_name})
        pose_object = pose["result"]["context"]
    except KeyError:
        print("cannot download object context: "+pose_name)
        return False
    except TypeError:
        print("cannot download object context: "+pose_name)
        return False
    if only_z:
        cart_coordinates_g = pose_object["O_T_OB"][12]
        cart_coordinates_g = cart_coordinates_g+ offset[0]
        cart_coordinates_current = call_method(robot,port,"get_state")["result"]["O_T_EE"][12]
        cart_coordinates_current = np.array(cart_coordinates_current)
    else:
        cart_coordinates_g = pose_object["O_T_OB"][12:15]
        cart_coordinates_g = [x+off for x,off in zip(cart_coordinates_g,offset)]
        cart_coordinates_current = call_method(robot,port,"get_state")["result"]["O_T_EE"][12:15]
        cart_coordinates_current = np.array(cart_coordinates_current)
   # cart_coordinates_current = np.array(cart_coordinates_current) + np.array(pose_object["OB_T_TCP"][12:15])
    distance = np.sqrt(np.sum((cart_coordinates_current - cart_coordinates_g)**2, axis=0))
    if distance < precision:
        return True
    else:
        logger.debug("check_location: Distance "+str(distance)+ ">"+str(precision))
        print("check_location: Distance "+str(distance)+ ">"+str(precision))
        return False

def place_current_insertable(robot):
    current_object = call_method(robot, 12000, "get_state")["result"]["grasped_object"]
    print(current_object)
    if current_object != "NullObject":
        place_insertable(robot, current_object, current_object+"_container", current_object+"_container_approach", current_object+"_container_above")


def place_insertable(robot, insertable="generic_insertable", container="generic_container", approach="generic_container_approach", above = None, port=12000,folder="",precision=0.002,max_time=False):
    t_0=time.time()
    if above:
        try:
            if not move_joint(robot,above,port=port,logging=False)["result"]["task_result"]["success"]:
                move(robot, "EndEffector",[-0.15],logging=False)
            if not move_joint(robot,above,port=port,logging=False)["result"]["task_result"]["success"]:
                print("cannot move to above pose with grasped object")
        except:
            pass
    path_to_default_context = os.getcwd() + "/../python/taxonomy/default_contexts/"
    f = open(path_to_default_context + "insertion.json")
    insertion_context = json.load(f)
    insertion_context["skill"]["objects"]["Insertable"] = insertable
    insertion_context["skill"]["objects"]["Container"] = container
    insertion_context["skill"]["objects"]["Approach"] = approach

    insertion_context["skill"]["p2"]["search_a"]= [8, 8, 0, 1.2, 1.2, 0]
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
    insertion_context["skill"]["time_max"] = 7.2
    insertion_context["skill"]["scaling_divisor"] = 4
    insertion_context["skill"]["log_data"] = True
    insertion_context["skill"]["log_name"] = folder+"Insertion"
    insertion_context["skill"]["log_to_file"] = True
    #o = call_method(robot,port,"download_object_context",{"object":location})["result"]["context"]["q"]
    insertion_context["skill"]["meta"] = {
                                "description":"Inserting object "+insertable+" to container "+container,
                                "tags":["Insertion",insertable,container],
                                "time":time.time()
                                }
    insertion_context["user"]["env_X"] = [0.007, 0.007, 0.002, 0.0175, 0.0175, 0.0175]
    insertion_context["user"]["F_ext_max"] = [100,50]
    low_force=set(["usb-c_1","trrs-6.35mm_aluminum_rod"])
    high_force=set(["cylinder_60_1"])
    count = 0
    while True:
        if max_time:
            if time.time()-t_0 >= max_time:
                print("exiting grasping function because of time")
                return False
        #if call_method(robot,port,"get_state")["result"]['grasped_object'] == 'NullObject':
        #    call_method(robot, port, "set_grasped_object", {"object": insertable})
        t0 = Task(robot, port=port)
        t1 = Task(robot, port=port)
        t2 = Task(robot, port=port)
        result = False
        while result == False:
            if max_time:
                if time.time()-t_0 >= max_time:
                    print("exiting grasping function because of time")
                    return False
            f = open(path_to_default_context + "move_joint.json")
            t0 = Task(robot,port=port)
            move_context = json.load(f)
            move_context["skill"]["objects"]["goal_pose"] = approach
            move_context["skill"]["time_max"] = 5
            move_context["skill"]["log_data"] = True
            move_context["skill"]["log_to_file"] = True
            move_context["skill"]["log_name"] = folder+"Move_to_approach"
            move_context["skill"]["meta"] = {
                "description":"Moving to a joint position above the "+insertable+"'s container in order to place it.",
                "tags":["MoveToPoseJoint",approach,"approach_pose","placing",insertable],
                "time":time.time()
            }
            t0.add_skill("move", "MoveToPoseJoint", move_context)
            t0.context["skills"]["move"]["skill"]["meta"]["time"] = time.time()
            status = call_method(robot,port,"get_state")["result"]
            if "status" not in status:
                if "current_task" != "IdleTask":
                    #call_method(robot,port, "release_object")
                    call_method(robot,port, "unlock_brakes")
                    time.sleep(10)
                    logger.error("Hit the breaks when placing object. -> UNSUCCESSFUL")
                    return False
            print("move fine")
            t0.start()
            result = t0.wait()["result"]["task_result"]["success"]
            t0.context["skills"]["move"]["skill"]["log_name"]=folder+"Move_to_approach2"
            t0.context["skills"]["move"]["skill"]["meta"]["description"]="Assure moving to a joint position above the "+insertable+"'s container was done with precision in order to place it."
            t0.context["skills"]["move"]["skill"]["meta"]["time"] = time.time()
            t0.start()
            #result = t0.wait()["result"]["task_result"]["success"]
            #t0.context["skills"]["move"]["skill"]["log_name"]=folder+"move_to_approach3"
            #t0.context["skills"]["move"]["skill"]["meta"]["description"]="Assure moving to a joint position above the "+insertable+"'s container was done with precision in order to place it."
            #t0.context["skills"]["move"]["skill"]["meta"]["time"] = time.time()
            #t0.start()
            result = t0.wait()["result"]["task_result"]["success"]
            if call_method(robot, port, "get_state")["result"]["grasped_object"] != insertable:
                return True
        print("place insertable ",insertable)
        t1.add_skill("insertion", "TaxInsertion", insertion_context)
        t1.context["skills"]["insertion"]["skill"]["meta"]["time"] = time.time()
        t1.start()
        result = t1.wait()
        print(result)
        if call_method(robot, port, "get_state")["result"]["grasped_object"] != insertable:
            return True

        o = call_method(robot, port, "download_object_context",{"object":insertable})["result"]["context"]
        precision= 0.003
        if o["mass"] > 0.5:
            print("increase allowd precision error from ",precision, "to 0.005")
            precision = 0.005
        

        if result["result"]["task_result"]["success"] == True and check_location(robot, container,port=port,precision=precision, only_z=True):
            print("successfull insertion of ",insertable, ". Releasing...")
            if not hold_release(robot,port,grasping_pos=insertable,folder=folder):
                print("releasing didn\'t work. Try homing...")
                call_method(robot,port,"home_gripper")
                time.sleep(10)
            # print("move to above pose")
            if above:
                move(robot, above, port=port,context="Move to a pose above the object "+insertable+" after successfully placing it into the object container.",folder=folder,log_name=insertable+"_above")
            else:
                move(robot, approach, [0.1,0,0], port=port,context="Move 10 cm above the object "+insertable+" after successfully placing it into the object container.",folder=folder,log_name=insertable+"_above")
            #call_method(robot, port, "home_gripper")
            return True
        else:
            print("unsuccessfull insertion. Check loctation...")
            if check_location(robot, container,port, precision=precision):
                print("seems like insertion was successfull.")
                if not hold_release(robot,port, folder=folder,grasping_pos=insertable):
                    call_method(robot,port,"home_gripper")
                    time.sleep(10)
                if above is None:
                    move(robot, approach, [0.1,0,0], port=port,context="Move 10 cm above the object "+insertable+" after successfully placing it into the object container.",folder=folder,log_name=insertable+"_above")
                else:
                    move(robot, above, port=port,context="Move to a pose above the object "+insertable+" after successfully placing it into the object container.",folder=folder,log_name=insertable+"_above")
                #call_method(robot, port, "home_gripper")
                return True
            else:  # insertion didn't work:
                if insertion_context["skill"]["p2"]["f_push"][2] > 44:  #more than 44 Newton Force
                    if insertable in high_force:
                        pass
                    else:
                        print("Cannot insert the object")
                        hold_release(robot,port, folder=folder,grasping_pos=insertable)
                        return False
                if insertable in low_force:
                    print("Cannot insert ",insertable," with high forces.")
                    hold_release(robot,port, folder=folder,grasping_pos=insertable)
                    return False
                print("insertion did not work. Try again with more force...")
                print("extract")
                extract(robot,insertable,approach,container,port=port,logging=False)
                print("move to approach")
                move(robot, approach,logging=False,port=port)
                print("for next try to place object use more force and less wiggle...")
                insertion_context["skill"]["p2"]["f_push"][2] += 10
                insertion_context["skill"]["p2"]["search_a"]= [x*0.5 for x in insertion_context["skill"]["p2"]["search_a"]]

        if count > 10:
            break
    hold_release(robot,port, folder=folder,grasping_pos=insertable)
    return False

def grasp_insertable(robot:str, insertable = "generic_insertable", container = "generic_container", approach = "generic_container_approach", above = None, port=12000, context="",folder="",max_time = False):
    t_0=time.time()
    z_offset = 0
    path_to_default_context = os.getcwd() + "/../python/taxonomy/default_contexts/"
    t1 = Task(robot, port=port)
    t2 = Task(robot, port=port)
    f = open(path_to_default_context + "move_cart.json")
    move_fine_context = json.load(f)
    move_fine_context["skill"]["objects"]["GoalPose"] = insertable
    move_fine_context["skill"]["p0"]["K_x"] = [2000, 2000, 2000, 200, 200, 200]
    move_fine_context["skill"]["p0"]["dX_d"] =  [0.05, 0.2]
    move_fine_context["skill"]["p0"]["ddX_d"] = [0.02, 0.05]
    #move_fine_context["skill"]["time_max"] = 10
    move_fine_context["skill"]["time_max"] = 7.2
    move_fine_context["skill"]["scaling_divisor"] = 1
    move_fine_context["skill"]["log_data"] = True
    move_fine_context["skill"]["log_to_file"] = True
    move_fine_context["skill"]["log_name"] = folder+"MoveFine"
    move_fine_context["skill"]["meta"] = { 
                                "description":"Move to a exact posiotion for grasping "+insertable+" from "+container+ ".  Offset in vertical direction: "+str(z_offset)+". "+context,
                                "tags":["MoveFine",container,insertable],
                                "time":time.time()
                                }
    move_fine_context["user"]["env_X"] = [0.002, 0.002, 0.002, 0.01, 0.01, 0.01]
    move_fine_context["control"]["cart_imp"] = {}
    move_fine_context["control"]["cart_imp"]["K_x"] = [10,10,1000,100,100,100]


    
    f = open(path_to_default_context + "extraction.json")
    extraction_context = json.load(f)
    extraction_context["skill"]["objects"]["Extractable"] = insertable
    extraction_context["skill"]["objects"]["Container"] = container
    extraction_context["skill"]["objects"]["ExtractTo"] = approach
    extraction_context["skill"]["time_max"] = 7.2
    extraction_context["skill"]["scaling_divisor"] = 1
    extraction_context["skill"]["log_data"] = True
    extraction_context["skill"]["log_to_file"] = True
    extraction_context["skill"]["log_name"] = folder+"Extraction"
    extraction_context["skill"]["meta"] = {
                                "description":"Extracting "+insertable+" from "+container+ " to a position slighly above the container."+context,
                                "tags":["Extraction",container,insertable]
                                }
    extraction_context["user"]["env_X"] = [0.003, 0.003, 0.001, 0.0175, 0.0175, 0.0175]

    count = 0
    alternation = 1
    
    while True:
        if max_time:
            if time.time()-t_0 >= max_time:
                print("exiting grasping function because of time")
                return False
        success_moving = False
        success_grasping = False
        grasp_count = 0
    
        alternation=alternation*(-1)
        ## print("current object grasped: ", call_method(robot,port,"get_state")["result"]['grasped_object'] )
        grasped_object = call_method(robot,port,"get_state")["result"]['grasped_object']
        if grasped_object == insertable:
            # print("object is already grasped")
            if not check_location(robot, container, port, precision=0.006,offset=[z_offset,0,0]): # not in container -> done
                print("Object already grasped")
                logger.debug("Object already grasped")
                if above:
                    if move(robot, above, port=port,logging=False):
                        return True
                else:
                    if move(robot,insertable,[0,0,0.1],port=port,logging=False):
                        return True
                return True
            else: #grasped but still in container
                # print("skipping grasping.")
                success_grasping = True
        elif grasped_object != 'NullObject':
            # print("I am already grasping something")
            call_method(robot, port, "release_object")
        else:
            pass
            # print("grasping ",insertable)
            #return 0
        if above is None:
            print("move 10cm up")
            logger.debug("grasp_insertable: move 10cm up")
            move(robot, approach, [0.1,0,0],port=port,context="Move 10 cm above the object "+insertable+" in context of grasping.",folder=folder,log_name=insertable+"_above_before")
        else:
            move_joint(robot, above, port=port,context="Move to a joint pose above object "+insertable+" in context of grasping.",folder=folder,log_name=insertable+"_above_before")
        #call_method(robot,port,"move_gripper",{"width":0.06,"force":100,"epsilon_outer":1,"speed":100})
        if not success_grasping:
            print("home_gripper1")
            call_method(robot,port,"home_gripper")
            call_method(robot,port,"release_object")
        #execution
        t1.add_skill("move_fine", "TaxMove", move_fine_context)
        grasp_width = call_method(robot,port,"download_object_context",{"object":insertable})["result"]["context"]["grasp_width"]
        print("success_grasping=",success_grasping)
        t_0 = time.time()
        while success_grasping == False:
            if max_time:
                if time.time()-t_0 >= max_time:
                    print("exiting grasping function because of time")
                    return False

            count = 0
            if time.time()-t_0 > 90:
                return False
            while success_moving == False:
                if max_time:
                    if time.time()-t_0 >= max_time:
                        print("exiting grasping function because of time")
                        return False
                #call_method(robot, port, "move_gripper",{"width":0.07,"speed":1,"force":100}
                t1.context["skills"]["move_fine"]["skill"]["meta"]["time"] = time.time()
                t1.start()
                # print("move_fine started")
                #success_moving = move_joint(robot,insertable, wait=True)["result"]["task_result"]["success"]
                try:
                    success_moving = t1.wait()["result"]["task_result"]["success"]
                except KeyError:
                    success_moving = False
                if time.time() - t_0 > 60:
                    success_moving=True 
                if not success_moving:
                    pass
                    # print(robot, ": moving success = ", success_moving)
                count += 1
                if count > 2:
                    # print("movement count: ",count)
                    break
            if not success_moving:
                # print("skip movement loop. Move above...")
                if above is None:
                    move(robot, approach, [0,0,0.1],port=port,context="Move 10 cm above the object "+insertable+" after grasping failed in order to home the gripper and try again.",folder=folder,log_name="retract_cart")
                else:
                    move(robot, above,port=port, context="Direct move to a pose above the object "+insertable+" after grasping failed in order to move out of the objects area.",folder=folder,log_name="retract_cart")
                    move_joint(robot,above,port=port,context="Move to a joint pose above the object "+insertable+" after grasping failed in order to home the gripper and try again.",folder=folder,log_name="retract_joint")
                print("home_gripper2")
                call_method(robot,port,"home_gripper")
                continue
            success_moving = False
            #move_joint(robot,insertable, wait=True)  #just for presicion
            if not check_location(robot,insertable,port,precision=0.0035,offset=[z_offset,0,0]) and time.time()-t_0<65:
                print("change move fine context")
                move_fine_context["control"]["cart_imp"]["K_x"] = [3000, 3000, 3000, 200, 200, 200]
                move_fine_context["skill"]["meta"]["time"] = time.time()
                t1 = Task(robot,port=port)
                t1.add_skill("move_fine","TaxMove",move_fine_context)
                t1.context["skills"]["move_fine"]["skill"]["meta"]["time"] = time.time()
                t1.start()
                result = t1.wait()["result"]["task_result"]["success"]
                if result:
                    success_moving = True
                # t1 = Task(robot,port=port)
                # t1.add_skill("move_fine","TaxMove",move_fine_context)
                # t1.context["skills"]["move_fine"]["skill"]["meta"]["time"] = time.time()
                # t1.start()
                # t1.wait()
                if not check_location(robot,insertable,port,precision=0.055,offset=[z_offset,0,0]):
                    logger.error("moving to grasping position failed")
                    success_moving = False
                    continue
            else:
                logger.debug("success moving to exact grasping position")
                success_moving=True
            
            #result = hold_grasp(robot,insertable, port=port)
            #success_grasping = wiggle_grasp(robot,insertable, port=port)
            tight_grasp_width = grasp_width-0.005
            if tight_grasp_width < 0:
                tight_grasp_width = 0
            if not call_method(robot,port,"grasp",{"speed":0.05,"force":100,"width":tight_grasp_width, "epsilon_outer":1,"epsilon_inner":1})["result"]["result"]:
                print("grasping not successfull, home gripper 3, move above, home_gripper4")
                call_method(robot,port,"home_gripper")
                move(robot,above,port=port,logging=False)
                move_joint(robot,above,port=port,logging=False)
                call_method(robot,port,"home_gripper")
                success_grasping=False
                success_moving=False
                continue
            result = True
            current_width = gripper_width(robot,port)
            if current_width > grasp_width+0.001:
                print("cannot close gripper: current_width:",current_width, " grasp_width",grasp_width)
                result = False
            if current_width < grasp_width-0.001:
                print("cannot find object: current_width:",current_width, " grasp_width",grasp_width)
                result = False
            if result:
                print("open and close gripper")
                call_method(robot,port,"move_gripper",{"speed":0.05,"force":100,"width":grasp_width+0.001})
                grasp=call_method(robot,port,"grasp",{"speed":0.05,"force":100,"width":0,"epsilon_outer":1})
                print("grasping again",grasp)
                call_method(robot,port,"set_grasped_object",{"object":insertable})
                success_grasping = True

            # #call_method(robot,12000,"set_grasped_object",{"object":insertable})
            # if not success_grasping:
            #     print("grasping was unsuccessfull. Moving to above")
            #     success_grasping = False 
            #     if above:
            #         move(robot, above,port=port)
            #     else:
            #         move(robot,insertable,[0,0,0.1],port=port)
            #     break
            if not success_grasping:
                hold_release(robot,port,grasping_pos=insertable,folder=folder)
                # print(robot, " grasping success for ", insertable," = ", success_grasping)
            else:
                break # successfull grasped :)
            if grasp_count > 1:
                # print("tried over 3 times. break out of loop")
                break
            grasp_count += 1

        
        if not success_grasping:
            print("modify grasping pose slightly")
            z_offset +=0.001
            z_offset = z_offset*alternation
            move_fine_context["skill"]["p0"]["T_T_EE_g_offset"] =  [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, z_offset, 0, 0, 1]
            move_fine_context["skill"]["meta"] = {
                                "description":"Move to a exact posiotion for grasping "+insertable+" from "+container+ ".  Offset in vertical direction: "+str(z_offset)+". "+context,
                                "tags":["MoveFine",container,insertable],
                                "time":time.time()
                                }
            continue
        #input("wait")
        #call_method(robot,12000,"grasp",{"width":0,"force":100,"epsilon_outer":1,"speed":100}) #
        #call_method(robot,12000,"set_grasped_object",{"object":insertable})
        # print("start extracting...")
        result = False
        t2.add_skill("extraction", "TaxExtraction", extraction_context)
        t2.context["skills"]["extraction"]["skill"]["meta"]["time"] = time.time()
        t2.start()
        result = t2.wait()["result"]["result"]
        if not result:
            # print("extraction not successful: check location")
            if check_location(robot, approach, port=port,precision=0.004) and call_method(robot,port,"get_state")["result"]["grasped_object"] == insertable:
                # print("seems like an successful extraction")
                call_method(robot,port,"set_grasped_object",{"object":insertable})
                return True
            if above:
                if not move(robot, above, port=port,logging=False):
                    return False
            else:
                if not move(robot,insertable,[0,0,0.1],port=port,logging=False):
                    return False
        else:
            if above:
                move(robot, above, port=port,logging=False)
            else:
                move(robot,insertable,[0,0,0.1],port=port,logging=False)
            if not check_location(robot, approach, port=port,precision=0.002):  # not fully extracted
                print("no full extraction")
            else:
                print("successfull extraction")
                call_method(robot,port,"set_grasped_object",{"object":insertable})
                return True
        print("extraction not successful: ",insertable, count)
        if count > 10:
            break
    # print("abort grabbing ", insertable)
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

def wiggle_release(robot,port=12000):
    current_object = None
    gripper_width = None
    try:
        result = call_method(robot,port,"get_state")["result"]
        current_object = result["grasped_object"]
        gripper_width = result["gripper_width"]
    except (KeyError, TypeError):
        gripper_width = 1
        print("set gripper width to ", gripper_width)
        pass
    wiggle_contextx = {
        "skill": {
            "dX_fourier_a_a": [-0, -0, -0, 0, 0.04, 0],
            "dX_fourier_a_phi": [0, 0, 0, 0, 0, 0],
            "dX_fourier_a_f": [0, -0, -0, 0, 2, 0],
            "dX_fourier_b_a": [0, 0, 0, 0, 0, 0],
            "dX_fourier_b_f": [0, 0, 0, 0, 0, 0],
            "use_EE": True,
            "time_max": 7.2,
            "log_data":False,
            "data_length":10000,
            "log_name":"release_object",
            "log_to_file": True, 
            "meta":{
                "description":"Release objec with a slight wiggle motion to help sliding the object's nipples into the gripper finger holes.",
                "tags":["wiggle","GenericWiggleMotion","release"],
                "time":time.time()
                },
        },
        "control": {
            "control_mode": 0,
            "cart_imp": {
                "K_x": [2000, 2000, 2000, 250, 25, 250]
            }
        }
    }
    tr = Task(robot,port)
    tr.add_skill("wigglex", "GenericWiggleMotion", wiggle_contextx)
    tr.start(queue=False)
    if call_method(robot,port,"move_gripper",{"speed":0.05,"force":100,"width":gripper_width+0.04})["result"]["result"]:
        call_method(robot, port, "stop_task")
    
    call_method(robot,port,"release_object",{"speed":0.1,"width":gripper_width+0.05})
    try: 
        print("Press <crl+c> for stopping.")
        tr.wait()
    except KeyboardInterrupt:
        call_method(robot, port, "stop_task")

def hold_release(robot,port=12000,control="cart",folder="",grasping_pos="EndEffector"):
    print("hold release")
    # moves to grasping position before object is releases -> object transformations are still active
    just_move = False
    grasped_object = "unknown"
    try:
        result = call_method(robot,port,"get_state")["result"]
        grasped_object= result["grasped_object"]
        
        if grasped_object == "NullObject":
            print("No grasping anything. Just open gripper...")
            just_move = True
    except (KeyError, TypeError):
        return True
    hold_context = {
        "skill": {
            "t_max": 3,
            "scaling_divisor":1,
            "log_data":True,
            "log_to_file":True,
            "log_name":folder+"HoldRelease",
            "data_length":10000,
            "meta":{
                "description":"Holding pose to release object "+grasped_object+" in the object container.",
                "tags":["HoldPose","release_object",grasped_object]
            }
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
                                        "K_x": [3000, 3000, 3000, 200, 5, 200]
                                        }
                                    }
    t = Task(robot, port)
    t.add_skill("hold","HoldPose",hold_context)
    t.start(queue=False)
    try:
        if call_method(robot,port,"move_gripper",{"speed":0.05,"force":100,"width":1})["result"]["result"]:
            call_method(robot, port, "stop_task")
            t.wait()
            move(robot,grasping_pos,port=port,speed=True,logging=False)
            return True
        
        if call_method(robot,port,"release_object",{"speed":0.1,"width":1})["result"]["result"]:
            call_method(robot, port, "stop_task")
            t.wait()
            move(robot,grasping_pos,port=port,speed=True,logging=False)
            return True
        call_method(robot, port, "stop_task")
        t.wait()   
        return False
    except TypeError:
        hold_release(robot,port=port,control=control,folder=folder)

def hold_grasp(robot,insertable, port=12000,control="cart"):
    object_context = None
    try:
        object_context = call_method(robot,port,"download_object_context",{"object":insertable})["result"]["context"]
    except (KeyError, TypeError):
        return False
    hold_context = {
        "skill": {
            "t_max": 7,
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
                                        "K_x": [3000, 3000, 3000, 100, 100, 200]
                                        }
                                    }
    grasping_result = False
    count = 0
    t = Task(robot, port)
    t.add_skill("hold","HoldPose",hold_context)
    t.start(queue=False)
    try:
        call_method(robot,port,"grasp",{"speed":0.05,"force":100,"width":object_context["grasp_width"], "epsilon_outer":1,"epsilon_inner":1})
        result = True
        current_width = gripper_width(robot,port)
        if current_width > object_context["grasp_width"]+0.001:
            result = False
        if current_width < object_context["grasp_width"]+0.001:
            result = False
        if result:
            call_method(robot,port,"move_gripper",{"speed":0.05,"force":100,"width":object_context["grasp_width"]+0.001})
            call_method(robot,port,"grasp",{"speed":0.05,"force":100,"width":0,"epsilon_outer":1})
            call_method(robot,port,"set_grasped_object",{"object":insertable})
            call_method(robot,port, "stop_task")
            # print("grasping successful")
            t.wait()
            return result
        else:
            call_method(robot,port,"release_object")
            call_method(robot,port,"move_gripper",{"speed":0.05,"force":100,"width":1})
            call_method(robot,port, "stop_task")
            t.wait()
        
    except (KeyError, TypeError):
        call_method(robot,port,"release_object")
        call_method(robot,port,"move_gripper",{"speed":0.05,"force":100,"width":1})
        call_method(robot,port, "stop_task")
        t.wait()
        return False
    # print("grasping result unsuccessful")
    call_method(robot,port,"release_object")
    call_method(robot,port,"move_gripper",{"speed":0.05,"force":100,"width":1})
    call_method(robot,port, "stop_task")
    t.wait()
    return False
    
def wiggle_grasp(robot,insertable, port=12000,control="cart"):
    object_context = None
    try:
        object_context = call_method(robot,port,"download_object_context",{"object":insertable})["result"]["context"]
    except (KeyError, TypeError):
        return False
    wiggle_contextx = {
        "skill": {
            "dX_fourier_a_a": [-0, -0, -0, 0, 0.02, 0.01],
            "dX_fourier_a_phi": [0, 0, 0, 0, 0, 0],
            "dX_fourier_a_f": [0, -0, -0, 0, 2, 0.5],
            "dX_fourier_b_a": [0, 0, 0, 0, 0, 0],
            "dX_fourier_b_f": [0, 0, 0, 0, 0, 0],
            "use_EE": True,
            "time_max": 7.2,
            "log_data":False,
            "log_to_file":True,
            "data_length":10000,
            "log_name":"grasp_object",
            "meta":{
                "description":"Grasping object"+object_context["name"]+"with a slight wiggle motion to help sliding the object's nipples into the gripper finger holes.",
                "tags":["wiggle","GenericWiggleMotion","grasping",object_context["name"]],
                "time":time.time()
                },

        },
        "control": {
            "control_mode": 0,
            "cart_imp": {
                "K_x": [2000, 2000, 2000, 250, 25, 250]
            }
        }
    }
    grasping_result = False
    count = 0
    t = Task(robot, port)
    t.add_skill("wiggle_grasp","GenericWiggleMotion",wiggle_contextx)
    t.start(queue=False)
    try:
        call_method(robot,port,"grasp",{"speed":0.05,"force":100,"width":object_context["grasp_width"], "epsilon_outer":1,"epsilon_inner":1})
        result = True
        current_width = gripper_width(robot,port)
        if current_width > object_context["grasp_width"]+0.001:
            # print("cannot close gripper - object not grasped properly")
            result = False
        if current_width < object_context["grasp_width"]-0.001:
            # print("no object between fingers")
            result = False
        if result:  # 
            call_method(robot,port,"move_gripper",{"speed":0.05,"force":100,"width":object_context["grasp_width"]+0.001})
            call_method(robot,port,"grasp",{"speed":0.05,"force":100,"width":0,"epsilon_outer":1})
            call_method(robot,port,"set_grasped_object",{"object":insertable})
            call_method(robot,port, "stop_task")
            # print("grasping successful")
            t.wait()
            return result
        else:
            call_method(robot,port,"release_object")
            call_method(robot,port,"move_gripper",{"speed":0.05,"force":100,"width":1})
            call_method(robot,port, "stop_task")
        
    except (KeyError, TypeError):
        call_method(robot,port,"release_object")
        call_method(robot,port,"move_gripper",{"speed":0.05,"force":100,"width":1})
        call_method(robot,port, "stop_task")
        t.wait()
        return False
    # print("grasping result unsuccessful")
    call_method(robot,port,"release_object")
    call_method(robot,port,"move_gripper",{"speed":0.05,"force":100,"width":1})
    call_method(robot,port, "stop_task")
    t.wait()
    return False

def gripper_width(robot,port):
    result = call_method(robot,port,"get_state")
    if result:
        return result["result"]["gripper_width"]
    return False 
    
def extract(robot, extractable, extractTo, container, port=12000,logging=True,folder=""):
    path_to_default_context = os.getcwd() + "/../python/taxonomy/default_contexts/"
    f = open(path_to_default_context + "extraction.json")
    move_context = json.load(f)
    move_context["skill"]["objects"]["Container"] = container
    move_context["skill"]["objects"]["ExtractTo"] = extractTo
    move_context["skill"]["objects"]["Extractable"] = extractable
    move_context["skill"]["time_max"] = 10
    move_context["skill"]["log_data"] = logging
    move_context["skill"]["log_to_file"]=True
    move_context["skill"]["data_length"]=10000
    move_context["skill"]["log_name"]=folder+"extraction"
    move_context["skill"]["meta"]={
                "description":"Extracting "+extractable+".",
                "tags":["extraction","TaxExtraction",extractable],
                "time":time.time()
                }

    move_context["user"]["env_X"] = [0, 0, 1, 1, 1, 1]
    t = Task(robot, port)
    t.add_skill("extraction","TaxExtraction",move_context)
    t.start(queue=False)
    return t.wait()

def insert(robot, insertable, approach, container, deltaX =[0,0,0,0,0,0], port=12000,folder="",logging=True):
    path_to_default_context = os.getcwd() + "/../python/taxonomy/default_contexts/"
    f = open(path_to_default_context + "insertion.json")
    move_context = json.load(f)
    move_context["skill"]["p0"]["K_x"] = [3000, 3000, 3000, 300, 300, 300]
    move_context["skill"]["objects"]["Container"] = container
    move_context["skill"]["objects"]["Approach"] = approach
    move_context["skill"]["objects"]["Insertable"] = insertable
    move_context["skill"]["time_max"] = 7
    move_context["skill"]["p2"]["f_push"][2] = 25
    move_context["skill"]["p0"]["DeltaX"] = deltaX
    move_context["user"]["env_X"] = [0, 0, 1, 1, 1, 1]
    move_context["skill"]["log_data"] = logging
    move_context["skill"]["log_to_file"]=True
    move_context["skill"]["data_length"]=10000
    move_context["skill"]["log_name"]=folder+"insertion"
    move_context["skill"]["meta"]={
                "description":"Inserting "+insertable+".",
                "tags":["insertion","TaxInsertion",insertable],
                "time":time.time()
                }
    t = Task(robot, port)
    t.add_skill("insertion","TaxInsertion",move_context)
    t.start(queue=False)
    return t.wait()



def modify_object_transformations(ip, object, z_mm, y_mm=0.0, x_mm=0.0, mass=0.0,y_ang=0, inertia = [1,0,0, 0,1,0, 0,0,1],mios_port = 12000):
    # old inertia (works)  [0.00684,-0.00279,0, -0.00279,0.00709,0, 0,0,0.00731]
    # new inertia: 
    try:
        o = call_method(ip,mios_port,"download_object_context",{"object":object})["result"]["context"]
    except KeyError:
        call_method(ip,mios_port,"teach_object",{"object":object})
        o = call_method(ip,mios_port,"download_object_context",{"object":object})["result"]["context"]

    o["OB_T_TCP"] = [   np.cos(np.radians(y_ang)),   0,   -np.sin(np.radians(y_ang)),  0,  #drehung um y-achse
                        0,               1,   0,               0,
                        np.sin(np.radians(y_ang)),   0,   np.cos(np.radians(y_ang)),   0,
                        0,               0,   0,               1]
    #o["OB_T_TCP"] = [   1, 0,                               0,  0,  # drehung um x-achse
    #                    0,  np.cos(y_ang),   -np.sin(y_ang),   0,
    #                    0,   np.sin(y_ang),   np.cos(y_ang),   0,
    #                    0,               0,   0,               1]
    
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
    call_method(ip,mios_port, "set_object", o)



def modify_object_kinematics(ip, object,wrench_size=19,l_short=None,l_long=None, grasping_offset_mm=[0,0,0],angle_y=0.,angle_x=0.,mass=None,mios_port = 12000):
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

    try:
        o = call_method(ip,mios_port,"download_object_context",{"object":object})["result"]["context"]
    except KeyError:
        call_method(ip,mios_port,"teach_object",{"object":object})
        o = call_method(ip,mios_port,"download_object_context",{"object":object})["result"]["context"]
    o["OB_I"] = inertia_list
    o["OB_T_gp"] = T_grasp_com_list
    o["OB_T_TCP"] = T_com_tip_list
    o["mass"] = mass
    o["object"] = o["name"]
    call_method(ip,mios_port, "set_object", o)
    return kinematics

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

def get_folder_size(folder_path):
    """
    Calculates the total size of a folder, including all its sub-folders and files.

    Args:
        folder_path (str): The path to the folder.

    Returns:
        int: The total size of the folder in bytes.
    """
    total_size = 0
    # os.walk generates the file names in a directory tree
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for f in filenames:
            # os.path.join creates a full path to the file
            fp = os.path.join(dirpath, f)
            # os.path.getsize gets the size of the file
            # We skip symbolic links to avoid errors and double counting
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size