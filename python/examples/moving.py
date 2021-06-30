#!/usr/bin/python3 -u
from task import *
from ws_client import *


def teach_location(robot: str, location: str):
    call_method(robot, 12000, "teach_object", {"object": location})


def move_to_location(robot: str, location: str):
    context = {
        "skill": {
            "speed": [0.1, 0.5],
            "acc": [0.5, 1],
            "objects": {
                "GoalPose": location
            }
        },
        "control": {
            "control_mode": 0
        }
    }
    t = Task(robot)
    t.add_skill("move", "TaxMove", context)
    t.start()
    result = t.wait()
    print("Result: " + str(result))
