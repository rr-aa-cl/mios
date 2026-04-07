import time
import copy
from threading import Thread
from xmlrpc.client import ServerProxy

from mongodb_client.mongodb_client import MongoDBClient
from services.knowledge import Knowledge
from utils.helper_functions import move_joint, grasp_insertable, place_insertable
from utils.ws_client import call_method

from experiments.config import get_ips, list_block_1, list_block_2, list_U
from experiments.insertion import learn_single_task, InsertionFactory, TimeMetric, SVMLearner
from experiments.analysis import get_states
from experiments.robot_control import stop_services

def learn_from_trial(source_ip, source_uuid, source_trial_n: list, target_ip, target_instance):
    mongodb_client = MongoDBClient(source_ip)
    source_results = mongodb_client.read("ml_results", "insertion", {"meta.uuid": source_uuid})[0]
    for trial_n in source_trial_n:
        theta = source_results[f"n{trial_n}"]["theta"]
        source_tags = source_results["meta"]["tags"] + [f"trial_n{trial_n}"]
        knowledge = Knowledge(None, "similar", ["default_context"], None, None, "insertion", theta, 0.04, 
                              None, False, None, [1], "insertion", source_results["meta"]["skill_instance"], 
                              source_uuid, None, time.ctime(), source_tags)
        sc = SVMLearner(1, 1, 0, True, False, -1, True).get_configuration()
        pd = InsertionFactory([target_ip], TimeMetric("insertion", {"time": 5}),
                              {"Insertable": target_instance, "Container": f"{target_instance}_container",
                               "Approach": f"{target_instance}_container_approach"}).get_problem_definition(target_instance)
        pd.cost_function.finish_thr = 2

        if not get_states([target_instance[:3]])[0]:
            print(f"{target_ip} is not ready!")
            break
            
        if target_instance in ["010_left", "023_left", "027_left", "024_left"]:
            pd.domain.limits["p2_f_push_z"] = (0, 60)
            
        dualarm_cmd = {"agent": target_ip, "port": 13000, "skills": [], "sleep": 1}
        target_tags = ["transfermapping", f"from_{source_uuid}"]
        learn_single_task(target_ip, pd, sc, target_tags, 1, False, knowledge.to_dict(), True, 8000, dualarm_cmd)

def transfer_to_all_from_trial(source_ip: str, source_uuid, source_trial_n: list):
    all_modules = list_block_1 + list_block_2 + list_U
    target_ips = get_ips(all_modules)
    target_instances = [f"{m}_left" for m in all_modules]
    threads = []
    for target_ip, target_instance in zip(target_ips, target_instances):
        t = Thread(target=learn_from_trial, args=(source_ip, source_uuid, source_trial_n, target_ip, target_instance))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

def transfer_learning():
    robots = {"collective-016.rsi.ei.tum.de": "cylinder_50",
              "collective-005.rsi.ei.tum.de": "usb-a",
              "collective-010.rsi.ei.tum.de": "schuko",
              "collective-029.rsi.ei.tum.de": "IEC60320_C13",
              "collective-017.rsi.ei.tum.de": "abus_e30"}
    tasks = ["cylinder_50", "usb-a", "schuko", "IEC60320_C13", "abus_e30"]
    
    sc = SVMLearner(130, 10, 0, True, False, -1, True).get_configuration()
    tags = ["transfer_learning", "evaluation", "base"]
    n_current_iter = {task: 0 for task in tasks}
    slowest_iteration = 0
    
    while slowest_iteration < 10:
        threads = []
        print(f"Number of slowest iteration: {slowest_iteration+1}/10")
        try:
            for robot, insertable in robots.items():
                # Simplified movement/grasping logic for brevity
                k_source = Knowledge()
                k_source.kb_location = "collective-020.rsi.ei.tum.de"
                k_source.mode = "global" 
                k_source.kb_db = "global_knowledge"
                k_source.kb_task_type = "insertion"
                k_source.scope = tags + [insertable, f"n{n_current_iter[insertable]+1}"]
                k_source.type = "all"

                pd = InsertionFactory([robot], TimeMetric("insertion", {"time": 5}),
                                      {"Insertable": insertable, "Container": f"{insertable}_container",
                                       "Approach": f"{insertable}_container_approach"}).get_problem_definition(insertable)
                
                dualarm_cmd = {"agent": robot, "port": 13000, "sleep": 1, "pose": f"{insertable}_hold"}
                t = Thread(target=learn_single_task, args=(robot, pd, sc, tags),
                           kwargs={'dualarm_cmd': dualarm_cmd, 'wait': True, 'knowledge': k_source.to_dict(),
                                   'keep_record': False, 'current_number_iterations': n_current_iter[insertable]})
                t.start()
                threads.append(t)
                
            for t in threads:
                t.join()
                
            # Consistency checks
            client = MongoDBClient("collective-020.rsi.ei.tum.de")
            for robot, task in robots.items():
                k_tags = tags + [f"n{n_current_iter[task]+1}", task]
                if client.read("global_knowledge", "insertion", {"meta.tags": k_tags}):
                    n_current_iter[task] += 1
            
            # Reset memory on KB server
            try:
                kb = ServerProxy("http://collective-020.rsi.ei.tum.de:8001", allow_none=True)
                kb.clear_memory()
            except Exception:
                pass
                
        except KeyboardInterrupt:
            stop_services(list(robots.keys()))
            return False
        
        slowest_iteration = min(n_current_iter.values())
    
    # Transfer phase
    tags.pop(tags.index("base"))
    for task in tasks:
        for n_iter in range(0, 10):
            threads = []
            print(f"Transfer iteration: {n_iter+1}/10 from {task}")
            for robot, ins in robots.items():
                k_source = Knowledge()
                k_source.kb_location = "collective-020.rsi.ei.tum.de"
                k_source.mode = "global"
                k_source.scope = tags + [task, f"n{n_iter+1}"]
                k_source.type = "all"
                
                r_tags = tags + [f"from_{task}"]
                pd = InsertionFactory([robot], TimeMetric("insertion", {"time": 5}),
                                      {"Insertable": ins, "Container": f"{ins}_container",
                                       "Approach": f"{ins}_container_approach"}).get_problem_definition(ins)
                t = Thread(target=learn_single_task, args=(robot, pd, sc, r_tags, n_iter, False, k_source.to_dict(), True))
                t.start()
                threads.append(t)
            for t in threads:
                t.join()
