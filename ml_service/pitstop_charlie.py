from concurrent.futures import thread
from copy import deepcopy
import time
import sys
import logging
logger = logging.getLogger("ml_service")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)
from problem_definition.domain import Domain
from run_experiments import *

# ---------------------------- exp robots ------------------------------------
list_robots = list_block_1 + list_block_2 + list_U
# list_robots = list_block_2

# list_robots = ["001", "003", "004"]

print(len(list_robots))
print(list_robots)
# ---------------------------- cutoff cost ------------------------------------

tasks = {   
        "collective-001.rsi.ei.tum.de":["A_018","D_007_extHexScrewdriver-10","D_016_extHexScrewdriver-30","D_017_extDodScrewdriver-30","B_002_IEC-C7"],
        "collective-003.rsi.ei.tum.de":["A_001_triangle-1","D_012","D_005","D_018","D_028"],
        "collective-004.rsi.ei.tum.de":["A_002_hexagon-1","D_019","D_020"],
        "collective-005.rsi.ei.tum.de":["B_001_USB-1","D_006", "D_026", "D_027"],
        "collective-006.rsi.ei.tum.de":["A_32_pentagon-1","D_002", "D_001", "D_021"],
        "collective-007.rsi.ei.tum.de":["A_004_cylinder-1","D_022","D_011"],
        # "collective-008.rsi.ei.tum.de":["008_left","D_008", "D_004","D_013"],
        "collective-036.rsi.ei.tum.de":["010_left","D_009","D_014","D_024","D_025"],#PC 10 is broken and changed to 36 now
        "collective-011.rsi.ei.tum.de":["B_004_audioJack-35","D_010", "D_015","D_023"],
        "collective-012.rsi.ei.tum.de":["012_left","C_007","C_key_05","C_006"],
        "collective-009.rsi.ei.tum.de":["009_left","A_015_trapezoid","B_017_IT2DE","B_013"],
        "collective-013.rsi.ei.tum.de":["A_030_shamrock","A_012_ellipsoid-2", "C_011"],
        "collective-014.rsi.ei.tum.de":["B_006_HDMI-1","A_024_moon","C_020","B_016"],
        "collective-015.rsi.ei.tum.de":["B_012_DE2DE","A_011","C_025"],
        "collective-016.rsi.ei.tum.de":["A_026_cylinder_10","A_026_cylinder_20","A_026_cylinder_60","A_026_cylinder_30"],  #,,,],"A_026_cylinder_60"
        "collective-017.rsi.ei.tum.de":["A_008_square-1","B_015","C_key_12","A_013_hexagram"],
        # Checkt 041 for correct teaching:
        "collective-041.rsi.ei.tum.de":["A_009_hexagon-3","A_021_arrow","A_key_24","C_022"],  # check 41_left
        "collective-021.rsi.ei.tum.de":["A_010_square-2","C_018","A_020_pentagram","C_019"],
        "collective-022.rsi.ei.tum.de":["B_007_audioJack","C_010","C_013","C_009"],
        "collective-023.rsi.ei.tum.de":["B_008_USB-2","A_019_oneline","C_key_08","C_014"],
        "collective-024.rsi.ei.tum.de":["B_014_CN","C_017","C_015"],
        "collective-025.rsi.ei.tum.de":["A_014_doji-1","A_023_stairs","A_025_heart"],
        # "collective-026.rsi.ei.tum.de":["026_left","B-014","A_022_diamond","B-018"],
        "collective-027.rsi.ei.tum.de":["B_010_plugF-2","C_016","C_key_23","A_031_audi"],
        # "collective-040.rsi.ei.tum.de":[], # teach 40
        # "collective-029.rsi.ei.tum.de":["029_left","A_016_sector","A_018_cross-2", "A_016_cross-1"]
        }
total = 0
for k in tasks:
    total += len(tasks[k])
print("total tasks: ",total)

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

    def resume_all(self):
        threads = []
        for robot in self.robots:
            threads.append(Thread(target=self.resume, args=(robot,)))
            threads[-1].start()
        for t in threads:
            t.join()

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
            
def collective25(n_current_iter:int, tags_addon:list = ["100collective","ps_charlie_1"], n_agents:int = 25, prefill=False): #10
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

    sc = SVMLearner(150,10,0,True,False, 0.4,True).get_configuration()
        
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
            except socket.gaierror:
                continue
            if not check_object(robot, tasks[robot][0]):
                Rest.pause_all()
                continue
            if sum([t.is_alive() for t in threads]) >= n_agents:
                continue
            if not get_states([robot.split(".")[0][-3:]])[0]:
                continue
            Rest.resume_all()
            insertable = tasks[robot].pop(0)
            container = insertable+"_container" 
            approach = container+"_approach"
            pd = InsertionFactory([robot], TimeMetric("insertion", {"time": 5}),
                                    {"Insertable": insertable, "Container": container,
                                    "Approach": approach}).get_problem_definition(insertable)
            if insertable in cutoff:
                sc.finish_cost = cutoff[insertable]
            else:
                sc.finish_cost = 0.8  ###########################'!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            if insertable == "010_left" or insertable == "023_left" or insertable == "027_left":
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

        
    
    


