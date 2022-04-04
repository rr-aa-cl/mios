#!/usr/bin/python3 -u
import time
import socket
from threading import Thread
from utils.ws_client import *
from utils.experiment_wizard import *
from services.svm import SVMConfiguration
from definitions.taxonomy_templates import insertion

from definitions.templates import *
from definitions.cost_functions import *
from definitions.service_configs import *


robots = [ 
            "collective-panda-prime", 
            #"collective-panda-001", 
            "collective-panda-002",
            "collective-panda-003",
            "collective-panda-004", 
            "collective-panda-008",
            #"collective-panda-009"
            ]


def get_ip(hostname: str):
    print("hostname: ",hostname)
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
        #print(self.skill_context)
        print("start ", self.skill_names, " at ", self.robot)
        response = start_task(self.robot, "GenericTask", parameters)

        self.task_uuid = response["result"]["task_uuid"]

    def wait(self):
        result = wait_for_task(self.robot, self.task_uuid)
        print("Task execution took " + str(time.time() - self.t_0) + " s.")
        return result


def learn_insertion(robot: str, approach: str, insertable: str, container: str, tags: list, knowledge=None,
                    wait: bool=True):
    pd = InsertionFactory([robot], TimeMetric("insertion", {"time": 5}),
                          {"Insertable": insertable, "Container": container,
                           "Approach": approach}).get_problem_definition(insertable)
    sc = SVMLearner().get_configuration()
    learn_task(robot, pd, sc, tags, knowledge=knowledge)


def learn_task(robot:str, problem_definition: ProblemDefinition, service_config: ServiceConfiguration, tags: list,
               n_iterations: int = 10, keep_record: bool = False, knowledge = None, wait: bool = False):
    start_experiment(robot, [robot], problem_definition, service_config, 10, knowledge=knowledge, tags=tags,
                     keep_record=False, wait=wait)

def grab_insertable(robot:str):
    call_method(robot, 12000, "release_object")
    path_to_default_context = os.getcwd() + "/../python/taxonomy/default_contexts/"
    t1 = Task(robot)
    t2 = Task(robot)
    f = open(path_to_default_context + "move_joint.json")
    move_context = json.load(f)
    move_context["skill"]["objects"]["goal_pose"] = "generic_container_above"
    f = open(path_to_default_context + "move_cart.json")
    move_fine_context = json.load(f)
    move_fine_context["skill"]["objects"]["GoalPose"] = "generic_insertable"

    f = open(path_to_default_context + "extraction.json")
    extraction_context = json.load(f)
    extraction_context["skill"]["objects"]["Extractable"] = "generic_insertable"
    extraction_context["skill"]["objects"]["Container"] = "generic_container"
    extraction_context["skill"]["objects"]["ExtractTo"] = "generic_container_approach"


    #execution
    t1.add_skill("move", "MoveToPoseJoint", move_context)
    t1.add_skill("move_fine", "TaxMove", move_fine_context)
    success_moving = False
    success_grasping = False
    while success_grasping == False:
        while success_moving == False:
            t1.start()
            success_moving = t1.wait()["result"]["task_result"]["success"]
            if not success_moving:
                print(robot, ": moving success = ", success_moving)
        success_moving = False
        result = call_method(robot, 12000, "grasp_object", {"object": "generic_insertable"})
        #call_method(robot, 12000,"set_grasped_object", {"object": "generic_insertable"})
        success_grasping  = result["result"]["result"]
        if not success_grasping:
            print(robot, " grasping success = ", success_grasping)


    t2.add_skill("extraction", "TaxExtraction", extraction_context)
    t2.start()
    print(t2.wait())
    return True
    success_extraction = False
    while success_extraction == False:
        t2.start()
        success_extraction = t2.wait()["result"]["task_result"]["success"]
        if not success_extraction:
            print(robot, " extraction success: ", success_extraction)

def place_insertable(robot):
    path_to_default_context = os.getcwd() + "/../python/taxonomy/default_contexts/"
    t0 = Task(robot)
    t1 = Task(robot)
    t2 = Task(robot)

    f = open(path_to_default_context + "insertion.json")
    insertion_context = json.load(f)
    insertion_context["skill"]["objects"]["Insertable"] = "generic_insertable"
    insertion_context["skill"]["objects"]["Container"] = "generic_container"
    insertion_context["skill"]["objects"]["Approach"] = "generic_container_approach"

    insertion_context["skill"]["p2"]["search_a"]= [10, 10, 0, 2, 2, 0]
    insertion_context["skill"]["p2"]["search_f"] = [1, 0.75, 0, 1, 0.75, 0]
    insertion_context["skill"]["p2"]["f_push"] = [0, 0, 20, 0, 0, 0]

    f = open(path_to_default_context + "move_cart.json")
    move_fine_context = json.load(f)
    move_fine_context["skill"]["objects"]["GoalPose"] = "generic_container_above"
    f = open(path_to_default_context + "move_joint.json")
    move_context = json.load(f)
    move_context["skill"]["objects"]["goal_pose"] = "generic_approach"
    #t0.add_skill("move", "MoveToPoseJoint", move_context)
    #t0.add_skill("move_fine", "TaxMove", move_fine_context)
    #t0.start()
    #result = t0.wait()

    t1.add_skill("insertion", "TaxInsertion", insertion_context)
    t1.start()
    result = t1.wait()
    if result["result"]["task_result"]["success"] == True:
        call_method(robot, 12000, "release_object")
    else:
        return False
    t2.add_skill("move_fine", "TaxMove", move_fine_context)
    #t2.add_skill("move", "MoveToPoseJoint", move_context)
    t2.start()
    t2.wait()


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
            "p0": {
                "dX_d": [0.2, 0.5],
                "ddX_d": [0.5, 1],
                "DeltaX": [0, 0, 0, 0, 0, 0],
                "K_x": [500, 500, 500, 100, 100, 100]
            },
            "p1": {
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
                "K_x": [500, 500, 500, 100, 100, 100]
            },
            "p2": {
                "search_a": [0, 0, 0, 0, 0, 0],
                "search_f": [0, 0, 0, 0, 0, 0],
                "search_phi": [0, 0, 0, 0, 0, 0],
                "K_x": [500, 500, 0, 100, 100, 100],
                "f_push": [0, 0, 2, 0, 0, 0],
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1]
            },
            "p3": {
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
                "f_push": 15,
                "K_x": [500, 500, 0, 100, 100, 100]
            },
            "time_max": 5
        },
        "control": {
            "control_mode": 0,
            "cart_imp": {
                "K_x": [500, 500, 500, 100, 100, 100]
            }
        }
    }
    move_up_context = {
        "skill": {
            "objects": {
                "GoalPose": "EndEffector"
            },
            "p0": {
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
                "K_x": [1500, 1500, 1500, 150, 150, 150],
                "T_T_EE_g_offset": [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0.05, 1]
            }
        },
        "control": {
            "control_mode": 0
        },
        "user": {
            "env_X": [0.3, 0.3, 0.3, 0.08, 0.08, 0.08]
        }
    }
    extraction_context = {
        "skill": {
            "objects": {
                "Container": "generic_container",
                "ExtractTo": "generic_container_approach",
                "Extractable": "generic_insertable"
            },
            "p0": {
                "search_a": [5, 5, 0, 1, 1, 0],
                "search_f": [2, 1.5, 0, 1, 0.75, 0],
                "K_x": [50, 50, 1500, 50, 50, 100],
                "dX_d": [0.2, 0.5],
                "ddX_d": [0.5, 1]
            },
            "p1": {
                "dX_d": [0.2, 0.5],
                "ddX_d": [0.5, 1],
                "K_x": [1000, 1000, 1500, 100, 100, 100]
            }
        },
        "control": {
            "control_mode": 0,
            "cart_imp": {
                "K_x": [702, 276, 1798, 110, 131, 45]
            }
        },
        "user": {
            "env_X": [0.02, 0.02, 0.02, 0.08, 0.08, 0.08]
        }
    }

    insertion_context1 = copy.deepcopy(insertion_context)
    insertion_context1["skill"]["p0"]["DeltaX"] = [0.01, -0.005, 0, 10, 5, 0]
    insertion_context1["skill"]["p2"]["search_a"] = [3, 3, 0, 0, 0, 0]
    insertion_context1["skill"]["p2"]["search_f"] = [1, 0.75, 0, 0, 0, 0]

    insertion_context2 = copy.deepcopy(insertion_context)
    insertion_context2["skill"]["p0"]["DeltaX"] = [-0.002, 0.005, 0, 10, -10, 0]
    insertion_context2["skill"]["p2"]["dX_d"] = [0.01, 0.01]
    insertion_context2["skill"]["p2"]["search_a"] = [8, 8, 0, 0, 0, 0]
    insertion_context2["skill"]["p2"]["search_f"] = [1, 0.75, 0, 0, 0, 0]
    insertion_context3 = copy.deepcopy(insertion_context)
    insertion_context3["skill"]["p0"]["DeltaX"] = [-0.01, 0.005, 0, 0.0, -7, 0]
    insertion_context3["skill"]["p2"]["dX_d"] = [0.01, 0.01]
    insertion_context3["skill"]["p2"]["search_a"] = [8, 8, 0, 0, 0, 0]
    insertion_context3["skill"]["p2"]["search_f"] = [1, 0.75, 0, 0, 0, 0]
    insertion_context3["skill"]["p2"]["K_x"] = [100, 100, 0, 50, 50, 50]


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
    move_up_context2["skill"]["p0"]["T_T_EE_g_offset"][14] = 0.2
    t.add_skill("move3", "TaxMove", move_up_context2)
    t.add_skill("fail", "GenericWiggleMotion", wiggle_context)
    t.start(False)
    result = t.wait()


def demo_part_2():

    result = start_task(robots[0], "MoveToJointPose", {
        "parameters": {
            "pose": "telepresence_init",
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
    threads = []
    for a in agents:
        threads.append(
            Thread(target=grab_insertable, args=(a,))
        )
        threads[-1].start()
    print("grabbing insertables...")
    for t in threads:
        t.join()
    print("all insertables grabbed.")
    input("continue")
    tag = "demo_learning"
    knowledge = {"mode": "none", "kb_location": robots[0], "kb_tags": [tag]}
    learning_services = []
    threads = []
    for a in agents:
        threads.append(
            Thread(target=learn_insertion, args=(a, "generic_container_approach", "generic_insertable", "generic_container", ["demo"],
                       knowledge , False, )))
        threads[-1].start()
        learning_services.append(ServerProxy("http://" + a + ":8000", allow_none=True))

    input("Press Enter to stop learning.")
    for s in learning_services:
        s.stop_service()
    for s in learning_services:
        while s.is_busy() is True:
            time.sleep(1)

#        pd = insertion("generic_insertable", "generic_container", "generic_container_approach")
#        tags = [tag, a, "automatica_demo"]
#        threads.append(
#            Thread(target=start_single_experiment, args=(a, [a], pd, service_config, 1, tags, knowledge, False,)))
#        threads[-1].start()
#        j += 1#
#
#    input("Press key to stop.")
#    for a in agents:
#        s = ServerProxy("http://" + a + ":8000", allow_none=True)
#        s.stop_service()
#        stop_task(a)


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
            "p0": {
                "dX_d": [0.2, 0.5],
                "ddX_d": [0.5, 1],
                "DeltaX": [0.005, 0, 0, 0, 10, 0],
                "K_x": [1500, 1500, 1500, 100, 100, 100]
            },
            "p1": {
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
                "K_x": [1500, 1500, 1500, 100, 100, 100]
            },
            "p2": {
                "search_a": [15, 15, 4, 1, 1.5, 0],
                "search_f": [2, 1, 0.6, 0.7, 0.87, 0],
                "search_phi": [0, 0, 0, 0, 0, 0],
                "K_x": [500, 500, 0, 100, 100, 100],
                "f_push": [0, 0, 15, 0, 0, 0],
                "dX_d": [0.15, 0.3],
                "ddX_d": [0.5, 1]
            },
            "p3": {
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
                "f_push": 15,
                "K_x": [500, 500, 0, 100, 100, 100]
            }
        },
        "control": {
            "control_mode": 0,
            "cart_imp": {
                "K_x": [1004, 1536, 1617, 100, 100, 68]
            }
        },
        "user": {
            "env_X": [0.002, 0.002, 0.002, 0.02, 0.02, 0.02]
        }
    }
    extraction_context = {
        "skill": {
            "objects": {
                "Container": "generic_container",
                "ExtractTo": "generic_container_approach",
                "Extractable": "generic_insertable"
            },
            "p0": {
                "search_a": [5, 5, 0, 1, 1, 0],
                "search_f": [2, 1.5, 0, 1, 0.75, 0],
                "K_x": [50, 50, 1500, 50, 50, 100],
                "dX_d": [0.2, 0.5],
                "ddX_d": [0.5, 1]
            },
            "p1": {
                "dX_d": [0.2, 0.5],
                "ddX_d": [0.5, 1],
                "K_x": [1000, 1000, 1500, 100, 100, 100]
            }
        },
        "control": {
            "control_mode": 0,
            "cart_imp": {
                "K_x": [702, 276, 1798, 110, 131, 45]
            }
        },
        "user": {
            "env_X": [0.01, 0.01, 0.01, 0.02, 0.02, 0.02]
        }
    }
    t = Task(robots[0])
    t.add_skill("insertion", "TaxInsertion", insertion_context)
    t.add_skill("extraction", "TaxExtraction", extraction_context)
    t.start()
    t.wait()

    result = start_task(robots[0], "MoveToJointPose", {
        "parameters": {
            "pose": "telepresence_init",
            "speed": 1,
            "acc": 2
        }
    })
    wait_for_task(robots[0], result["result"]["task_uuid"])

    wiggle_context = {
        "skill": {
            "dX_fourier_a_a": [0, 0.05, 0.05, 0, 0, 0],
            "dX_fourier_a_phi": [0, 0.0, 0.0, 0, 0, 0],
            "dX_fourier_a_f": [0, 0.5, 1, 0, 0, 0],
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
    t.add_skill("fail", "GenericWiggleMotion", wiggle_context)
    t.start(False)
    result = t.wait()


def teach_insertable(robot: str):
    input("Press key to start teaching. [Pose above container, without object]")
    call_method(robot, 12000, "teach_object", {"object": "generic_container_above"})
    input("Teach where to grab object. ")
    call_method(robot, 12000, "teach_object", {"object": "generic_insertable"})
    call_method(robot, 12000, "set_grasped_object", {"object": "generic_insertable"})
    input("Teach approach, with grabbed object")
    call_method(robot, 12000, "teach_object", {"object": "generic_container_approach"})
    input("Teach container, with grabbed object")
    call_method(robot, 12000, "teach_object", {"object": "generic_container"})


def command_collective(cmd: str, args: dict = {}):
    threads = []
    for r in robots:
        robot = r
        threads.append(Thread(target=call_method, args=(robot, 12000, cmd, args,)))
        threads[-1].start()

    for t in threads:
        t.join()

def move_collective(location):
    threads = []
    for r in robots:
        robot = r
        threads.append(Thread(target=move, args=(robot, location,)))
        threads[-1].start()

    for t in threads:
        t.join()

def move(robot, location):
    context = {
        "skill": {
            "p0":{
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
                "K_x": [2000, 2000, 2000, 250, 250, 250],

            },
            "objects": {
                    "GoalPose": location
                }
        },
        "control": {
            "control_mode": 2
        }
    }
    t = Task(robot)
    t.add_skill("move", "TaxMove", context)
    t.start()
    result = t.wait()
    print("Result: " + str(result))