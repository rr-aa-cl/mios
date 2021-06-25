#!/usr/bin/python3 -u
from ws_client import *
import time
import socket


def get_ip(hostname: str):
    return socket.gethostbyname(hostname)


class Task:
    def __init__(self, robot):
        self.skill_names = []
        self.skill_types = []
        self.skill_context = dict()

        self.robot = robot
        self.task_uuid = "INVALID"
        self.t_0 = 0

    def add_skill(self, name, type, context):
        self.skill_names.append(name)
        self.skill_types.append(type)
        self.skill_context[name] = context

    def start(self, queue: bool = False):
        self.t_0 = time.time()
        parameters = {
            "parameters": {
                "skill_names": self.skill_names,
                "skill_types": self.skill_types,
                "as_queue": queue
            },
            "skills": self.skill_context
        }
        print(self.skill_context)
        print("DONE")
        response = start_task(self.robot, "GenericTask", parameters)

        self.task_uuid = response["result"]["task_uuid"]

    def wait(self):
        result = wait_for_task(self.robot, self.task_uuid)
        print("Task execution took " + str(time.time() - self.t_0) + " s.")
        return result


def direct_joint_mode(master: str, slave: str):
    master_context = {
        "skill": {
            "is_master": True,
            "ip_dst": get_ip(slave),
            "port_dst": 8888,
            "port_src": 8888,
            "telepresence_mode": "DirectJoint",
            "direct_joint": {
                "alpha": [15, 15, 10, 10, 8, 6, 3]
            }
        },
        "control": {
            "control_mode": 1
        }
    }
    slave_context = {
        "skill": {
            "is_master": False,
            "ip_dst": get_ip(master),
            "port_dst": 8888,
            "port_src": 8888,
            "telepresence_mode": "DirectJoint",
            "direct_joint": {
                "alpha": [0, 0, 0, 0, 0, 0, 0]
            }
        },
        "control": {
            "control_mode": 1
        }
    }
    t_m = Task(master)
    t_s = Task(slave)
    t_m.add_skill("telepresence", "Telepresence", master_context)
    t_s.add_skill("telepresence", "Telepresence", slave_context)

    t_m.start()
    t_s.start()


def joystick_mode(master: str, slave: str):
    master_context = {
        "skill": {
            "is_master": True,
            "ip_dst": get_ip(slave),
            "port_dst": 8888,
            "port_src": 8888,
            "telepresence_mode": "Joystick",
            "joystick": {
                "amp": [0.01, 0.01, 0.01, 0, 0, 0],
                "force_thr": [4, 4, 4, 2, 2, 2]
            }
        },
        "control": {
            "control_mode": 0
        }
    }
    slave_context = {
        "skill": {
            "is_master": False,
            "ip_dst": get_ip(master),
            "port_dst": 8888,
            "port_src": 8888,
            "telepresence_mode": "Joystick"
        },
        "control": {
            "control_mode": 0
        }
    }
    t_m = Task(master)
    t_s = Task(slave)
    t_m.add_skill("telepresence", "Telepresence", master_context)
    t_s.add_skill("telepresence", "Telepresence", slave_context)

    t_m.start()
    t_s.start()


def direct_cartesian_mode(master: str, slave: str):
    master_context = {
        "skill": {
            "is_master": True,
            "ip_dst": get_ip(slave),
            "port_dst": 8888,
            "port_src": 8888,
            "telepresence_mode": "DirectCart",
            "direct_cart": {
                "alpha": [0, 0, 0, 0, 0, 0]
            }
        },
        "control": {
            "control_mode": 0
        }
    }
    slave_context = {
        "skill": {
            "is_master": False,
            "ip_dst": get_ip(master),
            "port_dst": 8888,
            "port_src": 8888,
            "telepresence_mode": "DirectCart"
        },
        "control": {
            "control_mode": 0
        }
    }
    t_m = Task(master)
    t_s = Task(slave)
    t_m.add_skill("telepresence", "Telepresence", master_context)
    t_s.add_skill("telepresence", "Telepresence", slave_context)

    t_m.start()
    t_s.start()


def multi_direct_joint_mode(master: str, slaves: list):

    ip_slaves = []
    for s in slaves:
        ip_slaves.append(get_ip(s))

    master_context = {
        "skill": {
            "is_master": True,
            "ip_dst": "0.0.0.0",
            "port_dst": 8888,
            "port_src": 8888,
            "multicast": True,
            "multicast_group": ip_slaves,
            "telepresence_mode": "DirectJoint"
        },
        "control": {
            "control_mode": 1
        }
    }
    t_m = Task(master)
    t_m.add_skill("telepresence", "Telepresence", master_context)
    t_m.start()

    for s in slaves:
        slave_context = {
            "skill": {
                "is_master": False,
                "ip_dst": get_ip(master),
                "port_dst": 8888,
                "port_src": 8888,
                "multicast": True,
                "telepresence_mode": "DirectJoint"
            },
            "control": {
                "control_mode": 1
            }
        }
        t_s = Task(s)
        t_s.add_skill("telepresence", "Telepresence", slave_context)
        t_s.start()
