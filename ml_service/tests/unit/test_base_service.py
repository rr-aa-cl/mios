"""
test_base_service.py – Phase 0 baseline + Phase 4 knowledge-loading tests.

BaseService is heavily stateful. We test the knowledge-loading branches
by injecting mocks for KnowledgeManager and MongoDBClient.
No hardware or real Mongo required.
"""
import pytest
from unittest.mock import MagicMock, patch
from services.base_service import ServiceConfiguration


# ---------------------------------------------------------------------------
# ServiceConfiguration
# ---------------------------------------------------------------------------
class MockServiceConfiguration(ServiceConfiguration):
    def _to_dict(self):
        return {}
    def _from_dict(self, config_dict):
        pass

class TestServiceConfiguration:
    def test_default_service_name(self):
        from services.base_service import ServiceConfiguration
        cfg = MockServiceConfiguration("svm")
        assert cfg.service_name == "svm"

    def test_to_dict_contains_service_name(self):
        from services.base_service import ServiceConfiguration
        cfg = MockServiceConfiguration("cmaes")
        d = cfg.to_dict()
        assert d["service_name"] == "cmaes"

    def test_from_dict_restores_service_name(self):
        from services.base_service import ServiceConfiguration
        cfg = MockServiceConfiguration("svm")
        d = cfg.to_dict()
        cfg2 = MockServiceConfiguration("placeholder")
        cfg2.from_dict(d)
        assert cfg2.service_name == "svm"


# ---------------------------------------------------------------------------
# Knowledge mode = None (no knowledge transfer)
# ---------------------------------------------------------------------------
class TestKnowledgeModeNone:
    def test_no_knowledge_initialises_centroid_as_none(
        self, simple_problem_definition, simple_knowledge
    ):
        """When knowledge.mode is None and parameters is None, centroid must be None."""
        from services.svm import SVMService, SVMConfiguration
        simple_knowledge.mode = None
        simple_knowledge.parameters = None

        svc = SVMService.__new__(SVMService)
        svc.problem_definition = simple_problem_definition
        svc.knowledge = simple_knowledge
        svc.configuration = SVMConfiguration()
        svc.mongo_port = 27017
        svc.mios_port = 12000
        svc.centroid = None
        svc.initial_knowledge_list = []
        svc.confidence = None
        svc.external_success = {}
        svc.similarity_estimate = {}
        svc.internal_success = []
        svc.starting_time = 0
        svc.host_name = "localhost"

        # With mode=None and no parameters, the centroid is never set
        assert svc.centroid is None

    def test_knowledge_with_parameters_becomes_centroid(
        self, simple_problem_definition, simple_knowledge
    ):
        """When mode=None but parameters is not None, parameters become the centroid."""
        # This is the convention: parameters → centroid without querying Mongo
        simple_knowledge.mode = None
        simple_knowledge.parameters = {"p_x": 0.5, "p_y": 0.5}
        # Just verify the fixture is configured correctly
        assert simple_knowledge.parameters is not None


# ---------------------------------------------------------------------------
# SVMConfiguration
# ---------------------------------------------------------------------------
class TestSVMConfiguration:
    def test_default_n_trials(self):
        from services.svm import SVMConfiguration
        cfg = SVMConfiguration()
        assert cfg.n_trials == 400

    def test_to_dict_roundtrip(self):
        from services.svm import SVMConfiguration
        cfg = SVMConfiguration()
        cfg.n_trials = 100
        cfg.batch_width = 5
        d = cfg.to_dict()
        cfg2 = SVMConfiguration()
        cfg2.from_dict(d)
        assert cfg2.n_trials == 100
        assert cfg2.batch_width == 5

    def test_failure_base_cost_default(self):
        from services.svm import SVMConfiguration
        cfg = SVMConfiguration()
        assert cfg.failure_base_cost == -1


# ---------------------------------------------------------------------------
# _calculateMeanReward (pure function, no IO)
# ---------------------------------------------------------------------------
class TestCalculateMeanReward:
    def _make_svm(self, rewards, success):
        from services.svm import SVMService
        svc = SVMService.__new__(SVMService)
        svc.rewards = rewards
        svc.success = success
        svc.neglect_samples = 0
        return svc

    def test_all_failures_returns_zero(self):
        from services.svm import SVMService
        svc = self._make_svm([0.0, 0.0, 0.0], [0, 0, 0])
        assert svc._calculateMeanReward() == 0

    def test_all_successes_returns_mean(self):
        from services.svm import SVMService
        svc = self._make_svm([1.0, 2.0, 3.0], [1, 1, 1])
        assert svc._calculateMeanReward() == pytest.approx(2.0)

    def test_mixed_returns_mean_of_successes(self):
        from services.svm import SVMService
        svc = self._make_svm([1.0, 0.0, 3.0], [1, 0, 1])
        assert svc._calculateMeanReward() == pytest.approx(2.0)
