import utils.ws_global_loop
from asyncio import Server
from copy import deepcopy
from email import message

from numpy import iterable
from definitions.templates import *
from definitions.cost_functions import *
from definitions.service_configs import *
from utils.database import delete_global_knowledge
from utils.database import delete_global_results
from utils.experiment_wizard import *
from utils.taxonomy_utils import *
from services.knowledge import Knowledge
from utils.helper_functions import *
import os
from threading import Thread
import json
        
###################################################################################
list_block_1 = ["001", #"002", 
                "003", "004", "005", 
                "006", "007", "033", "032", "008"]  #"044"->032
list_block_2 = ["035",
                "034","013","014", # -> 043 -> 034
                "015","042",
                "017", "016",  #041->017
                "021","022"]
list_U = ["023", "024", "025","026", "018","040","029"] # "028",  047 ->018
list_external = ["050"]
# list_all = list_block_1 + list_block_2 + list_U
# for i in zip(list(range(1,26)), list_all):
#     print(i)

def get_ips(module_list):
    with open("../python/ip.json", "r") as jsonfile:
        data = json.load(jsonfile)        
        ips = [data[i] for i in module_list]
    return ips
###################################################################################


def learn_task(robot:str, problem_definition: ProblemDefinition, service_config: ServiceConfiguration, tags: list,
               n_iterations: int = 10, keep_record: bool = False, knowledge = None, wait: bool = False, service_port:int = 8000):
    start_experiment(robot, [robot], problem_definition, service_config, n_iterations, knowledge=knowledge, tags=tags,
                     keep_record=keep_record, wait=wait,service_port=service_port)
def learn_single_task(robot:str, problem_definition: ProblemDefinition, service_config: ServiceConfiguration, tags: list,
               current_number_iterations: int=0, keep_record: bool = False, knowledge = None, wait: bool = False, service_port:int=8000, dualarm_cmd:dict=None):
    return start_single_experiment(robot, [robot], problem_definition, service_config, current_number_iterations, tags, knowledge, keep_record, wait, service_port=service_port,dualarm_cmd=dualarm_cmd)

def test_learning():
    pd = InsertionFactory("collective-panda-001", ContactForcesMetric("insertion", {"contact_forces": 175}),
                          {"Insertable": "cylinder_40", "Container": "cylinder_40_container",
                           "Approach": "cylinder_40_container_approach"}).get_problem_definition("cylinder_40")
    sc = SVMLearner().get_configuration()
    learn_task("collective-panda-001", pd, sc, ["test_learning"])


def learn_insertion(robot: str, approach: str, insertable: str, container: str, tags: list, knowledge=None,
                    wait: bool=True, n_iterations = 30, service_port=8000):
    pd = InsertionFactory([robot], TimeMetric("insertion", {"time": 5}),
                          {"Insertable": insertable, "Container": container,
                           "Approach": approach}).get_problem_definition(insertable)
    #sc = SVMLearner(3000,10,0,True,False, -1,True).get_configuration()
    sc = OrigPSPLearner(3000,10,0,True,False, -1, True).get_configuration()
    pd.n_variations = 5
    pd.variate_only_success = True
    try:
        learn_task(robot, pd, sc, tags, knowledge=knowledge, n_iterations=n_iterations,service_port=service_port,wait=wait)
    except KeyboardInterrupt:
        print("stop learning ",robot)
        stop_services([robot])


def learn_extraction(robot: str, extract_to: str, extractable: str, container: str, tags: list, knowledge=None,
                    wait: bool=True, n_iterations = 10, service_port=8000):
    pd = ExtractionFactory(robot, ContactForcesMetric("insertion", {"contact_forces": 175}),
                          {"Extractable": extractable, "Container": container,
                           "ExtractTo": extract_to}).get_problem_definition(extractable)
    sc = SVMLearner().get_configuration()
    learn_task(robot, pd, sc, tags, knowledge=knowledge, n_iterations=n_iterations,service_port=service_port)


def learn_tip(robot: str, approach: str, tippable: str, tags: list, knowledge=None,
                    wait: bool=True, n_iterations = 10, service_port=8000):
    pd = TipFactory(robot, ContactForcesMetric("tip", {"contact_forces": 175}),
                          {"Tippable": tippable, "Approach": approach}).get_problem_definition(tippable)
    sc = SVMLearner().get_configuration()
    learn_task(robot, pd, sc, tags, knowledge=knowledge, n_iterations=n_iterations,service_port=service_port)


def learn_drag(robot: str, approach: str, draggable: str, goal_pose: str, tags: list, knowledge=None,
                    wait: bool=True, n_iterations = 10, service_port=8000):
    pd = DragFactory(robot, ContactForcesMetric("drag", {"contact_forces": 175}),
                          {"Draggable": draggable, "StartPose": approach, "GoalPose": goal_pose}).get_problem_definition(draggable)
    sc = SVMLearner().get_configuration()
    learn_task(robot, pd, sc, tags, knowledge=knowledge, n_iterations=n_iterations,service_port=service_port)


def learn_turn_lever(robot: str, start: str, lever: str, goal: str, tags: list, knowledge=None,
                    wait: bool=True, n_iterations = 10, service_port=8000):
    pd = TurnLeverFactory(robot, ContactForcesMetric("turn_lever", {"contact_forces": 175}),
                          {"Lever": lever, "StartPose": start, "GoalPosition": goal}).get_problem_definition(lever)
    sc = SVMLearner().get_configuration()
    learn_task(robot, pd, sc, tags, knowledge=knowledge, n_iterations=n_iterations,service_port=service_port)


def learn_press_button(robot: str, approach: str, button: str, tags: list, knowledge=None,
                    wait: bool=True, n_iterations = 10, service_port=8000):
    pd = PressButtonFactory(robot, ContactForcesMetric("press_button", {"contact_forces": 175}),
                          {"Button": button, "Approach": approach}).get_problem_definition(button)
    sc = SVMLearner().get_configuration()
    learn_task(robot, pd, sc, tags, knowledge=knowledge, n_iterations=n_iterations,service_port=service_port)


def learn_bend(robot: str, start_pose: str, goal_pose: str, bendable: str, tags: list, knowledge=None,
                    wait: bool=True, n_iterations = 10, service_port=8000):
    pd = BendFactory(robot, ContactForcesMetric("bend", {"contact_forces": 175}),
                          {"Bendable": bendable, "StartPose": start_pose, "GoalPose": goal_pose}).get_problem_definition(bendable)
    sc = SVMLearner().get_configuration()
    learn_task(robot, pd, sc, tags, knowledge=knowledge, n_iterations=n_iterations,service_port=service_port)


def learn_multiple_tasks(robot: str, task_instances: list, service_config: ServiceConfiguration, knowledge_configuration: dict, tags: list, iteration = 0, finish_threshold = {}):
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
            pd.optimum_thr = finish_threshold[insertable]
        if insertable == "HDMI_plug":  # increase the limits for HDMI_plug
            pd.domain.limits["p2_f_push_z"] = (0, 20)
        try:
            learn_single_task(robot, pd, service_config, tags, iteration, False, knowledge_configuration, True)
            print("finished learning ", pd.tags, "\nplacing...")
            place_insertable(robot, insertable, container, approach, container+"_above")
        except KeyboardInterrupt:
            print("stopping...")
            stop_services([robot])
            place_insertable(robot, insertable, container, approach, container+"_above")
            break


def delete_results(robot:str, tags:list):
    client = MongoDBClient(robot)
    if not client.remove("ml_results", "insertion", {"meta.tags":tags}):
        print("Cannot find ", tags, "at ml_results")
    if not client.remove("local_knowledge", "insertion", {"meta.tags": tags}):
        print("Cannot find ", tags, "at local_knowledge")
    if not client.remove("global_knowledge", "insertion", {"meta.tags": tags}):
        print("Cannot find ", tags, "at global_knowledge")
    

def delete_some_results(modules: list, tags:list):
    ips = get_ips(modules)
    threads = []
    for ip,module in zip(ips, modules):
        print("\nDelete results on ",module)
        delete_results(ip, tags)

def delete_double_results(modules: list, tags:list, keep_newest = True):
    ips = get_ips(modules)
    threads = []
    for ip,module in zip(ips, modules):
        client = MongoDBClient(ip)
        results = client.read("ml_results", "insertion", {"meta.tags":tags})
        if len(results) > 1:
            times = [r["meta"]["t_0"] for r in results]
            if keep_newest:
                keep_this = max(times)
                delete_this = [r["_id"] for r in results if r["meta"]["t_0"] < keep_this]
            else:
                keep_this = min(times)
                delete_this = [r["_id"] for r in results if r["meta"]["t_0"] > keep_this]
            print("\nFound multiple results on ",module)
            for id in delete_this:
                client.remove("ml_results", "insertion", {"_id": id})
        else:
            print("found ", len(results), " results. Nothing to delete.")


def check_pose(robot,pose):
    error = []
    call_method(robot,12000,"home_gripper")
    move_joint(robot,pose+"_container_above")
    call_method(robot,12000,"home_gripper")
    move_joint(robot,pose+"_container_approach")
    move(robot, pose,[0,0,0])
    move_joint(robot, pose)
    result = call_method(robot, 12000, "grasp_object",{"object":pose})
    if not result["result"]["result"]:
        print(pose, "not working")
        call_method(robot, 12000, "home_gripper")
        error.append(pose)
    else:
        call_method(robot,12000,"release_object")
    move(robot,pose+"_container_approach",[0,0,0.06])
    move_joint(robot,pose+"_container_above")
    return error

def check_poses(robot_dict):
    error = []
    for robot in robot_dict.keys():
        for pose in robot_dict[robot]:
            error.append(check_pose(robot,pose))
    return error

def learn_from_source(robot, insertable):
    stop_services([robot])
    wait_for_services([robot], [["localhost"]])
    print("start with default knowledge")
    path_to_default_context = os.getcwd() + "/../python/taxonomy/default_contexts/"
    f = open(path_to_default_context + "insertion.json")
    insertion = InsertionFactory([robot], TimeMetric("insertion", {"time": 5}),
                                        {"Insertable": insertable, "Container": insertable+"_container",
                                        "Approach": insertable+"_container_approach"})
    pd = insertion.get_problem_definition(insertable)
    skill_context = json.load(f)
    skill_context["skill"]["p2"]["f_push"][2] = 30
    if insertable == "024_left" or insertable == "027_left":
        pd.domain.limits["p2_f_push_z"] = (0,35)
        skill_context["skill"]["p2"]["f_push"][2] = 30
    if insertable == "023_left":
        pd.domain.limits["p2_f_push_z"] = (0,35)
        skill_context["skill"]["p2"]["f_push"][2] = 25
    if insertable == "029_left":
        skill_context["skill"]["p2"]["f_push"][2] = 15

    sc = SVMLearner(130,10,0,True,False, -1,True).get_configuration()

    skill_context = {"skills": {"insertion": skill_context}}
    skill_mapping = insertion.get_mapping()
    theta = dict()
    for key in skill_mapping.keys():
        for m in skill_mapping[key]:
            value = get_nested_parameter(skill_context, m)
            if value is not None:
                theta[key] = value
            else:
                print("The skill context provided has no key ",m)

    print(theta)
    knowledge = Knowledge(None, "similar", ["default_context"], None, None, "insertion", theta, 0.04, None, False, None, [1], "insertion", insertable, "default_context", None, time.ctime(),["default_context"])
    
    dualarm_skills = []
    if insertable != "016_left":
        move_context = {
                    "skill": {
                        "speed": 0.5,
                        "acc": 1,
                        "q_g": [0, 0, 0, 0, 0, 0, 0],
                        "objects": {
                            "goal_pose": "hold"}},
                    "control": {
                        "control_mode": 3},
                    "user": {
                        "env_X": [0.001, 0.001, 0.001, 0.001, 0.001, 0.001],
                        "F_ext_max": [100, 50]}}
        dualarm_skills.append(("move", "MoveToPoseJoint", move_context))
    else:
        call_method(robot,13000,"set_grasped_object",{"object":"016_right"})
        f = open(path_to_default_context + "insertion.json")
        insert_context = json.load(f)
        insert_context["skill"]["objects"]["Container"] = "016_right_container"
        insert_context["skill"]["objects"]["Insertable"] = "016_right"
        insert_context["skill"]["objects"]["Approach"] = "016_right_container_approach"
        dualarm_skills.append(("insert", "TaxInsertion", insert_context))
        f = open(path_to_default_context + "extraction.json")
        extract_context = json.load(f)
        extract_context["skill"]["objects"]["Container"] = "016_right_container"
        extract_context["skill"]["objects"]["Extractable"] = "016_right"
        extract_context["skill"]["objects"]["ExtractTo"] = "016_right_container_approach"
        dualarm_skills.append(("extract", "TaxExtraction", extract_context))

    dualarm_cmd = {"agent":robot,"port":13000,"skills":dualarm_skills,"sleep":1}
    learn_single_task(robot, pd, sc, ["default_context"], 0, False, knowledge.to_dict(), False, 8000, dualarm_cmd)
    input("press enter to stop robot")
    stop_services([robot])

def learn_alpha_skills(modules = list_block_1+list_block_2+list_U):
    ips = get_ips(modules)
    #states = get_states(modules)
    #remove modules that are not ready:
    
    insertables = [m+"_left" for m in modules]
    threads = []
    for i in range(0,len(ips)):
        threads.append(Thread(target=learn_from_source, args=(ips[i], insertables[i], 10)))
        threads[-1].start()
    print("threads started")
    for t in threads:
        t.join()
    print("finished :)")

def learn_isolated_nonSharing(robot, insertable, iterations = 1):
    stop_services([robot])
    wait_for_services([robot], [["localhost"]])
    path_to_default_context = os.getcwd() + "/../python/taxonomy/default_contexts/"
    f = open(path_to_default_context + "insertion.json")
    insertion = InsertionFactory2([robot], TimeMetric("insertion", {"time": 5}),
                                        {"Insertable": insertable, "Container": insertable+"_container",
                                        "Approach": insertable+"_container_approach"})
    pd = insertion.get_problem_definition(insertable)
    if insertable == "010_left" or insertable == "023_left" or insertable == "027_left" or insertable == "024_left":
        print("increase limits for ",insertable)
        pd.domain.limits["p2_f_push_z"] = (0,60)
    sc = SVMLearner(300,10,0,True,False, -1,True).get_configuration()
    knowledge = Knowledge()
    dualarm_skills = []
    if insertable != "016_left":
        move_context = {
                    "skill": {
                        "speed": 0.5,
                        "acc": 1,
                        "q_g": [0, 0, 0, 0, 0, 0, 0],
                        "objects": {
                            "goal_pose": "hold"}},
                    "control": {
                        "control_mode": 3},
                    "user": {
                        "env_X": [0.001, 0.001, 0.001, 0.001, 0.001, 0.001],
                        "F_ext_max": [100, 50]}}
        dualarm_skills.append(("move", "MoveToPoseJoint", move_context))
    else:
        call_method(robot,13000,"set_grasped_object",{"object":"016_right"})
        f = open(path_to_default_context + "insertion.json")
        insert_context = json.load(f)
        insert_context["skill"]["objects"]["Container"] = "016_right_container"
        insert_context["skill"]["objects"]["Insertable"] = "016_right"
        insert_context["skill"]["objects"]["Approach"] = "016_right_container_approach"
        dualarm_skills.append(("insert", "TaxInsertion", insert_context))
        f = open(path_to_default_context + "extraction.json")
        extract_context = json.load(f)
        extract_context["skill"]["objects"]["Container"] = "016_right_container"
        extract_context["skill"]["objects"]["Extractable"] = "016_right"
        extract_context["skill"]["objects"]["ExtractTo"] = "016_right_container_approach"
        dualarm_skills.append(("extract", "TaxExtraction", extract_context))

    dualarm_cmd = {"agent":robot,"port":13000,"skills":dualarm_skills,"sleep":1}
    if iterations > 1:
        learn_task(robot, pd, sc, ["noKnowledge", "noSharing", "isolated","PSP","insertion2","run_3"], iterations, True, knowledge.to_dict(),True,8000, dualarm_cmd)
    else:
        learn_single_task(robot, pd, sc, ["noKnowledge", "noSharing", "isolated","PSP","insertion2","run_3"], 0, False, knowledge.to_dict(), False, 8000, dualarm_cmd)

def learn_comparison(modules = list_block_1+list_block_2+list_U):
    ips = get_ips(modules)
    insertables = [m+"_left" for m in modules]
    threads = []
    for i in range(0,len(ips)):
        print("start thread for task ",insertables[i], " on ", ips[i])
        threads.append(Thread(target=learn_isolated_nonSharing, args=(ips[i], insertables[i], 1)))
        threads[-1].start()
    print("threads started")
    for t in threads:
        t.join()
    print("finished :)")
    
def learn_from_trial(source_ip, source_uuid, source_trial_n: list, target_ip, target_instance):
    mongodb_client = MongoDBClient(source_ip)
    source_results = mongodb_client.read("ml_results","insertion",{"meta.uuid":source_uuid})[0]
    for trial_n in source_trial_n:
        theta = source_results["n"+str(trial_n)]["theta"]
        source_tags = source_results["meta"]["tags"]
        source_tags.append("trial_n"+str(trial_n))
        knowledge = Knowledge(None, "similar", ["default_context"], None, None, "insertion", theta, 0.04, None, False, None, [1], "insertion", source_results["meta"]["skill_instance"], source_uuid, None, time.ctime(),source_tags)
        sc = SVMLearner(1,1,0,True,False, -1,True).get_configuration()
        insertable = target_instance
        container = insertable + "_container"
        approach = container + "approach"
        pd = InsertionFactory([target_ip], TimeMetric("insertion", {"time": 5}),
                                    {"Insertable": insertable, "Container": container,
                                    "Approach": approach}).get_problem_definition(insertable)
        pd.cost_function.finish_thr = 2  # undercut cutoff threshold 3 time to stop learning

        if not get_states([insertable[:3]])[0]:
            print(target_ip, " is not ready!")
            break
            
        if insertable == "010_left" or insertable == "023_left" or insertable == "027_left" or insertable == "024_left":
            print("increase limits for ",insertable)
            pd.domain.limits["p2_f_push_z"] = (0,60)
        dualarm_skills = []
        move_context = {
                    "skill": {
                        "speed": 0.5,
                        "acc": 1,
                        "q_g": [0, 0, 0, 0, 0, 0, 0],
                        "objects": {
                            "goal_pose": "hold"}},
                    "control": {
                        "control_mode": 3},
                    "user": {
                        "env_X": [0.001, 0.001, 0.001, 0.001, 0.001, 0.001],
                        "F_ext_max": [100, 50]}}
        dualarm_skills.append(("move", "MoveToPoseJoint", move_context))
        dualarm_cmd = {"agent":target_ip,"port":13000,"skills":dualarm_skills,"sleep":1}
        target_tags = ["transfermapping", "from_"+str()]
        learn_single_task(target_ip, pd, sc, target_tags, 1, False, knowledge.to_dict(), True, 8000, dualarm_cmd)

def transfer_to_all_from_trial(source_ip:str, source_uuid, source_trial_n: list):
    all_modules = list_block_1+list_block_2+list_U
    target_ips = get_ips(all_modules)
    target_instances = [m+"_left" for m in all_modules]
    threads = []
    for target_ip,target_instance in zip(target_ips,target_instances):
        Thread(target=learn_from_trial, args=(source_ip, source_uuid, source_trial_n, target_ip, target_instance))
    for t in threads:
        t.join()

def transfer_learning():
    robots = {"collective-016.rsi.ei.tum.de": "cylinder_50",
              "collective-005.rsi.ei.tum.de": "usb-a",
              "collective-010.rsi.ei.tum.de": "schuko",
              "collective-029.rsi.ei.tum.de": "IEC60320_C13",
              "collective-017.rsi.ei.tum.de": "abus_e30"}
    tasks = ["cylinder_50", "usb-a", "schuko", "IEC60320_C13", "abus_e30"]
    
    sc = SVMLearner(130,10,0,True,False, -1,True).get_configuration()
    #sc = CMAESLearner(10,13,True).get_configuration()
    # learning for base knowledge
    tags = ["transfer_learning","evaluation","base"]  # transfer_learning
    n_current_iter = {}
    for task in tasks:
        n_current_iter[task] = 0
    slowest_iteration = 0
    while slowest_iteration < 10:
        threads = []
        print("Number of slowest iteration: ", slowest_iteration+1,"/10")
        try:
            for robot in robots.keys():
                insertable = robots[robot]
                move_joint(robot,insertable+"_container_above",port=12000)
                if call_method(robot,13000,"get_state")["result"]["grasped_object"] == "NullObject":
                    call_method(robot, 13000, "grasp", {"width":0,"force":100,"speed":1,"epsilon_inner":1,"epsilon_outer":1})
                    call_method(robot, 13000, "set_grasped_object", {"object":insertable+"_hold"})
                    move_joint(robot, insertable+"_hold", port=13000)
                if call_method(robot,12000,"get_state")["result"]["grasped_object"] == "NullObject":
                    grasp_insertable(robot,insertable,insertable+"_container",insertable+"_container_approach",insertable+"_container_above",port=12000)
                knowledge_source = Knowledge()
                knowledge_source.kb_location = "collective-020.rsi.ei.tum.de"
                knowledge_source.mode = "global" 
                knowledge_source.kb_db = "global_knowledge"
                knowledge_source.kb_task_type = "insertion"
                knowledge_source.scope = []
                knowledge_source.scope.extend(tags)
                knowledge_source.scope.append(insertable)
                knowledge_source.scope.append("n"+str(n_current_iter[insertable]+1))
                knowledge_source.type = "all"

                pd = InsertionFactory([robot], TimeMetric("insertion", {"time": 5}),
                                        {"Insertable": insertable, "Container": insertable+"_container",
                                        "Approach": insertable+"_container_approach"}).get_problem_definition(insertable)
                if insertable == "IEC60320_C13" or insertable == "schuko":
                    pd.domain.limits["p2_f_push_z"] = (0, 30)
                dualarm_cmd = {"agent":robot,"port":13000,"sleep":10000,"pose":insertable+"_hold"} ## veraltet!!!
                threads.append(Thread(target=learn_single_task, args=(robot, pd, sc, tags),
                                                                kwargs={'dualarm_cmd':dualarm_cmd, 'wait':True, 'knowledge': knowledge_source.to_dict(),
                                                                        'keep_record':False,'current_number_iterations':n_current_iter[insertable]}))
                threads[-1].start()
            for t in threads:
                t.join()
            # check for completness:
            client = MongoDBClient(knowledge_source.kb_location)
            for robot in robots.keys():
                    task = robots[robot]
                    knowledge_tags = copy.deepcopy(tags)
                    knowledge_tags.extend(["n"+str(n_current_iter[task]+1), task])
                    print("checking ", knowledge_tags," for consistency.")

                    if not client.read("global_knowledge", "insertion",{"meta.tags":knowledge_tags}):
                        robot_db = MongoDBClient(robot)
                        if len(robot_db.read("ml_results","insertion",{"meta.tags":knowledge_tags})) < 133:
                            print("task ",task, " wasn finished properly. Deleting results and do it again.")
                        robot_db.remove("ml_results","insertion",{"meta.tags":knowledge_tags})
                    else:
                        n_current_iter[task] += 1
            kb = ServerProxy("http://" + knowledge_source.kb_location+ ":8001", allow_none=True)
            kb.clear_memory()
            knowledge_source.scope = []
            knowledge_source.tags = []
            del knowledge_source
        except KeyboardInterrupt:
            stop_services(list(robots.keys()))
            return True
        
        slowest_iteration = min(n_current_iter.values())
    
    # restart every robot 
    # for robot in robots.keys():
    #     insertable = robots[robot]
    #     move_joint(robot,insertable+"_hold",wait=True,port=13000)
    #     if place_insertable(robot, insertable, insertable+"_container",insertable+"_container_approach",insertable+"container_above",port=12000):
    #         move(robot,insertable+"_container_above",[0,0,0],wait=True)
    #         call_method(robot, 12000, "reboot")
    #         call_method(robot, 13000, "reboot")
    # time.sleep(600)
    # for robot in robots.keys():
    #     insertable = robots[robot]
    #     call_method(robot, 13000, "grasp", {"width":0,"force":100,"speed":1,"epsilon_inner":1,"epsilon_outer":1})
    #     move_joint(robot,insertable+"_hold",wait=True,port=13000)
    #     grasp_insertable(robot, insertable, insertable+"_container",insertable+"_container_approach",insertable+"container_above",port=12000)
    tags.pop(tags.index("base"))
    #transfer to here: 
    for task in tasks:
        for n_current_iter in range(0,10):
            threads = []
            print("Number of iteration: ", n_current_iter+1,"/10")
            for robot in robots.keys():

                robot_tags = copy.deepcopy(tags)

                insertable = robots[robot]
                knowledge_source = Knowledge()
                knowledge_source.kb_location = "collective-020.rsi.ei.tum.de"
                knowledge_source.mode = "global" 
                knowledge_source.kb_db = "global_knowledge"
                knowledge_source.kb_task_type = "insertion"
                knowledge_source.scope = []
                knowledge_source.scope.extend(robot_tags)
                knowledge_source.scope.append(task)  # search for knowledge of other (or same) insertable
                knowledge_source.scope.append("n"+str(n_current_iter+1))
                knowledge_source.type = "all"
                robot_tags.append("from_"+task)
                pd = InsertionFactory([robot], TimeMetric("insertion", {"time": 5}),
                                        {"Insertable": insertable, "Container": insertable+"_container",
                                        "Approach": insertable+"_container_approach"}).get_problem_definition(insertable)
                threads.append(Thread(target=learn_single_task, args=(robot, pd, sc, robot_tags, n_current_iter, False, knowledge_source.to_dict(), True)))
                threads[-1].start()
            for t in threads:
                t.join()
            # check for completness:
            client = MongoDBClient(knowledge_source.kb_location)
            for robot in robots.keys():
                knowledge_tags = copy.deepcopy(tags)
                knowledge_tags.extend(["n"+str(n_current_iter+1), task])
                print("checking ", knowledge_tags," for consistency.")
                if not client.read("global_knowledge", "insertion",{"meta.tags":knowledge_tags}):
                    robot_db = MongoDBClient(robot)
                    if len(robot_db.read("ml_results","insertion",{"meta.tags":knowledge_tags})) < 133:
                        print("task ",task, " wasn finished properly")
                        
            kb = ServerProxy("http://" + knowledge_source.kb_location+ ":8001", allow_none=True)
            kb.clear_memory()
            knowledge_source.scope = []
            knowledge_source.tags = []
            del knowledge_source

def get_cutoff():
    cutoff = {}
    modules = list_block_1+list_block_2+list_U
    for xxx in modules:
        ip = get_ips([xxx])[0]
        cost_collectiverun = lowest_results(ip, ["visualization_collective"])
        cost_isolatedrun = lowest_results(ip, ["visualization_isolated"])
        if min([cost_collectiverun, cost_isolatedrun]) < 0.2:
            cost = max([cost_collectiverun, cost_isolatedrun])
        elif max([cost_collectiverun, cost_isolatedrun]) > 1.5:
            cost = min([cost_collectiverun, cost_isolatedrun])
        else:
            cost = min([cost_collectiverun, cost_isolatedrun])
        cost = cost*1.2
        cutoff[str(xxx)+"_left"] = cost
    return cutoff

def get_optima_pistop_charlie(tags = ["baseline","iteration_0"]):
    cutoff = {}
    for host, arm in tasks.items():
        for info in arm.values():
            task_list = info["sequence"]
            for task in task_list:
                try:
                    search_tags = tags.copy()
                    search_tags.append(task)
                    lowest_cost = mean_results(host, search_tags)  #lowest_results(host, search_tags)
                except DataNotFoundError:
                    lowest_cost = 0.8
                cutoff[task] = float(lowest_cost*1.2)
    return cutoff

def get_optima_pistop_charlie_localhost(tags = ["baseline","iteration_0"]):
    cutoff = {}
    for host, arm in tasks.items():
        for info in arm.values():
            task_list = info["sequence"]
            for task in task_list:
                try:
                    search_tags = tags.copy()
                    search_tags.append(task)
                    lowest_cost = mean_results("localhost", search_tags)  #lowest_results(host, search_tags)
                except DataNotFoundError:
                    lowest_cost = 0.8
                cutoff[task] = float(lowest_cost*1.2)
    return cutoff

def get_successfull_tasks(tags = ["baseline","iteration_0"]):
    cutoff = {}
    for host, info in tasks.items():
        task_list = info["sequence"]
        for task in task_list:
            try:
                search_tags = tags.copy()
                search_tags.append(task)
                successes = learned_successfull(host, search_tags)
            except DataNotFoundError:
                successes = [False]
            cutoff[task] = successes
    return cutoff

def get_states(modules):
    ips = get_ips(modules)
    states = []
    for ip,xxx in zip(ips,modules):
        print("get state of ",xxx)
        try:
            response = call_method(ip, 12000, "get_state",timeout=3)
        except OSError:
            response = None
        if response == None:
            print("call_method response is ",type(response))
            states.append(False)
            continue
        s = ServerProxy("http://"+ip+":8000", allow_none=True)
        busy = s.is_busy()
        if type(response) is dict:
            try:
                print("grasped object: ",response["result"]["grasped_object"])
                status = response["result"]["current_task"]
                if status == "IdleTask" and not busy:
                    states.append(True)
                else:
                    states.append(False)
                    print("  ",ip, "robot is not ready:\n ml_service is busy", busy, "\n mios-left state:",status)
            except KeyError:
                states.append(False)

    return states

def test_cutoff(cutoff ={ '001_left': 0.7080000000000001,   # best solution found
                '003_left': 0.68016,
                '004_left': 0.74976,
                '005_left': 0.65, #
                '006_left': 0.6127199999999999,
                '007_left': 0.62616,
                '008_left': 0.6371999999999999,
                '010_left': 0.6888000000000001,
                '011_left': 0.63816,
                '012_left': 0.75528,
                '009_left': 0.6943199999999999,
                '013_left': 0.6348,
                '014_left': 0.6,
                '015_left': 0.68184,
                '016_left': 0.9,   #
                '017_left': 0.63864,
                '018_left': 0.63144,
                '021_left': 0.63528,
                '022_left': 0.6828000000000001,
                '023_left': 0.6648000000000001,
                '024_left': 0.9187199999999999,
                '025_left': 0.64752,
                '027_left': 0.68448,
                '028_left': 0.61824,
                '029_left': 0.68088}):
    lowest_index = {}
    modules = list_block_1+list_block_2+list_U
    for xxx in modules:
        ip = get_ips([xxx])[0]
        index_collectiverun = n_trial_until(ip, ["visualization_collective"], cutoff[xxx+"_left"])
        index_isolatedrun = n_trial_until(ip, ["visualization_isolated"], cutoff[xxx+"_left"])
        lowest_index[xxx+"_left"] = min([index_collectiverun,index_isolatedrun])
    return lowest_index


def five_agent_collective(if_reverse = False):
    modules = list_block_1 + list_block_2 + list_U
    cutoff = {  '001_left': 0.7080000000000001,   # best solution found *1.2
                '003_left': 0.68016,
                '004_left': 0.74976,
                '005_left': 0.65, #
                '006_left': 0.6127199999999999,
                '007_left': 0.62616,
                '008_left': 0.6371999999999999,
                '010_left': 0.6888000000000001,
                '011_left': 0.63816,
                '012_left': 0.75528,
                '009_left': 0.6943199999999999,
                '013_left': 0.6348,
                '014_left': 0.6,
                '015_left': 0.68184,
                '016_left': 0.9,   #
                '017_left': 0.63864,
                '018_left': 0.63144,
                '021_left': 0.63528,
                '022_left': 0.6828000000000001,
                '023_left': 0.6648000000000001,
                '024_left': 0.9187199999999999,
                '025_left': 0.64752,
                '027_left': 0.68448,
                '028_left': 0.61824,
                '029_left': 0.68088}
    # sc = SVMLearner(450,10,0,True,False, 0.4,True).get_configuration()
    sc = SVMLearner(450,10,0,True,False, 0.4,True).get_configuration()

    # tags = ["5agents_25tasks","collective"]
    
    if (if_reverse):
        tags = ["5agents_25tasks","collective_reverse"]
        modules.reverse()
    else:
        tags = ["5agents_25tasks","collective"]
        
        
    # for n_current_iter in range(29,30): #range(15,25):   (not reserve)
    for n_current_iter in [0]: # reverse one
        tasks = {}
        #tasks = {"collective-014.rsi.ei.tum.de":["014_left"]}  #  do this task at first
        for xxx in modules: 
            tasks["collective-"+str(xxx)+".rsi.ei.tum.de"] = [str(xxx)+"_left"]
        threads = []
        print("Number of iteration: ", n_current_iter+1)
        knowledge_source = Knowledge()
        knowledge_source.kb_location = "collective-001.rsi.ei.tum.de" # None #  
        knowledge_source.mode = "global"  # None:isolated parallel (no knowledge from theirself)  # "local": has transfer inside agent
        knowledge_source.scope = []
        knowledge_source.scope.extend(tags)
        knowledge_source.scope.append("n"+str(n_current_iter+1)) # searching for knowledge on the database (only works for the slow pipeline);  e.g. [] search all, 
        knowledge_source.type = "all"  # all: 
            
        dualarm_skills = []
        move_context = {
                    "skill": {
                        "speed": 0.5,
                        "acc": 1,
                        "q_g": [0, 0, 0, 0, 0, 0, 0],
                        "objects": {
                            "goal_pose": "hold"}},
                    "control": {
                        "control_mode": 3},
                    "user": {
                        "env_X": [0.001, 0.001, 0.001, 0.001, 0.001, 0.001],
                        "F_ext_max": [100, 50]}}
        dualarm_skills.append(("move", "MoveToPoseJoint", move_context))
        
        kb = ServerProxy("http://" + knowledge_source.kb_location+ ":8001", allow_none=True)
        kb.clear_memory()

        threads = []
        while len(tasks) > 0:
            robot = list(tasks.keys())[0]
            insertable = tasks.pop(robot)[0]  #first index because every robot has just one object
            container = insertable+"_container"
            approach = container+"_approach"
            pd = InsertionFactory([robot], TimeMetric("insertion", {"time": 5}),
                                    {"Insertable": insertable, "Container": container,
                                    "Approach": approach}).get_problem_definition(insertable)
            if not get_states([insertable[:3]])[0]:
                print(robot, "is not ready! Skipping task ",insertable)
                continue
            if insertable in cutoff:
                pd.optimum_thr = cutoff[insertable]
            if insertable == "010_left" or insertable == "023_left" or insertable == "027_left":
                print("increase limits for ",insertable)
                pd.domain.limits["p2_f_push_z"] = (0,60)
            dualarm_cmd = {"agent":robot,"port":13000,"skills":dualarm_skills,"sleep":1}
            threads.append(Thread(target=learn_single_task, args=(robot, pd, sc, tags, n_current_iter, False, knowledge_source.to_dict(), True, 8000, dualarm_cmd)))
            threads[-1].start()
            time.sleep(1)
            server = ServerProxy("http://%s:%s/" %(robot, "8000"))
            if server.start_telemetry("10.157.175.246", 8004):
                print("start sending telemetry")
            while sum([t.is_alive() for t in threads]) >= 5:  # 5agents are running in parallel
                time.sleep(1)

        for t in threads:
            t.join()
        tensor_server = ServerProxy("http://10.157.175.246:8004")
        tensor_server.stop()
        kb = ServerProxy("http://" + knowledge_source.kb_location+ ":8001", allow_none=True)
        kb.clear_memory()
        print("run ", n_current_iter, " finished :)")
    return "finished :)"


def collective_experiment():
    '''
    ToDo: Teach other tasks (all cylinders, USB-C, Keys for 003 and 008)
    '''
    #alt sequence
    # robots = {  "collective-panda-prime": ["key_door"],
    #             "collective-panda-002": ["key_abus_e30"],
    #             "collective-panda-003": ["key_padlock", "key_2"], #
    #             "collective-panda-004": ["cylinder_30", "cylinder_60", "cylinder_40", "cylinder_10", "cylinder_20", "cylinder_50"],#, "cylinder_50"], #  
    #             #"collective-panda-004": [ "cylinder_40", "cylinder_10", "cylinder_20","cylinder_30", "cylinder_60"], # 
    #             "collective-panda-008": ["HDMI_plug", "key_padlock_2", "key_hatch", "key_old"] # 
    #          }
    #default sequence
    robots = {  "collective-panda-prime": ["key_door"],
                "collective-panda-002": ["key_abus_e30"],
                "collective-panda-003": ["key_padlock","key_2"],
                "collective-panda-004": ["cylinder_40", "cylinder_10", "cylinder_20", "cylinder_30", "cylinder_50", "cylinder_60"], #
                "collective-panda-008": ["HDMI_plug", "key_padlock_2", "key_hatch", "key_old"]
            }
    cutoff = {  "key_door":0.25,
                "key_abus_e30": 0.25,
                "key_padlock": 0.25,
                "key_2": 0.25,
                "cylinder_40": 0.45,
                "cylinder_10": 0.5,
                "cylinder_20": 0.35,
                "cylinder_30": 0.4,
                "cylinder_50": 0.35,
                "cylinder_60": 0.55,
                "HDMI_plug": 0.3,
                "key_padlock_2": 0.25,
                "key_hatch": 0.25,
                "key_old": 0.25
                }
    sc = SVMLearner(130,10,0,True,False, 0.4,True).get_configuration()
    #return check_poses(robots)
    tags = ["collective_learning_04_alt"]
    for n_current_iter in range(19,26):
    #for n_current_iter in [7]:
        #check_poses(robots)
        threads = []
        print("Number of iteration: ", n_current_iter+1,"/25")
        knowledge_source = Knowledge()
        knowledge_source.kb_location = "collective-dev-001"
        knowledge_source.mode = "global"
        knowledge_source.scope = []
        knowledge_source.scope.extend(tags)
        knowledge_source.scope.append("n"+str(n_current_iter+1))
        knowledge_source.type = "all"
        for robot in robots.keys():
            threads.append(Thread(target=learn_multiple_tasks, args=(robot, robots[robot], sc, knowledge_source.to_dict(), tags, n_current_iter, cutoff)))
            threads[-1].start()
        for t in threads:
            t.join()
        # check for completness:
        client = MongoDBClient(knowledge_source.kb_location)
        for robot in robots.keys():
            for task in robots[robot]:
                knowledge_tags = tags.copy()
                knowledge_tags.extend(["n"+str(n_current_iter+1), task])
                print("checking ", knowledge_tags," for consistency.")
                if not client.read("global_knowledge", "insertion",{"meta.tags":knowledge_tags}):
                    print("task ",task, " wasn finished properly")
                    return task
        kb = ServerProxy("http://" + knowledge_source.kb_location+ ":8001", allow_none=True)
        kb.clear_memory()
        knowledge_source.scope = []
        knowledge_source.tags = []
        del knowledge_source


def collective_experiment_ext():
    '''
    ToDo: Teach other tasks (all cylinders, USB-C, Keys for 003 and 008)
    '''
    #alt sequence
    # robots = {  "collective-panda-prime": ["key_door"],
    #             "collective-panda-002": ["key_abus_e30"],
    #             "collective-panda-003": ["key_padlock", "key_2"], #
    #             "collective-panda-004": ["cylinder_30", "cylinder_60", "cylinder_40", "cylinder_10", "cylinder_20", "cylinder_50"],#, "cylinder_50"], #  
    #             #"collective-panda-004": [ "cylinder_40", "cylinder_10", "cylinder_20","cylinder_30", "cylinder_60"], # 
    #             "collective-panda-008": ["HDMI_plug", "key_padlock_2", "key_hatch", "key_old"] # 
    #          }
    #default sequence
    robots = {  "collective-panda-prime":   ["key_door"],
                "collective-panda-002":     ["key_abus_e30"],
                "collective-panda-003":     ["key_padlock","key_2"],
                "collective-panda-004":     ["cylinder_40", "cylinder_20", "cylinder_60"], #
                "collective-panda-008":     ["HDMI_plug", "key_padlock_2", "key_hatch", "key_old"],
                "collective-panda-005":     ["cylinder_30","cylinder_10","cylinder_50"]
            }
    cutoff = {  "key_door":0.25,
                "key_abus_e30": 0.25,
                "key_padlock": 0.25,
                "key_2": 0.25,
                "cylinder_40": 0.45,
                "cylinder_10": 0.5,
                "cylinder_20": 0.35,
                "cylinder_30": 0.4,
                "cylinder_50": 0.35,
                "cylinder_60": 0.55,
                "HDMI_plug": 0.3,
                "key_padlock_2": 0.25,
                "key_hatch": 0.25,
                "key_old": 0.25
                }
    sc = SVMLearner(130,10,0,True,False, 0.4,True).get_configuration()
    #return check_poses(robots)
    tags = ["collective_learning_04_ext_alt"]
    for n_current_iter in range(16,26):
    #for n_current_iter in [7]: a
        #check_poses(robots)
        threads = []
        print("Number of iteration: ", n_current_iter+1,"/25")
        knowledge_source = Knowledge()
        knowledge_source.kb_location = "collective-dev-001"
        knowledge_source.mode = "global" 
        knowledge_source.scope = []
        knowledge_source.scope.extend(tags)
        knowledge_source.scope.append("n"+str(n_current_iter+1))
        knowledge_source.type = "all"
        for robot in robots.keys():
            threads.append(Thread(target=learn_multiple_tasks, args=(robot, robots[robot], sc, knowledge_source.to_dict(), tags, n_current_iter, cutoff)))
            threads[-1].start()
        for t in threads:
            t.join()
        # check for completness:
        client = MongoDBClient(knowledge_source.kb_location)
        for robot in robots.keys():
            for task in robots[robot]:
                knowledge_tags = tags.copy()
                knowledge_tags.extend(["n"+str(n_current_iter+1), task])
                print("checking ", knowledge_tags," for consistency.")
                if not client.read("global_knowledge", "insertion",{"meta.tags":knowledge_tags}):
                    robot_db = MongoDBClient(robot)
                    if len(robot_db.read("ml_results","insertion",{"meta.tags":knowledge_tags})) < 133:
                        print("task ",task, " wasn finished properly")
                        return task
        kb = ServerProxy("http://" + knowledge_source.kb_location+ ":8001", allow_none=True)
        kb.clear_memory()
        knowledge_source.scope = []
        knowledge_source.tags = []
        del knowledge_source

def collective_experiment_parallel():
    '''
    ToDo: Teach other tasks (all cylinders, USB-C, Keys for 003 and 008)
    '''
    robots = {  "collective-panda-prime": ["key_door"],
                "collective-panda-002": ["key_abus_e30"],
                "collective-panda-003": ["key_padlock", "key_2"], #
                "collective-panda-004": ["cylinder_30", "cylinder_60", "cylinder_40", "cylinder_10", "cylinder_20", "cylinder_50"], #  
                "collective-panda-008": ["HDMI_plug", "key_padlock_2", "key_hatch", "key_old"] # 
             }
    #default sequence
    #robots = {  "collective-panda-prime": ["key_door"],
    #            "collective-panda-002": ["key_abus_e30"],
    #            "collective-panda-003": ["key_padlock","key_2"],
    #            "collective-panda-004": ["cylinder_40", "cylinder_10", "cylinder_20", "cylinder_30", "cylinder_50", "cylinder_60"], #
    #            "collective-panda-008": ["HDMI_plug", "key_padlock_2", "key_hatch", "key_old"]
    #        }
    cutoff = {  "key_door":0.25,
                "key_abus_e30": 0.25,
                "key_padlock": 0.25,
                "key_2": 0.25,
                "cylinder_40": 0.45,
                "cylinder_10": 0.5,
                "cylinder_20": 0.35,
                "cylinder_30": 0.4,
                "cylinder_50": 0.35,
                "cylinder_60": 0.55,
                "HDMI_plug": 0.3,
                "key_padlock_2": 0.25,
                "key_hatch": 0.25,
                "key_old": 0.25
                }
    sc = SVMLearner(130,10,0,True,False, 0,False).get_configuration()
    #return check_poses(robots)
    tags = ["collective_learning_parallel"]
    for n_current_iter in range(20,22):
    #for n_current_iter in [7]:
        #check_poses(robots)
        threads = []
        print("Number of iteration: ", n_current_iter+1,"/25")
        knowledge_source = Knowledge()
        #knowledge_source.kb_location = "collective-dev-001"
        # knowledge_source.mode = "local"
        knowledge_source.scope = []
        knowledge_source.scope.extend(tags)
        knowledge_source.scope.append("n"+str(n_current_iter+1))
        knowledge_source.type = "all"
        for robot in robots.keys():
            threads.append(Thread(target=learn_multiple_tasks, args=(robot, robots[robot], sc, knowledge_source.to_dict(), tags, n_current_iter, cutoff)))
            threads[-1].start()
        for t in threads:
            t.join()
        # check for completness:
        time.sleep(5)
        for robot in robots.keys():
            client = MongoDBClient(robot)
            for task in robots[robot]:
                filter = []
                filter.extend(tags)
                filter.append("n"+str(n_current_iter+1))
                filter.append(task)
                print("search for results:", filter)
                if not client.read("local_knowledge", "insertion",{"meta.tags":filter}):
                    print("task ",task, " has not created knowledge")
                    data = client.read("ml_results","insertion",{"meta.tags":filter})
                    if len(data) > 1:
                        print("several ml_service entries found...")
                        return task
                    if len(data) < 1:
                        print("no data found on ml_results")
                        return task
                    if len(data[0]) < 132:
                        print("task ",task, " was aborded to early")
                        return task
        #kb = ServerProxy("http://" + knowledge_source.kb_location+ ":8001", allow_none=True)
        #kb.clear_memory()
        knowledge_source.scope = []
        knowledge_source.tags = []
        del knowledge_source

def single_robot_learning():
    #default sequence
    robots = {  "collective-panda-prime": ["key_door"],
                "collective-panda-002": ["key_abus_e30"],
                "collective-panda-003": ["key_padlock","key_2"],
                "collective-panda-004": [ "cylinder_60", "cylinder_40", "cylinder_20"], #
                "collective-panda-005": ["cylinder_10", "cylinder_30", "cylinder_50"],
                "collective-panda-008": ["HDMI_plug", "key_padlock_2", "key_hatch", "key_old"]
            }
    cutoff = {  "key_door":0.25,
                "key_abus_e30": 0.25,
                "key_padlock": 0.25,
                "key_2": 0.25,
                "cylinder_40": 0.45,
                "cylinder_10": 0.5,
                "cylinder_20": 0.35,
                "cylinder_30": 0.4,
                "cylinder_50": 0.35,
                "cylinder_60": 0.55,
                "HDMI_plug": 0.3,
                "key_padlock_2": 0.25,
                "key_hatch": 0.25,
                "key_old": 0.25
                }
    sc = SVMLearner(130,10,0,True,False, 0,False).get_configuration()
    #return check_poses(robots)
    tags = ["single_robot_learning_without"]
    for n_current_iter in range(13,25):
    #for n_current_iter in [7]:
        #check_poses(robots)
        threads = []
        print("Number of iteration: ", n_current_iter+1,"/25")
        knowledge_source = Knowledge()
        #knowledge_source.kb_location = "collective-dev-001"
        knowledge_source.mode = None
        knowledge_source.scope = []
        knowledge_source.scope.extend(tags)
        knowledge_source.scope.append("n"+str(n_current_iter+1))
        knowledge_source.type = "all"
        for robot in robots.keys():
            threads.append(Thread(target=learn_multiple_tasks, args=(robot, robots[robot], sc, knowledge_source.to_dict(), tags, n_current_iter, cutoff)))
            threads[-1].start()
        for t in threads:
            t.join()
        # check for completness:
        time.sleep(5)
        for robot in robots.keys():
            client = MongoDBClient(robot)
            for task in robots[robot]:
                filter = []
                filter.extend(tags)
                filter.append("n"+str(n_current_iter+1))
                filter.append(task)
                print("search for results:", filter)
                if not client.read("local_knowledge", "insertion",{"meta.tags":filter}):
                    print("task ",task, " has not created knowledge")
                    data = client.read("ml_results","insertion",{"meta.tags":filter})
                    if len(data) > 1:
                        print("several ml_service entries found...")
                        return task
                    if len(data) < 1:
                        print("no data found on ml_results")
                        return task
                    if len(data[0]) < 132:
                        print("task ",task, " was aborded to early")
                        return task
        #kb = ServerProxy("http://" + knowledge_source.kb_location+ ":8001", allow_none=True)
        #kb.clear_memory()
        knowledge_source.scope = []
        knowledge_source.tags = []
        del knowledge_source

def single_robot_learning_trans():
    #default sequence
    robots = {  "collective-panda-prime": ["key_door"],
                "collective-panda-002": ["key_abus_e30"],
                "collective-panda-003": ["key_padlock","key_2"],
                "collective-panda-004": [ "cylinder_40", "cylinder_10", "cylinder_20", "cylinder_30", "cylinder_50", "cylinder_60"], # 
                "collective-panda-008": ["HDMI_plug", "key_padlock_2", "key_hatch", "key_old"]
            }
    cutoff = {  "key_door":0.25,
                "key_abus_e30": 0.25,
                "key_padlock": 0.25,
                "key_2": 0.25,
                "cylinder_40": 0.45,
                "cylinder_10": 0.5,
                "cylinder_20": 0.35,
                "cylinder_30": 0.4,
                "cylinder_50": 0.35,
                "cylinder_60": 0.55,
                "HDMI_plug": 0.3,
                "key_padlock_2": 0.25,
                "key_hatch": 0.25,
                "key_old": 0.25
                }
    sc = SVMLearner(130,10,0,True,False, 0,False).get_configuration()
    #return check_poses(robots)
    tags = ["single_robot_learning_trans"]
    for n_current_iter in range(11,25):
    #for n_current_iter in [7]:
        #check_poses(robots)
        print("Number of iteration: ", n_current_iter+1,"/25")
        knowledge_source = Knowledge()
        knowledge_source.kb_location = "collective-dev-001"
        knowledge_source.mode = "global"
        knowledge_source.scope = []
        knowledge_source.scope.extend(tags)
        knowledge_source.scope.append("n"+str(n_current_iter+1))
        knowledge_source.type = "all"
        for robot in robots.keys():
            learn_multiple_tasks(robot, robots[robot], sc, knowledge_source.to_dict(), tags, n_current_iter, cutoff)
        # check for completness:
            time.sleep(5)
            client = MongoDBClient(robot)
            for task in robots[robot]:
                filter = []
                filter.extend(tags)
                filter.append("n"+str(n_current_iter+1))
                filter.append(task)
                print("search for results:", filter)
                if not client.read("local_knowledge", "insertion",{"meta.tags":filter}):
                    print("task ",task, " has not created knowledge")
                    data = client.read("ml_results","insertion",{"meta.tags":filter})
                    if len(data) > 1:
                        print("several ml_service entries found...")
                        return task
                    if len(data) < 1:
                        print("no data found on ml_results")
                        return task
                    if len(data[0]) < 132:
                        print("task ",task, " was aborded to early")
                        return task
        #kb = ServerProxy("http://" + knowledge_source.kb_location+ ":8001", allow_none=True)
        #kb.clear_memory()
        knowledge_source.scope = []
        knowledge_source.tags = []
        del knowledge_source

def run_all():
    #result = collective_experiment_parallel()
    #if result:
    #    return result
    #result = single_robot_learning()
    #if result:
    #    return result
    result = single_robot_learning_trans()
    if result:
        return result

# def collective_experiment(robots):
#     '''
#     ToDo: Teach other tasks (all cylinders, USB-C, Keys for 003 and 008)
#     '''

#     cutoff = {  "key_door":0.25,
#                 "key_abus_e30": 0.25,
#                 "key_padlock": 0.25,
#                 "key_2": 0.25,
#                 "cylinder_40": 0.45,
#                 "cylinder_10": 0.5,
#                 "cylinder_20": 0.35,
#                 "cylinder_30": 0.4,
#                 "cylinder_50": 0.35,
#                 "cylinder_60": 0.55,
#                 "HDMI_plug": 0.3,
#                 "key_padlock_2": 0.25,
#                 "key_hatch": 0.25,
#                 "key_old": 0.25
#                 }
#     sc = SVMLearner(130,10,0,True,False, 0.9,True).get_configuration()
#     #return check_poses(robots)
#     tags = ["collective_learning_alt"]
#     for n_current_iter in range(2,11):
#     #for n_current_iter in [3]:
#         #check_poses(robots)
#         threads = []
#         print("Number of iteration: ", n_current_iter+1,"/10")
#         knowledge_source = Knowledge()
#         knowledge_source.kb_location = "collective-dev-001"
#         knowledge_source.mode = "global"
#         knowledge_source.scope.extend(tags)
#         knowledge_source.scope.append("n"+str(n_current_iter+1))
#         knowledge_source.type = "all"
#         for robot in robots.keys():
#             threads.append(Thread(target=learn_multiple_tasks, args=(robot, robots[robot], sc, knowledge_source.to_dict(), tags, n_current_iter, cutoff)))
#             threads[-1].start()
#         for t in threads:
#             t.join()
#         kb = ServerProxy("http://" + knowledge_source.kb_location+ ":8001", allow_none=True)
#         kb.clear_memory()
#         knowledge_source.scope = []
#         knowledge_source.tags = []
#         del knowledge_source
#     #delete_experiment_data(robots,tags)
#     #delete_global_knowledge("collective-dev-001","global_knowledge_db","insertion",tags)



def horizontal_learning_experiment():

    robots = [  "collective-panda-prime",
                "collective-panda-002",
                "collective-panda-003",
                "collective-panda-004",
                "collective-panda-008"]
    insertables = ["key_door","key_abus_e30","key_padlock","cylinder_30","HDMI_plug"]
    containers = [k+"_container" for k in insertables]
    approaches = [k+"_container_approach" for k in insertables]
    n_immigrants_vector = [2, 4, 6, 8, 0]

    tags = ["horizontal_learning_2"]
    knowledge_source = Knowledge()
    knowledge_source.kb_location = "collective-dev-001"
    # delete results with same tags:
    for r in robots:
        delete_results(r,tags)
    for n_current_iter in range(10):
        for n_immigrant in n_immigrants_vector:
            threads = []
            tags.append("n_immigrants="+str(n_immigrant))
            for i in range(len(robots)):
                pd = InsertionFactory([robots[i]], TimeMetric("insertion", {"time": 5}),
                                    {"Insertable": insertables[i], "Container": containers[i],
                                    "Approach": approaches[i]}).get_problem_definition(insertables[i])
                if insertables[i] == "HDMI_plug":  # increase the limits for HDMI_plug
                    pd.domain.limits["p2_f_push_z"] = (0, 25)
                sc = SVMLearner().get_configuration()
                sc.n_immigrant = n_immigrant
                sc.batch_synchronisation = True
                print(sc.to_dict())
                threads.append(Thread(target=learn_single_task, args=(robots[i], pd, sc, tags, int(n_current_iter), True, knowledge_source.to_dict(), True)))
                threads[-1].start()
            for t in threads:
                t.join()
            tags.pop(-1)
            kb = ServerProxy("http://" + knowledge_source.kb_location+ ":8001", allow_none=True)
            kb.clear_memory()
    print("\nfinished :)\n")

def stop_services(robots:list =[ "collective-panda-prime","collective-panda-002","collective-panda-003","collective-panda-004","collective-panda-008","collective-panda-005"]):
    for r in robots:
        s = ServerProxy("http://" + r + ":8000", allow_none=True)
        try:
            s.stop_service()
        except Exception as e:
            print("Error with robot ",r)
            print(e)

def wait_for_services(robots:list , agents):
    for r,a in zip(robots, agents):
        s = ServerProxy("http://" + r + ":8000", allow_none=True)
        try:
            while not s.is_ready(a):
                time.sleep(0.5)
        except Exception as e:
            print("Error with robot ",r)
            print(e)


def dualarm_demo_thread(robot, obj, tags, sc, knowledge:dict):
    results = []
    try:
        call_method(robot,12000,"stop_task")
        c = 0
        while call_method(robot,13000,"get_state")["result"]["current_task"] != "IdleTask":
                if c>3:
                    return -1
                if call_method(robot,13000,"get_state")["result"]["status"] == "UserStopped":
                    break
                print("sleep")
                c+=1
                time.sleep(1)
        while call_method(robot,12000,"get_state")["result"]["current_task"] != "IdleTask":
                if c>3:
                    return -1
                if call_method(robot,12000,"get_state")["result"]["status"] == "UserStopped":
                    print(obj, "(",robot,") is in userstop")
                    return -1
                print("sleep")
                c+=1
                time.sleep(1)
        

        call_method(robot,13000,"stop_task")
        result_right = move_joint(robot,"hold",13000,True)
        result_left = move_joint(robot,obj+"_container_above",12000,True)
        if not result_left["result"]["task_result"] or not result_right["result"]["task_result"]:
            print("cannot move arm at ", robot," ", obj)
            return 1
        call_method(robot,12000,"set_grasped_objext",{"object":obj})
        current_task = call_method(robot,13000,"get_state")["result"]["current_task"]
        if current_task != "IdleTask":
            return robot+" is not in IdleTask, but" + current_task

        #hold_pose(robot,1000000,13000)
        pd = InsertionFactory([robot], TimeMetric("insertion", {"time": 5}),
                                    {"Insertable": obj, "Container": obj+"_container",
                                    "Approach": obj+"_container_approach"}).get_problem_definition(obj)
        if obj == "010_left" or obj == "023_left" or obj == "027_left":
            print("increase limits for ",obj)
            pd.domain.limits["p2_f_push_z"] = (0,60)

        print("starting ", obj, " on ", robot)
        dualarm_skills = []
        path_to_default_context = os.getcwd() + "/../python/taxonomy/default_contexts/"
        move_context = {
                    "skill": {
                        "speed": 0.5,
                        "acc": 1,
                        "q_g": [0, 0, 0, 0, 0, 0, 0],
                        "objects": {
                            "goal_pose": "hold"}},
                    "control": {
                        "control_mode": 3},
                    "user": {
                        "env_X": [0.001, 0.001, 0.001, 0.001, 0.001, 0.001],
                        "F_ext_max": [100, 50]}}
        dualarm_skills.append(("move", "MoveToPoseJoint", move_context))
        if obj == "016_left":
            call_method(robot,13000,"set_grasped_object",{"object":"016_right"})
            f = open(path_to_default_context + "insertion.json")
            insert_context = json.load(f)
            insert_context["skill"]["objects"]["Container"] = "016_right_container"
            insert_context["skill"]["objects"]["Insertable"] = "016_right"
            insert_context["skill"]["objects"]["Approach"] = "016_right_container_approach"
            dualarm_skills.append(("insert", "TaxInsertion", insert_context))
            f = open(path_to_default_context + "extraction.json")
            extract_context = json.load(f)
            extract_context["skill"]["objects"]["Container"] = "016_right_container"
            extract_context["skill"]["objects"]["Extractable"] = "016_right"
            extract_context["skill"]["objects"]["ExtractTo"] = "016_right_container_approach"
            dualarm_skills.append(("extract", "TaxExtraction", extract_context))
        #dualarm_cmd = {"agent":robot,"port":13000,"skills":[("insert", "TaxInsertion", insert_context),("extract", "TaxExtraction", extract_context)],"sleep":1,"pose":"hold"}
        dualarm_cmd = {"agent":robot,"port":13000,"skills":dualarm_skills,"sleep":1}
        learn_single_task(robot, pd, sc, tags, 100, False, knowledge, False,service_port=8000, dualarm_cmd=dualarm_cmd)
    except ConnectionRefusedError:
        print("ConnectionRefusedError for ", obj, " on ", robot)
    except TypeError:
        print("TypeError for ",obj," on ",robot)

def dualarm_demo2(dualarm_modules = list_block_1+list_block_2+ list_U):   # 
    robots_dualarm = []
    #robots_dualarm.extend(get_ips(list_block_1))
    #robots_dualarm.extend(get_ips(list_block_2))
    #robots_dualarm.extend(get_ips(list_U))
    #robots_dualarm.extend(get_ips(list_external))
    robots_dualarm.extend(get_ips(dualarm_modules))
    modules = []
    modules.extend(dualarm_modules)
    #modules.extend(list_block_1)
    #modules.extend(list_block_2)
    #modules.extend(list_U)
    # modules.extend(list_external)

    threads = []
    sc = SVMLearner(2000,10,0,True,False, 0.4,True).get_configuration()
    tags = ["demorun"]
    knowledge_source = Knowledge()
    knowledge_source.kb_location = robots_dualarm[0] #None  # 
    knowledge_source.mode = "global"  #None  # 
    knowledge_source.scope = []
    knowledge_source.scope.extend(tags)
    #knowledge_source.scope.append("n"+str(n_current_iter+1))
    knowledge_source.type = "all"
    tasks = [
                "D_007",
                "D_012",
                "D_003",
                "D_006",
                "D_002",
                "D_022",
                "D_008",
                "D_009",
                "D_010", 
            ]
    for i in range(len(robots_dualarm)):
        obj = modules[i]+"_left"
        obj = tasks[i]
        threads.append(Thread(target=dualarm_demo_thread, args=(robots_dualarm[i], obj, tags, sc, knowledge_source.to_dict())))
    for t in threads:
        t.start()

    for t in threads:
        t.join()



def stop_dualarm(modules = list_block_1+list_block_2+list_U):
    def stop(r,m):
        try:
            print("stopping ",m,"  (",r,")")
            s=ServerProxy("http://" + r + ":8000", allow_none=True)
            s.stop_service()
            call_method(r,13000,"stop_task")
        except OSError:
            pass
        except ConnectionRefusedError:
            pass
    threads = []
    ips = get_ips(modules)
    for r,m in zip(ips,modules):
        threads.append(Thread(target=stop, args=(r,m)))
    for t in threads:
        t.start()
    for t in threads:
        t.join()


def stop_list(names):
    def stop(r,m):
        try:
            print("stopping ",m,"  (",r,")")
            s=ServerProxy("http://" + r + ":8000", allow_none=True)
            s.stop_service()
            call_method(r,13000,"stop_task")
        except OSError:
            pass
        except ConnectionRefusedError:
            pass
    threads = []
    ips = get_ips(names)
    for r,m in zip(ips,names):
        threads.append(Thread(target=stop, args=(r,m)))
    for t in threads:
        t.start()
    for t in threads:
        t.join()


def transfer_video_grab_insertable(robot: str, insertable: str, container: str, approach: str, above: str):
    # call_method(robot, 12000, "release_object")
    path_to_default_context = os.getcwd() + "/../python/taxonomy/default_contexts/"
    t1 = Task(robot)
    t2 = Task(robot)
    f = open(path_to_default_context + "move_joint.json")
    move_context = json.load(f)
    move_context["skill"]["objects"]["goal_pose"] = above
    f = open(path_to_default_context + "move_cart.json")
    move_fine_context = json.load(f)
    move_fine_context["skill"]["objects"]["GoalPose"] = insertable

    f = open(path_to_default_context + "extraction.json")
    extraction_context = json.load(f)
    extraction_context["skill"]["objects"]["Extractable"] = insertable
    extraction_context["skill"]["objects"]["Container"] = container
    extraction_context["skill"]["objects"]["ExtractTo"] = approach

    t1.add_skill("move", "MoveToPoseJoint", move_context)
    t1.add_skill("move_fine", "TaxMove", move_fine_context)
    t1.start()
    t1.wait()
    call_method(robot, 12000, "grasp_object", {"object": insertable})
    t2.add_skill("extraction", "TaxExtraction", extraction_context)
    t2.start()
    t2.wait()


def transfer_video_place_insertable(robot: str, insertable: str, container: str, approach: str, above: str):
    # call_method(robot, 12000, "grasp_object", {"object": insertable})
    path_to_default_context = os.getcwd() + "/../python/taxonomy/default_contexts/"
    t0 = Task(robot)
    t1 = Task(robot)
    t2 = Task(robot)

    f = open(path_to_default_context + "insertion.json")
    insertion_context = json.load(f)
    insertion_context["skill"]["objects"]["Insertable"] = insertable
    insertion_context["skill"]["objects"]["Container"] = container
    insertion_context["skill"]["objects"]["Approach"] = approach

    insertion_context["skill"]["p2"]["search_a"]= [10, 10, 0, 2, 2, 0]
    insertion_context["skill"]["p2"]["search_f"] = [1, 0.75, 0, 1, 0.75, 0]
    insertion_context["skill"]["p2"]["f_push"] = [0, 0, 20, 0, 0, 0]

    f = open(path_to_default_context + "move_cart.json")
    move_fine_context = json.load(f)
    move_fine_context["skill"]["objects"]["GoalPose"] = above
    f = open(path_to_default_context + "move_joint.json")
    move_context = json.load(f)
    move_context["skill"]["objects"]["goal_pose"] = approach
    #t0.add_skill("move", "MoveToPoseJoint", move_context)
    #t0.add_skill("move_fine", "TaxMove", move_fine_context)
    #t0.start()
    #result = t0.wait()

    t1.add_skill("insertion", "TaxInsertion", insertion_context)
    t1.start()
    result = t1.wait()
    print(result)
    if result["result"]["task_result"]["success"] == True:
        call_method(robot, 12000, "release_object")
    t2.add_skill("move_fine", "TaxMove", move_fine_context)
    t2.add_skill("move", "MoveToPoseJoint", move_context)
    t2.start()
    print(t2.wait())


def transfer_video(robot: str):
    insertables = ["key_old", "key_hatch", "key_pad2", "cylinder_10", "cylinder_20", "cylinder_30", "cylinder_40",
                   "cylinder_50", "cylinder_60"]
    #containers = ["lock_old", "lock_hatch", "lock_pad2", "container_10", "container_20", "container_30", "container_40",
    #               "container_50", "container_60"]
    
    #approaches = ["lock_old_approach", "lock_hatch_approach", "lock_pad_approach2", "container_10_approach", "container_20_approach", "container_30_approach", "container_40_approach",
    #               "container_50_approach", "container_60_approach"]
    #aboves = ["lock_old_above", "lock_hatch_above", "lock_pad_above2", "container_10_above",
    #               "container_20_above", "container_30_above", "container_40_above",
    #               "container_50_above", "container_60_above"]
    containers = [i+"_container" for i in insertables]
    approaches = [i+"_container_approach" for i in insertables]
    aboves = [i+"_container_above" for i in insertables]

    # knowledge = None
    insertables.reverse()
    containers.reverse()
    approaches.reverse()
    aboves.reverse()

    knowledge_parameters = {
        "p0_offset_x": 0.00140444240646354,
        "p0_offset_y": 0.00264740434345461,
        "p0_offset_phi": -1.51937200954519,
        "p0_offset_chi": -0.385589798231194,
        "p1_dx_d": 0.0694536112655875,
        "p1_dphi_d": 0.165282008467206,
        "p1_ddx_d": 0.340845275082904,
        "p1_ddphi_d": 0.259455095050753,
        "p1_K_x": 1163.00980283344,
        "p1_K_phi": 1624.16826815006,
        "p2_dx_d": 0.0797539698958545,
        "p2_dphi_d": 0.324427062148954,
        "p2_ddx_d": 0.0546693868423317,
        "p2_ddphi_d": 0.65033811624599,
        "p2_wiggle_a_x": 5,
        "p2_wiggle_a_y": 5,
        "p2_wiggle_a_phi": 3,
        "p2_wiggle_a_chi": 3,
        "p2_wiggle_f_x": 1.71423072724224,
        "p2_wiggle_f_y": 0.911976394336351,
        "p2_wiggle_f_phi": 1,
        "p2_wiggle_f_chi": 0.637993625800583,
        "p2_wiggle_phi_x": 3.8573608540209,
        "p2_wiggle_phi_y": 1.85088673858876,
        "p2_wiggle_phi_phi": 2.99169007335287,
        "p2_wiggle_phi_chi": 2.47250387188342,
        "p2_K_x": 1253.98806400288,
        "p2_K_y": 887.199718856526,
        "p2_K_z": 1299.36711041056,
        "p2_K_phi": 151.872556530053,
        "p2_K_chi": 50.9881343485834,
        "p2_K_psi": 107.99768198157,
        "p2_f_push_x": 0,
        "p2_f_push_y": 0,
        "p2_f_push_z": 15
    }

    for i in range(len(insertables)):
        if i == 0:
            knowledge = None
        else:
            knowledge = {"type": "similar", "mode": "parameters", "kb_location": "collective-panda-008",
                         "kb_db": "ml_results", "kb_task_type": "insertion", "scope":
                             ["insertion", "cylinder_40", "n1", "video_prior"], "parameters": knowledge_parameters}
        transfer_video_grab_insertable(robot, insertables[i], containers[i], approaches[i], aboves[i])
        learn_insertion(robot, approaches[i], insertables[i], containers[i], ["transfer_video"],
                       knowledge , wait=False)
        s = ServerProxy("http://" + robot + ":8000", allow_none=True)
        input("Press Enter to stop learning.")
        s.stop_service()
        while s.is_busy() is True:
            time.sleep(1)
        input("Press Enter to continue")
        transfer_video_place_insertable(robot, insertables[i], containers[i], approaches[i], aboves[i])



def cmaes_run(modules = None, if_reverse = False):
    if modules is None:
        modules = list_block_1 + list_block_2 + list_U
    cutoff = {  '001_left': 0.7080000000000001,   # best solution found *1.2
                '003_left': 0.68016,
                '004_left': 0.74976,
                '005_left': 0.65, #
                '006_left': 0.6127199999999999,
                '007_left': 0.62616,
                '008_left': 0.6371999999999999,
                '010_left': 0.6888000000000001,
                '011_left': 0.63816,
                '012_left': 0.75528,
                '009_left': 0.6943199999999999,
                '013_left': 0.6348,
                '014_left': 0.6,
                '015_left': 0.68184,
                '016_left': 0.9,   #
                '017_left': 0.63864,
                '041_left': 0.63144,
                '021_left': 0.63528,
                '022_left': 0.6828000000000001,
                '023_left': 0.6648000000000001,
                '024_left': 0.9187199999999999,
                '025_left': 0.64752,
                '027_left': 0.68448,
                '028_left': 0.61824,
                '029_left': 0.68088}
    # sc = SVMLearner(450,10,0,True,False, 0.4,True).get_configuration()
    #sc = SVMLearner(450,10,0,True,False, 0.4,True).get_configuration()
    sc = CMAESLearner(9, 20, False).get_configuration()
    tags = ["isolated", "CMAES", "25Tasks", "9ind20gen","additional_run"]
    #tags = ["test", "CMAEStest"]       
    # for n_current_iter in range(29,30): #range(15,25):   (not reserve)
    for n_current_iter in range(10): # reverse one
        tasks = {}
        for xxx in modules: 
            tasks["collective-"+str(xxx)+".rsi.ei.tum.de"] = [str(xxx)+"_left"]
        threads = []
        print("Number of iteration: ", n_current_iter+1)
        knowledge_source = Knowledge()
        knowledge_source.kb_location = "collective-001.rsi.ei.tum.de" # None #  
        knowledge_source.mode = None   # None:isolated parallel (no knowledge from theirself)  # "local": has transfer inside agent
        knowledge_source.scope = []
        knowledge_source.scope.extend(tags)
        knowledge_source.scope.append("n"+str(n_current_iter+1)) # searching for knowledge on the database (only works for the slow pipeline);  e.g. [] search all, 
        knowledge_source.type = "all"  # all: 
            
        dualarm_skills = []
        move_context = {
                    "skill": {
                        "speed": 0.5,
                        "acc": 1,
                        "q_g": [0, 0, 0, 0, 0, 0, 0],
                        "objects": {
                            "goal_pose": "hold"}},
                    "control": {
                        "control_mode": 3},
                    "user": {
                        "env_X": [0.001, 0.001, 0.001, 0.001, 0.001, 0.001],
                        "F_ext_max": [100, 50]}}
        dualarm_skills.append(("move", "MoveToPoseJoint", move_context))
        
        kb = ServerProxy("http://" + knowledge_source.kb_location+ ":8001", allow_none=True)
        kb.clear_memory()

        threads = []
        while len(tasks) > 0:
            robot = list(tasks.keys())[0]
            insertable = tasks.pop(robot)[0]  #first index because every robot has just one object
            container = insertable+"_container"
            approach = container+"_approach"
            pd = InsertionFactory([robot], TimeMetric("insertion", {"time": 5}),
                                    {"Insertable": insertable, "Container": container,
                                    "Approach": approach}).get_problem_definition(insertable)
            pd.cost_function.finish_thr = 2  # undercut cutoff threshold 3 time to stop learning

            if not get_states([insertable[:3]])[0]:
                print(robot, "is not ready! Skipping task ",insertable)
                continue
            if insertable in cutoff:
                pd.optimum_thr = cutoff[insertable]  
            if insertable == "010_left" or insertable == "023_left" or insertable == "027_left":
                print("increase limits for ",insertable)
                pd.domain.limits["p2_f_push_z"] = (0,60)
            dualarm_cmd = {"agent":robot,"port":13000,"skills":dualarm_skills,"sleep":1}
            threads.append(Thread(target=learn_single_task, args=(robot, pd, sc, tags, n_current_iter, False, knowledge_source.to_dict(), True, 8000, dualarm_cmd)))
            threads[-1].start()
            
        for t in threads:
            t.join()
        kb = ServerProxy("http://" + knowledge_source.kb_location+ ":8001", allow_none=True)
        kb.clear_memory()
        print("run ", n_current_iter, " finished :)")
    return "finished :)"


def psp_run(modules = None, if_reverse = False):
    if modules is None: 
        modules = list_block_1 + list_block_2 + list_U #
    cutoff = {  '001_left': 0.7080000000000001,   # best solution found *1.2
                '003_left': 0.68016,
                '004_left': 0.74976,
                '005_left': 0.65, #
                '006_left': 0.6127199999999999,
                '007_left': 0.62616,
                '008_left': 0.6371999999999999,
                '010_left': 0.6888000000000001,
                '011_left': 0.63816,
                '012_left': 0.75528,
                '009_left': 0.6943199999999999,
                '013_left': 0.6348,
                '014_left': 0.6,
                '015_left': 0.68184,
                '016_left': 0.9,   #
                '017_left': 0.63864,
                '041_left': 0.63144,
                '021_left': 0.63528,
                '022_left': 0.6828000000000001,
                '023_left': 0.6648000000000001,
                '024_left': 0.9187199999999999,
                '025_left': 0.64752,
                '027_left': 0.68448,
                '028_left': 0.61824,
                '029_left': 0.68088}
    # sc = SVMLearner(450,10,0,True,False, 0.4,True).get_configuration()
    sc = SVMLearner(450,10,0,True,False, 0.4,True).get_configuration()
    #sc = CMAESLearner(9, 20, False).get_configuration()
    tags = ["5agents_25tasks_local","isolated_local_noFastPipeline","additional_run"]
    #tags = ["test", "CMAEStest"]       
    # for n_current_iter in range(29,30): #range(15,25):   (not reserve)
    for n_current_iter in range(10): # reverse one
        tasks = {}
        for xxx in modules: 
            tasks["collective-"+str(xxx)+".rsi.ei.tum.de"] = [str(xxx)+"_left"]
        threads = []
        print("Number of iteration: ", n_current_iter+1)
        knowledge_source = Knowledge()
        knowledge_source.kb_location = "collective-001.rsi.ei.tum.de" # None #  
        knowledge_source.mode = None   # None:isolated parallel (no knowledge from theirself)  # "local": has transfer inside agent
        knowledge_source.scope = []
        knowledge_source.scope.extend(tags)
        knowledge_source.scope.append("n"+str(n_current_iter+1)) # searching for knowledge on the database (only works for the slow pipeline);  e.g. [] search all, 
        knowledge_source.type = "all"  # all: 
            
        dualarm_skills = []
        move_context = {
                    "skill": {
                        "speed": 0.5,
                        "acc": 1,
                        "q_g": [0, 0, 0, 0, 0, 0, 0],
                        "objects": {
                            "goal_pose": "hold"}},
                    "control": {
                        "control_mode": 3},
                    "user": {
                        "env_X": [0.001, 0.001, 0.001, 0.001, 0.001, 0.001],
                        "F_ext_max": [100, 50]}}
        dualarm_skills.append(("move", "MoveToPoseJoint", move_context))
        
        kb = ServerProxy("http://" + knowledge_source.kb_location+ ":8001", allow_none=True)
        kb.clear_memory()

        threads = []
        while len(tasks) > 0:
            robot = list(tasks.keys())[0]
            insertable = tasks.pop(robot)[0]  #first index because every robot has just one object
            container = insertable+"_container"
            approach = container+"_approach"
            pd = InsertionFactory([robot], TimeMetric("insertion", {"time": 5}),
                                    {"Insertable": insertable, "Container": container,
                                    "Approach": approach}).get_problem_definition(insertable)
            pd.cost_function.finish_thr = 2  # undercut cutoff threshold 3 time to stop learning

            if not get_states([insertable[:3]])[0]:
                print(robot, "is not ready! Skipping task ",insertable)
                continue
            if insertable in cutoff:
                pd.optimum_thr = cutoff[insertable]  
            if insertable == "010_left" or insertable == "023_left" or insertable == "027_left" or insertable == "024_left":
                print("increase limits for ",insertable)
                pd.domain.limits["p2_f_push_z"] = (0,60)
            dualarm_cmd = {"agent":robot,"port":13000,"skills":dualarm_skills,"sleep":1}
            threads.append(Thread(target=learn_single_task, args=(robot, pd, sc, tags, n_current_iter, False, knowledge_source.to_dict(), True, 8000, dualarm_cmd)))
            threads[-1].start()
            
        for t in threads:
            t.join()
        kb = ServerProxy("http://" + knowledge_source.kb_location+ ":8001", allow_none=True)
        kb.clear_memory()
        print("run ", n_current_iter, " finished :)")
    return "finished :)"

def teach_module(module:dict,port = 12000):
    for robot, insertables in sorted(module.items()):
        ip = get_ips([robot])[0]
        for insertable in insertables:
            input("teach "+insertable+" on "+robot+"?")
            try:
                context = call_method(ip,port,"download_object_context",{"object":insertable})["result"]["context"]
                teach_again = False
                if context["OB_T_TCP"][14] != 0:
                    teach_again = input("modify object kinematics? [y,N]")
                else:
                    teach_again = "y"
            except KeyError:
                teach_again="y"
            if teach_again =="y" or teach_again=="Y":
                hex = input("hexwrench? [y/N]",)
                if hex == "y" or hex == "Y":
                    size=int(input("wrench size [mm]?"))
                    l_short=float(input("length short handle in [m]"))
                    l_long=float(input("length long handle in [m]"))
                    offset = [0.,0.,0.]
                    offset[0]=float(input("grasping offset x [m]"))
                    offset[1]=float(input("grasping offset y [m]"))
                    offset[2]=float(input("grasping offset z [m]"))
                    angle_y=float(input("angle around y-axis [grad]"))
                    angle_x=float(input("angle around x-axis [grad]"))
                    mass=float(input("total weight [kg]"))
                    modify_object_kinematics(ip,insertable,size,l_short,l_long,offset,angle_y,angle_x,mass,mios_port=port)
                else:
                    z_mm=float(input("distance to tip (z-axis) in mm"))
                    y_ang=float(input("angle aroungd y-axis"))
                    mass=float(input("weight in kg"))
                    modify_object_transformations(ip,insertable,z_mm,y_ang=y_ang,mass=mass,mios_port=port)
            teach_insertable(ip, insertable,mios_port=port)
            input("open gripper?")
            call_method(ip,port,"release_object")
        teach_cam = input("teach cameras on "+robot+"?[n,Y]")
        if teach_cam !="n" and teach_cam != "N":
            teach_camera(ip,port)

def teach_insertable(robot:str, insertable:str, mios_port=12000):
    call_method(robot, mios_port, "home_gripper")
    input("Press key to start teaching. [Pose above container, without object]")
    call_method(robot, mios_port, "teach_object", {"object": insertable+"_box_container_above"})
    input("Teach where to grab object")
    call_method(robot, mios_port, "grasp", {"width":0,"speed":0.5,"force":100,"epsilon_outer":1,"epsilon_inner":1})
    time.sleep(2)
    current_finger_width = call_method(robot,mios_port,"get_state")["result"]["gripper_width"]
    call_method(robot,mios_port,"move_gripper",{"speed":1,"force":100,"width":current_finger_width+0.005})
    print("closing gripper")
    call_method(robot, mios_port, "grasp", {"width":0,"speed":1,"force":100,"epsilon_outer":1})
    call_method(robot, mios_port, "teach_object", {"object": insertable, "width":True})
    call_method(robot, mios_port, "set_grasped_object", {"object": insertable})
    
    #time.sleep(1)
    
    #print(call_method(robot, mios_port, "grasp_object", {"object": insertable}))
    input("Teach approach BOX [with object]")
    call_method(robot, mios_port, "teach_object", {"object": insertable+"_box_container_approach"})
    input("Teach container BOX [with object]")
    call_method(robot, mios_port, "teach_object", {"object": insertable+"_box_container"})
    input("Teach insertion above [with object]")
    call_method(robot, mios_port, "teach_object", {"object": insertable+"_container_above"}) 
    input("Teach insertion approach [with object]")
    call_method(robot, mios_port, "teach_object", {"object": insertable+"_container_approach"})
    input("Teach insertion container [with object]")
    call_method(robot, mios_port, "teach_object", {"object": insertable+"_container"})
    call_method(robot, mios_port, "release_object")    

def teach_camera(robot, mios_port=12000):
    call_method(robot,mios_port,"move_gripper",{"width":0,"speed":1,"force":10,"epsilon_inner":1,"epsilon_outer":1})
    keep_teaching = 'y'
    count=0
    while(keep_teaching != 'n'):
        input(str(count)+". camera position left side above")
        call_method(robot, mios_port, "teach_object", {"object": "camera_"+str(count)+"_left_above"})
        input(str(count)+". camera position left side")
        call_method(robot, mios_port, "teach_object", {"object": "camera_"+str(count)+"_left"})
        input(str(count)+". camera position right side above")
        call_method(robot, mios_port, "teach_object", {"object": "camera_"+str(count)+"_right_above"})
        input(str(count)+". camera position right side")
        call_method(robot, mios_port, "teach_object", {"object": "camera_"+str(count)+"_right"})
        keep_teaching = input("keep teaching next object: Teach "+str(count+1)+". objects camera position? [Y/n]") or 'y'
        count += 1
        if keep_teaching != "Y" and keep_teaching != 'y':
            keep_teaching = 'n'
    
#############################################################################
# list_block_1
# list_U
# automatica 
def demo_automatica(modules):
    robots_dualarm = get_ips(modules)    
    print(len(modules),len(robots_dualarm))
    tags = ["dualarm_demo_2", "Frankies_tag"]
    sc = SVMLearner(2000,10,0,True,False, 0.4,True).get_configuration()
    for r,m in zip(robots_dualarm,modules):
        print(r,":  ",m)
        call_method(r,12000,"stop_task")
        if m != "010":
            call_method(r,13000,"stop_task")
            move_joint(r,"hold",13000,False)
        move_joint(r,m+"_left_container_above",12000,False)
        call_method(r,12000,"set_grasped_object",{"object":m+"_left"})

    services = []
    #for r,m in zip(robots_dualarm, modules):
    for i in range(len(modules)):
        r = robots_dualarm[i]
        m = modules[i]
        print(r,":  ",m)
        services.append(ServerProxy("http://" + r + ":8000", allow_none=True))
        if m != "010":
            while call_method(r,13000,"get_state")["result"]["current_task"] != "IdleTask":
                if call_method(r,13000,"get_state")["result"]["status"] == "UserStopped":
                    break
                print("sleep")
                time.sleep(1)
            if call_method(r,13000,"get_state")["result"]["status"] == "UserStopped":
                    continue
            hold_pose(r,10000,13000)
        print(r,":  ",m)
        knowledge_source = Knowledge()
        knowledge_source.kb_location = robots_dualarm[0]
        knowledge_source.mode = "global"
        knowledge_source.scope = []
        knowledge_source.scope.extend(tags)
        #knowledge_source.scope.append("n"+str(n_current_iter+1))
        knowledge_source.type = "all"
        pd = InsertionFactory([r], TimeMetric("insertion", {"time": 5}),
                                    {"Insertable": m+"_left", "Container": m+"_left_container",
                                    "Approach": m+"_left_container_approach"}).get_problem_definition(m+"_left")
        print(pd.skill_instance)
        learn_single_task(r, pd, sc, tags, 100, False, knowledge_source.to_dict(), False,service_port=8000)
        print(m," started.")
    while True:
        input("Pause?")
        for s in services:
            s.pause_service()
        input("start again?")
        for s in services:
            s.resume_service()
            
            
def collective25():
    modules = list_block_1 + list_block_2 + list_U
    cutoff = {  '001_left': 0.6,   # best solution found *1.2
                '003_left': 0.6,
                '004_left': 0.6,
                '005_left': 0.6, #
                '006_left': 0.6,
                '007_left': 0.6,
                '008_left': 0.6,
                '010_left': 0.6,
                '011_left': 0.6,
                '012_left': 0.6,
                '009_left': 0.6,
                '013_left': 0.6,
                '014_left': 0.6,
                '015_left': 0.6,
                '016_left': 0.9,   #
                '017_left': 0.6,
                '018_left': 0.6,
                '021_left': 0.6,
                '022_left': 0.6,
                '023_left': 0.6,
                '024_left': 0.6,
                '025_left': 0.6,
                '027_left': 0.6,
                '028_left': 0.6, # TODO: replace
                '029_left': 0.6}
    sc = SVMLearner(450,10,0,True,False, 0.4,True).get_configuration()
    tags = ["group1","100tasks"]
    # for n_current_iter in range(29,30): #range(15,25):   (not reserve)
    for n_current_iter in [0]: # reverse one
        tasks = {}
        #tasks = {"collective-014.rsi.ei.tum.de":["014_left"]}  #  do this task at first
        for xxx in modules: 
            tasks["collective-"+str(xxx)+".rsi.ei.tum.de"] = [str(xxx)+"_left"]
        threads = []
        print("Number of iteration: ", n_current_iter+1)
        knowledge_source = Knowledge()
        knowledge_source.kb_location = "collective-001.rsi.ei.tum.de" # None #  
        knowledge_source.mode = "global"  # None:isolated parallel (no knowledge from theirself)  # "local": has transfer inside agent
        knowledge_source.scope = [] # TODO: may here add the tag of previous running
        knowledge_source.scope.extend(tags)
        knowledge_source.scope.append("n"+str(n_current_iter+1)) # searching for knowledge on the database (only works for the slow pipeline);  e.g. [] search all, 
        knowledge_source.type = "all"  # all: 
            
        dualarm_skills = []
        move_context = {
                    "skill": {
                        "speed": 0.5,
                        "acc": 1,
                        "q_g": [0, 0, 0, 0, 0, 0, 0],
                        "objects": {
                            "goal_pose": "hold"}},
                    "control": {
                        "control_mode": 3},
                    "user": {
                        "env_X": [0.001, 0.001, 0.001, 0.001, 0.001, 0.001],
                        "F_ext_max": [100, 50]}}
        dualarm_skills.append(("move", "MoveToPoseJoint", move_context))
        
        kb = ServerProxy("http://" + knowledge_source.kb_location+ ":8001", allow_none=True)
        kb.clear_memory()

        threads = []
        while len(tasks) > 0:
            for robot in tasks:
                server = ServerProxy("http://%s:%s/" %(robot, "8000"))
                if len(tasks[robot]) == 0:
                    tasks.pop(robot)
                    continue
                if server.is_busy():
                    continue
                insertable = tasks[robot][0]
                if not check_object(robot, insertable):
                    continue
                if sum([t.is_alive() for t in threads]) >= 10:
                    time.sleep(1)
                    continue
                #TODO: change names
                container = insertable+"_container" 
                approach = container+"_approach"
                pd = InsertionFactory([robot], TimeMetric("insertion", {"time": 5}),
                                        {"Insertable": insertable, "Container": container,
                                        "Approach": approach}).get_problem_definition(insertable)
                if not get_states([insertable[:3]])[0]:
                    print(robot, "is not ready! Skipping task ",insertable)
                    continue
                if insertable in cutoff:
                    pd.optimum_thr = cutoff[insertable]
                if insertable == "010_left" or insertable == "023_left" or insertable == "027_left":
                    print("increase limits for ",insertable)
                    pd.domain.limits["p2_f_push_z"] = (0,60)
                dualarm_cmd = {"agent":robot,"port":13000,"skills":dualarm_skills,"sleep":1}
                threads.append(Thread(target=learn_single_task, args=(robot, pd, sc, tags, n_current_iter, False, knowledge_source.to_dict(), True, 8000, dualarm_cmd)))
                threads[-1].start()
                time.sleep(1)

        for t in threads:
            t.join()
        kb = ServerProxy("http://" + knowledge_source.kb_location+ ":8001", allow_none=True)
        kb.clear_memory()
        print("run ", n_current_iter, " finished :)")
        # TODO: add video recording by call FLO's rpc
    return "finished :)"

def replay_trials(host:str, insertable:str, tags:list, source_tags:list, trials:list):
    client = MongoDBClient(host)
    tmp = client.read("ml_results","insertion",{"meta.tags":source_tags})
    if len(tmp)<1:
        print("cannot find source trials: ", source_tags)
        return False
    thetas = []
    for t in trials:
        thetas.append(tmp[-1]["n"+str(t)]["theta"])
    knowledge = Knowledge()
    knowledge.parameters = thetas
    sc = SVMLearner(len(trials),len(trials),0,True,False, 0,True).get_configuration()
    container = insertable+"_container" 
    approach = container+"_approach"
    pd = InsertionFactory([host], TimeMetric("insertion", {"time": 5}),
                            {"Insertable": insertable, "Container": container,
                            "Approach": approach}).get_problem_definition(insertable)
    pd.n_variations = 5
    pd.variate_only_success = True
    if insertable == "B_010_plugF-2":
                print("increase limits for ",insertable)
                pd.domain.limits["p2_f_push_z"] = (0,60)
    move_context = {
        "skill": {
            "speed": 0.5,
            "acc": 1,
            "q_g": [0, 0, 0, 0, 0, 0, 0],
            "objects": {
                "goal_pose": "hold_"+insertable}},
        "control": {
            "control_mode": 3},
        "user": {
            "env_X": [0.001, 0.001, 0.001, 0.001, 0.001, 0.001],
            "F_ext_max": [100, 50]}}
    dualarm_skills = []
    dualarm_skills.append(("move", "MoveToPoseJoint", move_context))
    dualarm_cmd = {"agent":host,"port":13000,"skills":dualarm_skills,"sleep":1}
    learn_single_task(host, pd, sc, tags, 1, False, knowledge.to_dict(), False, 8000, dualarm_cmd)
    

def robustnes_test():
    '''
    007 is teached to above insted of approach
    005 probably did this result 
    '''
    tasks_orig = {   
        "collective-001.rsi.ei.tum.de":["D_016_extHexScrewdriver-30","A_018","D_007_extHexScrewdriver-10","D_017_extDodScrewdriver-30","B_002_IEC-C7"],
        "collective-003.rsi.ei.tum.de":["D_028", "D_012", "D_005", "D_018", "A_001_triangle-1"],
        "collective-004.rsi.ei.tum.de":["D_020", "D_019", "A_002_hexagon-1"],
        "collective-005.rsi.ei.tum.de":["D_027", "D_026", "B_001_USB-1", "D_006"],
        "collective-006.rsi.ei.tum.de":["D_021", "A_32_pentagon-1","D_002", "D_001" ],
        "collective-007.rsi.ei.tum.de":["D_022", "A_004_cylinder-1","D_011"],
        "collective-008.rsi.ei.tum.de":["008_left","D_008", "D_004","D_013"],
        "collective-036.rsi.ei.tum.de":["D_024", "B_003_plugF-1","D_009","D_014","D_025"],#PC 10 is broken and changed to 36 now
        "collective-011.rsi.ei.tum.de":["B_004_audioJack-35", "D_010", "D_015","D_023"],
        "collective-012.rsi.ei.tum.de":["C_007", "B_005_IEC-C13", "C_006"], #"C_key_05" is lost
        "collective-009.rsi.ei.tum.de":["B_013", "A_005_cylinder-2","A_015_trapezoid","B_017_IT2DE"],
        "collective-013.rsi.ei.tum.de":["C_011", "A_030_shamrock","A_012_ellipsoid-2"],
        "collective-014.rsi.ei.tum.de":["B_016", "B_006_HDMI-1","A_024_moon","C_020"],
        "collective-015.rsi.ei.tum.de":["C_025", "B_012_DE2DE","A_011"],
        #"collective-016.rsi.ei.tum.de":["A_026_cylinder_60", "A_026_cylinder_10","A_026_cylinder_20","A_026_cylinder_30"],  #,,,],"A_026_cylinder_60"
        #"collective-017.rsi.ei.tum.de":["A_013_hexagram", "A_008_square-1","B_015","C_key_12"],
        # Checkt 041 for correct teaching:
        "collective-041.rsi.ei.tum.de":["A_009_hexagon-3","A_021_arrow","A_key_24","C_022"],  # check 41_left
        "collective-021.rsi.ei.tum.de":["A_020_pentagram", "A_010_square-2","C_018","C_019"],
        "collective-022.rsi.ei.tum.de":["C_009", "B_007_audioJack","C_010","C_013"],
        "collective-023.rsi.ei.tum.de":["C_014", "B_008_USB-2","A_019_oneline","C_key_08"],
        "collective-024.rsi.ei.tum.de":["B_014_CN", "C_015", "C_017"],
        "collective-025.rsi.ei.tum.de":["A_025_heart", "A_014_doji-1","A_023_stairs"],
        "collective-026.rsi.ei.tum.de":["B_018","A_016_cross-1","A_022_diamond"],    #["026_left","B-014","A_022_diamond","B-018"],
        "collective-027.rsi.ei.tum.de":["B_010_plugF-2","C_016","C_key_23","A_031_audi"]
        # "collective-040.rsi.ei.tum.de":[], # teach 40
        #"collective-029.rsi.ei.tum.de":["029_left","A_016_sector","A_018_cross-2", "A_016_cross-1"]
        }
    tasks = {}
    for host, insertables in tasks_orig.items():
        tasks[host] = insertables[-1]
    robot_count = 0
    threads = []
    dualarm_skills = []
    sc = SVMLearner(100,100,0,True,False, 0,True).get_configuration()
    tags = ["robustness_test","n3","directly_after_learning"]
    for host,insertable in tasks.items():
       # try:
       #     call_method(host,12000,"set_grasped_object",{"object":insertable},timeout=5)
       #     call_method(host,13000,"set_grasped_object",{"object":"hold_"+insertable},timeout=5)
       # except socket.gaierror:
       #     continue
        if not check_object(host,insertable):
            print("check ", host, insertable)
            continue
        
        client = MongoDBClient(host)
        robot_count += 1
        for result in client.read("ml_results","insertion",{"meta.tags":[insertable,"100collective","ps_charlie", "20agents"]}):
            successful_trials = []
            for trial_n, trial in result.items():
                if trial_n == "meta":
                    continue
                if trial_n == "final_results":
                    continue
                if trial_n == "_id":
                    continue
                if not trial["q_metric"]["success"]:
                    continue

                successful_trials.append(trial)
        if len(successful_trials)<1:
            continue
        best_trial = max(successful_trials, key=lambda d: d["q_metric"]["final_cost"])
        print(host, insertable)
        knowledge = Knowledge()
        knowledge.parameters = []
        for i in range(100): 
            knowledge.parameters.append(best_trial["theta"])
        container = insertable+"_container" 
        approach = container+"_approach"
        pd = InsertionFactory([host], TimeMetric("insertion", {"time": 5}),
                                {"Insertable": insertable, "Container": container,
                                "Approach": approach}).get_problem_definition(insertable)
        move_context = {
            "skill": {
                "speed": 0.5,
                "acc": 1,
                "q_g": [0, 0, 0, 0, 0, 0, 0],
                "objects": {
                    "goal_pose": "hold_"+insertable}},
            "control": {
                "control_mode": 3},
            "user": {
                "env_X": [0.001, 0.001, 0.001, 0.001, 0.001, 0.001],
                "F_ext_max": [100, 50]}}
        dualarm_skills.append(("move", "MoveToPoseJoint", move_context))
        dualarm_cmd = {"agent":host,"port":13000,"skills":dualarm_skills,"sleep":1}
        threads.append(Thread(target=learn_single_task, args=(host, pd, sc, tags, 1, False, knowledge.to_dict(), True, 8000, dualarm_cmd)))
        threads[-1].start()
        time.sleep(1)
            
            
def convergence_test():
    '''
    007 is teached to above insted of approach
    005 probably did this result 
    '''
    tasks_orig = {   
        "collective-001.rsi.ei.tum.de":["B_002_IEC-C7","D_016_extHexScrewdriver-30","A_018","D_007_extHexScrewdriver-10","D_017_extDodScrewdriver-30"],
        "collective-003.rsi.ei.tum.de":["D_028", "D_012", "D_005", "D_018", "A_001_triangle-1"],
        "collective-004.rsi.ei.tum.de":["D_020", "D_019", "A_002_hexagon-1"],
        "collective-005.rsi.ei.tum.de":["D_027", "D_026", "B_001_USB-1", "D_006"],
        #"collective-006.rsi.ei.tum.de":["D_021", "A_32_pentagon-1","D_002", "D_001" ],
        # "collective-007.rsi.ei.tum.de":["D_022", "A_004_cylinder-1","D_011"],
        #"collective-008.rsi.ei.tum.de":["008_left","D_008", "D_004","D_013"],
        "collective-044.rsi.ei.tum.de":["D_024", "B_003_plugF-1","D_009","D_014","D_025"],#PC 10 is broken and changed to 36 now
        
        #"collective-011.rsi.ei.tum.de":["B_004_audioJack-35", "D_010", "D_015","D_023"],
        "collective-012.rsi.ei.tum.de":["C_007", "B_005_IEC-C13", "C_006"], #"C_key_05" is lost
        "collective-043.rsi.ei.tum.de":["B_013", "A_005_cylinder-2","A_015_trapezoid","B_017_IT2DE"],
        "collective-013.rsi.ei.tum.de":["C_011", "A_030_shamrock","A_012_ellipsoid-2"],
        "collective-014.rsi.ei.tum.de":["B_016", "B_006_HDMI-1","A_024_moon","C_020"], 
        "collective-015.rsi.ei.tum.de":["C_025", "B_012_DE2DE","A_011"],
        "collective-016.rsi.ei.tum.de":["A_026_cylinder_30","A_026_cylinder_60", "A_026_cylinder_10","A_026_cylinder_20",],  #,,,],"A_026_cylinder_60"
        "collective-042.rsi.ei.tum.de":["A_013_hexagram", "A_008_square-1","B_015","C_key_12"],
        # # Checkt 041 for correct teaching:
        "collective-041.rsi.ei.tum.de":["A_009_hexagon-3","A_021_arrow","A_key_24","C_022"],  # check 41_left
        "collective-021.rsi.ei.tum.de":["B_RS-232", "A_010_square-2","C_018","C_019"],  #A_020_pentagram is broken
        "collective-022.rsi.ei.tum.de":["C_009", "B_007_audioJack","C_010","C_013"],
        #"collective-023.rsi.ei.tum.de":["C_014", "B_008_USB-2","A_019_oneline","C_key_08"],
        "collective-024.rsi.ei.tum.de":["B_014_CN", "C_015", "C_017"],
        "collective-025.rsi.ei.tum.de":["A_025_heart", "A_014_doji-1","A_023_stairs"],
        "collective-026.rsi.ei.tum.de":["A_016_cross-1","B_018","A_022_diamond"],    #["026_left","B-014","A_022_diamond","B-018"],
        "collective-047.rsi.ei.tum.de":["B_010_plugF-2","C_016","C_key_23","A_031_audi"]
        # "collective-040.rsi.ei.tum.de":[], # teach 40
        #"collective-029.rsi.ei.tum.de":["029_left","A_016_sector","A_018_cross-2", "A_016_cross-1"]
        }
    tasks = {}
    for host, insertables in tasks_orig.items():
        tasks[host] = insertables[0]

    robot_count = 0
    threads = []
    dualarm_skills = []
    control = "joint"  # control of the hold skill
    sc = SVMLearner(1500,10,0,True,False, 0,False).get_configuration()
    #sc = CMAESLearner(10,500,True).get_configuration()
    # sc = OrigPSPLearner(1500,10,0,True,False, 0,False).get_configuration()
    # convergence_test_4 was tagged with origPSP but is was actually normal PSP
    #tags = ["convergence_test_5","5000","success_check", "origPSP"]  # later do with success check -> repeat successful trial 5 times
    #tags = ["convergence_test_6", "500", "success_check", "origPSP", "holdpose"]
    #tags = ["convergence_test_7", "1500", "success_check", "origPSP", "lifted_jointpose","lubricated"]
    # convergence_test_8 is with non optimised poses  -> neglect!
    tags = ["nullspace", "table_insertion", "convergence_test_11","modify_length", "success_check","origPSPenhanced"]
    # tags = ["convergence_test_1","5000"]
    tags = ["nullspace", "table_insertion", "convergence_test_12","modify_length", "success_check","origPSPenhanced","Florian"]
    tags = ["dmeorun"]
    for host,insertable in tasks.items():
        
        insertable = insertable+"_table"
        if not check_object(host,insertable):
            print("check ", host, insertable)
            continue
        
        print(host, insertable)
        knowledge = Knowledge()
        container = insertable+"_container" 
        approach = container+"_approach"
        pd = InsertionFactory([host], TimeMetric("insertion", {"time": 5}),
                                {"Insertable": insertable, "Container": container,
                                "Approach": approach}).get_problem_definition(insertable)
        pd.n_variations = 3
        pd.variate_only_success = True
        if insertable == "B_010_plugF-2" or insertable == "B_013" or insertable == "B_014_CN" or insertable == "B_010_plugF-2" or insertable == "B_016":
                    print("increase limits for ",insertable)
                    pd.domain.limits["p2_f_push_z"] = (0,60)

        move_context = {
            "skill": {
                "speed": 0.5,
                "acc": 1,
                "q_g": [0, 0, 0, 0, 0, 0, 0],
                "objects": {
                    "goal_pose": "hold_"+insertable}},
            "control": {
                "control_mode": 3},
            "user": {
                "env_X": [0.001, 0.001, 0.001, 0.001, 0.001, 0.001],
                "F_ext_max": [100, 50]}}
        hold_context = {
            "skill": {
                "t_max": 3600,
            },
            "control": {
                "control_mode": 1,
                "joint_imp":{
                    "K_theta":[10000,10000,10000,10000,10000,10000,10000]
                }
                
            },
            "user": {"F_ext_max": [100, 50]}
        }
        if control == "cart":
            hold_context["control"] = { "control_mode": 0,
                                        "cart_imp": {
                                            "K_x": [3000, 3000, 3000, 200, 200, 200]
                                            }
                                        }
        dualarm_skills.append(("move", "MoveToPoseJoint", move_context))
        dualarm_skills.append(("hold", "HoldPose", hold_context))
        dualarm_cmd = {"agent":host,"port":13000,"skills":dualarm_skills,"sleep":1}
        threads.append(Thread(target=learn_single_task, args=(host, pd, sc, tags, 0, False, knowledge.to_dict(), True, 8000, dualarm_cmd)))
        threads[-1].start()
        time.sleep(1)
             

def start_local_learning():
    #used at stanford
    robot = "172.24.101.217"
    grasp_insertable(robot, "key","key_container","key_container_approach_offset")
    learn_insertion(robot,"key_container_approach","key","key_container",["without_knowledge"],n_iterations=1)
    sc = SVMLearner(130,10,0,False,False, 0,False).get_configuration()
    tags = ["demorun"]
    knowledge = Knowledge()
    knowledge.kb_location = "collective-001.rsi.ei.tum.de"
    knowledge.mode = "global"  # None:isolated parallel (no knowledge from theirself)  # "local": has transfer inside agent
    knowledge.scope = [] # TODO: may here add the tag of previous running
    knowledge.scope.extend(tags)
    # knowledge.scope.append("n"+str(n_current_iter+1)) # searching for knowledge on the database (only works for the slow pipeline);  e.g. [] search all, 
    knowledge.type = "all"  # all: 
    learn_multiple_tasks(robot, ["key"], sc, knowledge.to_dict(), tags, 1, {"key":0.6,})
    wiggle_context = {
        "skill": {
            "dX_fourier_a_a": [0, 0.05, 0.05, 0, 0, 0],
            "dX_fourier_a_phi": [0, 1.5, 0.0, 0, 0, 0],
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
    t = Task(robot)
    t.add_skill("success", "GenericWiggleMotion", wiggle_context)
    t.start(False)
    return t.wait()

def start_learning():
    '''
    007 is teached to above insted of approach
    005 probably did this result 
    '''
    tasks_orig = {   
        "collective-001.rsi.ei.tum.de":["B_002_IEC-C7","D_016_extHexScrewdriver-30","A_018","D_007_extHexScrewdriver-10","D_017_extDodScrewdriver-30"],
        "collective-003.rsi.ei.tum.de":["D_028", "D_012", "D_005", "D_018", "A_001_triangle-1"],
        "collective-004.rsi.ei.tum.de":["D_020", "D_019", "A_002_hexagon-1"],
        "collective-005.rsi.ei.tum.de":["D_027", "D_026", "B_001_USB-1", "D_006"],
        #"collective-006.rsi.ei.tum.de":["D_021", "A_32_pentagon-1","D_002", "D_001" ],
        "collective-007.rsi.ei.tum.de":["D_022", "A_004_cylinder-1","D_011"],
        "collective-008.rsi.ei.tum.de":["008_left","D_008", "D_004","D_013"],
        "collective-044.rsi.ei.tum.de":["D_024", "B_003_plugF-1","D_009","D_014","D_025"],#PC 10 is broken and changed to 36 now
        
        #"collective-011.rsi.ei.tum.de":["B_004_audioJack-35", "D_010", "D_015","D_023"],
        "collective-033.rsi.ei.tum.de":["D_023"],  # replacement for 011
        #"collective-012.rsi.ei.tum.de":["C_007", "B_005_IEC-C13", "C_006"], #"C_key_05" is lost
        "collective-035.rsi.ei.tum.de":["C_007"],  # replacement for 012
        #"collective-043.rsi.ei.tum.de":["B_013", "A_005_cylinder-2","A_015_trapezoid","B_017_IT2DE"],
        "collective-013.rsi.ei.tum.de":["C_011", "A_030_shamrock","A_012_ellipsoid-2"],
        "collective-014.rsi.ei.tum.de":["B_016", "B_006_HDMI-1","A_024_moon","C_020"], 
        "collective-015.rsi.ei.tum.de":["C_025", "B_012_DE2DE","A_011"],
        "collective-016.rsi.ei.tum.de":["A_026_cylinder_30", "A_026_cylinder_60", "A_026_cylinder_10","A_026_cylinder_20"],  #,,,],"A_026_cylinder_60"
        "collective-042.rsi.ei.tum.de":["mercedes_star", "A_008_square-1","B_015","C_key_12"],  #,"A_013_hexagram" is broken
        # # Checkt 041 for correct teaching:
        "collective-041.rsi.ei.tum.de":["A_009_hexagon-3","A_021_arrow","A_key_24","C_022"],  # check 41_left
        "collective-021.rsi.ei.tum.de":["B_RS-232", "A_010_square-2","C_018","C_019"],  #A_020_pentagram is broken
        "collective-022.rsi.ei.tum.de":["C_009", "B_007_audioJack","C_010","C_013"],
        "collective-023.rsi.ei.tum.de":["C_014", "B_008_USB-2","A_019_oneline","C_key_08"],
        "collective-024.rsi.ei.tum.de":["B_014_CN", "C_015", "C_017"],
        "collective-025.rsi.ei.tum.de":["A_025_heart", "A_014_doji-1","A_023_stairs"],
        "collective-026.rsi.ei.tum.de":["A_016_cross-1","B_018","A_022_diamond"],    #["026_left","B-014","A_022_diamond","B-018"],
        "collective-047.rsi.ei.tum.de":["B_010_plugF-2","C_016","C_key_23","A_031_audi"]
        # "collective-040.rsi.ei.tum.de":[], # teach 40
        #"collective-029.rsi.ei.tum.de":["029_left","A_016_sector","A_018_cross-2", "A_016_cross-1"]
    }
    tasks = {}
    for host, insertables in tasks_orig.items():
        tasks[host] = insertables[0] + "_table" 
   # tasks["172.24.69.1"] = ["key","hexagon_27","A_015"]
    threads = []
    sc = SVMLearner(1500,10,0,True,False, 0,False).get_configuration()
    tags = ["nullspace", "table_insertion","modify_length", "success_check","origPSPenhanced", "global_knowledge", "stanford"]
    tags = ["demorun"]
    knowledge = Knowledge()
    knowledge.kb_location = "collective-001.rsi.ei.tum.de"
    knowledge.mode = "global"  # None:isolated parallel (no knowledge from theirself)  # "local": has transfer inside agent
    knowledge.scope = [] # TODO: may here add the tag of previous running
    knowledge.scope.extend(tags)
    # knowledge.scope.append("n"+str(n_current_iter+1)) # searching for knowledge on the database (only works for the slow pipeline);  e.g. [] search all, 
    knowledge.type = "all"  # all: 
        
    #print("deleting knowledge on 172.24.69.1")

    #threads.append(Thread(target=learn_multiple_tasks, 
    #                      args=("172.24.69.1", ["key", "hexagon_27", "A_015"], sc, knowledge.to_dict(), tags, 0, {"key":0.6,"hexagon_27":0.6,"A_015":0.6})))
    #threads[-1].start()

    for host,insertable in tasks.items():
        if not get_states([host[11:14]]):
            continue
        
        #if insertable not in ("key","hexagon_27","A_015"):
        #    insertable = insertable+"_table"
        if not check_object(host,insertable):
            print("check ", host, insertable)
            continue
        
        print(host, insertable) 

        print("deleting knowledge on", host)
        
        container = insertable+"_container" 
        approach = container+"_approach"
        pd = InsertionFactory([host], TimeMetric("insertion", {"time": 5}),
                                {"Insertable": insertable, "Container": container,
                                "Approach": approach}).get_problem_definition(insertable)
        #pd.n_variations = 1
        #pd.variate_only_success = True
        if insertable == "B_010_plugF-2" or insertable == "B_013" or insertable == "B_014_CN" or insertable == "B_010_plugF-2" or insertable == "B_016":
                    print("increase limits for ",insertable)
                    pd.domain.limits["p2_f_push_z"] = (0,60)
        threads.append(Thread(target=learn_single_task, args=(host, pd, sc, tags, 0, False, knowledge.to_dict(), True, 8000)))
        threads[-1].start()
        time.sleep(1)
 


def check_object(host, obj):
    try:
        result = call_method(host, 12000, "get_state", timeout=2)
    except OSError:
        result = None
    if result is None:
        return False
    if type(result) == dict:
        if result["result"]["grasped_object"] == obj:
            return True
        else:
            move_joint(host, "raise_hand")
            print("wainting for ",host, " to grasp ", obj)
            return False

def remote_command(ip: str, command: str, *args):
    """
    Executes a specified command on a remote XML-RPC server with variable arguments.

    This function dynamically calls a remote method based on the 'command' string.

    Args:
        ip (str): The IP address or hostname of the remote XML-RPC server.
        command (str): The name of the method to execute on the server (e.g., "add", "system.listMethods").
        *args: A variable number of arguments to pass to the remote method.

    Returns:
        The result from the remote command, or None if an error occurred.
    """
    # Construct the full URL for the server proxy.
    # The f-string is a modern and readable way to format strings.
    server_url = f"http://{ip}:8010"
    print(f"Attempting to connect to {server_url} for {command} with {str(args)}...")

    try:
        # Using a 'with' statement is good practice, though not strictly required
        # for ServerProxy. It can help manage resources in more complex scenarios.
        with ServerProxy(server_url, allow_none=True) as s:
            method_to_call = getattr(s, command)
            result = method_to_call(*args)
            return result

    except Fault as e:
        # A Fault is a specific error raised by the XML-RPC server itself
        # (e.g., method not found, invalid parameters).
        print(f"An XML-RPC Fault occurred {ip}:")
        print(f"  Fault Code: {e.faultCode}")
        print(f"  Fault String: {e.faultString}\n")
        return None
    except AttributeError:
        # getattr() will raise an AttributeError if the command (method)
        # does not exist on the server.
        print(f"Error: The command '{command}' does not exist on the remote server.\n")
        return None
    except ConnectionRefusedError:
        print(f"Error: Connection was refused. Is the server running at {ip}?\n")
        return None
    except Exception as e:
        # Catch any other potential exceptions (e.g., network issues).
        print(f"An unexpected error occurred: {e}\n")
        return None

def module_command(ip:str|list,command:str,*args, wait=False):
    threads = []
    if type(ip) is list:
        for m in ip:
            threads.append(Thread(target=remote_command,args=(m,command, *args)))
            threads[-1].start()
    else:
        threads.append(Thread(target=remote_command,args=(ip,command, *args)))
        threads[-1].start()
    if wait:
        for t in threads:
            t.join()

def delete_experiment(name):
    global_client = MongoDBClient("collective-049.rsi.ei.tum.de")
    for col in global_client.get_collections("modules"):
        if global_client.remove("modules",col, {"meta.experiment":name}):
            print("removed "+name+" from modules."+col)
    if global_client.remove("fast_knowledge_pipe","insertion",{"tags":[name]}):
        print("removed knowledge from fast knowledge pipe")
    if global_client.remove("global_knowledge","insertion",{"meta.tags":[name]}):
        print("removed global knowledge ")
    if global_client.remove("global_ml_results","insertion",{"meta.tags":[name]}):
        print("removed global ml_results")
        
    global_client.client.drop_database(name)
    print("remove all remaining data of experiment "+name+" from gloabl database.")
    print("\nremoving now local data...\n")
    for host,task in tasks.items():
        delete_results(host,[name])
        client = MongoDBClient(host)
        for obj in client.get_collections("similarities"):
            if client.remove("similarities",obj,{"tags":[name]}):
                print("removed similarites for "+obj+" on "+host)

def delete_experiment_iteration(tags):
    global_client = MongoDBClient("collective-049.rsi.ei.tum.de")
    #for col in global_client.get_collections("modules"):
    #    if global_client.remove("modules",col, {"meta.experiment":name}):
    #        print("removed "+tags[0]+" from modules."+col)
    if global_client.remove("fast_knowledge_pipe","insertion",{"tags":tags}):
        print("removed knowledge from fast knowledge pipe")
    if global_client.remove("global_knowledge","insertion",{"meta.tags":tags}):
        print("removed global knowledge ")
    if global_client.remove("global_ml_results","insertion",{"meta.tags":tags}):
        print("removed global ml_results")
        
    #global_client.client.drop_database(name)
    global_client.delete_collection(tags[0],"iteration_"+tags[1])
    print("remove all remaining data of experiment "+tags[0]+" from gloabl database.")
    print("\nremoving now local data...\n")
    for host,task in tasks.items():
        delete_results(host,tags)
        client = MongoDBClient(host)
        for obj in client.get_collections("similarities"):
            if client.remove("similarities",obj,{"tags":tags}):
                print("removed similarites for "+obj+" on "+host)

def rename_experiment(tags,replacement):
    '''
    replacement = [(tag1, replacement_tag1),(tag2, replacement_tag2),...]
    '''

    for host, t in tasks.items():
        client = MongoDBClient(host)
        for task in t["sequence"]:
            search_tags = copy.deepcopy(tags)
            search_tags.append(task)
            docs = client.read("ml_results","insertion",{"meta.tags":search_tags})
            if len(docs)==0:
                print("No ml_results found for ",task,search_tags)
                continue
            if len(docs)>1:
                print("multiple ml_results found for ",task, host)
                #continue
            for d in docs:
                    for r in replacement:
                        found_tags = d["meta"]["tags"]
                        index = found_tags.index(r[0])
                        print(task,"remove ",found_tags.pop(index), "replace by ",r[1])
                        found_tags.insert(index,r[1])
                        #client.update("ml_results","insertion",{"_id":d["_id"]},{"meta.tags":found_tags})
def remove_double_pitstop_results(tags):
    for host,t in tasks.items():
        for task in t["sequence"]:
            module = host[11:14]
            search_tags = copy.deepcopy(tags)
            search_tags.append(task)
            delete_double_results([module],search_tags,keep_newest=False)


def calculate_similarity(host, insertable, experiments = ["pitstop_charlie2","pitstop_charlie_test"]):
    #filter = {"$or":[{"meta.tags":["pitstop_charlie2","iteration_6"]}, {"tags":{"$all":["pitstop_charlie2"]}}]}
    filter = {"$or":[]}
    for exp in experiments:
        filter["$or"].append({"meta.tags":{"$all":[insertable, exp]}})
    print(filter)
    results = get_multiple_experiment_data(host,"insertion","ml_results",filter=filter)
    similarity = {}
    for r in results:
        for obj, costs in r.get_external_cost_per_object().items():
            if obj == insertable:
                continue
            if obj not in similarity:
                similarity[obj] = []
            similarity[obj].extend(costs)
            if float('inf') in costs or float('nan') in costs:
                print("inf or NaN found >.<")
    for obj, costs in similarity.items():
        similarity[obj] = 1-np.mean(costs)
        if similarity[obj] < 0:
            similarity[obj] = 0

    similarity_sum = sum(similarity.values())
    if not similarity_sum == 0:
        for key in similarity.keys():  #normalize request probabilities
            similarity[key] = float(similarity[key] / similarity_sum)  # calculate probability for picking trial from this agent (=key)
    print(sum(similarity.values()))
    return similarity 

def best_external_knowledge(experiments=["pitstop_charlie2"]):
    filter = {"$or":[]}
    for exp in experiments:
        filter["$or"].append({"meta.tags":{"$all":[exp]}})
    print(filter)
    external_object_count = {}
    for host in tasks.keys():
        results =  get_multiple_experiment_data(host,"insertion","ml_results",filter=filter)
        for r in results:
            for obj,costs in r.get_external_cost_per_object().items():
                if obj not in external_object_count.keys():
                    external_object_count[obj] = 0
                external_object_count[obj] += len([True for cost in costs if cost <= 1.0])  #only count successes
    return external_object_count




def pitstop_chalie_transfer(obj = False, times=False,wait=False,knowledge_host=False):
    # TODO: make sure the videos and datasets are stored inside the same folder
     #  TODO: überarbeite collective module, experiment and manager sodass das datenset in den richtigen ordner landet
    from collective_manager.collective_manager import CollectiveManager
        #tasks = {  #left
                    #"collective-001.rsi.ei.tum.de":["abus-e30_1","abus-e30_2","usb-a_2","schuko_3"],
                    #"collective-005.rsi.ei.tum.de":["f3_1", "abus-e30_9", "abus-d6x_2","vga_3"],
                    #"collective-004.rsi.ei.tum.de":["burgwächter-spash_1","abus-e30_3","BS1363_1","vga_2"],
                    #"collective-008.rsi.ei.tum.de":["schuko_2","stabilit_1","cylinderlock-small_2","oldkey_2"],
                    #'collective-044.rsi.ei.tum.de': [  'hdmi_2','usb-c_1', 'hexkey-19_1', 'hexkey-17_1','abus-e30_5']
        #}
    

    #exp_name = "baseline"
    #iteration = 8
    knowledge_origin = "abus-e30_2"  # "cylinder10_1" dislayport, hexkey-27, schuko_2
    if obj:
        knowledge_origin = obj
    exp_name = "transfer_from_"+knowledge_origin
    #exp_name = "test_knowledge_transfer"
    
    iteration = 2  # make 9 to 10 because baseline 9 doent exist
    if times:
        iteration = times
    knowledge_ip = "collective-001.rsi.ei.tum.de"
    if knowledge_ip:
        knowledge_ip = knowledge_host

    global_db_ip = "10.157.175.0"
    if not obj:
        input(f"start {exp_name} with iteration {iteration}")
    for host, arm in tasks.items():
        print("set camera positions for ",host)
        s = ServerProxy("http://"+host+":8010",allow_none=True)
        for side in arm.keys():
            camera_positions = arm[side]["camera_positions"]
            if side == "left":
                s.set_available_objects(camera_positions, "left")
            else:
                s.set_available_objects(camera_positions, "right")
    module_command(list(tasks.keys()),command="reset",wait=False)
    cutoff = get_optima_pistop_charlie(["baseline"])
    for host in tasks.keys():
        s = ServerProxy("http://"+host+":8010",allow_none=True)
        for side in tasks[host].keys():
            message_count=0
            while not s.is_reseted(side):
                if message_count<1:
                    print("waiting for module ",host," to reset side "+side)
                    message_count+=1
                time.sleep(1)
    pds = []
    scs = []
    knowledges = []
    arms = []
    modules = []
    tasks_copy = deepcopy(tasks)
    print("\n\n")
    while tasks_copy:
        for host in tasks_copy:
            for arm in tasks_copy[host].keys():
                insertable = tasks_copy[host][arm]["sequence"].pop(0)
                print(host,": ",insertable)
                pds.append(InsertionFactory([list(tasks.keys())[0]], TimeMetric("insertion", {"time": 5}),
                                            {"Insertable": insertable, "Container": insertable+"_container",
                                            "Approach": insertable+"_container_approach"}).get_problem_definition(insertable))
                pds[-1].host = host
                pds[-1].optimum_thr = cutoff[insertable]
                pds[-1].cost_function.finish_thr = 2 
                pds[-1].n_variations = 3
                pds[-1].variate_only_success = True
                if insertable=="cylinder60_1" or insertable=="ha-24e-m_1" :  # increase the limits for HDMI_plug
                    pds[-1].domain.limits["p2_f_push_z"] = (0, 60)
                if insertable=="schuko_1" or insertable=="schuko_2":
                    pds[-1].domain.limits["p2_f_push_z"] = (0, 80)
                if insertable[:13] == "padlock-small":
                    pds[-1].domain.limits["p2_f_push_z"] = (0, 10)

                modules.append(host)

                arms.append(arm)
                #n_trials: int = 130,batch_width: int = 10,n_immigrant,exploration_mode,batch_synchronisation, request_probability, request_probability_decrease
                #scs.append(SVMLearner(160,10,0,True,False, 0,False).get_configuration())
                scs.append(SVMLearner(130,10,0,False,False, 0,False).get_configuration())
                
                knowledge = Knowledge()
                #knowledge.kb_location = global_db_ip # collective-049 #"collective-nas.rsi.ei.tum.de"
                knowledge.kb_location = knowledge_ip
                #knowledge.mode = None # "global"  # None:isolated parallel (no knowledge from theirself)  # "local": has transfer inside agent
                knowledge.mode = "specific" # "global"  # None:isolated parallel (no knowledge from theirself)  # "local": has transfer inside agent
                
                knowledge.scope = ["baseline","iteration_"+str(iteration)] # 
                knowledge.scope.extend([knowledge_origin])  
                # knowledge.scope.append("n"+str(n_current_iter+1)) # searching for knowledge on the database (only works for the slow pipeline);  e.g. [] search all, 
                knowledge.type = "all"  # all: 
                knowledge.kb_task_type = "insertion"
                knowledge.kb_db = "local_knowledge"
                knowledges.append(copy.deepcopy(knowledge))

        for host in list(tasks_copy.keys()):
            for arm in list(tasks_copy[host].keys()):
                if not tasks_copy[host][arm]["sequence"]:
                    tasks_copy[host].pop(arm)
        for host in list(tasks_copy.keys()):
            if not tasks_copy[host]:
                tasks_copy.pop(host)
    #s = ServerProxy("http://" + "collective-001.rsi.ei.tum.de" + ":"+str(8000), allow_none=True)
    #current_problem_uuid = s.start_service(pds[1].to_dict(), scs[1].to_dict(), [pds[1].host], knowledges[1].to_dict()) 
    #return current_problem_uuid
    
    print(pds[0].identity)
    #return True
    # s = ServerProxy("http://" + "10.157.174.169" + ":"+str(8000), allow_none=True)
    # current_problem_uuid = s.start_service(pds[0].to_dict(), scs[0].to_dict(), [pds[0].host], knowledges[0].to_dict()) 
    # return current_problem_uuid
    
    for i in range(0,len(pds)):
        pds[i] = pds[i].to_dict()
        scs[i] = scs[i].to_dict()
        knowledges[i] = knowledges[i].to_dict()
        print("types pd, sc, knowledge: ",type(pds[i]),type(scs[i]),type(knowledges[i]))
    
    print("start collective manager")
    manager = CollectiveManager(list(tasks.keys()),global_db_ip)
    #manager.remove_experiment("charli_test_2")
    #manager.add_module(["collective-001.rsi.ei.tum.de"])

    manager.add_experiment(name=exp_name,
                           modules=modules,
                           problem_definitions=pds,
                           knowledge_configs=knowledges,
                           service_configs=scs,
                           arms=arms,
                           n_agents=len(tasks),
                           keep_allocation=False,
                           iteration=iteration)
    manager.start_experiment(exp_name)
    t_0=time.time()
    if wait:
        while time.time() - t_0 < wait:
            time.sleep(30)
    return True

def transfer_exp():
    #dislayport, hexkey-27, schuko_2
    for i in range(3):
        pitstop_chalie_transfer("schuko_2",i,wait=2.25*60*60,knowledge_host='collective-008.rsi.ei.tum.de')
        

    #manager.start_rpc_server()

    # count = 0
    # while True:
    #     exp = manager.describe_experiment("charli_test")
    #     if count == 300:
    #         count = 0
    #         print(exp)  #print every 5min
    #     if not exp["running"]:
    #         break
    #     time.sleep(5)

        

def pitstop_chalie_baseline():
    # TODO: make sure the videos and datasets are stored inside the same folder
     #  TODO: überarbeite collective module, experiment and manager sodass das datenset in den richtigen ordner landet
    from collective_manager.collective_manager import CollectiveManager
        #tasks = {  #left
                    #"collective-001.rsi.ei.tum.de":["abus-e30_1","abus-e30_2","usb-a_2","schuko_3"],
                    #"collective-005.rsi.ei.tum.de":["f3_1", "abus-e30_9", "abus-d6x_2","vga_3"],
                    #"collective-004.rsi.ei.tum.de":["burgwächter-spash_1","abus-e30_3","BS1363_1","vga_2"],
                    #"collective-008.rsi.ei.tum.de":["schuko_2","stabilit_1","cylinderlock-small_2","oldkey_2"],
                    #'collective-044.rsi.ei.tum.de': [  'hdmi_2','usb-c_1', 'hexkey-19_1', 'hexkey-17_1','abus-e30_5']
        #}
    

    exp_name = "baseline"
    iteration = 0
    global_db_ip = "10.157.175.0"
    cutoff = get_optima_pistop_charlie(["baseline"])
    
    for host, task_dict in tasks.items():
        print("set camera positions for ",host)
        s = ServerProxy("http://"+host+":8010",allow_none=True)
        camera_positions = task_dict["camera_positions"]
        s.set_available_objects(camera_positions, "left")
    module_command(list(tasks.keys()),"reset",wait=False)
    for host in tasks.keys():
        s = ServerProxy("http://"+host+":8010",allow_none=True)
        message_count=0
        while not s.is_reseted():
            if message_count<1:
                print("waiting for module ",host," to reset.")
                message_count+=1
            time.sleep(1)

    pds = []
    scs = []
    knowledges = []
    arms = []
    modules = []
    tasks_copy = deepcopy(tasks)
    print("\n\n")
    while tasks_copy:
        for host in tasks_copy:
            for arm in tasks_copy[host].keys():
                insertable = tasks_copy[host][arm]["sequence"].pop(0)
                print(host,": ",insertable)
                pds.append(InsertionFactory([list(tasks.keys())[0]], TimeMetric("insertion", {"time": 5}),
                                            {"Insertable": insertable, "Container": insertable+"_container",
                                            "Approach": insertable+"_container_approach"}).get_problem_definition(insertable))
                pds[-1].host = host
                pds[-1].optimum_thr = cutoff[insertable]
                pds[-1].cost_function.finish_thr = 2 
                pds[-1].n_variations = 3
                pds[-1].variate_only_success = True
                if insertable=="cylinder60_1" or insertable=="ha-24e-m_1" :  # increase the limits for HDMI_plug
                    pds[-1].domain.limits["p2_f_push_z"] = (0, 60)
                if insertable=="schuko_1" or insertable=="schuko_2":
                    pds[-1].domain.limits["p2_f_push_z"] = (0, 80)
                if insertable[:13] == "padlock-small":
                    pds[-1].domain.limits["p2_f_push_z"] = (0, 10)

                modules.append(host)

                arms.append(arm)
                #n_trials: int = 130,batch_width: int = 10,n_immigrant,exploration_mode,batch_synchronisation, request_probability, request_probability_decrease
                scs.append(SVMLearner(160,10,0,True,False, 0,False).get_configuration())
                
                knowledge = Knowledge()
                knowledge.kb_location = global_db_ip # collective-049 #"collective-nas.rsi.ei.tum.de"
                knowledge.mode = None # "global"  # None:isolated parallel (no knowledge from theirself)  # "local": has transfer inside agent
                
                knowledge.type = "all"  # all: 
                knowledge.kb_task_type = "insertion"
                knowledge.kb_db = "local_knowledge"
                knowledges.append(copy.deepcopy(knowledge))

        for host in list(tasks_copy.keys()):
            for arm in list(tasks_copy[host].keys()):
                if not tasks_copy[host][arm]["sequence"]:
                    tasks_copy[host].pop(arm)
        for host in list(tasks_copy.keys()):
            if not tasks_copy[host]:
                tasks_copy.pop(host)
    #s = ServerProxy("http://" + "collective-001.rsi.ei.tum.de" + ":"+str(8000), allow_none=True)
    #current_problem_uuid = s.start_service(pds[1].to_dict(), scs[1].to_dict(), [pds[1].host], knowledges[1].to_dict()) 
    #return current_problem_uuid
    
    print(pds[0].identity)
    #return True
    # s = ServerProxy("http://" + "10.157.174.169" + ":"+str(8000), allow_none=True)
    # current_problem_uuid = s.start_service(pds[0].to_dict(), scs[0].to_dict(), [pds[0].host], knowledges[0].to_dict()) 
    # return current_problem_uuid
    
    for i in range(0,len(pds)):
        pds[i] = pds[i].to_dict()
        scs[i] = scs[i].to_dict()
        knowledges[i] = knowledges[i].to_dict()
        print("types pd, sc, knowledge: ",type(pds[i]),type(scs[i]),type(knowledges[i]))
    
    print("start collective manager")
    manager = CollectiveManager(list(tasks.keys()),global_db_ip)
    #manager.remove_experiment("charli_test_2")
    #manager.add_module(["collective-001.rsi.ei.tum.de"])

    manager.add_experiment(name=exp_name,
                           modules=modules,
                           problem_definitions=pds,
                           knowledge_configs=knowledges,
                           service_configs=scs,
                           arms=arms,
                           n_agents=len(tasks),
                           keep_allocation=False,
                           iteration=iteration)
    manager.start_experiment(exp_name)
    manager.start_rpc_server()


def pitstop_chalie():
    from collective_manager.collective_manager import CollectiveManager
    tasks = new_tasks # reallocate_tasks()
    easy_tasks = mean_task_cost(["load_balanced"])
    for host in tasks.keys():
        for side in tasks[host].keys():
            for task in tasks[host][side]["sequence"]:
                if task not in easy_tasks.keys():
                    tasks[host][side]["sequence"].pop(tasks[host][side]["sequence"].index(task))
            tasks[host][side]["camera_positions"] = {task:i for i,task in enumerate(tasks[host][side]["sequence"])}
            if len(tasks[host][side]["sequence"]) == 0:
                tasks[host].pop(side)
    exp_name = "easy_tasks" #"load_balanced"  # pistop_charlie2
    iteration = 2
    global_db_ip = "10.157.175.0"
    input(f"start {exp_name} with iteration {iteration}")
    for host, arm in tasks.items():
        print("set camera positions for ",host)
        s = ServerProxy("http://"+host+":8010",allow_none=True)
        for side in arm.keys():
            camera_positions = arm[side]["camera_positions"]
            if side == "left":
                s.set_available_objects(camera_positions, "left")
            else:
                s.set_available_objects(camera_positions, "right")
    module_command(list(tasks.keys()),command="reset",wait=False)
    cutoff = get_optima_pistop_charlie(["baseline"])
    for host in tasks.keys():
        s = ServerProxy("http://"+host+":8010",allow_none=True)
        for side in tasks[host].keys():
            message_count=0
            while not s.is_reseted(side):
                if message_count<1:
                    print("waiting for module ",host," to reset side "+side)
                    message_count+=1
                time.sleep(1)
    pds = []
    scs = []
    knowledges = []
    arms = []
    modules = []
    tasks_copy = deepcopy(tasks)
    print("\n\n")
    while tasks_copy:
        for host in tasks_copy:
            for arm in tasks_copy[host].keys():
                insertable = tasks_copy[host][arm]["sequence"].pop(0)
                print(host,": ",insertable)
                pds.append(InsertionFactory([host], TimeMetric("insertion", {"time": 5}),
                                            {"Insertable": insertable, "Container": insertable+"_container",
                                            "Approach": insertable+"_container_approach"}).get_problem_definition(insertable))
                pds[-1].host = host
                pds[-1].optimum_thr = cutoff[insertable]
                pds[-1].cost_function.finish_thr = 2 
                pds[-1].n_variations = 3
                pds[-1].variate_only_success = True
                if insertable=="cylinder60_1" or insertable=="ha-24e-m_1" :  # increase the limits for HDMI_plug
                    pds[-1].domain.limits["p2_f_push_z"] = (0, 60)
                if insertable=="schuko_1" or insertable=="schuko_2":
                    pds[-1].domain.limits["p2_f_push_z"] = (0, 80)
                if insertable[:13] == "padlock-small":
                    pds[-1].domain.limits["p2_f_push_z"] = (0, 10)

                modules.append(host)

                arms.append(arm)
                #n_trials: int = 130,batch_width: int = 10,n_immigrant,exploration_mode,batch_synchronisation, request_probability, request_probability_decrease
                scs.append(SVMLearner(160,10,0,False,False, 0.4,True).get_configuration())
                
                knowledge = Knowledge()
                knowledge.kb_location = global_db_ip # collective-049 #"collective-nas.rsi.ei.tum.de"
                knowledge.mode = "global"  # None:isolated parallel (no knowledge from theirself)  # "local": has transfer inside agent
                
                knowledge.type = "all"  # all: 
                knowledge.kb_task_type = "insertion"
                knowledge.kb_db = "global_knowledge"
                knowledge.scope = [exp_name,"iteration_"+str(iteration)] # 
                #knowledge.scope.extend([knowledge_origin])  
                knowledges.append(copy.deepcopy(knowledge))

        for host in list(tasks_copy.keys()):
            for arm in list(tasks_copy[host].keys()):
                if not tasks_copy[host][arm]["sequence"]:
                    tasks_copy[host].pop(arm)
        for host in list(tasks_copy.keys()):
            if not tasks_copy[host]:
                tasks_copy.pop(host)
    #s = ServerProxy("http://" + "collective-001.rsi.ei.tum.de" + ":"+str(8000), allow_none=True)
    #current_problem_uuid = s.start_service(pds[1].to_dict(), scs[1].to_dict(), [pds[1].host], knowledges[1].to_dict()) 
    #return current_problem_uuid
    
    print(pds[0].identity)
    #return True
    # s = ServerProxy("http://" + "10.157.174.169" + ":"+str(8000), allow_none=True)
    # current_problem_uuid = s.start_service(pds[0].to_dict(), scs[0].to_dict(), [pds[0].host], knowledges[0].to_dict()) 
    # return current_problem_uuid
    
    for i in range(0,len(pds)):
        pds[i] = pds[i].to_dict()
        scs[i] = scs[i].to_dict()
        knowledges[i] = knowledges[i].to_dict()
        print("types pd, sc, knowledge: ",type(pds[i]),type(scs[i]),type(knowledges[i]))
    
    print("start collective manager")
    manager = CollectiveManager(list(tasks.keys()),global_db_ip)
    n_agents = sum([len(m) for m in tasks.values()])  # full collective
    #manager.remove_experiment("charli_test_2")
    #manager.add_module(["collective-001.rsi.ei.tum.de"])

    manager.add_experiment(name=exp_name,
                           modules=modules,
                           problem_definitions=pds,
                           knowledge_configs=knowledges,
                           service_configs=scs,
                           arms=arms,
                           n_agents=n_agents,
                           keep_allocation=False,
                           iteration=iteration)
    manager.start_experiment(exp_name)
    manager.start_rpc_server()



def positiv_relation(): #prime experiment with similarity from previous experiments
    from collective_manager.collective_manager import CollectiveManager
    exp_name = "positive_relation"
    iteration = 6

    global_db_ip = "10.157.175.0"
    input(f"start {exp_name} with iteration {iteration}")
    
    for host, arm in tasks.items():
        print("set camera positions for ",host)
        s = ServerProxy("http://"+host+":8010",allow_none=True)
        for side in arm.keys():
            camera_positions = arm[side]["camera_positions"]
            if side == "left":
                s.set_available_objects(camera_positions, "left")
            else:
                s.set_available_objects(camera_positions, "right")
    module_command(list(tasks.keys()),command="reset",wait=False)
    cutoff = get_optima_pistop_charlie(["baseline"])
    for host in tasks.keys():
        s = ServerProxy("http://"+host+":8010",allow_none=True)
        for side in tasks[host].keys():
            message_count=0
            while not s.is_reseted(side):
                if message_count<1:
                    print("waiting for module ",host," to reset side "+side)
                    message_count+=1
                time.sleep(1)
    pds = []
    scs = []
    knowledges = []
    arms = []
    modules = []
    tasks_copy = deepcopy(tasks)
    print("\n\n")
    while tasks_copy:
        for host in tasks_copy:
            for arm in tasks_copy[host].keys():
                insertable = tasks_copy[host][arm]["sequence"].pop(0)
                print(host,": ",insertable)
                pds.append(InsertionFactory([host], TimeMetric("insertion", {"time": 5}),
                                            {"Insertable": insertable, "Container": insertable+"_container",
                                            "Approach": insertable+"_container_approach"}).get_problem_definition(insertable))
                pds[-1].host = host
                pds[-1].optimum_thr = cutoff[insertable]
                pds[-1].cost_function.finish_thr = 2 
                pds[-1].n_variations = 3
                pds[-1].variate_only_success = True
                if insertable=="cylinder60_1" or insertable=="ha-24e-m_1" :  # increase the limits for HDMI_plug
                    pds[-1].domain.limits["p2_f_push_z"] = (0, 60)
                if insertable=="schuko_1" or insertable=="schuko_2":
                    pds[-1].domain.limits["p2_f_push_z"] = (0, 80)
                if insertable[:13] == "padlock-small":
                    pds[-1].domain.limits["p2_f_push_z"] = (0, 10)

                modules.append(host)

                arms.append(arm)
                #n_trials: int = 130,batch_width: int = 10,n_immigrant,exploration_mode,batch_synchronisation, request_probability, request_probability_decrease
                scs.append(SVMLearner(160,10,0,False,False, 0.4,True).get_configuration())
                
                knowledge = Knowledge()
                knowledge.kb_location = global_db_ip # collective-049 #"collective-nas.rsi.ei.tum.de"
                knowledge.mode = "global"  # None:isolated parallel (no knowledge from theirself)  # "local": has transfer inside agent
                
                knowledge.type = "all"  # all: 
                knowledge.kb_task_type = "insertion"
                knowledge.kb_db = "global_knowledge"
                knowledge.scope = [exp_name,"iteration_"+str(iteration)] # 
                knowledge.similarity = calculate_similarity(host,insertable,["pitstop_charlie2","pitstop_charlie_test"])
                #knowledge.scope.extend([knowledge_origin])  
                knowledges.append(copy.deepcopy(knowledge))

        for host in list(tasks_copy.keys()):
            for arm in list(tasks_copy[host].keys()):
                if not tasks_copy[host][arm]["sequence"]:
                    tasks_copy[host].pop(arm)
        for host in list(tasks_copy.keys()):
            if not tasks_copy[host]:
                tasks_copy.pop(host)
    #s = ServerProxy("http://" + "collective-001.rsi.ei.tum.de" + ":"+str(8000), allow_none=True)
    #current_problem_uuid = s.start_service(pds[1].to_dict(), scs[1].to_dict(), [pds[1].host], knowledges[1].to_dict()) 
    #return current_problem_uuid
    
    print(pds[0].identity)
    #return True
    # s = ServerProxy("http://" + "10.157.174.169" + ":"+str(8000), allow_none=True)
    # current_problem_uuid = s.start_service(pds[0].to_dict(), scs[0].to_dict(), [pds[0].host], knowledges[0].to_dict()) 
    # return current_problem_uuid
    
    for i in range(0,len(pds)):
        pds[i] = pds[i].to_dict()
        scs[i] = scs[i].to_dict()
        knowledges[i] = knowledges[i].to_dict()
        print("types pd, sc, knowledge: ",type(pds[i]),type(scs[i]),type(knowledges[i]))
    
    print("start collective manager")
    manager = CollectiveManager(list(tasks.keys()),global_db_ip)
    n_agents = sum([len(m) for m in tasks.values()])  # full collective
    #manager.remove_experiment("charli_test_2")
    #manager.add_module(["collective-001.rsi.ei.tum.de"])

    manager.add_experiment(name=exp_name,
                           modules=modules,
                           problem_definitions=pds,
                           knowledge_configs=knowledges,
                           service_configs=scs,
                           arms=arms,
                           n_agents=n_agents,
                           keep_allocation=False,
                           iteration=iteration)
    manager.start_experiment(exp_name)
    manager.start_rpc_server()

def only_slow_pipe():
    from collective_manager.collective_manager import CollectiveManager
    exp_name = "slow_pipe"
    iteration = 5

    global_db_ip = "10.157.175.0"
    input(f"start {exp_name} with iteration {iteration}")
    
    for host, arm in tasks.items():
        print("set camera positions for ",host)
        s = ServerProxy("http://"+host+":8010",allow_none=True)
        for side in arm.keys():
            camera_positions = arm[side]["camera_positions"]
            if side == "left":
                s.set_available_objects(camera_positions, "left")
            else:
                s.set_available_objects(camera_positions, "right")
    module_command(list(tasks.keys()),command="reset",wait=False)
    cutoff = get_optima_pistop_charlie(["baseline"])
    for host in tasks.keys():
        s = ServerProxy("http://"+host+":8010",allow_none=True)
        for side in tasks[host].keys():
            message_count=0
            while not s.is_reseted(side):
                if message_count<1:
                    print("waiting for module ",host," to reset side "+side)
                    message_count+=1
                time.sleep(1)
    pds = []
    scs = []
    knowledges = []
    arms = []
    modules = []
    tasks_copy = deepcopy(tasks)
    print("\n\n")
    while tasks_copy:
        for host in tasks_copy:
            for arm in tasks_copy[host].keys():
                insertable = tasks_copy[host][arm]["sequence"].pop(0)
                print(host,": ",insertable)
                pds.append(InsertionFactory([host], TimeMetric("insertion", {"time": 5}),
                                            {"Insertable": insertable, "Container": insertable+"_container",
                                            "Approach": insertable+"_container_approach"}).get_problem_definition(insertable))
                pds[-1].host = host
                pds[-1].optimum_thr = cutoff[insertable]
                pds[-1].cost_function.finish_thr = 2 
                pds[-1].n_variations = 3
                pds[-1].variate_only_success = True
                if insertable=="cylinder60_1" or insertable=="ha-24e-m_1" :  # increase the limits for HDMI_plug
                    pds[-1].domain.limits["p2_f_push_z"] = (0, 60)
                if insertable=="schuko_1" or insertable=="schuko_2":
                    pds[-1].domain.limits["p2_f_push_z"] = (0, 80)
                if insertable[:13] == "padlock-small":
                    pds[-1].domain.limits["p2_f_push_z"] = (0, 10)

                modules.append(host)

                arms.append(arm)
                #n_trials: int = 130,batch_width: int = 10,n_immigrant,exploration_mode,batch_synchronisation, request_probability, request_probability_decrease
                scs.append(SVMLearner(160,10,0,False,False, 0,False).get_configuration())
                
                knowledge = Knowledge()
                knowledge.kb_location = global_db_ip # collective-049 #"collective-nas.rsi.ei.tum.de"
                knowledge.mode = "global"  # None:isolated parallel (no knowledge from theirself)  # "local": has transfer inside agent
                
                knowledge.type = "all"  # all: 
                knowledge.kb_task_type = "insertion"
                knowledge.kb_db = "global_knowledge"
                knowledge.scope = [exp_name,"iteration_"+str(iteration)] # 
                #knowledge.scope.extend([knowledge_origin])  
                knowledges.append(copy.deepcopy(knowledge))

        for host in list(tasks_copy.keys()):
            for arm in list(tasks_copy[host].keys()):
                if not tasks_copy[host][arm]["sequence"]:
                    tasks_copy[host].pop(arm)
        for host in list(tasks_copy.keys()):
            if not tasks_copy[host]:
                tasks_copy.pop(host)
    #s = ServerProxy("http://" + "collective-001.rsi.ei.tum.de" + ":"+str(8000), allow_none=True)
    #current_problem_uuid = s.start_service(pds[1].to_dict(), scs[1].to_dict(), [pds[1].host], knowledges[1].to_dict()) 
    #return current_problem_uuid
    
    print(pds[0].identity)
    #return True
    # s = ServerProxy("http://" + "10.157.174.169" + ":"+str(8000), allow_none=True)
    # current_problem_uuid = s.start_service(pds[0].to_dict(), scs[0].to_dict(), [pds[0].host], knowledges[0].to_dict()) 
    # return current_problem_uuid
    
    for i in range(0,len(pds)):
        pds[i] = pds[i].to_dict()
        scs[i] = scs[i].to_dict()
        knowledges[i] = knowledges[i].to_dict()
        print("types pd, sc, knowledge: ",type(pds[i]),type(scs[i]),type(knowledges[i]))
    
    print("start collective manager")
    manager = CollectiveManager(list(tasks.keys()),global_db_ip)
    n_agents = sum([len(m) for m in tasks.values()])  # full collective
    #manager.remove_experiment("charli_test_2")
    #manager.add_module(["collective-001.rsi.ei.tum.de"])

    manager.add_experiment(name=exp_name,
                           modules=modules,
                           problem_definitions=pds,
                           knowledge_configs=knowledges,
                           service_configs=scs,
                           arms=arms,
                           n_agents=n_agents,
                           keep_allocation=False,
                           iteration=iteration)
    manager.start_experiment(exp_name)
    manager.start_rpc_server()


def only_fast_pipe():
    from collective_manager.collective_manager import CollectiveManager
    exp_name = "fast_pipe"
    iteration = 5

    global_db_ip = "10.157.175.0"
    input(f"start {exp_name} with iteration {iteration}")
    
    for host, arm in tasks.items():
        print("set camera positions for ",host)
        s = ServerProxy("http://"+host+":8010",allow_none=True)
        for side in arm.keys():
            camera_positions = arm[side]["camera_positions"]
            if side == "left":
                s.set_available_objects(camera_positions, "left")
            else:
                s.set_available_objects(camera_positions, "right")
    module_command(list(tasks.keys()),command="reset",wait=False)
    cutoff = get_optima_pistop_charlie(["baseline"])
    for host in tasks.keys():
        s = ServerProxy("http://"+host+":8010",allow_none=True)
        for side in tasks[host].keys():
            message_count=0
            while not s.is_reseted(side):
                if message_count<1:
                    print("waiting for module ",host," to reset side "+side)
                    message_count+=1
                time.sleep(1)
    pds = []
    scs = []
    knowledges = []
    arms = []
    modules = []
    tasks_copy = deepcopy(tasks)
    print("\n\n")
    while tasks_copy:
        for host in tasks_copy:
            for arm in tasks_copy[host].keys():
                insertable = tasks_copy[host][arm]["sequence"].pop(0)
                print(host,": ",insertable)
                pds.append(InsertionFactory([host], TimeMetric("insertion", {"time": 5}),
                                            {"Insertable": insertable, "Container": insertable+"_container",
                                            "Approach": insertable+"_container_approach"}).get_problem_definition(insertable))
                pds[-1].host = host
                pds[-1].optimum_thr = cutoff[insertable]
                pds[-1].cost_function.finish_thr = 2 
                pds[-1].n_variations = 3
                pds[-1].variate_only_success = True
                if insertable=="cylinder60_1" or insertable=="ha-24e-m_1" :  # increase the limits for HDMI_plug
                    pds[-1].domain.limits["p2_f_push_z"] = (0, 60)
                if insertable=="schuko_1" or insertable=="schuko_2":
                    pds[-1].domain.limits["p2_f_push_z"] = (0, 80)
                if insertable[:13] == "padlock-small":
                    pds[-1].domain.limits["p2_f_push_z"] = (0, 10)

                modules.append(host)

                arms.append(arm)
                #n_trials: int = 130,batch_width: int = 10,n_immigrant,exploration_mode,batch_synchronisation, request_probability, request_probability_decrease
                scs.append(SVMLearner(160,10,0,False,False, 0.4,True).get_configuration())
                
                knowledge = Knowledge()
                knowledge.kb_location = global_db_ip # collective-049 #"collective-nas.rsi.ei.tum.de"
                knowledge.mode = "only_fast_pipe"  # None:isolated parallel (no knowledge from theirself)  # "local": has transfer inside agent
                
                knowledge.type = "all"  # all: 
                knowledge.kb_task_type = "insertion"
                knowledge.kb_db = "global_knowledge"
                knowledge.scope = [exp_name,"iteration_"+str(iteration)] # 
                #knowledge.scope.extend([knowledge_origin])  
                knowledges.append(copy.deepcopy(knowledge))

        for host in list(tasks_copy.keys()):
            for arm in list(tasks_copy[host].keys()):
                if not tasks_copy[host][arm]["sequence"]:
                    tasks_copy[host].pop(arm)
        for host in list(tasks_copy.keys()):
            if not tasks_copy[host]:
                tasks_copy.pop(host)
    #s = ServerProxy("http://" + "collective-001.rsi.ei.tum.de" + ":"+str(8000), allow_none=True)
    #current_problem_uuid = s.start_service(pds[1].to_dict(), scs[1].to_dict(), [pds[1].host], knowledges[1].to_dict()) 
    #return current_problem_uuid
    
    print(pds[0].identity)
    #return True
    # s = ServerProxy("http://" + "10.157.174.169" + ":"+str(8000), allow_none=True)
    # current_problem_uuid = s.start_service(pds[0].to_dict(), scs[0].to_dict(), [pds[0].host], knowledges[0].to_dict()) 
    # return current_problem_uuid
    
    for i in range(0,len(pds)):
        pds[i] = pds[i].to_dict()
        scs[i] = scs[i].to_dict()
        knowledges[i] = knowledges[i].to_dict()
        print("types pd, sc, knowledge: ",type(pds[i]),type(scs[i]),type(knowledges[i]))
    
    print("start collective manager")
    manager = CollectiveManager(list(tasks.keys()),global_db_ip)
    n_agents = sum([len(m) for m in tasks.values()])  # full collective
    #manager.remove_experiment("charli_test_2")
    #manager.add_module(["collective-001.rsi.ei.tum.de"])

    manager.add_experiment(name=exp_name,
                           modules=modules,
                           problem_definitions=pds,
                           knowledge_configs=knowledges,
                           service_configs=scs,
                           arms=arms,
                           n_agents=n_agents,
                           keep_allocation=False,
                           iteration=iteration)
    manager.start_experiment(exp_name)
    manager.start_rpc_server()



def check_results(tags:list, min_trials:int):
    not_finished = {}
    for host, arm in tasks.items():
        for side in arm.keys():
            task_list = arm[side]["sequence"]
            client = MongoDBClient(host)
            for task in task_list:
                success = True
                task_tags = copy.deepcopy(tags)
                task_tags.append(task)
                data = client.read("ml_results","insertion",{"meta.tags":task_tags})
                if not data:
                    print(host,task, "no results found: ",task_tags)
                    success=False
                if success and len(data) > 1:
                    print(host,task,"multiple results found. Takeing newest one")
                    latest=0
                    results = {}
                    for d in data:
                        if d["meta"]["t_0"] > latest:
                            results = d
                if success and len(data) == 1:
                    results = data[0]
                if success and len(results)-3 < min_trials:
                    print(host,task,"not enougth trials: ",len(results)-3)
                    success=False
                #check if successful trials
                if success:
                    successful_trials = False
                    for i in range(1,len(results)-2):
                        try:
                            if results["n"+str(i)]["q_metric"]["success"]:
                                successful_trials = True
                        except KeyError:
                            print(host,task, "Trial n"+str(i)+" is missing")
                    if not successful_trials:
                        if len(results)-3 < 160:
                            print(host,task,"stopped early without success")
                            success = False
                        else:
                            print(host,task, "was just unsuccessful")
                
                if not success:
                    if host not in not_finished:
                        not_finished[host] = {}
                    if side not in not_finished[host]:
                        not_finished[host][side] = arm[side]
                        not_finished[host][side]["sequence"] = []
                    not_finished[host][side]["sequence"].append(task)
    return not_finished

def exp_trials(experiment = ["pitstop_charlie2"]):
    trials = {}
    result = {}
    for host, arms in tasks.items():
        print(host)
        for side in arms.values(): 
            task_list  = side["sequence"]
            for task in task_list:  
                if task not in trials.keys():
                    trials[task] = []
                results = []
                for exp in experiment:
                    try:
                        results.extend(get_multiple_experiment_data(host,"insertion","ml_results",{"meta.tags":[task,exp]}))
                    except DataNotFoundError:
                        pass
                for r in results:
                    trials[task].append(len(r.costs))
                trials[task] = np.mean(trials[task])
    return trials


def mean_task_cost(experiment = ["load_balanced"]):
    tasks = new_tasks
    trials = {}
    result = {}
    for host, arms in tasks.items():
        print(host)
        for side in arms.values(): 
            task_list  = side["sequence"]
            for task in task_list:  
                if task not in trials.keys():
                    trials[task] = []
                results = []
                for exp in experiment:
                    try:
                        results.extend(get_multiple_experiment_data(host,"insertion","ml_results",{"meta.tags":[task,exp]}))
                    except DataNotFoundError:
                        pass
                for r in results:
                    trials[task].append(len(r.costs))
                trials[task] = np.mean(trials[task])
    for task in list(trials.keys()):
        if trials[task] > 75:
            trials.pop(task)
    return trials

def reallocate_tasks(experiment = ["pitstop_charlie2"],set_object=False):
    #tasks = new_tasks
    trials = {}
    result = {}
    for host, arms in tasks.items():
        print(host)
        for side in arms.values(): 
            task_list  = side["sequence"]
            for task in task_list:  
                if task not in trials.keys():
                    trials[task] = []
                results = []
                for exp in experiment:
                    try:
                        results.extend(get_multiple_experiment_data(host,"insertion","ml_results",{"meta.tags":[task,exp]}))
                    except DataNotFoundError:
                        pass
                for r in results:
                    trials[task].append(len(r.costs))
                trials[task] = np.mean(trials[task])
    for task in list(trials.keys()):
        if trials[task] > 75:
            trials.pop(task)
   # return trials
    
    pairs = [
        ('12point-socket-10_1', '6point-socket-10_1'),
        ('12point-socket-24_1','6point-socket-24_1'),
        ('6point-socket-22_1','12point-socket-22_1'),
        ('6point-socket-32_1', '12point-socket-32_1'),
        ('6point-socket-27_1','12point-socket-27_1'),
        ('cylinder20_1','cylinder50_1'),
        ('6point-socket-17_1','12point-socket-17_1'),
        ('6point-socket-36_1','12point-socket-36_1'),
        ('12point-socket-13_1','6point-socket-13_1'),
        ('6point-socket-41_1','12point-socket-41_1'),
        ('6point-socket-19_1','12point-socket-19_1'),
        ('6point-socket-16_1','12point-socket-16_1'),
        ('6point-socket-30_1','12point-socket-30_1'),
        ('cylinder30_1','cylinder60_1'),
        ('cylinder10_1','cylinder40_1'),
        ('hdmi_2','usb-c_1'),
        ('hdmi_1', 'ethernet_1')
    ]
    pair_dict = {}
    for t1,t2 in pairs:
        pair_dict[t1] = t2
        pair_dict[t2] = t1

    trials_list = [(value,key) for key,value in trials.items()]
    trials_list.sort(reverse=True)
    modules_sums = {}
    modules_original = {}
    for host in tasks.keys():
        for side in tasks[host].keys():
            modules_sums[host+"_"+side] = 0
            modules_original[host+"_"+side] = tasks[host][side]["sequence"]

    # inverted_index = {}
    # for key, value_list in modules_original.items():
    #     for string_item in value_list:
    #         if string_item not in inverted_index:
    #             inverted_index[string_item] = []
    #         inverted_index[string_item].append(key)
    done = []
    for trial in trials_list:
        if trial[1] in done:
            continue
        original_host = [key for key, value_list in modules_original.items() if trial[1] in value_list][0]
        target_node = min(modules_sums, key=modules_sums.get)
        if modules_sums[original_host] == 0:
            target_node = original_host
        
        if target_node not in result:
            result[target_node] = []
        print(original_host,target_node,trial[1])
        if set_object and target_node!=original_host:
            orig_host,orig_side = original_host.split("_")
            if orig_side == "left":
                orig_side = 12000
            else:
                orig_side = 13000
            #input(f"{original_host},{target_node}")
            o = call_method(orig_host,orig_side,"download_object_context",{"object":trial[1]})["result"]["context"]
            o["object"] = trial[1]
            o["name"] = trial[1]
            target_host,targe_side = target_node.split("_")
            if targe_side == "left":
                targe_side = 12000
            else:
                targe_side = 13000
            print("call_method", target_host,targe_side,"object:",trial[1])
            call_method(target_host,targe_side,"set_object",o)
        result[target_node].append(trial[1])

        if trial[1] in pair_dict:  #also append pair
            pair_task = pair_dict[trial[1]]
            found_index = next((index for index, pair in enumerate(trials_list) if pair[1] == pair_task), -1)
            result[target_node].append(trials_list[found_index][1])  # task
            if trials_list[found_index][0] > 130:
                modules_sums[target_node] += 130
            else:
                modules_sums[target_node] += trials_list[found_index][0]
            done.append(trials_list[found_index][1])
            if set_object and target_node!=original_host:
                orig_host,orig_side = original_host.split("_")
                if orig_side == "left":
                    orig_side = 12000
                else:
                    orig_side = 13000
                print("call_method", target_host,targe_side,"object:",trials_list[found_index][1])
                o = call_method(orig_host,orig_side,"download_object_context",{"object":trials_list[found_index][1]})["result"]["context"]
                o["object"] = trials_list[found_index][1]
                o["name"] = trials_list[found_index][1]
                target_host,targe_side = target_node.split("_")
                if targe_side == "left":
                    targe_side = 12000
                else:
                    targe_side = 13000
                print("call_method", target_host,targe_side,"object:",trials_list[found_index][1])
                call_method(target_host,targe_side,"set_object",o)
        if trial[0] > 130: 
            modules_sums[target_node] += 130
        else:
            modules_sums[target_node] += trial[0]

    #recreate tasks dict:
    relocated_tasks = copy.deepcopy(tasks)
    for key in result.keys():
        host, side = str(key).split('_')
        relocated_tasks[host][side]["sequence"] = result[key]
        relocated_tasks[host][side]["camera_positions"] = {task:i for i,task in enumerate(result[key])}
    
    return relocated_tasks
            
def get_missing(experiment:str,iteration:int):
    #check resutls in old task allocaiton (tasks)
    missing_old = check_results([experiment,"iteration_"+str(iteration)],1)
    #find in new task allocation (new_tasks):
    missing_new = {}
    for host in missing_old.keys():
        for side in missing_old[host].keys():
            for task in missing_old[host][side]["sequence"]:
                for new_host in new_tasks.keys():
                    for new_side in new_tasks[new_host].keys():
                        if task in new_tasks[new_host][new_side]["sequence"]:
                            if new_host not in missing_new:
                                missing_new[new_host] = {}
                            if new_side not in missing_new[new_host]:
                                missing_new[new_host][new_side] = {"sequence":[],"camera_positions":{}}
                            missing_new[new_host][new_side]["sequence"].append(task)
                            missing_new[new_host][new_side]["camera_positions"][task] = len(missing_new[new_host][new_side]["sequence"])-1
    return missing_new
                
def fix_missing(experiment = "baseline",iterations:list = [0,1,2]):
    from collective_manager.collective_manager import CollectiveManager
    exp_name = experiment
    global_db_ip = "10.157.175.0"
    knowledge_ip = "collective-016.rsi.ei.tum.de"
    knowledge_origin = "cylinder10_1"
    exp_name = "transfer_from_"+knowledge_origin
    pds = []
    scs = []
    knowledges = []
    arms = []
    modules = []
    cutoff = get_optima_pistop_charlie(["baseline"])
    print("\n\n")
    for i in iterations:
        tasks_copy = get_missing(experiment, i)
        while tasks_copy:
            for host in tasks_copy:
                for arm in tasks_copy[host].keys():
                    insertable = tasks_copy[host][arm]["sequence"].pop(0)
                    print(host,": ",insertable)
                    pds.append(InsertionFactory([list(tasks.keys())[0]], TimeMetric("insertion", {"time": 5}),
                                                {"Insertable": insertable, "Container": insertable+"_container",
                                                "Approach": insertable+"_container_approach"}).get_problem_definition(insertable))
                    pds[-1].tags.append("iteration_"+str(i))
                    pds[-1].tags.append("fix_missing")
                    
                    pds[-1].host = host
                    pds[-1].optimum_thr = cutoff[insertable]
                    pds[-1].cost_function.finish_thr = 2 
                    pds[-1].n_variations = 3
                    pds[-1].variate_only_success = True
                    if insertable=="cylinder60_1" or insertable=="ha-24e-m_1" :  # increase the limits for HDMI_plug
                        pds[-1].domain.limits["p2_f_push_z"] = (0, 60)
                    if insertable=="schuko_1" or insertable=="schuko_2":
                        pds[-1].domain.limits["p2_f_push_z"] = (0, 80)
                    if insertable[:13] == "padlock-small":
                        pds[-1].domain.limits["p2_f_push_z"] = (0, 10)

                    modules.append(host)

                    arms.append(arm)
                    #n_trials: int = 130,batch_width: int = 10,n_immigrant,exploration_mode,batch_synchronisation, request_probability, request_probability_decrease
                    #scs.append(SVMLearner(160,10,0,True,False, 0,False).get_configuration())
                    scs.append(SVMLearner(130,10,0,False,False, 0,False).get_configuration())
                    
                    knowledge = Knowledge()
                    #knowledge.kb_location = global_db_ip # collective-049 #"collective-nas.rsi.ei.tum.de"
                    knowledge.kb_location = knowledge_ip
                    #knowledge.mode = None # "global"  # None:isolated parallel (no knowledge from theirself)  # "local": has transfer inside agent
                    knowledge.mode = "specific" # "global"  # None:isolated parallel (no knowledge from theirself)  # "local": has transfer inside agent
                    
                    knowledge.scope = ["baseline","iteration_"+str(i)] # 
                    knowledge.scope.extend([knowledge_origin])  
                    # knowledge.scope.append("n"+str(n_current_iter+1)) # searching for knowledge on the database (only works for the slow pipeline);  e.g. [] search all, 
                    knowledge.type = "all"  # all: 
                    knowledge.kb_task_type = "insertion"
                    knowledge.kb_db = "local_knowledge"
                    knowledges.append(copy.deepcopy(knowledge))


            for host in list(tasks_copy.keys()):
                for arm in list(tasks_copy[host].keys()):
                    if not tasks_copy[host][arm]["sequence"]:
                        tasks_copy[host].pop(arm)
            for host in list(tasks_copy.keys()):
                if not tasks_copy[host]:
                    tasks_copy.pop(host)
    
    for i in range(0,len(pds)):
        pds[i] = pds[i].to_dict()
        scs[i] = scs[i].to_dict()
        knowledges[i] = knowledges[i].to_dict()
        #print("types pd, sc, knowledge: ",type(pds[i]),type(scs[i]),type(knowledges[i]))
    
    print("start collective manager")
    input(f"start Experiment with {experiment}"+ "\n".join([str(pd["host"])+" - "+str(pd["tags"]) for pd in pds]))
    manager = CollectiveManager(list(tasks.keys()),global_db_ip)
    #manager.remove_experiment("charli_test_2")
    #manager.add_module(["collective-001.rsi.ei.tum.de"])

    manager.add_experiment(name=exp_name,
                           modules=modules,
                           problem_definitions=pds,
                           knowledge_configs=knowledges,
                           service_configs=scs,
                           arms=arms,
                           n_agents=len(tasks),
                           keep_allocation=False,
                           iteration=False)
    manager.start_experiment(exp_name)
    manager.start_rpc_server()

def copy_best_trajectories(experiment,iteration=0,after_reallocation=False):
    def get_optima_trial_paths(task,experiment, iteration):
        try:
            data = get_multiple_experiment_data("localhost","insertion","ml_results", {"meta.tags":[task,experiment,"iteration_"+str(iteration)]})
        except DataNotFoundError:
            print("could not find data for task ",task)
            return False, False
        if len(data)>1:
            print("found multiple results for ",task)
        if len(data)<1:
            print("no data found for ",task)
        newest = 0
        take_this_i = 0
        for i,result in enumerate(data):
            if result.starting_time > newest:
                take_this_i = i 
                newest = result.starting_time
        result = data[take_this_i]
        optima = result.costs.index(min(result.costs))
        print(task, optima)
        if result.costs[optima] > 0.99:
            print("No successful trial found")
            return False, False
        remote_path = "/share/datasets/EmbodiedAIDataset/"+str(result.host[:14])+"/EmbodiedAIDataset/"+experiment+"/iteration_"+str(iteration)+"/"+task+"/n"+str(optima)+"/learning_insertion"
        local_path = "/run/media/samuel/Extreme SSD/baseline_optima/"+task+"/"
        return remote_path, local_path
    if after_reallocation:
        task_dict = new_tasks
    else:
        task_dict = tasks
    client = MongoDBClient()
    for host in task_dict.keys():
        for side in task_dict[host].keys():
            for task in task_dict[host][side]["sequence"]:
                #data = client.read("ml_results","insertion", {"meta.tags":[task,experiment,"iteration_"+str(iteration)]})
                success = False
                i = copy.deepcopy(iteration)
                while not success:
                    if i>10:
                        print("no data found (all iterations) for task ",task)
                        break
                    remote_path,local_path = get_optima_trial_paths(task,experiment,i)
                    if not remote_path:
                        i+=1
                        continue
                    if not copy_from_remote("collective_adm","192.168.178.98","Hw^PD=2DAN$}bw!",remote_path,local_path):
                        i+=1
                        continue
                    print(task, "done!")
                    success=True

    



tasks = {
        'collective-001.rsi.ei.tum.de': {"left":{"sequence":[ 'abus-e30_1','abus-e30_2', 'usb-a_2', 'schuko_1'], 
                "camera_positions":{'abus-e30_1':0, 'abus-e30_2':1, 'usb-a_2':2, 'schuko_1':3}},
                                        "right":{"sequence":['cylinder30_1','cylinder60_1'], 
                "camera_positions":{'cylinder30_1':0, 'cylinder60_1':1}}},                                                                     
        'collective-003.rsi.ei.tum.de':  {"left":{"sequence":['12point-socket-10_1', '6point-socket-10_1' ,'12point-socket-24_1','6point-socket-24_1'], 
                "camera_positions":{'12point-socket-10_1':0, '6point-socket-10_1':0 ,'12point-socket-24_1':1,'6point-socket-24_1':1}}},                               #teached
        'collective-004.rsi.ei.tum.de':  {"left":{"sequence":['padlock-small_1','abus-e30_3', 'BS1363_1'],  #, 'vga_2' 'burgwächter-splash_1':0,
                "camera_positions":{'padlock-small_1':0,'abus-e30_3':1, 'BS1363_1':2, 'vga_2':3}}},                                                             #teached
        'collective-005.rsi.ei.tum.de':  {"left":{"sequence":['f3_1', 'abus-e30_9', 'abus-d6x_2', 'vga_3'],
                "camera_positions":{'f3_1':0, 'abus-e30_9':1, 'abus-d6x_2':2, 'vga_3':3}}},                                                                              #teached
        'collective-006.rsi.ei.tum.de':  {"left":{"sequence":['abus-e30_10','burgwächter-atlantic_1','abus-e20_3'], #, 'padlock-small_2'
                "camera_positions":{'abus-e30_10':0,'burgwächter-atlantic_1':1,'abus-e20_3':2, 'padlock-small_2':3}}},                                                   #teached
        'collective-007.rsi.ei.tum.de':  {"left":{"sequence":['simple_2','europlug_1','burgwächter-look_1'],  #'padlock-small_1' broken at iteration4(baseline), later used at 004 (from pitstop_charlie2 iteration_4)
                "camera_positions":{'simple_2':0,'padlock-small_1':1,'europlug_1':2,'burgwächter-look_1':3}}},                                                           #teached
        'collective-008.rsi.ei.tum.de':  {  "left":{"sequence":['schuko_2', 'stabilit_1', 'cylinderlock-small_2', 'oldkey_2'],
                "camera_positions":{'schuko_2':0, 'stabilit_1':1, 'cylinderlock-small_2':2, 'oldkey_2':3}},
                                            "right":{"sequence":['cylinder10_1','cylinder40_1'],
                "camera_positions":{'cylinder10_1':0, 'cylinder40_1':1}}},                                                             #teached
        'collective-013.rsi.ei.tum.de':  {"left":{"sequence":['sector_1','trapezoid_1','6point-socket-22_1','12point-socket-22_1','burgwächter-yacht_1'],
                "camera_positions":{'sector_1':0,'trapezoid_1':1,'6point-socket-22_1':2,'12point-socket-22_1':2,'burgwächter-yacht_1':3}}},                                #teached
        'collective-014.rsi.ei.tum.de':  {"left":{"sequence":['iec-c7_1', '6point-socket-32_1', '12point-socket-32_1' ,'moon_1'],  # 
                "camera_positions":{'iec-c7_1':0, '6point-socket-32_1':1, '12point-socket-32_1':1,'moon_1':2}}},                                                        #teached
        'collective-015.rsi.ei.tum.de':  {"left":{"sequence":['leave_1','nipple_1','6point-socket-27_1','12point-socket-27_1', "yale_1"],
                "camera_positions":{'leave_1':0,'nipple_1':1,'6point-socket-27_1':2,'12point-socket-27_1':2, "yale_1":3}}},                                             #teached
        'collective-016.rsi.ei.tum.de':  {"left":{"sequence":['cylinder20_1','cylinder50_1'],
                "camera_positions":{'cylinder10_1':0,'cylinder20_1':1,'cylinder30_1':2,'cylinder40_1':3,'cylinder50_1':4,'cylinder60_1':5}}},                                #teached
        #'018': ['cylinderlock-small_4','padlock-diamant_1','hexkey-8_1','hexkey-10_1'],
        'collective-021.rsi.ei.tum.de':  {"left":{"sequence":['abus-e30_6','padlock-burgwächter_1','abus-d6x_1','6point-socket-17_1','12point-socket-17_1'],
                "camera_positions":{'abus-e30_6':0,'padlock-burgwächter_1':1,'abus-d6x_1':2,'6point-socket-17_1':3,'12point-socket-17_1':3}}},                             #teached
        'collective-022.rsi.ei.tum.de':  {"left":{"sequence":['padlock-burgwächter_2','abus-e20_2','padlock-medium_1','type-l_1'],
                "camera_positions":{'padlock-burgwächter_2':0,'abus-e20_2':1,'padlock-medium_1':2,'type-l_1':3}}},                                                       #teached
        'collective-023.rsi.ei.tum.de':  {"left":{"sequence":['ha-24e-m_1',  'iec-c13_1', 'display-port_1'],  #,'vga_1'
                "camera_positions":{'ha-24e-m_1':0,  'iec-c13_1':1,'vga_1':2, 'display-port_1':3}}},                                                                     #teached
        'collective-024.rsi.ei.tum.de':  {"left":{"sequence":['simple_3','abus-e30_8','6point-socket-36_1','12point-socket-36_1'],
                "camera_positions":{'simple_3':0,'abus-e30_8':1,'6point-socket-36_1':2,'12point-socket-36_1':2}}},                                                       #teached
        'collective-025.rsi.ei.tum.de':  {"left":{"sequence":[ 'hexkey-12_1', 'hexkey-14_1','12point-socket-13_1','6point-socket-13_1'],
                "camera_positions":{'hexkey-12_1':0, 'hexkey-14_1':1,'12point-socket-13_1':2,'6point-socket-13_1':2}}},                                                 #teached
        'collective-026.rsi.ei.tum.de': {"left": {"sequence":['usb-a_1', 'hdmi_1', 'ethernet_1', 'cross_1'],  #, 'trrs-3.5mm_1'     was collective-026 before 
                "camera_positions":{'usb-a_1':0, 'ethernet_1':2, 'hdmi_1':1, 'cross_1':3, 'trrs-3.5mm_1':3}}},                                                               #teached
        'collective-029.rsi.ei.tum.de':  {"left":{"sequence":['6point-socket-41_1','12point-socket-41_1','hexkey-27_1','hexkey-22_1'],  #
                "camera_positions":{'6point-socket-41_1':0,'12point-socket-41_1':0,'hexkey-27_1':1,'hexkey-22_1':2}}},   
        'collective-033.rsi.ei.tum.de':  {"left":{"sequence":['abus-e30_4',  'cylinderlock-small_1', '6point-socket-19_1','12point-socket-19_1'],  #'oldkey_1' broken for good
                "camera_positions":{'abus-e30_4':0, 'oldkey_1':1, 'cylinderlock-small_1':2, '6point-socket-19_1':3,'12point-socket-19_1':3}}},                             #teached
        'collective-035.rsi.ei.tum.de':  {"left":{"sequence":['iec-c14_1', 'cylinderlock-small_3','padlock-small_3'],  #,'oldkey_3'
                "camera_positions":{'iec-c14_1':0,'oldkey_3':1, 'cylinderlock-small_3':2,'padlock-small_3':3}}},                                                         #teached
        'collective-040.rsi.ei.tum.de':  {"left":{"sequence":['hexkey-6_1','noname_1','padlock-burgwächter_3','6point-socket-16_1','12point-socket-16_1'],
                "camera_positions":{'hexkey-6_1':0,'noname_1':1,'padlock-burgwächter_3':2,'6point-socket-16_1':3,'12point-socket-16_1':3}}},                               #teached
        'collective-017.rsi.ei.tum.de':  {"left":{"sequence":["trrs-6.35mm_aluminum_rod",'6point-socket-30_1','12point-socket-30_1', 'simple_1'],  #041
                "camera_positions":{"trrs-6.35mm_aluminum_rod":0,'6point-socket-30_1':1,'12point-socket-30_1':1, 'simple_1':2}}},                                        #teached
        'collective-042.rsi.ei.tum.de':  {"left":{"sequence":[ 'cross-2','audi_1','arrow_1', 'star_1','elliptoid_1'], #  
                "camera_positions":{'cross-2':0, 'audi_1':1, 'arrow_1':2, 'star_1':3,'elliptoid_1':4}}},                                                                   #teached
        '10.157.174.145':  {"left":{"sequence":['tae-u-m_1','gb-2099_1','cross_3',  'stairs_1' ],   # former collective-043.rsi.ei.tum.de
                "camera_positions":{'tae-u-m_1':0,'gb-2099_1':1,'cross_3':2,  'stairs_1':3}}},                                                                          #teached
        'collective-032.rsi.ei.tum.de':  {"left":{"sequence":['hdmi_2','usb-c_1','hexkey-19_1', 'hexkey-17_1','abus-e30_5'],  #ormer  044
                "camera_positions":{'hdmi_2':0,'usb-c_1':1, 'hexkey-19_1':2, 'hexkey-17_1':3,'abus-e30_5':4}}},      
        '10.157.175.149':  {"left":{"sequence":['nema-ungrounded_1','nema-grounded_1','heart_1','abus-e20_1'],   # former 047
                "camera_positions":{'nema-ungrounded_1':0,'nema-grounded_1':1,'heart_1':2,'abus-e20_1':3}}}        
                                                          #teached
        #'none': ['cylinder_1', 'cuboid_1','lock_1', 'lines_1','abus-e30_7','iec-c14_2','heart_1']
    }
# r=[]
# for task in tasks.keys():
    
#     if not task=="collective-006.rsi.ei.tum.de": #  and not task == "collective-029.rsi.ei.tum.de":
#         r.append(task)
# for t in r:
#     tasks.pop(t)

# #tasks["collective-029.rsi.ei.tum.de"].pop("right")
# #tasks["collective-008.rsi.ei.tum.de"].pop("right")
# #tasks["collective-013.rsi.ei.tum.de"]["left"]["sequence"] = ['12point-socket-22_1','burgwächter-yacht_1']

# tasks["collective-006.rsi.ei.tum.de"]["left"]["sequence"].pop(0)
# tasks["collective-029.rsi.ei.tum.de"]["left"]["sequence"].pop(0)
# tasks["collective-029.rsi.ei.tum.de"]["left"]["sequence"].pop(0)
# #tasks["collective-044.rsi.ei.tum.de"]["left"]["sequence"].pop(0)




#knowledge_origin = "abus-e30_2"
#exp_name = "transfer_from_"+knowledge_origin
#tasks = check_results([exp_name,"iteration_0"],1)

for host, arm in tasks.items():
    print(host,": ",[r["sequence"] for r in arm.values()])
count = 0
count_hosts=0
for host, arm in tasks.items():
    for task_dict in arm.values():
        count+=len(task_dict["sequence"])
        count_hosts+=1

print("total number of tasks: ",count,"\ntotal number of robots: ",count_hosts)

    #time.sleep(30)
    #manager.remove_experiment("charli_test")
    # try:
    #     while True:
    #         time.sleep(1)
    # except KeyboardInterrupt:
    #     print("remove experiment")
    #     manager.remove_experiment("charlie_test")

    # print("finished :)")
# if __name__=="__main__":      
#     from collective_manager.collective_manager import CollectiveModule
#     host = "collective-015.rsi.ei.tum.de"
#     m = CollectiveModule(host,{"left":True})
#     m.set_available_objects(["leave_1","nipple_1","6point-socket27_1","6point-socket10_1"],"left")

#     knowledge = Knowledge()
#     sc = SVMLearner(10,1,0,True,False, 0,True).get_configuration()
#     insertable = "leave_1"
#     container = insertable+"_container" 
#     approach = container+"_approach"
#     pd = InsertionFactory([host], TimeMetric("insertion", {"time": 5}),
#                             {"Insertable": insertable, "Container": container,
#                             "Approach": approach}).get_problem_definition(insertable)
#     pd.n_variations = 5
#     pd.variate_only_success = True

#     m.set_learning_config(pd.to_dict(),sc.to_dict(),knowledge.to_dict(),1,arm="left")

new_tasks = {'collective-001.rsi.ei.tum.de': {'left': {'sequence': ['schuko_1',
    'abus-e30_4']},
  'right': {'sequence': ['simple_3', 'abus-e30_9', 'iec-c13_1', 'audi_1']}},
 'collective-003.rsi.ei.tum.de': {'left': {'sequence': ['hexkey-14_1',
    'abus-e30_1',
    'abus-d6x_2',
    'hexkey-27_1']}},
 'collective-004.rsi.ei.tum.de': {'left': {'sequence': ['abus-e30_3',
    'iec-c14_1',
    'abus-e20_2',
    '12point-socket-27_1',
    '6point-socket-27_1']}},
 'collective-005.rsi.ei.tum.de': {'left': {'sequence': ['hexkey-12_1',
    '6point-socket-41_1',
    '12point-socket-41_1',
    'cylinderlock-small_2']}},
 'collective-006.rsi.ei.tum.de': {'left': {'sequence': ['abus-e20_3',
    'nema-ungrounded_1',
    'padlock-medium_1',
    'burgwächter-yacht_1']}},
 'collective-007.rsi.ei.tum.de': {'left': {'sequence': ['europlug_1',
    'sector_1',
    'ha-24e-m_1',
    'star_1']}},
 'collective-008.rsi.ei.tum.de': {'left': {'sequence': ['f3_1',
    'usb-a_2',
    '6point-socket-36_1',
    '12point-socket-36_1',
    'gb-2099_1']},
  'right': {'sequence': ['abus-e30_6',
    'burgwächter-atlantic_1',
    'elliptoid_1',
    'burgwächter-look_1']}},
 'collective-013.rsi.ei.tum.de': {'left': {'sequence': ['hexkey-19_1',
    '12point-socket-10_1',
    '6point-socket-10_1',
    'display-port_1',
    'abus-e30_5']}},
 'collective-014.rsi.ei.tum.de': {'left': {'sequence': ['iec-c7_1',
    'abus-e30_10',
    '6point-socket-19_1',
    '12point-socket-19_1',
    'padlock-small_1']}},
 'collective-015.rsi.ei.tum.de': {'left': {'sequence': ['yale_1',
    'abus-e20_1']}},
 'collective-016.rsi.ei.tum.de': {'left': {'sequence': ['cylinder20_1',
    'cylinder50_1']}},
 'collective-021.rsi.ei.tum.de': {'left': {'sequence': ['abus-d6x_1',
    'ethernet_1',
    'hdmi_1',
    'cylinderlock-small_1']}},
 'collective-022.rsi.ei.tum.de': {'left': {'sequence': ['leave_1',
    'tae-u-m_1',
    'oldkey_2',
    '12point-socket-17_1',
    '6point-socket-17_1']}},
 'collective-023.rsi.ei.tum.de': {'left': {'sequence': ['schuko_2',
    'hdmi_2',
    'usb-c_1',
    'nipple_1',
    'cylinder40_1',
    'cylinder10_1']}},
 'collective-024.rsi.ei.tum.de': {'left': {'sequence': ['abus-e30_8',
    'padlock-burgwächter_3']}},
 'collective-025.rsi.ei.tum.de': {'left': {'sequence': ['6point-socket-13_1',
    '12point-socket-13_1']}},
 'collective-026.rsi.ei.tum.de': {'left': {'sequence': ['cross_1',
    '6point-socket-30_1',
    '12point-socket-30_1',
    'padlock-burgwächter_1']}},
 'collective-029.rsi.ei.tum.de': {'left': {'sequence': ['hexkey-22_1',
    'vga_3',
    'trrs-6.35mm_aluminum_rod',
    'arrow_1']}},
 'collective-033.rsi.ei.tum.de': {'left': {'sequence': ['simple_2',
    'heart_1',
    'hexkey-6_1',
    'cylinderlock-small_3',
    'padlock-small_3']}},
 'collective-035.rsi.ei.tum.de': {'left': {'sequence': ['6point-socket-32_1',
    '12point-socket-32_1',
    'abus-e30_2',
    'simple_1',
    'moon_1']}},
 'collective-040.rsi.ei.tum.de': {'left': {'sequence': ['6point-socket-16_1',
    '12point-socket-16_1']}},
 'collective-017.rsi.ei.tum.de': {'left': {'sequence': ['usb-a_1',
    'padlock-burgwächter_2',
    '6point-socket-22_1',
    '12point-socket-22_1']}},
 'collective-042.rsi.ei.tum.de': {'left': {'sequence': ['cross-2',
    'trapezoid_1',
    'stabilit_1',
    'noname_1']}},
 '10.157.174.145': {'left': {'sequence': ['cross_3', 'stairs_1']}},  
 'collective-032.rsi.ei.tum.de': {'left': {'sequence': ['hexkey-17_1',
    '6point-socket-24_1',
    '12point-socket-24_1',
    'type-l_1']}},
 '10.157.175.149': {'left': {'sequence': ['nema-grounded_1',
    'cylinder60_1',
    'cylinder30_1',
    'BS1363_1']}}}
