from desk.mongodb_client import MongoDBClient
import os
from utils.ws_client import *
import json
import socket

import time

HARDCODED_PORT = 12000

class Task:
    def __init__(self, robot, port=HARDCODED_PORT):
        self.skill_names = []
        self.skill_types = []
        self.skill_context = dict()
        self.context = {
            "parameters": {"skill_names": [], "skill_types": [], "as_queue": False},
            "skills": self.skill_context,
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
        response = start_task(
            self.robot, "GenericTask", parameters=self.context, port=self.port
        )
        self.task_uuid = response["result"]["task_uuid"]

    def wait(self):
        result = wait_for_task(self.robot, self.task_uuid, port=self.port)
        # print("Task execution took " + str(time.time() - self.t_0) + " s.")
        return result

    def stop(self):
        result = stop_task(self.robot, port=self.port)
        # print("Task execution took " + str(time.time() - self.t_0) + " s.")
        return result


def grasp(robot):
    # grasp sth smaller than 10cm (epsilon_outer=0.1)
    return call_method(
        robot,
        HARDCODED_PORT,
        "grasp",
        {
            "width": 0.0,
            "speed": 1,
            "force": 200,
            "epsilon_inner": 1,
            "epsilon_outer": 0.1,
        },
    )


def open_gripper(robot):
    # opens the gripper completely
    return call_method(robot, HARDCODED_PORT, "release_object", {"speed": 1})


def move_gripper(robot, gripper_width):
    # open the gripper with gripper_width in [m] for e.g. 0.06 = 6cm
    return call_method(
        robot, HARDCODED_PORT, "move_gripper", {"width": gripper_width, "speed": 0.15}
    )


def init_position(robot):
    import math

    # move robot to start position
    M_PI_2 = math.pi / 2
    M_PI_4 = math.pi / 4
    # initial_joint_pose = [0, -M_PI_4, 0, -3 * M_PI_4, 0, M_PI_2, M_PI_4]
    initial_joint_pose = [
        -1.3248630826150967,
        -1.0180141037361554,
        0.8553967592921208,
        -2.2646868672636953,
        2.243648430342865,
        2.443334998639592,
        -0.6927231896896919,
    ]
    [
        -1.6379584697665992,
        -0.9672686907468586,
        0.9518780780416728,
        -2.102286267950551,
        2.2313950677265564,
        2.259109395974202,
        -2.1549792265466277,
    ]

    return start_task(
        robot,
        "MoveToJointPose",
        parameters={"parameters": {"q_g": initial_joint_pose, "pose": "NoneObject"}},
        port=HARDCODED_PORT,
    )


def handguiding_old(robot: str, message: str = "Press any key to stop"):
    context = {
        "skill": {
            "record_trajectory": False,
            # "recording_length": 1,
            # "recording_name": None,
        },
        "control": {"control_mode": 0},
    }
    t = Task(robot)
    t.add_skill("record_trajectory", "HandGuiding", context)
    t.start()
    input(message)
    result = t.stop()
    print("Result: " + str(result))


def teach_insertion(robot:str, object_name:str,port=HARDCODED_PORT):
    insertable = object_name
    print("\nteaching ",insertable, "for ", robot,"\n")

    handguiding(robot, "Insert the object into the robot\'s fingers. [Press any key to continue]")
    call_method(robot, port, "grasp", {"width":0,"speed":1,"force":100})
    time.sleep(1)
    call_method(robot, port, "teach_object", {"object": insertable, "width":True})
    time.sleep(1)
    current_finger_width = call_method(robot,HARDCODED_PORT,"get_state")["result"]["gripper_width"]
    call_method(robot,port,"move_gripper",{"speed":1,"force":100,"width":current_finger_width+0.005})
    time.sleep(1)
    print(call_method(robot, port, "grasp_object", {"object": insertable}))
    handguiding(robot, "Teach approach pose slightly above the object\'s container. [Press any key to continue]")
    time.sleep(2)
    call_method(robot, port, "teach_object", {"object": insertable+"_container_approach"})
    handguiding(robot, "Teach container pose with the object fully inserted into the container. [Press any key to continue]")
    time.sleep(1)
    call_method(robot, port, "teach_object", {"object": insertable+"_container"})
    # print(call_method(robot, HARDCODED_PORT, "grasp_object", {"object": insertable}))
    handguiding(robot, "Extract robot and object again. [Press any key to continue]")


def teach_insertion(robot:str, object_name:str,port=HARDCODED_PORT):
    insertable = object_name
    print("\nteaching ",insertable, "for ", robot,"\n")

    handguiding(robot, "Insert the object into the robot\'s fingers. [Press any key to continue]")
    call_method(robot, port, "grasp", {"width":0,"speed":1,"force":100})
    time.sleep(1)
    call_method(robot, port, "teach_object", {"object": insertable, "width":True})
    time.sleep(1)
    current_finger_width = call_method(robot,HARDCODED_PORT,"get_state")["result"]["gripper_width"]
    call_method(robot,port,"move_gripper",{"speed":1,"force":100,"width":current_finger_width+0.005})
    time.sleep(1)
    print(call_method(robot, port, "grasp_object", {"object": insertable}))
    handguiding(robot, "Teach approach pose slightly above the object\'s container. [Press any key to continue]")
    time.sleep(2)
    call_method(robot, port, "teach_object", {"object": insertable+"_container_approach"})
    handguiding(robot, "Teach container pose with the object fully inserted into the container. [Press any key to continue]")
    time.sleep(1)
    call_method(robot, port, "teach_object", {"object": insertable+"_container"})
    # print(call_method(robot, HARDCODED_PORT, "grasp_object", {"object": insertable}))
    handguiding(robot, "Extract robot and object again. [Press any key to continue]")


def handguiding(robot: str, message: str = "Press any key to stop"):
    context = {
        "skill": {
            "record_trajectory": False,
            # "recording_length": 1,
            # "recording_name": None,
        },
        "control": {"control_mode": 0},
    }
    t = Task(robot)
    t.add_skill("record_trajectory", "HandGuiding", context)
    t.start()
    input(message)
    result = t.stop()
    print("Result: " + str(result))


if __name__ == "__main__":
    ROBOT = "localhost"

    print('Breakpoint ------- 11')
    # current_finger_width = call_method(ROBOT,HARDCODED_PORT,"get_state")["result"]
    # print(str(current_finger_width))
    # init_position(ROBOT)
    # handguiding(ROBOT)
    # call_method(ROBOT, HARDCODED_PORT, "home_gripper") # Trial of open and close
    teach_insertion(ROBOT, "reza-1", HARDCODED_PORT)
    # init_position(ROBOT)
