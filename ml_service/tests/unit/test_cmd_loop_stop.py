"""Offline CMDLoop cancellation races; all Portal calls are mocked."""

import importlib.util
from pathlib import Path
import sys
from threading import Event, Thread
import time
import types
import unittest
from unittest import mock


class ContextTask:
    def __init__(self, agent, port):
        self.context = {"parameters": {"as_queue": False}, "skills": {}}

    def add_skill(self, name, skill_type, context):
        self.context["skills"][name] = context


_helper = types.ModuleType("utils.helper_functions")
_helper.Task = ContextTask
_transport = types.ModuleType("utils.ws_client")
_transport.call_method = mock.Mock(side_effect=AssertionError("Unexpected Portal call"))
_source = Path(__file__).resolve().parents[2] / "utils" / "cmd_loop.py"
_spec = importlib.util.spec_from_file_location("cmd_loop_tested", _source)
cmd_loop = importlib.util.module_from_spec(_spec)
with mock.patch.dict(sys.modules, {"utils.helper_functions": _helper, "utils.ws_client": _transport}):
    _spec.loader.exec_module(cmd_loop)


def accepted(**fields):
    return {"result": {"result": True, **fields}}


class CMDLoopStopTests(unittest.TestCase):
    def setUp(self):
        self.loop = cmd_loop.CMDLoop({
            "agent": "core.example", "port": 12000,
            "skills": [["hold", "HoldPose", {"skill": {}}]],
        })
        self.events = []
        self.wait_entered = Event()
        self.release = Event()
        patcher = mock.patch.object(cmd_loop, "call_method", side_effect=self.respond)
        self.portal = patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.cleanup)

    def cleanup(self):
        self.release.set()
        self.loop.stop_requested.set()
        if self.loop.thread is not None:
            self.loop.thread.join(timeout=2)

    def respond(self, host, port, method, payload, **kwargs):
        self.events.append(method)
        if method == "start_task":
            return accepted(task_uuid="task-1")
        if method == "wait_for_task":
            self.wait_entered.set()
            kwargs["cancel_event"].wait(timeout=2)
            return None
        self.assertEqual("stop_task", method)
        return accepted()

    def test_stop_cancels_active_wait_and_clears_queue_before_returning(self):
        self.assertTrue(self.loop.start())
        self.assertTrue(self.wait_entered.wait(timeout=1))
        self.assertTrue(self.loop.stop())
        self.assertTrue(self.loop.finished.is_set())
        self.assertFalse(self.loop.thread.is_alive())
        self.assertFalse(self.loop.start())
        self.assertEqual(["start_task", "wait_for_task", "stop_task"], self.events)
        start, wait, stop = self.portal.call_args_list
        self.assertFalse(start.args[3]["queue"])
        self.assertEqual(100, len(start.args[3]["parameters"]["skills"]))
        self.assertIs(self.loop.stop_requested, wait.kwargs["cancel_event"])
        self.assertEqual({"task_uuid": "task-1"}, wait.args[3])
        self.assertEqual({"raise_exception": False, "recover": False, "empty_queue": True}, stop.args[3])
        for call in (start, stop):
            self.assertEqual({"timeout": 5, "open_timeout": 2, "close_timeout": 0.2}, call.kwargs)
        self.assertEqual(0.2, wait.kwargs["close_timeout"])

    def test_stop_before_start_is_sticky_and_does_not_dispatch(self):
        self.assertTrue(self.loop.stop())
        self.assertFalse(self.loop.start())
        self.assertIsNone(self.loop.thread)
        self.assertEqual(["stop_task"], self.events)

    def test_request_stop_is_nonblocking_even_while_dispatch_lock_is_held(self):
        self.loop.keep_running = True
        with self.loop._dispatch_lock:
            self.loop.request_stop()
            self.assertTrue(self.loop.stop_requested.is_set())
            self.assertFalse(self.loop.keep_running)
            self.assertFalse(self.loop.start())
        self.portal.assert_not_called()
        self.assertTrue(self.loop.stop())

    def test_in_flight_start_finishes_before_stop_and_cannot_start_a_wait_or_another_task(self):
        dispatch_entered = Event()

        def respond(host, port, method, payload, **kwargs):
            if method == "start_task":
                self.events.append("start entered")
                dispatch_entered.set()
                self.release.wait(timeout=2)
                self.events.append("start returned")
                return accepted(task_uuid="task-1")
            self.events.append(method)
            return accepted()

        self.portal.side_effect = respond
        self.loop.start()
        self.assertTrue(dispatch_entered.wait(timeout=1))
        outcome = []
        stopper = Thread(target=lambda: outcome.append(self.loop.stop()))
        stopper.start()
        self.addCleanup(lambda: stopper.join(timeout=2))
        self.assertTrue(self.loop.stop_requested.wait(timeout=1))
        self.assertEqual(["start entered"], self.events)
        self.release.set()
        stopper.join(timeout=2)
        self.assertFalse(stopper.is_alive())
        self.assertEqual([True], outcome)
        self.assertEqual(["start entered", "start returned", "stop_task"], self.events)

    def test_pending_dispatch_returns_bounded_failure_then_stop_can_be_retried(self):
        dispatch_entered = Event()

        def respond(host, port, method, payload, **kwargs):
            self.events.append(method)
            if method == "start_task":
                dispatch_entered.set()
                self.release.wait(timeout=2)
                return accepted(task_uuid="task-1")
            return accepted()

        self.portal.side_effect = respond
        self.loop._DISPATCH_LOCK_TIMEOUT = 0.02
        self.loop.start()
        self.assertTrue(dispatch_entered.wait(timeout=1))
        started = time.monotonic()
        self.assertFalse(self.loop.stop())
        self.assertLess(time.monotonic() - started, 0.5)
        self.assertEqual(["start_task"], self.events)
        self.assertTrue(self.loop.stop_requested.is_set())
        self.release.set()
        self.assertTrue(self.loop.finished.wait(timeout=1))
        self.assertTrue(self.loop.stop())
        self.assertEqual(["start_task", "stop_task"], self.events)

    def test_stop_interrupts_long_inter_task_sleep(self):
        self.loop.sleep = 1000

        def respond(host, port, method, payload, **kwargs):
            if method == "wait_for_task":
                self.events.append(method)
                self.wait_entered.set()
                return accepted()
            return self.respond(host, port, method, payload, **kwargs)

        self.portal.side_effect = respond
        self.loop.start()
        self.assertTrue(self.wait_entered.wait(timeout=1))
        self.assertTrue(self.loop.stop())
        self.assertEqual(["start_task", "wait_for_task", "stop_task"], self.events)

    def test_stop_failure_is_explicit_and_retry_never_reenables_dispatch(self):
        for response in (None, {}, {"result": []}, {"result": {"result": False}},
                         {"result": {"result": 1}}):
            with self.subTest(response=response):
                self.portal.side_effect = [response, accepted()]
                self.assertFalse(self.loop.stop())
                self.assertTrue(self.loop.stop_requested.is_set())
                self.assertFalse(self.loop.start())
                self.assertTrue(self.loop.stop())

    def test_stop_transport_exception_returns_false(self):
        self.portal.side_effect = TimeoutError("stop reply lost")
        self.assertFalse(self.loop.stop())
        self.assertIn("stop reply lost", self.loop.last_error)
        self.assertFalse(self.loop.start())

    def test_unresponsive_worker_has_bounded_join_and_can_be_stopped_again(self):
        def respond(host, port, method, payload, **kwargs):
            if method == "wait_for_task":
                self.events.append(method)
                self.wait_entered.set()
                self.release.wait(timeout=2)
                return None
            return self.respond(host, port, method, payload, **kwargs)

        self.portal.side_effect = respond
        self.loop._JOIN_TIMEOUT = 0.02
        self.loop.start()
        self.assertTrue(self.wait_entered.wait(timeout=1))
        started = time.monotonic()
        self.assertFalse(self.loop.stop())
        self.assertLess(time.monotonic() - started, 0.5)
        self.assertTrue(self.loop.thread.is_alive())
        self.release.set()
        self.assertTrue(self.loop.finished.wait(timeout=1))
        self.assertTrue(self.loop.stop())
        self.assertEqual(1, self.events.count("start_task"))

    def test_lost_dispatch_reply_stops_core_without_repeating_dispatch(self):
        self.portal.side_effect = [None, accepted()]
        self.loop.start()
        self.assertTrue(self.loop.finished.wait(timeout=1))
        self.assertEqual(["start_task", "stop_task"], [call.args[2] for call in self.portal.call_args_list])
        self.assertTrue(self.loop.stop_requested.is_set())
        self.assertIn("dispatch", self.loop.last_error)
        self.assertFalse(self.loop.start())

    def test_lost_completion_reply_stops_core_without_repeating_dispatch(self):
        self.portal.side_effect = [accepted(task_uuid="task-1"), None, accepted()]
        self.loop.start()
        self.assertTrue(self.loop.finished.wait(timeout=1))
        self.assertEqual(["start_task", "wait_for_task", "stop_task"],
                         [call.args[2] for call in self.portal.call_args_list])
        self.assertTrue(self.loop.stop_requested.is_set())
        self.assertIn("completion", self.loop.last_error)


if __name__ == "__main__":
    unittest.main()
