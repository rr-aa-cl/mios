#!/usr/bin/python3 -u
import time
import numpy as np

from ws_client import *


def start_skill(address: str, skill: str, parameters: dict, control: dict, skill_name: str = "skill"):
    response = start_task(address, "GenericTask", parameters={"parameters": {
        "skill_names": [skill_name],
        "skill_types": [skill]
    },
        "skills": {
            "skill": {
                "skill": parameters,
                "control": control
            }
        }})
    return response


def test_tax_grab(robot="collective-panda-008.local"):
    start_skill(robot, "TaxGrab", {"objects": {"Retract": "tax_grab_retract", "Approach": "tax_grab_approach",
                                               "Grabbable": "cylinder_60"}, "speed": [0.1, 0.5], "acc": [0.5, 1.0],
                                   "grasp_width": 0.03, "grasp_speed": 2, "grasp_force": 30,
                                   "ROI_x": [-0.2, 0.2, -0.2, 0.2, -0.2, 0.2],
                                   "ROI_phi": [0, 0, 0, 0, 0, 0]}, {"control_mode": 2})


def test_tax_place(robot="collective-panda-008.local"):
    call_method(robot, 12000, "set_grasped_object", {"object": "cylinder_60"})
    start_skill(robot, "TaxPlace", {"objects": {"Retract": "tax_place_retract", "Approach": "tax_place_approach",
                                                "Placeable": "cylinder_60", "Surface": "cylinder_60"},
                                    "speed": [0.05, 0.5], "acc": [0.5, 1.0],
                                    "release_width": 0.06, "release_speed": 2,
                                    "ROI_x": [-0.2, 0.2, -0.2, 0.2, -0.2, 0.2],
                                    "ROI_phi": [0, 0, 0, 0, 0, 0]}, {"control_mode": 0})


def test_tax_turn(robot="collective-panda-008.local"):
    call_method(robot, 12000, "set_grasped_object", {"object": "tax_turn_turnable"})
    start_skill(robot, "TaxTurn", {"objects": {"Turnable": "tax_turn_turnable", "GoalOrientation": "tax_turn_goal"},
                                   "turn_speed": [0.05, 0.5], "turn_acc": [0.5, 1.0]},
                {"control_mode": 0})


def test_tax_press_button(robot="collective-panda-008.local"):
    start_skill(robot, "TaxPressButton",
                {"objects": {"Button": "tax_press_button_button", "Approach": "tax_press_button_approach"},
                 "approach_speed": [0.05, 0.5], "approach_acc": [0.5, 1.0],
                 "press_speed": [0.05, 0.5], "press_acc": [0.5, 1.0], "duration": 5,
                 "ROI_x": [-0.2, 0.2, -0.2, 0.2, -0.2, 0.2],
                 "ROI_phi": [0, 0, 0, 0, 0, 0]},
                {"control_mode": 0})

def iros_task():
    robot = "collective-panda-008.local"
    # move to grab key
    response = start_skill(robot, "TaxMove", {"objects": {"GoalPose": "iros_key_roi"},
                                              "speed": [0.1, 0.5], "acc": [0.5, 1]}, {"control_mode": 0})
    wait_for_task(robot, {"task_uuid": response["result"]["task_uuid"]})
    # grab key
    response = start_skill(robot, "TaxGrab", {"objects": {"Retract": "iros_key_grab_retract", "Approach": "iros_key_grab_approach",
                                               "Grabbable": "iros_key"}, "speed": [0.1, 0.5], "acc": [0.5, 1.0],
                                   "grasp_width": 0.03, "grasp_speed": 2, "grasp_force": 30,
                                   "ROI_x": [-0.2, 0.2, -0.2, 0.2, -0.2, 0.2],
                                   "ROI_phi": [0, 0, 0, 0, 0, 0]}, {"control_mode": 0})
    wait_for_task(robot, {"task_uuid": response["result"]["task_uuid"]})
    # move to insertion
    response = start_skill(robot, "TaxMove",
                           {"objects": {"GoalPose": "iros_insertion_roi"},
                            "speed": [0.1, 0.5], "acc": [0.5, 1]}, {"control_mode": 0})
    wait_for_task(robot, {"task_uuid": response["result"]["task_uuid"]})
    # insert key
    response = start_skill(robot, "TaxInsertion",
                           {"objects": {"Container": "iros_lock", "Approach": "iros_lock_approach",
                                        "Insertable": "iros_key"}, "approach_speed": [0.1, 0.5], "approach_acc": [0.5, 1.0],
                            "insertion_speed": [0.1, 0.5], "insertion_acc": [0.5, 1.0],
                            "search_a": [0, 0, 0, 0, 0, 0], "search_f": [0, 0, 0, 0, 0, 0],
                            "ROI_x": [-0.2, 0.2, -0.2, 0.2, -0.2, 0.2],
                            "ROI_phi": [0, 0, 0, 0, 0, 0]}, {"control_mode": 0})
    wait_for_task(robot, {"task_uuid": response["result"]["task_uuid"]})
    # turn key
    start_skill(robot, "TaxTurn", {"objects": {"Turnable": "iros_key", "GoalOrientation": "iros_turn_goal"},
                                   "turn_speed": [0.05, 0.5], "turn_acc": [0.5, 1.0]},
                {"control_mode": 0})
    wait_for_task(robot, {"task_uuid": response["result"]["task_uuid"]})
    # turn key back
    start_skill(robot, "TaxTurn", {"objects": {"Turnable": "iros_key", "GoalOrientation": "iros_lock"},
                                   "turn_speed": [0.05, 0.5], "turn_acc": [0.5, 1.0]},
                {"control_mode": 0})
    wait_for_task(robot, {"task_uuid": response["result"]["task_uuid"]})
    # extract key
    response = start_skill(robot, "TaxExtraction",
                           {"objects": {"Container": "iros_lock", "Retract": "iros_lock_approach",
                                        "Extractable": "iros_key"}, "extraction_speed": [0.1, 0.5], "extraction_acc": [0.5, 1.0],
                            "search_a": [0, 0, 0, 0, 0, 0], "search_f": [0, 0, 0, 0, 0, 0]}, {"control_mode": 0})
    wait_for_task(robot, {"task_uuid": response["result"]["task_uuid"]})
    # move to key storage
    response = start_skill(robot, "TaxMove",
                           {"objects": {"GoalPose": "iros_key_roi"},
                            "speed": [0.1, 0.5], "acc": [0.5, 1]}, {"control_mode": 0})
    wait_for_task(robot, {"task_uuid": response["result"]["task_uuid"]})
    # place key
    response = start_skill(robot, "TaxGrab", {"objects": {"Retract": "iros_key_grab_retract", "Approach": "iros_key_grab_approach",
                                               "Placeable": "iros_key", "Surface": "iros_key_storage"}, "speed": [0.1, 0.5], "acc": [0.5, 1.0],
                                   "release_width": 0.03, "release_speed": 2,
                                   "ROI_x": [-0.2, 0.2, -0.2, 0.2, -0.2, 0.2],
                                   "ROI_phi": [0, 0, 0, 0, 0, 0]}, {"control_mode": 0})
    wait_for_task(robot, {"task_uuid": response["result"]["task_uuid"]})
    # move to button
    response = start_skill(robot, "TaxMove",
                           {"objects": {"GoalPose": "iros_button_roi"},
                            "speed": [0.1, 0.5], "acc": [0.5, 1]}, {"control_mode": 0})
    wait_for_task(robot, {"task_uuid": response["result"]["task_uuid"]})
    # press button
    start_skill(robot, "TaxPressButton",
                {"objects": {"Button": "iros_button", "Approach": "iros_button_approach"},
                 "approach_speed": [0.05, 0.5], "approach_acc": [0.5, 1.0],
                 "press_speed": [0.05, 0.5], "press_acc": [0.5, 1.0], "duration": 5,
                 "ROI_x": [-0.2, 0.2, -0.2, 0.2, -0.2, 0.2],
                 "ROI_phi": [0, 0, 0, 0, 0, 0]},
                {"control_mode": 0})
    wait_for_task(robot, {"task_uuid": response["result"]["task_uuid"]})
    # move to idle pose
    response = start_skill(robot, "TaxMove",
                           {"objects": {"GoalPose": "iros_idle_pose"},
                            "speed": [0.1, 0.5], "acc": [0.5, 1]}, {"control_mode": 0})
