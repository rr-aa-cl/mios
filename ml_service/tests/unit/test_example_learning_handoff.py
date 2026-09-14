"""Offline ordering and cleanup checks for the compact learning workflow."""

import contextlib
import io
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import example_learning as examples


class LearningWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
        self.events = []
        self.real_object_check = examples.check_taught_insertion_objects
        self.services = self.patch("check_learning_services", side_effect=lambda *a: self.events.append("services"))
        self.objects = self.patch("check_taught_insertion_objects", side_effect=lambda *a: self.events.append("objects"))
        self.factory = self.patch("InsertionFactory")
        self.factory_instance = self.factory.return_value
        self.factory.side_effect = self.new_factory
        self.problem = SimpleNamespace(cost_function=SimpleNamespace())
        self.factory_instance.get_problem_definition.return_value = self.problem
        self.learner = self.patch("SVMLearner")
        for name in ("configure_supervised_motion", "supervised_nominal_knowledge"):
            self.patch(name)
        self.setter = self.patch("set_active_grasped_object", side_effect=lambda *a: self.events.append("set_object"))
        self.learn = self.patch("learn_task", side_effect=lambda *a, **kw: self.events.append("learn"))
        self.stop = self.patch("stop_learning", side_effect=lambda *a: self.events.append("stop"))
        self.portal = self.patch("call_method", side_effect=AssertionError("Unexpected Portal request"))
        self.proxy = self.patch("ServerProxy", side_effect=AssertionError("Unexpected ML connection"))

    def patch(self, name, **kwargs):
        return self.stack.enter_context(mock.patch.object(examples, name, **kwargs))

    def new_factory(self, *args, **kwargs):
        self.events.append("factory")
        return self.factory_instance

    def test_success_checks_readiness_and_objects_before_dispatch(self):
        examples.example_learning("robot.local", "taught_object")
        self.assertEqual([
            "services", "objects", "factory",
            "set_object", "learn", "services",
        ], self.events)
        self.services.assert_has_calls([mock.call("robot.local", 8000), mock.call("robot.local", 8000)])
        self.objects.assert_called_once_with("robot.local", "taught_object")
        self.setter.assert_called_once_with("robot.local", "taught_object")
        self.assertEqual({"Insertable": "taught_object", "Container": "taught_object_container",
                          "Approach": "taught_object_container_approach"}, self.factory.call_args.args[2])
        self.factory_instance.get_problem_definition.assert_called_once_with("taught_object")
        self.assertIs(True, self.learn.call_args.kwargs["wait"])
        self.assertEqual(1, self.learn.call_args.kwargs["n_iterations"])
        self.assertEqual(8000, self.learn.call_args.kwargs["service_port"])
        self.assertEqual(5, self.learner.call_args.args[0])
        self.assertEqual(1, self.learner.call_args.args[1])
        self.assertEqual(1, self.problem.n_variations)
        self.stop.assert_not_called()

    def test_defaults_match_the_taught_name_and_preserve_five_candidates(self):
        examples.example_learning()
        self.objects.assert_called_once_with("127.0.0.1", "janinetest1")
        self.setter.assert_called_once_with("127.0.0.1", "janinetest1")
        self.assertEqual(5, self.learner.call_args.args[0])

    def test_service_failure_prevents_object_lookup_and_all_task_changes(self):
        self.services.side_effect = RuntimeError("ML service unavailable")
        with self.assertRaisesRegex(RuntimeError, "ML service unavailable"):
            examples.example_learning()
        for operation in (self.objects, self.factory, self.learner,
                          self.setter, self.learn, self.stop):
            operation.assert_not_called()

    def test_missing_taught_object_prevents_controller_setter_and_learning_calls(self):
        self.objects.side_effect = self.real_object_check
        self.portal.side_effect = lambda robot, port, method, payload, **kwargs: {
            "result": {"result": False, "error": "object not found"}}
        with self.assertRaisesRegex(RuntimeError, "janinetest1"):
            examples.example_learning()
        self.assertTrue(self.portal.call_args_list)
        self.assertTrue(all(call.args[2] == "download_object_context" for call in self.portal.call_args_list))
        for operation in (self.factory, self.learner, self.setter, self.learn, self.stop, self.proxy):
            operation.assert_not_called()


    def test_factory_failure_does_not_dispatch_learning(self):
        self.factory.side_effect = RuntimeError("invalid problem context")
        with self.assertRaisesRegex(RuntimeError, "invalid problem context"):
            examples.example_learning()
        self.setter.assert_not_called()
        self.learn.assert_not_called()
        self.stop.assert_not_called()


    def test_setter_failure_does_not_dispatch_or_stop_learning(self):
        failure = RuntimeError("cannot select grasped object")
        self.setter.side_effect = failure
        with self.assertRaises(RuntimeError) as raised:
            examples.example_learning()
        self.assertIs(failure, raised.exception)
        self.learn.assert_not_called()
        self.stop.assert_not_called()

    def test_interrupt_or_lost_dispatch_reply_stops_learning(self):
        for failure in (KeyboardInterrupt(), ConnectionError("dispatch response lost")):
            with self.subTest(failure=type(failure).__name__):
                self.events.clear()
                self.stop.reset_mock()

                def dispatch(*args, **kwargs):
                    self.events.append("learn")
                    raise failure

                self.learn.side_effect = dispatch
                with self.assertRaises(type(failure)) as raised:
                    examples.example_learning()
                self.assertIs(failure, raised.exception)
                self.assertEqual(["learn", "stop"], self.events[-2:])
                self.stop.assert_called_once_with("127.0.0.1")

    def test_incomplete_post_dispatch_state_stops_learning(self):
        self.services.side_effect = [None, RuntimeError("ML worker is still busy")]
        with self.assertRaisesRegex(RuntimeError, "ML worker is still busy"):
            examples.example_learning()
        self.stop.assert_called_once_with("127.0.0.1")
        self.assertEqual("stop", self.events[-1])

    def test_stop_failure_is_reported(self):
        self.learn.side_effect = KeyboardInterrupt()

        def stop_failed(*args):
            self.events.append("stop")
            raise RuntimeError("could not confirm ML stopped")

        self.stop.side_effect = stop_failed
        with self.assertRaisesRegex(RuntimeError, "could not confirm ML stopped"):
            examples.example_learning()
        self.assertEqual("stop", self.events[-1])


if __name__ == "__main__":
    unittest.main()
