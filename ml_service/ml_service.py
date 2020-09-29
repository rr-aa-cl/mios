import logging
import time
import sys
from knowledge_processor.knowledge_processor import KnowledgeProcessor
from services.basinhopping import BasinhoppingService
from services.cmaes import *
from interface.interface import Interface
from services.generic_optimizer import *
from utils.udp_client import call_method
from definitions import *
from xmlrpc.client import ServerProxy
from task_scheduler.creation_pipeline import CreationPipeline
from definitions import *
from task_scheduler.task_scheduler import TaskScheduler
from task_scheduler.creation_pipeline import CreationPipeline


logger = logging.getLogger("ml_service")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)


def get_service_configuration():
    configuration = CMAESConfiguration()
    configuration.n_ind = 3
    configuration.n_gen = 2
    return configuration


def test_mios(agent: str = "localhost"):
    agents = set()
    agents.add(agent)

    pd = rastrigin()

    payload = {
        "problem_definition": pd.to_dict(),
        "service_configuration": get_service_configuration().to_dict(),
        "agents": list(agents)
    }

    response = call_method(agent, 12002, "learn_task", payload)
    print(response)


def test_interface(agent: str = "localhost"):
    agents = set()
    agents.add(agent)
    problem_def = rastrigin()
    interface = Interface()

    uuid = interface.start_service(problem_def, get_service_configuration(), agents)
    input("Press enter to stop service.")
    interface.stop_service()


def test_with_rpc_server():
    i = Interface()
    i.start_rpc_server(8000)


def test_with_rpc_client(agent: str = "localhost"):
    agents = []
    agents.append(agent)
    problem_def = insert_cylinder_30()

    print(problem_def.to_dict())

    s = ServerProxy('http://localhost:8000', allow_none=True)
    s.start_service(problem_def.to_dict(), CMAESConfiguration().to_dict(), agents, None)


def test_standalone(agent: str = "localhost"):
    agents = set()
    agents.add(agent)
    learner = GenericOptimizerService()
    learner.initialize(rastrigin(), get_service_configuration(), agents)
    learner.learn_task()


def test_knowledgeprocessor():
    problem_def = rastrigin()

    uuid = "bc7b9ac6-9084-4984-bc98-8c6f4d34a8e2"

    k = KnowledgeProcessor()
    id = k.process_knowledge({"meta.uuid":uuid},"ml_results",problem_def.task_type,"test_knowledge",problem_def.task_type)
    print(k.get_knowledge({"_id":id},"test_knowledge",problem_def.task_type))


def test_task_scheduler():
    t = TaskScheduler()
    c = CreationPipeline()
    c.create_tasks_from_template(rastrigin(), get_service_configuration(), 10, "http://localhost:8000", ["localhost"], "none")
    for task in c.tasks:
        t.add_task(task)

    t.solve_tasks()


def test_server_connection(host):
    s = ServerProxy(host)
    print(s.is_busy())