from copy import deepcopy
import time
import sys
import logging

from matplotlib import table
logger = logging.getLogger("ml_service")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)
from problem_definition.domain import Domain
from run_experiments import *
socket.setdefaulttimeout(3)
# ---------------------------- exp robots ------------------------------------
list_robots = list_block_1 + list_block_2 + list_U
# list_robots = list_block_2

# list_robots = ["001", "003", "004"]

print(len(list_robots))
print(list_robots)
# ---------------------------- cutoff cost ------------------------------------

# tasks = {   
#         "collective-001.rsi.ei.tum.de":["D_016_extHexScrewdriver-30","A_018","D_007_extHexScrewdriver-10","D_017_extDodScrewdriver-30","B_002_IEC-C7"],
#         #125, 21, 121, 162.5, 25.3 (grey)
#         "collective-003.rsi.ei.tum.de":["D_028", "D_012", "D_005", "D_018", "A_001_triangle-1"],
#         "collective-004.rsi.ei.tum.de":["D_020", "D_019", "A_002_hexagon-1"],
#         "collective-005.rsi.ei.tum.de":["D_027", "D_026", "B_001_USB-1", "D_006"],
#         "collective-006.rsi.ei.tum.de":["D_021", "A_32_pentagon-1","D_002", "D_001" ],
#         "collective-007.rsi.ei.tum.de":["D_022", "A_004_cylinder-1","D_011"],
#         "collective-008.rsi.ei.tum.de":["008_left","D_008", "D_004","D_013"],
#         "collective-036.rsi.ei.tum.de":["D_024", "B_003_plugF-1","D_009","D_014","D_025"],#PC 10 is broken and changed to 36 now
#         "collective-011.rsi.ei.tum.de":["B_004_audioJack-35", "D_010", "D_015","D_023"],
#         "collective-012.rsi.ei.tum.de":["C_007", "B_005_IEC-C13", "C_006"], #"C_key_05" is lost
#         "collective-009.rsi.ei.tum.de":["B_013", "A_005_cylinder-2","A_015_trapezoid","B_017_IT2DE"],
#         "collective-013.rsi.ei.tum.de":["C_011", "A_030_shamrock","A_012_ellipsoid-2"],
#         "collective-014.rsi.ei.tum.de":["B_016", "B_006_HDMI-1","A_024_moon","C_020"],
#         "collective-015.rsi.ei.tum.de":["C_025", "B_012_DE2DE","A_011"],
#         #"collective-016.rsi.ei.tum.de":["A_026_cylinder_60", "A_026_cylinder_10","A_026_cylinder_20","A_026_cylinder_30"],  #,,,],"A_026_cylinder_60"
#         "collective-017.rsi.ei.tum.de":["A_013_hexagram", "A_008_square-1","B_015","C_key_12"],  # included for convergence test
#         # Checkt 041 for correct teaching:
#         "collective-041.rsi.ei.tum.de":["A_009_hexagon-3","A_021_arrow","A_key_24","C_022"],  # check 41_left
#         "collective-021.rsi.ei.tum.de":["A_020_pentagram", "A_010_square-2","C_018","C_019"],
#         "collective-022.rsi.ei.tum.de":["C_009", "B_007_audioJack","C_010","C_013"],
#         "collective-023.rsi.ei.tum.de":["C_014", "B_008_USB-2","A_019_oneline","C_key_08"],
#         "collective-024.rsi.ei.tum.de":["B_014_CN", "C_015", "C_017"],
#         "collective-025.rsi.ei.tum.de":["A_025_heart", "A_014_doji-1","A_023_stairs"],
#         "collective-026.rsi.ei.tum.de":["B_018","A_016_cross-1","A_022_diamond"],    #["026_left","B-014","A_022_diamond","B-018"],
#         "collective-027.rsi.ei.tum.de":["B_010_plugF-2","C_016","C_key_23","A_031_audi"]
#         # "collective-040.rsi.ei.tum.de":[], # teach 40
#         #"collective-029.rsi.ei.tum.de":["029_left","A_016_sector","A_018_cross-2", "A_016_cross-1"]
#         }
tasks = {   
        "collective-001.rsi.ei.tum.de":["B_002_IEC-C7","D_016_extHexScrewdriver-30","A_018","D_007_extHexScrewdriver-10","D_017_extDodScrewdriver-30"],
        "collective-003.rsi.ei.tum.de":["D_028", "D_012", "D_005", "D_018", "A_001_triangle-1"],
        "collective-004.rsi.ei.tum.de":["D_020", "D_019", "A_002_hexagon-1"],
        "collective-005.rsi.ei.tum.de":["D_027", "D_026", "B_001_USB-1", "D_006"],
        "collective-006.rsi.ei.tum.de":["D_021", "A_32_pentagon-1","D_002", "D_001" ],
        "collective-007.rsi.ei.tum.de":["D_022", "A_004_cylinder-1","D_011"],
        "collective-008.rsi.ei.tum.de":["008_left","D_008", "D_004","D_013"],
        "collective-044.rsi.ei.tum.de":["D_024", "B_003_plugF-1","D_009","D_014","D_025"],#PC 10 is broken and changed to 36 now
        
        "collective-011.rsi.ei.tum.de":["B_004_audioJack-35", "D_010", "D_015","D_023"],
        "collective-012.rsi.ei.tum.de":["C_007", "B_005_IEC-C13", "C_006"], #"C_key_05" is lost
        "collective-043.rsi.ei.tum.de":["B_013", "A_005_cylinder-2","A_015_trapezoid","B_017_IT2DE"],
        "collective-013.rsi.ei.tum.de":["C_011", "A_030_shamrock","A_012_ellipsoid-2"],
        "collective-014.rsi.ei.tum.de":["B_016", "B_006_HDMI-1","A_024_moon","C_020"], 
        "collective-015.rsi.ei.tum.de":["C_025", "B_012_DE2DE","A_011"],
        "collective-016.rsi.ei.tum.de":["A_026_cylinder_30", "A_026_cylinder_60", "A_026_cylinder_10","A_026_cylinder_20"],  #,,,],"A_026_cylinder_60"
        "collective-042.rsi.ei.tum.de":["A_013_hexagram", "A_008_square-1","B_015","C_key_12"],
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
task_sequence = []
count = 0
tasks_temp = copy.deepcopy(tasks)
while True:
    for robot in tasks_temp.keys():
        robot_tasks = tasks_temp[robot]
        if len(robot_tasks)>0:
            task_sequence.append(robot_tasks.pop(0))
            count += 1
            print(task_sequence[-1])
    if sum([len(robot_tasks) for robot_tasks in tasks_temp.values()]) == 0:
        break

print("total tasks: ",count)
print("task sequence: ",task_sequence)

def set_all_object(tasks=tasks, tablemount = False):
    for robot in tasks:
        ip = get_ips([robot.split(".")[0][-3:]])[0]
        next_obj = tasks[robot][0]
        if tablemount:
            next_obj = next_obj + "_table"
        print("set ", next_obj, " for ", robot)
        call_method(ip,12000,"grasp",{"speed":0.2,"force":100,"width":0,"epsilon_inner":1,"epsilon_outer":1})
        call_method(ip,13000,"grasp",{"speed":0.2,"force":100,"width":0,"epsilon_inner":1,"epsilon_outer":1})
        set_result = call_method(ip,12000,"set_grasped_object",{"object":next_obj})
        # print(set_)
        call_method(ip,13000,"set_grasped_object",{"object":"hold_"+next_obj})
    
    # print all current object for double-check
    for robot in tasks:
        ip = get_ips([robot.split(".")[0][-3:]])[0]
        result = call_method(ip, 12000, "get_state")
        if type(result) == dict:
            print(robot, " is grasping ", result["result"]["grasped_object"])
        else:
            print("cannot reach ", robot)
class have_a_rest:
    def __init__(self):
        self.robots = list(tasks.keys())

    def pause_all(self):
        threads = []
        for robot in self.robots:
            threads.append(Thread(target=self.pause, args=(robot,)))
            threads[-1].start()
        for t in threads:
            t.join()
        #logger.debug("All robots are paused.") 

    def resume_all(self):
        threads = []
        for robot in self.robots:
            threads.append(Thread(target=self.resume, args=(robot,)))
            threads[-1].start()
        for t in threads:
            t.join()
        #logger.debug("All robots are resumed.") 

    def pause(self, one):
        #logger.debug("pause "+one)
        s = ServerProxy("http://" + one + ":8000", allow_none=True)
        try:
            s.pause_service()
        except socket.gaierror:
            #logger.debug("pause: "+ one +" socket.gaierror")
            pass
        
    def resume(self, one):
        #logger.debug("resume "+one)
        s = ServerProxy("http://" + one + ":8000", allow_none=True)
        try:
            s.resume_service()
        except socket.gaierror:
            #logger.debug("resume: "+ one +" socket.gaierror")
            pass

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
waiting_robots = []
# -----------------------------------------------------------------------------
def prefill_fast_pipe(iteration_n:int, kb_location:str, tags: list = ["10agents_25tasks","ps_alpha_5"]):
    client = MongoDBClient("collective-001.rsi.ei.tum.de")
    kb = ServerProxy("http://" + kb_location+ ":8001", allow_none=True)
    kb.clear_memory()
    tags.append("n"+str(iteration_n))
    data = client.read("global_ml_results","insertion", {"meta.tags":tags})
    print(len(data), " results round.")
    cnt = 0
    for results in data: 
        task_ident = str(results["meta"]["tags"])
        domain = Domain.from_dict(results["meta"]["domain"])
        for i in range(1,len(results)-3+1):
            if results["n"+str(i)]["q_metric"]["success"]:
                theta = []
                for key in results["n"+str(i)]["theta"].keys():
                    theta.append(results["n"+str(i)]["theta"][key])
                theta_normalised = domain.normalize(theta).tolist()
                kb.push_trial(task_ident, list(theta_normalised), results["n"+str(i)]["q_metric"]["final_cost"], 1000)
                cnt += 1
            else:
                continue
    print(cnt, "successfull trials pushed.")
            
def collective25(n_current_iter:int, tags_addon:list = ["100collective","ps_charlie", "20agents"], n_agents:int = 25, prefill=False): #10
    '''
    n_current_iter: number of current iteration

    '''
    logger.debug("start")
    if prefill:
        prefill_fast_pipe(n_current_iter, "collective-001.rsi.ei.tum.de")
        tags = ["ps_alpha_5","10agents_25tasks"]
    else:
        s = ServerProxy("http://collective-001.rsi.ei.tum.de:8001")
        s.clear_memory()
        tags = deepcopy(tags_addon)
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

    sc = SVMLearner(1500,10,0,True,False, 0.4,True).get_configuration()
    #sc = OrigPSPLearner(150,10,0,True,False, 0.4,True).get_configuration()
        
    # for n_current_iter in range(29,30): #range(15,25):   (not reserve)

    print("Number of iteration: ", n_current_iter+1)
    knowledge_source = Knowledge()
    knowledge_source.kb_location = "collective-001.rsi.ei.tum.de" # None #  
    knowledge_source.mode = "global"  # None:isolated parallel (no knowledge from theirself)  # "local": has transfer inside agent
    knowledge_source.scope = []
    knowledge_source.scope.extend(deepcopy(tags))
    knowledge_source.scope.append("n"+str(n_current_iter+1)) # searching for knowledge on the database (only works for the slow pipeline);  e.g. [] search all, 
    knowledge_source.type = "all"  # all: 
        
    threads = []
    if prefill:
        tags.extend(tags_addon)
    
    while len(tasks) > 0:
        finished_robot = []
        Rest = have_a_rest() # init with the robots
        for robot in tasks:
            server = ServerProxy("http://%s:%s/" %(robot, "8000"))
            if len(tasks[robot]) == 0:
                finished_robot.append(robot)
                continue
            try:
                if server.is_busy():
                    continue
            except (socket.gaierror, TimeoutError):
                continue
            if not check_object(robot, tasks[robot][0]):
                if len(task_sequence) > 0:
                    if task_sequence[0] == tasks[robot][0]:
                        Rest.pause_all()
                continue
            if sum([t.is_alive() for t in threads]) >= n_agents:
                continue
            if not get_states([robot.split(".")[0][-3:]])[0]: # get_states() returns True if IdleTask and not Busy
                continue

            Rest.resume_all()
            insertable = tasks[robot].pop(0)
            container = insertable+"_container" 
            approach = container+"_approach"
            pd = InsertionFactory([robot], TimeMetric("insertion", {"time": 5}),
                                    {"Insertable": insertable, "Container": container,
                                    "Approach": approach}).get_problem_definition(insertable)
            if insertable in cutoff:
                pd.optimum_thr = cutoff[insertable]
            else:
                pd.optimum_thr = 0  ###########################'!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            pd.cost_function.finish_thr = 2  # undercut cutoff threshold 3 time to stop learning
            if insertable == "010_left" or insertable == "023_left" or insertable == "027_left" or insertable[0] == "B":
                print("increase limits for ",insertable)
                pd.domain.limits["p2_f_push_z"] = (0,60)
            dualarm_skills = []
            holdPose = "hold_"+insertable
            if insertable[-4:] == "left":
                holdPose = "hold"
            move_context = {
                        "skill": {
                            "speed": 0.5,
                            "acc": 1,
                            "q_g": [0, 0, 0, 0, 0, 0, 0],
                            "objects": {
                                "goal_pose": holdPose}},
                        "control": {
                            "control_mode": 3},
                        "user": {
                            "env_X": [0.001, 0.001, 0.001, 0.001, 0.001, 0.001],
                            "F_ext_max": [100, 50]}}
            dualarm_skills.append(("move", "MoveToPoseJoint", move_context))
            
            dualarm_cmd = {"agent":robot,"port":13000,"skills":dualarm_skills,"sleep":1}
            threads.append(Thread(target=learn_single_task, args=(robot, pd, sc, tags, n_current_iter, False, knowledge_source.to_dict(), True, 8000, dualarm_cmd)))
            threads[-1].start()
            time.sleep(1)
        for robot in finished_robot:
            tasks.pop(robot)

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
        
def set_next_object(module, obj:int|str = None):
    addr = "collective-"+module+".rsi.ei.tum.de"
    ip = get_ips([module])[0]
    result = call_method(ip, 12000, "get_state",timeout=5)
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
    elif type(obj) is str:
        print("set next object to ", obj)
        next_obj = obj
    elif type(obj) is int:
        next_obj = tasks[addr][obj]
        print("set next object to ", obj)
    else:
        print("Faulty input! obj should be str or int, but, ",obj,", is ", type(obj))
        return False
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

def move_to_first_approach(tabletop=False):
    for i,t in enumerate(tasks):
        #if i<10:
        #    continue
        ins = tasks[t][0]
        if tabletop:
            ins = ins+"_table"
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

def modify_object_length(module, object, length_mm):
    ip = get_ips([module])[0]
    client = MongoDBClient(ip)
    o = client.read("miosL", "environment", {"name":object})[0]
    o["OB_T_TCP"][14] = length_mm/1000
    o["object"] = o["name"]
    call_method(ip,12000, "set_object", o)

def release_object(module, hand="left"):
    ip = get_ips([module])[0]
    if hand == "left": 
        call_method(ip, 12000, "release_object", timeout=2)
    elif hand == "right":
        call_method(ip, 13000, "release_object", timeout=2)
    elif hand == "both":
        call_method(ip, 12000, "release_object", timeout=2)
        call_method(ip, 13000, "release_object", timeout=2)
    else:
        print("Hand is not properly specified.")

def change_tags(old_tags, replacement_tags, database = "ml_results"):

    possible_tasks = []
    for mtasks in tasks.values():
        for task in mtasks:
            possible_tasks.append(task) 
    for host in tasks.keys():
        client = MongoDBClient(host)
        try:
            data = client.read(database, "insertion", {"meta.tags":old_tags})
            if len(data) < 1:
                print("cannot find data at ", host)
            if len(data) > 1:
                print("found ",len(data), " entries at ", host)
                answer = input(" continue? [Y/n]") 
                if answer != "" or answer != "y" or answer != "Y":
                    print("aborting...\n")
                    continue
            for d in data:
                instance = "NullObject"
                for t in d["meta"]["tags"]:
                    if t in possible_tasks:
                        instanec = t
                        break
                print(d["meta"]["tags"], "  >  ", replacement_tags+[t])
                client.update(database, "insertion", {"_id": d["_id"]}, {"meta.tags":replacement_tags})
        except:
            print("cannot update tags on ", host)
            continue


def get_state(module):
    ip = get_ips([module])[0]
    current_task_left = call_method(ip, 12000, "get_state")["result"]["current_task"]
    current_task_right = call_method(ip, 13000, "get_state")["result"]["current_task"]
    print("Left arm tasks is:", current_task_left, "Right arm task is:", current_task_right)
    grasped_object = call_method(ip, 12000, "get_state")["result"]["grasped_object"]
    print("Grasped object is:", grasped_object)

def grasp(m):
     ip = get_ips([m])[0]
     call_method(ip, 12000,"grasp",{"width":0,"force":100,"speed":1,"epsilon_outer":1,"epsilon_inner":1})
     call_method(ip, 13000,"grasp",{"width":0,"force":100,"speed":1,"epsilon_outer":1,"epsilon_inner":1})

def count_experiments():
    alle = []
    alle_ps_1 = []
    alle_ps_2 = []
    alle_ps_test = []
    alle_ps_test2 = []
    alle_ps_test3 = []
    alle_ps_test4 = []
    alle_ps_test6 = []
    alle_ps_test7 = []
    for r in tasks.keys():
        r_local = r[:-14]+".local"
        client = MongoDBClient(r_local)
        print("\n",r)
        ps_charlie_1 = client.read("ml_results","insertion",{"meta.tags":["ps_charlie_1"]})
        not_this = []
        for d in range(len(ps_charlie_1)):
            if "rest_test" in ps_charlie_1[d]["meta"]["tags"]:
                not_this.append(d)
        not_this.reverse()
        for i in not_this:
            _ = ps_charlie_1.pop(i)
        print("ps_charlie_1: ",len(ps_charlie_1))
        alle.append(len(ps_charlie_1))
        alle_ps_1.append(len(ps_charlie_1))


        ps_charlie_2 = client.read("ml_results","insertion",{"meta.tags":["ps_charlie_2", "n5"]})
        print("ps_charlie_2 n5: ",len(ps_charlie_2), "should be ",len(tasks[r]))
        alle.append(len(ps_charlie_2))
        alle_ps_2.append(len(ps_charlie_2))
        ps_charlie_2 = client.read("ml_results","insertion",{"meta.tags":["ps_charlie_2", "n6"]})
        print("ps_charlie_2 n6: ",len(ps_charlie_2), "should be ",len(tasks[r]))
        alle.append(len(ps_charlie_2))
        alle_ps_2.append(len(ps_charlie_2))

        ps_charlie_test = client.read("ml_results","insertion",{"meta.tags":["ps_charlie_test","n2"]})
        print("ps_charlie_test n2: ",len(ps_charlie_test), "should be ",len(tasks[r]))
        alle.append(len(ps_charlie_test))
        alle_ps_test.append(len(ps_charlie_test))
        alle_ps_test2.append(len(ps_charlie_test))
        ps_charlie_test = client.read("ml_results","insertion",{"meta.tags":["ps_charlie_test","n3"]})
        print("ps_charlie_test n3: ",len(ps_charlie_test), "should be ",len(tasks[r]))
        alle.append(len(ps_charlie_test))
        alle_ps_test.append(len(ps_charlie_test))
        alle_ps_test3.append(len(ps_charlie_test))
        ps_charlie_test = client.read("ml_results","insertion",{"meta.tags":["ps_charlie_test","n4"]})
        print("ps_charlie_test n4: ",len(ps_charlie_test), "should be ",len(tasks[r]))
        alle.append(len(ps_charlie_test))
        alle_ps_test.append(len(ps_charlie_test))
        alle_ps_test4.append(len(ps_charlie_test))
        ps_charlie_test = client.read("ml_results","insertion",{"meta.tags":["ps_charlie_test","n6"]})
        print("ps_charlie_test n6: ",len(ps_charlie_test), "should be ",len(tasks[r]))
        alle.append(len(ps_charlie_test))
        alle_ps_test.append(len(ps_charlie_test))
        alle_ps_test6.append(len(ps_charlie_test))
        ps_charlie_test = client.read("ml_results","insertion",{"meta.tags":["ps_charlie_test","n7"]})
        print("ps_charlie_test n7: ",len(ps_charlie_test), "should be ",len(tasks[r]))
        alle.append(len(ps_charlie_test))
        alle_ps_test.append(len(ps_charlie_test))
        alle_ps_test7.append(len(ps_charlie_test))

    print("\n\nps_charlie_1", sum(alle_ps_1))
    print("ps_charlie_2", sum(alle_ps_2))
    print("ps_charlie_test", sum(alle_ps_test))
    print("ps_charlie_test n2", sum(alle_ps_test2))
    print("ps_charlie_test n3", sum(alle_ps_test3))
    print("ps_charlie_test n4", sum(alle_ps_test4))
    print("ps_charlie_test n6", sum(alle_ps_test6))
    print("ps_charlie_test n7", sum(alle_ps_test7))
    
    print("\n\ntotal: ",sum(alle))
        
