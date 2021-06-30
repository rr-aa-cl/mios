#!/usr/bin/python3 -u
from task import *
from ws_client import *
import time


def record_trajectory(robot: str, duration: int, trajectory_name: str):
    context = {
        "skill": {
            "record_trajectory": True,
            "recording_length": duration * 1000,
            "recording_name": trajectory_name
        },
        "control": {
            "control_mode": 0
        }
    }
    t = Task(robot)
    t.add_skill("record_trajectory", "HandGuiding", context)
    t.start()
    time.sleep(duration)
    result = t.stop()
    print("Result: " + str(result))


def play_trajectory(robot: str, trajectory_name: str):
    context = {
        "skill": {
            "file": trajectory_name
        },
        "control": {
            "control_mode": 0
        }
    }
    t = Task(robot)
    t.add_skill("move_trajectory", "MoveTrajectory", context)
    t.start()
    result = t.wait()
    print("Result: " + str(result))
