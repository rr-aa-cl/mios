from mios_examples import *
import math

def addObjectToDatabase(robot,object:str,width:float,force:float=10.0,epsilon:[float,float]=[0.005,0.005],speed:float=1.0):
    call_method(robot, port, "teach_object",{"object":name})


def teach_robot_poses(robot:str,port=12000):
    name=None
    while(name!='x'):
        name=input("Name pose (x to abort) :")
        print("\nteaching ",name, "for ", robot,"\n")
        if name!='x':
            call_method(robot, port, "teach_object",{"object":name})

def screw(robot,approach,location,port=12000, wait=True):
    screw_context = {
        "skill": {
            "p0": {
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
                "K_x": [1500, 1500, 1500, 150, 150, 150]
            },
            "p1": {
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
                "K_x": [1500, 1500, 1500, 150, 150, 150]
            },
            "p2": {
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
                "K_x": [1500, 1500, 1500, 150, 150, 150],
                "f_screw": 5,
                "m_max": 20,
                "phi": 0.1,
                "rot_d": 10,
                "grasp_speed": 2.0,
                "grasp_force": 100,
                "release_speed": 2.0,
                "joint_vel": 1,
                "joint_acc": 2
            },
            "p3": {
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
                "K_x": [1500, 1500, 1500, 150, 150, 150]
            },
            "objects": {
                "Approach": approach,
                "Screw": location
            }
        },
        "control": {
            "control_mode": 1,
            "nullspace":
            {
                "K_theta": [50, 50, 50, 50, 20, 20, 20],
                "xi_theta": [0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7],
                "active": True              
            }
        },
        "user": {
            "env_X": [0.005, 0.005, 0.005, 0.0175, 0.0175, 0.0175],
            "F_ext":[100,50]
        }
    }
    screw_context["skill"]["objects"]["goal_pose"] = location
    screw_context["skill"]["time_max"] = 10
    t0 = Task(robot, port=port)
    t0.add_skill("screw", "TaxScrewNullspace", screw_context)
    t0.start()
    if wait:
        return t0.wait()

def move(robot,pose,port=12000,wait=True,cartesian=True,nullspace=True,accuracy=False):
    move_context = {
        "skill": {
            "p0":{
                "dX_d": [0.5, 0.5],
                "ddX_d": [0.5, 0.5],
                "K_x": [1000, 1000, 1000, 50, 50, 50],
                "T_T_EE_g_offset": [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]

            },
            "time_max":10,
            "objects": {
                    "GoalPose": pose
                }
        },
        "control": {
            "control_mode": 0
        },
        "user":{
            "F_ext_max": [20,10],
            #"env_X": [0.002, 0.002, 0.002, 0.0175, 0.0175, 0.0175]  #[0.001, 0.001, 0.001, 0.001, 0.001, 0.001]
        }
    }
    if nullspace:
        move_context["control"]["nullspace"] = {
            "K_theta": [20, 20, 15, 10, 7, 5, 2],
            "xi_theta": [0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7],
            "active": True
            }
    if accuracy:
        move_context["control"]["nullspace"] = {
            "K_theta": [20, 20, 15, 10, 7, 5, 2],
            "xi_theta": [0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7],
            "active": True
            }
    t = Task(robot, port=port)
    t.add_skill("move", "TaxMove", move_context)
    t.start()
    if wait:
        return t.wait()

def graspObject(robot,obj,port=12000):
    call_method(robot, port, "grasp", {"force":100, "speed":0.5, "width":0, "epsilon_inner":1, "epsilon_outer":1})
    call_method(robot, port, "set_grasped_object", {"object":obj})
    

def release(robot,port=12000):
    call_method(robot, port, "release_object")

def moveGripper(robot,width,speed=1,force=1,port=12000):
    call_method(robot, port, "move_gripper",{"width":width,"speed":speed,"force":force})

def setObject(robot,obj,port=12000):
    call_method(robot, port, "set_grasped_object", {"object":obj})

def homeSystem(robot):
    call_method(robot,12000,"home_gripper")
    call_method(robot,13000,"home_gripper")

def screw(robot,approach,location,port=12000, wait=True):
    screw_context = {
        "skill": {
            "p0": {
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
                "K_x": [1500, 1500, 1500, 150, 150, 150]
            },
            "p1": {
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
                "K_x": [1500, 1500, 1500, 150, 150, 150]
            },
            "p2": {
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
                "K_x": [1500, 1500, 1500, 150, 150, 150],
                "f_screw": 5,
                "m_max": 20,
                "phi": 0.1,
                "rot_d": 10,
                "grasp_speed": 2.0,
                "grasp_force": 100,
                "release_speed": 2.0,
                "joint_vel": 1,
                "joint_acc": 2
            },
            "p3": {
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
                "K_x": [1500, 1500, 1500, 150, 150, 150]
            },
            "objects": {
                "Approach": approach,
                "Screw": location
            }
        },
        "control": {
            "control_mode": 1,
            "nullspace":
            {
                "K_theta": [50, 50, 50, 50, 20, 20, 20],
                "xi_theta": [0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7],
                "active": True
            }
        },
        "user": {
            "env_X": [0.005, 0.005, 0.005, 0.0175, 0.0175, 0.0175],
            "F_ext":[100,50]
        }
    }
    screw_context["skill"]["objects"]["goal_pose"] = location
    screw_context["skill"]["time_max"] = 10
    t0 = Task(robot, port=port)
    t0.add_skill("screw", "TaxScrewNullspace", screw_context)
    t0.start()
    if wait:
        return t0.wait()





