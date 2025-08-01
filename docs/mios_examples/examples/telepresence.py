#!/usr/bin/python3 -u
from task import *
import socket


def get_ip(hostname: str):
    return socket.gethostbyname(hostname)


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
            "control_mode": 1,
            "joint_imp": {
                "K_theta": [1500,1200,800,600,300,200,50]
            }
        }
    }
    t_m = Task(master)
    t_s = Task(slave)
    t_m.add_skill("telepresence", "Telepresence", master_context)
    t_s.add_skill("telepresence", "Telepresence", slave_context)

    t_m.start()
    t_s.start()
    input("Press Enter to stop...")
    t_m.stop()
    t_s.stop()


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
    input("Press Enter to stop...")
    t_m.stop()
    t_s.stop()


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
    input("Press Enter to stop...")
    t_m.stop()
    t_s.stop()


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

    slave_tasks = []

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
        slave_tasks.append(t_s)
    input("Press Enter to stop...")
    t_m.stop()
    for t in slave_tasks:
        t.stop()
