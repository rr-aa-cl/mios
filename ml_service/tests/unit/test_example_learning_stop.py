"""Offline cancellation checks; no learning or controller requests are sent."""

from pathlib import Path
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import example_learning as examples


class LearningStopTests(unittest.TestCase):
    def setUp(self):
        self.events = []
        self.proxy = mock.MagicMock()
        self.service = self.proxy.return_value.__enter__.return_value
        self.service.stop_service.side_effect = lambda: self.events.append("stop ML")
        self.portal = mock.Mock(side_effect=lambda *args, **kwargs: self.events.append("stop Core"))
        self.check = mock.Mock(side_effect=lambda *args: self.events.append("check idle"))
        for name, replacement in (("ServerProxy", self.proxy), ("call_method", self.portal),
                                  ("check_learning_services", self.check)):
            patch = mock.patch.object(examples, name, replacement)
            patch.start()
            self.addCleanup(patch.stop)
        self.sleep = mock.patch.object(examples.time, "sleep").start()
        self.addCleanup(mock.patch.stopall)

    def test_stop_requests_precede_idle_confirmation(self):
        examples.stop_learning("deployment.local")
        self.assertEqual(["stop ML", "stop Core", "check idle"], self.events)
        self.service.stop_service.assert_called_once_with()
        self.portal.assert_called_once_with(
            "deployment.local", 12000, "stop_task",
            {"raise_exception": False, "recover": False, "empty_queue": True},
            timeout=5, open_timeout=5, close_timeout=0.2)
        self.check.assert_called_once_with("deployment.local", 8000)

    def test_busy_worker_retries_both_stop_requests(self):
        self.check.side_effect = [RuntimeError("ML is busy"), None]
        with mock.patch.object(examples.time, "monotonic", side_effect=[0, 1]):
            examples.stop_learning("127.0.0.1")
        self.assertEqual(2, self.service.stop_service.call_count)
        self.assertEqual(2, self.portal.call_count)
        self.assertEqual(2, self.check.call_count)
        self.sleep.assert_called_once_with(0.2)

    def test_lost_ml_stop_reply_still_stops_core_and_checks_state(self):
        self.service.stop_service.side_effect = TimeoutError("ML reply lost")
        examples.stop_learning("127.0.0.1")
        self.portal.assert_called_once()
        self.check.assert_called_once()

    def test_lost_core_stop_reply_can_be_resolved_by_idle_readback(self):
        self.portal.side_effect = TimeoutError("Core reply lost")
        examples.stop_learning("127.0.0.1")
        self.service.stop_service.assert_called_once()
        self.check.assert_called_once()

    def test_unconfirmed_stop_exits_at_deadline_with_rpc_failures(self):
        self.service.stop_service.side_effect = TimeoutError("ML reply lost")
        self.portal.side_effect = TimeoutError("Core reply lost")
        self.check.side_effect = RuntimeError("Core remains busy")
        with mock.patch.object(examples.time, "monotonic", side_effect=[0, 11]):
            with self.assertRaises(RuntimeError) as raised:
                examples.stop_learning("127.0.0.1")
        for message in ("ML reply lost", "Core reply lost", "Core remains busy"):
            self.assertIn(message, str(raised.exception))
        self.sleep.assert_not_called()

    def test_service_transport_has_a_finite_socket_timeout(self):
        transport = examples._ServiceTransport()
        connection = transport.make_connection("127.0.0.1:8000")
        self.assertEqual(5, connection.timeout)
        connection.close()


if __name__ == "__main__":
    unittest.main()
