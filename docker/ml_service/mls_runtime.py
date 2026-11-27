#!/usr/bin/env python3
"""Start, probe and stop the learning service (MLS) container.

Docker Compose and Kubernetes both use this file from the MLS image:

  mls_runtime.py start   supervise start_interface.py (the image's command)
  mls_runtime.py probe   read-only readiness check
  mls_runtime.py stop    ask the service to cancel learning (preStop hook)

Configuration (environment):
  MIOS_ML_PORT, MIOS_WS_PORT, MONGO_PORT   service, Core Portal, MongoDB ports
  MIOS_NONRT_CPUS             optional: pin the service to these CPUs
  MIOS_STARTUP_WAIT_SECONDS   optional: wait this long for MongoDB and Core
"""

import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
from xmlrpc.client import ServerProxy


MLS_PID_FILE = Path("/run/mios-mls/mls.pid")


def cpu_set(value):
    cpus = set()
    for part in value.split(","):
        bounds = part.strip().split("-")
        if len(bounds) not in (1, 2):
            raise ValueError(f"Invalid CPU list: {value!r}")
        first, last = int(bounds[0]), int(bounds[-1])
        if first < 0 or last < first:
            raise ValueError(f"Invalid CPU list: {value!r}")
        cpus.update(range(first, last + 1))
    if not cpus:
        raise ValueError("CPU list must not be empty")
    return cpus


def pin_cpus(cpus):
    os.sched_setaffinity(0, cpus)
    actual = os.sched_getaffinity(0)
    if actual != cpus:
        raise RuntimeError(
            f"Requested CPUs {sorted(cpus)}, allowed {sorted(actual)}. "
            "Check the node topology and Kubernetes/runtime CPU allocation.")


def check_ports(ports):
    for port in ports:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            pass


def wait_for_ports(ports, timeout):
    if timeout <= 0:
        return
    print(f"Waiting for localhost ports {ports}...", flush=True)
    deadline = time.monotonic() + timeout
    while True:
        try:
            check_ports(ports)
            return
        except OSError:
            if time.monotonic() >= deadline:
                raise RuntimeError(f"Dependencies on localhost ports {ports} are unavailable")
            time.sleep(2)


def process_identity(pid):
    fields = Path(f"/proc/{pid}/stat").read_text().rsplit(") ", 1)[1].split()
    if fields[0] == "Z":
        raise RuntimeError(f"Service process {pid} has exited")
    return int(fields[1]), int(fields[19])  # Parent PID and process start time.


def mls_pid():
    pid, started = map(int, MLS_PID_FILE.read_text().split())
    if pid <= 1 or process_identity(pid) != (1, started):
        raise RuntimeError("MLS process marker does not identify the running service")
    return pid


def check_owned_ports(pid, ports):
    # hostNetwork exposes sockets belonging to other containers too. A plain
    # TCP probe could accept another stack's service while this one starts.
    # Require the actual service process in this PID namespace to own each socket.
    sockets = set()
    for fd in Path(f"/proc/{pid}/fd").iterdir():
        try:
            target = os.readlink(fd)
        except FileNotFoundError:
            continue  # A descriptor can close while we inspect it.
        if target.startswith("socket:[") and target.endswith("]"):
            sockets.add(target[8:-1])
    listening = set()
    for table in (Path("/proc/net/tcp"), Path("/proc/net/tcp6")):
        if not table.exists():
            continue
        for line in table.read_text().splitlines()[1:]:
            fields = line.split()
            if fields[3] == "0A" and fields[9] in sockets:
                listening.add(int(fields[1].rsplit(":", 1)[1], 16))
    if not set(ports).issubset(listening):
        raise RuntimeError(f"Service process {pid} does not own listeners on {ports}")
    check_ports(ports)


def port(name, legacy, default):
    """Read a port; `legacy` is the lower-case name start_interface.py reads."""
    return int(os.environ.get(name) or os.environ.get(legacy) or default)


def start_mls(ports):
    # Python's default SIGTERM disposition is insufficient as namespace PID 1.
    # Keep the existing service as a child and forward signals to its group,
    # including optimizer children. The preStop hook requests a learning stop first.
    child = None
    shutdown_deadline = None

    def signal_group(signum):
        if child is not None:
            try:
                os.killpg(child.pid, signum)
            except ProcessLookupError:
                pass

    def stop(signum, frame):
        nonlocal shutdown_deadline
        if shutdown_deadline is None:
            shutdown_deadline = time.monotonic() + 10
        signal_group(signum)

    previous = {sig: signal.signal(sig, stop) for sig in (signal.SIGTERM, signal.SIGINT)}
    try:
        # start_interface.py takes its ports from these lower-case variables.
        environment = dict(os.environ, interface_port=str(ports["ml"]),
                           mios_port=str(ports["core"]), mongo_port=str(ports["mongo"]))
        child = subprocess.Popen(["python3", "-u", "./start_interface.py"],
                                 start_new_session=True, env=environment)
        MLS_PID_FILE.parent.mkdir(parents=True, exist_ok=True)
        _, started = process_identity(child.pid)
        MLS_PID_FILE.write_text(f"{child.pid} {started}\n")
        if shutdown_deadline is not None:
            signal_group(signal.SIGTERM)
        while True:
            try:
                code = child.wait(timeout=1)
                # An explicit shutdown is a normal exit for the supervisor.
                return 0 if shutdown_deadline is not None else (code if code >= 0 else 128 - code)
            except subprocess.TimeoutExpired:
                if shutdown_deadline is not None and time.monotonic() >= shutdown_deadline:
                    signal_group(signal.SIGKILL)
                    child.wait(timeout=2)
                    return 0
    finally:
        # An initialization error must not leave an unmanaged learning child.
        if child is not None and child.poll() is None:
            signal_group(signal.SIGKILL)
            try:
                child.wait(timeout=2)
            except subprocess.TimeoutExpired:
                print("MLS child did not exit after SIGKILL", file=sys.stderr, flush=True)
        try:
            MLS_PID_FILE.unlink(missing_ok=True)
        except OSError:
            pass
        for sig, handler in previous.items():
            signal.signal(sig, handler)


def main():
    mode = sys.argv[1] if len(sys.argv) == 2 else ""
    ports = {"ml": port("MIOS_ML_PORT", "interface_port", 8000),
             "core": port("MIOS_WS_PORT", "mios_port", 12000),
             "mongo": port("MONGO_PORT", "mongo_port", 27017)}
    if mode == "start":
        if os.environ.get("MIOS_NONRT_CPUS"):
            pin_cpus(cpu_set(os.environ["MIOS_NONRT_CPUS"]))
        wait_for_ports([ports["mongo"], ports["core"]],
                       int(os.environ.get("MIOS_STARTUP_WAIT_SECONDS") or 0))
        return start_mls(ports)
    elif mode == "probe":
        check_owned_ports(mls_pid(), [ports["ml"], ports["ml"] + 1])
    elif mode == "stop":
        # Core and Control are still alive when Kubernetes runs this hook.
        # Bound the RPC so a failed MLS cannot consume the Pod's shutdown grace.
        check_owned_ports(mls_pid(), [ports["ml"]])
        socket.setdefaulttimeout(5)
        with ServerProxy(f"http://127.0.0.1:{ports['ml']}/", allow_none=True) as service:
            if service.stop_service() is False:
                raise RuntimeError("MLS did not acknowledge learning cancellation")
    else:
        raise ValueError("Expected start, probe, or stop")


if __name__ == "__main__":
    # PID 1 must also accept termination while waiting for start-up dependencies.
    signal.signal(signal.SIGTERM, lambda signum, frame: sys.exit(128 + signum))
    try:
        sys.exit(main())
    except (OSError, RuntimeError, ValueError) as error:
        print(f"MLS runtime {sys.argv[1:]}: {error}", file=sys.stderr, flush=True)
        sys.exit(1)
