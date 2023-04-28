#!/usr/bin/python3 -u
from utils.ws_client import *
import time

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

def test_insertion(robot: str):
    context = {
        "skill": {
            "objects": {
                "Container": "generic_container",
                "Approach": "generic_container_approach",
                "Insertable": "generic_insertable"
            },
            "p0":{
                "K_x": [1000, 1000, 1000, 100, 100, 100],
                "DeltaX": [0, 0, 0, 0, 0, 0],
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1]
            },
            "p1": {
                "K_x": [1000, 1000, 1000, 100, 100, 100],
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1]
            },
            "p2": {
                "K_x": [1000, 1000, 1000, 100, 100, 100],
                "search_a": [0, 0, 0, 0, 0, 0],
                "search_f": [0, 0, 0, 0, 0, 0],
                "f_push": 10
            },
            "p3": {
                "K_x": [1000, 1000, 1000, 100, 100, 100],
                "f_push": 10,
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1]
            },
            "time_max": 5
        },
        "control": {
            "control_mode": 0
        },
        "user": {
            "env_X": [0.02, 0.04]
        }
    }
    t = Task(robot)
    t.add_skill("insertion", "TaxInsertion", context)
    t.start()
    result = t.wait()
    print(result)