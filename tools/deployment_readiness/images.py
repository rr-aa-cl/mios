"""Inspect local candidate images without starting a service or contacting a robot."""
import hashlib
import json
import re
import uuid

from .common import Check

# This program runs only in a disposable, isolated image probe. It reads package
# metadata/configuration and ELF dependencies; it never imports MIOS/vendor code.
PROBE_PROGRAM = r'''
import ast
import glob
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

role = sys.argv[1]
result = {"packages": {}, "files": {}, "libraries": {}, "imports": {}}
def file_info(path):
    p = Path(path)
    result["files"][str(p)] = {"exists": p.is_file(), "executable": os.access(p, os.X_OK),
                              "readable": os.access(p, os.R_OK)}
    return p

def library(path):
    p = file_info(path)
    if not p.is_file():
        result["libraries"][str(p)] = {"exists": False}
        return
    try:
        proc = subprocess.run(["ldd", str(p)], capture_output=True, text=True, timeout=8)
        text = proc.stdout + proc.stderr
        dependencies = {}
        for line in text.splitlines():
            if "=>" in line:
                name, target = line.strip().split("=>", 1)
                dependencies[name.strip()] = target.strip().split(" (")[0]
        result["libraries"][str(p)] = {
            "exists": True, "returncode": proc.returncode,
            "missing": [line.strip() for line in text.splitlines() if "not found" in line],
            "dependencies": dependencies, "diagnostic": text[-2000:] if proc.returncode else "",
        }
    except (OSError, subprocess.TimeoutExpired) as error:
        result["libraries"][str(p)] = {"exists": True, "error": str(error)}

if role in ("control", "core"):
    file_info("/entrypoint.sh")
    from ament_index_python.packages import get_package_prefix
    names = (["controller_manager", "controller_interface", "hardware_interface",
              "joint_state_broadcaster", "forward_command_controller", "franka_hardware", "franka_bringup",
              "franka_semantic_components", "franka_robot_state_broadcaster", "franka_gripper",
              "mios_ros2_control", "mios_ros2_runtime"] if role == "control"
             else ["mios_ros2_runtime", "mios_msgs"])
    for name in names:
        try:
            prefix = get_package_prefix(name)
            result["packages"][name] = {"prefix": prefix}
            try:
                version = ET.parse(Path(prefix)/"share"/name/"package.xml").getroot().findtext("version")
                result["packages"][name]["version"] = version
            except (OSError, ET.ParseError) as error:
                # Core deliberately copies only the transport artifacts. Its
                # package.xml source symlink need not survive this minimal copy.
                result["packages"][name]["metadata_error"] = str(error)
        except Exception as error:
            result["packages"][name] = {"error": str(error)}

if role in ("control", "core"):
    scripts = (["start_model_broadcaster.sh", "start_control.sh", "check_control_ready.sh"]
               if role == "control" else ["start_core.sh"])
    for name in scripts:
        script = file_info("/usr/local/bin/" + name)
        try:
            result["files"][str(script)]["sha256"] = hashlib.sha256(script.read_bytes()).hexdigest()
        except OSError as error:
            result["files"][str(script)]["sha256_error"] = str(error)

if role == "control":
    bringup = result["packages"].get("franka_bringup", {}).get("prefix", "/missing")
    file_info(Path(bringup)/"share/franka_bringup/launch/franka.launch.py")
    gripper = result["packages"].get("franka_gripper", {}).get("prefix", "/missing")
    gripper_launch = file_info(Path(gripper)/"share/franka_gripper/launch/gripper.launch.py")
    gripper_library = file_info(Path(gripper)/"lib/libgripper_server.so")
    result["gripper_recovery"] = {}
    try:
        tree = ast.parse(gripper_launch.read_text())
        for call in ast.walk(tree):
            if not isinstance(call, ast.Call) or not isinstance(call.func, ast.Name) or call.func.id != "Node":
                continue
            keywords = {item.arg: item.value for item in call.keywords}
            executable = keywords.get("executable")
            if isinstance(executable, ast.Constant) and executable.value == "franka_gripper_node":
                result["gripper_recovery"]["launch"] = {
                    name: ast.literal_eval(keywords[name])
                    for name in ("respawn", "respawn_delay", "respawn_max_retries")
                }
        result["gripper_recovery"]["read_failure_guard"] = (
            b"Gripper state read failed; restarting connection" in gripper_library.read_bytes())
    except (OSError, SyntaxError, KeyError, ValueError, TypeError) as error:
        result["gripper_recovery"]["error"] = str(error)
    cm = result["packages"].get("controller_manager", {}).get("prefix", "/missing")
    binary = file_info(Path(cm)/"lib/controller_manager/ros2_control_node")
    result["sync_binary_support"] = (binary.is_file() and
        b"hardware_synchronization.expect_blocking_read_write" in binary.read_bytes())
    library(binary)
    prefix = result["packages"].get("mios_ros2_control", {}).get("prefix", "/missing")
    # All three MIOS classes are exported from this one shared library; they
    # are not separate libmios_robot_model_broadcaster/libmios_joint_position DSOs.
    result["plugins"] = {}
    try:
        manifest = ET.parse(Path(prefix)/"share/mios_ros2_control/mios_controllers.xml").getroot()
        for lib in manifest.iter("library"):
            for plugin in lib.findall("class"):
                result["plugins"][plugin.get("name")] = {
                    "library": lib.get("path"), "base_class_type": plugin.get("base_class_type")}
    except (OSError, ET.ParseError) as error:
        result["plugin_error"] = str(error)
    config = Path(prefix)/"share/mios_ros2_control/config/mios_controllers.yaml"
    result["yaml_path"] = str(config)
    try:
        import yaml
        installed = yaml.safe_load(config.read_text())
        result["parameters"] = installed["controller_manager"]["ros__parameters"]
        result["controller_parameters"] = {
            name: installed.get(name, {}).get("ros__parameters", {})
            for name in ("mios_effort_controller", "mios_joint_position_controller")
        }
    except Exception as error:
        result["yaml_error"] = str(error)
    for package, lib in [
        ("controller_manager", "controller_manager"),
        ("controller_interface", "controller_interface"),
        ("hardware_interface", "hardware_interface"),
        ("joint_state_broadcaster", "joint_state_broadcaster"),
        ("forward_command_controller", "forward_command_controller"),
        ("franka_hardware", "franka_hardware"),
        ("franka_semantic_components", "franka_semantic_components"),
        ("franka_robot_state_broadcaster", "franka_robot_state_broadcaster"),
        ("franka_gripper", "gripper_server"),
        ("mios_ros2_control", "mios_effort_controller"),
    ]:
        base = result["packages"].get(package, {}).get("prefix", "/missing/"+package)
        library(Path(base)/"lib"/("lib"+lib+".so"))
    entry = file_info("/opt/mios/python/mios_examples.py")
    try:
        ast.parse(entry.read_text())
        result["teaching_syntax"] = True
    except (OSError, SyntaxError) as error:
        result["teaching_syntax"] = str(error)

elif role == "core":
    executable = file_info("/opt/mios/install/bin/mios_ros2_core_runtime")
    library(executable)
    prefix = result["packages"].get("mios_ros2_runtime", {}).get("prefix", "/missing")
    library(Path(prefix)/"lib/libmios_ros2_runtime_backend.so")
    # Core imports Control's transport tree, which also contains unused hardware
    # artifacts. Check Core's actual runtime/plugin closure, not every copied ELF.
    for p in sorted(set(glob.glob("/opt/mios/install/lib/lib*.so*"))):
        # Boost bundles include unused components; their standalone dependency
        # lookup differs from the executable/plugin closure. ldd already follows
        # every Boost dependency actually used by the MIOS entry points.
        if not Path(p).name.startswith("libboost_"):
            library(p)

elif role == "ml":
    for name in ("start_interface.py", "example_learning.py", "interface/interface.py",
                 "definitions/templates.py", "utils/ws_client.py"):
        p = file_info(Path("/mios_mls")/name)
        try:
            ast.parse(p.read_text())
            result["files"][str(p)]["syntax"] = True
        except (OSError, SyntaxError) as error:
            result["files"][str(p)]["syntax"] = str(error)
    result["taxonomy"] = bool(glob.glob("/python/taxonomy/default_contexts/*.json"))
    for name in ("numpy", "scipy", "sklearn", "pymongo", "redis", "websockets",
                 "pyDOE3", "deap", "requests", "ifaddr", "skopt"):
        try:
            importlib.import_module(name)
            result["imports"][name] = True
        except Exception as error:
            result["imports"][name] = str(error)
print("MIOS_READINESS_JSON=" + json.dumps(result))
'''


def _version(value):
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)(?:$|[-+])", str(value))
    return tuple(map(int, match.groups())) if match else None


def _arch(value):
    return {"x86_64": "amd64", "aarch64": "arm64"}.get(value, value)


def _overlay(path):
    return str(path).startswith(("/ws/install/", "/ws/build/")) or path == "/ws/install"


def _evaluate(role, facts, context):
    checks = []
    prefix = f"images.{role}"

    def check(name, passed, message, remediation="", details=None):
        checks.append(Check(f"{prefix}.{name}", "PASS" if passed else "FAIL", message,
                            remediation if not passed else "", details or {}))

    packages = facts.get("packages", {})
    if role in ("control", "core"):
        bad = {name: data for name, data in packages.items()
               if data.get("error") or not _overlay(data.get("prefix", ""))}
        check("overlay", bool(packages) and not bad,
              "Selected ROS package overlay", "Rebuild the candidate against the /ws/install overlay.", bad)
        files = facts.get("files", {})
        expected = {"/entrypoint.sh": "executable"}
        scripts = (["start_model_broadcaster.sh", "start_control.sh", "check_control_ready.sh"]
                   if role == "control" else ["start_core.sh"])
        expected.update({"/usr/local/bin/" + name: "executable" for name in scripts})
        if role == "control":
            bringup = packages.get("franka_bringup", {}).get("prefix", "/missing")
            expected[bringup + "/share/franka_bringup/launch/franka.launch.py"] = "readable"
        missing = {path: {"required": permission, "actual": files.get(path, {})}
                   for path, permission in expected.items()
                   if not files.get(path, {}).get("exists") or files[path].get(permission) is not True}
        check("startup_files", not missing,
              "Compose startup entrypoint, launch files, and helpers are installed",
              "Rebuild the candidate with its Dockerfile entrypoint and required bringup/model artifacts.", missing)
    if role in ("control", "core"):
        for name in scripts:
            source = context.repo_root / "docker/ros2" / name
            installed_path = "/usr/local/bin/" + name
            installed = facts.get("files", {}).get(installed_path, {})
            check_name = "startup_helper_digest" if name == "start_model_broadcaster.sh" else name.removesuffix(".sh") + "_digest"
            try:
                digest = hashlib.sha256(source.read_bytes()).hexdigest()
            except OSError as error:
                checks.append(Check(f"{prefix}.{check_name}", "UNKNOWN",
                                    "Cannot verify image startup script against repository source.",
                                    f"Restore a readable {source} before checking the image.",
                                    {"source_path": str(source), "error": str(error)}))
                continue
            check(check_name, installed.get("exists") is True
                  and installed.get("readable") is True and installed.get("sha256") == digest
                  and not installed.get("sha256_error"),
                  f"Installed {name} matches the repository startup script.",
                  f"Rebuild/select the {role} image with the current {source}.",
                  {"source_path": str(source), "installed_path": installed_path,
                   "expected_sha256": digest, "actual_sha256": installed.get("sha256")})
    if role == "control":
        recovery = facts.get("gripper_recovery", {})
        restart = recovery.get("launch", {})
        check("gripper_recovery", recovery.get("read_failure_guard") is True
              and restart.get("respawn") is True
              and restart.get("respawn_delay") == 2.0
              and type(restart.get("respawn_max_retries")) is int
              and restart["respawn_max_retries"] == 5 and not recovery.get("error"),
              "Gripper driver read-failure guard and bounded connection retries are installed",
              "Rebuild Control with docker/ros2/franka_gripper_recovery.patch, then recreate its container.",
              recovery)
        required_plugins = ["mios_ros2_control/" + name for name in
                            ("MiosEffortController", "MiosRobotModelBroadcaster", "MiosJointPositionController")]
        plugins = facts.get("plugins", {})
        bad_plugins = {name: plugins.get(name) for name in required_plugins
                       if plugins.get(name, {}).get("library") != "mios_effort_controller"
                       or plugins.get(name, {}).get("base_class_type") != "controller_interface::ControllerInterface"}
        check("plugins", not bad_plugins,
              "Effort, model broadcaster, and native position plugins use the checked MIOS library",
              "Rebuild mios_ros2_control with its plugin manifest and libmios_effort_controller.so.",
              {"plugins": bad_plugins, "error": facts.get("plugin_error")} if bad_plugins else {})
        cm = packages.get("controller_manager", {})
        version = _version(cm.get("version"))
        check("controller_manager", version is not None and version >= (4, 47, 0)
              and facts.get("sync_binary_support") is True,
              f"Controller manager synchronization support (selected version {cm.get('version', 'unknown')})",
              "Build/select mios-ros2-control:sync447 (controller_manager >= 4.47.0); a stale :local 4.45.2 cannot use this setting.", cm)
        executable = cm.get("prefix", "/missing") + "/lib/controller_manager/ros2_control_node"
        entry = facts.get("files", {}).get(executable, {})
        check("executable", entry.get("exists") and entry.get("executable"),
              "Controller manager executable is installed", "Rebuild the controller-manager overlay.")
        params = facts.get("parameters", {})
        sync = params.get("hardware_synchronization.expect_blocking_read_write",
                          params.get("hardware_synchronization", {}).get("expect_blocking_read_write")
                          if isinstance(params.get("hardware_synchronization"), dict) else None)
        check("configuration", sync is True and type(params.get("update_rate")) is int
              and params["update_rate"] == 1000,
              "Installed controller YAML enables synchronization at 1000 Hz",
              "Rebuild the image with the current mios_controllers.yaml; setting an unsupported parameter is insufficient.",
              {"path": facts.get("yaml_path"), "synchronization": sync,
               "update_rate": params.get("update_rate"), "error": facts.get("yaml_error")})
        check("lock_memory", params.get("lock_memory") is True,
              "Installed controller manager enables memory locking",
              "Rebuild/select the controller YAML with lock_memory: true.",
              {"lock_memory": params.get("lock_memory")})
        if context.profile == "motion":
            requirements = {
                "mios_effort_controller": {
                    "allow_effort_activation": True,
                    "allow_zero_effort_activation": True,
                    "allow_runtime_effort_commands": True,
                    "allow_runtime_actuator_commands": True,
                    "allow_runtime_cartesian_actuator_commands": True,
                    "robot_state_source": "hardware",
                    "robot_state_safety_enabled": True,
                },
                "mios_joint_position_controller": {
                    "allow_position_activation": True,
                    "allow_runtime_joint_position_commands": False,
                },
            }
            installed_controllers = facts.get("controller_parameters", {})
            mismatches = {}
            for controller, wanted in requirements.items():
                actual = installed_controllers.get(controller, {})
                for key, expected in wanted.items():
                    value = actual.get(key)
                    matches = value is expected if isinstance(expected, bool) else value == expected
                    if not matches:
                        mismatches[f"{controller}.{key}"] = {"expected": expected, "actual": value}
            check("motion_gates", not mismatches,
                  "Installed effort and native position hold gates match the learning preflight",
                  "Rebuild/select the commissioned controller configuration expected by example_learning.py.",
                  mismatches)
        affinity = params.get("cpu_affinity")
        check("cpu_priority", affinity in (context.control_cpu, [context.control_cpu])
              and params.get("thread_priority") == context.controller_priority,
              "Installed controller CPU and real-time priority match the deployment",
              "Align the installed YAML with the CPU/priority selected for host IRQ and worker checks.",
              {"cpu_affinity": affinity, "thread_priority": params.get("thread_priority")})
        check("teaching", facts.get("teaching_syntax") is True,
              "Teaching entry script exists and parses", "Rebuild the Control image with python/mios_examples.py.")
    if role in ("control", "core"):
        libs = facts.get("libraries", {})
        bad_libs = {path: data for path, data in libs.items()
                    if not data.get("exists") or data.get("returncode") != 0
                    or data.get("missing") or data.get("error")}
        check("dependencies", bool(libs) and not bad_libs,
              "Expected executable and library dependencies resolve",
              "Rebuild missing plugins and their runtime dependencies together; inspect ldd details.", bad_libs)
        if role == "control":
            interface_names = {"libcontroller_manager.so", "libcontroller_interface.so", "libhardware_interface.so"}
            wrong = {path: {name: target for name, target in data.get("dependencies", {}).items()
                            if name in interface_names and not _overlay(target)}
                     for path, data in libs.items()}
            wrong = {path: links for path, links in wrong.items() if links}
            check("interface_linkage", bool(libs) and not wrong,
                  "Control plugins resolve ros2_control interfaces from the same overlay",
                  "Rebuild all loaded consumers against the pinned overlay; do not mix system 4.45.2 interfaces.", wrong)
        else:
            entry = facts.get("files", {}).get("/opt/mios/install/bin/mios_ros2_core_runtime", {})
            check("executable", entry.get("exists") and entry.get("executable"),
                  "Core runtime executable is installed", "Rebuild the Core runtime image.")
            vendor = {path: {name: target for name, target in data.get("dependencies", {}).items()
                             if re.search(r"(?:^|/)libfranka\.so(?:\.|$)", name, re.IGNORECASE)
                             or re.search(r"(?:^|/)libfranka\.so(?:\.|$)", target, re.IGNORECASE)}
                      for path, data in libs.items()}
            vendor = {path: links for path, links in vendor.items() if links}
            check("fci_boundary", bool(libs) and not bad_libs and not vendor,
                  "Core runtime/plugin dependency closure has no libfranka",
                  "Keep vendor FCI ownership in Control; rebuild Core using only the ROS transport backend.", vendor)
    if role == "ml":
        files = facts.get("files", {})
        bad = {name: data for name, data in files.items()
               if not data.get("exists") or data.get("syntax") is not True}
        check("entry_files", bool(files) and not bad and facts.get("taxonomy") is True,
              "ML entry files parse and default taxonomy is installed",
              "Rebuild ML with the entry scripts and python/taxonomy/default_contexts.", bad)
        imports = facts.get("imports", {})
        failed = {name: status for name, status in imports.items() if status is not True}
        check("python_dependencies", bool(imports) and not failed,
              "ML third-party Python dependencies import",
              "Install/rebuild the ML image's missing or incompatible dependencies.", failed)
    return checks


def collect(context, runner):
    """Inspect selected local images by immutable ID, then run isolated probes."""
    checks = []
    for role in ("control", "core", "ml"):
        ref = context.images.get(role)
        stem = f"images.{role}"
        if not ref:
            checks.append(Check(stem+".local", "FAIL", f"No {role} candidate image selected",
                                "Select an explicit local image tag or digest."))
            continue
        inspected = runner.run(["docker", "image", "inspect", str(ref)], timeout=10)
        if inspected.returncode:
            checks.append(Check(stem+".local", "FAIL", f"Local {role} image unavailable: {ref}",
                                "Build the candidate locally or select an existing image; this check never pulls.",
                                {"error": inspected.stderr.strip(), "timed_out": inspected.timed_out}))
            continue
        try:
            metadata = json.loads(inspected.stdout)[0]
            image_id = metadata["Id"]
            if not re.fullmatch(r"sha256:[0-9a-f]{64}", image_id):
                raise ValueError("Docker inspect did not return an immutable image ID")
        except (ValueError, KeyError, IndexError, TypeError) as error:
            checks.append(Check(stem+".inspect", "UNKNOWN", "Cannot decode image metadata", details={"error": str(error)}))
            continue
        checks.append(Check(stem+".local", "PASS", f"Local {role} image: {ref}",
                            details={"image_id": image_id}))
        compatible = metadata.get("Os") == "linux" and _arch(metadata.get("Architecture")) == _arch(context.docker_arch)
        checks.append(Check(stem+".architecture", "PASS" if compatible else "FAIL",
                            f"Image architecture {metadata.get('Os')}/{metadata.get('Architecture')}; daemon {context.docker_arch}",
                            "Build the image for the Docker daemon's native Linux architecture." if not compatible else ""))
        if role in ("control", "core"):
            labels = (metadata.get("Config") or {}).get("Labels") or {}
            actual = labels.get("io.mios.core-contract.version")
            matches = actual == context.contract_version
            checks.append(Check(stem+".contract", "PASS" if matches else "FAIL",
                                f"Core contract label {actual!r}; required {context.contract_version}",
                                "Rebuild Core and Control with the repository's matching contract version." if not matches else ""))
        config = metadata.get("Config") or {}
        expected_command = {"control": ["/usr/local/bin/start_control.sh"],
                            "core": ["/usr/local/bin/start_core.sh"],
                            "ml": ["python3", "./start_interface.py"]}[role]
        startup_ok = config.get("Cmd") == expected_command
        if role in ("control", "core"):
            startup_ok = startup_ok and config.get("Entrypoint") == ["/entrypoint.sh"]
        checks.append(Check(stem + ".startup_command", "PASS" if startup_ok else "FAIL",
                            "Image default command starts its service independently of Compose.",
                            "Rebuild the image with its service startup command." if not startup_ok else "",
                            {"command": config.get("Cmd"), "entrypoint": config.get("Entrypoint")}))
        if role == "control":
            healthcheck = (config.get("Healthcheck") or {}).get("Test")
            healthy = healthcheck == ["CMD", "/usr/local/bin/check_control_ready.sh"]
            checks.append(Check(stem + ".healthcheck", "PASS" if healthy else "FAIL",
                                "Control image checks successful preparation and launch process readiness.",
                                "Rebuild Control with its readiness healthcheck." if not healthy else "",
                                {"healthcheck": healthcheck}))
        if not compatible:
            continue
        name = "mios-readiness-" + role + "-" + uuid.uuid4().hex[:12]
        setup = "source /opt/ros/jazzy/setup.bash && source /ws/install/setup.bash && " if role != "ml" else ""
        shell = "set -e; " + setup + "exec python3 - " + role
        argv = ["docker", "run", "--pull", "never", "--rm", "--name", name,
                "--network", "none", "--read-only", "--cap-drop", "ALL",
                "--security-opt", "no-new-privileges", "--pids-limit", "64",
                "--env", "BASH_ENV=/dev/null", "--env", "ENV=/dev/null",
                "--env", "PYTHONDONTWRITEBYTECODE=1", "--env", "OPENBLAS_NUM_THREADS=1",
                "--entrypoint", "/bin/bash", "-i", image_id,
                "--noprofile", "--norc", "-c", shell]
        try:
            probed = runner.run(argv, timeout=45, input=PROBE_PROGRAM)
        finally:
            # A stopped Docker client does not stop its container. This also
            # runs on cancellation/exception, which then propagates unchanged.
            # Success usually means --rm already removed this unique name.
            cleaned = runner.run(["docker", "rm", "--force", name], timeout=10)
        if probed.timed_out or probed.returncode:
            checks.append(Check(stem+".probe", "UNKNOWN", "Isolated image probe did not complete",
                                "Inspect the probe error and rerun; no deployment container was started.",
                                {"error": probed.stderr.strip(), "timed_out": probed.timed_out,
                                 "cleanup_returncode": cleaned.returncode, "probe_container": name}))
            continue
        try:
            payloads = [line.partition("=")[2] for line in probed.stdout.splitlines()
                        if line.startswith("MIOS_READINESS_JSON=")]
            facts = json.loads(payloads[-1])
            if not isinstance(facts, dict):
                raise ValueError("Probe facts are not an object")
            checks.extend(_evaluate(role, facts, context))
        except (ValueError, IndexError, TypeError, AttributeError) as error:
            checks.append(Check(stem+".probe", "UNKNOWN", "Image probe returned invalid facts",
                                "Inspect the image's Python/setup installation.", {"error": str(error)}))
    return checks
