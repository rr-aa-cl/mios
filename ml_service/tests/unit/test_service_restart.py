"""Repeat the real learning lifecycle with in-memory storage and fake Core I/O."""

from copy import deepcopy
from threading import Event
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from engine import engine as engine_module
from interface import interface as interface_module
from services import base_service


class ControlledService(base_service.BaseService):
    """Replace only the optimizer, keeping service and engine lifecycle code."""

    def __init__(self, *args):
        super().__init__(*args)
        self.learning = Event()
        self.finish = Event()

    def _initialize(self):
        self.initial_engine_state = (
            self.engine.stop_requested.is_set(),
            self.engine.started.is_set(),
            self.engine.keep_running,
            self.engine.cnt_trial,
            self.engine.queued_trials.empty(),
            dict(self.engine.completed_trials),
        )

    def _learn_task(self):
        self.learning.set()
        assert self.finish.wait(5), "Test did not release the optimizer"
        if self.stop_requested.is_set():
            return False
        self.stop()  # SVM also requests engine shutdown on normal completion.
        return True

    def _terminate(self):
        pass

    def _is_learned(self):
        return False


@pytest.mark.parametrize("first_outcome", ["completed", "cancelled"])
def test_consecutive_runs_get_fresh_service_and_engine(
    monkeypatch, mios_mongo_client, simple_problem_definition, first_outcome
):
    monkeypatch.delenv("MIOS_ENABLE_REDIS", raising=False)
    for module in (base_service, engine_module):
        monkeypatch.setattr(module, "MongoDBClient", Mock(return_value=mios_mongo_client))
    manager = Mock()
    manager.get_knowledge_by_id.return_value = None
    monkeypatch.setattr(base_service, "KnowledgeManager", Mock(return_value=manager))
    monkeypatch.setattr(base_service.socket, "setdefaulttimeout", Mock())

    # Construct the real Interface without starting listeners or database servers.
    monkeypatch.setattr(interface_module, "Database", Mock())
    monkeypatch.setattr(interface_module, "InterfaceServer", Mock())
    monkeypatch.setattr(interface_module.Interface, "start_global_database", Mock())
    interface = interface_module.Interface()
    services = []

    def make_service(*args):
        service = ControlledService(*args)
        services.append(service)
        return service

    monkeypatch.setattr(interface_module, "SVMService", make_service)
    forbidden_calls = []
    for module, names in (
        (engine_module, ("call_method", "start_task", "stop_task", "wait_for_task")),
        (interface_module, ("call_method",)),
    ):
        for name in names:
            call = Mock(side_effect=AssertionError("Unexpected Core request"))
            monkeypatch.setattr(module, name, call)
            forbidden_calls.append(call)

    # Empty setup lets the real engine start and join its worker without motion.
    simple_problem_definition.setup_instructions = []
    configuration = SimpleNamespace(service_name="svm", exploration_mode=True)
    agents = {"fake-core"}
    run_ids, latches, threads = [], [], []
    try:
        for index in range(2):
            run_id = interface.start_service(
                deepcopy(simple_problem_definition), configuration, agents
            )
            assert run_id != "INVALID"
            run_ids.append(run_id)
            service = services[index]
            thread = interface.learn_thread
            threads.append(thread)
            latches.append(interface.stop_requested)
            assert service.learning.wait(2), "Initialization did not reach the optimizer"
            assert service.initial_engine_state == (False, False, False, 0, True, {})
            assert service.engine.started.is_set()
            assert service.engine.stop_requested is service.stop_requested
            assert not service.stop_requested.is_set()
            assert interface.is_busy() is True

            if index == 1:
                previous = services[0]
                assert service is not previous
                assert service.engine is not previous.engine
                assert service.stop_requested is not previous.stop_requested
                assert latches[1] is not latches[0]
                assert previous.stop_requested.is_set()
                assert not previous.engine_thread.is_alive()
                assert not threads[0].is_alive()

            cancelled = index == 0 and first_outcome == "cancelled"
            if cancelled:
                assert interface.stop_service() is True
                assert interface.is_busy() is True  # Optimizer has not exited yet.
                assert interface.start_service(
                    deepcopy(simple_problem_definition), configuration, agents
                ) == "INVALID"
            service.finish.set()
            thread.join(3)
            assert not thread.is_alive(), "Learning lifecycle did not finish"
            assert service.result is (not cancelled)
            assert not service.engine_thread.is_alive()
            assert all(not worker.is_alive() for worker in service.engine.worker_threads.values())
            assert interface.is_busy() is False

        assert run_ids[0] != run_ids[1]
        assert services[0].database_results_id != services[1].database_results_id
        assert agents == {"fake-core"}
        records = mios_mongo_client.read("ml_results", "insertion", {})
        assert len(records) == 2
        assert all("final_results" in record for record in records)
        for call in forbidden_calls:
            call.assert_not_called()
    finally:
        for service in services:
            service.finish.set()
            service.stop()
        for thread in threads:
            thread.join(3)
