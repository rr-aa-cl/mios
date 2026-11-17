"""Exercise learning cancellation with real threads and fake external resources."""

from concurrent.futures import Future
from threading import Event, Thread
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from services import base_service
from utils.exception import StopService


class Service(base_service.BaseService):
    def _initialize(self):
        self.initialize_hook()

    def _learn_task(self):
        return self.learn_hook()

    def _terminate(self):
        pass

    def _is_learned(self):
        return False


class FakeEngine:
    def __init__(self):
        self.stop_requested = Event()
        self.started = Event()
        self.entered = Event()
        self.before_started = Event()
        self.before_started.set()
        self.before_finished = Event()
        self.before_finished.set()
        self.finished = Event()
        self.keep_running = False
        self.fail_start = False
        self.did_work = False
        self.stop_calls = 0
        self.stop_result = True
        self.initialize = Mock(return_value="results-id")
        self.resume = Mock()
        self.push_trial = Mock(return_value="trial-id")

    def main_loop(self):
        self.entered.set()
        try:
            if self.fail_start:
                return
            assert self.before_started.wait(3)
            self.started.set()
            if not self.stop_requested.is_set():
                self.keep_running = True
                self.did_work = True
            assert self.stop_requested.wait(3)
            assert self.before_finished.wait(3)
        finally:
            self.keep_running = False
            self.finished.set()

    def stop(self):
        self.stop_calls += 1
        self.stop_requested.set()
        self.keep_running = False
        return self.stop_result


@pytest.fixture
def session(monkeypatch, simple_problem_definition):
    engine = FakeEngine()
    factory = Mock(return_value=engine)
    manager = Mock()
    manager.get_knowledge_by_id.return_value = None
    database = Mock()
    database.read.return_value = [{"meta": {}, "final_results": {}}]
    monkeypatch.setattr(base_service, "Engine", factory)
    monkeypatch.setattr(base_service, "KnowledgeManager", Mock(return_value=manager))
    monkeypatch.setattr(base_service, "MongoDBClient", Mock(return_value=database))
    monkeypatch.setattr(base_service.socket, "setdefaulttimeout", Mock())
    service = Service()
    service.initialize_hook = Mock()
    service.learn_hook = Mock(return_value=True)
    simple_problem_definition.is_valid = Mock(return_value=True)
    config = SimpleNamespace(exploration_mode=False)
    value = SimpleNamespace(
        service=service, engine=engine, factory=factory, manager=manager,
        database=database,
        initialize=lambda: service.initialize(simple_problem_definition, config, {"robot"}),
    )
    yield value
    service.stop_requested.set()
    engine.stop_requested.set()
    engine.before_started.set()
    engine.before_finished.set()
    if service.engine_thread is not None and service.engine_thread.ident is not None:
        service.engine_thread.join(2)
        assert not service.engine_thread.is_alive()


@pytest.fixture
def background():
    threads = []

    def run(function):
        result = Future()

        def invoke():
            try:
                result.set_result(function())
            except BaseException as error:
                result.set_exception(error)

        thread = Thread(target=invoke, daemon=True)
        threads.append(thread)
        thread.start()
        return result

    yield run
    for thread in threads:
        thread.join(3)
        assert not thread.is_alive()


def test_stop_before_initialization_does_not_create_engine(session):
    assert session.service.stop() is True
    assert session.initialize() is False
    session.factory.assert_not_called()
    session.service.initialize_hook.assert_not_called()


@pytest.mark.parametrize("stage", ["knowledge", "constructor", "engine", "optimizer", "thread"])
def test_stop_during_startup_is_not_lost(session, background, stage):
    entered, release = Event(), Event()

    def blocked(value):
        def call(*args, **kwargs):
            entered.set()
            assert release.wait(2)
            return value
        return call

    if stage == "knowledge":
        session.service.knowledge.mode = "local"
        session.manager.get_similar_knowledge.side_effect = blocked({})
    elif stage == "constructor":
        session.factory.side_effect = blocked(session.engine)
    elif stage == "engine":
        session.engine.initialize.side_effect = blocked("results-id")
    elif stage == "optimizer":
        session.service.initialize_hook.side_effect = blocked(None)
    else:
        session.engine.before_started.clear()
        entered = session.engine.entered
        release = session.engine.before_started

    result = background(session.initialize)
    try:
        assert entered.wait(1)
        assert session.service.stop() is True
    finally:
        release.set()
    assert result.result(2) is False
    assert session.service.keep_running is False
    assert session.service.stop_requested.is_set()
    assert session.engine.did_work is False
    session.service.learn_hook.assert_not_called()
    if session.service.engine_thread is not None:
        assert not session.service.engine_thread.is_alive()


def test_engine_failure_before_started_does_not_hang_initializer(session, background):
    session.engine.fail_start = True
    result = background(session.initialize)
    assert result.result(1) is False
    assert session.engine.finished.is_set()
    assert session.engine.stop_calls >= 1


@pytest.mark.parametrize("stage", ["engine", "optimizer"])
def test_initialization_exception_cleans_up_engine(session, stage):
    target = session.engine.initialize if stage == "engine" else session.service.initialize_hook
    target.side_effect = RuntimeError("initialization failed")
    with pytest.raises(RuntimeError, match="initialization failed"):
        session.initialize()
    assert session.service.stop_requested.is_set()
    assert session.engine.stop_calls >= 1
    assert session.service.engine_thread is None


def test_stop_before_optimizer_cannot_restart_learning(session):
    assert session.initialize() is True
    assert session.service.engine.stop_requested is session.service.stop_requested
    assert session.service.stop() is True
    assert session.service.learn_task() is False
    assert session.service.keep_running is False
    session.service.learn_hook.assert_not_called()
    assert session.engine.finished.is_set()


@pytest.mark.parametrize("error", [RuntimeError("optimizer failed"), KeyboardInterrupt()])
def test_optimizer_exception_waits_for_engine_cleanup(session, background, error):
    assert session.initialize() is True
    session.engine.before_finished.clear()
    session.service.learn_hook.side_effect = error
    result = background(session.service.learn_task)
    try:
        assert session.service.stop_requested.wait(1)
        assert not result.done()
    finally:
        session.engine.before_finished.set()
    with pytest.raises(type(error)):
        result.result(1)
    assert session.service.result is False
    assert session.engine.finished.is_set()
    assert not session.service.engine_thread.is_alive()
    session.database.read.assert_not_called()


def test_normal_optimizer_stop_preserves_success(session):
    assert session.initialize() is True

    def complete():
        session.service.stop()
        return True

    session.service.learn_hook.side_effect = complete
    assert session.service.learn_task() is True
    assert session.service.result is True
    assert session.engine.finished.is_set()
    session.database.update.assert_called_once()


def test_stop_returns_core_acknowledgement_and_latches_before_call(session):
    assert session.initialize() is True
    session.engine.stop_result = False
    original_stop = session.engine.stop

    def stop():
        assert session.service.stop_requested.is_set()
        assert session.service.keep_running is False
        return original_stop()

    session.engine.stop = stop
    assert session.service.stop() is False
    assert session.service.start() is False
    session.engine.resume.assert_not_called()


def test_stopped_service_cannot_enqueue_another_trial(session):
    assert session.initialize() is True
    session.service.stop()
    with pytest.raises(StopService):
        session.service.push_trial([0.5, 0.5])
    session.engine.push_trial.assert_not_called()


def test_stop_wakes_paused_trial_without_enqueuing(session, background):
    assert session.initialize() is True
    session.service.pause_execution = True
    session.service.keep_running = True
    result = background(lambda: session.service.push_trial([0.5, 0.5]))
    session.service.stop()
    with pytest.raises(StopService):
        result.result(1)
    session.engine.push_trial.assert_not_called()
