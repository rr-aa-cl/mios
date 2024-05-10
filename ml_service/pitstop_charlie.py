from copy import deepcopy
from http import client

from pathspec import iter_tree
from run_experiments import *

# ---------------------------- exp robots ------------------------------------
list_robots = list_block_1 + list_block_2 + list_U
# list_robots = list_block_2

# list_robots = ["001", "003", "004"]

print(len(list_robots))
print(list_robots)
# ---------------------------- cutoff cost ------------------------------------
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
# -----------------------------------------------------------------------------
def prefill_fast_pipe(iteration_n:int, kb_location:str, tags: list = ["10agents_25robots","ps_alpha_5"]):
    client = MongoDBClient("collective-001.rsi.ei.tum.de")
    kb = ServerProxy("http://" + kb_location+ ":8001", allow_none=True)
    tags.append("n"+str(iteration_n))
    data = client.read("global_ml_results","insertion", {"meta.tags":tags})
    for results in data: 
        task_ident = str(results["meta"]["tags"])
        for i in range(1,len(results)-3+1):
            try:
                if results["n"+str(i)]["q_metric"]["success"]:
                    kb.push_trial(task_ident, results["n"+str(i)]["theta"],results["n"+str(i)]["q_metric"]["final_result"], 1000)
                else:
                    continue
            except KeyError:
                break

            
def collective25(n_current_iter:int, tags_addon:list = ["100collective","ps_charlie_1"], n_agents:int = 25): #10
    '''
    n_current_iter: number of current iteration

    '''
    tags = ["ps_alpha_5","10agents_25tasks", "round1"]
    # tags = ["100_testing"]
    # modules = list_block_1 + list_block_2 + list_U
    
    modules = list_block_1 
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
                '040_left': 0.61824,
                '029_left': 0.68088}
    # sc = SVMLearner(450,10,0,True,False, 0.4,True).get_configuration()
    sc = SVMLearner(450,10,0,True,False, 0.4,True).get_configuration()
        
    # for n_current_iter in range(29,30): #range(15,25):   (not reserve)

    tasks = {   
                "collective-001.rsi.ei.tum.de":["D_007","D_016","D_017"],
                "collective-003.rsi.ei.tum.de":["D_012","D_005","D_018"],
                "collective-004.rsi.ei.tum.de":["D_003","D_019","D_020"],
                "collective-005.rsi.ei.tum.de":["D_006", "D_024", "D_027"],
                "collective-006.rsi.ei.tum.de":["D_002", "D_001", "D_021"],
                "collective-007.rsi.ei.tum.de":["D_022","D_024","D_025"],
                "collective-008.rsi.ei.tum.de":["D_008", "D_004", "D_013"],
                "collective-010.rsi.ei.tum.de":["D_009"],
                "collective-011.rsi.ei.tum.de":["D_010"],
                "collective-012.rsi.ei.tum.de":["C_key_05"],
                "collective-009.rsi.ei.tum.de":["B_017_IT2DE"],
                "collective-013.rsi.ei.tum.de":["A_012_ellipsoid-2"],
                "collective-014.rsi.ei.tum.de":["A_024_moon"],
                "collective-015.rsi.ei.tum.de":["B_012_DE2DE"],
                "collective-016.rsi.ei.tum.de":["A_026_cylinder_s6"],
                "collective-017.rsi.ei.tum.de":["C_key_12"],
                "collective-041.rsi.ei.tum.de":["A_key_24"],
                "collective-021.rsi.ei.tum.de":["A_020_pentagram"],
                "collective-022.rsi.ei.tum.de":["C_key_10"],
                "collective-023.rsi.ei.tum.de":["C_key_08"],
                "collective-024.rsi.ei.tum.de":["C_key_24"],
                "collective-025.rsi.ei.tum.de":["A_023_stairs"],
                "collective-026.rsi.ei.tum.de":["A_022_diamond"],
                "collective-027.rsi.ei.tum.de":["C_key_23"],
                # "collective-040.rsi.ei.tum.de":[],
                "collective-029.rsi.ei.tum.de":["A_018_cross-2", "A_016_cross-1"]
            }


    threads = []
    print("Number of iteration: ", n_current_iter+1)
    knowledge_source = Knowledge()
    knowledge_source.kb_location = "collective-001.rsi.ei.tum.de" # None #  
    knowledge_source.mode = "global"  # None:isolated parallel (no knowledge from theirself)  # "local": has transfer inside agent
    knowledge_source.scope = [] # TODO: may here add the tag of previous running
    knowledge_source.scope.extend(deepcopy(tags))
    knowledge_source.scope.append("n"+str(n_current_iter+1)) # searching for knowledge on the database (only works for the slow pipeline);  e.g. [] search all, 
    knowledge_source.type = "all"  # all: 
        
    

    threads = []
    tags.extend(tags_addon)
    while len(tasks) > 0:
        for robot in tasks:
            
            
            dualarm_skills = []
            move_context = {
                        "skill": {
                            "speed": 0.5,
                            "acc": 1,
                            "q_g": [0, 0, 0, 0, 0, 0, 0],
                            "objects": {
                                "goal_pose": "hold_" + tasks[robot][0]}},
                        "control": {
                            "control_mode": 3},
                        "user": {
                            "env_X": [0.001, 0.001, 0.001, 0.001, 0.001, 0.001],
                            "F_ext_max": [100, 50]}}
            dualarm_skills.append(("move", "MoveToPoseJoint", move_context))
            
            kb = ServerProxy("http://" + knowledge_source.kb_location+ ":8001", allow_none=True)
            kb.clear_memory()
            
            server = ServerProxy("http://%s:%s/" %(robot, "8000"))
            if len(tasks[robot]) == 0:
                tasks.pop(robot)
                continue
            if server.is_busy():
                continue
            insertable = tasks[robot][0]
            if not check_object(robot, insertable):
                continue
            if sum([t.is_alive() for t in threads]) >= n_agents:
                time.sleep(1)
                continue

            container = insertable+"_container" 
            approach = container+"_approach"
            pd = InsertionFactory([robot], TimeMetric("insertion", {"time": 5}),
                                    {"Insertable": insertable, "Container": container,
                                    "Approach": approach}).get_problem_definition(insertable)
            if not get_states([robot.split(".")[0][-3:]])[0]:
                print(robot, "is not ready! Skipping task ",insertable)
                continue
            if insertable in cutoff:
                sc.finish_cost = cutoff[insertable]
            else:
                sc.finish_cost = 0.6
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
    return "finished :)"

def check_object(host, obj):
    result = call_method(host, 12000, "get_state")
    if type(result) == dict:
        if result["result"]["grasped_object"] == obj:
            return True
        else:
            if host == "collective-041.rsi.ei.tum.de" or host == get_ips["041"][0]:
                move_joint(host, "raise_hand_041")
            else:                
                move_joint(host, "raise_hand")
            print("wainting for ",host, " to grasp ", obj)
            return False

def alpha_experiment():
    for i in range(10):  # iteration
        for n in range(6,10):
            var_agent_collective(n,i, [str(n)+"agents_25tasks","collective","ps_alpha_var"])

def alpha_experiment_second():
    for i in range(10):  # iteration
        for n in range(1,5):
            var_agent_collective(n,i, [str(n)+"agents_25tasks","collective","ps_alpha_var"])
