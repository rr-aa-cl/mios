"""Missing trial results must cancel learning without inventing optimizer data."""

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest

from engine import engine as engine_module
from services import base_service
from utils.exception import StopService


CONTEXT = {"name": "GenericTask", "skills": {}, "parameters": {}}
ACCEPTED = {"result": {"result": True, "task_uuid": "owned-task"}}
STOPPED = {"result": {"result": True}}


def trial():
    instruction = {"method": "start_task", "parameters": deepcopy(CONTEXT)}
    value = engine_module.Trial(deepcopy(CONTEXT), [instruction], [deepcopy(instruction)], {})
    value.trial_uuid = "trial-1"
    return value


@pytest.fixture
def engine(monkeypatch, mongo_client):
    monkeypatch.delenv("MIOS_ENABLE_REDIS", raising=False)
    monkeypatch.setattr(engine_module, "MongoDBClient", MagicMock())
    monkeypatch.setattr(engine_module, "call_method", Mock(side_effect=AssertionError("Unexpected Core request")))
    monkeypatch.setattr(engine_module, "start_task", Mock(return_value=deepcopy(ACCEPTED)))
    monkeypatch.setattr(engine_module, "stop_task", Mock(return_value=deepcopy(STOPPED)))
    monkeypatch.setattr(engine_module, "wait_for_task", Mock(return_value=None))
    instance = engine_module.Engine({"fake-core"})
    instance.database_results_collection = mongo_client.ml_results.insertion
    instance.database_results_id = instance.database_results_collection.insert_one({}).inserted_id
    instance.keep_running = True
    instance.cnt_trial = 1
    instance.problem_definition = SimpleNamespace(
        setup_instructions=[], add_skill_info={}, n_variations=1,
        tags=["offline", "test"], skill_instance="taught_object",
        apply_object_modifiers=Mock(), variate_only_success=True,
        domain=SimpleNamespace(limits={}, vector_mapping=[]),
    )
    instance.write_task_result = Mock()
    yield instance
    instance.stop_requested.set()
    instance._cleanup_complete.set()


@pytest.fixture
def clock(engine, monkeypatch):
    value = SimpleNamespace(now=100.0, waits=[])
    monkeypatch.setattr(engine_module, "time", SimpleNamespace(
        monotonic=lambda: value.now,
        time=Mock(side_effect=AssertionError("Trial deadlines must not use the adjustable wall clock")),
    ))

    def wait(timeout):
        assert timeout > 0
        assert len(value.waits) < 3, "Trial deadline did not cancel the wait"
        value.waits.append(timeout)
        value.now += 60.0
        return engine.stop_requested.is_set()

    monkeypatch.setattr(engine.stop_requested, "wait", wait)
    return value


def test_trial_deadline_stops_owned_task_without_a_completed_result(engine, clock):
    assert engine._start_task("fake-core", deepcopy(CONTEXT))[0] is True

    with pytest.raises(StopService):
        engine.wait_for_trial("trial-1", max_wait_time=50)

    assert clock.waits
    assert engine.stop_requested.is_set()
    assert engine.keep_running is False
    assert engine.completed_trials == {}
    assert engine.cnt_completed == 0
    assert engine._owned_agents == set()
    assert engine._cleanup_complete.is_set()
    engine_module.stop_task.assert_called_once_with(
        "fake-core", raise_exception=False, recover=False, empty_queue=True,
        port=12000, timeout=5, open_timeout=2, close_timeout=0.2)
    assert engine.push_trial(trial()) == "INVALID"
    assert engine.queued_trials.empty()


@pytest.mark.parametrize("reply", [None, {"result": {"result": False}}])
def test_trial_deadline_preserves_ownership_when_core_stop_is_unconfirmed(engine, clock, reply):
    assert engine._start_task("fake-core", deepcopy(CONTEXT))[0] is True
    engine_module.stop_task.return_value = reply

    with pytest.raises(StopService):
        engine.wait_for_trial("trial-1", max_wait_time=50)

    assert engine.stop_requested.is_set()
    assert engine._owned_agents == {"fake-core"}
    assert not engine._cleanup_complete.is_set()
    assert engine.completed_trials == {}
    assert engine.cnt_completed == 0
    assert engine.push_trial(trial()) == "INVALID"


def test_completed_trial_is_returned_without_cancelling_learning(engine, clock):
    completed = trial()
    engine.completed_trials[completed.trial_uuid] = completed

    assert engine.wait_for_trial(completed.trial_uuid, max_wait_time=50) is completed

    assert engine.cnt_completed == 1
    assert not engine.stop_requested.is_set()
    assert not clock.waits
    engine_module.stop_task.assert_not_called()


def test_cancelled_wait_raises_without_fabricating_a_trial(engine, clock):
    engine.stop_requested.set()

    with pytest.raises(StopService):
        engine.wait_for_trial("trial-1", max_wait_time=50)

    assert not clock.waits
    assert engine.completed_trials == {}
    assert engine.cnt_completed == 0
    assert engine.push_trial(trial()) == "INVALID"


@pytest.mark.parametrize("stop_acknowledged", [True, False])
def test_lost_core_completion_stops_without_reset_rescue_or_requeue(engine, monkeypatch, stop_acknowledged):
    engine_module.stop_task.return_value = {"result": {"result": stop_acknowledged}}
    monkeypatch.setattr(engine, "_reset_task", Mock(side_effect=AssertionError("Unexpected reset after lost completion")))
    monkeypatch.setattr(engine, "_rescue_task", Mock(side_effect=AssertionError("Unexpected rescue after lost completion")))
    monkeypatch.setattr(engine.stop_requested, "wait", Mock(side_effect=AssertionError("Unexpected retry after lost completion")))

    engine._run_trial("fake-core", trial())

    assert engine.stop_requested.is_set()
    engine_module.start_task.assert_called_once()
    engine_module.wait_for_task.assert_called_once()
    engine_module.stop_task.assert_called_once()
    engine._reset_task.assert_not_called()
    engine._rescue_task.assert_not_called()
    assert engine.queued_trials.empty()
    assert engine.completed_trials == {}
    assert engine.cnt_completed == 0
    assert engine._owned_agents == (set() if stop_acknowledged else {"fake-core"})
    assert engine._cleanup_complete.is_set() is stop_acknowledged


def test_reset_cancellation_does_not_publish_trial_or_launch_rescue(engine, monkeypatch):
    result = engine_module.TaskResult()
    result.q_metric.final_cost = 0.5
    result.q_metric.success = True
    result.q_metric.optimal = True
    result.q_metric.heuristic = 0.0
    result.q_metric.success_rate = 1.0
    monkeypatch.setattr(engine, "_execute_task", Mock(return_value=(True, result)))
    monkeypatch.setattr(engine, "_rescue_task", Mock(side_effect=AssertionError("Unexpected rescue after cancelled reset")))
    monkeypatch.setattr(engine.stop_requested, "wait", Mock(side_effect=AssertionError("Unexpected retry after cancelled reset")))

    engine._run_trial("fake-core", trial())

    assert engine.stop_requested.is_set()
    engine_module.start_task.assert_called_once()  # The reset was dispatched.
    engine_module.wait_for_task.assert_called_once()
    engine_module.stop_task.assert_called_once()
    engine._rescue_task.assert_not_called()
    engine.write_task_result.assert_not_called()
    assert engine.completed_trials == {}
    assert engine.cnt_completed == 0
    assert engine.cnt_optimal == 0
    assert engine.queued_trials.empty()
    assert engine.log_client.write.call_count == 1  # Only the trial-start record.


def test_confirmed_core_completion_releases_ownership_without_stop(engine):
    engine_module.wait_for_task.return_value = {
        "result": {"result": True, "task_result": {
            "success": True, "skill_results": {}, "error": []}},
    }
    assert engine._start_task("fake-core", deepcopy(CONTEXT))[0] is True

    success, result = engine._wait_for_task("fake-core", "owned-task")

    assert success is True
    assert result.q_metric.success is True
    assert engine._owned_agents == set()
    assert engine._cleanup_complete.is_set()
    assert not engine.stop_requested.is_set()
    engine_module.stop_task.assert_not_called()


def test_base_service_does_not_advance_optimizer_after_trial_deadline(engine, clock, monkeypatch):
    monkeypatch.setattr(base_service, "KnowledgeManager", Mock())
    monkeypatch.setattr(base_service, "MongoDBClient", Mock())
    monkeypatch.setattr(base_service.socket, "setdefaulttimeout", Mock())
    next_candidate = Mock()

    class WaitingService(base_service.BaseService):
        def _initialize(self):
            pass

        def _learn_task(self):
            self.wait_for_result("trial-1")
            next_candidate()
            return True

        def _terminate(self):
            pass

        def _is_learned(self):
            return False

    service = WaitingService()
    service.engine = engine
    service.stop_requested = engine.stop_requested
    service.problem_definition = engine.problem_definition
    assert engine._start_task("fake-core", deepcopy(CONTEXT))[0] is True

    assert service.learn_task() is False

    assert service.result is False
    assert service.stop_requested.is_set()
    next_candidate.assert_not_called()
    assert engine.cnt_completed == 0
    assert engine.completed_trials == {}
    assert engine.push_trial(trial()) == "INVALID"
