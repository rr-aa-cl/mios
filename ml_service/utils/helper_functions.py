import json
import os

from utils.ws_client import call_method
from utils.taxonomy_utils import Task

def move(robot, location, offset):
    context = {
        "skill": {
            "p0":{
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
                "K_x": [2000, 2000, 2000, 250, 250, 250],
                "T_T_EE_g_offset": [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, offset[0], offset[1], offset[2], 1]

            },
            "objects": {
                    "GoalPose": location
                }
        },
        "control": {
            "control_mode": 2
        }
    }
    t = Task(robot)
    t.add_skill("move", "TaxMove", context)
    t.start()
    result = t.wait()
    print("Result: " + str(result))

def move_joint(robot, location):
    path_to_default_context = os.getcwd() + "/../python/taxonomy/default_contexts/"
    t0 = Task(robot)
    f = open(path_to_default_context + "move_joint.json")
    move_context = json.load(f)
    move_context["skill"]["objects"]["goal_pose"] = location
    t0.add_skill("move", "MoveToPoseJoint", move_context)
    t0.start()
    result = t0.wait()

def place_insertable(robot, insertable="generic_insertable", container="generic_container", approach="generic_container_approach", above = None):
    if call_method(robot,12000,"get_state")["result"]['grasped_object'] == 'NullObject':
        call_method(robot, 12000, "set_grasped_object", {"object": insertable})
    path_to_default_context = os.getcwd() + "/../python/taxonomy/default_contexts/"
    t0 = Task(robot)
    t1 = Task(robot)
    t2 = Task(robot)
    if above is None:
        move(robot, approach, [0,0,0.1])
    else:
        move_joint(robot, above)
    f = open(path_to_default_context + "insertion.json")
    insertion_context = json.load(f)
    insertion_context["skill"]["objects"]["Insertable"] = insertable
    insertion_context["skill"]["objects"]["Container"] = container
    insertion_context["skill"]["objects"]["Approach"] = approach

    insertion_context["skill"]["p2"]["search_a"]= [10, 10, 0, 2, 2, 0]
    insertion_context["skill"]["p2"]["search_f"] = [1, 0.75, 0, 1, 0.75, 0]
    insertion_context["skill"]["p2"]["f_push"] = [0, 0, 20, 0, 0, 0]

    f = open(path_to_default_context + "move_joint.json")
    move_context = json.load(f)
    move_context["skill"]["objects"]["goal_pose"] = approach
    t0.add_skill("move", "MoveToPoseJoint", move_context)
    t0.start()
    result = t0.wait()

    t1.add_skill("insertion", "TaxInsertion", insertion_context)
    t1.start()
    result = t1.wait()
    
    if result["result"]["task_result"]["success"] == True:
        call_method(robot, 12000, "release_object")
    else:
        return False
    move(robot, approach, [0,0,0.1])
    call_method(robot, 12000, "home_gripper")

def grasp_insertable(robot:str, insertable = "generic_insertable", container = "generic_container", approach = "generic_container_approach", above = None):
    print("current object grasped: ", call_method(robot,12000,"get_state")["result"]['grasped_object'] )
    if call_method(robot,12000,"get_state")["result"]['grasped_object'] == 'NullObject':
        call_method(robot, 12000, "release_object")
    else:
        print("I am already grasping something")
        return 0
    if above is None:
        move(robot, approach, [0,0,0.1])
    else:
        move_joint(robot, above)
    call_method(robot,12000,"move_gripper",{"width":0.06,"force":100,"epsilon_outer":1,"speed":100})
    path_to_default_context = os.getcwd() + "/../python/taxonomy/default_contexts/"
    t1 = Task(robot)
    t2 = Task(robot)
    f = open(path_to_default_context + "move_cart.json")
    move_fine_context = json.load(f)
    move_fine_context["skill"]["objects"]["GoalPose"] = insertable

    f = open(path_to_default_context + "extraction.json")
    extraction_context = json.load(f)
    extraction_context["skill"]["objects"]["Extractable"] = insertable
    extraction_context["skill"]["objects"]["Container"] = container
    extraction_context["skill"]["objects"]["ExtractTo"] = approach
    #execution
    t1.add_skill("move_fine", "TaxMove", move_fine_context)
    success_moving = False
    success_grasping = False
    count = 0
    while success_grasping == False:
        while success_moving == False:
            call_method(robot, 12000, "move_gripper",{"width":0.07,"speed":1,"force":100})
            t1.start()
            success_moving = t1.wait()["result"]["task_result"]["success"]
            if not success_moving:
                print(robot, ": moving success = ", success_moving)
            count += 1
            if count > 2:
                continue
        success_moving = False
        result = call_method(robot,12000,"grasp",{"width":0,"force":100,"epsilon_outer":1,"speed":100}) #call_method(robot, 12000, "grasp_object", {"object": "generic_insertable"})
        call_method(robot,12000,"set_grasped_object",{"object":insertable})
        #call_method(robot, 12000,"set_grasped_object", {"object": "generic_insertable"})
        success_grasping  = result["result"]["result"]
        if not success_grasping:
            print(robot, " grasping success = ", success_grasping)
        count += 1
        if count > 12:
            continue

    t2.add_skill("extraction", "TaxExtraction", extraction_context)
    t2.start()
    print(t2.wait())
    return True

