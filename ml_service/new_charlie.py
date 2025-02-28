from copy import deepcopy
import time
import random

from problem_definition.domain import Domain
from run_experiments import *

        

tasks = {   
            "collective-007.rsi.ei.tum.de":["D_022","D_011"],
            "collective-006.rsi.ei.tum.de":["D_002", "D_001", "D_021"],
            "collective-011.rsi.ei.tum.de":["D_010", "D_015","D_023"],
        }   

todos = deepcopy(tasks) # unfinihsed tasks
dos = []    # tasks in execution
threads = [] 

def check_object(host, obj):
    result = call_method(host, 12000, "get_state")
    if type(result) == dict:
        if result["result"]["grasped_object"] == obj:
            return True
    else:
        return False

def update_todos(x):
    "rm one task of x in todos, if x is empty than rm it from todos"
    todos[x].pop(0)
    if len(todos[x]) == 0:
        del todos[x]
    print(todos)
    
def start_single(x, n_current_iter=1, tags_addon:list = ["new_charlie_test"]): #10
   
    tags = ["testing"]
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

    sc = SVMLearner(50,10,0,True,False, 0.4,True).get_configuration()
        
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
    
    server = ServerProxy("http://%s:%s/" %(x, "8000"))
    insertable = tasks[x][0]    
    container = insertable+"_container" 
    approach = container+"_approach"
    pd = InsertionFactory([x], TimeMetric("insertion", {"time": 5}),
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
            
    dualarm_cmd = {"agent":x,"port":13000,"skills":dualarm_skills,"sleep":1}
    learn_single_task(x, pd, sc, tags, n_current_iter, False, knowledge_source.to_dict(), True, 8000, dualarm_cmd)

    
def doing(x):
    # 1. add x into dos
    # 2. rm x from todos
    # 3. start learing next task in the todos of x
    # 4. learning done ^ rm x form dos ^ raise hand
    # 5. if there is still objs for x; block it and stop other dos
    
    dos.append(x)
    print("start ", todos[x][0])
    update_todos(x)
    # time.sleep(random.randint(1, 20))
    start_single(x)
    
    print("stop ", x)
    dos.remove(x)
    # raise hand 
    move_joint(x, "raise_hand")
    
    # if x still in todos, then change object and stop others in dos
    if x in todos:
        print("wainting for ", x, " to grasp ", todos[x][0])    
        temp_dos = deepcopy(dos)
        for one in temp_dos:
            s = ServerProxy("http://" + one + ":8000", allow_none=True)
            s.pause_service()
            print("pause: " + one)
        
        while True:
            if check_object(x, todos[x][0]):
                break
            else:
                time.sleep(1)
        
        for one in temp_dos:
            s = ServerProxy("http://" + one + ":8000", allow_none=True)
            s.resume()
            print("pause: " + one)
    
# nr of the robot limitation to use 
n_agent = 2


while True:
    # if no robot is leaning ^ no task in todo; then stop
    if len(todos) == 0:
        if sum([t.is_alive() for t in threads]) == 0:
            if len(dos) == 0:
                break
    
    time.sleep(1)
    i = 0
     
    while len(dos) < n_agent and len(todos) > 0:
        # it will prefer to assign the task to the robots in the front of the todos
        # if it is busy then try to assign the task to the next one
        if i+1 > len(todos):
            # jump out of current iteration;in other words, do not assign tasks to any robot when no robot is available
            break
        
        x = list(todos.keys())[i]
        if  x in dos:
            # print(x + " is busy now")
            i = i + 1
        
        else:
            threads.append(Thread(target=doing, args=(x,)))
            threads[-1].start()
            

