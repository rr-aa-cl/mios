"""Command-line entry point for a bounded pre-deployment readiness report."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import ipaddress
import json
import math
from pathlib import Path
import sys

from .common import Check, Context, Runner
from .configuration import collect_configuration, collect_docker, collect_existing
from . import host, images


def positive_gib(value):
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("Must be a positive finite number")
    return number


def ipv4(value):
    try:
        return str(ipaddress.IPv4Address(value))
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from error


def parser():
    repo = Path(__file__).resolve().parents[2]
    result = argparse.ArgumentParser(
        description="Inspect the local Linux host and candidate MIOS images before deployment. Never starts the robot stack or opens FCI.")
    result.add_argument("--profile", choices=("motion", "state-only"), default="motion",
                        help="default: motion, requiring commissioned power settings and teaching/learning gates; "
                             "state-only requires task execution and controller-owned Move disabled")
    result.add_argument("--compose-file", type=Path, default=repo / "docker/ros2/docker-compose.runtime.yml")
    result.add_argument("--control-image", help="override MIOS_ROS2_CONTROL_IMAGE for this inspection")
    result.add_argument("--core-image", help="override MIOS_ROS2_CORE_IMAGE for this inspection")
    result.add_argument("--ml-image", help="override MIOS_ML_SERVICE_IMAGE for this inspection")
    result.add_argument("--robot-ip", type=ipv4, help="override ROBOT_IP for this inspection")
    result.add_argument("--no-ping", action="store_true", help="omit the ICMP reachability sample; reported as a warning")
    result.add_argument("--min-free-gib", type=positive_gib, default=2, help="minimum free Docker storage, default: 2 GiB")
    result.add_argument("--strict", action="store_true", help="also treat warnings as blockers")
    result.add_argument("--json", type=Path, dest="json_report", metavar="FILE", help="also write the structured report to FILE")
    result.add_argument("--quiet", action="store_true", help="show only warnings, failures, and the final result")
    return result


def summarize(checks, strict=False):
    counts = Counter(check.status for check in checks)
    ready = bool(checks) and not (counts["FAIL"] or counts["UNKNOWN"] or (strict and counts["WARN"]))
    status = "BLOCKED" if not ready else "READY_WITH_WARNINGS" if counts["WARN"] else "READY"
    return ready, status, {name: counts[name] for name in ("PASS", "WARN", "FAIL", "UNKNOWN")}


def run(args, runner=None):
    runner = runner or Runner()
    context = Context(repo_root=Path(__file__).resolve().parents[2], profile=args.profile, ping=not args.no_ping)
    checks = []

    def collect(name, operation):
        try:
            found = operation()
        except Exception as error:
            found = [Check(name, "UNKNOWN", f"Inspection could not finish: {type(error).__name__}: {error}",
                           "Resolve the inspection error and rerun; this report cannot establish readiness.")]
        checks.extend(found)
        for check in found:
            if not args.quiet or check.status != "PASS":
                print(f"[{check.status:7}] {check.id}: {check.message}", flush=True)
                if check.remediation and check.status != "PASS":
                    print(f"          Fix: {check.remediation}", flush=True)

    collect("configuration", lambda: collect_configuration(context, args, runner))
    usable = False

    def docker_checks():
        nonlocal usable
        found, usable = collect_docker(context, runner, args.min_free_gib)
        return found

    collect("docker", docker_checks)
    if usable:
        collect("host", lambda: host.collect(context, runner))
        if context.compose:
            collect("deployment", lambda: collect_existing(context, runner))
        if context.images:
            if not args.quiet:
                print("Inspecting candidate images in disposable containers with networking disabled...", flush=True)
            collect("images", lambda: images.collect(context, runner))
        else:
            collect("images", lambda: [Check("images", "UNKNOWN", "No candidate image set could be resolved.")])
    else:
        collect("host_and_images", lambda: [Check("host_and_images", "UNKNOWN", "Host and image probes require a verified local rootful Docker daemon.")])
    ready, status, counts = summarize(checks, args.strict)
    report = {
        "schema_version": 1,
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "profile": context.profile,
        "ready": ready,
        "status": status,
        "strict": args.strict,
        "robot_ip": context.robot_ip,
        "compose_file": str(args.compose_file.resolve()),
        "images": context.images,
        "counts": counts,
        "checks": [check.to_dict() for check in checks],
        "limits": [
            "This report is a point-in-time check on this host and these image IDs.",
            "No FCI connection, controller activation, or motion test was performed.",
            "ICMP and static settings cannot prove real-time deadlines or physical workspace readiness.",
            "Run the offline image tests and a separately supervised bounded transport validation before motion.",
            "Control, Core, and ML startup configuration is checked; Control health covers preparation and its launch process, not live task or gripper readiness.",
        ],
    }
    if args.json_report:
        try:
            args.json_report.parent.mkdir(parents=True, exist_ok=True)
            args.json_report.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
        except (OSError, ValueError) as error:
            print(f"Cannot save readiness report: {error}", file=sys.stderr)
            return 2
    print(f"\n{status} for {context.profile} pre-deployment: " + ", ".join(f"{n} {key.lower()}" for key, n in counts.items()), flush=True)
    print("Physical motion readiness still requires supervised validation. No host settings or running services were changed.")
    if args.json_report:
        print(f"Report: {args.json_report.resolve()}")
    return 0 if ready else 1


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        return run(args)
    except KeyboardInterrupt:
        print("\nReadiness inspection interrupted; no readiness result established.", file=sys.stderr)
        return 130
