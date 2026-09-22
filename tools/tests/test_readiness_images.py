"""Candidate checks must never run deployment services or access robot networks."""
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from deployment_readiness.common import CommandResult, Context
from deployment_readiness.images import _evaluate, collect

IMAGE_ID = "sha256:" + "a" * 64
SOURCE_HELPER = Path(__file__).resolve().parents[2] / "docker/ros2/start_model_broadcaster.sh"
INSTALLED_HELPER = "/usr/local/bin/start_model_broadcaster.sh"


def script_facts(name):
    source = SOURCE_HELPER.parent / name
    return {"exists": True, "executable": True, "readable": True,
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}



def control_facts():
    return {
        "packages": {
            "controller_manager": {"prefix": "/ws/install/controller_manager", "version": "4.47.0"},
            "franka_bringup": {"prefix": "/ws/install/franka_bringup", "version": "0.1.0"},
        },
        "sync_binary_support": True,
        "gripper_recovery": {"read_failure_guard": True,
                             "launch": {"respawn": True, "respawn_delay": 2.0,
                                        "respawn_max_retries": 5}},
        "files": {
            **{"/usr/local/bin/" + name: script_facts(name)
               for name in ("start_control.sh", "check_control_ready.sh")},
            "/ws/install/controller_manager/lib/controller_manager/ros2_control_node": {
                "exists": True, "executable": True},
            "/entrypoint.sh": {"exists": True, "executable": True},
            INSTALLED_HELPER: {"exists": True, "executable": True, "readable": True,
                               "sha256": hashlib.sha256(SOURCE_HELPER.read_bytes()).hexdigest()},
            "/ws/install/franka_bringup/share/franka_bringup/launch/franka.launch.py": {
                "exists": True, "readable": True},
        },
        "plugins": {
            "mios_ros2_control/" + name: {"library": "mios_effort_controller",
                                          "base_class_type": "controller_interface::ControllerInterface"}
            for name in ("MiosEffortController", "MiosRobotModelBroadcaster", "MiosJointPositionController")
        },
        "parameters": {"update_rate": 1000, "hardware_synchronization.expect_blocking_read_write": True,
                       "cpu_affinity": 6, "thread_priority": 80, "lock_memory": True},
        "controller_parameters": {
            "mios_effort_controller": {
                "allow_effort_activation": True, "allow_zero_effort_activation": True,
                "allow_runtime_effort_commands": True, "allow_runtime_actuator_commands": True,
                "allow_runtime_cartesian_actuator_commands": True,
                "robot_state_source": "hardware", "robot_state_safety_enabled": True,
            },
            "mios_joint_position_controller": {
                "allow_position_activation": True, "allow_runtime_joint_position_commands": False,
            },
        },
        "teaching_syntax": True,
        "libraries": {"/ws/install/mios_ros2_control/lib/libmios_effort_controller.so": {
            "exists": True, "returncode": 0, "missing": [],
            "dependencies": {"libcontroller_interface.so": "/ws/install/controller_interface/lib/libcontroller_interface.so"},
        }},
    }


class FakeRunner:
    def __init__(self, facts=None, *, version="0.1.0", arch="amd64", timeout=False, missing=False, error=None):
        self.facts = control_facts() if facts is None else facts
        self.version, self.arch, self.timeout, self.missing = version, arch, timeout, missing
        self.calls = []
        self.error = error
        self.command = ["/usr/local/bin/start_control.sh"]
        self.healthcheck = ["CMD", "/usr/local/bin/check_control_ready.sh"]

    def run(self, argv, timeout=10, input=None):
        self.calls.append((list(argv), timeout, input))
        if argv[:3] == ["docker", "image", "inspect"]:
            if self.missing:
                return CommandResult(1, stderr="No such image")
            return CommandResult(0, json.dumps([{
                "Id": IMAGE_ID, "Os": "linux", "Architecture": self.arch,
                "Config": {"Labels": {"io.mios.core-contract.version": self.version},
                           "Cmd": self.command, "Entrypoint": ["/entrypoint.sh"],
                           "Healthcheck": {"Test": self.healthcheck}},
            }]))
        if argv[:2] == ["docker", "run"]:
            if self.error is not None:
                raise self.error
            if self.timeout:
                return CommandResult(124, stderr="timeout", timed_out=True)
            return CommandResult(0, "MIOS_READINESS_JSON=" + json.dumps(self.facts) + "\n")
        if argv[:3] == ["docker", "rm", "--force"]:
            return CommandResult(0)
        raise AssertionError("Unexpected command: " + repr(argv))


class ImageReadinessTests(unittest.TestCase):
    def setUp(self):
        self.context = Context(Path(__file__).resolve().parents[2], images={"control": "mios-ros2-control:sync447"})

    def find(self, checks, suffix, role="control"):
        return next(c for c in checks if c.id == f"images.{role}.{suffix}")

    def test_candidate_probe_is_isolated_and_uses_inspected_id(self):
        runner = FakeRunner()
        checks = collect(self.context, runner)
        self.assertEqual("PASS", self.find(checks, "controller_manager").status)
        self.assertEqual("PASS", self.find(checks, "startup_helper_digest").status)
        call, timeout, program = next(c for c in runner.calls if c[0][:2] == ["docker", "run"])
        for flag, value in [("--pull", "never"), ("--network", "none"), ("--cap-drop", "ALL"),
                            ("--security-opt", "no-new-privileges"), ("--entrypoint", "/bin/bash")]:
            self.assertEqual(value, call[call.index(flag)+1])
        self.assertIn("--read-only", call)
        self.assertIn(IMAGE_ID, call)
        self.assertNotIn(self.context.images["control"], call)
        self.assertLessEqual(timeout, 60)
        self.assertNotIn("/var/run/docker.sock", str(call))
        self.assertFalse(set(call) & {"--privileged", "--device", "--volume", "-v", "--mount"})
        self.assertNotIn("/entrypoint.sh", str(call))
        self.assertNotIn("ros2 launch", str(call))
        self.assertIn('ast.parse(entry.read_text())', program)

    def test_stale_startup_helper_cannot_pass_in_either_profile(self):
        for profile in ("state-only", "motion"):
            with self.subTest(profile=profile):
                self.context.profile = profile
                facts = control_facts()
                stale_digest = hashlib.sha256(b"old model-only startup\n").hexdigest()
                facts["files"][INSTALLED_HELPER]["sha256"] = stale_digest
                result = self.find(_evaluate("control", facts, self.context), "startup_helper_digest")
                self.assertEqual("FAIL", result.status)
                self.assertEqual(stale_digest, result.details["actual_sha256"])
                self.assertEqual(hashlib.sha256(SOURCE_HELPER.read_bytes()).hexdigest(),
                                 result.details["expected_sha256"])
                self.assertIn("Rebuild", result.remediation)

    def test_stale_wrapper_or_health_probe_fails(self):
        for name in ("start_control.sh", "check_control_ready.sh"):
            with self.subTest(name=name):
                facts = control_facts()
                facts["files"]["/usr/local/bin/" + name]["sha256"] = "stale"
                self.assertEqual("FAIL", self.find(_evaluate("control", facts, self.context),
                                                   name.removesuffix(".sh") + "_digest").status)

    def test_image_must_start_control_and_check_preparation_by_default(self):
        runner = FakeRunner()
        checks = collect(self.context, runner)
        self.assertEqual("PASS", self.find(checks, "startup_command").status)
        self.assertEqual("PASS", self.find(checks, "healthcheck").status)
        runner.command = ["bash"]
        runner.healthcheck = ["NONE"]
        checks = collect(self.context, runner)
        self.assertEqual("FAIL", self.find(checks, "startup_command").status)
        self.assertEqual("FAIL", self.find(checks, "healthcheck").status)

    def test_gripper_requires_patched_driver_and_bounded_retries(self):
        for condition in ("missing", "old_driver", "no_respawn", "no_delay", "unbounded", "read_error"):
            with self.subTest(condition=condition):
                facts = control_facts()
                recovery = facts["gripper_recovery"]
                if condition == "missing":
                    del facts["gripper_recovery"]
                elif condition == "old_driver":
                    recovery["read_failure_guard"] = False
                elif condition == "no_respawn":
                    recovery["launch"]["respawn"] = False
                elif condition == "no_delay":
                    recovery["launch"]["respawn_delay"] = 0.0
                elif condition == "unbounded":
                    recovery["launch"]["respawn_max_retries"] = -1
                else:
                    recovery["error"] = "unreadable launch file"
                self.assertEqual("FAIL", self.find(_evaluate("control", facts, self.context),
                                                   "gripper_recovery").status)
        self.assertEqual("PASS", self.find(_evaluate("control", control_facts(), self.context),
                                           "gripper_recovery").status)

    def test_missing_or_unreadable_installed_helper_cannot_pass_digest_check(self):
        for condition in ("missing_file", "missing_digest", "unreadable", "read_error"):
            with self.subTest(condition=condition):
                facts = control_facts()
                helper = facts["files"][INSTALLED_HELPER]
                if condition == "missing_file":
                    del facts["files"][INSTALLED_HELPER]
                elif condition == "missing_digest":
                    del helper["sha256"]
                elif condition == "unreadable":
                    helper["readable"] = False
                else:
                    helper["sha256_error"] = "Permission denied"
                result = self.find(_evaluate("control", facts, self.context), "startup_helper_digest")
                self.assertEqual("FAIL", result.status)
                self.assertEqual(INSTALLED_HELPER, result.details["installed_path"])

    def test_missing_or_unreadable_repository_helper_is_unknown(self):
        facts = control_facts()
        for error in (FileNotFoundError("source helper missing"), PermissionError("source helper unreadable")):
            with self.subTest(error=type(error).__name__), mock.patch.object(Path, "read_bytes", side_effect=error):
                result = self.find(_evaluate("control", facts, self.context), "startup_helper_digest")
            self.assertEqual("UNKNOWN", result.status)
            self.assertEqual(str(SOURCE_HELPER), result.details["source_path"])
            self.assertIn(str(error), result.details["error"])

    def test_stale_local_image_cannot_pass_from_yaml_setting(self):
        facts = control_facts()
        facts["packages"]["controller_manager"]["version"] = "4.45.2"
        facts["sync_binary_support"] = False
        self.context.images["control"] = "mios-ros2-control:local"
        result = self.find(collect(self.context, FakeRunner(facts)), "controller_manager")
        self.assertEqual("FAIL", result.status)
        self.assertIn("sync447", result.remediation)

    def test_sync_string_true_is_not_boolean_configuration(self):
        facts = control_facts()
        facts["parameters"]["hardware_synchronization.expect_blocking_read_write"] = "true"
        self.assertEqual("FAIL", self.find(_evaluate("control", facts, self.context), "configuration").status)

    def test_wrong_rate_and_cpu_priority_fail(self):
        facts = control_facts()
        facts["parameters"].update(update_rate=2000, cpu_affinity=7, thread_priority=99)
        checks = _evaluate("control", facts, self.context)
        self.assertEqual("FAIL", self.find(checks, "configuration").status)
        self.assertEqual("FAIL", self.find(checks, "cpu_priority").status)

    def test_missing_dependency_and_mixed_interface_overlay_fail(self):
        facts = control_facts()
        lib = next(iter(facts["libraries"].values()))
        lib["missing"] = ["libfranka.so.0.20 => not found"]
        lib["dependencies"]["libcontroller_interface.so"] = "/opt/ros/jazzy/lib/libcontroller_interface.so"
        checks = _evaluate("control", facts, self.context)
        self.assertEqual("FAIL", self.find(checks, "dependencies").status)
        self.assertEqual("FAIL", self.find(checks, "interface_linkage").status)

    def test_timeout_cleans_only_unique_probe_container(self):
        runner = FakeRunner(timeout=True)
        checks = collect(self.context, runner)
        run = next(c[0] for c in runner.calls if c[0][:2] == ["docker", "run"])
        cleanup = next(c[0] for c in runner.calls if c[0][:3] == ["docker", "rm", "--force"])
        name = run[run.index("--name")+1]
        self.assertTrue(name.startswith("mios-readiness-control-"))
        self.assertEqual(["docker", "rm", "--force", name], cleanup)
        self.assertEqual("UNKNOWN", self.find(checks, "probe").status)

    def test_cancel_and_exception_remove_unique_probe_and_propagate(self):
        for error in (KeyboardInterrupt(), RuntimeError("probe runner failed")):
            with self.subTest(exception=type(error).__name__):
                runner = FakeRunner(error=error)
                with self.assertRaises(type(error)) as caught:
                    collect(self.context, runner)
                self.assertIs(error, caught.exception)
                run = next(c[0] for c in runner.calls if c[0][:2] == ["docker", "run"])
                name = run[run.index("--name")+1]
                self.assertTrue(name.startswith("mios-readiness-control-"))
                self.assertEqual(["docker", "rm", "--force", name], runner.calls[-1][0])

    def test_success_also_attempts_cleanup(self):
        runner = FakeRunner()
        collect(self.context, runner)
        self.assertEqual(["docker", "rm", "--force"], runner.calls[-1][0][:3])

    def test_memory_lock_requires_typed_true_in_both_profiles(self):
        for profile in ("state-only", "motion"):
            self.context.profile = profile
            for value in (False, "true", None):
                with self.subTest(profile=profile, value=value):
                    facts = control_facts()
                    facts["parameters"]["lock_memory"] = value
                    checks = _evaluate("control", facts, self.context)
                    self.assertEqual("FAIL", self.find(checks, "lock_memory").status)

    def test_motion_gates_match_learning_preflight(self):
        self.context.profile = "motion"
        self.assertEqual("PASS", self.find(_evaluate("control", control_facts(), self.context), "motion_gates").status)
        expected = control_facts()["controller_parameters"]
        for controller, parameters in expected.items():
            for key, value in parameters.items():
                with self.subTest(controller=controller, parameter=key):
                    facts = control_facts()
                    facts["controller_parameters"][controller][key] = not value if isinstance(value, bool) else "topic"
                    checks = _evaluate("control", facts, self.context)
                    failed = self.find(checks, "motion_gates")
                    self.assertEqual("FAIL", failed.status)
                    self.assertIn(f"{controller}.{key}", failed.details)

    def test_missing_or_string_motion_gate_fails(self):
        self.context.profile = "motion"
        for value in (None, "true"):
            with self.subTest(value=value):
                facts = control_facts()
                if value is None:
                    del facts["controller_parameters"]["mios_effort_controller"]["allow_effort_activation"]
                else:
                    facts["controller_parameters"]["mios_effort_controller"]["allow_effort_activation"] = value
                self.assertEqual("FAIL", self.find(_evaluate("control", facts, self.context), "motion_gates").status)

    def test_state_only_does_not_require_motion_gates(self):
        self.context.profile = "state-only"
        facts = control_facts()
        facts["controller_parameters"] = {}
        checks = _evaluate("control", facts, self.context)
        self.assertFalse(any(check.id.endswith("motion_gates") for check in checks))
        self.assertEqual("PASS", self.find(checks, "configuration").status)
        self.assertEqual("PASS", self.find(checks, "lock_memory").status)

    def test_missing_local_image_never_pulls_or_runs(self):
        runner = FakeRunner(missing=True)
        self.assertEqual("FAIL", self.find(collect(self.context, runner), "local").status)
        self.assertEqual(1, len(runner.calls))

    def test_wrong_architecture_skips_execution(self):
        runner = FakeRunner(arch="arm64")
        self.assertEqual("FAIL", self.find(collect(self.context, runner), "architecture").status)
        self.assertEqual(1, len(runner.calls))

    def test_missing_contract_label_fails(self):
        checks = collect(self.context, FakeRunner(version=None))
        self.assertEqual("FAIL", self.find(checks, "contract").status)

    def test_core_link_to_vendor_sdk_fails_boundary(self):
        facts = {"packages": {"mios_ros2_runtime": {"prefix": "/ws/install/mios_ros2_runtime", "version": "0.1.0"}},
                 "files": {"/opt/mios/install/bin/mios_ros2_core_runtime": {"exists": True, "executable": True}},
                 "libraries": {"core": {"exists": True, "returncode": 0, "missing": [],
                                          "dependencies": {"libfranka.so.0.20": "/usr/lib/libfranka.so.0.20"}}}}
        self.assertEqual("FAIL", self.find(_evaluate("core", facts, self.context), "fci_boundary", "core").status)
        facts["libraries"]["core"]["dependencies"] = {
            "libmios_ros2_runtime_backend.so": "/ws/install/mios_ros2_runtime/lib/libmios_ros2_runtime_backend.so",
            "libfranka_msgs__rosidl_typesupport_cpp.so": "/ws/install/franka_msgs/lib/libfranka_msgs__rosidl_typesupport_cpp.so",
        }
        # ROS message transport is allowed; only the vendor SDK owns FCI.
        self.assertEqual("PASS", self.find(_evaluate("core", facts, self.context), "fci_boundary", "core").status)
        facts["packages"]["mios_ros2_runtime"]["metadata_error"] = "missing symlinked package.xml"
        self.assertEqual("PASS", self.find(_evaluate("core", facts, self.context), "overlay", "core").status)

    def test_missing_control_startup_file_fails(self):
        for path in ("/entrypoint.sh", "/usr/local/bin/start_model_broadcaster.sh",
                     "/ws/install/franka_bringup/share/franka_bringup/launch/franka.launch.py"):
            with self.subTest(path=path):
                facts = control_facts()
                del facts["files"][path]
                failure = self.find(_evaluate("control", facts, self.context), "startup_files")
                self.assertEqual("FAIL", failure.status)
                self.assertIn(path, failure.details)

    def test_startup_helper_must_be_executable_and_launch_readable(self):
        for path, permission in (("/usr/local/bin/start_model_broadcaster.sh", "executable"),
                                 ("/ws/install/franka_bringup/share/franka_bringup/launch/franka.launch.py", "readable")):
            with self.subTest(path=path):
                facts = control_facts()
                facts["files"][path][permission] = False
                self.assertEqual("FAIL", self.find(_evaluate("control", facts, self.context), "startup_files").status)

    def test_core_requires_executable_entrypoint(self):
        facts = {"files": {"/entrypoint.sh": {"exists": True, "executable": True},
                           "/usr/local/bin/start_core.sh": script_facts("start_core.sh")}}
        self.assertEqual("PASS", self.find(_evaluate("core", facts, self.context), "startup_files", "core").status)
        facts["files"]["/entrypoint.sh"]["executable"] = False
        self.assertEqual("FAIL", self.find(_evaluate("core", facts, self.context), "startup_files", "core").status)

    def test_broadcaster_and_position_classes_use_single_checked_library(self):
        self.assertEqual("PASS", self.find(_evaluate("control", control_facts(), self.context), "plugins").status)
        for name in ("MiosRobotModelBroadcaster", "MiosJointPositionController"):
            with self.subTest(plugin=name):
                facts = control_facts()
                del facts["plugins"]["mios_ros2_control/" + name]
                self.assertEqual("FAIL", self.find(_evaluate("control", facts, self.context), "plugins").status)
                facts = control_facts()
                facts["plugins"]["mios_ros2_control/" + name]["library"] = "missing_other_library"
                self.assertEqual("FAIL", self.find(_evaluate("control", facts, self.context), "plugins").status)

    def test_ml_missing_dependency_fails_without_requiring_docker_cli(self):
        facts = {"files": {"/mios_mls/start_interface.py": {"exists": True, "syntax": True}},
                 "taxonomy": True, "imports": {"numpy": True, "websockets": "No module named websockets"},
                 "docker_cli": None}
        checks = _evaluate("ml", facts, self.context)
        self.assertEqual("FAIL", self.find(checks, "python_dependencies", "ml").status)
        self.assertFalse(any(check.id.endswith("docker_cli") for check in checks))


if __name__ == "__main__":
    unittest.main()
