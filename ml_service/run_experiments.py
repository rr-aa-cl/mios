"""
Backward-compatibility shim for ml_service experiments.
This file re-exports all functions from the new experiments package.
Prefer importing directly from experiments.<domain> in new code.
"""

from experiments.config import *
from experiments.robot_control import *
from experiments.analysis import *
from experiments.insertion import *
from experiments.transfer import *
from experiments.collective import *
from experiments.general_skills import *

# Explicitly re-export some common utilities that were previously in the global namespace
from utils.helper_functions import get_nested_parameter, move_joint, move, grasp_insertable, place_insertable
from mongodb_client.mongodb_client import MongoDBClient
from services.knowledge import Knowledge
from problem_definition.problem_definition import ProblemDefinition
from services.base_service import ServiceConfiguration

def test_learning():
    """Simple test function from original run_experiments.py."""
    from definitions.templates import InsertionFactory
    from definitions.cost_functions import ContactForcesMetric
    from definitions.service_configs import SVMLearner
    
    pd = InsertionFactory("collective-panda-001", ContactForcesMetric("insertion", {"contact_forces": 175}),
                          {"Insertable": "cylinder_40", "Container": "cylinder_40_container",
                           "Approach": "cylinder_40_container_approach"}).get_problem_definition("cylinder_40")
    sc = SVMLearner().get_configuration()
    learn_task("collective-panda-001", pd, sc, ["test_learning"])
