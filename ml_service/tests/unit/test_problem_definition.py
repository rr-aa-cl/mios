"""
test_problem_definition.py – Phase 0 baseline + Phase 5 roundtrip tests.
No hardware or MongoDB required.
"""
import pytest
from problem_definition.problem_definition import ProblemDefinition, CostFunction
from problem_definition.domain import Domain
from engine.task_result import TaskResult, QMetric, cost_types


# ---------------------------------------------------------------------------
# CostFunction
# ---------------------------------------------------------------------------
class TestCostFunction:
    def test_to_dict_roundtrip(self):
        cf = CostFunction()
        cf.optimum_skills = ["insertion"]
        cf.heuristic_expressions = "var * 2"
        cf.finish_thr = 5
        d = cf.to_dict()
        cf2 = CostFunction.from_dict(d)
        assert cf2.optimum_skills == cf.optimum_skills
        assert cf2.heuristic_expressions == cf.heuristic_expressions
        assert cf2.finish_thr == cf.finish_thr

    def test_default_weights_sum_not_necessarily_one(self):
        # Default optimum_weights are all 0 — callers must set them
        cf = CostFunction()
        assert sum(cf.optimum_weights.values()) == 0


# ---------------------------------------------------------------------------
# ProblemDefinition to_dict / from_dict roundtrip
# ---------------------------------------------------------------------------
class TestProblemDefinitionRoundtrip:
    def test_to_dict_contains_required_keys(self, simple_problem_definition):
        pd = simple_problem_definition
        d = pd.to_dict()
        for key in ("domain", "default_context", "setup_instructions", "skill_class",
                    "skill_instance", "tags", "cost_function", "identity"):
            assert key in d, f"Missing key: {key}"

    def test_from_dict_reconstructs_skill_class(self, simple_problem_definition):
        pd = simple_problem_definition
        d = pd.to_dict()
        pd2 = ProblemDefinition.from_dict(d)
        assert pd2.skill_class == pd.skill_class

    def test_from_dict_reconstructs_skill_instance(self, simple_problem_definition):
        pd = simple_problem_definition
        pd2 = ProblemDefinition.from_dict(pd.to_dict())
        assert pd2.skill_instance == pd.skill_instance

    def test_from_dict_reconstructs_tags(self, simple_problem_definition):
        pd = simple_problem_definition
        pd2 = ProblemDefinition.from_dict(pd.to_dict())
        assert pd2.tags == pd.tags

    def test_from_dict_reconstructs_identity(self, simple_problem_definition):
        pd = simple_problem_definition
        pd2 = ProblemDefinition.from_dict(pd.to_dict())
        assert pd2.identity == pd.identity

    def test_from_dict_reconstructs_domain_limits(self, simple_problem_definition):
        pd = simple_problem_definition
        pd2 = ProblemDefinition.from_dict(pd.to_dict())
        assert pd2.domain.limits == pd.domain.limits

    def test_from_dict_reconstructs_cost_function(self, simple_problem_definition):
        pd = simple_problem_definition
        pd2 = ProblemDefinition.from_dict(pd.to_dict())
        assert pd2.cost_function.optimum_skills == pd.cost_function.optimum_skills

    def test_full_roundtrip_idempotent(self, simple_problem_definition):
        """Two roundtrips should produce the same dict."""
        pd = simple_problem_definition
        d1 = pd.to_dict()
        d2 = ProblemDefinition.from_dict(d1).to_dict()
        # Compare key fields (not full dict — uuid is mutable)
        for key in ("skill_class", "skill_instance", "tags", "identity"):
            assert d1[key] == d2[key], f"Mismatch on key: {key}"


# ---------------------------------------------------------------------------
# self_check
# ---------------------------------------------------------------------------
class TestSelfCheck:
    def test_valid_problem_definition_passes(self, simple_problem_definition):
        assert simple_problem_definition.self_check() is True


# ---------------------------------------------------------------------------
# get_identification_name
# ---------------------------------------------------------------------------
class TestIdentificationName:
    def test_identification_name_contains_skill_class(self, simple_problem_definition):
        name = simple_problem_definition.get_identification_name()
        assert "insertion" in name

    def test_identification_name_contains_skill_instance(self, simple_problem_definition):
        name = simple_problem_definition.get_identification_name()
        assert "cylinder_40" in name
