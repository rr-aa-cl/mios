"""Cancellation regressions with fake Core transport and no external services."""

import asyncio
from copy import deepcopy
from threading import Event, Thread
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from engine import engine as engine_module
from utils import ws_client


CONTEXT = {"name": "GenericTask", "skills": {}, "parameters": {}}
ACCEPTED = {"result": {"result": True, "task_uuid": "owned-task"}}
STOPPED = {"result": {"result": True}}


@pytest.fixture
def engine(monkeypatch):
    monkeypatch.delenv("MIOS_ENABLE_REDIS", raising=False)
    monkeypatch.setattr(engine_module, "MongoDBClient", MagicMock())
    monkeypatch.setattr(engine_module, "call_method", Mock(side_effect=AssertionError("Unexpected RPC")))
    monkeypatch.setattr(engine_module, "start_task", Mock(return_value=deepcopy(ACCEPTED)))
    monkeypatch.setattr(engine_module, "stop_task", Mock(return_value=deepcopy(STOPPED)))
    monkeypatch.setattr(engine_module, "wait_for_task", Mock(side_effect=AssertionError("Unexpected wait")))
    instance = engine_module.Engine({"fake-core"})
    instance.keep_running = True
    instance.problem_definition = SimpleNamespace(
        setup_instructions=[], add_skill_info={}, n_variations=1,
        tags=["offline", "test"], skill_instance="object",
        apply_object_modifiers=Mock(),
    )
    instance.write_final_results = Mock()
    yield instance
    # Release only local test state, even if a test assertion failed.
    instance.stop_requested.set()
    instance._cleanup_complete.set()


def trial():
    instruction = {"method": "start_task", "parameters": deepcopy(CONTEXT)}
    return engine_module.Trial(deepcopy(CONTEXT), [instruction], [deepcopy(instruction)], {})


def test_busy_agent_is_not_removed_from_registered_agents(engine):
    engine.free_agents.remove("fake-core")
    assert engine.agents == {"fake-core"}


def test_stop_before_main_loop_cannot_resurrect_or_run_setup(engine, monkeypatch):
    engine.problem_definition.setup_instructions = trial().reset_instructions
    assert engine.stop() is True
    engine.main_loop()
    assert engine.started.is_set()
    assert engine.keep_running is False
    engine_module.start_task.assert_not_called()
    engine_module.call_method.assert_not_called()
    engine.write_final_results.assert_called_once()
    assert engine.push_trial(trial()) == "INVALID"


def test_empty_engine_signals_started_and_stops_without_dispatch(engine):
    engine.agents.clear()
    engine.free_agents.clear()
    thread = Thread(target=engine.main_loop)
    thread.start()
    try:
        assert engine.started.wait(1)
        assert engine.stop() is True
    finally:
        engine.stop_requested.set()
        thread.join(1)
    assert not thread.is_alive()
    engine_module.start_task.assert_not_called()
    engine_module.stop_task.assert_not_called()


def test_paused_dispatch_is_cancelled_without_starting_task(engine, monkeypatch):
    engine.pause()
    waiting = Event()
    original_wait = engine.stop_requested.wait

    def wait(timeout):
        waiting.set()
        return original_wait(timeout)

    monkeypatch.setattr(engine.stop_requested, "wait", wait)
    results = []
    thread = Thread(target=lambda: results.append(engine._start_task("fake-core", deepcopy(CONTEXT))))
    thread.start()
    try:
        assert waiting.wait(1)
        assert engine.stop() is True
    finally:
        engine.stop_requested.set()
        thread.join(1)
    assert results == [(False, "INVALID")]
    engine_module.start_task.assert_not_called()


def test_inflight_start_is_followed_by_core_stop_and_not_wait_or_reset(engine, monkeypatch):
    dispatching, release = Event(), Event()
    events, results = [], []

    def start(*args, **kwargs):
        events.append("start")
        dispatching.set()
        assert release.wait(2)
        events.append("accepted")
        return deepcopy(ACCEPTED)

    def stop(*args, **kwargs):
        events.append("stop")
        return deepcopy(STOPPED)

    engine_module.start_task.side_effect = start
    engine_module.stop_task.side_effect = stop
    worker = Thread(target=lambda: results.append(engine._start_task("fake-core", deepcopy(CONTEXT))))
    stopping = Thread(target=engine.stop)
    worker.start()
    try:
        assert dispatching.wait(1)
        stopping.start()
        assert engine.stop_requested.wait(1)
        release.set()
    finally:
        release.set()
        worker.join(2)
        if stopping.ident is not None:
            stopping.join(2)
    assert not worker.is_alive() and not stopping.is_alive()
    assert events == ["start", "accepted", "stop"]
    assert results == [(False, "INVALID")]
    engine_module.wait_for_task.assert_not_called()
    engine_module.stop_task.assert_called_once_with(
        "fake-core", raise_exception=False, recover=False, empty_queue=True,
        port=12000, timeout=5, open_timeout=2, close_timeout=0.2)


@pytest.mark.parametrize("response", [None, {}, {"result": {"result": False}},
                                     {"result": {"result": "true"}}, TimeoutError("lost reply")])
def test_failed_core_stop_is_reported_and_retry_preserves_ownership(engine, response):
    assert engine._start_task("fake-core", deepcopy(CONTEXT))[0] is True
    if isinstance(response, Exception):
        engine_module.stop_task.side_effect = response
    else:
        engine_module.stop_task.return_value = response
    assert engine.stop() is False
    assert engine._owned_agents == {"fake-core"}
    assert not engine._cleanup_complete.is_set()
    assert engine._start_task("fake-core", deepcopy(CONTEXT))[0] is False
    engine_module.stop_task.side_effect = None
    engine_module.stop_task.return_value = deepcopy(STOPPED)
    assert engine.stop() is True
    assert not engine._owned_agents
    assert engine._cleanup_complete.is_set()


def test_dispatch_lock_timeout_reports_pending_stop_without_sending_early_stop(engine, monkeypatch):
    lock = Mock()
    lock.acquire.return_value = False
    monkeypatch.setattr(engine, "_dispatch_lock", lock)
    assert engine.stop() is False
    assert engine.stop_requested.is_set()
    lock.acquire.assert_called_once_with(timeout=2.5)
    engine_module.stop_task.assert_not_called()


def test_successful_direct_instruction_preserves_preexisting_pending_task_ownership(engine):
    # A start acknowledgement is not task completion. An unrelated successful
    # instruction must not discard ownership of the still-pending task.
    assert engine._start_task("fake-core", deepcopy(CONTEXT)) == (True, "owned-task")
    engine_module.call_method.return_value = deepcopy(STOPPED)
    engine_module.call_method.side_effect = None
    engine._dispatch_instruction("fake-core", "set_grasped_object", {"object": "held"})
    assert engine._owned_agents == {"fake-core"}
    assert not engine._cleanup_complete.is_set()
    assert engine.stop() is True
    engine_module.stop_task.assert_called_once_with(
        "fake-core", raise_exception=False, recover=False, empty_queue=True,
        port=12000, timeout=5, open_timeout=2, close_timeout=0.2)


@pytest.mark.parametrize("phase", ["setup", "reset", "rescue"])
@pytest.mark.parametrize("method", ["start_task", "set_grasped_object"])
def test_stopped_engine_never_dispatches_setup_reset_or_rescue(engine, phase, method):
    current = trial()
    current.reset_instructions[0]["method"] = method
    current.rescue_instructions[0]["method"] = method
    engine.problem_definition.setup_instructions = current.reset_instructions
    engine.stop()
    if phase == "setup":
        engine.setup_experiment("fake-core")
    elif phase == "reset":
        engine._reset_task("fake-core", current)
    else:
        engine._rescue_task("fake-core", current)
    engine_module.start_task.assert_not_called()
    engine_module.call_method.assert_not_called()


def test_cancellation_after_trial_execution_skips_reset_rescue_and_new_variations(engine, monkeypatch):
    engine.cnt_trial = 1
    engine.problem_definition.n_variations = 3

    def execute(*args):
        engine.stop()
        return False, None

    monkeypatch.setattr(engine, "_execute_task", Mock(side_effect=execute))
    monkeypatch.setattr(engine, "_reset_task", Mock())
    monkeypatch.setattr(engine, "_rescue_task", Mock())
    engine._run_trial("fake-core", trial())
    engine._execute_task.assert_called_once()
    engine._reset_task.assert_not_called()
    engine._rescue_task.assert_not_called()
    assert engine.queued_trials.empty()


def test_stop_during_setup_failure_ends_retry_loop(engine, monkeypatch):
    engine.problem_definition.setup_instructions = trial().reset_instructions

    def fail(*args):
        engine.stop()
        return False, "INVALID"

    start = Mock(side_effect=fail)
    monkeypatch.setattr(engine, "_start_task", start)
    engine.setup_experiment("fake-core")
    start.assert_called_once()


def test_main_loop_joins_worker_before_final_results(engine, monkeypatch):
    joined = Event()
    worker = Mock()
    worker.join.side_effect = lambda: joined.set()
    engine.worker_threads = {"fake-core": worker}
    monkeypatch.setattr(engine, "_main_loop", lambda: None)
    engine.write_final_results.side_effect = lambda: pytest.fail("Worker not joined") if not joined.is_set() else None
    engine.main_loop()
    worker.join.assert_called_once_with()
    engine.write_final_results.assert_called_once()


def test_thread_start_failure_does_not_skip_cleanup_with_invalid_join(engine, monkeypatch):
    worker = Mock(ident=None)
    worker.start.side_effect = RuntimeError("cannot start worker")
    worker.join.side_effect = AssertionError("Cannot join an unstarted thread")
    monkeypatch.setattr(engine_module, "Thread", Mock(return_value=worker))
    with pytest.raises(RuntimeError, match="cannot start worker"):
        engine.main_loop()
    worker.join.assert_not_called()
    assert engine.stop_requested.is_set()
    engine.write_final_results.assert_called_once()


def test_main_loop_remains_busy_until_failed_core_stop_is_retried(engine, monkeypatch):
    assert engine._start_task("fake-core", deepcopy(CONTEXT))[0]
    engine_module.stop_task.return_value = None
    assert engine.stop() is False
    waiting = Event()
    original_wait = engine._cleanup_complete.wait

    def wait():
        waiting.set()
        return original_wait()

    monkeypatch.setattr(engine._cleanup_complete, "wait", wait)
    monkeypatch.setattr(engine, "_main_loop", lambda: None)
    thread = Thread(target=engine.main_loop)
    thread.start()
    try:
        assert waiting.wait(1)
        engine.write_final_results.assert_not_called()
        assert thread.is_alive()
        engine_module.stop_task.return_value = deepcopy(STOPPED)
        assert engine.stop() is True
    finally:
        engine._cleanup_complete.set()
        thread.join(1)
    assert not thread.is_alive()
    engine.write_final_results.assert_called_once()


def test_cancelled_task_wait_uses_single_cancellable_request(engine):
    def wait(*args, **kwargs):
        assert kwargs["cancel_event"] is engine.stop_requested
        engine.stop()
        return None

    engine_module.wait_for_task.side_effect = wait
    result, _ = engine._wait_for_task("fake-core", "owned-task")
    assert result is False
    engine_module.wait_for_task.assert_called_once_with(
        "fake-core", "owned-task", port=12000, open_timeout=2, close_timeout=0.2,
        cancel_event=engine.stop_requested)


@pytest.mark.parametrize("phase", ["opening", "receiving"])
def test_websocket_cancel_interrupts_one_connection_without_reissuing_rpc(monkeypatch, phase):
    async def exercise():
        entered = asyncio.Event()
        cancelled = asyncio.Event()
        stop = Event()
        socket = MagicMock()
        socket.send = AsyncMock()
        socket.__aexit__ = AsyncMock(return_value=False)

        async def block():
            entered.set()
            try:
                await asyncio.Event().wait()
            finally:
                cancelled.set()

        socket.__aenter__ = AsyncMock(side_effect=block if phase == "opening" else None,
                                      return_value=socket)
        socket.recv = AsyncMock(side_effect=block)
        connect = Mock(return_value=socket)
        monkeypatch.setattr(ws_client.websockets, "connect", connect)
        operation = asyncio.create_task(ws_client.send(
            "fake-core", request={"method": "wait_for_task", "request": {"task_uuid": "owned"}},
            timeout=100, open_timeout=2, close_timeout=0.2, cancel_event=stop))
        await asyncio.wait_for(entered.wait(), timeout=1)
        stop.set()
        assert await asyncio.wait_for(operation, timeout=1) is None
        assert cancelled.is_set()
        connect.assert_called_once_with("ws://fake-core:12000/mios/core", open_timeout=2, close_timeout=0.2)
        assert socket.send.call_count == (1 if phase == "receiving" else 0)
        assert socket.__aexit__.call_count == (1 if phase == "receiving" else 0)

    asyncio.run(exercise())


def test_already_cancelled_websocket_never_connects(monkeypatch):
    connect = Mock(side_effect=AssertionError("Must not connect"))
    monkeypatch.setattr(ws_client.websockets, "connect", connect)
    stop = Event()
    stop.set()
    assert ws_client.call_method("fake-core", 12000, "wait_for_task", cancel_event=stop,
                                 open_timeout=2, close_timeout=0.2) is None
    connect.assert_not_called()
