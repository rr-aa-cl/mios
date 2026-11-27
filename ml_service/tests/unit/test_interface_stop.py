"""Learning cancellation races with fake services; no robot or database I/O."""

from threading import Event, Lock, RLock, Thread
from types import SimpleNamespace
from unittest import mock
from xmlrpc.client import ServerProxy, Transport

import pytest

from interface import interface as interface_module


@pytest.fixture
def interface():
    instance = interface_module.Interface.__new__(interface_module.Interface)
    instance.service = None
    instance.learn_thread = None
    instance.cmd_loop = None
    instance.mios_port = 12000
    instance.mongo_port = 27017
    instance.interface_port = 8000
    instance.service_lock = Lock()
    instance.lifecycle_lock = RLock()
    instance.stop_requested = Event()
    instance.stop_failed = False
    return instance


def fake_service():
    return SimpleNamespace(
        engine_thread=None, result=False,
        initialize=mock.Mock(return_value=True),
        learn_task=mock.Mock(return_value=False),
        stop=mock.Mock(return_value=True), start=mock.Mock(), pause=mock.Mock())


def problem():
    return SimpleNamespace(self_check=lambda: True, uuid=None)


def test_stop_during_constructor_cancels_before_initialization(interface):
    constructing, release = Event(), Event()
    service = fake_service()

    def construct(*args):
        constructing.set()
        assert release.wait(3)
        return service

    results = []
    with mock.patch.object(interface_module, 'CMAESService', side_effect=construct):
        caller = Thread(target=lambda: results.append(interface.start_service(
            problem(), SimpleNamespace(service_name='cmaes'), {'robot'})))
        caller.start()
        try:
            assert constructing.wait(3)
            assert interface.stop_service() is True
            assert interface.is_busy() is True
        finally:
            release.set()
            caller.join(3)
            if interface.learn_thread:
                interface.learn_thread.join(3)
    assert not caller.is_alive()
    assert results and results[0] != 'INVALID'
    assert not interface.learn_thread.is_alive()
    service.initialize.assert_not_called()
    service.learn_task.assert_not_called()
    service.stop.assert_called_once()
    assert interface.is_busy() is False


def test_stop_acknowledgement_does_not_publish_idle_before_worker_exits(interface):
    learning, release = Event(), Event()
    service = fake_service()

    def learn():
        learning.set()
        assert release.wait(3)
        return False

    service.learn_task.side_effect = learn
    with mock.patch.object(interface_module, 'CMAESService', return_value=service):
        interface.start_service(problem(), SimpleNamespace(service_name='cmaes'), {'robot'})
        try:
            assert learning.wait(3)
            assert interface.stop_service() is True
            assert interface.is_busy() is True
            assert interface.start_service(problem(), SimpleNamespace(service_name='cmaes'), {'robot'}) == 'INVALID'
        finally:
            release.set()
            interface.learn_thread.join(3)
    assert not interface.learn_thread.is_alive()
    assert interface.is_busy() is False


def test_failed_core_stop_blocks_new_run_until_retry(interface):
    service = fake_service()
    service.stop.side_effect = [False, True]
    interface.service = service
    interface.service_lock.acquire()
    assert interface.stop_service() is False
    interface.service_lock.release()  # The local worker is done, Core remains uncertain.
    assert interface.is_busy() is True
    assert interface.start_service(problem(), SimpleNamespace(service_name='cmaes'), {'robot'}) == 'INVALID'
    assert interface.stop_service() is True
    assert interface.is_busy() is False


def test_failed_optional_cmd_loop_does_not_prevent_learning_stop(interface):
    service = fake_service()
    interface.service = service
    interface.service_lock.acquire()
    loop = mock.Mock()
    loop.stop.side_effect = [RuntimeError('connection lost'), True]
    interface.cmd_loop = loop
    assert interface.stop_service() is False
    service.stop.assert_called_once()
    assert interface.cmd_loop is loop  # Preserve it for the retry.
    assert interface.stop_service() is True
    assert interface.cmd_loop is None
    interface.service_lock.release()


def test_idle_stop_does_not_send_requests_for_an_old_service(interface):
    interface.service = fake_service()
    assert interface.stop_service() is True
    interface.service.stop.assert_not_called()


@pytest.mark.parametrize('failure', ['invalid_problem', 'unknown_service', 'constructor'])
def test_failed_start_releases_busy_lock(interface, failure):
    definition = problem()
    configuration = SimpleNamespace(service_name='cmaes')
    if failure == 'invalid_problem':
        definition.self_check = lambda: False
    if failure == 'unknown_service':
        configuration.service_name = 'unknown'
    with mock.patch.object(interface_module, 'CMAESService', side_effect=RuntimeError('construction failed')):
        if failure == 'constructor':
            with pytest.raises(RuntimeError, match='construction failed'):
                interface.start_service(definition, configuration, {'robot'})
        else:
            assert interface.start_service(definition, configuration, {'robot'}) == 'INVALID'
    assert interface.is_busy() is False


def test_resume_cannot_undo_stop(interface):
    interface.service = fake_service()
    interface.stop_service()
    assert interface.resume_service() is False
    interface.service.start.assert_not_called()


def test_failed_engine_thread_start_does_not_leave_interface_busy(interface):
    service = fake_service()
    service.engine_thread = Thread(target=lambda: None)  # Allocated, never started.
    service.initialize.side_effect = RuntimeError('cannot start engine thread')
    interface.service = service
    interface.service_lock.acquire()
    with pytest.raises(RuntimeError, match='cannot start engine thread'):
        interface.learn_task(problem(), SimpleNamespace(service_name='cmaes'), {'robot'}, None)
    assert interface.is_busy() is False
    service.stop.assert_called_once()


def test_xmlrpc_stop_returns_boolean_and_keeps_api_available(interface):
    # This listener is a test-owned loopback server with no service/database.
    interface.rpc_server = interface_module.InterfaceServer(
        ('127.0.0.1', 0), allow_none=True, logRequests=False)
    port = interface.rpc_server.server_address[1]
    thread = Thread(target=interface.start_rpc_server)
    thread.start()

    class TestTransport(Transport):
        def make_connection(self, host):
            connection = super().make_connection(host)
            connection.timeout = 2
            return connection

    try:
        with ServerProxy(f'http://127.0.0.1:{port}', transport=TestTransport()) as proxy:
            assert proxy.stop_service() is True
            assert proxy.is_busy() is False
        assert thread.is_alive()
    finally:
        interface.rpc_server.shutdown()
        interface.rpc_server.server_close()
        thread.join(3)
    assert not thread.is_alive()
