#!/usr/bin/python3 -u
import time
import socket
from threading import Thread
from utils.database import delete_local_knowledge
from services.knowledge import Knowledge
#from ml_service.utils.database import delete_local_knowledge, delete_local_results
from utils.ws_client import *
from utils.experiment_wizard import *
from services.svm import SVMConfiguration
from definitions.taxonomy_templates import insertion

from definitions.templates import *
from definitions.cost_functions import *
from definitions.service_configs import *
from knowledge_processor.knowledge_manager import KnowledgeManager

from utils.taxonomy_utils import download_best_result, download_best_result_2

import run_experiments


from mongodb_client.mongodb_client import MongoDBClient
import random

from xmlrpc.server import SimpleXMLRPCServer
from socketserver import ThreadingMixIn




robots = [ 
            "collective-panda-prime", 
            #"collective-panda-001", 
            "collective-panda-002",
            "collective-panda-003",
            "collective-panda-004", 
            "collective-panda-008"
            #"collective-panda-009"
            ]


def get_ip(hostname: str):
    print("hostname: ",hostname)
    return socket.gethostbyname(hostname)


class MySimpleXMLRPCServer(SimpleXMLRPCServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.register_function(self.quit)
    
    def quit(self):
        self._BaseServer__shutdown_request = True
        return 0

class InterfaceServer(ThreadingMixIn, MySimpleXMLRPCServer):
    pass
class Publisher:
    def __init__(self, port=8008):
        self.port = port
        self.status = {}
        self.rpc_server = InterfaceServer(("0.0.0.0", self.port), allow_none=True)
        self.publisher_thread = Thread(self.start_publisher(),daemon=False)

    def run(self):
        self.publisher_thread.start()
    def start_publisher(self):
        self.rpc_server.register_function(self.status, "status")
        self.rpc_server.handle_request()  #serve_forever()

    def status(self):
        return self.status
    
    def push_status(self, key, status):
        self.status[key] = status

#p = Publisher()
#p.run()


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



def delete_local_results(agents: list, db: str, skill_class: str, tags: list):
    for a in agents:
        client = MongoDBClient(a)
        client.remove(db, skill_class, {"meta.tags": tags })

def learn_insertion(robot: str, approach: str, insertable: str, container: str, tags: list, knowledge=None,
                    wait: bool=True):
    pd = InsertionFactory([robot], TimeMetric("insertion", {"time": 5}),
                          {"Insertable": insertable, "Container": container,
                           "Approach": approach}).get_problem_definition(insertable)
    sc = SVMLearner().get_configuration()
    sc.n_immigrant = 2
    # sc = CMAESLearner().get_configuration()
    learn_task(robot, pd, sc, tags, knowledge=knowledge)


def learn_task(robot:str, problem_definition: ProblemDefinition, service_config: ServiceConfiguration, tags: list,
               n_iterations: int = 1, keep_record: bool = False, knowledge = None, wait: bool = False):
    start_experiment(robot, [robot], problem_definition, service_config, 1, knowledge=knowledge, tags=tags,
                     keep_record=False, wait=wait)

def grasp_insertable_collective():
    threads = []
    for r in robots:
        robot = r
        threads.append(Thread(target=grasp_insertable, args=(robot,)))
        threads[-1].start()

    for t in threads:
        t.join()

def grasp_insertable(robot:str, insertable = "generic_insertable"):
    print("current object grasped: ",call_method(robot,12000,"get_state")["result"]['grasped_object'] )
    if call_method(robot,12000,"get_state")["result"]['grasped_object'] == 'NullObject':
        call_method(robot, 12000, "release_object")
    else:
        print("I am already grasping something")
        return 0
    #call_method(robot, 12000, "home_gripper")
    call_method(robot,12000,"move_gripper",{"width":0.06,"force":100,"epsilon_outer":1,"speed":100})
    path_to_default_context = os.getcwd() + "/../python/taxonomy/default_contexts/"
    t1 = Task(robot)
    t2 = Task(robot)
    f = open(path_to_default_context + "move_joint.json")
    move_context = json.load(f)
    move_context["skill"]["objects"]["goal_pose"] = "generic_container_above"
    f = open(path_to_default_context + "move_cart.json")
    move_fine_context = json.load(f)
    move_fine_context["skill"]["objects"]["GoalPose"] = insertable

    f = open(path_to_default_context + "extraction.json")
    extraction_context = json.load(f)
    extraction_context["skill"]["objects"]["Extractable"] = insertable
    extraction_context["skill"]["objects"]["Container"] = "generic_container"
    extraction_context["skill"]["objects"]["ExtractTo"] = "generic_container_approach"


    #execution
    t1.add_skill("move", "MoveToPoseJoint", move_context)
    t1.add_skill("move_fine", "TaxMove", move_fine_context)
    success_moving = False
    success_grasping = False
    count = 0
    while success_grasping == False:
        while success_moving == False:
            call_method(robot, 12000, "move_gripper",{"width":0.07,"speed":1,"force":100})
            t1.start()
            success_moving = t1.wait()["result"]["task_result"]["success"]
            if not success_moving:
                print(robot, ": moving success = ", success_moving)
            count += 1
            if count > 2:
                continue
        success_moving = False
        result = call_method(robot,12000,"grasp",{"width":0,"force":100,"epsilon_outer":1,"speed":100}) #call_method(robot, 12000, "grasp_object", {"object": "generic_insertable"})
        call_method(robot,12000,"set_grasped_object",{"object":insertable})
        #call_method(robot, 12000,"set_grasped_object", {"object": "generic_insertable"})
        success_grasping  = result["result"]["result"]
        if not success_grasping:
            print(robot, " grasping success = ", success_grasping)
        count += 1
        if count > 12:
            continue


    t2.add_skill("extraction", "TaxExtraction", extraction_context)
    t2.start()
    print(t2.wait())
    return True


def place_insertable(robot):
    call_method(robot, 12000, "set_grasped_object", {"object": "generic_insertable"})
    path_to_default_context = os.getcwd() + "/../python/taxonomy/default_contexts/"
    t0 = Task(robot)
    t1 = Task(robot)
    t2 = Task(robot)
    move(robot,"generic_container_approach")
    f = open(path_to_default_context + "insertion.json")
    insertion_context = json.load(f)
    insertion_context["skill"]["objects"]["Insertable"] = "generic_insertable"
    insertion_context["skill"]["objects"]["Container"] = "generic_container"
    insertion_context["skill"]["objects"]["Approach"] = "generic_container_approach"

    insertion_context["skill"]["p2"]["search_a"]= [10, 10, 0, 2, 2, 0]
    insertion_context["skill"]["p2"]["search_f"] = [1, 0.75, 0, 1, 0.75, 0]
    insertion_context["skill"]["p2"]["f_push"] = [0, 0, 20, 0, 0, 0]
    if robot == "collective-panda-002":
        insertion_context["skill"]["p2"]["f_push"] = [0, 0, 8, 0, 0, 0]

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
    call_method(robot, 12000, "home_gripper")


def run_demo():
    input("Start part I")
    demo_part_1()
    input("Start part II")
    demo_part_2()
    input("Start part III")
    demo_part_3()
    input("Start IV")
    demo_part_4()

def run_demo_looped():
    try:
        while(True):
            demo_part_1()
            demo_part_2_looped()
            demo_part_3_looped()
            demo_part_4()
    except KeyboardInterrupt:
        stop_service_collective()
        command_collective("stop_task")
        place_insertable(robots[0])
        move_collective("default_pose")
        pass

def stop_services():
    learning_services = []
    for a in robots:
        learning_services.append(ServerProxy("http://" + a + ":8000", allow_none=True))
    for s in learning_services:
        s.stop_service()
    for s in learning_services:
        while s.is_busy() is True:
            time.sleep(1)

def preparation():
    
    robots = [  "collective-panda-prime",
                "collective-panda-002",
                "collective-panda-003",
                "collective-panda-004",
                "collective-panda-008"]
    tags = ["demo_learning"]
    delete_local_knowledge(robots, "local_knowledge", "insertion", tags)
    insertables = ["generic_insertable","generic_insertable","generic_insertable","generic_insertable","generic_insertable"]
    containers = ["generic_container","generic_container","generic_container","generic_container","generic_container"]
    approaches = [k+"_approach" for k in containers]
    n_immigrants_vector = [4]

    
    knowledge_source = Knowledge()
    knowledge_source.kb_location = "collective-dev-001"
    # delete results with same tags:
    for n_immigrant in n_immigrants_vector:
            threads = []
            tags.append("n_immigrants="+str(n_immigrant))
            for i in range(len(robots)):
                pd = InsertionFactory([robots[i]], TimeMetric("insertion", {"time": 5}),
                                    {"Insertable": insertables[i], "Container": containers[i],
                                    "Approach": approaches[i]}).get_problem_definition(insertables[i])
                if robots[i] == "collective-panda-008":  # increase the limits for HDMI_plug
                    pd.domain.limits["p2_f_push_z"] = (0, 25)
                sc = SVMLearner().get_configuration()
                sc.n_immigrant = n_immigrant
                sc.batch_synchronisation = False
                print(sc.to_dict())
                threads.append(Thread(target=learn_task, args=(robots[i], pd, sc, tags, 1, True, knowledge_source.to_dict(), True)))
                threads[-1].start()
            for t in threads:
                t.join()
            tags.pop(-1)
            kb = ServerProxy("http://" + knowledge_source.kb_location+ ":8001", allow_none=True)
            kb.clear_memory()
    print("\nfinished :)\n")


def demo_part_1():
    #for r in robots:
    #    publisher.push_status(r,"delete knowledge")
   # grab_insertable(robots[0])

    #km = KnowledgeManager("collective-panda-003.local")
    #client = MongoDBClient("collective-panda-003.local")
    #knowledge = km.get_knowledge_by_filter(client, "ml_results", "insertion", {"meta.tags": {"$all": ["eth_plut", "contact_forces", "n7"]}})
    #print(knowledge)
    #call_method(robots[0], 12000, "set_grasped_object", {"object": "generic_insertable"})
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
    #t.add_skill("move3", "TaxMove", move_up_context2)
    t.add_skill("fail", "GenericWiggleMotion", wiggle_context)
    t.start(False)
    result = t.wait()


    #publisher.push_status(robots[0],"learning")
    #learn_insertion(robots[0],"generic_container_approach","generic_insertable","generic_container",["dummy"],knowledge=knowledge)
    #time.sleep(16)
    #s = ServerProxy("http://" + robots[0]+ ":8000", allow_none=True)
    #s.stop_service()
    #while s.is_busy() is True:
    #    time.sleep(1)
    #while call_method(robots[0],12000,"get_state")["result"]["current_task"] != "IdleTask":
    ##    time.sleep(1)
    #t.start(False)
    #result = t.wait()
    #publisher.push_status(robots[0],"Ready")
    delete_local_results([robots[0]], "ml_results","insertion",["dummy"])



def demo_part_2():
    #publisher.push_status(robots[0],"telepresence: leader")
    #for r in robots[1:]:
    #    publisher.push_status(r, "telepresence: follower")
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


def demo_part_2_looped():
    #publisher.push_status(robots[0],"telepresence: leader")
    #for r in robots[1:]:
    #    publisher.push_status(r, "telepresence: follower")

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

    time.sleep(10)
    for ip in ip_slaves:
        stop_task(ip)

    stop_task(ip_master)

def demo_part_3():
    #publisher.push_status(robots[0],"IdleTask")
    #for r in robots[1:]:
    #    publisher.push_status(r, "learning")

    base_batch_size_experiment = 5
    n_trials_experiment = 180
    agents = robots[1:]
    threads = []
    # for a in agents:
    #     threads.append(
    #         Thread(target=grab_insertable, args=(a,))
    #     )
    #     threads[-1].start()
    # print("grabbing insertables...")
    # for t in threads:
    #     t.join()
    # print("all insertables grabbed.")
    #input("continue")
    knowledge_1 = Knowledge()
    knowledge_1.mode = "global"
    knowledge_1.scope = ["demo2"]  #
    knowledge_1.kb_location = robots[0]
    knowledge_2 = Knowledge()
    knowledge_2.mode = "local"
    knowledge_2.scope = "demo_learning"
    learning_services = []
    threads_1 = []
    threads_2 = []
    for a in agents:
        threads_1.append(
            Thread(target=learn_insertion, args=(a, "generic_container_approach", "generic_insertable", "generic_container", ["demo2"],
                       knowledge_1 , False, )))
        threads_1[-1].start()
        learning_services.append(ServerProxy("http://" + a + ":8000", allow_none=True))

    #input("Press Enter to stop learning. part 1")
    try:
        time.sleep(30)
        print("start knowledge sharing")
        indexes = list(range(len(learning_services)))
        random.shuffle(indexes)
        for i in indexes:
            print("stopping ",i)
            time.sleep(random.randint(10, 15))
            print("here")
            learning_services[i].stop_service()
            print("agent stopped",i)
            while learning_services[i].is_busy() is True:
                time.sleep(1)
                print("waiting for",i)
            print("starting",i)
            threads_2.append(
                Thread(target=learn_insertion, args=(agents[i], "generic_container_approach", "generic_insertable", "generic_container", ["demo2"],
                        knowledge_2 , False, )))
            threads_2[-1].start()
    except KeyboardInterrupt:
        pass
    # for s in learning_services:
    #     while s.is_busy() is True:
    #         time.sleep(1)

    # knowledge = {"mode": "local", "type": "similar", "kb_location": robots[0], "kb_tags": [tag], "scope":[tag]}
    # learning_services = []
    # threads = []
    # for a in agents:
    #     threads.append(
    #         Thread(target=learn_insertion, args=(a, "generic_container_approach", "generic_insertable", "generic_container", ["demo"],
    #                    knowledge , False, )))
    #     threads[-1].start()
    #     learning_services.append(ServerProxy("http://" + a + ":8000", allow_none=True))

    input("Press Enter to stop learning.")
    for s in learning_services:
        s.stop_service()
    for s in learning_services:
        while s.is_busy() is True:
            time.sleep(1)

    # path_to_default_context = os.getcwd() + "/../python/taxonomy/default_contexts/"
    # f = open(path_to_default_context + "extraction.json")
    # extraction_context = json.load(f)
    # extraction_context["skill"]["objects"]["Extractable"] = "generic_insertable"
    # extraction_context["skill"]["objects"]["Container"] = "generic_container"
    # extraction_context["skill"]["objects"]["ExtractTo"] = "generic_container_approach"
    # tasks = []
    # for r in agents:
    #     tasks.append(Task(r))
    #     tasks[-1].add_skill("extraction", "TaxExtraction", extraction_context)
    #     tasks[-1].start(False)
    # for t in tasks:
    #     t.wait()

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
def demo_part_3_looped():
    #publisher.push_status(robots[0],"IdleTask")
    #for r in robots[1:]:
    #    publisher.push_status(r, "learning")

    base_batch_size_experiment = 5
    n_trials_experiment = 180
    agents = robots[1:]
    threads = []
    #for a in agents:
    #    threads.append(
    #        Thread(target=grab_insertable, args=(a,))
    #    )
    #    threads[-1].start()
    #print("grabbing insertables...")
    #for t in threads:
    #    t.join()
    #print("all insertables grabbed.")
    #input("continue")
    tag = "demo_learning"
    knowledge_1 = {"mode": "global", "type": "similar", "kb_location": robots[0], "kb_tags": [tag], "scope":[tag]}
    knowledge_2 = {"mode": "local", "type": "similar", "kb_location": robots[0], "kb_tags": [tag], "scope":[tag]}
    learning_services = []
    threads_1 = []
    threads_2 = []
    for a in agents:
        threads_1.append(
            Thread(target=learn_insertion, args=(a, "generic_container_approach", "generic_insertable", "generic_container", ["demo2"],
                       knowledge_1 , False, )))
        threads_1[-1].start()
        learning_services.append(ServerProxy("http://" + a + ":8000", allow_none=True))

    #input("Press Enter to stop learning. part 1")
    try:
        time.sleep(120)
        # print("start knowledge sharing")
        indexes = list(range(len(learning_services)))
        random.shuffle(indexes)
        count = 0
        for i in indexes:
            
            # print("stopping ",i)
            if count == 0:
                time.sleep(random.randint(10, 15))
                count += 1
            else:
                time.sleep(random.randint(15,20))

            learning_services[i].stop_service()
            while learning_services[i].is_busy() is True:
                time.sleep(1)

            threads_2.append(
                Thread(target=learn_insertion, args=(agents[i], "generic_container_approach", "generic_insertable", "generic_container", ["demo2"],
                        knowledge_2 , False, )))
            threads_2[-1].start()
    except KeyboardInterrupt:
        pass

    time.sleep(45)
    for s in learning_services:
        s.stop_service()
    for s in learning_services:
        while s.is_busy() is True:
            time.sleep(1)

    # path_to_default_context = os.getcwd() + "/../python/taxonomy/default_contexts/"
    # f = open(path_to_default_context + "extraction.json")
    # extraction_context = json.load(f)
    # extraction_context["skill"]["objects"]["Extractable"] = "generic_insertable"
    # extraction_context["skill"]["objects"]["Container"] = "generic_container"
    # extraction_context["skill"]["objects"]["ExtractTo"] = "generic_container_approach"
    # tasks = []
    # for r in agents:
    #     tasks.append(Task(r))
    #     tasks[-1].add_skill("extraction", "TaxExtraction", extraction_context)
    #     tasks[-1].start(False)
    # for t in tasks:
    #     t.wait()

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
    #publisher.push_status(robots[0],"learning")
    #for r in robots[1:]:
    #    publisher.push_status(r, "IdleTask")
        
    tag = "demo_learning"
    #insertion_context = download_best_result("collective-panda-002","ml_results","insertion","generic_insertable",[])
    
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
                "f_push": [0, 0, 20, 0, 0, 0],
                "dX_d": [0.15, 0.3],
                "ddX_d": [0.5, 1]
            },
            "p3": {
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
                "f_push": 25,
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

    #insertion_context = download_best_result("collective-panda-002","ml_results","insertion","generic_insertable",[])
    insertion_context = download_best_result("collective-panda-prime","ml_results","insertion","generic_insertable",[])

    print(insertion_context)

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
    insertion_result = t.wait()

    result = start_task(robots[0], "MoveToJointPose", {
            "parameters": {
                "pose": "telepresence_init",
                "speed": 1,
                "acc": 2
            }
        })
    wait_for_task(robots[0], result["result"]["task_uuid"])

    if insertion_result["result"]["task_result"]["success"]:
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
        t.add_skill("success", "GenericWiggleMotion", wiggle_context)
        t.start(False)
    
        result = t.wait()
    
    #place_insertable_collective()
    #place_insertable(robots[0])
    #command_collective("release_object")

    move_collective("default_pose")
    delete_local_results(robots, "ml_results","insertion",["demo2"])
    #command_collective("home_gripper")
    
def stop_service_collective():
    learning_services = []
    for r in robots:
        learning_services.append(ServerProxy("http://" + r+ ":8000", allow_none=True))
    for s in learning_services:
        s.stop_service()
    for s in learning_services:
        while s.is_busy() is True:
            time.sleep(1)

def stop_service(robot):
    learning_services = []
    for r in robots:
        learning_services.append(ServerProxy("http://" + robot+ ":8000", allow_none=True))
    for s in learning_services:
        s.stop_service()
    for s in learning_services:
        while s.is_busy() is True:
            time.sleep(1)

def teach_insertable(robot: str):
    input("Press key to start teaching. [Pose above container, without object]")
    call_method(robot, 12000, "teach_object", {"object": "generic_container_above"})
    input("Teach where to grab object. ")
    call_method(robot, 12000, "teach_object", {"object": "generic_insertable"})
    #call_method(robot, 12000, "grasp_object", {"object": "generic_insertable"})
    call_method(robot, 12000, "grasp", {"width":0,"speed":100,"force":100,"epsilon_outer":1})
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

def place_insertable_collective():
    threads = []
    for r in robots:
        robot = r
        threads.append(Thread(target=place_insertable, args=(robot,)))
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
