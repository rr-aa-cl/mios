"""Regression tests for readiness decisions; no Docker or robot is contacted."""
import copy
import contextlib
import io
import json
from pathlib import Path
import platform
import re
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from deployment_readiness.common import Check, CommandResult, Context, Runner
from deployment_readiness.configuration import (
    collect_configuration, collect_docker, collect_existing, manager_settings,
    parameters, planned_ports, validate_compose,
)
from deployment_readiness.cli import parser, run, summarize

ROOT = Path(__file__).resolve().parents[2]


def deployment():
    common = {"network_mode": "host", "ipc": "host", "environment": {"ROS_DOMAIN_ID": "0"}}
    control = dict(copy.deepcopy(common), image="control:candidate", cap_add=["SYS_NICE"],
                   ulimits={"rtprio": 99, "memlock": -1})
    control["environment"]["MIOS_CONTROL_WORKER_CPUS"] = "0-5,8-19"
    control["environment"].update(ROBOT_IP="192.168.4.100", MIOS_LOAD_GRIPPER="false")
    control["command"] = ["/usr/local/bin/start_control.sh"]
    control["healthcheck"] = {"test": ["CMD", "/usr/local/bin/check_control_ready.sh"]}
    control["stop_grace_period"] = "20s"
    core = dict(copy.deepcopy(common), image="core:candidate", cpuset="0-5,8-19")
    core["command"] = ["/usr/local/bin/start_core.sh"]
    core["stop_grace_period"] = "30s"
    core["environment"].update(ROBOT_IP="192.168.4.100", MIOS_ENABLE_CORE_SCHEDULER="true",
                              MIOS_ENABLE_CORE_TASK_EXECUTION="false",
                              MIOS_ALLOW_CONTROLLER_OWNED_MOVE_MODE="false")
    core["depends_on"] = {"mios_ros2_control": {"condition": "service_healthy", "required": True}}
    ml = {"image": "ml:candidate", "network_mode": "host", "cpuset": "0-5,8-19",
          "command": ["python3", "./start_interface.py"],
          "environment": {"interface_port": "8000", "mios_port": "12000", "mongo_port": "27017"},
          "depends_on": {"mios_ros2_core": {"condition": "service_started", "required": True}}}
    return {"services": {"mios_ros2_control": control, "mios_ros2_core": core,
                         "mios_ml_service": ml}}


class FakeRunner:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def run(self, argv, **kwargs):
        self.calls.append((argv, kwargs))
        return self.responses.pop(0)


class ComposeTests(unittest.TestCase):
    def setUp(self):
        self.context = Context(ROOT, profile="state-only", compose=deployment())
        self.services = self.context.compose["services"]

    def status(self, check_id):
        return {c.id: c.status for c in validate_compose(self.context)}[check_id]

    def test_documented_state_only_configuration_passes(self):
        self.assertTrue(all(c.status == "PASS" for c in validate_compose(self.context)))

    def test_repository_launch_defaults_pass_motion_without_environment_exports(self):
        source = (ROOT / "docker/ros2/docker-compose.runtime.yml").read_text()
        compose = deployment()
        # Read only environment defaults and startup commands, not a YAML parser.
        # Resolve :- defaults directly so the host environment cannot mask drift.
        for service in ("mios_ros2_control", "mios_ros2_core"):
            block = re.search(r"^  " + service + r":\n(.*?)(?=^  \S|\Z)", source, re.M | re.S)
            self.assertIsNotNone(block, service)
            command = re.search(r'^    command: (\[.*\])$', block[1], re.M)
            self.assertIsNotNone(command, service)
            compose["services"][service]["command"] = json.loads(command[1])
            environment = dict(re.findall(r'^      ([A-Z_]+): "?\$\{[A-Z_]+:-([^}]+)\}"?$', block[1], re.M))
            self.assertTrue(environment, service)
            compose["services"][service]["environment"] = environment
            grace = re.search(r'^    stop_grace_period: (\S+)$', block[1], re.M)
            self.assertIsNotNone(grace, service)
            compose["services"][service]["stop_grace_period"] = grace[1]
        self.assertNotIn("  mios_ros2_model:", source)
        context = Context(ROOT, compose=compose)
        self.assertEqual(context.profile, "motion")
        failed = [c for c in validate_compose(context) if c.status != "PASS"]
        self.assertEqual([], failed)

        # Explicit state-only deployments must close the task/move gates while
        # retaining the scheduler that serves the Portal.
        context.profile = "state-only"
        self.assertEqual("FAIL", next(c for c in validate_compose(context) if c.id == "compose.task_gates").status)
        core = compose["services"]["mios_ros2_core"]
        for gate in ("MIOS_ENABLE_CORE_TASK_EXECUTION", "MIOS_ALLOW_CONTROLLER_OWNED_MOVE_MODE"):
            core["environment"][gate] = "false"
        self.assertTrue(all(c.status == "PASS" for c in validate_compose(context)))

    def test_state_only_requires_scheduler_for_portal_even_with_motion_gates_closed(self):
        core = self.services["mios_ros2_core"]
        core["environment"]["MIOS_ENABLE_CORE_SCHEDULER"] = "false"
        check = next(check for check in validate_compose(self.context) if check.id == "compose.task_gates")
        self.assertEqual(check.status, "FAIL")
        self.assertIn("does not open the Portal", check.remediation)
        self.assertIn("MIOS_ENABLE_CORE_SCHEDULER=true", check.remediation)

    def test_state_only_portal_keeps_task_and_move_gates_closed(self):
        core = self.services["mios_ros2_core"]
        original = core["environment"].copy()
        for key in ("MIOS_ENABLE_CORE_TASK_EXECUTION", "MIOS_ALLOW_CONTROLLER_OWNED_MOVE_MODE"):
            with self.subTest(key=key):
                core["environment"] = dict(original, **{key: "true"})
                self.assertEqual(self.status("compose.task_gates"), "FAIL")

    def test_plain_start_requires_ml_and_no_profiled_services(self):
        for name in self.services:
            with self.subTest(name=name):
                self.services[name]["profiles"] = ["optional"]
                self.assertEqual(self.status("compose.default_services"), "FAIL")
                del self.services[name]["profiles"]
        del self.services["mios_ml_service"]
        self.assertEqual(self.status("compose.services"), "FAIL")

    def test_ml_needs_host_network_but_not_shared_ipc(self):
        ml = self.services["mios_ml_service"]
        self.assertNotIn("ipc", ml)
        self.assertEqual(self.status("compose.mios_ml_service.transport"), "PASS")
        ml["network_mode"] = "bridge"
        self.assertEqual(self.status("compose.mios_ml_service.transport"), "FAIL")

    def test_ml_must_use_nonrt_cpus_and_depend_on_core(self):
        ml = self.services["mios_ml_service"]
        ml["cpuset"] = "6-7"
        self.assertEqual(self.status("compose.nonrt_placement"), "FAIL")
        for dependency in ({}, {"condition": "service_completed_successfully"},
                           {"condition": "service_started", "required": False}):
            with self.subTest(dependency=dependency):
                ml["depends_on"]["mios_ros2_core"] = dependency
                self.assertEqual(self.status("compose.ml_dependency"), "FAIL")

    def test_ml_runtime_overrides_are_not_covered_by_image_probe(self):
        ml = self.services["mios_ml_service"]
        for key, value in (("volumes", [{"source": "/tmp/code", "target": "/mios_mls"}]),
                           ("entrypoint", []), ("working_dir", "/other/code")):
            with self.subTest(key=key):
                ml[key] = value
                self.assertEqual(self.status("compose.mios_ml_service.overrides"), "UNKNOWN")
                del ml[key]
        ml["environment"]["PYTHONHOME"] = "/other/python"
        self.assertEqual(self.status("compose.mios_ml_service.overrides"), "UNKNOWN")

    def test_ml_launch_overrides_cannot_bypass_port_inspection(self):
        ml = self.services["mios_ml_service"]
        for command in (["python3", "./start_interface.py", "--interface_port", "8100"],
                        ["bash", "-lc", "python3 ./start_interface.py"],
                        ["python3", "./example_learning.py"]):
            with self.subTest(command=command):
                ml["command"] = command
                self.assertEqual(self.status("compose.command_shape"), "UNKNOWN")

    def test_resolved_ml_ports_determine_listeners_and_must_match_core(self):
        env = self.services["mios_ml_service"]["environment"]
        env["interface_port"] = "8100"
        ports, database = planned_ports(self.context)
        self.assertIn(("tcp", 8100, "ML RPC"), ports)
        self.assertIn(("tcp", 8101, "ML knowledge RPC"), ports)
        self.assertEqual(database, 27017)
        for key, value in (("mios_port", "13000"), ("mongo_port", "27018")):
            with self.subTest(key=key):
                original = env[key]
                env[key] = value
                self.assertEqual(self.status("compose.ml_dependency_ports"), "FAIL")
                env[key] = original
        core = self.services["mios_ros2_core"]
        core["environment"].update(MIOS_WS_PORT="13000", MONGO_PORT="27018")
        env.update(mios_port="13000", mongo_port="27018")
        self.assertEqual(self.status("compose.ml_dependency_ports"), "PASS")

    def test_ml_invalid_and_colliding_ports_block(self):
        env = self.services["mios_ml_service"]["environment"]
        for value in ("invalid", "0", "65535", "12000", "11999", True):
            with self.subTest(value=value):
                env["interface_port"] = value
                self.assertEqual(self.status("compose.ports"), "FAIL")
        env["interface_port"] = "8000"
        env["mongo_port"] = "invalid"
        self.assertEqual(self.status("compose.ml_dependency_ports"), "FAIL")

    def test_alternate_core_command_cannot_bypass_fixed_parameter_gate(self):
        core = self.services["mios_ros2_core"]
        core["command"] = ["bash", "-lc", "exec start_core.sh # ignored flags"]
        self.assertNotIn("allow_robot_parameter_application", parameters(core))
        self.assertEqual(self.status("compose.parameter_application"), "FAIL")

    def test_alternate_controller_yaml_is_not_covered_by_image_probe(self):
        control = self.services["mios_ros2_control"]
        control["command"].append("controllers_yaml:=/tmp/other.yaml")
        self.assertEqual(self.status("compose.controller_yaml"), "FAIL")

    def test_separate_model_helper_cannot_race_control_setup(self):
        self.services["mios_ros2_model"] = {"image": "control:candidate"}
        self.assertEqual(self.status("compose.integrated_setup"), "FAIL")

    def test_core_waits_for_control_preparation_readiness(self):
        for dependency in ({}, {"condition": "service_started"},
                           {"condition": "service_healthy", "required": False}):
            with self.subTest(dependency=dependency):
                self.services["mios_ros2_core"]["depends_on"]["mios_ros2_control"] = dependency
                self.assertEqual(self.status("compose.core_dependency"), "FAIL")

    def test_healthcheck_cannot_be_disabled_or_replaced_by_process_only_check(self):
        control = self.services["mios_ros2_control"]
        for health in ({}, {"disable": True}, {"test": ["CMD", "true"]},
                       {"test": ["CMD", "/usr/local/bin/check_control_ready.sh"], "disable": True}):
            with self.subTest(health=health):
                control["healthcheck"] = health
                self.assertEqual(self.status("compose.control_healthcheck"), "FAIL")

    def test_shutdown_grace_preserves_core_release_and_control_cleanup_budgets(self):
        for service, minimum in (("mios_ros2_control", "20s"), ("mios_ros2_core", "30s")):
            for value in (None, "10s", "19999ms", "invalid", True):
                with self.subTest(service=service, value=value):
                    self.services[service]["stop_grace_period"] = value
                    self.assertEqual(self.status("compose.shutdown_grace"), "FAIL")
            self.services[service]["stop_grace_period"] = minimum
        self.services["mios_ros2_core"]["stop_grace_period"] = "0m30s"
        self.services["mios_ros2_control"]["stop_grace_period"] = "20000ms"
        self.assertEqual(self.status("compose.shutdown_grace"), "PASS")

    def test_duplicate_planned_ports_fail_before_socket_inspection(self):
        core = self.services["mios_ros2_core"]
        core["environment"]["MIOS_RPC_PORT"] = "12000"
        self.assertEqual(self.status("compose.ports"), "FAIL")
        with self.assertRaises(ValueError):
            planned_ports(self.context)

    def test_invalid_port_range_fails(self):
        core = self.services["mios_ros2_core"]
        core["environment"]["MIOS_RPC_PORT"] = "65536"
        self.assertEqual(self.status("compose.ports"), "FAIL")

    def test_matching_invalid_domain_is_not_validated(self):
        for service in self.services.values():
            service["environment"]["ROS_DOMAIN_ID"] = "invalid"
        self.assertEqual(self.status("compose.ros_domain"), "FAIL")

    def test_mounts_and_entrypoint_overrides_prevent_readiness(self):
        for key, value in [("volumes", [{"source": "/tmp/config", "target": "/ws"}]),
                           ("entrypoint", ["/other-entrypoint"]), ("entrypoint", []),
                           ("entrypoint", ""), ("tmpfs", ["/ws"]),
                           ("volumes_from", ["other-container"])]:
            with self.subTest(key=key):
                self.services["mios_ros2_control"][key] = value
                self.assertEqual(self.status("compose.mios_ros2_control.overrides"), "UNKNOWN")
                del self.services["mios_ros2_control"][key]

    def test_loader_environment_cannot_replace_probed_paths(self):
        self.services["mios_ros2_control"]["environment"]["LD_LIBRARY_PATH"] = '/old/libs'
        self.assertEqual(self.status("compose.mios_ros2_control.overrides"), "UNKNOWN")

    def test_outer_shell_must_actually_execute_the_checked_command(self):
        core = self.services["mios_ros2_core"]
        script = core["command"][0]
        for command in (script, ['exec', '/opt/mios/install/bin/mios_ros2_core_runtime', '--ros-args'],
                        ['bash', '-nc', script], ['bash', '-lc', script, 'ignored-argv']):
            with self.subTest(command=command):
                core["command"] = command
                self.assertEqual(self.status("compose.command_shape"), "UNKNOWN")

    def test_shell_wrappers_and_substitutions_are_not_guessed(self):
        core = self.services["mios_ros2_core"]
        original = core["command"][0]
        for changed in ['echo ignored; ' + original, original + ' && echo done',
                        original + ' -p database_name:=$(echo mios)']:
            with self.subTest(changed=changed):
                core["command"] = ["bash", "-lc", changed]
                self.assertEqual(self.status("compose.command_shape"), "UNKNOWN")

    def test_motion_profile_requires_enabled_task_and_gripper_gates(self):
        self.context.profile = "motion"
        self.assertEqual(self.status("compose.task_gates"), "FAIL")
        self.assertEqual(self.status("compose.gripper"), "FAIL")
        core = self.services["mios_ros2_core"]
        for key in ("MIOS_ENABLE_CORE_SCHEDULER", "MIOS_ENABLE_CORE_TASK_EXECUTION", "MIOS_ALLOW_CONTROLLER_OWNED_MOVE_MODE"):
            core["environment"][key] = "true"
        control = self.services["mios_ros2_control"]
        control["environment"]["MIOS_LOAD_GRIPPER"] = "true"
        self.assertTrue(all(c.status == "PASS" for c in validate_compose(self.context)))
        core["environment"]["MIOS_ENABLE_CORE_SCHEDULER"] = "false"
        self.assertEqual(self.status("compose.task_gates"), "FAIL")

    def test_native_lifecycle_allows_a_matching_nonzero_ros_domain(self):
        self.context.profile = "motion"
        for service in self.services.values():
            service["environment"]["ROS_DOMAIN_ID"] = "1"
        self.assertEqual(self.status("compose.ros_domain"), "PASS")
        self.services["mios_ros2_core"]["environment"]["ROS_DOMAIN_ID"] = "2"
        self.assertEqual(self.status("compose.ros_domain"), "FAIL")

    def test_low_soft_realtime_limit_is_rejected(self):
        self.services["mios_ros2_control"]["ulimits"]["rtprio"] = {"soft": 0, "hard": 99}
        self.assertEqual(self.status("compose.realtime_permissions"), "FAIL")

    def test_whole_control_container_must_not_be_pinned(self):
        self.services["mios_ros2_control"]["cpuset"] = "6"
        self.assertEqual(self.status("compose.worker_placement"), "FAIL")

    def test_explicit_override_cannot_be_silently_ignored(self):
        args = parser().parse_args(["--control-image", "required:candidate", "--ml-image", "required:ml",
                                   "--robot-ip", "192.168.4.101"])
        runner = FakeRunner([CommandResult(0, json.dumps(self.context.compose))])
        checks = collect_configuration(self.context, args, runner)
        failed = {c.id for c in checks if c.status == "FAIL"}
        self.assertIn("compose.override.control_image", failed)
        self.assertIn("compose.override.ml_image", failed)
        self.assertIn("compose.override.robot_ip", failed)

    def test_ml_image_override_is_resolved_through_plain_compose(self):
        args = parser().parse_args(["--ml-image", "required:ml"])
        self.services["mios_ml_service"]["image"] = "required:ml"
        runner = FakeRunner([CommandResult(0, json.dumps(self.context.compose))])
        checks = collect_configuration(self.context, args, runner)
        self.assertTrue(all(check.status == "PASS" for check in checks))
        command, options = runner.calls[0]
        self.assertEqual(command, ["docker", "compose", "-f", str(args.compose_file),
                                   "config", "--format", "json"])
        self.assertEqual(options["env"]["MIOS_ML_SERVICE_IMAGE"], "required:ml")
        self.assertEqual(self.context.images["ml"], "required:ml")

    def test_ml_image_without_override_comes_from_resolved_service(self):
        runner = FakeRunner([CommandResult(0, json.dumps(self.context.compose))])
        with patch.dict("os.environ", {"MIOS_ML_SERVICE_IMAGE": "ignored-by-custom-compose:local"}):
            collect_configuration(self.context, parser().parse_args([]), runner)
        self.assertEqual(self.context.images["ml"], "ml:candidate")

    def test_unresolvable_compose_blocks(self):
        runner = FakeRunner([CommandResult(1, stderr="interpolation failed")])
        checks = collect_configuration(self.context, parser().parse_args([]), runner)
        self.assertIn("UNKNOWN", [c.status for c in checks])

    def test_checked_in_controller_settings_are_readable(self):
        settings = manager_settings(ROOT / "ros2_ws/src/mios_ros2_control/config/mios_controllers.yaml")
        self.assertEqual(settings["update_rate"], 1000)


class DockerTests(unittest.TestCase):
    def docker(self, info, endpoint='unix:///var/run/docker.sock'):
        runner = FakeRunner([CommandResult(0, json.dumps(info)), CommandResult(0, json.dumps(endpoint))])
        with patch.dict('os.environ', {}, clear=True), patch('deployment_readiness.configuration.shutil.disk_usage') as usage:
            usage.return_value.free = 10 * 1024**3
            return collect_docker(Context(ROOT), runner)

    def info(self):
        return {"ServerVersion": "29", "OSType": "linux", "KernelVersion": platform.release(),
                "Architecture": "x86_64", "SecurityOptions": ["name=seccomp"], "DockerRootDir": "/var/lib/docker"}

    def test_remote_docker_cannot_validate_local_host(self):
        checks, usable = self.docker(self.info(), 'ssh://other-host')
        self.assertFalse(usable)
        self.assertEqual(next(c for c in checks if c.id == "docker.local_host").status, "FAIL")

    def test_missing_security_metadata_is_unknown(self):
        info = self.info()
        del info['SecurityOptions']
        checks, usable = self.docker(info)
        self.assertFalse(usable)
        self.assertEqual(next(c for c in checks if c.id == "docker.realtime_mode").status, "UNKNOWN")

    def test_rootless_is_not_accepted_for_realtime(self):
        info = self.info()
        info['SecurityOptions'].append('name=rootless')
        checks, usable = self.docker(info)
        self.assertFalse(usable)
        self.assertEqual(next(c for c in checks if c.id == "docker.realtime_mode").status, "FAIL")

    def test_missing_daemon_is_not_ready(self):
        checks, usable = collect_docker(Context(ROOT), FakeRunner([CommandResult(127, stderr="docker missing")]))
        self.assertFalse(usable)
        self.assertEqual(checks[0].status, "UNKNOWN")

    def test_known_running_owner_and_conflicting_ports_block(self):
        context = Context(ROOT, compose=deployment())
        runner = FakeRunner([
            CommandResult(0, json.dumps({"Names": "mios-ros2-control", "Image": "control:candidate"})),
            CommandResult(0, "tcp ESTAB 0 0 192.168.4.1:54321 192.168.4.100:1337\n"),
            CommandResult(0, "tcp LISTEN 0 10 0.0.0.0:12000 0.0.0.0:*\n"),
        ])
        with patch('deployment_readiness.configuration.socket.create_connection'):
            checks = collect_existing(context, runner)
        failed = {c.id for c in checks if c.status == "FAIL"}
        self.assertTrue({'deployment.fci_owner', 'deployment.fci_connection', 'deployment.ports'} <= failed)


class OutcomeTests(unittest.TestCase):
    def test_cli_and_context_default_to_motion_with_explicit_state_only_option(self):
        self.assertEqual(parser().parse_args([]).profile, "motion")
        self.assertEqual(Context(ROOT).profile, "motion")
        self.assertEqual(parser().parse_args(["--profile", "state-only"]).profile, "state-only")

    def test_unknown_and_failed_checks_always_block(self):
        for status in ('UNKNOWN', 'FAIL'):
            self.assertFalse(summarize([Check('check', status, 'message')])[0])

    def test_strict_mode_also_blocks_warnings(self):
        checks = [Check('check', 'WARN', 'message')]
        self.assertTrue(summarize(checks)[0])
        self.assertFalse(summarize(checks, strict=True)[0])

    def test_empty_report_cannot_be_ready(self):
        self.assertFalse(summarize([])[0])

    def test_missing_executable_is_a_bounded_result(self):
        with patch('subprocess.run', side_effect=FileNotFoundError):
            result = Runner().run(['missing-command'])
        self.assertEqual(result.returncode, 127)

    def test_cli_exit_and_json_agree_for_ready_and_unverified_images(self):
        def configured(context, args, runner):
            context.compose = deployment()
            context.images = {"control": "control:candidate", "core": "core:candidate", "ml": "ml:candidate"}
            return [Check("configuration", "PASS", "fixture")]

        for image_status, expected_exit in (("PASS", 0), ("UNKNOWN", 1)):
            with self.subTest(image_status=image_status), tempfile.TemporaryDirectory() as directory:
                report_path = Path(directory) / 'readiness.json'
                args = parser().parse_args(['--quiet', '--json', str(report_path)])
                prefix = 'deployment_readiness.cli.'
                with contextlib.ExitStack() as stack:
                    stack.enter_context(patch(prefix + 'collect_configuration', side_effect=configured))
                    stack.enter_context(patch(prefix + 'collect_docker', return_value=([Check('docker', 'PASS', 'fixture')], True)))
                    stack.enter_context(patch(prefix + 'host.collect', return_value=[Check('host', 'PASS', 'fixture')]))
                    stack.enter_context(patch(prefix + 'collect_existing', return_value=[Check('deployment', 'PASS', 'fixture')]))
                    stack.enter_context(patch(prefix + 'images.collect', return_value=[Check('images', image_status, 'fixture')]))
                    stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
                    code = run(args, runner=FakeRunner([]))
                saved = json.loads(report_path.read_text())
                self.assertEqual(code, expected_exit)
                self.assertEqual(saved['profile'], 'motion')
                self.assertEqual(saved['ready'], expected_exit == 0)
                self.assertEqual(saved['images']['control'], 'control:candidate')
                self.assertTrue(saved['checked_at_utc'])


if __name__ == '__main__':
    unittest.main()
