#!/usr/bin/python3 -u
from ws_client import *


def teach_location(robot: str, location: str):
    call_method(robot, 12000, "teach_object", {"object": location})


def move_to_location(robot, location):
    start_task(robot, "MoveToCartPose", {"parameters": {"pose": location, "speed": [0.1, 0.5], "acc": [0.5, 1]}})
