import logging
import time
import sys
from knowledge_processor.knowledge_processor import KnowledgeProcessor
from services.basinhopping import BasinhoppingService
from services.cmaes import *
from interface.interface import Interface
from services.generic_optimizer import *
from problem_definition.problem_definition import ProblemDefinition
from problem_definition.domain import Domain
from utils.udp_client import call_method
from definitions import *


logger = logging.getLogger("ml_service")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)





def get_service_configuration():
    configuration = CMAESConfiguration()
    configuration.n_ind = 5
    configuration.n_gen = 5
    return configuration


def test_mios(agent: str = "localhost"):
    agents = set()
    agents.add(agent)

    pd = rastrigin()

    payload = {
        "problem_definition": {
            "domain": {
                "limits": pd.domain.limits,
                "context_mapping": pd.domain.context_mapping
            }
        },
        "service_configuration": {
            "service_name": "cmaes",
            "tol": 1e-5
        },
        "agents": list(agents)
    }

    response = call_method(agent, 12002, "learn_task", payload)
    print(response)


def test_interface(agent: str = "localhost"):
    agents = set()
    agents.add(agent)
    problem_def = rastrigin()
  
    knowledge = None

    interface = Interface()

    #learning without knowledge
    uuid = interface.start_service(problem_def, get_service_configuration(), agents, knowledge)
    input("Press enter to stop service.")
    interface.stop_service()
    return
    time.sleep(2)
    while interface.is_busy():
        time.sleep(2)
        print("wainting for 1st task to finish...")
    interface.stop_service()

    #extracting knowledge
    k = KnowledgeProcessor()
    k.process_knowledge({"meta.uuid":uuid},"ml_results",problem_def.task_type,"test_knowledge",problem_def.task_type)
    print("knowledge processed.")
    time.sleep(3)
    knowledge = k.get_knowledge({"meta.task_type":problem_def.task_type},"test_knowledge",problem_def.task_type)
    print("knowledge:  ",knowledge)
    #learning with knowledge
    uuid = interface.start_service(problem_def, get_service_configuration(), agents, knowledge)
    input("Press enter to stop service.")
    interface.stop_service()


def test_standalone(agent: str = "localhost"):
    agents = set()
    agents.add(agent)
    learner = GenericOptimizerService()
    learner.initialize(rastrigin(), get_service_configuration(), agents)
    learner.learn_task()
