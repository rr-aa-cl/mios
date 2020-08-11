import logging
import sys
from services.basinhopping import BasinhoppingService
from problem_definition.problem_definition import ProblemDefinition
from problem_definition.domain import Domain


if __name__ == '__main__':

    logger = logging.getLogger("ml_service")
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)


    agents = set()
    agents.add("localhost")

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

    learner = BasinhoppingService()
    learner.initialize(pd, agents)
    learner.learn_task()
