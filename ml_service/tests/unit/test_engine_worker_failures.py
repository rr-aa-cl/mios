"""Offline worker failure regressions; all Core and Mongo transports are mocked."""

from copy import deepcopy
from threading import Event, Thread
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest

from engine import engine as engine_module


AGENT = "fake-core"
CONTEXT = {"name": "GenericTask", "skills": {}, "parameters": {}}
STOPPED = {"result": {"result": True}}


@pytest.fixture
def engine(monkeypatch):
    monkeypatch.delenv("MIOS_ENABLE_REDIS", raising=False)
    monkeypatch.setattr(engine_module, "MongoDBClient", MagicMock())
    for method in ("call_method", "start_task", "wait_for_task"):
        monkeypatch.setattr(engine_module, method, Mock(
            side_effect=AssertionError("Unexpected Core request")))
    monkeypatch.setattr(engine_module, "stop_task", Mock(return_value=deepcopy(STOPPED)))
    instance = engine_module.Engine({AGENT})
    instance.keep_running = True
    instance.exploration_mode = True
    instance.cnt_trial = 1
    instance.problem_definition = SimpleNamespace(
        setup_instructions=[], add_skill_info={}, n_variations=1,
        tags=["offline", "test"], skill_instance="held-object",
        apply_object_modifiers=Mock(), variate_only_success=True,
        domain=SimpleNamespace(limits={}, vector_mapping=[]),
        calculate_cost=Mock(side_effect=lambda result: result.q_metric),
    )
    instance.write_final_results = Mock()
    instance.write_task_result = Mock()
    yield instance
    instance.stop_requested.set()
    instance._cleanup_complete.set()


def trial():
    instruction = {"method": "start_task", "parameters": deepcopy(CONTEXT),
                   "preconditions": {"grasped_object": "held-object", "status": "Idle"}}
    current = engine_module.Trial(
        deepcopy(CONTEXT), [instruction], [deepcopy(instruction)], {})
    current.trial_uuid = "trial-1"
    return current


def completed_result(*errors):
    result = engine_module.TaskResult()
    result.errors = list(errors)
    result.q_metric.success = not errors
    return result


def mock_execution(engine, monkeypatch, result):
    monkeypatch.setattr(engine, "_start_task", Mock(return_value=(True, "task-1")))
    monkeypatch.setattr(engine, "_wait_for_task", Mock(return_value=(True, result)))


@pytest.mark.parametrize("error", ["TaskError", "RealTimeError", "UserStopped"])
def test_fresh_physical_fault_cancels_trial_without_reset_rescue_or_requeue(engine, monkeypatch, error):
    mock_execution(engine, monkeypatch, completed_result(error))
    monkeypatch.setattr(engine, "_reset_task", Mock())
    monkeypatch.setattr(engine, "_rescue_task", Mock())
    monkeypatch.setattr(engine.stop_requested, "wait", Mock(return_value=False))

    engine._run_trial(AGENT, trial())

    assert engine.stop_requested.is_set()
    assert not engine.keep_running
    engine._start_task.assert_called_once()
    engine._wait_for_task.assert_called_once()
    engine.problem_definition.calculate_cost.assert_not_called()
    engine._reset_task.assert_not_called()
    engine._rescue_task.assert_not_called()
    engine.write_task_result.assert_not_called()
    engine.stop_requested.wait.assert_not_called()
    assert engine.queued_trials.empty()
    assert engine.completed_trials == {}


@pytest.mark.parametrize("previous_error", ["TaskError", "RealTimeError", "UserStopped"])
def test_previous_variation_error_does_not_override_current_clean_result(engine, monkeypatch, previous_error):
    current = trial()
    current.task_result.errors = [previous_error]
    fresh = completed_result()
    mock_execution(engine, monkeypatch, fresh)
    monkeypatch.setattr(engine.stop_requested, "wait", Mock(return_value=False))

    assert engine._execute_task(AGENT, current) == (True, fresh)

    assert not engine.stop_requested.is_set()
    engine.problem_definition.calculate_cost.assert_called_once_with(fresh)


def mock_precondition_response(engine, monkeypatch, response):
    engine_module.call_method.side_effect = None
    engine_module.call_method.return_value = response
    mock_execution(engine, monkeypatch, completed_result())


@pytest.mark.parametrize("phase", ["reset", "rescue"])
def test_precondition_mismatch_skips_whole_instruction(engine, monkeypatch, phase):
    mock_precondition_response(engine, monkeypatch, {"result": {
        "result": True, "grasped_object": "different-object", "status": "Idle"}})

    getattr(engine, f"_{phase}_task")(AGENT, trial())

    assert engine._running()
    engine._start_task.assert_not_called()
    engine._wait_for_task.assert_not_called()
    engine_module.stop_task.assert_not_called()
    engine_module.call_method.assert_called_once()
    assert engine_module.call_method.call_args.args[:3] == (AGENT, 12000, "get_state")


INVALID_STATES = [
    None,
    {},
    {"result": None},
    {"result": []},
    {"result": {"result": False, "grasped_object": "held-object", "status": "Idle"}},
    {"result": {"result": "true", "grasped_object": "held-object", "status": "Idle"}},
    {"result": {"grasped_object": "held-object", "status": "Idle"}},
    {"result": {"result": True, "status": "Idle"}},
    {"result": {"result": True, "grasped_object": "held-object"}},
]


@pytest.mark.parametrize("phase", ["reset", "rescue"])
@pytest.mark.parametrize("response", INVALID_STATES, ids=[
    "missing-reply", "missing-result", "null-result", "list-result", "rejected",
    "nonboolean-acceptance", "missing-acceptance", "missing-object", "missing-status",
])
def test_unknown_precondition_state_cancels_without_dispatch_or_retry(engine, monkeypatch, phase, response):
    mock_precondition_response(engine, monkeypatch, response)
    # Cancellation must also stop any previously dispatched task still owned.
    engine._owned_agents.add(AGENT)
    engine._cleanup_complete.clear()
    monkeypatch.setattr(engine.stop_requested, "wait", Mock(return_value=False))

    getattr(engine, f"_{phase}_task")(AGENT, trial())

    assert engine.stop_requested.is_set()
    assert not engine.keep_running
    assert engine._owned_agents == set()
    assert engine._cleanup_complete.is_set()
    engine_module.call_method.assert_called_once()
    engine._start_task.assert_not_called()
    engine._wait_for_task.assert_not_called()
    engine.stop_requested.wait.assert_not_called()
    engine_module.stop_task.assert_called_once_with(
        AGENT, raise_exception=False, recover=False, empty_queue=True,
        port=12000, timeout=5, open_timeout=2, close_timeout=0.2)


def set_grasp_precondition(current):
    # InsertionFactory guards extraction by object name, not by robot status.
    for instruction in current.reset_instructions + current.rescue_instructions:
        instruction["preconditions"] = {"grasped_object": "held-object"}


@pytest.mark.parametrize("phase", ["reset", "rescue"])
@pytest.mark.parametrize("state_fields", [
    {"status": "Reflex"},
    {"status": "UserStopped"},
    {},
    {"status": None},
    {"status": "Unknown"},
    {"status": "Idle", "error_message": "Robot state is stale"},
], ids=["reflex", "user-stopped", "missing-status", "null-status", "unknown-status", "state-error"])
def test_matching_grasp_does_not_allow_reset_or_rescue_in_fault_or_unknown_state(
        engine, monkeypatch, phase, state_fields):
    current = trial()
    set_grasp_precondition(current)
    response = {"result": {"result": True, "grasped_object": "held-object", **state_fields}}
    mock_precondition_response(engine, monkeypatch, response)
    monkeypatch.setattr(engine.stop_requested, "wait", Mock(return_value=False))

    getattr(engine, f"_{phase}_task")(AGENT, current)

    assert engine.stop_requested.is_set()
    assert not engine.keep_running
    engine._start_task.assert_not_called()
    engine._wait_for_task.assert_not_called()
    engine.stop_requested.wait.assert_not_called()
    engine_module.call_method.assert_called_once()


@pytest.mark.parametrize("phase", ["reset", "rescue"])
@pytest.mark.parametrize("preconditions", [None, [], ["grasped_object"], "", "grasped_object", 1],
                         ids=["null", "empty-list", "nonempty-list", "empty-string", "nonempty-string", "integer"])
def test_malformed_preconditions_cancel_without_motion(engine, monkeypatch, phase, preconditions):
    current = trial()
    for instruction in current.reset_instructions + current.rescue_instructions:
        instruction["preconditions"] = preconditions
    mock_precondition_response(engine, monkeypatch, {"result": {
        "result": True, "grasped_object": "held-object", "status": "Idle"}})

    getattr(engine, f"_{phase}_task")(AGENT, current)

    assert engine.stop_requested.is_set()
    assert not engine.keep_running
    engine._start_task.assert_not_called()
    engine._wait_for_task.assert_not_called()
    engine_module.call_method.assert_not_called()


@pytest.mark.parametrize("phase", ["reset", "rescue"])
@pytest.mark.parametrize("status", ["Idle", "Move"])
def test_matching_preconditions_dispatch_instruction_once(engine, monkeypatch, phase, status):
    current = trial()
    set_grasp_precondition(current)
    mock_precondition_response(engine, monkeypatch, {"result": {
        "result": True, "grasped_object": "held-object", "status": status}})

    getattr(engine, f"_{phase}_task")(AGENT, current)

    assert engine._running()
    engine._start_task.assert_called_once_with(AGENT, CONTEXT)
    engine._wait_for_task.assert_called_once_with(AGENT, "task-1")
    engine_module.call_method.assert_called_once()
    engine_module.stop_task.assert_not_called()


@pytest.mark.parametrize("really_started", [False, True], ids=["before-start", "after-start"])
def test_trial_thread_start_failure_balances_queue_without_releasing_a_live_worker(
        engine, monkeypatch, really_started):
    entered = Event()
    available_during_worker = []
    created = []

    class FailedTrialThread(Thread):
        def start(self):
            if self._target.__name__ == "_setup_worker":
                return super().start()
            created.append(self)
            if really_started:
                super().start()
                assert entered.wait(2), "Trial worker did not start"
            raise RuntimeError("trial thread start failed")

    def run_trial(agent, current):
        entered.set()
        assert engine.stop_requested.wait(2), "Engine did not cancel after launch exception"
        available_during_worker.append(agent in engine.free_agents)

    monkeypatch.setattr(engine_module, "Thread", FailedTrialThread)
    monkeypatch.setattr(engine, "setup_experiment", Mock())
    monkeypatch.setattr(engine, "_run_trial", Mock(side_effect=run_trial))
    engine_module.call_method.side_effect = None
    engine_module.call_method.return_value = {"result": {"busy": False}}
    current = trial()
    engine.queued_trials.put(current)
    done = Mock(wraps=engine.queued_trials.task_done)
    monkeypatch.setattr(engine.queued_trials, "task_done", done)

    with pytest.raises(RuntimeError, match="trial thread start failed"):
        engine.main_loop()

    assert engine.stop_requested.is_set()
    assert not engine.keep_running
    assert engine.free_agents == {AGENT}
    assert engine.agents == {AGENT}
    assert engine.queued_trials.empty()
    assert engine.queued_trials.unfinished_tasks == 0
    done.assert_called_once_with()
    engine.setup_experiment.assert_called_once_with(AGENT)
    engine.write_final_results.assert_called_once_with()
    assert len(created) == 1
    assert not created[0].is_alive()
    assert engine._run_trial.call_count == int(really_started)
    assert available_during_worker == ([False] if really_started else [])
    engine_module.start_task.assert_not_called()
    engine_module.wait_for_task.assert_not_called()
    engine_module.stop_task.assert_not_called()
