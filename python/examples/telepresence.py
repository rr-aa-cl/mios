#!/usr/bin/python3 -u
from ws_client import *


def start_joystick_mode(ip_master, ip_slave):
    start_skill(ip_master, "Telepresence", {"is_master": True, "ip_dst": ip_slave, "port_dst": 8888, "port_src": 8888,
                                            "telepresence_mode": "Joystick",
                                            "joystick": {"amp": [0.01, 0.01, 0.01, 0, 0, 0],
                                                         "force_thr": [4, 4, 4, 2, 2, 2]}},
                {"control_mode": 0})
    start_skill(ip_slave, "Telepresence", {"is_master": False, "ip_dst": ip_master, "port_dst": 8888, "port_src": 8888,
                                           "telepresence_mode": "Joystick"}, {"control_mode": 0})


def start_joint_mode(ip_master, ip_slave):
    start_skill(ip_master, "Telepresence", {"is_master": True, "ip_dst": ip_slave, "port_dst": 8888, "port_src": 8888,
                                            "telepresence_mode": "DirectJoint",
                                            "direct_joint": {"alpha": [15, 15, 10, 7, 6, 4, 3]}}, {"control_mode": 1})
    start_skill(ip_slave, "Telepresence", {"is_master": False, "ip_dst": ip_master, "port_dst": 8888, "port_src": 8888,
                                           "telepresence_mode": "DirectJoint",
                                           "direct_joint": {"alpha": [0, 0, 0, 0, 0, 0, 0]}}, {"control_mode": 1})


def start_cartesian_mode(ip_master, ip_slave):
    start_skill(ip_master, "Telepresence", {"is_master": True, "ip_dst": ip_slave, "port_dst": 8888, "port_src": 8888,
                                            "telepresence_mode": "DirectCart",
                                            "direct_cart": {"alpha": [0, 0, 0, 0, 0, 0]}}, {"control_mode": 0})
    start_skill(ip_slave, "Telepresence", {"is_master": False, "ip_dst": ip_master, "port_dst": 8888, "port_src": 8888,
                                           "telepresence_mode": "DirectCart",
                                           "direct_cart": {"alpha": [0, 0, 0, 0, 0, 0]}}, {"control_mode": 0})


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
