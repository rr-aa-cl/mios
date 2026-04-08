"""
test_task_result.py – Unit tests for QMetric, TaskResult, and calculate().
No hardware or MongoDB required.
"""
import pytest
from engine.task_result import QMetric, TaskResult, cost_types


# ---------------------------------------------------------------------------
# QMetric
# ---------------------------------------------------------------------------
class TestQMetricDefaults:
    def test_default_final_cost_is_inf(self):
        q = QMetric()
        assert q.final_cost == float("inf")

    def test_default_success_is_false(self):
        q = QMetric()
        assert q.success is False

    def test_default_cost_is_empty_dict(self):
        q = QMetric()
        assert q.cost == {}

    def test_default_heuristic_is_inf(self):
        q = QMetric()
        assert q.heuristic == float("inf")

    def test_default_optimal_is_false(self):
        q = QMetric()
        assert q.optimal is False

    def test_default_success_rate_is_zero(self):
        q = QMetric()
        assert q.success_rate == 0


class TestQMetricToDict:
    def test_to_dict_contains_all_keys(self):
        q = QMetric()
        d = q.to_dict()
        for key in ("final_cost", "success", "cost", "heuristic", "optimal", "success_rate"):
            assert key in d

    def test_to_dict_preserves_values(self):
        q = QMetric()
        q.final_cost = 0.42
        q.success = True
        q.optimal = True
        q.success_rate = 1.0
        d = q.to_dict()
        assert d["final_cost"] == 0.42
        assert d["success"] is True
        assert d["optimal"] is True
        assert d["success_rate"] == 1.0


# ---------------------------------------------------------------------------
# TaskResult
# ---------------------------------------------------------------------------
class TestTaskResultDefaults:
    def test_default_errors_is_empty_list(self):
        tr = TaskResult()
        assert tr.errors == []

    def test_default_n_variations_is_one(self):
        tr = TaskResult()
        assert tr.n_variations == 1

    def test_default_q_metric_is_qmetric(self):
        tr = TaskResult()
        assert isinstance(tr.q_metric, QMetric)


class TestTaskResultToDict:
    def test_to_dict_contains_required_keys(self):
        tr = TaskResult()
        d = tr.to_dict()
        assert "q_metric" in d
        assert "errors" in d
        # Note: the key has a typo in source ("n_varialtions")
        assert "n_varialtions" in d

    def test_to_dict_q_metric_is_dict(self):
        tr = TaskResult()
        d = tr.to_dict()
        assert isinstance(d["q_metric"], dict)


# ---------------------------------------------------------------------------
# TaskResult.calculate()
# ---------------------------------------------------------------------------
class TestTaskResultCalculate:
    def _make_result(self, success=True, skill_results=None):
        """Build a fake mios result dict."""
        if skill_results is None:
            skill_results = {
                "insertion": {
                    "cost": {ct: 0.1 for ct in cost_types},
                    "heuristic": 0.5,
                }
            }
        return {
            "success": success,
            "skill_results": skill_results,
            "error": [],
        }

    def test_calculate_happy_path(self):
        tr = TaskResult()
        result = self._make_result(success=True)
        assert tr.calculate(result) is True
        assert tr.q_metric.success is True
        assert tr.q_metric.success_rate == 1
        assert tr.errors == []

    def test_calculate_returns_false_when_no_success_key(self):
        tr = TaskResult()
        assert tr.calculate({"skill_results": {}}) is False

    def test_calculate_returns_false_when_no_skill_results(self):
        tr = TaskResult()
        assert tr.calculate({"success": True, "skill_results": None}) is False

    def test_calculate_returns_false_when_skill_results_missing(self):
        tr = TaskResult()
        assert tr.calculate({"success": True}) is False

    def test_calculate_returns_false_when_cost_is_none(self):
        tr = TaskResult()
        skill_results = {
            "insertion": {
                "cost": {"time": None},
                "heuristic": 0.0,
            }
        }
        result = self._make_result(skill_results=skill_results)
        assert tr.calculate(result) is False

    def test_calculate_accumulates_costs_across_skills(self):
        tr = TaskResult()
        skill_results = {
            "insertion": {
                "cost": {ct: 1.0 for ct in cost_types},
                "heuristic": 2.0,
            },
            "grasp": {
                "cost": {ct: 3.0 for ct in cost_types},
                "heuristic": 4.0,
            },
        }
        result = self._make_result(success=True, skill_results=skill_results)
        tr.calculate(result)
        for ct in cost_types:
            assert tr.q_metric.cost[ct] == pytest.approx(4.0)
        # Note: heuristic is accumulated inside the inner cost_type loop,
        # so each skill's heuristic is added len(cost_types) times.
        n_cost = len(cost_types)
        assert tr.q_metric.heuristic == pytest.approx(2.0 * n_cost + 4.0 * n_cost)

    def test_calculate_failure_sets_success_false(self):
        tr = TaskResult()
        result = self._make_result(success=False)
        tr.calculate(result)
        assert tr.q_metric.success is False
        assert tr.q_metric.success_rate == 0


# ---------------------------------------------------------------------------
# TaskResult.add_variation()
# ---------------------------------------------------------------------------
class TestTaskResultAddVariation:
    def test_add_variation_increments_n_variations(self):
        tr = TaskResult()
        q = QMetric()
        q.final_cost = 1.0
        q.success = True
        q.heuristic = 0.0
        q.cost = {}
        tr.add_variation(q)
        assert tr.n_variations == 2

    def test_add_variation_averages_final_cost_when_both_succeed(self):
        tr = TaskResult()
        tr.q_metric.final_cost = 2.0
        tr.q_metric.success = True
        tr.q_metric.success_rate = 1.0
        tr.q_metric.heuristic = 0.0
        tr.q_metric.cost = {}

        q = QMetric()
        q.final_cost = 4.0
        q.success = True
        q.heuristic = 0.0
        q.cost = {}
        tr.add_variation(q)
        # (2.0 * 1 + 4.0) / 2 = 3.0
        assert tr.q_metric.final_cost == pytest.approx(3.0)

    def test_add_variation_failure_overrides_success(self):
        tr = TaskResult()
        tr.q_metric.final_cost = 2.0
        tr.q_metric.success = True
        tr.q_metric.success_rate = 1.0
        tr.q_metric.heuristic = 0.0
        tr.q_metric.cost = {}

        q = QMetric()
        q.final_cost = 99.0
        q.success = False
        q.heuristic = 0.0
        q.cost = {}
        tr.add_variation(q)
        assert tr.q_metric.success is False
        # When new variation fails, its final_cost replaces the existing one
        assert tr.q_metric.final_cost == pytest.approx(99.0)

    def test_add_variation_averages_success_rate(self):
        tr = TaskResult()
        tr.q_metric.success_rate = 1.0
        tr.q_metric.success = True
        tr.q_metric.final_cost = 1.0
        tr.q_metric.heuristic = 0.0
        tr.q_metric.cost = {}

        q = QMetric()
        q.success = False
        q.final_cost = 5.0
        q.heuristic = 0.0
        q.cost = {}
        tr.add_variation(q)
        # (1.0 * 1 + 0) / 2 = 0.5
        assert tr.q_metric.success_rate == pytest.approx(0.5)
