"""In-flight candidate evidence survives faults; all Mongo/Core I/O is offline."""

from copy import deepcopy
from threading import Event, Lock, Thread
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import numpy as np
import pytest
from pymongo.results import UpdateResult

from engine import engine as engine_module


CONTEXT = {
    "name": "GenericTask",
    "parameters": {"skill_names": ["insertion"], "skill_types": ["TaxInsertion"]},
    "skills": {"insertion": {"skill": {"objects": {"Insertable": "test-peg"},
                                        "p0": {"dX_d": [0.01, 0.1]},
                                        "p1": {"K_x": [200, 200, 200, 20, 20, 20]}},
                              "control": {"control_mode": 1}}},
}
ACCEPTED = {"result": {"result": True, "task_uuid": "insertion-core-uuid"}}
COMPLETED = {"result": {"result": True, "task_result": {
    "success": True, "skill_results": {"insertion": {"cost": {"time": 1.25}, "heuristic": 0}},
    "error": [], "diagnostic_detail": {"preserve_raw": [1, 2, 3]},
}}}


def trial(*, key="trial-1", log=True, reset=False):
    reset_context = {"name": "GenericTask", "parameters": {}, "skills": {}}
    instructions = [{"method": "start_task", "parameters": reset_context}] if reset else []
    value = engine_module.Trial(deepcopy(CONTEXT), instructions, [], {"p0_speed": np.float64(0.01)}, log=log)
    value.trial_uuid, value.agent = key, "fake-core"
    return value


@pytest.fixture
def engine(monkeypatch, mongo_client):
    monkeypatch.delenv("MIOS_ENABLE_REDIS", raising=False)
    monkeypatch.setattr(engine_module, "MongoDBClient", MagicMock())
    monkeypatch.setattr(engine_module, "call_method", Mock(side_effect=AssertionError("Unexpected Core RPC")))
    monkeypatch.setattr(engine_module, "start_task", Mock(return_value=deepcopy(ACCEPTED)))
    monkeypatch.setattr(engine_module, "wait_for_task", Mock(return_value=deepcopy(COMPLETED)))
    monkeypatch.setattr(engine_module, "stop_task", Mock(return_value={"result": {"result": True}}))
    instance = engine_module.Engine({"fake-core"})
    instance.keep_running, instance.cnt_trial = True, 1
    instance.database_results_collection = mongo_client.ml_results.insertion
    instance.database_results_id = instance.database_results_collection.insert_one({"meta": {}}).inserted_id
    instance.x = np.empty((0, 1))

    def cost(result):
        result.q_metric.final_cost = 0.5
        return result.q_metric

    def modify(context):
        context["skills"]["insertion"]["skill"]["pose_modifier_applied"] = True

    instance.problem_definition = SimpleNamespace(
        setup_instructions=[], add_skill_info={"log_name": "offline/"}, n_variations=1,
        tags=["offline", "audit"], skill_instance="test-peg", apply_object_modifiers=modify,
        variate_only_success=True, calculate_cost=cost,
        domain=SimpleNamespace(limits={"p0_speed": [0.001, 0.1]}, vector_mapping=["p0_speed"]),
    )
    monkeypatch.setattr(instance.stop_requested, "wait", Mock(return_value=False))
    yield instance
    instance.stop_requested.set()
    instance._cleanup_complete.set()


def document(engine):
    return engine.database_results_collection.find_one({"_id": engine.database_results_id})


def pending(engine, key="trial-1"):
    return document(engine)["pending_trials"][key]


def test_exact_mutated_context_is_persisted_before_dispatch_and_raw_result_before_reset(engine, monkeypatch):
    current = trial()
    observations = []

    def dispatch(agent, task_name, context, queue, **kwargs):
        saved = pending(engine)
        assert saved["task_context"] == context
        assert saved["dispatch_state"] == "prepared"
        assert "task_uuid" not in saved  # Preparation is not proof of Core execution.
        assert saved["theta"] == {"p0_speed": 0.01}
        assert saved["agent"] == "fake-core"
        assert saved["trial_number"] == 1
        assert saved["t_0"] == current.t_0
        skill = saved["task_context"]["skills"]["insertion"]["skill"]
        assert skill["pose_modifier_applied"] is True
        assert skill["log_name"].endswith("n1/learning_insertion-0")
        assert skill["meta"]["tags"] == ["offline", "audit"]
        assert "context" in skill["meta"] and "time" in skill["meta"]
        observations.append(deepcopy(saved))
        return deepcopy(ACCEPTED)

    def reset(agent, value):
        saved = pending(engine)
        assert saved["start_response"] == ACCEPTED
        assert saved["task_uuid"] == "insertion-core-uuid"
        assert value.task_uuid == "insertion-core-uuid"
        assert saved["completion_response"] == COMPLETED
        assert saved["dispatch_state"] == "completion_reply_received"
        assert saved["task_context"] == observations[0]["task_context"]
        engine.stop()  # Interruption in reset must retain insertion evidence.

    engine_module.start_task.side_effect = dispatch
    monkeypatch.setattr(engine, "_reset_task", reset)
    engine._run_trial("fake-core", current)

    assert len(observations) == 1
    assert pending(engine)["completion_response"] == COMPLETED
    assert "n1" not in document(engine)
    assert engine.completed_trials == {}


@pytest.mark.parametrize("outcome", ["exception", "unacknowledged", "missing_run", "uninitialized"])
def test_required_audit_failure_prevents_dispatch(engine, monkeypatch, outcome):
    if outcome == "uninitialized":
        engine.database_results_collection = None
    elif outcome == "missing_run":
        engine.database_results_collection.delete_one({"_id": engine.database_results_id})
    else:
        collection = Mock()
        collection.update_one.side_effect = OSError("audit storage unavailable") if outcome == "exception" else None
        collection.update_one.return_value = UpdateResult({}, acknowledged=False)
        monkeypatch.setattr(engine.database_results_collection, "with_options", Mock(return_value=collection))

    with pytest.raises((RuntimeError, OSError)):
        engine._execute_task("fake-core", trial())

    engine_module.start_task.assert_not_called()
    engine_module.wait_for_task.assert_not_called()
    assert engine._owned_agents == set()


def test_stop_arriving_during_required_write_prevents_dispatch(engine, monkeypatch):
    original = engine._write_results_update

    def save_then_cancel(update):
        original(update)
        engine.stop_requested.set()

    monkeypatch.setattr(engine, "_write_results_update", save_then_cancel)
    assert engine._execute_task("fake-core", trial()) == (False, None)
    assert pending(engine)["dispatch_state"] == "prepared"
    engine_module.start_task.assert_not_called()


def test_cancel_during_audit_retries_owned_task_stop_after_dispatch_lock_timeout(engine, monkeypatch):
    saved, release = Event(), Event()
    errors, results = [], []
    original = engine._write_results_update

    class ImmediateTimeoutLock:
        """Deterministically model stop's bounded acquisition while audit holds it."""
        def __init__(self):
            self.lock = Lock()

        def __enter__(self):
            self.lock.acquire()

        def __exit__(self, *args):
            self.lock.release()

        def acquire(self, timeout):
            assert timeout == 2.5
            return self.lock.acquire(blocking=False)

        def release(self):
            self.lock.release()

    def delayed_write(update):
        original(update)
        saved.set()
        assert release.wait(2), "Test did not release the audit write"

    def run():
        try:
            current = trial()
            results.append(engine._start_task("fake-core", current.task_context, trial=current))
        except BaseException as error:
            errors.append(error)

    engine._owned_agents.add("already-running-core")
    engine._cleanup_complete.clear()
    monkeypatch.setattr(engine, "_dispatch_lock", ImmediateTimeoutLock())
    monkeypatch.setattr(engine, "_write_results_update", delayed_write)
    worker = Thread(target=run)
    worker.start()
    try:
        assert saved.wait(2)
        assert engine.stop() is False  # Audit still holds dispatch lock.
        engine_module.stop_task.assert_not_called()
    finally:
        release.set()
        worker.join(2)

    assert not worker.is_alive()
    assert not errors
    assert results == [(False, "INVALID")]
    assert engine._owned_agents == set()
    assert engine._cleanup_complete.is_set()
    assert pending(engine)["dispatch_state"] == "prepared"
    engine_module.start_task.assert_not_called()
    engine_module.stop_task.assert_called_once_with(
        "already-running-core", raise_exception=False, recover=False, empty_queue=True,
        port=12000, timeout=5, open_timeout=2, close_timeout=0.2)


@pytest.mark.parametrize("stop_acknowledged", [True, False])
def test_lost_start_reply_retains_attempt_without_claiming_execution(engine, stop_acknowledged):
    engine_module.start_task.return_value = None
    engine_module.stop_task.return_value = {"result": {"result": stop_acknowledged}}
    assert engine._execute_task("fake-core", trial()) == (False, None)

    saved = pending(engine)
    assert saved["dispatch_state"] == "start_reply_missing"
    assert saved["start_response"] is None
    assert saved["task_uuid"] is None
    assert saved["task_context"]["skills"]["insertion"]["skill"]["p0"]["dX_d"] == [0.01, 0.1]
    assert engine.stop_requested.is_set()
    assert engine._owned_agents == (set() if stop_acknowledged else {"fake-core"})
    engine_module.stop_task.assert_called_once_with(
        "fake-core", raise_exception=False, recover=False, empty_queue=True,
        port=12000, timeout=5, open_timeout=2, close_timeout=0.2)
    engine_module.wait_for_task.assert_not_called()


def test_completion_transport_loss_retains_context_and_uuid_after_core_stop(engine):
    engine_module.wait_for_task.return_value = None
    engine._run_trial("fake-core", trial())

    saved = pending(engine)
    assert saved["task_uuid"] == "insertion-core-uuid"
    assert saved["dispatch_state"] == "completion_reply_missing"
    assert saved["completion_response"] is None
    assert engine.stop_requested.is_set()
    assert engine.completed_trials == {}
    assert "n1" not in document(engine)
    engine_module.stop_task.assert_called_once()


def test_successful_insertion_raw_result_survives_reset_transport_failure(engine):
    engine_module.start_task.side_effect = [deepcopy(ACCEPTED), {"result": {"result": True, "task_uuid": "reset-uuid"}}]
    engine_module.wait_for_task.side_effect = [deepcopy(COMPLETED), None]
    engine._run_trial("fake-core", trial(reset=True))

    saved = pending(engine)
    assert saved["task_uuid"] == "insertion-core-uuid"
    assert saved["start_response"] == ACCEPTED
    assert saved["completion_response"] == COMPLETED
    assert "n1" not in document(engine)
    assert engine.completed_trials == {}
    assert engine_module.start_task.call_count == 2  # Existing insertion/reset dispatch only.
    engine_module.stop_task.assert_called_once()


def test_reply_arriving_with_cancellation_is_still_preserved(engine):
    def finish_and_cancel(*args, **kwargs):
        engine.stop_requested.set()
        return deepcopy(COMPLETED)

    engine_module.wait_for_task.side_effect = finish_and_cancel
    engine._run_trial("fake-core", trial())
    assert pending(engine)["completion_response"] == COMPLETED
    assert engine.completed_trials == {}
    assert "n1" not in document(engine)


def test_post_dispatch_audit_failure_leaves_prepared_evidence_and_worker_stops_core(engine, monkeypatch):
    original = engine._write_results_update
    calls = []

    def fail_after_dispatch(update):
        calls.append(update)
        if len(calls) > 1:
            raise OSError("lost database after start")
        return original(update)

    monkeypatch.setattr(engine, "_write_results_update", fail_after_dispatch)
    current = trial()
    engine.queued_trials.put(current)
    engine.queued_trials.get_nowait()
    engine._worker_loop("fake-core", current)

    assert pending(engine)["dispatch_state"] == "prepared"
    assert engine.stop_requested.is_set()
    assert engine._owned_agents == set()
    engine_module.stop_task.assert_called_once()
    engine_module.wait_for_task.assert_not_called()
    assert engine.completed_trials == {}


def test_normal_completion_atomically_saves_compact_result_and_removes_only_its_pending_entry(engine, monkeypatch):
    other = trial(key="other-trial")
    engine._record_pending_trial("other-core", other, other.task_context)
    updates, concerns = [], []
    original_options = engine.database_results_collection.with_options

    def with_options(**kwargs):
        concerns.append(kwargs["write_concern"].document)
        collection = original_options(**kwargs)
        return SimpleNamespace(update_one=lambda query, update, **options: (
            updates.append(deepcopy(update)), collection.update_one(query, update, **options))[1])

    monkeypatch.setattr(engine.database_results_collection, "with_options", with_options)
    engine._run_trial("fake-core", trial())

    saved = document(engine)
    assert set(saved["pending_trials"]) == {"other-trial"}
    assert saved["n1"]["task_uuid"] == "insertion-core-uuid"
    assert saved["n1"]["trial_uuid"] == "trial-1"
    assert "task_context" not in saved["n1"]
    assert set(engine.completed_trials) == {"trial-1"}
    assert updates[-1]["$set"]["n1"] == saved["n1"]
    assert updates[-1]["$unset"] == {"pending_trials.trial-1": ""}
    assert all(value == {"w": 1, "j": True, "wtimeout": 5000} for value in concerns)


def test_failed_final_save_retains_pending_and_does_not_publish_optimizer_result(engine, monkeypatch):
    original = engine._write_results_update

    def fail_final(update):
        if "$unset" in update:
            raise OSError("final save failed")
        return original(update)

    monkeypatch.setattr(engine, "_write_results_update", fail_final)
    with pytest.raises(OSError, match="final save failed"):
        engine._run_trial("fake-core", trial())
    assert pending(engine)["completion_response"] == COMPLETED
    assert "n1" not in document(engine)
    assert engine.completed_trials == {}


@pytest.mark.parametrize("interrupted", [False, True])
def test_log_opt_out_still_audits_dispatch_without_accumulating_completed_contexts(engine, interrupted):
    seen = []

    def dispatch(*args, **kwargs):
        seen.append(pending(engine))
        return deepcopy(ACCEPTED)

    engine_module.start_task.side_effect = dispatch
    if interrupted:
        engine_module.wait_for_task.return_value = None
    engine._run_trial("fake-core", trial(log=False))

    assert len(seen) == 1
    assert "n1" not in document(engine)
    assert ("trial-1" in document(engine)["pending_trials"]) is interrupted
    assert ("trial-1" in engine.completed_trials) is not interrupted


def test_repeated_candidates_leave_no_completed_full_contexts(engine):
    for number in range(20):
        engine._run_trial("fake-core", trial(key=f"trial-{number}"))
        assert document(engine).get("pending_trials") == {}
    saved = document(engine)
    assert len([key for key in saved if key.startswith("n")]) == 20
    assert all("task_context" not in saved[f"n{number}"] for number in range(1, 21))


def test_idempotent_acknowledged_write_does_not_require_modified_count(engine):
    # Matched-but-unchanged writes are valid, including equal timestamps in a retry.
    update = {"$set": {"unchanged": "value"}}
    engine._write_results_update(update)
    engine._write_results_update(update)
    assert document(engine)["unchanged"] == "value"
