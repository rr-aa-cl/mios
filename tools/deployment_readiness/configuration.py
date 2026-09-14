"""Inspect the resolved deployment configuration and existing host services."""
import ipaddress
import json
import os
import platform
import re
import shutil
import socket

from .common import Check


def parameters(service):
    """Mirror the inspected image startup scripts' quoted environment inputs."""
    environment = service.get("environment", {})
    command = service.get("command")
    if command == ["/usr/local/bin/start_control.sh"]:
        mapping = {"robot_ip": ("ROBOT_IP", "192.168.4.100"),
                   "load_gripper": ("MIOS_LOAD_GRIPPER", "true")}
        fixed = {"robot_type": "fr3", "controllers_yaml": "/ws/install/mios_ros2_control/share/mios_ros2_control/config/mios_controllers.yaml"}
    elif command == ["/usr/local/bin/start_core.sh"]:
        mapping = {"robot_ip": ("ROBOT_IP", "192.168.4.100"),
                   "database_name": ("MONGO_DB_NAME", "mios"),
                   "database_port": ("MONGO_PORT", "27017"),
                   "robot_configuration": ("ROBOT_CONFIG", "0"),
                   "websocket_port": ("MIOS_WS_PORT", "12000"),
                   "rpc_port": ("MIOS_RPC_PORT", "12001"),
                   "udp_port": ("MIOS_UDP_PORT", "12002"),
                   "enable_core_scheduler": ("MIOS_ENABLE_CORE_SCHEDULER", "true"),
                   "enable_core_task_execution": ("MIOS_ENABLE_CORE_TASK_EXECUTION", "true"),
                   "allow_controller_owned_move_mode": ("MIOS_ALLOW_CONTROLLER_OWNED_MOVE_MODE", "true")}
        fixed = {"allow_robot_parameter_application": "false"}
    else:
        return {}
    # Bash ${NAME:-default} also chooses the default for unset/empty inputs.
    return dict(fixed, **{key: str(environment.get(name) if environment.get(name) not in (None, "") else default)
                          for key, (name, default) in mapping.items()})


def command_shape(service, kind):
    return service.get("command") == {
        "control": ["/usr/local/bin/start_control.sh"],
        "core": ["/usr/local/bin/start_core.sh"],
        "ml": ["python3", "./start_interface.py"],
    }[kind]


def ml_service_ports(service):
    """Mirror start_interface.py's environment defaults without running it."""
    environment = service.get("environment", {})
    ports = []
    for name, default in (("interface_port", 8000), ("mios_port", 12000), ("mongo_port", 27017)):
        value = environment.get(name)
        if value is None:
            value = default
        if type(value) not in (str, int):
            raise ValueError(f"ML {name} must be an integer in 1..65535")
        try:
            port = int(value)
        except ValueError as error:
            raise ValueError(f"ML {name} must be an integer in 1..65535") from error
        if not 1 <= port <= 65535:
            raise ValueError(f"ML {name} must be an integer in 1..65535")
        ports.append(port)
    return tuple(ports)


def planned_ports(context):
    services = context.compose["services"]
    p = parameters(services["mios_ros2_core"])
    ml_port, _, _ = ml_service_ports(services["mios_ml_service"])
    ports = [("tcp", int(p.get("websocket_port", 12000)), "Core Portal"),
             ("tcp", int(p.get("rpc_port", 12001)), "Core RPC"),
             ("udp", int(p.get("udp_port", 12002)), "Core UDP"),
             ("tcp", ml_port, "ML RPC"), ("tcp", ml_port + 1, "ML knowledge RPC")]
    database_port = int(p.get("database_port", 27017))
    if any(not 1 <= port <= 65535 for _, port, _ in ports) or not 1 <= database_port <= 65535:
        raise ValueError("Deployment ports must be integers in 1..65535")
    pairs = [(proto, port) for proto, port, _ in ports] + [("tcp", database_port)]
    if len(pairs) != len(set(pairs)):
        raise ValueError("Core, ML, and Mongo ports collide")
    return ports, database_port


def manager_settings(path):
    """Read only simple manager scalars; reject unsupported YAML forms.

    The authoritative installed YAML is parsed with PyYAML inside the image.
    This intentionally small reader avoids a host-side dependency and never
    guesses when this repository's top-level manager structure changes.
    """
    text = path.read_text()
    block = re.search(r"(?m)^controller_manager:\s*\n((?:[ \t].*\n|\n)*)", text)
    if not block:
        raise ValueError("Missing top-level controller_manager mapping")
    result = {}
    for key in ("cpu_affinity", "thread_priority", "update_rate"):
        matches = re.findall(rf"(?m)^    {key}:\s*(\d+)\s*(?:#.*)?$", block[1])
        if len(matches) != 1:
            raise ValueError(f"Expected one integer controller_manager.{key}")
        result[key] = int(matches[0])
    return result


def limit_covers(value, needed):
    limits = [value.get("soft"), value.get("hard")] if isinstance(value, dict) else [value]
    return all(isinstance(limit, int) and (limit == -1 or limit >= needed) for limit in limits)


def duration_covers(value, seconds):
    if not isinstance(value, str) or not re.fullmatch(r"(?:\d+(?:\.\d+)?(?:ns|us|ms|s|m|h))+", value):
        return False
    units = {"ns": 1e-9, "us": 1e-6, "ms": 1e-3, "s": 1, "m": 60, "h": 3600}
    return sum(float(number) * units[unit] for number, unit in
               re.findall(r"(\d+(?:\.\d+)?)(ns|us|ms|s|m|h)", value)) >= seconds


def validate_compose(context):
    checks = []
    services = context.compose.get("services", {})
    names = ("mios_ros2_control", "mios_ros2_core", "mios_ml_service")
    missing = [name for name in names if name not in services]
    if missing:
        return [Check("compose.services", "FAIL", f"Missing services: {', '.join(missing)}")]
    control, core, ml = (services[name] for name in names)
    profiled = [name for name in names if services[name].get("profiles")]
    checks.append(Check("compose.default_services", "FAIL" if profiled else "PASS",
                        f"Services excluded from plain Compose startup: {', '.join(profiled)}." if profiled else
                        "Control, Core, and ML are included in plain Compose startup.",
                        "Remove service profiles so docker compose up starts the complete stack." if profiled else ""))
    checks.append(Check("compose.integrated_setup", "FAIL" if "mios_ros2_model" in services else "PASS",
                        "Control owns controller preparation; a separate model helper service must be removed."))
    for name, service in zip(names, (control, core, ml)):
        masked = service.get("entrypoint") is not None or any(
            service.get(key) for key in ("volumes", "configs", "secrets", "tmpfs", "volumes_from"))
        loader_env = {"PATH", "LD_PRELOAD", "LD_LIBRARY_PATH", "PYTHONPATH", "PYTHONHOME", "AMENT_PREFIX_PATH",
                      "COLCON_PREFIX_PATH", "BASH_ENV", "ENV"}
        masked = masked or bool(loader_env.intersection(service.get("environment", {})))
        masked = masked or (name == "mios_ml_service" and service.get("working_dir") not in (None, "/mios_mls"))
        checks.append(Check(f"compose.{name}.overrides", "UNKNOWN" if masked else "PASS",
                            f"{name}: mounts, entrypoint, working directory, or loader environment overrides are outside the image probe's coverage." if masked else f"{name}: no runtime overrides replace inspected files or their loader paths.",
                            "Remove overrides or extend the checker to inspect the effective mounted configuration." if masked else ""))
        needs_shared_ipc = name != "mios_ml_service"
        ok = service.get("network_mode") == "host" and (not needs_shared_ipc or service.get("ipc") == "host")
        transport = "host networking and shared IPC" if needs_shared_ipc else "host networking"
        checks.append(Check(f"compose.{name}.transport", "PASS" if ok else "FAIL",
                            f"{name}: {transport} {'configured' if ok else 'required'}",
                            f"Restore {transport} in the deployment service." if not ok else ""))
    dependencies = ml.get("depends_on", {})
    dependency = dependencies.get("mios_ros2_core", {}) if isinstance(dependencies, dict) else {}
    dependency_ok = (isinstance(dependency, dict) and dependency.get("condition") == "service_started"
                     and dependency.get("required", True) is True)
    checks.append(Check("compose.ml_dependency", "PASS" if dependency_ok else "FAIL",
                        "ML must depend on Core startup.",
                        "Set mios_ml_service.depends_on.mios_ros2_core.condition to service_started." if not dependency_ok else ""))
    dependencies = core.get("depends_on", {})
    dependency = dependencies.get("mios_ros2_control", {}) if isinstance(dependencies, dict) else {}
    dependency_ok = (isinstance(dependency, dict) and dependency.get("condition") == "service_healthy"
                     and dependency.get("required", True) is True)
    checks.append(Check("compose.core_dependency", "PASS" if dependency_ok else "FAIL",
                        "Core must wait for Control's completed controller preparation.",
                        "Set mios_ros2_core.depends_on.mios_ros2_control.condition to service_healthy." if not dependency_ok else ""))
    health = control.get("healthcheck", {})
    health_ok = (health.get("test") == ["CMD", "/usr/local/bin/check_control_ready.sh"]
                 and not health.get("disable"))
    checks.append(Check("compose.control_healthcheck", "PASS" if health_ok else "FAIL",
                        "Control readiness must verify completed preparation and a live ROS launch process."))
    grace_ok = duration_covers(control.get("stop_grace_period"), 20) and duration_covers(core.get("stop_grace_period"), 30)
    checks.append(Check("compose.shutdown_grace", "PASS" if grace_ok else "FAIL",
                        "Shutdown must allow Core to release effort control and Control to stop its child processes.",
                        "Set Core stop_grace_period to at least 30s and Control to at least 20s." if not grace_ok else ""))
    caps = {cap.removeprefix("CAP_") for cap in control.get("cap_add", [])}
    limits = control.get("ulimits", {})
    rt_ok = "SYS_NICE" in caps and limit_covers(limits.get("rtprio"), 99)
    memlock = limits.get("memlock")
    mem_ok = memlock == -1 or memlock == {"soft": -1, "hard": -1}
    checks.append(Check("compose.realtime_permissions", "PASS" if rt_ok and mem_ok else "FAIL",
                        "Control requires SYS_NICE, rtprio >= 99, and unlimited memlock.",
                        "Restore the real-time capability and ulimits in the Control service." if not (rt_ok and mem_ok) else ""))
    worker = control.get("environment", {}).get("MIOS_CONTROL_WORKER_CPUS")
    affinity_ok = bool(worker) and command_shape(control, "control") and not control.get("cpuset")
    checks.append(Check("compose.worker_placement", "PASS" if affinity_ok else "FAIL",
                        "Control workers use taskset; the whole Control container must remain unpinned.",
                        "Restore the taskset wrapper and remove any Control service cpuset." if not affinity_ok else ""))
    if worker:
        context.worker_cpus = str(worker)
    context.nonrt_cpus = str(core.get("cpuset", ""))
    placement_ok = bool(context.nonrt_cpus) and str(ml.get("cpuset", "")) == context.nonrt_cpus
    checks.append(Check("compose.nonrt_placement", "PASS" if placement_ok else "FAIL",
                        "Core and ML must use the same explicit non-real-time CPU set.",
                        "Set MIOS_NONRT_CPUS consistently for Core and ML." if not placement_ok else ""))
    domains = {str(s.get("environment", {}).get("ROS_DOMAIN_ID", "0")) for s in (control, core)}
    domain_ok = len(domains) == 1 and all(d.isdigit() and 0 <= int(d) <= 232 for d in domains)
    checks.append(Check("compose.ros_domain", "PASS" if domain_ok else "FAIL",
                        f"ROS domain IDs: {', '.join(sorted(domains))}"))
    shapes_ok = command_shape(control, "control") and command_shape(core, "core") and command_shape(ml, "ml")
    checks.append(Check("compose.command_shape", "PASS" if shapes_ok else "UNKNOWN",
                        "Only the inspected image startup scripts and documented ML command are supported.",
                        "Use the repository startup commands without extra arguments or shell wrappers." if not shapes_ok else ""))
    cp, kp = parameters(control), parameters(core)
    yaml_ok = cp.get("controllers_yaml") == "/ws/install/mios_ros2_control/share/mios_ros2_control/config/mios_controllers.yaml"
    checks.append(Check("compose.controller_yaml", "PASS" if yaml_ok else "FAIL",
                        "Control must launch with the installed MIOS YAML inspected by the image probe."))
    try:
        planned_ports(context)
        checks.append(Check("compose.ports", "PASS", "Planned Core/ML/Mongo ports are valid and distinct."))
    except (ValueError, KeyError, TypeError) as error:
        checks.append(Check("compose.ports", "FAIL", str(error)))
    try:
        _, ml_mios_port, ml_mongo_port = ml_service_ports(ml)
        matching_ports = (ml_mios_port == int(kp.get("websocket_port", 12000))
                          and ml_mongo_port == int(kp.get("database_port", 27017)))
        checks.append(Check("compose.ml_dependency_ports", "PASS" if matching_ports else "FAIL",
                            "ML mios_port and mongo_port must match Core's Portal and database ports.",
                            "Set ML mios_port from MIOS_WS_PORT and mongo_port from MONGO_PORT." if not matching_ports else ""))
    except (ValueError, TypeError) as error:
        checks.append(Check("compose.ml_dependency_ports", "FAIL", str(error)))
    matching_robot = cp.get("robot_ip") == kp.get("robot_ip") == context.robot_ip
    checks.append(Check("compose.robot_ip", "PASS" if matching_robot else "FAIL",
                        f"Control and Core must target {context.robot_ip}."))
    parameter_off = kp.get("allow_robot_parameter_application") == "false"
    checks.append(Check("compose.parameter_application", "PASS" if parameter_off else "FAIL",
                        "Core must explicitly disable parameter application during tasks.",
                        "Use the inspected start_core.sh command, which fixes allow_robot_parameter_application:=false." if not parameter_off else ""))
    task_execution = "true" if context.profile == "motion" else "false"
    gates = {"enable_core_scheduler": "true", "enable_core_task_execution": task_execution,
             "allow_controller_owned_move_mode": task_execution}
    bad_gates = [key for key, expected in gates.items() if kp.get(key) != expected]
    checks.append(Check("compose.task_gates", "PASS" if not bad_gates else "FAIL",
                        f"{context.profile} requires Core scheduler=true for the Portal and task execution/controller-owned Move={task_execution}.",
                        "Set MIOS_ENABLE_CORE_SCHEDULER=true: scheduler=false runs only a construction test and does not open the Portal. "
                        f"Set MIOS_ENABLE_CORE_TASK_EXECUTION={task_execution} and MIOS_ALLOW_CONTROLLER_OWNED_MOVE_MODE={task_execution}." if bad_gates else "",
                        {key: kp.get(key) for key in gates}))
    if context.profile == "motion":
        gripper_ok = cp.get("load_gripper") == "true"
        checks.append(Check("compose.gripper", "PASS" if gripper_ok else "FAIL",
                            "Teaching and insertion learning require the gripper service.",
                            "Set MIOS_LOAD_GRIPPER=true for this deployment." if not gripper_ok else ""))
    return checks


def collect_configuration(context, args, runner):
    checks = []
    try:
        settings = manager_settings(context.repo_root / "ros2_ws/src/mios_ros2_control/config/mios_controllers.yaml")
        context.control_cpu = settings["cpu_affinity"]
        context.controller_priority = settings["thread_priority"]
        if settings["update_rate"] != 1000:
            raise ValueError("The Franka deployment requires update_rate: 1000")
        context.contract_version = json.loads((context.repo_root / "contracts/core-contract.json").read_text())["version"]
        checks.append(Check("config.source", "PASS", "Repository controller settings and Core contract loaded."))
    except (OSError, ValueError, KeyError) as error:
        checks.append(Check("config.source", "UNKNOWN", str(error), "Use an intact repository checkout with the controller config and contract manifest."))
    env = os.environ.copy()
    for key, value in (("MIOS_ROS2_CONTROL_IMAGE", args.control_image),
                       ("MIOS_ROS2_CORE_IMAGE", args.core_image),
                       ("MIOS_ML_SERVICE_IMAGE", args.ml_image), ("ROBOT_IP", args.robot_ip)):
        if value is not None:
            env[key] = value
    result = runner.run(["docker", "compose", "-f", str(args.compose_file), "config", "--format", "json"], timeout=20, env=env)
    if result.returncode:
        checks.append(Check("compose.resolve", "UNKNOWN", result.stderr.strip() or "Could not resolve Compose configuration.",
                            "Install Docker Compose and correct the Compose configuration/environment."))
        return checks
    try:
        context.compose = json.loads(result.stdout)
        services = context.compose["services"]
        context.images = {"control": services["mios_ros2_control"]["image"],
                          "core": services["mios_ros2_core"]["image"],
                          "ml": services["mios_ml_service"]["image"]}
        context.robot_ip = str(ipaddress.IPv4Address(parameters(services["mios_ros2_control"])["robot_ip"]))
        for option, actual in (("control_image", context.images["control"]), ("core_image", context.images["core"]),
                               ("ml_image", context.images["ml"]), ("robot_ip", context.robot_ip)):
            requested = getattr(args, option)
            if requested is not None and requested != actual:
                checks.append(Check(f"compose.override.{option}", "FAIL", f"Requested {requested}, but Compose resolves {actual}.",
                                    "Use the repository's environment substitutions in Compose."))
        checks.append(Check("compose.resolve", "PASS", f"Resolved {args.compose_file.name}; selected image references recorded."))
        checks.extend(validate_compose(context))
    except (ValueError, KeyError, TypeError) as error:
        checks.append(Check("compose.resolve", "FAIL", f"Unsupported or incomplete Compose configuration: {error}"))
    return checks


def collect_docker(context, runner, min_free_gib=2):
    checks = []
    result = runner.run(["docker", "info", "--format", "{{json .}}"], timeout=15)
    if result.returncode:
        return [Check("docker.daemon", "UNKNOWN", result.stderr.strip() or "Cannot query Docker.",
                      "Start Docker and grant this user access to its socket; run the checker again.")], False
    try:
        info = json.loads(result.stdout)
        checks.append(Check("docker.daemon", "PASS", f"Docker {info.get('ServerVersion', 'unknown')} is reachable."))
        context.docker_arch = {"x86_64": "amd64", "aarch64": "arm64"}.get(info.get("Architecture"), info.get("Architecture", "unknown"))
        endpoint = os.getenv("DOCKER_HOST") if not os.getenv("DOCKER_CONTEXT") else None
        if endpoint is None:
            inspected = runner.run(["docker", "context", "inspect", "--format", "{{json .Endpoints.docker.Host}}"])
            endpoint = json.loads(inspected.stdout) if inspected.returncode == 0 else "unknown"
        local = endpoint.startswith("unix://") and info.get("OSType") == "linux" and info.get("KernelVersion") == platform.release()
        checks.append(Check("docker.local_host", "PASS" if local else "FAIL",
                            "Docker must use this Linux host's kernel and a local Unix socket.",
                            "Run the checker directly on the deployment host with its local Docker context." if not local else ""))
        options = info.get("SecurityOptions")
        rootless = isinstance(options, list) and any("rootless" in option for option in options)
        known = isinstance(options, list)
        checks.append(Check("docker.realtime_mode", "UNKNOWN" if not known else "FAIL" if rootless else "PASS",
                            "Rootful Docker is required for this real-time deployment."))
        if local:
            try:
                free = shutil.disk_usage(info["DockerRootDir"]).free / 1024**3
                status = "FAIL" if free < min_free_gib else "WARN" if free < 5 else "PASS"
                checks.append(Check("docker.disk_space", status, f"Docker storage has {free:.1f} GiB free; minimum {min_free_gib:g} GiB.",
                                    "Free Docker storage before deployment; building images may require substantially more space." if status != "PASS" else ""))
            except OSError as error:
                checks.append(Check("docker.disk_space", "UNKNOWN", f"Cannot inspect Docker storage: {error}"))
        return checks, local and known and not rootless
    except (ValueError, KeyError, TypeError, AttributeError) as error:
        checks.append(Check("docker.info", "UNKNOWN", f"Cannot interpret Docker inspection: {error}"))
        return checks, False


def collect_existing(context, runner):
    """Check for deployment conflicts without stopping services or opening FCI."""
    checks = []
    result = runner.run(["docker", "ps", "--format", "{{json .}}"])
    if result.returncode:
        checks.append(Check("deployment.containers", "UNKNOWN", "Cannot enumerate running containers."))
    else:
        containers = []
        try:
            containers = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
            control_name = context.compose.get("services", {}).get("mios_ros2_control", {}).get("container_name", "mios-ros2-control")
            owners = [c.get("Names", "") for c in containers if c.get("Names") == control_name or
                      re.search(r"mios[-_]direct|franka_bringup|ros2[-_]control", c.get("Names", "") + " " + c.get("Image", ""))]
            checks.append(Check("deployment.fci_owner", "FAIL" if owners else "PASS",
                                f"Existing potential FCI owners: {', '.join(owners)}" if owners else "No known FCI-owner container is running.",
                                "Release arm controllers and stop the existing FCI owner through your supervised shutdown procedure before replacement." if owners else ""))
        except (ValueError, TypeError):
            checks.append(Check("deployment.containers", "UNKNOWN", "Cannot parse the running-container inventory."))
    result = runner.run(["ss", "-H", "-tun", "dst", context.robot_ip])
    if result.returncode:
        checks.append(Check("deployment.fci_connection", "UNKNOWN", "Cannot inspect existing robot connections.", "Install iproute2 and rerun on the deployment host."))
    else:
        connected = any(re.search(r":1337\s*(?:$|\s)", line) for line in result.stdout.splitlines())
        checks.append(Check("deployment.fci_connection", "FAIL" if connected else "PASS",
                            "An existing FCI connection to the robot must be released." if connected else "No existing connection to the robot's FCI TCP port was observed.",
                            "Stop the existing FCI client before deploying another owner." if connected else ""))
    try:
        ports, database_port = planned_ports(context)
    except (ValueError, KeyError, TypeError) as error:
        checks.append(Check("deployment.ports", "FAIL", str(error)))
        return checks
    result = runner.run(["ss", "-H", "-lntu"])
    if result.returncode:
        checks.append(Check("deployment.ports", "UNKNOWN", "Cannot inspect listening ports.", "Install iproute2 and rerun."))
    else:
        occupied = set()
        for line in result.stdout.splitlines():
            fields = line.split()
            if len(fields) >= 5 and fields[0] in {"tcp", "udp"}:
                port = fields[4].rsplit(":", 1)[-1]
                if port.isdigit():
                    occupied.add((fields[0], int(port)))
        conflicts = [f"{name} ({proto}/{port})" for proto, port, name in ports if (proto, port) in occupied]
        checks.append(Check("deployment.ports", "FAIL" if conflicts else "PASS",
                            "Ports already occupied: " + ", ".join(conflicts) if conflicts else "Planned Core and ML ports are available.",
                            "Stop the existing services or select nonconflicting ports consistently before deployment." if conflicts else ""))
    try:
        with socket.create_connection(("127.0.0.1", database_port), timeout=1):
            checks.append(Check("deployment.mongo", "PASS", f"Mongo dependency port {database_port} accepts TCP connections (credentials not checked)."))
    except OSError:
        checks.append(Check("deployment.mongo", "FAIL", f"Core needs a Mongo service on localhost:{database_port}.", "Start the separately managed Mongo service before deploying Core."))
    return checks
