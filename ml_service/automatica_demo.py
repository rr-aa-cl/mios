#!/usr/bin/python3 -u
from utils.ws_client import *
import time
import socket
from utils.experiment_wizard import *
from utils.database import *
from services.svm import SVMConfiguration
from definitions.insertion_definitions import insert_generic
from threading import Thread


robots = ["collective-panda-prime",
 #"collective-panda-007",
  "collective-panda-002",
  #        "collective-panda-008",
           "collective-panda-003",
            "collective-panda-004",
          "collective-panda-008"]#,
   #        "collective-panda-010",
   #         "collective-panda-004"]


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


def run_demo():
    input("Start part I")
    demo_part_1()
    input("Start part II")
    demo_part_2()
    input("Start part III")
    demo_part_3()
    input("Start IV")
    demo_part_4()


def demo_part_1():
    call_method(robots[0], 12000, "set_grasped_object", {"object": "generic_insertable"})
    insertion_context = {
        "skill": {
            "objects": {
                "Container": "generic_container",
                "Approach": "generic_container_approach",
                "Insertable": "generic_insertable"
            },
            "approach_speed": [0.2, 0.5],
            "approach_acc": [0.5, 1],
            "insertion_speed": [0.1, 0.4],
            "insertion_acc": [0.5, 1.0],
            "f_max_push": 10,
            "search_a": [0, 0, 0, 0, 0, 0],
            "search_f": [0, 0, 0, 0, 0., 0],
            "ROI_x": [-0.2, 0.2, -0.2, 0.2, -0.2, 0.2],
            "ROI_phi": [0, 0, 0, 0, 0, 0],
            "stuck_dx_thr": 0.035,
            "DeltaX": [0, 0, 0, 0, 0, 0],
            "time_max": 5
        },
        "control": {
            "control_mode": 0,
            "cart_imp": {
                "K_x": [500, 500, 500, 100, 100, 100]
            }
        },
        "user": {
            "env_X": [0.02, 0.04]
        }
    }
    move_up_context = {
        "skill": {
            "objects": {
                "GoalPose": "EndEffector"
            },
            "speed": [0.1, 0.5],
            "acc": [0.5, 1],
            "T_T_EE_g_offset": [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0.05, 1]
        },
        "control": {
            "control_mode": 0
        }
    }
    extraction_context = {
        "skill": {
            "objects": {
                "Container": "generic_container",
                "ExtractTo": "generic_container_approach",
                "Extractable": "generic_insertable"
            },
            "extraction_speed": [0.5, 1],
            "extraction_acc": [1, 4],
            "search_a": [3, 1.7, 3.6, 0.64, 0.85, 0],
            "search_f": [0.77, 0, 0.8, 0.16, 0.58, 0],
            "stuck_dx_thr": 0.09
        },
        "control": {
            "control_mode": 0,
            "cart_imp": {
                "K_x": [702, 276, 1798, 110, 131, 45]
            }
        },
        "user": {
            "env_X": [0.03, 0.08]
        }
    }

    insertion_context1 = copy.deepcopy(insertion_context)
    insertion_context1["skill"]["DeltaX"] = [0.01, -0.005, 0, 10, 5, 0]
    insertion_context1["skill"]["search_a"] = [3, 3, 0, 0, 0, 0]
    insertion_context1["skill"]["search_f"] = [1, 0.75, 0, 0, 0, 0]

    insertion_context2 = copy.deepcopy(insertion_context)
    insertion_context2["skill"]["DeltaX"] = [-0.002, 0.005, 0, 10, -10, 0]
    insertion_context2["skill"]["insertion_speed"] = [0.01, 0.01]
    insertion_context2["skill"]["search_a"] = [8, 8, 0, 0, 0, 0]
    insertion_context2["skill"]["search_f"] = [1, 0.75, 0, 0, 0, 0]
    insertion_context3 = copy.deepcopy(insertion_context)
    insertion_context3["skill"]["DeltaX"] = [-0.01, 0.005, 0, 0.0, -7, 0]
    insertion_context3["skill"]["insertion_speed"] = [0.01, 0.01]
    insertion_context3["skill"]["search_a"] = [8, 8, 0, 0, 0, 0]
    insertion_context3["skill"]["search_f"] = [1, 0.75, 0, 0, 0, 0]
    insertion_context3["control"]["cart_imp"]["K_x"] = [100, 100, 500, 50, 50, 50]


    wiggle_context = {
        "skill": {
            "dX_fourier_a_a": [0, 0.05, 0, 0, 0, 0],
            "dX_fourier_a_phi": [0, 0.71, 0, 0, 0, 0],
            "dX_fourier_a_f": [0, 1, 0, 0, 0, 0],
            "dX_fourier_b_a": [0, 0, 0, 0, 0, 0],
            "dX_fourier_b_f": [0, 0, 0, 0, 0, 0],
            "use_EE": True,
            "time_max": 5
        },
        "control": {
            "control_mode": 0
        }
    }

    t = Task(robots[0])
    t.add_skill("insertion1", "TaxInsertion", insertion_context1)
    t.add_skill("extraction1", "TaxExtraction", extraction_context)
    t.add_skill("move1", "TaxMove", move_up_context)
    t.add_skill("insertion2", "TaxInsertion", insertion_context2)
    t.add_skill("extraction2", "TaxExtraction", extraction_context)
    t.add_skill("move2", "TaxMove", move_up_context)
    t.add_skill("insertion3", "TaxInsertion", insertion_context3)
    t.add_skill("extraction3", "TaxExtraction", extraction_context)
    move_up_context2 = copy.deepcopy(move_up_context)
    move_up_context2["skill"]["T_T_EE_g_offset"][14] = 0.2
    t.add_skill("move3", "TaxMove", move_up_context2)
    t.add_skill("fail", "GenericWiggleMotion", wiggle_context)

    result = start_task(robots[0], "MoveToJointPose", {
        "parameters": {
            "pose": "generic_container_approach",
            "speed": 1,
            "acc": 2
        }
    })
    wait_for_task(robots[0], result["result"]["task_uuid"])

    t.start(True)
    result = t.wait()


def demo_part_2():

    result = start_task(robots[0], "MoveToJointPose", {
        "parameters": {
            "pose": "automatica_telepresence",
            "speed": 1,
            "acc": 2
        }
    })
    wait_for_task(robots[0], result["result"]["task_uuid"])

    ip_master = get_ip(robots[0])
    ip_slaves = []
    for i in range(1, len(robots)):
        ip_slaves.append(get_ip(robots[i]))

    print(ip_slaves)

    telepresence_master_context = {
        "skill": {
            "is_master": True,
            "ip_dst": "0.0.0.0",
            "port_dst": 8888,
            "port_src": 8888,
            "telepresence_mode": "DirectJoint",
            "multicast": True,
            "multicast_group": ip_slaves,
            "direct_joint": {
                "alpha": [0, 0, 0, 0, 0, 0, 0]
            }
        },
        "control": {
            "control_mode": 1
        }
    }
    telepresence_slave_context = {
        "skill": {
            "is_master": False,
            "ip_dst": "0.0.0.0",
            "port_dst": 8888,
            "port_src": 8888,
            "telepresence_mode": "DirectJoint",
            "multicast": True,
            "direct_joint": {
                "alpha": [0, 0, 0, 0, 0, 0, 0]
            }
        },
        "control": {
            "control_mode": 1
        }
    }
    t = Task(robots[0])
    t.add_skill("telepresence", "Telepresence", telepresence_master_context)
    t.start()
    for i in range(1, len(robots)):
        t = Task(robots[i])
        t.add_skill("telepresence", "Telepresence", telepresence_slave_context)
        print(robots[i])
        t.start()

    input("Press key to stop.")
    for ip in ip_slaves:
        stop_task(ip)

    stop_task(ip_master)


def demo_part_3():
    base_batch_size_experiment = 5
    n_trials_experiment = 180
    agents = robots[1:]
    for a in agents:
        call_method(a, 12000, "set_grasped_object", {"object": "generic_insertable"})

    service_config = SVMConfiguration()
    service_config.exploration_mode = True
    service_config.n_trials = n_trials_experiment
    service_config.batch_width = base_batch_size_experiment * len(agents)
    print(service_config.batch_width)
    service_config.n_immigrant = service_config.batch_width - base_batch_size_experiment
    tag = "live_plotting_test" #"collective_experiment_shared"
    knowledge = {"mode": "none", "kb_location": agents[0], "kb_tags": [tag]}
    threads = []
    pd = insert_generic()
    s = ServerProxy("http://" + agents[0] + ":8001", allow_none=True)
    s.clear_memory()
    j = 0
    for a in agents:
        pd = insert_generic()
        tags = [tag, a, "automatica_demo"]
        delete_results([a], tags)
        threads.append(
            Thread(target=start_single_experiment, args=(a, [a], pd, service_config, 1, tags, knowledge, False,)))
        threads[-1].start()
        j += 1

    input("Press key to stop.")
    for a in agents:
        s = ServerProxy("http://" + a + ":8000", allow_none=True)
        s.stop_service()
        stop_task(a)


def demo_part_4():
    call_method(robots[0], 12000, "set_grasped_object", {"object": "generic_insertable"})
    result = start_task(robots[0], "MoveToJointPose", {
        "parameters": {
            "pose": "generic_container_approach",
            "speed": 1,
            "acc": 2
        }
    })
    wait_for_task(robots[0], result["result"]["task_uuid"])
    insertion_context = {
        "skill": {
            "objects": {
                "Container": "generic_container",
                "Approach": "generic_container_approach",
                "Insertable": "generic_insertable"
            },
            "approach_speed": [0.2, 0.5],
            "approach_acc": [0.5, 1],
            "insertion_speed": [0.15, 0.3],
            "insertion_acc": [0.5, 1.62],
            "f_max_push": 10,
            "DeltaX": [0.005, 0, 0, 0, 10, 0],
            "search_a": [5, 6, 4, 1.15, 1.5, 0],
            "search_f": [2, 1, 0.6, 0.7, 0.87, 0],
            "ROI_x": [-0.2, 0.2, -0.2, 0.2, -0.2, 0.2],
            "ROI_phi": [0, 0, 0, 0, 0, 0],
            "stuck_dx_thr": 0.035
        },
        "control": {
            "control_mode": 0,
            "cart_imp": {
                "K_x": [1004, 1536, 1617, 100, 100, 68]
            }
        },
        "user": {
            "env_X": [0.02, 0.02]
        }
    }
    turn_context = {
        "skill": {
            "objects": {
                "Turnable": "generic_insertable",
                "GoalOrientation": "automatica_turn_goal"
            },
            "turn_speed": [0.1, 0.5],
            "turn_acc": [0.5, 1.0]},
        "control": {
            "control_mode": 0,
            "cart_imp": {
                "K_x": [665, 665, 665, 173, 173, 173]
            }
        },
        "user": {
            "env_X": [0.03, 0.04]
        }
    }
    turn_back_context = {
        "skill": {
            "objects": {
                "Turnable": "generic_insertable",
                "GoalOrientation": "generic_container"
            },
            "turn_speed": [0.1, 0.5],
            "turn_acc": [0.5, 1.0]},
        "control": {
            "control_mode": 0,
            "cart_imp": {
                "K_x": [665, 665, 665, 173, 173, 173]
            }
        },
        "user": {
            "env_X": [0.03, 0.04]
        }
    }
    extraction_context = {
        "skill": {
            "objects": {
                "Container": "generic_container",
                "ExtractTo": "generic_container_approach",
                "Extractable": "generic_insertable"
            },
            "extraction_speed": [0.5, 1],
            "extraction_acc": [1, 4],
            "search_a": [3, 1.7, 3.6, 0.64, 0.85, 0],
            "search_f": [0.77, 0, 0.8, 0.16, 0.58, 0],
            "stuck_dx_thr": 0.09
        },
        "control": {
            "control_mode": 0,
            "cart_imp": {
                "K_x": [702, 276, 1798, 110, 131, 45]
            }
        },
        "user": {
            "env_X": [0.03, 0.08]
        }
    }
    t = Task(robots[0])
    t.add_skill("insertion", "TaxInsertion", insertion_context)
    # t.add_skill("turn", "TaxTurn", turn_context)
    # t.add_skill("turn_back", "TaxTurn", turn_back_context)
    t.add_skill("extraction", "TaxExtraction", extraction_context)
    t.start()
    t.wait()

    result = start_task(robots[0], "MoveToJointPose", {
        "parameters": {
            "pose": "automatica_telepresence",
            "speed": 1,
            "acc": 2
        }
    })
    wait_for_task(robots[0], result["result"]["task_uuid"])

    wiggle_context = {
        "skill": {
            "dX_fourier_a_a": [0, 0.05, 0.1, 0, 0, 0],
            "dX_fourier_a_phi": [0, 0.71, 0.71, 0, 0, 0],
            "dX_fourier_a_f": [0, 1, 0.5, 0, 0, 0],
            "dX_fourier_b_a": [0, 0, 0, 0, 0, 0],
            "dX_fourier_b_f": [0, 0, 0, 0, 0, 0],
            "use_EE": True,
            "time_max": 10
        },
        "control": {
            "control_mode": 0
        }
    }

    t = Task(robots[0])
    t.add_skill("fail", "GenericWiggleMotion", wiggle_context)
    t.start(False)
    result = t.wait()


def teach_insertable(robot: str):
    input("Press key to start teaching.")
    call_method(robot, 12000, "set_grasped_object", {"object": "generic_insertable"})
    input("Teach approach")
    call_method(robot, 12000, "teach_object", {"object": "generic_container_approach"})
    input("Teach container")
    call_method(robot, 12000, "teach_object", {"object": "generic_container"})


def delete_results(agents, tags):
    delete_local_results(agents,"ml_results","insert_object", tags)
    delete_local_knowledge(agents,"ml_results","insert_object", tags)


def command_collective(cmd: str):
    threads = []
    for r in robots:
        robot = r
        threads.append(Thread(target=call_method, args=(robot, 12000, cmd,)))
        threads[-1].start()

    for t in threads:
        t.join()
