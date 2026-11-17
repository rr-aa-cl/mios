"""Experiment completion and dispatch ordering with no robot or database I/O."""

from threading import Event, Thread
from types import SimpleNamespace
from unittest import mock
from xmlrpc.client import Fault

import pytest

from utils import experiment_wizard as wizard


@pytest.fixture
def experiment(monkeypatch):
    problem = SimpleNamespace(tags=["insertion", "taught_object"], skill_class="insertion")
    problem.to_dict = lambda: {"tags": list(problem.tags), "skill_class": problem.skill_class}
    configuration = SimpleNamespace(to_dict=lambda: {"service_name": "svm"})
    database = mock.Mock()
    database.read.return_value = []
    monkeypatch.setattr(wizard, "MongoDBClient", mock.Mock(return_value=database))

    proxy = mock.Mock()
    proxy.start_service.return_value = "run-1"
    proxy.wait_for_service.return_value = True
    proxy.is_busy.side_effect = AssertionError("An idle reply does not confirm experiment completion")
    connection = mock.MagicMock()
    connection.__enter__.return_value = proxy
    connection.__exit__.return_value = False
    factory = mock.Mock(return_value=connection)
    monkeypatch.setattr(wizard, "ServerProxy", factory)
    monkeypatch.setattr(wizard, "call_method", mock.Mock(side_effect=AssertionError("Unexpected Core request")))
    monkeypatch.setattr(wizard, "Task", mock.Mock(side_effect=AssertionError("Unexpected Core task")))

    def run(**options):
        defaults = {"keep_record": False, "wait": True, "service_port": 8123}
        defaults.update(options)
        return wizard.start_experiment(
            "offline.invalid", ["offline.invalid"], problem, configuration, **defaults)

    return SimpleNamespace(run=run, proxy=proxy, connection=connection,
                           factory=factory, database=database, problem=problem)


def test_finished_requires_successful_completion_reply(experiment, capsys):
    experiment.run()

    experiment.proxy.start_service.assert_called_once()
    experiment.proxy.wait_for_service.assert_called_once_with()
    experiment.proxy.is_busy.assert_not_called()
    experiment.factory.assert_called_once_with("http://offline.invalid:8123", allow_none=True)
    experiment.connection.__exit__.assert_called_once()
    assert "finished" in capsys.readouterr().out.lower()


def test_no_finished_message_while_server_completion_is_pending(experiment, capsys):
    waiting, release = Event(), Event()
    failures = []

    def complete():
        waiting.set()
        assert release.wait(3), "Test did not release the server completion reply"
        return True

    def run():
        try:
            experiment.run()
        except BaseException as error:
            failures.append(error)

    experiment.proxy.wait_for_service.side_effect = complete
    worker = Thread(target=run)
    worker.start()
    try:
        assert waiting.wait(2), "Client did not request server completion"
        assert worker.is_alive()
        assert "finished" not in capsys.readouterr().out.lower()
        experiment.proxy.start_service.assert_called_once()
    finally:
        release.set()
        worker.join(3)

    assert not worker.is_alive()
    assert not failures
    assert "finished" in capsys.readouterr().out.lower()


@pytest.mark.parametrize("reply", ["INVALID", "", None, False, True, 0, 1, {}, []])
def test_rejected_or_malformed_start_cannot_report_completion(experiment, capsys, reply):
    experiment.proxy.start_service.return_value = reply

    with pytest.raises(RuntimeError):
        experiment.run()

    experiment.proxy.wait_for_service.assert_not_called()
    assert "finished" not in capsys.readouterr().out.lower()
    experiment.connection.__exit__.assert_called_once()


@pytest.mark.parametrize("reply", [False, None, 0, 1, "", "True", {}, []])
def test_failed_or_malformed_completion_cannot_report_success(experiment, capsys, reply):
    experiment.proxy.wait_for_service.return_value = reply

    with pytest.raises(RuntimeError):
        experiment.run()

    experiment.proxy.wait_for_service.assert_called_once_with()
    assert "finished" not in capsys.readouterr().out.lower()
    experiment.connection.__exit__.assert_called_once()


@pytest.mark.parametrize("error", [TimeoutError("completion reply lost"), Fault(1, "worker failed")])
def test_lost_or_faulted_completion_is_not_reported_as_finished(experiment, capsys, error):
    experiment.proxy.wait_for_service.side_effect = error

    with pytest.raises((type(error), RuntimeError)):
        experiment.run()

    assert "finished" not in capsys.readouterr().out.lower()
    experiment.connection.__exit__.assert_called_once()


def test_async_dispatch_reports_started_without_waiting(experiment, capsys):
    experiment.run(wait=False)

    experiment.proxy.start_service.assert_called_once()
    experiment.proxy.wait_for_service.assert_not_called()
    experiment.proxy.is_busy.assert_not_called()
    output = capsys.readouterr().out.lower()
    assert "started" in output
    assert "finished" not in output


def test_async_repetitions_are_rejected_before_dispatch(experiment, capsys):
    with pytest.raises((ValueError, RuntimeError)):
        experiment.run(wait=False, n_eval=2)

    experiment.proxy.start_service.assert_not_called()
    experiment.proxy.wait_for_service.assert_not_called()
    assert "finished" not in capsys.readouterr().out.lower()


def test_repetitions_finish_before_the_next_dispatch(experiment, capsys):
    events = []

    def start(problem, configuration, agents, knowledge):
        assert not events or events[-1][0] == "complete"
        iteration = next(tag for tag in problem["tags"] if tag in ("n1", "n2", "n3"))
        events.append(("start", iteration))
        return "run-" + iteration

    def complete():
        assert events[-1][0] == "start"
        events.append(("complete", events[-1][1]))
        return True

    experiment.proxy.start_service.side_effect = start
    experiment.proxy.wait_for_service.side_effect = complete
    experiment.run(n_eval=3)

    assert events == [
        ("start", "n1"), ("complete", "n1"),
        ("start", "n2"), ("complete", "n2"),
        ("start", "n3"), ("complete", "n3"),
    ]
    assert capsys.readouterr().out.lower().count("finished") == 3


def test_failed_repetition_prevents_later_dispatch(experiment, capsys):
    experiment.proxy.wait_for_service.side_effect = [True, False]

    with pytest.raises(RuntimeError):
        experiment.run(n_eval=3)

    assert experiment.proxy.start_service.call_count == 2
    assert experiment.proxy.wait_for_service.call_count == 2
    assert capsys.readouterr().out.lower().count("finished") == 1
