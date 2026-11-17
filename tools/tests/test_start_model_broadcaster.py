"""Run the startup shell helper against a fake ROS CLI; no ROS or Docker needed."""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import textwrap
import time
import unittest


SCRIPT = Path(__file__).resolve().parents[2] / "docker/ros2/start_model_broadcaster.sh"
MODEL = "mios_robot_model_broadcaster"
EFFORT = "mios_effort_controller"
POSITION = "mios_joint_position_controller"
TYPES = {
    MODEL: "mios_ros2_control/MiosRobotModelBroadcaster",
    EFFORT: "mios_ros2_control/MiosEffortController",
    POSITION: "mios_ros2_control/MiosJointPositionController",
    "joint_state_broadcaster": "joint_state_broadcaster/JointStateBroadcaster",
    "franka_robot_state_broadcaster": "franka_robot_state_broadcaster/FrankaRobotStateBroadcaster",
}

FAKE_ROS = r'''#!/usr/bin/env python3
import json
import os
from pathlib import Path
import re
import sys
import time

root = Path(os.environ["FAKE_ROS_ROOT"])
config = json.loads((root / "config.json").read_text())
state = json.loads((root / "state.json").read_text())
arguments = sys.argv[1:]
with (root / "calls.jsonl").open("a") as log:
    log.write(json.dumps(arguments) + "\n")

if arguments[:2] == ["control", "list_controllers"]:
    operation, name = "list", ""
elif arguments[:2] == ["control", "load_controller"]:
    operation, name = "load", arguments[2]
elif arguments[:2] == ["control", "set_controller_state"]:
    operation, name = "set", arguments[2]
elif arguments[:2] == ["service", "call"]:
    assert arguments[2].endswith("/configure_controller"), arguments
    assert arguments[3] == "controller_manager_msgs/srv/ConfigureController", arguments
    operation = "configure"
    name = re.fullmatch(r"\{name: '([^']+)'\}", arguments[4])[1]
else:
    raise AssertionError(arguments)

event = operation + ":" + name
if config.get("hang") == event:
    time.sleep(30)
if config.get("fail") == event:
    print("service failed", file=sys.stderr)
    sys.exit(1)
if operation == "list":
    if config.get("malformed"):
        print(config["malformed"] if isinstance(config["malformed"], str) else "unparseable controller response")
    elif not state and config.get("empty_diagnostic"):
        row = "No controllers are currently loaded!"
        print("\033[32m" + row + "\033[0m" if config.get("color") else row)
    else:
        for controller, item in state.items():
            row = f"{controller} {item['type']} {item['state']}"
            print("\033[32m" + row + "\033[0m" if config.get("color") else row)
    sys.exit(0)
if config.get("no_effect") != event:
    if operation == "load":
        state[name] = {"type": config["types"][name], "state": "unconfigured"}
    elif operation == "configure":
        # Model actual configure semantics: never switch an active controller.
        if state[name]["state"] == "unconfigured":
            state[name]["state"] = "inactive"
    elif operation == "set":
        state[name]["state"] = arguments[3]
if config.get("inject_after") == event:
    state[config["injected_name"]] = {
        "type": config["injected_type"], "state": "active"}
(root / "state.json").write_text(json.dumps(state))
print("ok: false" if config.get("no_effect") == event else "ok: true")
'''


class StartupHelperTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        executable = self.root / "ros2"
        executable.write_text(textwrap.dedent(FAKE_ROS))
        executable.chmod(0o755)
        self.config = {"types": TYPES}
        self.state = {}
        self.environment = dict(os.environ, PATH=str(self.root) + os.pathsep + os.environ["PATH"],
                                FAKE_ROS_ROOT=str(self.root), MIOS_CONTROLLER_WAIT_SECONDS="15",
                                MIOS_CONTROLLER_MANAGER="/controller_manager",
                                MIOS_MODEL_BROADCASTER=MODEL)

    def add(self, name, state):
        self.state[name] = {"type": TYPES[name], "state": state}

    def run_helper(self, expected=0):
        (self.root / "config.json").write_text(json.dumps(self.config))
        (self.root / "state.json").write_text(json.dumps(self.state))
        result = subprocess.run(["bash", str(SCRIPT)], env=self.environment,
                                capture_output=True, text=True, timeout=20, check=False)
        if expected == 0:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.state = json.loads((self.root / "state.json").read_text())
        calls_file = self.root / "calls.jsonl"
        calls = [json.loads(line) for line in calls_file.read_text().splitlines()] if calls_file.exists() else []
        self.mutations = [call for call in calls if call[:2] != ["control", "list_controllers"]]
        # Every test enforces that arm activation/deactivation is never requested.
        for call in self.mutations:
            if call[:2] == ["control", "set_controller_state"]:
                self.assertEqual(call[2:4], [MODEL, "active"])
        return result

    def assert_ready(self):
        self.assertEqual(self.state[MODEL]["state"], "active")
        self.assertEqual(self.state[EFFORT]["state"], "inactive")
        self.assertEqual(self.state[POSITION]["state"], "inactive")

    def test_missing_controllers_are_loaded_and_prepared_without_arm_activation(self):
        self.add("joint_state_broadcaster", "active")
        self.add("franka_robot_state_broadcaster", "active")
        self.run_helper()
        self.assert_ready()
        self.assertEqual(sum(call[:2] == ["control", "load_controller"] for call in self.mutations), 3)
        self.assertEqual(sum(call[:2] == ["service", "call"] for call in self.mutations), 3)

    def test_empty_manager_diagnostic_allows_initial_controller_preparation(self):
        self.config.update(empty_diagnostic=True, color=True)
        self.run_helper()
        self.assert_ready()
        self.assertEqual(sum(call[:2] == ["control", "load_controller"] for call in self.mutations), 3)
        self.assertEqual(sum(call[:2] == ["service", "call"] for call in self.mutations), 3)

    def test_near_match_for_empty_manager_diagnostic_is_rejected(self):
        self.config["malformed"] = "No controllers are currently loaded! unexpected response"
        self.run_helper(expected=1)
        self.assertEqual(self.mutations, [])

    def test_unconfigured_controllers_are_configured_without_reloading(self):
        for name in (MODEL, EFFORT, POSITION):
            self.add(name, "unconfigured")
        self.run_helper()
        self.assert_ready()
        self.assertFalse(any(call[:2] == ["control", "load_controller"] for call in self.mutations))

    def test_prepared_controllers_are_idempotent_with_colored_output(self):
        self.add(MODEL, "active")
        self.add(EFFORT, "inactive")
        self.add(POSITION, "inactive")
        self.config["color"] = True
        self.run_helper()
        self.assert_ready()
        self.assertEqual(self.mutations, [])

    def test_inactive_model_is_the_only_controller_activated(self):
        for name in (MODEL, EFFORT, POSITION):
            self.add(name, "inactive")
        self.run_helper()
        self.assert_ready()
        self.assertEqual(self.mutations, [["control", "set_controller_state", MODEL, "active",
                                           "-c", "/controller_manager"]])

    def test_existing_active_arm_owner_blocks_every_mutation(self):
        for name in (EFFORT, POSITION, "another_controller"):
            with self.subTest(name=name):
                self.state = {name: {"type": TYPES.get(name, "custom/ArmController"), "state": "active"}}
                result = self.run_helper(expected=1)
                self.assertIn("active command controller", result.stderr)
                self.assertEqual(self.mutations, [])

    def test_broadcaster_name_cannot_hide_command_type(self):
        self.state[MODEL] = {"type": "custom/ArmController", "state": "active"}
        self.run_helper(expected=1)
        self.assertEqual(self.mutations, [])

    def test_wrong_target_type_blocks_before_any_mutation(self):
        self.state[POSITION] = {"type": TYPES[EFFORT], "state": "inactive"}
        result = self.run_helper(expected=1)
        self.assertIn("unexpected type", result.stderr)
        self.assertEqual(self.mutations, [])

    def test_model_override_cannot_activate_an_arm_controller(self):
        for name in (EFFORT, POSITION):
            with self.subTest(name=name):
                self.environment["MIOS_MODEL_BROADCASTER"] = name
                self.run_helper(expected=1)
                self.assertEqual(self.mutations, [])

    def test_load_failure_stops_before_model_activation(self):
        self.config["fail"] = "load:" + EFFORT
        result = self.run_helper(expected=1)
        self.assertIn("Failed to load", result.stderr)
        self.assertEqual(len(self.mutations), 1)

    def test_configure_service_failure_stops_before_next_controller(self):
        self.add(EFFORT, "unconfigured")
        self.config["fail"] = "configure:" + EFFORT
        result = self.run_helper(expected=1)
        self.assertIn("Failed to configure", result.stderr)
        self.assertEqual(len(self.mutations), 1)

    def test_success_exit_without_load_effect_is_rejected_by_readback(self):
        self.config["no_effect"] = "load:" + EFFORT
        result = self.run_helper(expected=1)
        self.assertIn("missing, expected inactive", result.stderr)
        self.assertEqual(len(self.mutations), 1)

    def test_success_exit_with_failed_configuration_is_rejected_by_readback(self):
        self.add(EFFORT, "unconfigured")
        self.config["no_effect"] = "configure:" + EFFORT
        result = self.run_helper(expected=1)
        self.assertIn("unconfigured, expected inactive", result.stderr)
        self.assertEqual(len(self.mutations), 1)

    def test_model_activation_needs_observed_active_state(self):
        for name in (MODEL, EFFORT, POSITION):
            self.add(name, "inactive")
        self.config["no_effect"] = "set:" + MODEL
        result = self.run_helper(expected=1)
        self.assertIn("inactive, expected active", result.stderr)

    def test_owner_appearing_after_load_stops_without_deactivating_it(self):
        self.config.update(inject_after="load:" + EFFORT, injected_name=EFFORT,
                           injected_type=TYPES[EFFORT])
        self.run_helper(expected=1)
        self.assertEqual(self.state[EFFORT]["state"], "active")
        self.assertEqual(len(self.mutations), 1)

    def test_final_inspection_rejects_arm_activated_during_model_start(self):
        for name in (MODEL, EFFORT, POSITION):
            self.add(name, "inactive")
        self.config.update(inject_after="set:" + MODEL, injected_name=POSITION,
                           injected_type=TYPES[POSITION])
        self.run_helper(expected=1)
        self.assertEqual(self.state[POSITION]["state"], "active")
        self.assertEqual(len(self.mutations), 1)

    def test_malformed_controller_response_cannot_look_ready(self):
        self.config["malformed"] = True
        self.run_helper(expected=1)
        self.assertEqual(self.mutations, [])

    def test_unavailable_manager_has_a_deadline(self):
        self.config["fail"] = "list:"
        self.environment["MIOS_CONTROLLER_WAIT_SECONDS"] = "1"
        result = self.run_helper(expected=1)
        self.assertIn("Timed out waiting", result.stderr)
        self.assertEqual(self.mutations, [])

    def test_hung_ros_call_is_killed_within_the_deadline(self):
        self.config["hang"] = "list:"
        self.environment["MIOS_CONTROLLER_WAIT_SECONDS"] = "1"
        started = time.monotonic()
        self.run_helper(expected=1)
        self.assertLess(time.monotonic() - started, 4)
        self.assertEqual(self.mutations, [])


if __name__ == "__main__":
    unittest.main()
