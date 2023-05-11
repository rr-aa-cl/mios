from itertools import count
from subprocess import call
from definitions.templates import *
from definitions.cost_functions import *
from definitions.service_configs import *
from utils.database import delete_global_knowledge
from utils.experiment_wizard import *
from utils.taxonomy_utils import *
from services.knowledge import Knowledge
from utils.helper_functions import *
import os
from threading import Thread


def learn_task(robot:str, problem_definition: ProblemDefinition, service_config: ServiceConfiguration, tags: list,
               n_iterations: int = 10, keep_record: bool = False, knowledge = None, wait: bool = False, service_port:int = 8000):
    start_experiment(robot, [robot], problem_definition, service_config, n_iterations, knowledge=knowledge, tags=tags,
                     keep_record=keep_record, wait=wait,service_port=service_port)
def learn_single_task(robot:str, problem_definition: ProblemDefinition, service_config: ServiceConfiguration, tags: list,
               current_number_iterations: int=0, keep_record: bool = False, knowledge = None, wait: bool = False, service_port:int=8000):
    start_single_experiment(robot, [robot], problem_definition, service_config, current_number_iterations, tags, knowledge, keep_record, wait, service_port=service_port)

def test_learning():
    pd = InsertionFactory("collective-panda-001", ContactForcesMetric("insertion", {"contact_forces": 175}),
                          {"Insertable": "cylinder_40", "Container": "cylinder_40_container",
                           "Approach": "cylinder_40_container_approach"}).get_problem_definition("cylinder_40")
    sc = SVMLearner().get_configuration()
    learn_task("collective-panda-001", pd, sc, ["test_learning"])


def learn_insertion(robot: str, approach: str, insertable: str, container: str, tags: list, knowledge=None,
                    wait: bool=True, n_iterations = 10, service_port=8000):
    pd = InsertionFactory([robot], TimeMetric("insertion", {"time": 5}),
                          {"Insertable": insertable, "Container": container,
                           "Approach": approach}).get_problem_definition(insertable)
    sc = SVMLearner().get_configuration()
    learn_task(robot, pd, sc, tags, knowledge=knowledge, n_iterations=n_iterations,service_port=service_port)


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
        learn_single_task(robot, pd, service_config, tags, iteration, False, knowledge_configuration, True,service_port=service_port)
        print("finished learning ", pd.tags, "\nplacing...")
        place_insertable(robot, insertable, container, approach, container+"_above")


def delete_results(robot:str, tags:list):
    client = MongoDBClient(robot)
    client.remove("ml_results", "insertion", {"meta.tags":tags})

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
        knowledge_source.mode = "local"
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

#def stop_services(robots:list =[ "collective-panda-prime","collective-panda-002","collective-panda-003","collective-panda-004","collective-panda-008","collective-panda-005"]):
#    for r in robots:
#        s = ServerProxy("http://" + r + ":8000", allow_none=True)
#        try:
#            s.stop_service()
#        except Exception as e:
#            print("Error with robot ",r)
#            print(e)



def dualarm_demo():
    robots_dualarm = [
    "10.157.175.221",  #0 ms            collective-001.local    [n/a]           A8:A1:59:B8:22:8B                   [n/a]                               ASRock Incorporation                      
    "10.157.174.166",  #0 ms            collective-002.local    [n/a]           A8:A1:59:B8:25:9A                   [n/a]                               ASRock Incorporation                      
    "10.157.174.167",  #0 ms            collective-003.local    [n/a]           A8:A1:59:B8:24:E8                   [n/a]                               ASRock Incorporation                      
    "10.157.174.168",  #0 ms            collective-004.local    [n/a]           A8:A1:59:B8:25:EC                   [n/a]                               ASRock Incorporation                      
    "10.157.174.89" ,  #0 ms            collective-005.local    [n/a]           A8:A1:59:B8:23:72                   [n/a]                               ASRock Incorporation                      
    "10.157.174.80" ,  #0 ms            collective-006.local    [n/a]           A8:A1:59:B8:23:74                   [n/a]                               ASRock Incorporation                      
    "10.157.174.200",  #0 ms            collective-007.local    [n/a]           A8:A1:59:B2:B1:6E                   [n/a]                               ASRock Incorporation                      
    "10.157.175.129",  #0 ms            collective-008.local    [n/a]           A8:A1:59:B8:22:F4                   [n/a]                               ASRock Incorporation                      
    "10.157.174.36" ,  #0 ms            collective-009.local    [n/a]           A8:A1:59:B8:25:BD                   [n/a]                               ASRock Incorporation                      
    "10.157.174.59",  #collective-010.local
    "10.157.175.87",  #0 ms            collective-011.local    [n/a]           A8:A1:59:B8:23:62                   [n/a]                               ASRock Incorporation                      
    "10.157.174.241",  #0 ms            collective-012.local    [n/a]           A8:A1:59:B8:25:DF                   [n/a]                               ASRock Incorporation                      
    "10.157.174.201",  #0 ms            collective-013.local    [n/a]           A8:A1:59:B2:BF:1F                   [n/a]                               ASRock Incorporation                      
    "10.157.174.247",  #0 ms            collective-014.local    [n/a]           A8:A1:59:B2:1C:28                   [n/a]                               ASRock Incorporation                      
    "10.157.174.202",  #0 ms            collective-015.local    [n/a]           A8:A1:59:B8:23:38                   [n/a]                               ASRock Incorporation                      
    "10.157.174.203",  #0 ms            collective-016.local    [n/a]           A8:A1:59:B2:B2:E4                   [n/a]                               ASRock Incorporation                      
    "10.157.174.46",  #0 ms            collective-017.local    [n/a]           A8:A1:59:B8:24:CF                   [n/a]                               ASRock Incorporation                      
    "10.157.174.103",  #0 ms            collective-018.local    [n/a]           A8:A1:59:B8:23:1E                   [n/a]                               ASRock Incorporation                      
    "10.157.174.206",  #0 ms            collective-019.local    [n/a]           A8:A1:59:B8:22:E2                   [n/a]                               ASRock Incorporation                      
    #"10.157.174.204",  #0 ms            collective-020.local    [n/a]           A8:A1:59:B8:22:AE                   [n/a]                               ASRock Incorporation                      
    "10.157.175.173",  #0 ms            collective-021.local    [n/a]           A8:A1:59:B8:24:C9                   [n/a]                               ASRock Incorporation                      
    "10.157.174.244",  #0 ms            collective-022.local    [n/a]           A8:A1:59:B8:24:E6                   [n/a]                               ASRock Incorporation                      
    "10.157.174.205",  #0 ms            collective-023.local    [n/a]           A8:A1:59:B8:26:4D                   [n/a]                               ASRock Incorporation                      
    "10.157.175.156",  #0 ms            collective-024.local    [n/a]           A8:A1:59:B8:23:5A                   [n/a]                               ASRock Incorporation                      
    "10.157.174.186",  #0 ms            collective-025.local    [n/a]           A8:A1:59:B8:25:D5                   [n/a]                               ASRock Incorporation                      
    "10.157.174.245",  #0 ms            collective-026.local    [n/a]           A8:A1:59:B2:1C:7A                   [n/a]                               ASRock Incorporation                      
    "10.157.174.249",  #0 ms            collective-027.local    [n/a]           A8:A1:59:B8:23:B9                   [n/a]                               ASRock Incorporation                      
    "10.157.174.255",  #0 ms            collective-028.local    [n/a]           A8:A1:59:B2:AE:FF                   [n/a]                               ASRock Incorporation                      
    "10.157.174.42" ,  #0 ms            collective-029.local    [n/a]           A8:A1:59:B2:AD:9A                   [n/a]                               ASRock Incorporation                      
    #"10.157.175.236",#collective-030
    "10.157.174.148",#collective-032
    #"10.157.174.160",#collective-034
    #"10.157.174.163",  #0 ms            collective-038.local    [n/a]           A8:A1:59:B8:23:9F                   [n/a]                               ASRock Incorporation                      
    #"10.157.174.175",  #0 ms            collective-039.local    [n/a]           A8:A1:59:B8:25:70                   [n/a]                               ASRock Incorporation                      
    #"10.157.174.52" ,  #0 ms            collective-046.local    [n/a]           A8:A1:59:B8:23:A5                   [n/a]                               ASRock Incorporation                      
    "10.157.175.134"]  #0 ms            collective-050.local    [n/a]           A8:A1:59:B2:0F:85                   [n/a]                               ASRock Incorporation 
    modules = ["001",\
            "002","003","004","005","006","007","008","009","010","011","012","013","014","015","016","017",\
            "018","019",#"020",
            "021","022","023","024","025","026","027","028","029",#"030",
            "032",#"034",#"038","039","046",
            "050",]


    print(len(modules),len(robots_dualarm))
    tags = ["dualarm_demo_2"]
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

def stop_dualarm():
    robots_dualarm = [
    "10.157.175.221",  #0 ms            collective-001.local    [n/a]           A8:A1:59:B8:22:8B                   [n/a]                               ASRock Incorporation                      
    "10.157.174.166",  #0 ms            collective-002.local    [n/a]           A8:A1:59:B8:25:9A                   [n/a]                               ASRock Incorporation                      
    "10.157.174.167",  #0 ms            collective-003.local    [n/a]           A8:A1:59:B8:24:E8                   [n/a]                               ASRock Incorporation                      
    "10.157.174.168",  #0 ms            collective-004.local    [n/a]           A8:A1:59:B8:25:EC                   [n/a]                               ASRock Incorporation                      
    "10.157.174.89" ,  #0 ms            collective-005.local    [n/a]           A8:A1:59:B8:23:72                   [n/a]                               ASRock Incorporation                      
    "10.157.174.80" ,  #0 ms            collective-006.local    [n/a]           A8:A1:59:B8:23:74                   [n/a]                               ASRock Incorporation                      
    "10.157.174.200",  #0 ms            collective-007.local    [n/a]           A8:A1:59:B2:B1:6E                   [n/a]                               ASRock Incorporation                      
    "10.157.175.129",  #0 ms            collective-008.local    [n/a]           A8:A1:59:B8:22:F4                   [n/a]                               ASRock Incorporation                      
    "10.157.174.36" ,  #0 ms            collective-009.local    [n/a]           A8:A1:59:B8:25:BD                   [n/a]                               ASRock Incorporation                      
    "10.157.174.59",  #collective-010.local
    "10.157.175.87",  #0 ms            collective-011.local    [n/a]           A8:A1:59:B8:23:62                   [n/a]                               ASRock Incorporation                      
    "10.157.174.241",  #0 ms            collective-012.local    [n/a]           A8:A1:59:B8:25:DF                   [n/a]                               ASRock Incorporation                      
    "10.157.174.201",  #0 ms            collective-013.local    [n/a]           A8:A1:59:B2:BF:1F                   [n/a]                               ASRock Incorporation                      
    "10.157.174.247",  #0 ms            collective-014.local    [n/a]           A8:A1:59:B2:1C:28                   [n/a]                               ASRock Incorporation                      
    "10.157.174.202",  #0 ms            collective-015.local    [n/a]           A8:A1:59:B8:23:38                   [n/a]                               ASRock Incorporation                      
    "10.157.174.203",  #0 ms            collective-016.local    [n/a]           A8:A1:59:B2:B2:E4                   [n/a]                               ASRock Incorporation                      
    "10.157.174.46",  #0 ms            collective-017.local    [n/a]           A8:A1:59:B8:24:CF                   [n/a]                               ASRock Incorporation                      
    "10.157.174.103",  #0 ms            collective-018.local    [n/a]           A8:A1:59:B8:23:1E                   [n/a]                               ASRock Incorporation                      
    "10.157.174.206",  #0 ms            collective-019.local    [n/a]           A8:A1:59:B8:22:E2                   [n/a]                               ASRock Incorporation                      
    #"10.157.174.204",  #0 ms            collective-020.local    [n/a]           A8:A1:59:B8:22:AE                   [n/a]                               ASRock Incorporation                      
    "10.157.175.173",  #0 ms            collective-021.local    [n/a]           A8:A1:59:B8:24:C9                   [n/a]                               ASRock Incorporation                      
    "10.157.174.244",  #0 ms            collective-022.local    [n/a]           A8:A1:59:B8:24:E6                   [n/a]                               ASRock Incorporation                      
    "10.157.174.205",  #0 ms            collective-023.local    [n/a]           A8:A1:59:B8:26:4D                   [n/a]                               ASRock Incorporation                      
    "10.157.175.156",  #0 ms            collective-024.local    [n/a]           A8:A1:59:B8:23:5A                   [n/a]                               ASRock Incorporation                      
    "10.157.174.186",  #0 ms            collective-025.local    [n/a]           A8:A1:59:B8:25:D5                   [n/a]                               ASRock Incorporation                      
    "10.157.174.245",  #0 ms            collective-026.local    [n/a]           A8:A1:59:B2:1C:7A                   [n/a]                               ASRock Incorporation                      
    "10.157.174.249",  #0 ms            collective-027.local    [n/a]           A8:A1:59:B8:23:B9                   [n/a]                               ASRock Incorporation                      
    "10.157.174.255",  #0 ms            collective-028.local    [n/a]           A8:A1:59:B2:AE:FF                   [n/a]                               ASRock Incorporation                      
    "10.157.174.42" ,  #0 ms            collective-029.local    [n/a]           A8:A1:59:B2:AD:9A                   [n/a]                               ASRock Incorporation                      
    #"10.157.175.236",#collective-030
    "10.157.174.148",#collective-032
    #"10.157.174.160",#collective-034
    #"10.157.174.163",  #0 ms            collective-038.local    [n/a]           A8:A1:59:B8:23:9F                   [n/a]                               ASRock Incorporation                      
    #"10.157.174.175",  #0 ms            collective-039.local    [n/a]           A8:A1:59:B8:25:70                   [n/a]                               ASRock Incorporation                      
    #"10.157.174.52" ,  #0 ms            collective-046.local    [n/a]           A8:A1:59:B8:23:A5                   [n/a]                               ASRock Incorporation                      
    "10.157.175.134"]  #0 ms            collective-050.local    [n/a]           A8:A1:59:B2:0F:85                   [n/a]                               ASRock Incorporation 
    modules = ["001",\
            "002","003","004","005","006","007","008","009","010","011","012","013","014","015","016","017",\
            "018","019",#"020",
            "021","022","023","024","025","026","027","028","029",#"030",
            "032",#"034",#"038","039","046",
            "050",]    
    for r,m in zip(robots_dualarm,modules):
        call_method(r,13000,"stop_task")
        print("stopping ",m,"  (",r,")")
        s=ServerProxy("http://" + r + ":8000", allow_none=True)
        s.stop_service()


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

def teach_insertable(robot:str, insertable:str, mios_port=12000):
    input("Press key to start teaching. [Pose above container, without object]")
    call_method(robot, mios_port, "teach_object", {"object": insertable+"_container_above"})
    input("Teach where to grab object")
    call_method(robot, mios_port, "grasp", {"width":0,"speed":1,"force":100})
    call_method(robot, mios_port, "teach_object", {"object": insertable, "teach_width":True})
    current_finger_width = call_method(robot,mios_port,"get_state")["result"]["gripper_width"]
    call_method(robot,mios_port,"move_gripper",{"speed":1,"force":100,"width":current_finger_width+0.005})
    #call_method(robot, mios_port, "grasp", {"width":0,"speed":1,"force":100,"epsilon_outer":1})
    #call_method(robot, mios_port, "set_grasped_object", {"object": insertable})
    time.sleep(1)
    print("closing gripper")
    print(call_method(robot, mios_port, "grasp_object", {"object": insertable}))
    input("Teach approach [with object]")
    call_method(robot, mios_port, "teach_object", {"object": insertable+"_container_approach"})
    input("Teach container [with object]")
    call_method(robot, mios_port, "teach_object", {"object": insertable+"_container"})        

