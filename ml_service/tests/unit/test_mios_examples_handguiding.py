"""Offline teaching abort tests; no ROS, Portal, or database connection."""

import contextlib
import importlib.util
import io
from pathlib import Path
import sys
import types
import unittest
from unittest import mock


# Load the deployed teaching source rather than a copied learning-image file.
# Stub its transport import so these tests also run with stdlib unittest alone.
_transport = types.ModuleType("utils.ws_client")
_transport.__all__ = ["call_method", "start_task", "stop_task", "wait_for_task"]
for _name in _transport.__all__:
    setattr(_transport, _name, mock.Mock(side_effect=AssertionError("Unexpected Portal call")))
_source = Path(__file__).resolve().parents[3] / "python" / "mios_examples.py"
_spec = importlib.util.spec_from_file_location("mios_teaching_examples_tested", _source)
examples = importlib.util.module_from_spec(_spec)
with mock.patch.dict(sys.modules, {"utils.ws_client": _transport}):
    _spec.loader.exec_module(examples)


class HandGuidingAbortTests(unittest.TestCase):
    def setUp(self):
        # Server readiness polling is tested separately below.
        for name in ("_wait_for_handguiding_control", "_wait_for_handguiding_stop"):
            patcher = mock.patch.object(examples, name)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_unavailable_portal_blocks_teaching(self):
        with mock.patch.object(examples, "call_method", return_value=None) as portal, \
                mock.patch.object(examples, "start_task") as start:
            with self.assertRaisesRegex(RuntimeError, "Core Portal at 192.0.2.10:12000 is unavailable") as raised:
                examples.teach_insertion("192.0.2.10", "test_object")
        self.assertIn("MIOS_ENABLE_CORE_SCHEDULER=true", str(raised.exception))
        portal.assert_called_once_with("192.0.2.10", 12000, "get_state", {}, timeout=5)
        start.assert_not_called()

    def test_core_state_error_keeps_server_reason_before_teaching(self):
        with mock.patch.object(examples, "call_method", return_value={"result": {
                "result": False, "error": "Robot state is stale"}}), \
                mock.patch.object(examples, "start_task") as start:
            with self.assertRaisesRegex(RuntimeError, "Read Core state failed: Robot state is stale"):
                examples.teach_insertion("127.0.0.1", "test_object")
        start.assert_not_called()

    def _run_teaching(self, input_error=None, start_response=None):
        if start_response is None:
            start_response = {"result": {"result": True, "task_uuid": "teaching-task"}}
        with contextlib.ExitStack() as stack:
            portal = stack.enter_context(mock.patch.object(
                examples, "call_method", return_value={"result": {
                    "result": True, "current_task": "IdleTask", "status": "Idle"}},
            ))
            start = stack.enter_context(mock.patch.object(
                examples, "start_task", return_value=start_response,
            ))
            stop = stack.enter_context(mock.patch.object(
                examples, "stop_task", return_value={"result": {"result": True}},
            ))
            confirm = stack.enter_context(mock.patch("builtins.input", side_effect=input_error))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            with self.assertRaises(RuntimeError) as raised:
                examples.teach_insertion("127.0.0.1", "test_object")

        self.assertEqual([call.args[2] for call in portal.call_args_list], ["get_state", "get_state"])
        start.assert_called_once()
        return raised.exception, stop, confirm

    def test_keyboard_interrupt_stops_task_and_aborts_before_grasp_or_pose_capture(self):
        error, stop, confirm = self._run_teaching(input_error=KeyboardInterrupt())
        self.assertIsInstance(error.__cause__, KeyboardInterrupt)
        stop.assert_called_once_with("127.0.0.1", empty_queue=True, port=12000)
        confirm.assert_called_once()

    def test_eof_stops_task_and_aborts_before_grasp_or_pose_capture(self):
        error, stop, confirm = self._run_teaching(input_error=EOFError())
        self.assertIsInstance(error.__cause__, EOFError)
        stop.assert_called_once_with("127.0.0.1", empty_queue=True, port=12000)
        confirm.assert_called_once()

    def test_rejected_start_aborts_before_operator_confirmation(self):
        error, stop, confirm = self._run_teaching(start_response={"result": {
            "result": False, "task_uuid": "INVALID", "error": "Core task gate is closed",
        }})
        self.assertIn("Core task gate is closed", str(error))
        confirm.assert_not_called()
        stop.assert_not_called()

    def test_missing_start_uuid_aborts_before_operator_confirmation(self):
        error, stop, confirm = self._run_teaching(start_response={"result": {"result": True}})
        self.assertIn("valid task UUID", str(error))
        confirm.assert_not_called()
        stop.assert_called_once_with("127.0.0.1", empty_queue=True, port=12000)

    def test_lost_start_reply_stops_potential_task(self):
        with mock.patch.object(examples, "_require_idle_core"), \
                mock.patch.object(examples, "start_task", side_effect=TimeoutError("reply lost")), \
                mock.patch.object(examples, "stop_task", return_value={"result": {"result": True}}) as stop, \
                mock.patch("builtins.input") as confirm, contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(TimeoutError):
                examples.teach_insertion("127.0.0.1", "test_object")
        stop.assert_called_once_with("127.0.0.1", empty_queue=True, port=12000)
        confirm.assert_not_called()

    def test_normal_confirmation_stops_task_and_returns_success(self):
        success = {"result": {"result": True}}
        with mock.patch.object(examples, "_require_idle_core"), \
                mock.patch.object(examples, "start_task", return_value={"result": {
            "result": True, "task_uuid": "teaching-task",
        }}), mock.patch.object(examples, "stop_task", return_value=success) as stop, \
                mock.patch("builtins.input", return_value=""), \
                contextlib.redirect_stdout(io.StringIO()):
            result = examples.handguiding("127.0.0.1")
        self.assertEqual(result, success)
        stop.assert_called_once_with("127.0.0.1", empty_queue=True, port=12000)


    def test_existing_core_task_blocks_teaching(self):
        with mock.patch.object(examples, "call_method", return_value={"result": {
                "result": True, "current_task": "GenericTask", "status": "Idle"}}), \
                mock.patch.object(examples, "start_task") as start:
            with self.assertRaisesRegex(RuntimeError, "Ctrl\\+C"):
                examples.teach_insertion("127.0.0.1", "test_object")
        start.assert_not_called()



class HandGuidingReadinessTests(unittest.TestCase):
    def state(self, *, active=False, task="IdleTask", status="Idle"):
        return {"result": {"result": True, "control_active": active,
                           "current_task": task, "status": status}}

    def test_prompt_waits_for_core_to_dispatch_control(self):
        replies = [self.state(), self.state(task="GenericTask"),
                   self.state(task="GenericTask", active=True, status="Move")]
        with mock.patch.object(examples, "call_method", side_effect=replies) as portal, \
                mock.patch.object(examples.time, "sleep"):
            examples._wait_for_handguiding_control("core.example")
        self.assertEqual(3, portal.call_count)
        self.assertTrue(all(call.args[:3] == ("core.example", 12000, "get_state")
                            for call in portal.call_args_list))

    def test_old_core_without_readiness_field_is_rejected(self):
        with mock.patch.object(examples, "call_method", return_value={"result": {"result": True}}), \
                self.assertRaisesRegex(RuntimeError, "rebuild the Core image"):
            examples._wait_for_handguiding_control("core.example")

    def test_fault_cannot_enable_guiding(self):
        with mock.patch.object(examples, "call_method", return_value=self.state(status="Reflex")), \
                self.assertRaisesRegex(RuntimeError, "Reflex"):
            examples._wait_for_handguiding_control("core.example")

    def test_failed_activation_times_out_without_confirmation_and_stops_task(self):
        with mock.patch.object(examples, "_require_idle_core"), \
                mock.patch.object(examples, "_wait_for_handguiding_stop"), \
                mock.patch.object(examples, "start_task", return_value={"result": {
                    "result": True, "task_uuid": "teaching-task"}}), \
                mock.patch.object(examples, "stop_task", return_value={"result": {"result": True}}) as stop, \
                mock.patch.object(examples, "call_method", return_value=self.state()), \
                mock.patch.object(examples.time, "monotonic", side_effect=[0, 0, 21]), \
                mock.patch.object(examples.time, "sleep"), \
                mock.patch("builtins.input") as confirm, \
                contextlib.redirect_stdout(io.StringIO()), \
                self.assertRaisesRegex(RuntimeError, "did not acquire"):
            examples.handguiding("core.example")
        confirm.assert_not_called()
        stop.assert_called_once_with("core.example", empty_queue=True, port=12000)

    def test_stop_waits_for_task_and_physical_controller_release(self):
        replies = [self.state(task="GenericTask", active=True, status="Move"),
                   self.state(status="Move"), self.state()]
        with mock.patch.object(examples, "call_method", side_effect=replies) as portal, \
                mock.patch.object(examples.time, "sleep"):
            examples._wait_for_handguiding_stop("core.example")
        self.assertEqual(3, portal.call_count)

    def test_lost_stop_state_blocks_pose_capture(self):
        with mock.patch.object(examples, "call_method", return_value=None), \
                self.assertRaisesRegex(RuntimeError, "Wait for HandGuiding stop failed"):
            examples._wait_for_handguiding_stop("core.example")


class GraspVerificationTests(unittest.TestCase):
    SUCCESS = {"result": {"result": True}}
    METHODS = (["grasp"] + ["get_state"] * 3 + ["teach_object", "get_state", "get_state",
               "move_gripper", "grasp_object"] + ["get_state"] * 4 + ["teach_object"] * 2)

    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
        for name in ("_require_idle_core", "_wait_for_handguiding_control", "_wait_for_handguiding_stop"):
            self.stack.enter_context(mock.patch.object(examples, name))
        self.real_handguiding = examples.handguiding
        self.guide = self.stack.enter_context(mock.patch.object(examples, "handguiding"))
        self.portal = self.stack.enter_context(mock.patch.object(examples, "call_method"))
        self.confirm = self.stack.enter_context(mock.patch("builtins.input"))
        self.sleep = self.stack.enter_context(mock.patch.object(examples.time, "sleep"))

    @staticmethod
    def state(width):
        return {"result": {"result": True, "gripper_width": width}}

    def prepare(self, width=0.022, final_width=None):
        for operation in (self.portal, self.guide, self.confirm, self.sleep):
            operation.reset_mock(side_effect=True)
        self.confirm.return_value = ""
        self.responses = [self.state(width) if method == "get_state" else self.SUCCESS
                          for method in self.METHODS]
        if final_width is not None:
            self.responses[12] = self.state(final_width)
        self.portal.side_effect = self.responses

    def methods(self):
        return [call.args[2] for call in self.portal.call_args_list]

    def assert_no_following_poses(self, last_index):
        self.assertEqual(self.METHODS[:last_index + 1], self.methods())
        self.guide.assert_called_once()
        for call in self.portal.call_args_list:
            if call.args[2] == "teach_object":
                self.assertEqual("test_object", call.args[3]["object"])

    def test_requested_sequence_supports_ordinary_narrow_and_maximum_clearance_widths(self):
        for width, final_width in ((0.04, 0.04), (0.022, 0.022),
                                   (0.000591096, 0.000516), (0.075, 0.075)):
            with self.subTest(width=width):
                self.prepare(width, final_width)

                def confirm(message):
                    # Only the support prompt may occur outside HandGuiding.
                    # Regrasp feedback must proceed to approach teaching
                    # without waiting for another operator response.
                    self.assertEqual(self.METHODS[:6], self.methods())
                    self.assertIn("support", message.lower())
                    self.assertNotIn("Type held", message)
                    return ""

                self.confirm.side_effect = confirm
                examples.teach_insertion("127.0.0.1", "test_object")
                self.assertEqual(self.METHODS, self.methods())
                calls = self.portal.call_args_list
                self.assertEqual({"width": 0.0, "speed": 1.0, "force": 100.0,
                                  "epsilon_inner": 0.002, "epsilon_outer": 0.08}, calls[0].args[3])
                self.assertEqual({"object": "test_object", "width": True, "force": 100.0}, calls[4].args[3])
                self.assertAlmostEqual(width + 0.005, calls[7].args[3]["width"])
                self.assertEqual({"width", "speed"}, set(calls[7].args[3]))
                self.assertEqual(1.0, calls[7].args[3]["speed"])
                self.assertEqual({"object": "test_object", "speed": 1.0}, calls[8].args[3])
                for call in calls:
                    if call.args[2] == "get_state":
                        self.assertEqual(5, call.kwargs["timeout"])
                    elif call.args[2] in ("grasp", "move_gripper", "grasp_object"):
                        self.assertEqual(30, call.kwargs["timeout"])
                self.assertEqual([mock.call(0.55)] * 8, self.sleep.call_args_list)
                self.confirm.assert_called_once()
                self.assertEqual(4, self.guide.call_count)
                self.assertEqual(["test_object_container_approach", "test_object_container"],
                                 [call.args[3]["object"] for call in calls[13:]])

    def test_initial_failed_or_malformed_grasp_never_reads_or_saves(self):
        responses = [None, {}, {"result": None}, {"result": []},
                     {"result": {"result": 1}}, {"result": {"result": "true"}}]
        responses.extend({"result": {"result": False, "error": "Could not grasp.", "gripper_width": width}}
                         for width in (0, 0.000591096, 0.022, 0.04))
        for response in responses:
            with self.subTest(response=response):
                self.prepare()
                self.responses[0] = response
                with self.assertRaises(RuntimeError) as raised:
                    examples.teach_insertion("127.0.0.1", "test_object")
                self.assertIn("no grasp pose was saved", str(raised.exception).lower())
                self.assert_no_following_poses(0)
                self.sleep.assert_not_called()
                self.confirm.assert_not_called()

    @classmethod
    def invalid_feedback(cls):
        responses = [None, {}, {"result": []}, {"result": {"result": False}},
                     {"result": {"result": True}}, {"result": {"result": 1, "gripper_width": 0.022}}]
        responses.extend(cls.state(width) for width in (
            0, -0.001, None, float("nan"), float("inf"), float("-inf"),
            "0.022", True, False, {}, [], 0.081,
        ))
        return responses

    def test_initial_invalid_feedback_blocks_saving_and_opening(self):
        for response in self.invalid_feedback():
            with self.subTest(response=response):
                self.prepare()
                self.responses[1] = response
                with self.assertRaises(RuntimeError):
                    examples.teach_insertion("127.0.0.1", "test_object")
                self.assert_no_following_poses(1)
                self.confirm.assert_not_called()

    def test_initial_detection_returns_settled_width_without_prompting(self):
        self.prepare()
        widths = [0.002, 0.0015, 0.00059, 0.00055, 0.00055]
        self.portal.side_effect = [self.SUCCESS] + [self.state(width) for width in widths]
        self.assertEqual(0.00055, examples._detect_and_verify_grasp_width("127.0.0.1"))
        self.assertEqual(["grasp"] + ["get_state"] * 5, self.methods())
        self.assertEqual([mock.call(0.55)] * 5, self.sleep.call_args_list)
        self.confirm.assert_not_called()

    def test_six_unsettled_samples_abort_initial_detection_without_retry(self):
        for widths in ([0.02, 0.018, 0.016, 0.014, 0.012, 0.01],
                       [0.01, 0.01015, 0.01030, 0.01045, 0.01060, 0.01075]):
            with self.subTest(widths=widths):
                self.prepare()
                self.portal.side_effect = [self.SUCCESS] + [self.state(width) for width in widths]
                with self.assertRaisesRegex(RuntimeError, "did not settle within six"):
                    examples.teach_insertion("127.0.0.1", "test_object")
                self.assertEqual(["grasp"] + ["get_state"] * 6, self.methods())
                self.assertEqual([mock.call(0.55)] * 6, self.sleep.call_args_list)
                self.guide.assert_called_once()
                self.confirm.assert_not_called()

    def test_failed_pose_save_prevents_width_read_opening_and_named_grasp(self):
        self.prepare()
        self.responses[4] = {"result": {"result": False, "error": "database unavailable"}}
        with self.assertRaisesRegex(RuntimeError, "database unavailable"):
            examples.teach_insertion("127.0.0.1", "test_object")
        self.assert_no_following_poses(4)
        self.confirm.assert_not_called()

    def test_post_teaching_width_change_or_invalid_read_blocks_opening(self):
        responses = self.invalid_feedback() + [self.state(0.0217), self.state(0.0223)]
        for response in responses:
            with self.subTest(response=response):
                self.prepare()
                self.responses[5] = response
                with self.assertRaises(RuntimeError) as raised:
                    examples.teach_insertion("127.0.0.1", "test_object")
                self.assert_no_following_poses(5)
                self.confirm.assert_not_called()
                self.assertIn("approach", str(raised.exception).lower())
                self.assertNotIn("no grasp pose was saved", str(raised.exception).lower())

    def test_insufficient_opening_clearance_blocks_before_support_prompt(self):
        for width in (0.0751, 0.08):
            with self.subTest(width=width):
                self.prepare(width)
                with self.assertRaises(RuntimeError):
                    examples.teach_insertion("127.0.0.1", "test_object")
                self.assert_no_following_poses(5)
                self.confirm.assert_not_called()

    def test_support_prompt_interrupt_prevents_opening_after_pose_was_recorded(self):
        for interruption in (KeyboardInterrupt(), EOFError()):
            with self.subTest(interruption=type(interruption).__name__):
                self.prepare()
                self.confirm.side_effect = interruption
                with self.assertRaises(RuntimeError) as raised:
                    examples.teach_insertion("127.0.0.1", "test_object")
                self.assert_no_following_poses(5)
                self.confirm.assert_called_once()
                self.assertIn("approach", str(raised.exception).lower())
                self.assertNotIn("no grasp pose was saved", str(raised.exception).lower())

    def test_nonblank_support_response_aborts_without_opening(self):
        for answer in ("no", "abort", "yes", "supported"):
            with self.subTest(answer=answer):
                self.prepare()
                self.confirm.side_effect = [answer]
                with self.assertRaisesRegex(RuntimeError, "gripper was not opened"):
                    examples.teach_insertion("127.0.0.1", "test_object")
                self.assert_no_following_poses(5)
                self.confirm.assert_called_once()

    def test_feedback_must_remain_valid_and_unchanged_during_support_confirmation(self):
        for response in self.invalid_feedback() + [self.state(0.0217), self.state(0.0223)]:
            with self.subTest(response=response):
                self.prepare()
                self.responses[6] = response
                with self.assertRaises(RuntimeError):
                    examples.teach_insertion("127.0.0.1", "test_object")
                self.assert_no_following_poses(6)
                self.confirm.assert_called_once()
                self.assertEqual([mock.call(0.55)] * 4, self.sleep.call_args_list)

    def test_failed_or_malformed_move_and_named_grasp_never_retry_or_start_approach(self):
        failures = [None, {}, {"result": []}, {"result": {"result": False, "error": "motion rejected"}},
                    {"result": {"result": 1}}, {"result": {"result": "true"}}]
        for index in (7, 8):
            for response in failures:
                with self.subTest(index=index, response=response):
                    self.prepare()
                    self.responses[index] = response
                    with self.assertRaises(RuntimeError) as raised:
                        examples.teach_insertion("127.0.0.1", "test_object")
                    self.assert_no_following_poses(index)
                    self.confirm.assert_called_once()
                    self.assertIn("approach", str(raised.exception).lower())

    def test_invalid_or_changed_final_grasp_feedback_prevents_following_poses(self):
        cases = [(9, response) for response in self.invalid_feedback()]
        cases += [(12, response) for response in self.invalid_feedback() + [self.state(0.0217), self.state(0.0223)]]
        for index, response in cases:
            with self.subTest(index=index, response=response):
                self.prepare()
                self.responses[index] = response
                with self.assertRaises(RuntimeError):
                    examples.teach_insertion("127.0.0.1", "test_object")
                self.assert_no_following_poses(index)
                self.confirm.assert_called_once()

    def test_task_stop_and_operator_prompts_precede_the_corresponding_gripper_commands(self):
        events = []
        self.prepare()

        def start(*args, **kwargs):
            events.append("start")
            return {"result": {"result": True, "task_uuid": "teaching-task"}}

        def confirm(message):
            self.assertNotIn("Type held", message)
            if "support" in message.lower():
                events.append("support_confirmation")
            else:
                events.append("guiding_confirmation")
            return ""

        def stop(*args, **kwargs):
            events.append("stop")
            return self.SUCCESS

        def portal_response(robot, port, method, payload, **kwargs):
            events.append(method)
            if method == "get_state":
                return self.state(0.022)
            self.assertIn(method, ("grasp", "teach_object", "move_gripper", "grasp_object"))
            return self.SUCCESS

        self.confirm.side_effect = confirm
        self.portal.side_effect = portal_response
        self.sleep.side_effect = lambda duration: events.append("feedback_pause")
        with mock.patch.object(examples, "handguiding", self.real_handguiding), \
                mock.patch.object(examples, "start_task", side_effect=start) as starts, \
                mock.patch.object(examples, "stop_task", side_effect=stop) as stops:
            examples.teach_insertion("127.0.0.1", "test_object")

        expected = [
            "start", "guiding_confirmation", "stop", "grasp",
            "feedback_pause", "get_state", "feedback_pause", "get_state", "feedback_pause", "get_state",
            "teach_object", "get_state", "support_confirmation", "feedback_pause", "get_state",
            "move_gripper", "grasp_object", "feedback_pause", "get_state", "feedback_pause", "get_state",
            "feedback_pause", "get_state", "feedback_pause", "get_state", "start",
        ]
        self.assertEqual(expected, events[:len(expected)])
        self.assertEqual(self.METHODS, self.methods())
        self.assertEqual(4, starts.call_count)
        self.assertEqual(4, stops.call_count)
        self.assertEqual(5, self.confirm.call_count)


class AlreadyGraspedTeachingTests(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
        self.stack.enter_context(mock.patch.object(examples, "_require_idle_core"))
        self.stack.enter_context(mock.patch.object(examples, "_wait_for_handguiding_control"))
        self.stack.enter_context(mock.patch.object(examples, "_wait_for_handguiding_stop"))
        self.portal = self.stack.enter_context(mock.patch.object(examples, "call_method"))
        self.start = self.stack.enter_context(mock.patch.object(examples, "start_task", return_value={
            "result": {"result": True, "task_uuid": "teaching-task"},
        }))
        self.stop = self.stack.enter_context(mock.patch.object(examples, "stop_task", return_value={"result": {"result": True}}))
        self.confirm = self.stack.enter_context(mock.patch("builtins.input", return_value=""))
        self.detect = self.stack.enter_context(mock.patch.object(
            examples, "_detect_and_verify_grasp_width", side_effect=AssertionError("Already-held object must not be regrasped")))

    def test_explicit_already_grasped_accepts_submillimetre_width_without_gripper_commands(self):
        width = 0.0005492529016919434
        self.portal.side_effect = [
            {"result": {"result": True, "gripper_width": width}},
            {"result": {"result": True}},
            {"result": {"result": True}},
            {"result": {"result": True}},
        ]
        examples.teach_insertion("127.0.0.1", "janinetest1", already_grasped=True)
        self.assertEqual(["get_state", "teach_object", "teach_object", "teach_object"],
                         [call.args[2] for call in self.portal.call_args_list])
        poses = [call.args[3] for call in self.portal.call_args_list[1:]]
        self.assertEqual([
            {"object": "janinetest1", "width": True, "force": 100.0},
            {"object": "janinetest1_container_approach"},
            {"object": "janinetest1_container"},
        ], poses)
        self.detect.assert_not_called()
        self.assertEqual(4, self.confirm.call_count)
        self.assertEqual(4, self.start.call_count)
        self.assertEqual(4, self.stop.call_count)

    def test_invalid_held_width_or_readback_blocks_all_pose_saves_(self):
        responses = [None, {"result": {"result": False}}]
        responses.extend({"result": {"result": True, "gripper_width": width}}
                         for width in (0, -0.001, None, float("nan"), float("inf"), 0.08107059, "0.0005", True))
        for response in responses:
            with self.subTest(response=response):
                self.portal.reset_mock()
                self.start.reset_mock()
                self.stop.reset_mock()
                self.portal.return_value = response
                with self.assertRaises(RuntimeError) as raised:
                    examples.teach_insertion("127.0.0.1", "janinetest1", already_grasped=True)
                if isinstance(response, dict) and response["result"].get("gripper_width") == 0.08107059:
                    self.assertIn("already_grasped=False", str(raised.exception))
                self.assertEqual(["get_state"], [call.args[2] for call in self.portal.call_args_list])
                self.start.assert_called_once()
                self.stop.assert_called_once()
        self.detect.assert_not_called()

    def test_abort_at_first_held_object_confirmation_reads_no_width_and_saves_no_pose(self):
        for interruption in (KeyboardInterrupt(), EOFError()):
            with self.subTest(interruption=type(interruption).__name__):
                self.start.reset_mock()
                self.stop.reset_mock()
                self.confirm.reset_mock()
                self.confirm.side_effect = interruption
                with self.assertRaises(RuntimeError) as raised:
                    examples.teach_insertion("127.0.0.1", "janinetest1", already_grasped=True)
                self.assertIs(interruption, raised.exception.__cause__)
                self.confirm.assert_called_once()
                self.start.assert_called_once()
                self.stop.assert_called_once_with("127.0.0.1", empty_queue=True, port=12000)
        self.portal.assert_not_called()
        self.detect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
