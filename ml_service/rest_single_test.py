from copy import deepcopy
import time

from problem_definition.domain import Domain
from run_experiments import *

# ---------------------------- exp robots ------------------------------------
list_robots = ["007", "008", "010"]

print(len(list_robots))
print(list_robots)
# ---------------------------- tasks ------------------------------------
tasks = {   
            "collective-007.rsi.ei.tum.de":["D_022","D_011"],
            # "collective-008.rsi.ei.tum.de":["D_008", "D_004","D_013"],
            # "collective-010.rsi.ei.tum.de":["D_009","D_014","D_024","D_025"],
        }   

print(tasks)
total = 0
for k in tasks:
    total += len(tasks[k])
print("total tasks: ",total)

# ---------------------------- cutoff ------------------------------------

cutoff = {  
            '007_left': 0.62616,
            # '008_left': 0.6371999999999999,
            # '010_left': 0.6888000000000001,
        }
# ---------------------------- rest ------------------------------------


waiting_robots = []
# -----------------------------------------------------------------------------
            
def test(n_current_iter =1 , tags_addon:list = ["100collective","ps_charlie_1"], n_agents:int = 1): #10
    '''
    n_current_iter: number of current iteration

    '''
    # prefill_fast_pipe(n_current_iter, "collective-001.rsi.ei.tum.de")
    tags = ["rest_test"]
    # tags = ["100_testing"]
    # modules = list_block_1 + list_block_2 + list_U
    
    modules = list_robots 

    cutoff = {  
            '007_left': 0.62616,
            '008_left': 0.6371999999999999,
            '010_left': 0.6888000000000001,
        }   

    sc = SVMLearner(50,10,0,True,False, 0.4,True).get_configuration()
        
    # for n_current_iter in range(29,30): #range(15,25):   (not reserve)

    threads = []
    print("Number of iteration: ", n_current_iter+1)
    knowledge_source = Knowledge()
    knowledge_source.kb_location = "collective-001.rsi.ei.tum.de" # None #  
    knowledge_source.mode = "global"  # None:isolated parallel (no knowledge from theirself)  # "local": has transfer inside agent
    knowledge_source.scope = []
    knowledge_source.scope.extend(deepcopy(tags))
    knowledge_source.scope.append("n"+str(n_current_iter+1)) # searching for knowledge on the database (only works for the slow pipeline);  e.g. [] search all, 
    knowledge_source.type = "all"  # all: 
        
    threads = []
    tags.extend(tags_addon)
    
    robot = "collective-007.rsi.ei.tum.de"
    
    insertable = tasks[robot].pop(0)
    container = insertable+"_container" 
    approach = container+"_approach"
    pd = InsertionFactory([robot], TimeMetric("insertion", {"time": 5}),
                            {"Insertable": insertable, "Container": container,
                            "Approach": approach}).get_problem_definition(insertable)
    if insertable in cutoff:
        pd.optimum_thr = cutoff[insertable]
    else:
        pd.optimum_thr = 0.8  ###########################'!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    if insertable == "010_left" or insertable == "023_left" or insertable == "027_left":
        print("increase limits for ",insertable)
        pd.domain.limits["p2_f_push_z"] = (0,60)
    dualarm_skills = []
    move_context = {
                "skill": {
                    "speed": 0.5,
                    "acc": 1,
                    "q_g": [0, 0, 0, 0, 0, 0, 0],
                    "objects": {
                        "goal_pose": "hold_" + insertable}},
                "control": {
                    "control_mode": 3},
                "user": {
                    "env_X": [0.001, 0.001, 0.001, 0.001, 0.001, 0.001],
                    "F_ext_max": [100, 50]}}
    dualarm_skills.append(("move", "MoveToPoseJoint", move_context))
    
    dualarm_cmd = {"agent":robot,"port":13000,"skills":dualarm_skills,"sleep":1}
    threads.append(Thread(target=learn_single_task, args=(robot, pd, sc, tags, n_current_iter, False, knowledge_source.to_dict(), True, 8000, dualarm_cmd)))
    threads[-1].start()
    time.sleep(10)
    
    s = ServerProxy("http://" + robot + ":8000", allow_none=True)
    s.pause_service()
    print("pause: " + robot)
    
    time.sleep(10)
    s.resume_service()
    print("resume: " + robot)
    
    threads[-1].join()
    print("finished :)") 
    return 1

            



def check_object(host, obj):
    result = call_method(host, 12000, "get_state")
    if type(result) == dict:
        if result["result"]["grasped_object"] == obj:
            if host in waiting_robots:
                waiting_robots.pop(waiting_robots.index(host))
            return True
        else:
            if host in waiting_robots:
                return False
            waiting_robots.append(host)
            move_joint(host, "raise_hand")
            print("wainting for ",host, " to grasp ", obj)
            return False
        
def set_next_object(module, obj=None):
    addr = "collective-"+module+".rsi.ei.tum.de"
    ip = get_ips([module])[0]
    result = call_method(ip, 12000, "get_state")
    if type(result) is dict:
        current_obj = result["result"]["grasped_object"]
    else:
        print("cannot reach mios...")
        return False
    if current_obj == "NullObject":
        print("nothing is grasped right now")
        # if obj is None:
        #     print("please provide object")
        #     return False
        i = -1
    else:    
        try:
            i = tasks[addr].index(current_obj)
        except ValueError:
            print(current_obj, " is not part of ", addr)
            call_method(ip, 12000, "release_object", timeout=2)
            call_method(ip, 13000, "release_object", timeout=2)
            return False

    print(i," current object is ", current_obj)
    if obj is None:
        try:
            next_obj = tasks[addr][i+1]
            print("next object is ", next_obj)
        except IndexError:
            next_obj = tasks[addr][0]
            print("new start with ",next_obj)
    else:
        print("set next object to ", obj)
        next_obj = obj
    input("open")
    call_method(ip, 13000,"release_object",timeout=2)
    call_method(ip, 12000, "release_object",timeout=2)
    input("homeing?")
    threads = []
    port = 12000
    for i in range(0,2):
        port += i*1000
        threads.append(Thread(target=call_method,args=(ip, port, "home_gripper")))
        threads[-1].start()
    input("move to approach of "+next_obj)
    if next_obj not in get_objects(module):
        print("\n Object ",next_obj, " is not teached!")
        return False
    while True:
        print("moving")
        r1 = move_joint(ip, next_obj+"_container_above", wait=True)
        r2 = move_joint(ip, "hold_"+next_obj, wait=True, port=13000)
        if type(r1) is dict and type(r2) is dict:
            if r1["result"]["task_result"]["success"] and r1["result"]["task_result"]["success"]:
                break
        print("left arm ", r1)
        time.sleep(1)
    input("grasp")
    call_method(ip, 12000, "grasp",{"force":100,"speed":100,"width":0,"epsilon_inner":1,"epsilon_outer":1},timeout=2)
    call_method(ip, 13000, "grasp",{"force":100,"speed":100,"width":0,"epsilon_inner":1,"epsilon_outer":1},timeout=2)
    call_method(ip,12000,"set_grasped_object",{"object":next_obj})
    call_method(ip,13000,"set_grasped_object",{"object":next_obj})
    move_joint(ip,next_obj+"_container_approach",wait=False)
    return True

def get_objects(module):
    robot = get_ips([module])[0]
    client = MongoDBClient(robot)
    data = client.read("miosL","environment",{})   
    names  =[ ]
    for d in data:
        names.append(d["name"])
    return names

def move_to_first_approach():
    for t in tasks:
        ins = tasks[t][1]
        print(t, ": ", ins)
        while True:
            r1 = move_joint(t, ins+"_container_approach", wait=True)
            r2 = move_joint(t, "hold_"+ins, wait=True,port=13000)
            if type(r1) is dict and type(r2) is dict:
                if r1["result"]["task_result"]["success"] and r1["result"]["task_result"]["success"]:
                    break
            print("left: ",r1)
            print("right: ",r2)
            time.sleep(0.5)
        input("move to above")
        call_method(t, 12000, "teach_object",{"object":ins+"_container_above"})

        
    
    


