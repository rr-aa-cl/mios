"""Bounded offline regressions for waiting when queued trials cannot dispatch."""

import logging
from threading import Event, Thread
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest

from engine import engine as engine_module


class CheckedSet(set):
    def __init__(self, values, check):
        super().__init__(values)
        self.check = check

    def __contains__(self, value):
        self.check(value)
        return super().__contains__(value)


class OrderedAgents(set):
    """Make the unavailable agent precede the available one deterministically."""

    def __init__(self, values):
        super().__init__(values)
        self.order = tuple(values)

    def __iter__(self):
        return iter(self.order)

    def copy(self):
        return list(self.order)


@pytest.fixture
def engine(monkeypatch):
    monkeypatch.delenv("MIOS_ENABLE_REDIS", raising=False)
    monkeypatch.setattr(engine_module, "MongoDBClient", MagicMock())
    for method in ("call_method", "start_task", "stop_task", "wait_for_task"):
        monkeypatch.setattr(engine_module, method, Mock(side_effect=AssertionError("Unexpected Core request")))
    instance = engine_module.Engine({"occupied-core"})
    instance.exploration_mode = True
    instance.problem_definition = SimpleNamespace(setup_instructions=[])
    instance.write_final_results = Mock()
    instance._run_trial = Mock(side_effect=AssertionError("Unexpected trial dispatch"))
    trial = engine_module.Trial({"name": "GenericTask", "skills": {}, "parameters": {}}, [], [], {})
    instance.queued_trials.put(trial)
    yield instance
    instance.stop_requested.set()
    instance._cleanup_complete.set()


def test_occupied_agent_yields_and_limits_waiting_logs(engine, monkeypatch, caplog):
    waits, checks = [], []
    clock = SimpleNamespace(now=100.0)
    monkeypatch.setattr(engine_module, "time", SimpleNamespace(monotonic=lambda: clock.now))

    def checked(agent):
        assert len(checks) == len(waits), "Scheduler rescanned an occupied agent without yielding"
        checks.append(agent)

    def wait(timeout):
        assert timeout > 0
        waits.append(timeout)
        clock.now += 1.0
        if len(waits) == 7:
            engine.stop_requested.set()
        return engine.stop_requested.is_set()

    engine.free_agents = CheckedSet([], checked)
    monkeypatch.setattr(engine.stop_requested, "wait", wait)
    with caplog.at_level(logging.DEBUG, logger="ml_service"):
        engine.main_loop()

    assert len(checks) == len(waits) == 7
    waiting_messages = [record for record in caplog.records
                        if record.levelno == logging.DEBUG and "occupied-core" in record.getMessage()]
    assert 1 <= len(waiting_messages) <= 2
    engine._run_trial.assert_not_called()
    engine_module.call_method.assert_not_called()


def test_assigned_agent_logs_respect_thirty_second_boundaries_per_agent(engine, monkeypatch, caplog):
    agents = ["occupied-a", "occupied-b"]
    timestamps = [100.0, 129.999, 130.0, 159.999, 160.0]
    clock = SimpleNamespace(now=timestamps[0])
    scans, waits, logged_at = [], [], {agent: [] for agent in agents}
    seen_records = 0
    engine.agents = OrderedAgents(agents)
    monkeypatch.setattr(engine_module, "time", SimpleNamespace(monotonic=lambda: clock.now))

    def checked(agent):
        assert len(scans) < (len(waits) + 1) * len(agents), "Scheduler rescanned before yielding"
        scans.append((clock.now, agent))

    def wait(timeout):
        nonlocal seen_records
        assert timeout > 0
        assert len(scans) == (len(waits) + 1) * len(agents), "Scheduler must scan both agents before yielding"
        records = [record for record in caplog.records
                   if record.levelno == logging.DEBUG
                   and "is still assigned to a trial worker" in record.getMessage()]
        for record in records[seen_records:]:
            logged_at[record.args[0]].append(clock.now)
        seen_records = len(records)
        waits.append(clock.now)
        if len(waits) == len(timestamps):
            engine.stop_requested.set()
        else:
            clock.now = timestamps[len(waits)]
        return engine.stop_requested.is_set()

    engine.free_agents = CheckedSet([], checked)
    monkeypatch.setattr(engine.stop_requested, "wait", wait)
    with caplog.at_level(logging.DEBUG, logger="ml_service"):
        engine.main_loop()

    assert waits == timestamps
    assert scans == [(timestamp, agent) for timestamp in timestamps for agent in agents]
    assert logged_at == {agent: [100.0, 130.0, 160.0] for agent in agents}
    assert engine.queued_trials.unfinished_tasks == 0
    engine._run_trial.assert_not_called()
    engine_module.call_method.assert_not_called()
    engine_module.start_task.assert_not_called()


def test_stop_wakes_scheduler_without_starting_pending_trial(engine, monkeypatch):
    waiting = Event()
    failures, checks = [], []
    original_wait = engine.stop_requested.wait

    def checked(agent):
        assert not checks, "Scheduler rescanned the occupied agent before waiting"
        checks.append(agent)

    def wait(timeout):
        assert timeout > 0
        waiting.set()
        # Hold the scheduler until cancellation, independently of wall-clock delay.
        return original_wait()

    def run():
        try:
            engine.main_loop()
        except BaseException as error:
            failures.append(error)

    engine.free_agents = CheckedSet([], checked)
    monkeypatch.setattr(engine.stop_requested, "wait", wait)
    worker = Thread(target=run)
    worker.start()
    try:
        assert waiting.wait(2), "Scheduler did not enter a cancellation-aware wait"
        assert worker.is_alive()
        assert engine.stop() is True
    finally:
        engine.stop_requested.set()
        worker.join(2)

    assert not worker.is_alive()
    assert not failures
    engine._run_trial.assert_not_called()
    engine_module.start_task.assert_not_called()
    assert engine.queued_trials.unfinished_tasks == 0


@pytest.mark.parametrize("blocker", ["assigned", "worker_cleanup"])
def test_available_second_agent_dispatches_before_scheduler_waits(engine, monkeypatch, blocker):
    engine.agents = OrderedAgents(["occupied-core", "ready-core"])
    engine.free_agents = {"ready-core"}
    if blocker == "worker_cleanup":
        engine.free_agents.add("occupied-core")
        original_get = engine.queued_trials.get

        def get(*args, **kwargs):
            trial = original_get(*args, **kwargs)
            # The prior worker published itself free but has not exited yet.
            engine.worker_threads["occupied-core"] = SimpleNamespace(
                ident=1, is_alive=lambda: True, join=Mock())
            return trial

        monkeypatch.setattr(engine.queued_trials, "get", get)

    monkeypatch.setattr(engine.stop_requested, "wait", Mock(
        side_effect=AssertionError("Scheduler waited before checking the available second agent")))
    engine_module.call_method.side_effect = None
    engine_module.call_method.return_value = {"result": {"busy": False}}

    def execute(agent, trial):
        assert agent == "ready-core"
        engine.stop_requested.set()

    engine._run_trial.side_effect = execute
    engine.main_loop()

    engine._run_trial.assert_called_once()
    assert engine._run_trial.call_args.args[0] == "ready-core"
    assert engine_module.call_method.call_count == 1
    assert engine_module.call_method.call_args.args[:3] == ("ready-core", 12000, "is_busy")
    engine.stop_requested.wait.assert_not_called()


@pytest.mark.parametrize("response", [None, {"result": {"busy": True}}], ids=["unreachable", "busy"])
def test_unavailable_core_is_not_polled_again_without_yielding(engine, monkeypatch, response):
    polls, waits = [], []

    def poll(*args, **kwargs):
        assert len(polls) == len(waits), "Core was polled again without yielding"
        polls.append(args)
        return response

    def wait(timeout):
        assert timeout > 0
        waits.append(timeout)
        if len(waits) == 3:
            engine.stop_requested.set()
        return engine.stop_requested.is_set()

    engine_module.call_method.side_effect = poll
    monkeypatch.setattr(engine.stop_requested, "wait", wait)
    engine.main_loop()

    assert len(polls) == len(waits) == 3
    engine._run_trial.assert_not_called()
    engine_module.start_task.assert_not_called()
