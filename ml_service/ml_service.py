import logging
import sys
from services.basinhopping import BasinhoppingService
from services.cmaes import *
from services.generic_optimizer import *
from problem_definition.problem_definition import ProblemDefinition
from problem_definition.domain import Domain
from utils.udp_client import call_method


logger = logging.getLogger("ml_service")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)


def get_problem_definition_rastrigin():
    limits = {
        "x1": (-5.12, 5.12),
        "x2": (-5.12, 5.12),
        "x3": (-5.12, 5.12),
        "x4": (-5.12, 5.12),
        "x5": (-5.12, 5.12),
        "x6": (-5.12, 5.12)
    }
    context_mapping = {
        "x1": ["parameters.x-1"],
        "x2": ["parameters.x-2"],
        "x3": ["parameters.x-3"],
        "x4": ["parameters.x-4"],
        "x5": ["parameters.x-5"],
        "x6": ["parameters.x-6"]
    }
    domain = Domain(limits, context_mapping)
    default_context = {
        "name": "LearnerTest"
    }
    pd = ProblemDefinition(domain, default_context, [], [], [])
    return pd

def get_service_configuration():
    configuration = GenericOptimizerConfiguration()
    return configuration


def test_mios(agent: str = "localhost"):
    agents = set()
    agents.add(agent)

    pd = get_problem_definition_rastrigin()

    payload = {
        "problem_definition": {
            "domain": {
                "limits": pd.domain.limits,
                "context_mapping": pd.domain.context_mapping
            }
        },
        "service_configuration": {
            "tol": 1e-5
        },
        "agents": list(agents)
    }

    response = call_method(agent, 12002, "learn_task", payload)
    print(response)


def test_standalone(agent: str = "localhost"):
    agents = set()
    agents.add(agent)
    learner = GenericOptimizerService()
    learner.initialize(get_problem_definition_rastrigin(), get_service_configuration(), agent)
    learner.learn_task()
