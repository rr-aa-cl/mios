"""
conftest.py – shared fixtures for the MIOS ml_service test suite.

All fixtures here are usable without a live robot, MongoDB, or Redis.
Hardware-dependent tests must be decorated with @pytest.mark.integration
and live in tests/integration/.
"""
import sys
import os
import pytest
import mongomock

# ---------------------------------------------------------------------------
# Make ml_service importable from tests/ without installation
# ---------------------------------------------------------------------------
ML_SERVICE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ML_SERVICE_ROOT not in sys.path:
    sys.path.insert(0, ML_SERVICE_ROOT)


# ---------------------------------------------------------------------------
# mongomock client fixture
# ---------------------------------------------------------------------------
@pytest.fixture()
def mongo_client():
    """Return a mongomock MongoClient (in-memory, no real Mongo required)."""
    return mongomock.MongoClient()


@pytest.fixture()
def mios_mongo_client(mongo_client):
    """
    Return a MongoDBClient wrapper backed by mongomock.
    Patches MongoDBClient so no real MongoDB connection is attempted.
    """
    from mongodb_client.mongodb_client import MongoDBClient
    client = MongoDBClient.__new__(MongoDBClient)
    client.client = mongo_client
    client.max_retry = 3
    return client


# ---------------------------------------------------------------------------
# Minimal Domain fixture (2-parameter insertion-like domain)
# ---------------------------------------------------------------------------
@pytest.fixture()
def simple_domain():
    from problem_definition.domain import Domain
    limits = {
        "p_x": (-0.005, 0.005),
        "p_y": (-0.005, 0.005),
    }
    mapping = {
        "p_x": ["skills.insertion.skill.p0.DeltaX-1"],
        "p_y": ["skills.insertion.skill.p0.DeltaX-2"],
    }
    x_0 = {"p_x": 0.5, "p_y": 0.5}
    return Domain(limits, mapping, x_0)


# ---------------------------------------------------------------------------
# Minimal ProblemDefinition fixture
# ---------------------------------------------------------------------------
@pytest.fixture()
def simple_problem_definition(simple_domain):
    from problem_definition.problem_definition import ProblemDefinition, CostFunction
    cf = CostFunction()
    cf.optimum_skills = ["insertion"]
    cf.optimum_weights = {"success": 1.0, "time": 0.0, "contact_forces": 0.0, "heuristic": 0.0}
    cf.optimum_expressions = {k: "var" for k in cf.optimum_weights}
    cf.max_cost = {k: 1.0 for k in cf.optimum_weights}
    cf.heuristic_expressions = "var"
    cf.finish_thr = 3

    default_context = {
        "name": "GenericTask",
        "parameters": {"skill_types": ["TaxInsertion"], "skill_names": ["insertion"]},
        "skills": {
            "insertion": {
                "skill": {"p0": {"DeltaX": [0, 0, 0, 0, 0, 0]}},
                "control": {"control_mode": 2},
                "user": {}
            }
        }
    }
    pd = ProblemDefinition(
        skill_class="insertion",
        skill_instance="cylinder_40",
        domain=simple_domain,
        default_context=default_context,
        setup_instructions=[{"method": "start_task", "parameters": {"name": "GenericTask", "skills": {}, "parameters": {}}}],
        termination_instructions=[],
        reset_instructions=[{"method": "start_task", "parameters": {"name": "GenericTask", "skills": {}, "parameters": {}}}],
        rescue_instructions=[{"method": "start_task", "parameters": {"name": "GenericTask", "skills": {}, "parameters": {}}}],
        cost_function=cf,
        identity=[1],
        tags=["test", "cylinder_40"],
    )
    return pd


# ---------------------------------------------------------------------------
# Minimal Knowledge fixture
# ---------------------------------------------------------------------------
@pytest.fixture()
def simple_knowledge():
    from services.knowledge import Knowledge
    k = Knowledge(
        mode=None,
        type="similar",
        scope=[],
        kb_location=None,
        parameters=None,
    )
    return k


# ---------------------------------------------------------------------------
# Mock WebSocket agent (returns a canned success response)
# ---------------------------------------------------------------------------
@pytest.fixture()
def mock_ws_response():
    """A dict that looks like a successful mios response."""
    return {
        "result": {
            "result": True,
            "task_uuid": "test-uuid-1234",
            "task_result": {
                "success": True,
                "time": 2.5,
                "contact_forces": 10.0,
                "heuristic": 0.0,
                "error_codes": [],
            },
            "error": ""
        }
    }
