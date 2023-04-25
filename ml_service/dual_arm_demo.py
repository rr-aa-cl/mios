from definitions.templates import *
from definitions.cost_functions import *
from definitions.service_configs import *
from utils.database import delete_global_knowledge
from utils.experiment_wizard import *
from utils.taxonomy_utils import *
from services.knowledge import Knowledge
from utils.helper_functions import *
from run_experiments import *
from demo2 import stop_service
from run_experiments import *
from threading import Thread
from run_experiments import learn_insertion


path_to_default_context = os.getcwd() + "/../python/taxonomy/default_contexts/"
#robot = "kfm01-dev.rsi.ei.tum.de"
#robot = "collective-008"

port_right = 13000
port_left = 12000


def hold_pose(robot, duration, port):
    hold_context = {
        "skill": {
            "t_max": duration,
        },
        "control": {
            "control_mode": 0,
            "cart_imp": {
                "K_x": [2000, 2000, 2000, 250, 250, 250]
            }
        },
        "user": {"F_ext_max": [100, 50]}
    }
    t = Task(robot, port)
    t.add_skill("hold","HoldPose",hold_context)
    t.start(queue=False)
    #t.wait()


def insert_test(robot, learning_time = 121, wait=True):
    move_joint(robot,"hold_lock",port_right)
    hold_pose(robot,3600,port_right)
    approach = "generic" + "_container_approach"
    container = "generic" + "_container"
    
    move_joint(robot,"generic"+"_container_above", port_left)
    call_method(robot,port_left,"set_grasped_object",{"object":"generic_insertable"})
    move_joint(robot,"generic"+"_container_approach", port_left)

    #insertion_context = download_best_result_tags("collective-panda-prime.local","ml_results","insertion",["collective_learning"])
    f = open(path_to_default_context + "insertion.json")
    insertion_context = json.load(f)
    

    sc = SVMLearner(130,10,0,True,False, 0,True).get_configuration()
    tags = ["demo_collective","key_door"]
    #tags = ["demo_learning"]
    threads = []
    pd = InsertionFactory([robot], TimeMetric("insertion", {"time": 5}),
                                    {"Insertable": "generic_insertable", "Container": container,
                                    "Approach": approach}).get_problem_definition("generic_insertable")
    print(learning_time)
    if learning_time > 120:
        knowledge_source = Knowledge()
        knowledge_source.kb_location = robot  # "collective-dev-001"  #"collective-panda-prime" 
        knowledge_source.mode = "local"
        knowledge_source.scope = []
        knowledge_source.scope.extend(tags)
        knowledge_source.type = "all"
        learn_single_task(robot, pd, sc, tags, 0, False, knowledge_source.to_dict(), False)
    else:
        knowledge_source = Knowledge()
        #knowledge_source.kb_location =  "collective-dev-001.rsi.ei.tum.de"  #"collective-panda-prime" 
        knowledge_source.mode = "local"
        knowledge_source.scope = ["demo_collective"]
        knowledge_source.scope.extend(["generic_insertable"])
        knowledge_source.type = "all"
        learn_single_task(robot, pd, sc, tags, 0, False, knowledge_source.to_dict(), False)
    if wait:
        input("Press any key to stop learning.")
    
        stop_service(robot)

        while call_method(robot,port_left,"is_busy")["result"]["busy"]:
            stop_service(robot)

            time.sleep(2)
        stop_task(robot,port=port_right)
        time.sleep(5)
    #place_insertable("collective-panda-prime","key_door","key_door_container","key_door_container_approach","key_door_container_above")


def rotate_to_lock():
    print("rotate to table")
    move_joint(robot,"hold_lock",port_right, wait=True)
    result = move_joint(robot,"rotation_1",port_right, wait=True)
    result = move(robot,"generic_lock",[0,0,0],port_right)
   
    
def rotate_to_hold():
    print("rotate to holding position")
    move_joint(robot,"rotation_1", port_right)
    move_joint(robot,"hold_lock",port_right)

def take_lock():
    call_method(robot,port_right,"home_gripper")
    rotate_to_lock()
    result = call_method(robot,port_right,"grasp_object",{"object":"generic_lock"})
    while not result["result"]["result"]:
        move_joint(robot, port_right,"generic_lock")
        result = call_method(robot,port_right,"grasp_object",{"object":"generic_lock"})
    move(robot,"rotation_1",[0,0,0],port_right)

def place_lock():
    rotate_to_lock()
    if not call_method(robot,port_right,"release_object")["result"]["result"]:
        call_method(robot,port_right,"home_gripper")
    move(robot,"rotation_1",[0,0,0],port_right)

def take_key():
    move_joint(robot,"generic_insertable_grasp",port_left)
    time.sleep(5)
    call_method(robot,port_left,"grasp_object",{"object":"generic_insertable"})
    move_joint(robot,"generic_insertable_container_above",port_left)

def release_key():
    move_joint(robot,"place_insertable",port_left)
    call_method(robot,port_left,"release_object",{"object":"generic_insertable"})
    move_joint(robot,"generic_insertable_grasp",port_left)

def thread_right():
    call_method(robot,port_right,"home_gripper")
    rotate_to_lock()
    while not call_method(robot,port_right,"grasp_object",{"object":"generic_lock"})["result"]["result"]:
        print("grasping lock not successfull")
        call_method(robot,port_right,"move_gripper",{"speed":1,"width":0.08,"force":100})
        move_joint(robot,"generic_lock",port_right)
    rotate_to_hold()

def thread_left():
    call_method(robot,port_left,"release_object")
    call_method(robot,port_left,"home_gripper")
    take_key()


def demo():
    threads = []
    threads.append(Thread(target=thread_left))
    threads.append(Thread(target=thread_right))
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    insert_test(50)
    call_method(robot,port_right,"stop_task")
    call_method(robot,port_left,"stop_task")
    time.sleep(10)
    threads = []
    threads.append(Thread(target=place_lock))
    threads.append(Thread(target=release_key))
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

def stop_services():
    def stop_service(service):
        is_running = True
        while is_running:
            try:
                service.stop_sercive()
                time.sleep(3)
                is_running = service.is_busy()
            except:
                is_running = False
    hostnames = ["collective-%03d.rsi.ei.tum.de"%n for n in range(1,47)]
    threads = []
    learning_services = []
    for r in hostnames:
        threads.append(Thread(target=stop_service, args=(ServerProxy("http://" + r+ ":8000", allow_none=True))))
        threads[-1].start()
        threads.append(Thread(target=stop_service, args=(ServerProxy("http://" + r+ ":9000", allow_none=True))))
        threads[-1].start()     
    for t in threads:
        t.join()


def test():
    hostnames = ["collective-%03d.rsi.ei.tum.de"%n for n in range(1,25)]
    for robot in hostnames:
        try:
            insert_test(robot,50,wait=False)
        except TypeError:
            pass
    input("press key to stop learning")
    for robot in hostnames:
        try:
            stop_service(robot)
            while call_method(robot,port_left,"is_busy")["result"]["busy"]:
                stop_service(robot)
            stop_task(robot,port=port_right)
        except TypeError:
            pass

def dryrun():
    hostnames = ["collective-%03d.rsi.ei.tum.de"%n for n in range(1,50)]
    lefties = []
    righties = []
    dualarm = []
    for host in hostnames:
        stop_task(host,port=12000)
        stop_task(host,port=13000)
        r_left = call_method(host,12000,"get_state")
        r_right = call_method(host,13000,"get_state")
        if r_left is not None:
            if r_left["result"]["state"] == "idle":
                lefties.append(host)
        if r_right is not None:
            if r_right["result"]["state"] == "idle":
                righties.append(host)
        if host in lefties and host in righties:
            dualarm.append(host)
            lefties.remove(host)
            righties.remove(host)
    
    print("dualarm:\n",dualarm,"\n")
    print("lefties:\n",lefties,"\n")
    print("righties:\n",righties,"\n")

def run_collective():
    tasks = {"collective-001":{"left":["insertable_left"], "right":["insertable_right"]}
    #...
    }
    tags = ["AI.BAY","demo"]
    threads = []
    for host in tasks.keys():
        knowledge_source = Knowledge()
        knowledge_source.kb_location = "collective-dev-001"
        knowledge_source.mode = "global"
        knowledge_source.scope = []
        knowledge_source.scope.extend(tags)
        knowledge_source.scope.append("n"+str(n_current_iter+1))
        knowledge_source.type = "all"
        learn_insertion(host, tasks[host]["left"]+"approach", tasks[host]["left"], tasks[host]["left"]+"container",tags,None,False,1,8000)
        learn_insertion(host, tasks[host]["right"]+"approach", tasks[host]["right"], tasks[host]["right"]+"container",tags,None,False,1,9000)





