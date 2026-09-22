#!/usr/bin/env python3
"""Kubernetes startup and read-only probes; no teaching or gripper commands."""

import fcntl
import os
from pathlib import Path
import resource
import signal
import socket
import subprocess
import sys
import time
from xmlrpc.client import ServerProxy


MLS_PID_FILE = Path("/run/mios-k8s/mls.pid")


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


def wait_for_ports(ports, timeout=180):
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
    # TCP probe could accept the old Compose stack while this service starts.
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


def start_mls():
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
        child = subprocess.Popen(["python3", "-u", "./start_interface.py"], start_new_session=True)
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


def start_control():
    # Capabilities are granted only to Control by the manifest. Kubernetes has
    # no Docker-style ulimits field; set limits before exec'ing the image entrypoint.
    resource.setrlimit(resource.RLIMIT_RTPRIO, (99, 99))
    resource.setrlimit(resource.RLIMIT_MEMLOCK, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
    cpus = cpu_set(os.environ["MIOS_CONTROL_WORKER_CPUS"])
    cpus.add(int(os.environ["MIOS_CONTROL_RT_CPU"]))
    pin_cpus(cpus)
    # Retain this descriptor through exec for the lifetime of Control and its
    # children. The node-local lock also protects against overlapping Pods
    # during manual deletion. Existing Docker containers do not use this lock.
    lock = os.open("/var/lock/mios-fr3/fci.lock", os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(lock)
        raise RuntimeError("Another Kubernetes Control process holds the node's FCI owner lock")
    os.set_inheritable(lock, True)
    print("RT limits and CPU availability verified; FCI owner lock acquired.", flush=True)
    os.execv("/entrypoint.sh", ["/entrypoint.sh", "/usr/local/bin/start_control.sh"])


def main():
    mode = sys.argv[1] if len(sys.argv) == 2 else ""
    mongo_port = int(os.environ.get("MONGO_PORT", "27017"))
    core_port = int(os.environ.get("MIOS_WS_PORT", "12000"))
    ml_port = int(os.environ.get("MIOS_ML_PORT", "8000"))
    if mode == "control":
        start_control()
    elif mode == "core":
        pin_cpus(cpu_set(os.environ["MIOS_NONRT_CPUS"]))
        wait_for_ports([mongo_port])
        os.execv("/entrypoint.sh", ["/entrypoint.sh", "/usr/local/bin/start_core.sh"])
    elif mode == "mls":
        pin_cpus(cpu_set(os.environ["MIOS_NONRT_CPUS"]))
        wait_for_ports([mongo_port, core_port])
        return start_mls()
    elif mode == "probe-core":
        check_owned_ports(1, [core_port])
    elif mode == "probe-mls":
        check_owned_ports(mls_pid(), [ml_port, ml_port + 1])
    elif mode == "stop-mls":
        # Native sidecar ordering leaves Core and Control alive for this hook.
        # Bound the RPC so a failed MLS cannot consume the Pod's shutdown grace.
        check_owned_ports(mls_pid(), [ml_port])
        socket.setdefaulttimeout(5)
        with ServerProxy(f"http://127.0.0.1:{ml_port}/", allow_none=True) as service:
            if service.stop_service() is False:
                raise RuntimeError("MLS did not acknowledge learning cancellation")
    else:
        raise ValueError("Expected control, core, mls, probe-core, probe-mls, or stop-mls")


if __name__ == "__main__":
    # PID 1 must also accept termination while waiting for startup dependencies.
    # Caught signal handlers reset on exec into the native Core/Control programs.
    signal.signal(signal.SIGTERM, lambda signum, frame: sys.exit(128 + signum))
    try:
        sys.exit(main())
    except (OSError, RuntimeError, ValueError) as error:
        print(f"MIOS Kubernetes {sys.argv[1:]}: {error}", file=sys.stderr, flush=True)
        sys.exit(1)
