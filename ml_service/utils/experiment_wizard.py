from xmlrpc.client import ServerProxy

from definitions.insertion_definitions import *
from problem_definition.problem_definition import ProblemDefinition
from services.base_service import ServiceConfiguration


def start_experiment(agent: str, pd: ProblemDefinition, service: ServiceConfiguration, n_eval: int = 1,
                     tags: list = None):
    if tags is None:
        tags = []

    agents = [agent]
    problem_def = pd
    problem_def.tags.extend(tags)

    for i in range(n_eval):
        if "n" + str(i) in problem_def.tags:
            problem_def.tags.remove("n" + str(i))
        problem_def.tags.append("n" + str(i+1))
        s = ServerProxy("http://" + agent + ":8000", allow_none=True)
        s.start_service(problem_def.to_dict(), service.to_dict(), agents, None)
        s.wait_for_service()
