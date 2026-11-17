"""Offline service and taught-object boundaries for the compact learning API."""

import asyncio
import contextlib
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import example_learning as examples
from utils import ws_client


class ReadOnlyLearningServiceTests(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.state = {"result": {"result": True, "current_task": "IdleTask", "status": "Idle", "control_active": False}}
        self.portal = self.stack.enter_context(mock.patch.object(examples, "call_method", return_value=self.state))
        self.proxy = self.stack.enter_context(mock.patch.object(examples, "ServerProxy"))
        self.service = self.proxy.return_value.__enter__.return_value
        self.service.is_busy.return_value = False

    def test_valid_check_uses_only_get_state_and_is_busy(self):
        examples.check_learning_services("127.0.0.1", service_port=8100)
        self.portal.assert_called_once_with("127.0.0.1", 12000, "get_state", {}, timeout=5,
                                            open_timeout=5, close_timeout=0.2)
        self.assertEqual("http://127.0.0.1:8100", self.proxy.call_args.args[0])
        self.assertEqual([mock.call.is_busy()], self.service.method_calls)
        self.proxy.return_value.__exit__.assert_called_once()

    def test_core_unreachable_or_malformed_state_blocks_before_ml_query(self):
        for response in (None, {}, {"result": []}, {"result": {"result": False}},
                         {"result": {"result": True}}):
            with self.subTest(response=response):
                self.portal.return_value = response
                with self.assertRaises(RuntimeError):
                    examples.check_learning_services("127.0.0.1")
        self.proxy.assert_not_called()

    def test_core_fault_or_running_task_blocks_before_ml_query(self):
        updates = (
            {"error": "transport fault"}, {"error_message": "robot reflex"},
            {"status": "Reflex"}, {"current_task": "Insertion"},
        )
        for update in updates:
            with self.subTest(update=update):
                self.portal.return_value = {"result": {**self.state["result"], **update}}
                with self.assertRaises(RuntimeError):
                    examples.check_learning_services("127.0.0.1")
        self.proxy.assert_not_called()

    def test_busy_or_non_boolean_ml_response_is_rejected(self):
        for busy in (True, None, 0, "false", {}, []):
            with self.subTest(busy=busy):
                self.service.is_busy.return_value = busy
                with self.assertRaises(RuntimeError):
                    examples.check_learning_services("127.0.0.1")

    def test_ml_connection_error_identifies_the_requested_endpoint(self):
        self.service.is_busy.side_effect = ConnectionRefusedError("connection refused")
        with self.assertRaisesRegex(RuntimeError, "127.0.0.1:8100"):
            examples.check_learning_services("127.0.0.1", service_port=8100)

    def test_unreleased_control_or_missing_status_blocks_completion(self):
        for update in ({"status": "Move"}, {"status": None}, {"control_active": True},
                       {"control_active": None}, {"control_active": "false"}):
            with self.subTest(update=update):
                self.portal.return_value = {"result": {**self.state["result"], **update}}
                with self.assertRaisesRegex(RuntimeError, "Core is not ready"):
                    examples.check_learning_services("127.0.0.1")
        self.proxy.assert_not_called()

    def test_old_core_without_controller_readiness_requires_rebuild(self):
        del self.state["result"]["control_active"]
        with self.assertRaisesRegex(RuntimeError, "rebuild the Core image"):
            examples.check_learning_services("127.0.0.1")
        self.proxy.assert_not_called()


class LearningWebSocketTimeoutTests(unittest.TestCase):
    def test_read_only_check_forwards_open_and_close_deadlines_to_websocket(self):
        response = {"result": {"result": True, "current_task": "IdleTask", "status": "Idle", "control_active": False}}
        websocket = mock.Mock(send=mock.AsyncMock(), recv=mock.AsyncMock(return_value=json.dumps(response)))
        connection = mock.MagicMock()
        connection.__aenter__.return_value = websocket
        loop = asyncio.new_event_loop()
        self.addCleanup(loop.close)
        with mock.patch.object(ws_client.websockets, "connect", return_value=connection) as connect, \
                mock.patch.object(examples, "ServerProxy") as proxy, \
                mock.patch.object(ws_client.asyncio, "new_event_loop", return_value=loop), \
                mock.patch.object(ws_client.asyncio, "set_event_loop"), \
                mock.patch.object(ws_client.asyncio, "get_event_loop", return_value=loop):
            proxy.return_value.__enter__.return_value.is_busy.return_value = False
            examples.check_learning_services("127.0.0.1")
        connect.assert_called_once_with("ws://127.0.0.1:12000/mios/core", open_timeout=5, close_timeout=0.2)
        websocket.send.assert_awaited_once()
        self.assertEqual({"method": "get_state", "request": {}}, json.loads(websocket.send.call_args.args[0]))
        websocket.recv.assert_awaited_once()
        connection.__aexit__.assert_awaited_once()


class TaughtInsertionObjectTests(unittest.TestCase):
    robot = "127.0.0.1"
    insertable = "janinetest1"

    def names(self, insertable=None):
        name = insertable or self.insertable
        return (name, name + "_container_approach", name + "_container")

    @staticmethod
    def reply(name):
        return {"result": {"result": True, "context": {"name": name}}}

    def test_valid_trio_uses_only_bounded_object_downloads(self):
        names = self.names()
        with mock.patch.object(examples, "call_method", side_effect=[self.reply(name) for name in names]) as portal:
            examples.check_taught_insertion_objects(self.robot, self.insertable)
        self.assertEqual([
            mock.call(self.robot, 12000, "download_object_context", {"object": name},
                      timeout=5, open_timeout=5, close_timeout=0.2)
            for name in names
        ], portal.call_args_list)

    def test_different_learning_name_cannot_reuse_another_taught_trio(self):
        taught = set(self.names("janinetest"))

        def lookup(_robot, _port, method, request, **_kwargs):
            self.assertEqual("download_object_context", method)
            name = request["object"]
            return self.reply(name) if name in taught else {"result": {"result": False}}

        with mock.patch.object(examples, "call_method", side_effect=lookup), \
                self.assertRaisesRegex(RuntimeError, "janinetest1"):
            examples.check_taught_insertion_objects(self.robot, "janinetest1")

    def test_missing_approach_or_container_identifies_required_context(self):
        for missing in self.names()[1:]:
            with self.subTest(missing=missing):
                replies = [self.reply(name) if name != missing else {"result": {"result": False}}
                           for name in self.names()]
                with mock.patch.object(examples, "call_method", side_effect=replies), \
                        self.assertRaisesRegex(RuntimeError, missing):
                    examples.check_taught_insertion_objects(self.robot, self.insertable)

    def test_malformed_download_replies_are_rejected(self):
        malformed = (None, [], {}, {"result": []}, {"result": True},
                     {"result": {"result": "true", "context": {"name": self.insertable}}},
                     {"result": {"result": True}},
                     {"result": {"result": True, "context": []}},
                     {"result": {"result": True, "context": {}}})
        for response in malformed:
            with self.subTest(response=response):
                replies = [response, *[self.reply(name) for name in self.names()[1:]]]
                with mock.patch.object(examples, "call_method", side_effect=replies), \
                        self.assertRaises(RuntimeError):
                    examples.check_taught_insertion_objects(self.robot, self.insertable)

    def test_success_flag_cannot_mask_wrong_returned_object_name(self):
        replies = [self.reply("another_object"), *[self.reply(name) for name in self.names()[1:]]]
        with mock.patch.object(examples, "call_method", side_effect=replies), \
                self.assertRaisesRegex(RuntimeError, self.insertable):
            examples.check_taught_insertion_objects(self.robot, self.insertable)

    def test_invalid_object_name_fails_without_io(self):
        with mock.patch.object(examples, "call_method") as portal:
            for name in (None, "", " ", 1, True):
                with self.subTest(name=name), self.assertRaises(ValueError):
                    examples.check_taught_insertion_objects(self.robot, name)
        portal.assert_not_called()


class ActiveGraspedObjectTests(unittest.TestCase):
    def test_true_setter_reply_needs_no_readback(self):
        with mock.patch.object(examples, "call_method", return_value={"result": {"result": True}}) as portal:
            examples.set_active_grasped_object("127.0.0.1", "janinetest1")
        portal.assert_called_once_with("127.0.0.1", 12000, "set_grasped_object", {"object": "janinetest1"})

    def test_failed_setter_accepts_valid_matching_state_readback(self):
        replies = [{"result": {"result": False, "error": "duplicate request"}},
                   {"result": {"result": True, "grasped_object": "janinetest1"}}]
        with mock.patch.object(examples, "call_method", side_effect=replies) as portal:
            examples.set_active_grasped_object("127.0.0.1", "janinetest1")
        self.assertEqual(mock.call("127.0.0.1", 12000, "get_state", {}, timeout=5,
                                   open_timeout=5, close_timeout=0.2), portal.call_args_list[1])

    def test_malformed_setter_and_readback_raise_runtime_error(self):
        for setter in (None, [], {}, {"result": []}, {"result": True}, {"result": {"result": "true"}}):
            for state in (None, {"result": []}, {"result": {"grasped_object": "janinetest1"}},
                          {"result": {"result": False, "grasped_object": "janinetest1"}},
                          {"result": {"result": "true", "grasped_object": "janinetest1"}},
                          {"result": {"result": True, "grasped_object": "other"}}):
                with self.subTest(setter=setter, state=state), \
                        mock.patch.object(examples, "call_method", side_effect=[setter, state]), \
                        self.assertRaises(RuntimeError):
                    examples.set_active_grasped_object("127.0.0.1", "janinetest1")

    def test_malformed_setter_can_only_succeed_with_valid_matching_readback(self):
        with mock.patch.object(examples, "call_method", side_effect=[
            {"result": []}, {"result": {"result": True, "grasped_object": "janinetest1"}},
        ]):
            examples.set_active_grasped_object("127.0.0.1", "janinetest1")


if __name__ == "__main__":
    unittest.main()
