from xmlrpc.client import ServerProxy
import copy
import time

from utils.database import backup_result
from problem_definition.problem_definition import ProblemDefinition
from services.base_service import ServiceConfiguration
from mongodb_client.mongodb_client import MongoDBClient


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
        print("starting with ", problem_def.tags)
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
                     tags: list = None, knowledge: dict = None, keep_record: bool = True, wait: bool = True, service_port:int = 8000):
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
    s = ServerProxy("http://" + learner + ":"+str(service_port), allow_none=True)
    if knowledge_tmp is not None:
        #if "scope" not in knowledge_tmp:
        #    knowledge_tmp["scope"] = []
        #if "n" + str(iter) in knowledge_tmp["scope"]:
        #    knowledge_tmp["scope"].remove("n" + str(iter))
        #knowledge_tmp["scope"].append("n" + str(iter+1))
        print(knowledge_tmp)
    print("start task on ", agents, " with knowledge scope = ",knowledge_tmp["meta"]["scope"])
    uuid = s.start_service(problem_def.to_dict(), service.to_dict(), agents, knowledge_tmp)
    if wait:
        while s.is_busy():
            time.sleep(15)
    
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
