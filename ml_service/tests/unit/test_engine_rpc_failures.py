"""Core reply failures cancel learning without retrying physical tasks."""

from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest

from engine import engine as engine_module


AGENT = "fake-core"
CONTEXT = {"name": "GenericTask", "parameters": {}, "skills": {}}
ACCEPTED = {"result": {"result": True, "task_uuid": "owned-task"}}
STOPPED = {"result": {"result": True}}
TASK_RESULT = {
    "success": True,
    "exception": False,
    "external_stop": False,
    "error": [],
    "skill_results": {"insertion": {"cost": {"time": 1.25}, "heuristic": 0.0}},
}


def completion(task_result=None, *, accepted=True):
    return {"result": {"result": accepted,
                       "task_result": deepcopy(TASK_RESULT if task_result is None else task_result)}}


def trial():
    instruction = {"method": "start_task", "parameters": deepcopy(CONTEXT)}
    value = engine_module.Trial(deepcopy(CONTEXT), [instruction], [deepcopy(instruction)], {})
    value.trial_uuid = "rpc-failure-trial"
    value.agent = AGENT
    return value


@pytest.fixture
def engine(monkeypatch, mongo_client):
    monkeypatch.delenv("MIOS_ENABLE_REDIS", raising=False)
    monkeypatch.setattr(engine_module, "MongoDBClient", MagicMock())
    monkeypatch.setattr(engine_module, "call_method", Mock(
        side_effect=AssertionError("Unexpected Core request")))
    monkeypatch.setattr(engine_module, "start_task", Mock(return_value=deepcopy(ACCEPTED)))
    monkeypatch.setattr(engine_module, "wait_for_task", Mock(return_value=completion()))
    monkeypatch.setattr(engine_module, "stop_task", Mock(return_value=deepcopy(STOPPED)))
    instance = engine_module.Engine({AGENT})
    instance.keep_running = True
    instance.database_results_collection = mongo_client.ml_results.insertion
    instance.database_results_id = instance.database_results_collection.insert_one({}).inserted_id
    instance.problem_definition = SimpleNamespace(
        setup_instructions=[], add_skill_info={}, n_variations=1,
        tags=["offline", "rpc-failure"], skill_instance="test-object",
        apply_object_modifiers=Mock(), variate_only_success=True,
        domain=SimpleNamespace(limits={}, vector_mapping=[]),
    )
    instance.write_task_result = Mock()
    yield instance
    instance.stop_requested.set()
    instance._cleanup_complete.set()


def assert_cancelled(engine, *, stopped=True):
    assert engine.stop_requested.is_set()
    assert engine.keep_running is False
    assert engine._owned_agents == (set() if stopped else {AGENT})
    assert engine._cleanup_complete.is_set() is stopped
    assert engine.completed_trials == {}
    assert engine.cnt_completed == 0
    assert engine.queued_trials.empty()
    assert engine.push_trial(trial()) == "INVALID"
    engine_module.stop_task.assert_called_once_with(
        AGENT, raise_exception=False, recover=False, empty_queue=True,
        port=12000, timeout=5, open_timeout=2, close_timeout=0.2)


INVALID_START_REPLIES = [
    pytest.param(None, id="missing"),
    pytest.param([], id="outer-list"),
    pytest.param("invalid", id="outer-string"),
    pytest.param({}, id="no-result"),
    pytest.param({"result": None}, id="null-result"),
    pytest.param({"result": []}, id="list-result"),
    pytest.param({"result": {}}, id="missing-acceptance"),
    pytest.param({"result": {"result": False}}, id="rejected-without-error"),
    pytest.param({"result": {"result": "true", "task_uuid": "owned-task"}}, id="string-acceptance"),
    pytest.param({"result": {"result": 1, "task_uuid": "owned-task"}}, id="integer-acceptance"),
    pytest.param({"result": {"result": True}}, id="missing-uuid"),
    *[pytest.param({"result": {"result": True, "task_uuid": value}}, id=label)
      for label, value in (("null-uuid", None), ("empty-uuid", ""),
                           ("blank-uuid", "  "), ("invalid-uuid", "INVALID"),
                           ("non-string-uuid", 42))],
]


@pytest.mark.parametrize("reply", INVALID_START_REPLIES)
def test_invalid_start_reply_cancels_instead_of_retrying(engine, monkeypatch, reply):
    engine_module.start_task.return_value = deepcopy(reply)
    monkeypatch.setattr(engine.stop_requested, "wait", Mock(
        side_effect=AssertionError("Invalid start must cancel without a retry delay")))

    assert engine._start_task(AGENT, deepcopy(CONTEXT)) == (False, "INVALID")

    assert_cancelled(engine)
    engine_module.start_task.assert_called_once()
    engine_module.wait_for_task.assert_not_called()
    assert engine.skill_count == 0
    # Cancellation stays latched even after Core acknowledges the stop.
    assert engine._start_task(AGENT, deepcopy(CONTEXT)) == (False, "INVALID")
    engine_module.start_task.assert_called_once()


INVALID_COMPLETION_REPLIES = [
    pytest.param(None, id="missing"),
    pytest.param([], id="outer-list"),
    pytest.param("invalid", id="outer-string"),
    pytest.param({}, id="no-result"),
    pytest.param({"result": None}, id="null-result"),
    pytest.param({"result": []}, id="list-result"),
    pytest.param({"result": {"task_result": TASK_RESULT}}, id="missing-acceptance"),
    pytest.param(completion(accepted=False), id="rejected-without-error"),
    pytest.param(completion(accepted="true"), id="string-acceptance"),
    pytest.param(completion(accepted=1), id="integer-acceptance"),
    pytest.param({"result": {"result": True}}, id="missing-task-result"),
    *[pytest.param({"result": {"result": True, "task_result": value}}, id=label)
      for label, value in (("null-task-result", None), ("list-task-result", []),
                           ("string-task-result", "invalid"))],
    pytest.param(completion({}), id="calculation-missing-success"),
    pytest.param(completion({"success": True, "error": []}), id="calculation-missing-skills"),
    pytest.param(completion({**TASK_RESULT, "skill_results": {
        "insertion": {"cost": {"time": None}, "heuristic": 0.0}}}), id="calculation-null-cost"),
    *[pytest.param(completion({**TASK_RESULT, "skill_results": {
        "insertion": {"cost": value, "heuristic": 0.0}}}), id=label)
      for label, value in (("malformed-cost-mapping-null", None),
                           ("malformed-cost-mapping-list", []))],
    pytest.param(completion({**TASK_RESULT, "exception": True}), id="task-exception"),
    pytest.param(completion({**TASK_RESULT, "external_stop": True}), id="external-stop"),
]


@pytest.mark.parametrize("reply", INVALID_COMPLETION_REPLIES)
def test_invalid_completion_cancels_and_does_not_release_unconfirmed_task(engine, monkeypatch, reply):
    assert engine._start_task(AGENT, deepcopy(CONTEXT)) == (True, "owned-task")
    engine_module.wait_for_task.return_value = deepcopy(reply)
    monkeypatch.setattr(engine.stop_requested, "wait", Mock(
        side_effect=AssertionError("Invalid completion must cancel without a retry delay")))

    success, result = engine._wait_for_task(AGENT, "owned-task")

    assert success is False
    assert isinstance(result, engine_module.TaskResult)
    assert_cancelled(engine)
    engine_module.start_task.assert_called_once()
    engine_module.wait_for_task.assert_called_once_with(
        AGENT, "owned-task", port=12000, open_timeout=2, close_timeout=0.2,
        cancel_event=engine.stop_requested)


@pytest.mark.parametrize("error_code", ["TaskError", "RealTimeError", "UserStopped"])
@pytest.mark.parametrize("flags_present", [True, False], ids=["false-flags", "absent-flags"])
@pytest.mark.parametrize("stop_acknowledged", [True, False], ids=["stopped", "unconfirmed-stop"])
def test_fault_error_code_cancels_before_releasing_task_ownership(
        engine, monkeypatch, error_code, flags_present, stop_acknowledged):
    assert engine._start_task(AGENT, deepcopy(CONTEXT)) == (True, "owned-task")
    result = {**TASK_RESULT, "success": False, "error": [error_code]}
    if not flags_present:
        result.pop("exception")
        result.pop("external_stop")
    engine_module.wait_for_task.return_value = completion(result)

    def stop(*args, **kwargs):
        # A parsed task fault is not permission to release the agent first:
        # stop still has to address that Core and clear any queued tasks.
        assert engine._owned_agents == {AGENT}
        assert not engine._cleanup_complete.is_set()
        assert engine.stop_requested.is_set()
        return {"result": {"result": stop_acknowledged}}

    engine_module.stop_task.side_effect = stop
    monkeypatch.setattr(engine.stop_requested, "wait", Mock(
        side_effect=AssertionError("Faulted completion must cancel without a retry delay")))

    success, _ = engine._wait_for_task(AGENT, "owned-task")

    assert success is False
    assert_cancelled(engine, stopped=stop_acknowledged)
    engine_module.start_task.assert_called_once()
    engine_module.wait_for_task.assert_called_once()


@pytest.mark.parametrize("stage", ["start", "completion"])
@pytest.mark.parametrize("stop_reply", [None, {"result": {"result": False}},
                                       {"result": {"result": "true"}}],
                         ids=["missing-stop", "rejected-stop", "ambiguous-stop"])
def test_unconfirmed_stop_preserves_ownership_until_explicit_stop_retry(engine, stage, stop_reply):
    engine_module.stop_task.return_value = deepcopy(stop_reply)
    if stage == "start":
        engine_module.start_task.return_value = None
        assert engine._start_task(AGENT, deepcopy(CONTEXT)) == (False, "INVALID")
    else:
        assert engine._start_task(AGENT, deepcopy(CONTEXT)) == (True, "owned-task")
        engine_module.wait_for_task.return_value = completion(accepted=False)
        assert engine._wait_for_task(AGENT, "owned-task")[0] is False

    assert_cancelled(engine, stopped=False)
    assert engine._start_task(AGENT, deepcopy(CONTEXT)) == (False, "INVALID")
    engine_module.start_task.assert_called_once()
    engine_module.stop_task.return_value = deepcopy(STOPPED)

    assert engine.stop() is True

    assert engine._owned_agents == set()
    assert engine._cleanup_complete.is_set()
    assert engine.stop_requested.is_set()
    assert engine_module.stop_task.call_count == 2
    engine_module.start_task.assert_called_once()


@pytest.mark.parametrize("stage", ["start", "completion"])
@pytest.mark.parametrize("failure", ["rejected", "transport-exception"])
@pytest.mark.parametrize("stop_acknowledged", [True, False])
def test_worker_failure_releases_assignment_without_reset_rescue_or_requeue(
        engine, monkeypatch, stage, failure, stop_acknowledged):
    transport = engine_module.start_task if stage == "start" else engine_module.wait_for_task
    if failure == "transport-exception":
        transport.side_effect = TimeoutError("Core reply was lost")
    else:
        transport.return_value = {"result": {"result": False}}
    engine_module.stop_task.return_value = {"result": {"result": stop_acknowledged}}
    monkeypatch.setattr(engine, "_reset_task", Mock(
        side_effect=AssertionError("No reset after an unresolved task")))
    monkeypatch.setattr(engine, "_rescue_task", Mock(
        side_effect=AssertionError("No rescue after an unresolved task")))
    current = trial()
    engine.queued_trials.put(current)
    assert engine.queued_trials.get_nowait() is current
    engine.free_agents.remove(AGENT)

    engine._worker_loop(AGENT, current)

    assert_cancelled(engine, stopped=stop_acknowledged)
    # The worker is finished; unresolved physical ownership is tracked
    # separately, and the cancellation latch still prevents dispatch.
    assert engine.free_agents == {AGENT}
    assert engine.queued_trials.unfinished_tasks == 0
    engine_module.start_task.assert_called_once()
    assert engine_module.wait_for_task.call_count == (stage == "completion")
    engine._reset_task.assert_not_called()
    engine._rescue_task.assert_not_called()
    engine.write_task_result.assert_not_called()


@pytest.mark.parametrize("task_success", [True, False])
def test_valid_completion_keeps_learning_running_even_when_candidate_fails(engine, task_success):
    engine_module.wait_for_task.return_value = completion({**TASK_RESULT, "success": task_success})

    assert engine._start_task(AGENT, deepcopy(CONTEXT)) == (True, "owned-task")
    assert engine._owned_agents == {AGENT}
    assert not engine._cleanup_complete.is_set()
    success, result = engine._wait_for_task(AGENT, "owned-task")

    assert success is True
    assert result.q_metric.success is task_success
    assert result.q_metric.cost["time"] == 1.25
    assert engine.keep_running is True
    assert not engine.stop_requested.is_set()
    assert engine._owned_agents == set()
    assert engine._cleanup_complete.is_set()
    engine_module.stop_task.assert_not_called()
