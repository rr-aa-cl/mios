import time
import json
import os
from threading import Thread
from xmlrpc.client import ServerProxy

from problem_definition.problem_definition import ProblemDefinition
from services.base_service import ServiceConfiguration
from services.knowledge import Knowledge
from utils.experiment_wizard import start_experiment, start_single_experiment
from utils.helper_functions import get_nested_parameter, move_joint, grasp_insertable, place_insertable
from utils.ws_client import call_method

from definitions.templates import InsertionFactory
from definitions.cost_functions import TimeMetric
from definitions.service_configs import SVMLearner, OrigPSPLearner

from experiments.config import get_ips, list_block_1, list_block_2, list_U
from experiments.robot_control import stop_services
from experiments.analysis import get_states

def learn_task(robot: str, problem_definition: ProblemDefinition, service_config: ServiceConfiguration, tags: list,
               n_iterations: int = 10, keep_record: bool = False, knowledge=None, wait: bool = False, service_port: int = 8000):
    start_experiment(robot, [robot], problem_definition, service_config, n_iterations, knowledge=knowledge, tags=tags,
                     keep_record=keep_record, wait=wait, service_port=service_port)

def learn_single_task(robot: str, problem_definition: ProblemDefinition, service_config: ServiceConfiguration, tags: list,
                      current_number_iterations: int = 0, keep_record: bool = False, knowledge=None, wait: bool = False, 
                      service_port: int = 8000, dualarm_cmd: dict = None):
    return start_single_experiment(robot, [robot], problem_definition, service_config, current_number_iterations, tags, 
                                   knowledge, keep_record, wait, service_port=service_port, dualarm_cmd=dualarm_cmd)

def learn_insertion(robot: str, approach: str, insertable: str, container: str, tags: list, knowledge=None,
                    wait: bool = True, n_iterations=30, service_port=8000):
    pd = InsertionFactory([robot], TimeMetric("insertion", {"time": 5}),
                          {"Insertable": insertable, "Container": container,
                           "Approach": approach}).get_problem_definition(insertable)
    sc = OrigPSPLearner(3000, 10, 0, True, False, -1, True).get_configuration()
    pd.n_variations = 5
    pd.variate_only_success = True
    try:
        learn_task(robot, pd, sc, tags, knowledge=knowledge, n_iterations=n_iterations, service_port=service_port, wait=wait)
    except KeyboardInterrupt:
        print(f"stop learning {robot}")
        stop_services([robot])

def learn_from_source(robot, insertable, iterations=10):
    stop_services([robot])
    # Note: wait_for_services logic is missing in run_experiments.py but I'll add the core logic
    print(f"Start with default knowledge for {insertable}")
    
    context_dir = os.path.join(os.getcwd(), "..", "python", "taxonomy", "default_contexts")
    insertion = InsertionFactory([robot], TimeMetric("insertion", {"time": 5}),
                                 {"Insertable": insertable, "Container": f"{insertable}_container",
                                  "Approach": f"{insertable}_container_approach"})
    pd = insertion.get_problem_definition(insertable)
    
    with open(os.path.join(context_dir, "insertion.json"), "r") as f:
        skill_context = json.load(f)
    
    skill_context["skill"]["p2"]["f_push"][2] = 30
    if insertable in ["024_left", "027_left", "023_left"]:
        pd.domain.limits["p2_f_push_z"] = (0, 35)
    
    sc = SVMLearner(130, 10, 0, True, False, -1, True).get_configuration()
    
    skill_mapping = insertion.get_mapping()
    theta = {}
    wrapper_context = {"skills": {"insertion": skill_context}}
    for key, mappings in skill_mapping.items():
        for m in mappings:
            value = get_nested_parameter(wrapper_context, m)
            if value is not None:
                theta[key] = value

    knowledge = Knowledge(None, "similar", ["default_context"], None, None, "insertion", theta, 0.04, 
                          None, False, None, [1], "insertion", insertable, "default_context", 
                          None, time.ctime(), ["default_context"])
    
    dualarm_skills = []
    # Simplified dualarm_cmd logic as in run_experiments.py
    dualarm_cmd = {"agent": robot, "port": 13000, "skills": dualarm_skills, "sleep": 1}
    learn_single_task(robot, pd, sc, ["default_context"], 0, False, knowledge.to_dict(), False, 8000, dualarm_cmd)
    input("Press enter to stop robot...")
    stop_services([robot])

def learn_alpha_skills(modules=None):
    if modules is None:
        modules = list_block_1 + list_block_2 + list_U
    ips = get_ips(modules)
    insertables = [f"{m}_left" for m in modules]
    threads = []
    for ip, insertable in zip(ips, insertables):
        t = Thread(target=learn_from_source, args=(ip, insertable))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

def learn_isolated_nonSharing(robot, insertable, iterations=1):
    stop_services([robot])
    insertion = InsertionFactory([robot], TimeMetric("insertion", {"time": 5}),
                                 {"Insertable": insertable, "Container": f"{insertable}_container",
                                  "Approach": f"{insertable}_container_approach"})
    pd = insertion.get_problem_definition(insertable)
    if insertable in ["010_left", "023_left", "027_left", "024_left"]:
        pd.domain.limits["p2_f_push_z"] = (0, 60)
    sc = SVMLearner(300, 10, 0, True, False, -1, True).get_configuration()
    
    dualarm_cmd = {"agent": robot, "port": 13000, "skills": [], "sleep": 1}
    tags = ["noKnowledge", "noSharing", "isolated", "PSP", "insertion2", "run_3"]
    if iterations > 1:
        learn_task(robot, pd, sc, tags, iterations, True, {}, True, 8000, dualarm_cmd)
    else:
        learn_single_task(robot, pd, sc, tags, 0, False, {}, False, 8000, dualarm_cmd)

def learn_comparison(modules=None):
    if modules is None:
        modules = list_block_1 + list_block_2 + list_U
    ips = get_ips(modules)
    insertables = [f"{m}_left" for m in modules]
    threads = []
    for ip, ins in zip(ips, insertables):
        t = Thread(target=learn_isolated_nonSharing, args=(ip, ins, 1))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

def five_agent_collective(if_reverse=False):
    modules = list_block_1 + list_block_2 + list_U
    if if_reverse:
        modules.reverse()
        tags = ["5agents_25tasks", "collective_reverse"]
    else:
        tags = ["5agents_25tasks", "collective"]

    sc = SVMLearner(450, 10, 0, True, False, 0.4, True).get_configuration()
    
    # Extract cutoff from local scope to match original
    cutoff = { '001_left': 0.708, '003_left': 0.68016, '004_left': 0.74976, '005_left': 0.65,
               '006_left': 0.6127, '007_left': 0.62616, '008_left': 0.6372, '010_left': 0.6888,
               '011_left': 0.63816, '012_left': 0.75528, '009_left': 0.6943, '013_left': 0.6348,
               '014_left': 0.6, '015_left': 0.68184, '016_left': 0.9, '017_left': 0.63864,
               '018_left': 0.63144, '021_left': 0.63528, '022_left': 0.6828, '023_left': 0.6648,
               '024_left': 0.9187, '025_left': 0.64752, '027_left': 0.68448, '028_left': 0.61824,
               '029_left': 0.68088 }

    knowledge_source = Knowledge()
    knowledge_source.kb_location = "collective-001.rsi.ei.tum.de"
    knowledge_source.mode = "global"
    knowledge_source.scope = tags + ["n1"]
    knowledge_source.type = "all"
    
    tasks_to_do = ["collective-" + str(xxx) + ".rsi.ei.tum.de" for xxx in modules]
    task_map = { "collective-" + str(xxx) + ".rsi.ei.tum.de": [str(xxx) + "_left"] for xxx in modules }
    
    threads = []
    for robot in tasks_to_do:
        insertable = task_map[robot][0]
        container = insertable + "_container"
        approach = container + "_approach"
        pd = InsertionFactory([robot], TimeMetric("insertion", {"time": 5}),
                              {"Insertable": insertable, "Container": container,
                               "Approach": approach}).get_problem_definition(insertable)
        
        if not get_states([insertable[:3]])[0]:
            print(f"{robot} is not ready! Skipping {insertable}")
            continue
            
        if insertable in cutoff:
            pd.optimum_thr = cutoff[insertable]
            
        dualarm_cmd = {"agent": robot, "port": 13000, "skills": [], "sleep": 1}
        t = Thread(target=learn_single_task, args=(robot, pd, sc, tags, 0, False, knowledge_source.to_dict(), True, 8000, dualarm_cmd))
        t.start()
        threads.append(t)
        
        while sum([th.is_alive() for th in threads]) >= 5:
            time.sleep(1)
            
    for t in threads:
        t.join()
    return "finished :)"
