import sys
import logging
from utils.udp_client import call_method
from interface.interface import Interface
from knowledge_processor.knowledge_processor import KnowledgeProcessor
from utils.udp_client import call_method
from definitions import *
from services.cmaes import *


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


def get_knowledge(result_tags, knowledge_tags):
    k = KnowledgeProcessor()
    k.process_knowledge({"meta.tags": result_tags})
    print("knowledge processed.")
    return k.get_knowledge({"meta.tags": problem_def.task_type}, "test_knowledge", problem_def.task_type)


def start_learning(agent, problem_definition, knowledge=None, tags=None):
    if tags is None:
        tags = []
    agents = set()
    agents.add(agent)
    interface = Interface()
    for t in tags:
        problem_definition.tags.append(t)

    # learning without knowledge
    uuid = interface.start_service(problem_definition, get_service_configuration(), agents, knowledge)


def test_single_task(host):
    start_learning(host, rastrigin())


def test_task_sequence(host):
    start_learning(host, rastrigin(), None, ["test_sequence_1"])
    k1 = get_knowledge(["test_sequence_1"], ["test_sequence_1"])
    start_learning(host, rastrigin(), k1, ["test_sequence_2"])
    k2 = get_knowledge(["test_sequence_2"], ["test_sequence_2"])
    start_learning(host, rastrigin(), k2, ["test_sequence_3"])