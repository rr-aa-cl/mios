#!/usr/bin/python3 -u
from ws_client import *
import time


def record_trajectory(robot: str, duration: int, trajectory_name: str):
    start_skill(robot, "HandGuiding", {"record_trajectory": True, "recording_length": duration * 1000,
                                       "recording_name": trajectory_name}, {"control_mode": 0})
    time.sleep(duration)
    stop_task(robot)


def play_trajectory(robot: str, file: str):
    start_skill(robot, "MoveTrajectory", {"file": file, "plane": False, "F_ff": 5}, {"control_mode": 0})


def start_skill(address: str, skill: str, parameters: dict, control: dict):
    response = start_task(address, "GenericTask", parameters={"parameters": {
        "skill_names": ["skill"],
        "skill_types": [skill]
    },
        "skills": {
            "skill": {
                "skill": parameters,
                "control": control
            }
        }})