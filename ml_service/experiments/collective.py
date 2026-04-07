import time
from threading import Thread
from xmlrpc.client import ServerProxy

from mongodb_client.mongodb_client import MongoDBClient
from services.knowledge import Knowledge
from definitions.service_configs import SVMLearner
from utils.helper_functions import move_joint, grasp_insertable, place_insertable
from experiments.insertion import learn_single_task, InsertionFactory, TimeMetric
from experiments.robot_control import stop_services

def learn_multiple_tasks(robot: str, task_instances: list, service_config, knowledge_config: dict, tags: list, iteration=0, finish_threshold=None):
    if finish_threshold is None:
        finish_threshold = {}
    for insertable in task_instances:
        container = f"{insertable}_container"
        approach = f"{container}_approach"
        move_joint(robot, f"{container}_above")
        if not grasp_insertable(robot, insertable, container, approach, f"{container}_above"):
            print(f"cannot grasp {insertable}. Continuing with next Task.")
            continue
        pd = InsertionFactory([robot], TimeMetric("insertion", {"time": 5}),
                              {"Insertable": insertable, "Container": container,
                               "Approach": approach}).get_problem_definition(insertable)
        if insertable in finish_threshold:
            pd.optimum_thr = finish_threshold[insertable]
        if insertable == "HDMI_plug":
            pd.domain.limits["p2_f_push_z"] = (0, 20)
        try:
            learn_single_task(robot, pd, service_config, tags, iteration, False, knowledge_config, True)
            print(f"finished learning {pd.tags}\nplacing...")
            place_insertable(robot, insertable, container, approach, f"{container}_above")
        except KeyboardInterrupt:
            print("stopping...")
            stop_services([robot])
            place_insertable(robot, insertable, container, approach, f"{container}_above")
            break

def collective_experiment():
    robots = {
        "collective-panda-prime": ["key_door"],
        "collective-panda-002": ["key_abus_e30"],
        "collective-panda-003": ["key_padlock", "key_2"],
        "collective-panda-004": ["cylinder_40", "cylinder_10", "cylinder_20", "cylinder_30", "cylinder_50", "cylinder_60"],
        "collective-panda-008": ["HDMI_plug", "key_padlock_2", "key_hatch", "key_old"]
    }
    cutoff = {
        "key_door": 0.25, "key_abus_e30": 0.25, "key_padlock": 0.25, "key_2": 0.25,
        "cylinder_40": 0.45, "cylinder_10": 0.5, "cylinder_20": 0.35, "cylinder_30": 0.4,
        "cylinder_50": 0.35, "cylinder_60": 0.55, "HDMI_plug": 0.3, "key_padlock_2": 0.25,
        "key_hatch": 0.25, "key_old": 0.25
    }
    sc = SVMLearner(130, 10, 0, True, False, 0.4, True).get_configuration()
    tags = ["collective_learning_04_alt"]
    
    for n_iter in range(19, 26):
        threads = []
        print(f"Number of iteration: {n_iter+1}/25")
        k_source = Knowledge()
        k_source.kb_location = "collective-dev-001"
        k_source.mode = "global"
        k_source.scope = tags + [f"n{n_iter+1}"]
        k_source.type = "all"
        
        for robot in robots.keys():
            t = Thread(target=learn_multiple_tasks, args=(robot, robots[robot], sc, k_source.to_dict(), tags, n_iter, cutoff))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
            
        client = MongoDBClient(k_source.kb_location)
        for robot in robots.keys():
            for task in robots[robot]:
                k_tags = tags + [f"n{n_iter+1}", task]
                if not client.read("global_knowledge", "insertion", {"meta.tags": k_tags}):
                    print(f"task {task} wasn't finished properly")
                    return task
        
        try:
            kb = ServerProxy(f"http://{k_source.kb_location}:8001", allow_none=True)
            kb.clear_memory()
        except Exception:
            pass

def collective_experiment_ext():
    robots = {
        "collective-panda-prime": ["key_door"],
        "collective-panda-002": ["key_abus_e30"],
        "collective-panda-003": ["key_padlock", "key_2"],
        "collective-panda-004": ["cylinder_40", "cylinder_20", "cylinder_60"],
        "collective-panda-008": ["HDMI_plug", "key_padlock_2", "key_hatch", "key_old"],
        "collective-panda-005": ["cylinder_30", "cylinder_10", "cylinder_50"]
    }
    cutoff = {
        "key_door": 0.25, "key_abus_e30": 0.25, "key_padlock": 0.25, "key_2": 0.25,
        "cylinder_40": 0.45, "cylinder_10": 0.5, "cylinder_20": 0.35, "cylinder_30": 0.4,
        "cylinder_50": 0.35, "cylinder_60": 0.55, "HDMI_plug": 0.3, "key_padlock_2": 0.25,
        "key_hatch": 0.25, "key_old": 0.25
    }
    sc = SVMLearner(130, 10, 0, True, False, 0.4, True).get_configuration()
    tags = ["collective_learning_04_ext_alt"]
    
    for n_iter in range(16, 26):
        threads = []
        print(f"Number of iteration: {n_iter+1}/25")
        k_source = Knowledge()
        k_source.kb_location = "collective-dev-001"
        k_source.mode = "global"
        k_source.scope = tags + [f"n{n_iter+1}"]
        k_source.type = "all"
        
        for robot in robots.keys():
            t = Thread(target=learn_multiple_tasks, args=(robot, robots[robot], sc, k_source.to_dict(), tags, n_iter, cutoff))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
            
        client = MongoDBClient(k_source.kb_location)
        for robot in robots.keys():
            for task in robots[robot]:
                k_tags = tags + [f"n{n_iter+1}", task]
                if not client.read("global_knowledge", "insertion", {"meta.tags": k_tags}):
                    print(f"task {task} wasn't finished properly")
                    return task
        
        try:
            kb = ServerProxy(f"http://{k_source.kb_location}:8001", allow_none=True)
            kb.clear_memory()
        except Exception:
            pass

def collective_experiment_parallel():
    robots = {
        "collective-panda-prime": ["key_door"],
        "collective-panda-002": ["key_abus_e30"],
        "collective-panda-003": ["key_padlock", "key_2"],
        "collective-panda-004": ["cylinder_30", "cylinder_60", "cylinder_40", "cylinder_10", "cylinder_20", "cylinder_50"],
        "collective-panda-008": ["HDMI_plug", "key_padlock_2", "key_hatch", "key_old"]
    }
    cutoff = {
        "key_door": 0.25, "key_abus_e30": 0.25, "key_padlock": 0.25, "key_2": 0.25,
        "cylinder_40": 0.45, "cylinder_10": 0.5, "cylinder_20": 0.35, "cylinder_30": 0.4,
        "cylinder_50": 0.35, "cylinder_60": 0.55, "HDMI_plug": 0.3, "key_padlock_2": 0.25,
        "key_hatch": 0.25, "key_old": 0.25
    }
    sc = SVMLearner(130, 10, 0, True, False, 0, False).get_configuration()
    tags = ["collective_learning_parallel"]
    
    for n_iter in range(20, 22):
        threads = []
        print(f"Number of iteration: {n_iter+1}/25")
        k_source = Knowledge()
        k_source.scope = tags + [f"n{n_iter+1}"]
        k_source.type = "all"
        
        for robot in robots.keys():
            t = Thread(target=learn_multiple_tasks, args=(robot, robots[robot], sc, k_source.to_dict(), tags, n_iter, cutoff))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        
        time.sleep(5)
        for robot in robots.keys():
            client = MongoDBClient(robot)
            for task in robots[robot]:
                filter_tags = tags + [f"n{n_iter+1}", task]
                if not client.read("local_knowledge", "insertion", {"meta.tags": filter_tags}):
                    print(f"task {task} has not created knowledge")
                    return task
