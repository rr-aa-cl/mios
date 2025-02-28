import time
from xmlrpc.client import ServerProxy
from utils.ws_client import *
from utils.helper_functions import *
from threading import Thread
import copy
import os

from services.knowledge import Knowledge
from definitions.service_configs import *
from definitions.templates import *
from definitions.cost_functions import *
from utils.taxonomy_utils import *
from definitions.cost_functions import *
from run_experiments import learn_single_task
from utils.taxonomy_utils import download_best_result_tags, download_best_result, download_knowldge_to_context

robots = {  "collective-panda-prime": ["key_door"],
            "collective-panda-002": ["key_abus_e30"],
            "collective-panda-003": ["key_padlock"],
            "collective-panda-004": ["cylinder_40"],
            "collective-panda-008": ["HDMI_plug"]}
path_to_default_context = os.getcwd() + "/../python/taxonomy/default_contexts/"

robots_list = list(robots.keys())
print(robots_list)

def run_demo():
    input("Start part I")
    demo_part_1()
    input("Start part II")
    demo_part_2()
    input("Start part III")
    learning_time = demo_part_3()
    print(learning_time)
    input("Start IV")
    demo_part_4(learning_time)

def demo_part_1():
    approach = robots[robots_list[0]][0] + "_container_approach"
    container = robots[robots_list[0]][0] + "_container"

    grasp_insertable(robots_list[0], robots[robots_list[0]][0], container, approach)

    f = open(path_to_default_context + "insertion.json")
    insertion_context = json.load(f)
    insertion_context["skill"]["objects"]["Container"] = container
    insertion_context["skill"]["objects"]["Approach"] = approach
    insertion_context["skill"]["objects"]["Insertable"] = robots[robots_list[0]][0]
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
    f = open(path_to_default_context + "extraction.json")
    extraction_context = json.load(f)
    extraction_context["skill"]["objects"]["Container"] = container
    extraction_context["skill"]["objects"]["ExtractTo"] = approach
    extraction_context["skill"]["objects"]["Extractable"] = robots[robots_list[0]][0]

    insertion_context1 = copy.deepcopy(insertion_context)
    insertion_context1["skill"]["p0"]["DeltaX"] = [0.01, -0.005, 0, 10, 5, 0]
    insertion_context1["skill"]["p2"]["search_a"] = [3, 3, 0, 0, 0, 0]
    insertion_context1["skill"]["p2"]["search_f"] = [1, 0.75, 0, 0, 0, 0]
    insertion_context1["skill"]["p2"]["f_push"] = [0, 0, 2, 0, 0, 0]

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

    t = Task(robots_list[0])
    t.add_skill("insertion1", "TaxInsertion", insertion_context1)
    t.add_skill("extraction1", "TaxExtraction", extraction_context)
    #t.add_skill("move1", "TaxMove", move_up_context)
    t.add_skill("insertion2", "TaxInsertion", insertion_context2)
    t.add_skill("extraction2", "TaxExtraction", extraction_context)
    #t.add_skill("move2", "TaxMove", move_up_context)
    t.add_skill("insertion3", "TaxInsertion", insertion_context3)
    t.add_skill("extraction3", "TaxExtraction", extraction_context)
    move_up_context2 = copy.deepcopy(move_up_context)
    move_up_context2["skill"]["p0"]["T_T_EE_g_offset"][14] = 0.2
    t.add_skill("move3", "TaxMove", move_up_context2)
    t.add_skill("fail", "GenericWiggleMotion", wiggle_context)
    t.start(False)
    result = t.wait()

def demo_part_2():
    result = start_task(robots_list[0], "MoveToJointPose", {
        "parameters": {
            "pose": "telepresence_init",
            "speed": 1,
            "acc": 2
        }
    })
    wait_for_task(robots_list[0], result["result"]["task_uuid"])

    ip_master = get_ip(robots_list[0])
    ip_slaves = []
    for i in range(1, len(robots_list)):
        ip_slaves.append(get_ip(robots_list[i]))

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
    t = Task(robots_list[0])
    t.add_skill("telepresence", "Telepresence", telepresence_master_context)
    t.start()
    for i in range(1, len(robots)):
        t = Task(robots_list[i])
        t.add_skill("telepresence", "Telepresence", telepresence_slave_context)
        print(robots_list[i])
        t.start()

    input("Press key to stop.")
    for ip in ip_slaves:
        stop_task(ip)

    stop_task(ip_master)

def demo_part_3():
    learning_time = time.time()
    sc = SVMLearner(130,10,0,True,False, 0.9,True).get_configuration()
    tags = ["demo_collective"]
    threads = []
    knowledge_source = Knowledge()
    knowledge_source.kb_location = "collective-panda-prime"
    knowledge_source.mode = "global"
    knowledge_source.scope = []
    knowledge_source.scope.extend(tags)
    knowledge_source.type = "all"
    for robot in robots.keys():
        if robot == "collective-panda-prime":
            continue
        threads.append(Thread(target=learn_multiple_tasks, args=(robot, robots[robot], sc, knowledge_source.to_dict(), tags, 0, )))
        threads[-1].start()
    input("Press any key to stop learning.")
    stop_service_collective()
    learning_time = time.time() - learning_time
    print(learning_time)
    delete_experiment_data(robots, ["demo_collective"])
    delete_experiment_data(robots_list[1:], ["demo_collective"])
    return learning_time

def demo_part_4(learning_time = 121):
    approach = robots[robots_list[0]][0] + "_container_approach"
    container = robots[robots_list[0]][0] + "_container"

    move_joint(robots_list[0],robots[robots_list[0]][0]+"_container_approach")

    #insertion_context = download_best_result_tags("collective-panda-002.local","ml_results","insertion",["demo_collective"])
    #insertion_context = download_best_result(robots_list[0],"ml_results","insertion",robots[robots_list[0]][0],"")
    insertion_context = download_best_result_tags("collective-panda-prime.local","ml_results","insertion",["collective_learning"])
    f = open(path_to_default_context + "insertion.json")
    insertion_context = json.load(f)
    
    # context_map = InsertionFactory([robots_list[0]], TimeMetric("insertion", {"time": 5}), 
    #                                     {"Insertable":robots[robots_list[0]][0],"Container":container,"Approach":approach}).get_mapping()
    # insertion_context = download_knowldge_to_context("collective-panda-prime.local","local_knowledge","insertion",["demo_learning","key_door"], insertion_context, context_map)
    # print(insertion_context)

    # insertion_context["skill"]["objects"]["Container"] = container
    # insertion_context["skill"]["objects"]["Approach"] = approach
    # insertion_context["skill"]["objects"]["Insertable"] = robots[robots_list[0]][0]
    # insertion_context["skill"]["p2"]["f_push"] = [0,0,20,0,0,0]
    # f = open(path_to_default_context + "extraction.json")
    # extraction_context = json.load(f)
    # extraction_context["skill"]["objects"]["Container"] = container
    # extraction_context["skill"]["objects"]["ExtractTo"] = approach
    # extraction_context["skill"]["objects"]["Extractable"] = robots[robots_list[0]][0]
    # t = Task(robots_list[0])
    # t.add_skill("insertion", "TaxInsertion", insertion_context)
    # t.add_skill("extraction", "TaxExtraction", extraction_context)
    # t.start()
    # insertion_result = t.wait()

    sc = SVMLearner(130,10,0,True,False, 0.9,True).get_configuration()
    tags = ["demo_collective","key_door"]
    #tags = ["demo_learning"]
    threads = []
    pd = InsertionFactory([robots_list[0]], TimeMetric("insertion", {"time": 5}),
                                    {"Insertable": robots[robots_list[0]][0], "Container": container,
                                    "Approach": approach}).get_problem_definition(robots[robots_list[0]][0])
    print(learning_time)
    if learning_time > 120:
        knowledge_source = Knowledge()
        knowledge_source.kb_location = robots_list[0]  # "collective-dev-001"  #"collective-panda-prime" 
        knowledge_source.mode = "local"
        knowledge_source.scope = []
        knowledge_source.scope.extend(tags)
        knowledge_source.type = "all"
        learn_single_task(robots_list[0], pd, sc, tags, 0, False, knowledge_source.to_dict(), False)
    else:
        knowledge_source = Knowledge()
        knowledge_source.kb_location = robots_list[0]  # "collective-dev-001"  #"collective-panda-prime" 
        knowledge_source.mode = "global"
        knowledge_source.scope = ["demo_collective"]
        knowledge_source.scope.extend(["key_abus_e30"])
        knowledge_source.type = "all"
        learn_single_task(robots_list[0], pd, sc, tags, 0, False, knowledge_source.to_dict(), False)
    input("Press any key to stop learning.")
    
    stop_service_collective()

    while call_method(robots_list[0],12000,"is_busy")["result"]["busy"]:
        time.sleep(2)

    result = start_task_and_wait(robots_list[0], "MoveToJointPose", {
            "parameters": {
                "pose": "telepresence_init",
                "speed": 1,
                "acc": 2
            }
        })

    results = MongoDBClient(robots_list[0]).read("ml_results","insertion",{"meta.tags":tags})
    success = False
    for r in results:
        for i in range(1,len(r)-3 +1):
            if r["n"+str(i)]["q_metric"]["success"]:
                success = True
    if success:
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
        t = Task(robots_list[0])
        t.add_skill("success", "GenericWiggleMotion", wiggle_context)
        t.start(False)
        result = t.wait()
    delete_experiment_data(robots_list, ["demo_collective"])
    delete_experiment_data([robots_list[0]], ["demo_collective"],db="global_knowledge")
    time.sleep(5)
    place_insertable("collective-panda-prime","key_door","key_door_container","key_door_container_approach","key_door_container_above")

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

def grasp_collective():
    threads = []
    for r in robots.keys():
        threads.append(Thread(target=grasp_insertable, args=(r, robots[r][0], robots[r][0]+"_container", robots[r][0]+"_container_approach",robots[r][0]+"_container_above")))
        threads[-1].start()

    for t in threads:
        t.join()

def place_collective():
    threads = []
    for r in robots.keys():
        call_method(r,12000,"set_grasped_object",{"object":robots[r][0]})
        threads.append(Thread(target=place_insertable, args=(r, robots[r][0], robots[r][0]+"_container", robots[r][0]+"_container_approach",robots[r][0]+"_container_above")))
        threads[-1].start()

    for t in threads:
        t.join()

def learn_multiple_tasks(robot: str, task_instances: list, service_config: ServiceConfiguration, knowledge_configuration: Knowledge, tags: list, iteration = 0, finish_threshold = {}):
    for insertable in task_instances:
        container = insertable+"_container"
        approach = container+"_approach"
        move_joint(robot, container+"_above")
        if not grasp_insertable(robot, insertable, container, approach, container+"_above"):
            print("cannot grasp "+insertable+". Contiuing with next Task.")
            continue
        pd = InsertionFactory([robot], TimeMetric("insertion", {"time": 5}),
                                    {"Insertable": insertable, "Container": container,
                                    "Approach": approach}).get_problem_definition(insertable)
        if insertable in finish_threshold:
            service_config.finish_cost = finish_threshold[insertable]
        if insertable == "HDMI_plug":  # increase the limits for HDMI_plug
            pd.domain.limits["p2_f_push_z"] = (0, 25)
        learn_single_task(robot, pd, service_config, tags, iteration, False, knowledge_configuration, True)
        print("finished learning ", pd.tags, "\nplacing...")
        place_insertable(robot, insertable, container, approach, container+"_above")

def teach_insertable(robot:str, insertable:str):
    input("Press key to start teaching. [Pose above container, without object]")
    call_method(robot, 12000, "teach_object", {"object": insertable+"_container_above"})
    input("Teach where to grab object")
    call_method(robot, 12000, "grasp", {"width":0,"speed":1,"force":100})
    call_method(robot, 12000, "teach_object", {"object": insertable, "teach_width":True})
    current_finger_width = call_method(robot,12000,"get_state")["result"]["gripper_width"]
    call_method(robot,12000,"move_gripper",{"speed":1,"force":100,"width":current_finger_width+0.005})
    print("closing gripper")
    print(call_method(robot, 12000, "grasp_object", {"object": insertable}))
    input("Teach approach [with object]")
    call_method(robot, 12000, "teach_object", {"object": insertable+"_container_approach"})
    input("Teach container [with object]")
    call_method(robot, 12000, "teach_object", {"object": insertable+"_container"})  