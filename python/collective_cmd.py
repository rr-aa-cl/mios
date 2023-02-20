from desk.mongodb_client import MongoDBClient
import pymongo
from xmlrpc.client import ServerProxy
import os
from threading import Thread
from utils.ws_client import *

import time
import copy
hostnames = [
"10.157.175.221",  #0 ms            collective-001.local    [n/a]           A8:A1:59:B8:22:8B                   [n/a]                               ASRock Incorporation                      
"10.157.174.166",  #0 ms            collective-002.local    [n/a]           A8:A1:59:B8:25:9A                   [n/a]                               ASRock Incorporation                      
"10.157.174.167",  #0 ms            collective-003.local    [n/a]           A8:A1:59:B8:24:E8                   [n/a]                               ASRock Incorporation                      
"10.157.174.168",  #0 ms            collective-004.local    [n/a]           A8:A1:59:B8:25:EC                   [n/a]                               ASRock Incorporation                      
"10.157.174.89" ,  #0 ms            collective-005.local    [n/a]           A8:A1:59:B8:23:72                   [n/a]                               ASRock Incorporation                      
"10.157.174.80" ,  #0 ms            collective-006.local    [n/a]           A8:A1:59:B8:23:74                   [n/a]                               ASRock Incorporation                      
"10.157.174.200",  #0 ms            collective-007.local    [n/a]           A8:A1:59:B2:B1:6E                   [n/a]                               ASRock Incorporation                      
"10.157.175.129",  #0 ms            collective-008.local    [n/a]           A8:A1:59:B8:22:F4                   [n/a]                               ASRock Incorporation                      
"10.157.174.36" ,  #0 ms            collective-009.local    [n/a]           A8:A1:59:B8:25:BD                   [n/a]                               ASRock Incorporation                      
"10.157.175.87",  #0 ms            collective-011.local    [n/a]           A8:A1:59:B8:23:62                   [n/a]                               ASRock Incorporation                      
"10.157.174.241",  #0 ms            collective-012.local    [n/a]           A8:A1:59:B8:25:DF                   [n/a]                               ASRock Incorporation                      
"10.157.174.201",  #0 ms            collective-013.local    [n/a]           A8:A1:59:B2:BF:1F                   [n/a]                               ASRock Incorporation                      
"10.157.174.247",  #0 ms            collective-014.local    [n/a]           A8:A1:59:B2:1C:28                   [n/a]                               ASRock Incorporation                      
"10.157.174.202",  #0 ms            collective-015.local    [n/a]           A8:A1:59:B8:23:38                   [n/a]                               ASRock Incorporation                      
"10.157.174.203",  #0 ms            collective-016.local    [n/a]           A8:A1:59:B2:B2:E4                   [n/a]                               ASRock Incorporation                      
"10.157.174.46",  #0 ms            collective-017.local    [n/a]           A8:A1:59:B8:24:CF                   [n/a]                               ASRock Incorporation                      
"10.157.174.103",  #0 ms            collective-018.local    [n/a]           A8:A1:59:B8:23:1E                   [n/a]                               ASRock Incorporation                      
"10.157.174.206",  #0 ms            collective-019.local    [n/a]           A8:A1:59:B8:22:E2                   [n/a]                               ASRock Incorporation                      
"10.157.174.204",  #0 ms            collective-020.local    [n/a]           A8:A1:59:B8:22:AE                   [n/a]                               ASRock Incorporation                      
"10.157.175.173",  #0 ms            collective-021.local    [n/a]           A8:A1:59:B8:24:C9                   [n/a]                               ASRock Incorporation                      
"10.157.174.244",  #0 ms            collective-022.local    [n/a]           A8:A1:59:B8:24:E6                   [n/a]                               ASRock Incorporation                      
"10.157.174.205",  #0 ms            collective-023.local    [n/a]           A8:A1:59:B8:26:4D                   [n/a]                               ASRock Incorporation                      
"10.157.175.156",  #0 ms            collective-024.local    [n/a]           A8:A1:59:B8:23:5A                   [n/a]                               ASRock Incorporation                      
"10.157.174.186",  #0 ms            collective-025.local    [n/a]           A8:A1:59:B8:25:D5                   [n/a]                               ASRock Incorporation                      
"10.157.174.245",  #0 ms            collective-026.local    [n/a]           A8:A1:59:B2:1C:7A                   [n/a]                               ASRock Incorporation                      
"10.157.174.249",  #0 ms            collective-027.local    [n/a]           A8:A1:59:B8:23:B9                   [n/a]                               ASRock Incorporation                      
"10.157.174.255",  #0 ms            collective-028.local    [n/a]           A8:A1:59:B2:AE:FF                   [n/a]                               ASRock Incorporation                      
"10.157.174.42" ,  #0 ms            collective-029.local    [n/a]           A8:A1:59:B2:AD:9A                   [n/a]                               ASRock Incorporation                      
"10.157.174.163",  #0 ms            collective-038.local    [n/a]           A8:A1:59:B8:23:9F                   [n/a]                               ASRock Incorporation                      
"10.157.174.175",  #0 ms            collective-039.local    [n/a]           A8:A1:59:B8:25:70                   [n/a]                               ASRock Incorporation                      
"10.157.174.52" ,  #0 ms            collective-046.local    [n/a]           A8:A1:59:B8:23:A5                   [n/a]                               ASRock Incorporation                      
"10.157.175.134"]  #0 ms            collective-050.local    [n/a]           A8:A1:59:B2:0F:85                   [n/a]                               ASRock Incorporation 
#hostnames = ["collective-%03d.rsi.ei.tum.de"%n for n in range(1,50)]

#hostnames = ["collective-%03d.local"%n for n in range(1,50)]
#hostnames.remove("collective-001.rsi.ei.tum.de")
#hostnames.remove("collective-002.rsi.ei.tum.de")
#hostnames.remove("collective-007.rsi.ei.tum.de")
#hostnames.remove("collective-012.rsi.ei.tum.de")
#hostnames.remove("collective-016.rsi.ei.tum.de")
#hostnames.remove("collective-017.rsi.ei.tum.de")
#hostnames.remove("collective-018.rsi.ei.tum.de")
#hostnames.remove("collective-020.rsi.ei.tum.de")

#for host in hostnames:
#    if host.find("010") != -1:
#        hostnames.remove(host)
#hostnames.remove("collective-010.rsi.ei.tum.de")

print(hostnames)


class Task:
    def __init__(self, robot, port=12000):
        self.skill_names = []
        self.skill_types = []
        self.skill_context = dict()
        self.context = {
            "parameters": {
                "skill_names": [],
                "skill_types": [],
                "as_queue": False
            },
            "skills": self.skill_context
        }

        self.robot = robot
        self.port = port
        self.task_uuid = "INVALID"
        self.t_0 = 0

    def add_skill(self, name, skill_class, context):
        self.skill_names.append(name)
        self.skill_types.append(skill_class)
        self.skill_context[name] = context

        self.context["parameters"]["skill_names"] = self.skill_names
        self.context["parameters"]["skill_types"] = self.skill_types
        self.context["skills"] = self.skill_context

    def start(self, queue: bool = False):
        self.t_0 = time.time()
        self.context["parameters"]["as_queue"] = queue
        response = start_task(self.robot, "GenericTask", parameters=self.context, port=self.port)
        self.task_uuid = response["result"]["task_uuid"]

    def wait(self):
        result = wait_for_task(self.robot, self.task_uuid, port=self.port)
        #print("Task execution took " + str(time.time() - self.t_0) + " s.")
        return result

    def stop(self):
        result = stop_task(self.robot, port=self.port)
        #print("Task execution took " + str(time.time() - self.t_0) + " s.")
        return result


def get_ip(hostname: str):
    print("hostname: ",hostname)
    return socket.gethostbyname(hostname)

def populate_database(host, db, ip, user_name="franka", user_pw="frankaRSI"):
    try:
        client = MongoDBClient(host)
        new_params = {"desk_name":user_name, "desk_pwd":user_pw,"robot_ip":ip, "spoc_token":"","spoc_in_control":False}
        client.update(db,"parameters",{"name":"system"}, new_params)
        print("updated ", host,": ",db)
    except:
            print(host, " not updated")
def populate_databases(db, ip, user_name="franka", user_pw="frankaRSI"):
    for host in hostnames:
        populate_database(host,db,ip,user_name,user_pw)

def populate_all():
    threads = []
    for host in hostnames:
        threads.append(Thread(target=populate_database, args=(host,"miosL","192.168.3.100","franka","frankaRSI",)))
        threads[-1].start()
        threads.append(Thread(target=populate_database, args=(host,"miosR","192.168.4.100","franka","frankaRSI",)))
        threads[-1].start()
    
    for t in threads:
        t.join()

def command_collective(cmd: str, args: dict = {}):
    threads = []
    for r in hostnames:
        robot = r
        threads.append(Thread(target=call_method, args=(robot, 12000, cmd, args,)))
        threads.append(Thread(target=call_method, args=(robot, 13000, cmd, args,)))
        threads[-2].start()
        threads[-1].start()

    for t in threads:
        t.join()

def copy_object(source:str, destinations:list, object_name:str, robot_arm="left"):
    def _send_object(destination, db, collection, document):
        if "_id" in document:
            document.pop("_id")
        client = MongoDBClient(destination)
        if len(client.read(db, collection, {"name": document["name"]})):
            client.remove(db, collection, {"name":document["name"]})
        client.write(db, collection, document)
    if destinations == "all":
        destinations = hostnames
        if source in destinations:
            destinations.remove(source)
    client = MongoDBClient(source)
    obj = None
    if robot_arm == "left":
        obj = client.read("miosL","environment",{"name":object_name})
    else:
        obj = client.read("miosR","environment",{"name":object_name})
    if len(obj) != 1:
        print("Failure: Found ", len(obj), " objects on ", source, " with name ", object_name)
        return "error"
    else:
        obj = obj[0]
    threads = []
    for destination in destinations:
        if robot_arm == "left":
            threads.append(Thread(target=_send_object, args=(destination, "miosL", "environment", obj)))
        else:
            threads.append(Thread(target=_send_object, args=(destination, "miosR", "environment", obj)))
        threads[-1].start()
    for t in threads:
        t.join()
    print("sending completed. Restart cluster!")

def move(robot, location, offset, port=12000, wait = True):
    context = {
        "skill": {
            "p0":{
                "dX_d": [0.1, 0.5],
                "ddX_d": [0.5, 1],
                "K_x": [2000, 2000, 2000, 250, 250, 250],
                "T_T_EE_g_offset": [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, offset[0], offset[1], offset[2], 1]

            },
            "time_max":10,
            "objects": {
                    "GoalPose": location
                }
        },
        "control": {
            "control_mode": 2
        }
    }
    t = Task(robot, port=port)
    t.add_skill("move", "TaxMove", context)
    t.start()
    if wait:
        return t.wait()

    #print("Result: " + str(result))

def move_joint(robot, location,port=12000, wait=True):
    path_to_default_context = os.getcwd() + "/taxonomy/default_contexts/"
    f = open(path_to_default_context + "move_joint.json")
    move_context = json.load(f)
    move_context["skill"]["objects"]["goal_pose"] = location
    move_context["skill"]["time_max"] = 10
    t0 = Task(robot, port=port)
    t0.add_skill("move", "MoveToPoseJoint", move_context)
    t0.start()
    if wait:
        return t0.wait()

def move_all(pose = "default_pose"):
    threads = []
    for host in hostnames:
        threads.append(Thread(target=move_joint, args=(host, pose, 12000, True)))
        threads[-1].start()
        threads.append(Thread(target=move_joint, args=(host, pose, 13000, True)))
        threads[-1].start()
    for t in threads:
        t.join()
    print("finished")

def demo_part_left(master="008",wait=True):
    robots = copy.deepcopy(hostnames)
    for host in robots:
        stop_task(host)
    for host in robots:
        if host.find(master) != -1:
            master = host
            break
    robots.remove(master)
    print("master is ", master)
    master = get_ip(master)
    result_left = start_task(master, "MoveToJointPose", {
        "parameters": {
            "pose": "default_pose",
            "speed": 1,
            "acc": 2
        }
    })
    result_left = wait_for_task(master, result_left["result"]["task_uuid"])
    if not result_left["result"]["task_result"]["success"]:
        print("master could not move to default pose")
        return "error"


    ip_slaves = []
    threads = []
    for i in range(0, len(robots)):
        ip_slaves.append(get_ip(robots[i]))
        threads.append(Thread(target=start_task_and_wait, args=(ip_slaves[-1], "MoveToJointPose",{
        "parameters": {
            "pose": "default_pose",
            "speed": 1,
            "acc": 2
        }
        })))
        threads[-1].start()
    for t in threads:
        t.join()
    time.sleep(2)

    print(ip_slaves)

    telepresence_master_context_left = {
        "skill": {
            "is_master": True,
            "ip_dst": "0.0.0.0",
            "port_dst": 8888,
            "port_src": 8888,
            "telepresence_mode": "DirectJoint",
            "multicast": True,
            "multicast_group": ip_slaves,
            "multicast_ip":"225.0.0.1",
            "host": master,
            "direct_joint": {
                "alpha": [15, 15, 10, 10, 8, 6, 3]#[0, 0, 0, 0, 0, 0, 0]
            }
        },
        "control": {
            "control_mode": 1
        }
    }
    telepresence_slave_context_left = {
        "skill": {
            "is_master": False,
            "ip_dst": "0.0.0.0",
            "port_dst": 8888,
            "port_src": 8888,
            "telepresence_mode": "DirectJoint",
            "multicast": True,
            "multicast_ip":"225.0.0.1",
            "direct_joint": {
                "alpha": [0, 0, 0, 0, 0, 0, 0]
            }
        },
        "control": {
            "control_mode": 1,
            "joint_imp": {
                "K_theta": [1500,1200,800,600,300,200,50]
            }
        }
    }
    print(telepresence_master_context_left)
    t_left = Task(master)
    t_left.add_skill("telepresence", "Telepresence", telepresence_master_context_left)
    t_left.start()
    for i in range(0, len(robots)):
        try:
            t_left = Task(robots[i])
            telepresence_slave_context_left["skill"]["host"] = robots[i]
            t_left.add_skill("telepresence", "Telepresence", telepresence_slave_context_left)
            print(robots[i])
            t_left.start()
        except TypeError:
            print(robots[i], " is not working.")
            pass
    if wait:
        input("Press key to stop.")
        for ip in ip_slaves:
            stop_task(ip)

        stop_task(master)

def demo_part_right(master = "008", wait = True):
    robots = copy.deepcopy(hostnames)
    for host in robots:
        stop_task(host,port=13000)
    for host in robots:
        if host.find(master) != -1:
            master = host
            break
    robots.remove(master)
    print("master is ", master)
    master = get_ip(master)
    result_right = start_task(master, "MoveToJointPose", {
        "parameters": {
            "pose": "beer",
            "speed": 1,
            "acc": 2
        }
    },port=13000)
    result_right = wait_for_task(master, result_right["result"]["task_uuid"],port=13000)
    if not result_right["result"]["task_result"]["success"]:
        print(result_right)
        print("master could not move to default pose")
        return "error"


    ip_slaves = []
    threads = []
    for i in range(0, len(robots)):
        ip_slaves.append(get_ip(robots[i]))
        threads.append(Thread(target=start_task_and_wait, args=(ip_slaves[-1], "MoveToJointPose",{
        "parameters": {
            "pose": "beer",
            "speed": 1,
            "acc": 2
        }
        }),kwargs={"port":13000}))
        threads[-1].start()
    for t in threads:
        t.join()
    time.sleep(2)

    print(ip_slaves)

    telepresence_master_context_right = {
        "skill": {
            "is_master": True,
            "ip_dst": "0.0.0.0",
            "port_dst": 8886,
            "port_src": 8886,
            "telepresence_mode": "DirectJoint",
            "multicast": True,
            "multicast_group": ip_slaves,
            "multicast_ip":"225.0.0.3",
            "remote_event_port":13000,
            "host": master,
            "direct_joint": {
                "alpha": [15, 15, 10, 10, 8, 6, 3]#[0, 0, 0, 0, 0, 0, 0]
            }
        },
        "control": {
            "control_mode": 1
        }
    }
    telepresence_slave_context_right = {
        "skill": {
            "is_master": False,
            "ip_dst": "0.0.0.0",
            "port_dst": 8886,
            "port_src": 8886,
            "telepresence_mode": "DirectJoint",
            "multicast": True,
            "multicast_ip":"225.0.0.3",
            "remote_event_port":13000,
            "direct_joint": {
                "alpha": [0, 0, 0, 0, 0, 0, 0]
            }
        },
        "control": {
            "control_mode": 1,
            "joint_imp": {
                "K_theta": [1500,1200,800,600,300,200,50]
            }
        }
    }
    print(telepresence_master_context_right)
    t_right = Task(master,13000)
    t_right.add_skill("telepresence","Telepresence", telepresence_master_context_right)
    t_right.start()
    for i in range(0, len(robots)):
        try:
            t_right = Task(robots[i],13000)
            telepresence_slave_context_right["skill"]["host"] = robots[i]
            t_right.add_skill("telepresence", "Telepresence", telepresence_slave_context_right)
            print(robots[i])
            t_right.start()
        except TypeError:
            print(robots[i], " is not working.")
            pass

    if wait:
        input("Press key to stop.")
        for ip in ip_slaves:
            stop_task(ip,port=13000)

        stop_task(master,port=13000)

def teleop_dualarm(master = "008"):
    demo_part_left(master,wait=False)
    demo_part_right(master,wait=False)
    input("Press Key to stop")
    threads = []
    for ip in hostnames:
        if master in ip:
            continue
        threads.append(Thread(target=stop_task, args=(ip,),kwargs={"port":13000}))
        threads[-1].start()
        threads.append(Thread(target=stop_task, args=(ip,),kwargs={"port":12000}))
        threads[-1].start()
    
    stop_task(master,port=13000)
    stop_task(master,port=12000)

def direct_joint_mode(master: str, slave: str):
    master_context = {
        "skill": {
            "is_master": True,
            "ip_dst": get_ip(slave),
            "port_dst": 8888,
            "port_src": 8888,
            "telepresence_mode": "DirectJoint",
            "direct_joint": {
                "alpha": [15, 15, 10, 10, 8, 6, 3]
            }
        },
        "control": {
            "control_mode": 1
        }
    }
    slave_context = {
        "skill": {
            "is_master": False,
            "ip_dst": get_ip(master),
            "port_dst": 8888,
            "port_src": 8888,
            "telepresence_mode": "DirectJoint",
            "direct_joint": {
                "alpha": [0, 0, 0, 0, 0, 0, 0]
            }
        },
        "control": {
            "control_mode": 1,
            "joint_imp": {
                "K_theta": [1500,1200,800,600,300,200,50]
            }
        }
    }
    t_m = Task(master)
    t_s = Task(slave)
    t_m.add_skill("telepresence", "Telepresence", master_context)
    t_s.add_skill("telepresence", "Telepresence", slave_context)

    t_m.start()
    t_s.start()
    input("Press Enter to stop...")
    t_m.stop()
    t_s.stop()


def restart_collective():
    client =ServerProxy("http://collective-009.rsi.ei.tum.de:"+str(8008), allow_none=True)
    client.reboot_robots()

def get_status():
    for number,host in enumerate(hostnames):
        print("\ncollective-%03d"%(number+1))
        result = call_method(host,12000,"get_state")
        if result is not None:
            if result["result"]["current_task"] == "IdleTask":
                if result["result"]["status"] == "Idle":
                    print(host," -left- everything is good.")
                elif result["result"]["status"] == "Reflex":
                    print(host," -left- Non-upright-mounting Reflex.")
                else:
                    print(host, " -left- unknown status")
            else:
                print(host, " -left- Not in IdleTask")
        else:
            print(host, " -left- Not reachable!")

        result = call_method(host,13000,"get_state")
        if result is not None:
            if result["result"]["current_task"] == "IdleTask":
                if result["result"]["status"] == "Idle":
                    print(host," -right- everything is good.")
                elif result["result"]["status"] == "Reflex":
                    print(host," -right- Non-upright-mounting Reflex.")
                else:
                    print(host, " -right- unknown status")
            else:
                print(host, " -right- Not in IdleTask")
        else:
            print(host, " -right- Not reachable!")


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


        
    