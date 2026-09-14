"""Read-only checks for the Linux host and the dedicated Franka network link.

Nothing here opens FCI, changes scheduling, or changes a kernel/NIC setting.
Packet timing while a controller is running needs separate supervised validation.
"""
import gzip
import ipaddress
import json
import platform
import re
from pathlib import Path

from .common import Check


def parse_cpu_list(value):
    """Parse Linux CPU-list syntax, rejecting malformed or unreasonable ranges."""
    result = set()
    if not value.strip():
        return result
    for part in value.strip().split(","):
        match = re.fullmatch(r"(\d+)(?:-(\d+))?", part.strip())
        if not match:
            raise ValueError(f"Invalid CPU list: {value!r}")
        first, last = int(match[1]), int(match[2] or match[1])
        if first > last or last > 8191:
            raise ValueError(f"Invalid CPU range: {part!r}")
        result.update(range(first, last + 1))
    return result


def _read(path):
    try:
        return Path(path).read_text().strip()
    except (OSError, UnicodeError):
        return None


def _json_command(runner, command):
    result = runner.run(command, timeout=5)
    if result.returncode:
        return None, result.stderr.strip() or "Command failed"
    try:
        data = json.loads(result.stdout)
        if not isinstance(data, list) or any(not isinstance(item, dict) for item in data):
            raise ValueError("Expected an array of objects")
        return data, ""
    except (ValueError, TypeError) as error:
        return None, f"Unrecognized command output: {error}"


def _kernel_check(context):
    realtime = _read(context.sys_root / "kernel/realtime")
    if realtime in {"0", "1"}:
        enabled = realtime == "1"
    else:
        config_path = context.kernel_config_path or Path(f"/boot/config-{platform.release()}")
        config = _read(config_path)
        if config is None:
            try:
                with gzip.open(context.proc_root / "config.gz", "rt") as stream:
                    config = stream.read(2_000_000)
            except (OSError, EOFError, UnicodeError):
                config = None
        if config is None:
            return Check("host.realtime_kernel", "UNKNOWN", "Cannot verify the running kernel has PREEMPT_RT.",
                         "Expose /sys/kernel/realtime or the running kernel's boot configuration.")
        enabled = bool(re.search(r"^CONFIG_PREEMPT_RT(?:_FULL)?=y$", config, re.MULTILINE))
    return Check("host.realtime_kernel", "PASS" if enabled else "FAIL",
                 "PREEMPT_RT is enabled." if enabled else "The running kernel does not have PREEMPT_RT enabled.",
                 "Boot the commissioned PREEMPT_RT kernel." if not enabled else "")


def _cpu_checks(context):
    root = context.sys_root / "devices/system/cpu"
    checks = []
    try:
        workers = parse_cpu_list(context.worker_cpus)
        nonrt = parse_cpu_list(context.nonrt_cpus)
        if context.control_cpu < 0 or not workers or not nonrt:
            raise ValueError("Controller CPU must be nonnegative and worker/non-RT CPU lists must be nonempty.")
    except (ValueError, TypeError) as error:
        return [Check("host.cpu_configuration", "FAIL", str(error))], set()
    online_text = _read(root / "online")
    try:
        online = parse_cpu_list(online_text) if online_text is not None else set()
    except ValueError:
        online = set()
    requested = workers | nonrt | {context.control_cpu}
    if not online:
        checks.append(Check("host.cpu_online", "UNKNOWN", "Cannot read the online CPU list."))
    else:
        missing = sorted(requested - online)
        checks.append(Check("host.cpu_online", "FAIL" if missing else "PASS",
                            f"Configured CPUs are offline or absent: {missing}." if missing else "Every configured CPU is online.",
                            "Match deployment CPU lists to this host." if missing else ""))
    sibling_text = _read(root / f"cpu{context.control_cpu}/topology/thread_siblings_list")
    try:
        siblings = parse_cpu_list(sibling_text) if sibling_text is not None else set()
    except ValueError:
        siblings = set()
    if context.control_cpu not in siblings:
        checks.append(Check("host.cpu_siblings", "UNKNOWN", "Cannot determine the controller CPU's SMT siblings."))
        reserved = {context.control_cpu}
    else:
        reserved = siblings & online if online else siblings
        overlap = sorted(reserved & (workers | nonrt))
        checks.append(Check("host.cpu_siblings", "FAIL" if overlap else "PASS",
                            f"Worker/non-RT CPU lists share the controller's physical core: {overlap}." if overlap
                            else f"Controller physical core {sorted(reserved)} is excluded from workers and Core/model CPUs.",
                            "Exclude the controller CPU and all online SMT siblings from both CPU lists." if overlap else ""))
    isolation_text = _read(root / "isolated")
    try:
        isolated = parse_cpu_list(isolation_text) if isolation_text is not None else None
    except ValueError:
        isolated = None
    if isolated is None:
        checks.append(Check("host.cpu_isolation", "UNKNOWN", "Cannot verify CPU isolation."))
    else:
        missing = sorted(reserved - isolated)
        checks.append(Check("host.cpu_isolation", "FAIL" if missing else "PASS",
                            f"Controller physical-core CPUs lack scheduler isolation: {missing}." if missing
                            else f"Controller physical-core CPUs {sorted(reserved)} are isolated.",
                            "Apply the host's documented isolcpus/nohz_full/rcu_nocbs boot configuration and reboot." if missing else ""))
    return checks, reserved


def _power_checks(context, reserved):
    root = context.sys_root / "devices/system/cpu"
    issue_status = "FAIL" if context.profile == "motion" else "WARN"
    unknown_status = "UNKNOWN" if context.profile == "motion" else "WARN"
    governors, unknown_governors, idle_risks, unknown_idle = {}, [], [], []
    for cpu in sorted(reserved):
        cpu_root = root / f"cpu{cpu}"
        governor = _read(cpu_root / "cpufreq/scaling_governor")
        if governor is None:
            unknown_governors.append(cpu)
        else:
            governors[str(cpu)] = governor
        states = sorted((cpu_root / "cpuidle").glob("state[0-9]*"))
        if not states:
            cmdline = _read(context.proc_root / "cmdline") or ""
            if "cpuidle.off=1" not in cmdline.split():
                unknown_idle.append(f"cpu{cpu}: no readable idle states")
        for state in states:
            disabled, latency = _read(state / "disable"), _read(state / "latency")
            if disabled == "1":
                continue
            try:
                if disabled != "0" or latency is None:
                    raise ValueError()
                if int(latency) > 1:
                    idle_risks.append(f"cpu{cpu}/{state.name} ({latency} us)")
            except ValueError:
                unknown_idle.append(f"cpu{cpu}/{state.name}: unreadable latency/disable")
    nonperformance = {cpu: value for cpu, value in governors.items() if value != "performance"}
    governor_status = issue_status if nonperformance else unknown_status if unknown_governors else "PASS"
    idle_status = issue_status if idle_risks else unknown_status if unknown_idle else "PASS"
    return [
        Check("host.cpu_governor", governor_status,
              f"Reserved CPU governors: {governors}; unreadable CPUs: {unknown_governors}.",
              "Apply the commissioned performance power policy before motion." if governor_status != "PASS" else "",
              {"governors": governors, "unreadable_cpus": unknown_governors}),
        Check("host.cpu_idle", idle_status,
              f"Enabled idle states above 1 us: {idle_risks}; unreadable: {unknown_idle}.",
              "Apply the commissioned low-latency idle policy before motion; this checker changes no settings." if idle_status != "PASS" else "",
              {"enabled_deep_states": idle_risks, "unreadable": unknown_idle}),
    ]


def _irq_checks(context, runner, interface, interface_root):
    interrupts = _read(context.proc_root / "interrupts") or ""
    irqs = set()
    for line in interrupts.splitlines():
        match = re.match(r"\s*(\d+):", line)
        if match and re.search(r"(?<![\w])" + re.escape(interface) + r"(?:[-\s]|$)", line):
            irqs.add(match[1])
    try:
        irqs.update(path.name for path in (interface_root / "device/msi_irqs").iterdir() if path.name.isdigit())
    except OSError:
        pass
    if not irqs:
        return [Check("host.nic_irq", "UNKNOWN", f"Cannot identify IRQs for {interface}.",
                      "Make /proc/interrupts and the NIC's sysfs device information readable.")]
    affinity, unknown, wrong = {}, [], []
    for irq in sorted(irqs, key=int):
        irq_root = context.proc_root / f"irq/{irq}"
        value = _read(irq_root / "effective_affinity_list")
        if value is None:
            value = _read(irq_root / "smp_affinity_list")
        affinity[irq] = value
        try:
            cpus = parse_cpu_list(value) if value is not None else None
        except ValueError:
            cpus = None
        if cpus is None:
            unknown.append(irq)
        elif cpus != {context.control_cpu}:
            wrong.append(irq)
    affinity_status = "FAIL" if wrong else "UNKNOWN" if unknown else "PASS"
    checks = [Check("host.nic_irq_affinity", affinity_status,
                    f"NIC IRQ CPU affinities: {affinity}.",
                    "Apply tools/pin_franka_nic_irq.sh with the deployment CPU and robot IP." if affinity_status != "PASS" else "",
                    {"affinities": affinity})]
    threads = runner.run(["ps", "-eLo", "tid=,cls=,rtprio=,comm="], timeout=5)
    priorities = {irq: [] for irq in irqs}
    if not threads.returncode:
        for line in threads.stdout.splitlines():
            parts = line.split(None, 3)
            if len(parts) != 4:
                continue
            match = re.match(r"irq/(\d+)-", parts[3])
            if match and match[1] in irqs:
                priorities[match[1]].append({"tid": parts[0], "policy": parts[1], "priority": parts[2]})
    unknown = [irq for irq, values in priorities.items() if not values]
    wrong = []
    for irq, values in priorities.items():
        for value in values:
            try:
                priority = int(value["priority"])
            except ValueError:
                priority = -1
            if value["policy"] != "FF" or priority != context.irq_priority or priority <= context.controller_priority:
                wrong.append(irq)
    status = "FAIL" if wrong else "UNKNOWN" if unknown else "PASS"
    checks.append(Check("host.nic_irq_priority", status,
                        f"NIC IRQ scheduling: {priorities}; required FIFO {context.irq_priority} above controller {context.controller_priority}.",
                        "Verify threaded IRQ visibility and apply the documented IRQ service settings." if status != "PASS" else "",
                        {"threads": priorities}))
    return checks


def _nic_tuning(runner, interface):
    checks = []
    for flag, check_id in (("--show-eee", "eee"), ("--show-coalesce", "coalescing"), ("--show-pause", "pause")):
        result = runner.run(["ethtool", flag, interface], timeout=5)
        output = result.stdout.strip()
        if result.returncode:
            checks.append(Check(f"host.nic_{check_id}", "WARN", f"Cannot inspect NIC {check_id}: {result.stderr.strip() or 'query failed'}.",
                                "Inspect this optional NIC tuning setting with ethtool."))
            continue
        if check_id == "eee":
            good = bool(re.search(r"EEE status:\s*(?:disabled|not supported)", output, re.I))
        elif check_id == "coalescing":
            good = bool(re.search(r"^rx-usecs:\s*0\s*$", output, re.M)) and not re.search(r"Adaptive RX:\s*on|adaptive-rx:\s*on", output, re.I)
        else:
            good = bool(re.search(r"^RX:\s*off\s*$", output, re.M | re.I) and re.search(r"^TX:\s*off\s*$", output, re.M | re.I))
        checks.append(Check(f"host.nic_{check_id}", "PASS" if good else "WARN",
                            f"NIC {check_id} matches the low-latency settings." if good else f"NIC {check_id} is enabled or its disabled setting was not confirmed.",
                            "Review tools/pin_franka_nic_irq.sh and NIC capabilities." if not good else "",
                            {"output": output[:4000]}))
    return checks


def _network_checks(context, runner):
    try:
        ipaddress.IPv4Address(context.robot_ip)
    except ipaddress.AddressValueError:
        return [Check("host.robot_ip", "FAIL", "Robot IP must be a literal IPv4 address.")]
    routes, error = _json_command(runner, ["ip", "-j", "-4", "route", "get", context.robot_ip])
    if not routes:
        return [Check("host.robot_route", "UNKNOWN", f"Cannot determine the robot route: {error or 'no route returned'}.")]
    route = routes[0]
    interface = route.get("dev")
    if not isinstance(interface, str) or not re.fullmatch(r"[\w.:-]+", interface) or interface == "lo" or route.get("gateway") or route.get("type") in {"local", "blackhole", "unreachable", "prohibit"}:
        return [Check("host.robot_route", "FAIL", f"Robot route must use direct Ethernet without a gateway: {route}.",
                      "Connect and route the robot through its dedicated Ethernet interface.")]
    checks = [Check("host.robot_route", "PASS", f"Robot {context.robot_ip} is routed directly through {interface}.", details={"interface": interface, "route": route})]
    root = context.sys_root / f"class/net/{interface}"
    physical = (root / "device").exists() and not (root / "wireless").exists() and _read(root / "type") == "1"
    checks.append(Check("host.nic_physical", "PASS" if physical else "FAIL",
                        f"{interface} is a physical Ethernet interface." if physical else f"{interface} is not identifiable as physical wired Ethernet.",
                        "Use the dedicated robot Ethernet NIC." if not physical else ""))
    defaults, error = _json_command(runner, ["ip", "-j", "-4", "route", "show", "default"])
    if defaults is None:
        checks.append(Check("host.nic_dedicated", "UNKNOWN", f"Cannot inspect default routes: {error}."))
    else:
        shared = any(route.get("dev") == interface for route in defaults)
        checks.append(Check("host.nic_dedicated", "FAIL" if shared else "PASS",
                            "Robot NIC also carries a default route." if shared else "Robot NIC carries no default route; physical link exclusivity still needs site verification.",
                            "Keep general network traffic on a separate interface." if shared else ""))
    values = {name: _read(root / name) for name in ("operstate", "carrier", "speed", "duplex")}
    unknown = any(value is None for value in values.values())
    try:
        fast = int(values["speed"] or "0") >= 1000
    except ValueError:
        fast = False
        unknown = True
    good = values["operstate"] == "up" and values["carrier"] == "1" and fast and values["duplex"] == "full"
    checks.append(Check("host.nic_link", "PASS" if good else "UNKNOWN" if unknown else "FAIL",
                        f"Robot NIC link: {values}.", "Require link up at 1000 Mb/s or faster, full duplex." if not good else "", values))
    checks.extend(_irq_checks(context, runner, interface, root))
    checks.extend(_nic_tuning(runner, interface))
    if context.ping:
        result = runner.run(["ping", "-n", "-I", interface, "-c", "5", "-i", "0.2", "-W", "1", "-w", "4", context.robot_ip], timeout=5)
        loss = re.search(r"([\d.]+)% packet loss", result.stdout)
        reachable = result.returncode == 0 and loss and float(loss[1]) == 0
        status = "PASS" if reachable else "UNKNOWN" if result.returncode in {124, 126, 127} else "FAIL"
        checks.append(Check("host.robot_ping", status,
                            "Five ICMP probes completed without loss; this does not validate FCI timing." if reachable else "Robot ICMP reachability was not confirmed without packet loss.",
                            "Verify robot power/address and the direct network link." if not reachable else "",
                            {"stdout": result.stdout[-2000:], "stderr": result.stderr[-1000:]}))
    else:
        checks.append(Check("host.robot_ping", "WARN", "Robot reachability was explicitly skipped; no packets sent to the robot."))
    return checks


def collect(context, runner):
    """Return host findings; all commands are bounded and have no side effects."""
    checks = [_kernel_check(context)]
    cpu_checks, reserved = _cpu_checks(context)
    checks.extend(cpu_checks)
    if reserved:
        checks.extend(_power_checks(context, reserved))
    checks.extend(_network_checks(context, runner))
    return checks
