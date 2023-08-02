from xmlrpc.client import ServerProxy
import copy
import time
from threading import Thread
from utils.database import backup_result
from problem_definition.problem_definition import ProblemDefinition
from services.base_service import ServiceConfiguration
from mongodb_client.mongodb_client import MongoDBClient
from utils.ws_client import *
from utils.taxonomy_utils import Task
from utils.helper_functions import *


class DualarmCMD():
    def __init__(self, cmd):
        self.keep_running = False
        self.thread = None
        self.port = None
        self.cmd = cmd
        self.agent = self.cmd["agent"]
        if "sleep" in cmd:
            self.sleep = cmd["sleep"]
        else:
            self.sleep = 5
        if "port" in cmd:
            self.port = cmd["port"]
        else:
            self.port = 13000
        

        self.hold_context = {
                    "skill": {
                        "t_max": self.sleep,},
                    "control": {
                        "control_mode": 0,
                        "cart_imp": {
                            "K_x": [2000, 2000, 2000, 250, 250, 250]}},
                        #"joint_imp":{
                        #    "K_theta":[10000,10000,10000,10000,10000,10000,10000]}},
                    "user": {"F_ext_max": [100, 50]}}
        self.move_context = {
                    "skill": {
                        "speed": 0.5,
                        "acc": 1,
                        "q_g": [0, 0, 0, 0, 0, 0, 0],
                        "objects": {
                            "goal_pose": self.cmd["pose"]}},
                    "control": {
                        "control_mode": 3},
                    "user": {
                        "env_X": [0.001, 0.001, 0.001, 0.001, 0.001, 0.001]}}

    def _execute_loop(self):
        print("execute_loop")
        while(self.keep_running):
            print("sending tasks")
            t = Task(self.agent, self.port)
            t.add_skill("move", "MoveToPoseJoint", self.move_context)
            t.add_skill("hold","HoldPose",self.hold_context)
            t.start(queue=False)
            t.wait()

    def stop(self):
        self.keep_running = False
        call_method(self.agent,self.port,"stop_task")
        self.thread.join()
    def start(self):
        print("start with ", self.cmd)
        self.keep_running = True
        self.thread = Thread(target=self._execute_loop)
        self.thread.start()


def start_experiment(learner: str, agents: list, pd: ProblemDefinition, service: ServiceConfiguration, n_eval: int = 1,
                     tags: list = None, knowledge: dict = None, keep_record: bool = True, wait: bool = True, service_port:int = 8000):
    if tags is None:
        tags = []

    agents = agents
    problem_def = pd
    problem_def.tags.extend(tags)
    client = MongoDBClient(learner)

    for i in range(n_eval):
        if "n" + str(i) in problem_def.tags:
            problem_def.tags.remove("n" + str(i))
        problem_def.tags.append("n" + str(i+1))
        #print("starting with ", problem_def.tags)
        if keep_record is True and len(client.read("ml_results", problem_def.skill_class, {"meta.tags": {"$all": problem_def.tags}})) != 0:
            print("Continue at n" + str(i+1))
            continue
        s = ServerProxy("http://" + learner + ":"+str(service_port), allow_none=True)
        # if knowledge is not None:
        #     if "scope" not in knowledge:
        #         knowledge["scope"] = []
        #     if "n" + str(i) in knowledge["scope"]:
        #         knowledge["scope"].remove("n" + str(i))
        #     knowledge["scope"].append("n" + str(i+1))
        uuid = s.start_service(problem_def.to_dict(), service.to_dict(), agents, knowledge)
        while s.is_busy():
            time.sleep(2)
        #if wait is True:
        #    s.wait_for_service()
        print(problem_def.tags, " finished.")


def start_single_experiment(learner: str, agents: list, pd: ProblemDefinition, service: ServiceConfiguration, iter: int = 1,
                     tags: list = None, knowledge: dict = None, keep_record: bool = True, wait: bool = True, service_port:int = 8000, dualarm_cmd:dict=None):
    if tags is None:
        tags = []

    agents = agents
    problem_def = pd
    problem_def.tags.extend(tags)
    client = MongoDBClient(learner)

    knowledge_tmp = copy.deepcopy(knowledge)

    if "n" + str(iter) in problem_def.tags:
        problem_def.tags.remove("n" + str(iter))
    problem_def.tags.append("n" + str(iter+1))
    if keep_record is True and len(client.read("ml_results", problem_def.skill_class, {"meta.tags": {"$all": problem_def.tags}})) != 0:
        print("Continue at n" + str(iter+1))
        return
    if dualarm_cmd is not None:
        move_joint(dualarm_cmd["agent"],dualarm_cmd["pose"],port=dualarm_cmd["port"],wait=True)
        c = DualarmCMD(dualarm_cmd)
        c.start()

    s = ServerProxy("http://" + learner + ":"+str(service_port), allow_none=True)
    #if knowledge_tmp is not None:
        #if "scope" not in knowledge_tmp:
        #    knowledge_tmp["scope"] = []
        #if "n" + str(iter) in knowledge_tmp["scope"]:
        #    knowledge_tmp["scope"].remove("n" + str(iter))
        #knowledge_tmp["scope"].append("n" + str(iter+1))
        #print(knowledge_tmp)
    #print("start task on ", agents, " with knowledge scope = ",knowledge_tmp["meta"]["scope"])
    uuid = s.start_service(problem_def.to_dict(), service.to_dict(), agents, knowledge_tmp)
    if wait:
        while s.is_busy():
            time.sleep(15)
    c.stop()
    move_joint(dualarm_cmd["agent"],dualarm_cmd["pose"],port=dualarm_cmd["port"],wait=True)
        # backup_result(agent, "collective-control-001.local", problem_def.skill_class, uuid)

def delete_experiment_data(robots: list, tags: list, task_class: str ="insertion", db: str ="ml_results", min_size: int =0, mongo_port=27017):
    for robot in robots:
        mongo_client = MongoDBClient(robot,mongo_port)
        documents = mongo_client.read(db, task_class, {"meta.tags":tags})
        if len(documents) == 0:
            print("Not found documents on ", robot)
        ids = []
        for d in documents:
            if len(d) > min_size:
                ids.append(d["_id"])
        
        for id in ids:
            mongo_client.remove(db, task_class, {"_id":id})
