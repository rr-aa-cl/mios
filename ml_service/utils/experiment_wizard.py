from xmlrpc.client import ServerProxy

from definitions.insertion_definitions import *
from utils.database import backup_result
from problem_definition.problem_definition import ProblemDefinition
from services.base_service import ServiceConfiguration
from mongodb_client.mongodb_client import MongoDBClient


def start_experiment(learner: str, agents: list, pd: ProblemDefinition, service: ServiceConfiguration, n_eval: int = 1,
                     tags: list = None, knowledge: dict = None, keep_record: bool = True):
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
        if keep_record is True and len(client.read("ml_results", problem_def.task_type, {"meta.tags": {"$all": problem_def.tags}})) != 0:
            print("Continue at n" + str(i+1))
            continue
        s = ServerProxy("http://" + learner + ":8000", allow_none=True)
        if knowledge is not None:
            if "n" + str(i) in knowledge["kb_tags"]:
                knowledge["kb_tags"].remove("n" + str(i))
            knowledge["kb_tags"].append("n" + str(i+1))
        uuid = s.start_service(problem_def.to_dict(), service.to_dict(), agents, knowledge)
        s.wait_for_service()
        # backup_result(agent, "collective-control-001.local", problem_def.task_type, uuid)
