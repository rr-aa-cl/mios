"""Review or execute one insertion diagnostic, with no reset, rescue, or retry."""

import argparse
from copy import deepcopy
import csv
from datetime import datetime, timezone
import inspect
import json
import math
import os
from pathlib import Path
import sys

import numpy as np

from definitions.cost_functions import TimeMetric
from definitions.templates import InsertionFactory
from example_learning import (check_learning_services, check_taught_insertion_objects,
                              configure_supervised_motion, supervised_nominal_knowledge)
from services.base_service import BaseService
from utils import ws_client
from utils.ws_client import call_method, start_task, stop_task, wait_for_task


PORT = 12000
INSERTION_TIME_LIMIT_SECONDS = 15.0
TASK_WAIT_SECONDS = 50
RPC_LIMITS = {"timeout": 5, "open_timeout": 5, "close_timeout": 0.2}
STOP_PARAMETERS = {"raise_exception": False, "recover": False, "empty_queue": True}
SETUP_POSITION_TOLERANCE_M = 0.005
SETUP_ORIENTATION_TOLERANCE_RAD = 0.0175
SETUP_JOINT_TOLERANCE_RAD = 0.0175
SEARCH_PROFILES = ("nominal", "centered-xy")


class TrialUnsuccessful(RuntimeError):
    """Core returned a valid completion result whose success flag is false."""


class SetupArrivalError(RuntimeError):
    """Measured setup arrival could not be confirmed before insertion."""


def check_transport_api():
    """Check the local client contract without calling Core or MLS.

    Older checkouts lack bounded connection/close options, including in the
    generic call_method. Check every layer before attempting even a state read;
    never retry a dispatched request to work around a TypeError.
    """
    checks = (
        ("call_method", call_method, ("offline.invalid", PORT, "get_state", {}),
         {**RPC_LIMITS, "cancel_event": None}),
        ("start_task", start_task, ("offline.invalid", "GenericTask"),
         {"parameters": {}, "queue": False, "port": PORT, **RPC_LIMITS}),
        ("stop_task", stop_task, ("offline.invalid",),
         {"port": PORT, **STOP_PARAMETERS, **RPC_LIMITS}),
        ("wait_for_task", wait_for_task, ("offline.invalid", "task-uuid"),
         {"port": PORT, **RPC_LIMITS, "timeout": TASK_WAIT_SECONDS}),
        ("send", ws_client.send, ("offline.invalid",),
         {"port": PORT, "endpoint": "mios/core", "request": {}, "silent": False,
          **RPC_LIMITS, "cancel_event": None}),
    )
    incompatible = []
    for name, function, args, kwargs in checks:
        try:
            inspect.signature(function).bind(*args, **kwargs)
        except (TypeError, ValueError) as error:
            incompatible.append(f"{name}: {error}")
    if incompatible:
        raise RuntimeError(
            f"Incompatible WebSocket client at {ws_client.__file__}: "
            + "; ".join(incompatible)
            + ". Copy ml_service/utils/ws_client.py from the same updated checkout "
            "as diagnose_insertion.py, then rerun without --run to check locally. "
            "No Core or MLS calls were made."
        )


def build_plan(robot, insertable, *, search_profile="nominal"):
    """Build a local nominal plan, with an optional diagnostic XY search."""
    if not isinstance(robot, str) or not robot.strip():
        raise ValueError("An explicit robot host is required.")
    if not isinstance(insertable, str) or not insertable.strip():
        raise ValueError("An explicit taught insertable name is required.")
    if search_profile not in SEARCH_PROFILES:
        raise ValueError(f"Unknown search profile: {search_profile!r}.")
    pd = InsertionFactory([robot], TimeMetric("insertion", {"time": 15}), {
        "Insertable": insertable, "Container": insertable + "_container",
        "Approach": insertable + "_container_approach",
    }).get_problem_definition(insertable)
    configure_supervised_motion(pd)
    # Use the repository's normal budget for this diagnostic, independently of
    # edits to the shared JSON. It includes approach, calibration, and search.
    pd.default_context["skills"]["insertion"]["skill"]["time_max"] = INSERTION_TIME_LIMIT_SECONDS
    parameters = supervised_nominal_knowledge(pd)["parameters"]
    # Keep the learning seed intact and record every diagnostic override.
    # Zero phases remove the offset in a*(sin(2*pi*f*t+phi)-sin(phi)).
    # The 2:1 frequencies produce a figure-eight force pattern in 20/3 s.
    overrides = ({"p2_wiggle_f_x": 0.3, "p2_wiggle_f_y": 0.15,
                  "p2_wiggle_phi_x": 0.0, "p2_wiggle_phi_y": 0.0}
                 if search_profile == "centered-xy" else {})
    for name, value in overrides.items():
        lower, upper = pd.domain.limits[name]
        if not lower <= value <= upper:
            raise ValueError(f"Search override {name}={value} is outside the insertion domain.")
    effective_parameters = {**parameters, **overrides}
    insertion = deepcopy(pd.default_context)
    for parameter, mappings in pd.domain.context_mapping.items():
        for mapping in mappings:
            BaseService.set_nested_parameter(None, insertion, mapping.split("."), effective_parameters[parameter])
    if len(pd.setup_instructions) != 1 or pd.setup_instructions[0]["method"] != "start_task":
        raise RuntimeError("Expected exactly one setup task in the insertion factory.")
    tasks = []
    for stage, context in (("setup", deepcopy(pd.setup_instructions[0]["parameters"])),
                           ("insertion", insertion)):
        context["parameters"]["as_queue"] = False
        tasks.append({"stage": stage, "request": {
            "task": context["name"], "parameters": context, "queue": False,
        }})
    return {"robot": robot, "insertable": insertable, "core_port": PORT,
            "task_wait_seconds": TASK_WAIT_SECONDS, "nominal_parameters": parameters,
            "search_profile": search_profile, "parameter_overrides": overrides,
            "setup_arrival_tolerances": {
                "position_m": SETUP_POSITION_TOLERANCE_M,
                "orientation_rad": SETUP_ORIENTATION_TOLERANCE_RAD,
                "joint_rad": SETUP_JOINT_TOLERANCE_RAD,
            },
            "tasks": tasks, "automatic_reset": False, "automatic_rescue": False}


def search_waveform(p2, times):
    """Evaluate Core's raw search wrench; omit push, impedance and limiting.

    Time is relative to the start of the wiggle primitive. Columns are forces
    Fx/Fy/Fz in N followed by torques Tx/Ty/Tz in Nm, all in the task frame.
    """
    vectors = [np.asarray(p2[key], dtype=float) for key in ("search_a", "search_f", "search_phi")]
    if any(vector.shape != (6,) or not np.all(np.isfinite(vector)) for vector in vectors):
        raise ValueError("Search amplitudes, frequencies and phases must be six finite numbers each.")
    times = np.asarray(times, dtype=float)
    if times.ndim != 1 or not np.all(np.isfinite(times)):
        raise ValueError("Search preview times must be a finite one-dimensional array.")
    amplitude, frequency, phase = vectors
    return amplitude * (np.sin(2 * np.pi * times[:, None] * frequency + phase) - np.sin(phase))


def write_search_preview(directory, plan):
    """Save an offline preview derived from the exact planned p2 request."""
    insertion = next(task for task in plan["tasks"] if task["stage"] == "insertion")
    skill = insertion["request"]["parameters"]["skills"]["insertion"]["skill"]
    p2 = skill["p2"]
    duration = float(skill["time_max"])
    sample_interval = 0.01
    times = np.arange(round(duration / sample_interval) + 1) * sample_interval
    samples = search_waveform(p2, times)
    axes = []
    for name, unit, amplitude, frequency, phase in zip(
            ("Fx", "Fy", "Fz", "Tx", "Ty", "Tz"), ("N", "N", "N", "Nm", "Nm", "Nm"),
            p2["search_a"], p2["search_f"], p2["search_phi"]):
        mean = -amplitude * math.sin(phase) if frequency != 0 else 0.0
        extent = abs(amplitude) if frequency != 0 else 0.0
        axes.append({"axis": name, "unit": unit, "amplitude": amplitude,
                     "frequency_hz": frequency, "phase_rad": phase,
                     "full_cycle_mean": mean, "range": [mean - extent, mean + extent]})
    report = {
        "search_profile": plan["search_profile"],
        "formula": "a * (sin(2*pi*f*t + phi) - sin(phi))",
        "time_reference": "Seconds since wiggle begins; actual wiggle uses only part of the skill budget.",
        "scope": "Raw task-frame search wrench only; excludes push, impedance, frame transforms and controller limits.",
        "interpretation": "A centered force pattern does not guarantee a centered motion. Partial cycles can have nonzero mean.",
        "preview_duration_s": duration, "sample_interval_s": sample_interval,
        "axes": axes, "configured_f_push": deepcopy(p2["f_push"]),
    }
    directory = Path(directory)
    (directory / "search-preview.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    with (directory / "search-preview.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["time_s", "Fx_N", "Fy_N", "Fz_N", "Tx_Nm", "Ty_Nm", "Tz_Nm"])
        writer.writerows([float(time), *wrench.tolist()] for time, wrench in zip(times, samples))
    return report


class RunLog:
    def __init__(self, directory, plan):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=False)
        (self.directory / "plan.json").write_text(json.dumps(plan, indent=2, allow_nan=False) + "\n")
        self.path = self.directory / "events.jsonl"
        self.path.touch(exist_ok=False)

    def write(self, operation, kind, data):
        event = {"time_utc": datetime.now(timezone.utc).isoformat(),
                 "operation": operation, "kind": kind, "data": data}
        with self.path.open("a") as stream:
            stream.write(json.dumps(event, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())

    def error(self, operation, error):
        # Preserve the original failure even if result storage also fails.
        try:
            self.write(operation, "error", {"type": type(error).__name__, "message": str(error)})
        except Exception:
            pass


def invoke(log, operation, request, function, *, require_log=True):
    try:
        log.write(operation, "request", request)
    except Exception:
        if require_log:
            raise
    try:
        response = function()
        try:
            log.write(operation, "response", response)
        except Exception:
            if require_log:
                raise
        return response
    except BaseException as error:
        log.error(operation, error)
        raise


def accepted(response, operation):
    result = response.get("result") if isinstance(response, dict) else None
    if (not isinstance(result, dict) or result.get("result") is not True
            or result.get("error") not in (None, "")
            or result.get("error_message") not in (None, "")):
        raise RuntimeError(f"{operation} was rejected or unconfirmed: {response!r}")
    return result


def completed(response, expected_skills):
    result = accepted(response, "Task completion").get("task_result")
    if (not isinstance(result, dict) or type(result.get("success")) is not bool
            or result.get("exception") is not False or result.get("external_stop") is not False
            or not isinstance(result.get("error"), list) or result["error"]):
        raise RuntimeError(f"Task failed or returned an ambiguous result: {result!r}")
    skills = result.get("skill_results")
    if not isinstance(skills, dict) or set(skills) != set(expected_skills):
        raise RuntimeError("Task completion does not contain all expected skill results.")
    for name, skill in skills.items():
        if (not isinstance(skill, dict) or not isinstance(skill.get("cost"), dict)
                or type(skill.get("heuristic")) not in (int, float)
                or not math.isfinite(skill["heuristic"])):
            raise RuntimeError(f"Malformed result for skill {name!r}: {skill!r}")
        # Current Core exports cost/heuristic only per skill. Validate any
        # additional status fields supplied by a newer Core without coercion.
        for flag, required in (("success", True), ("exception", False), ("external_stop", False)):
            if flag in skill and skill[flag] is not required:
                raise RuntimeError(f"Skill {name!r} reported {flag}={skill[flag]!r}.")
        for field in ("error", "errors", "last_errors"):
            if field in skill and (not isinstance(skill[field], list) or skill[field]):
                raise RuntimeError(f"Skill {name!r} reported {field}={skill[field]!r}.")
    if result["success"] is False:
        raise TrialUnsuccessful(
            f"Core reported success=False for {', '.join(expected_skills)} "
            "without a task exception or external stop. "
            "Inspect Core's logs for the stopping condition."
        )
    return result


def snapshot(robot, log, stage):
    try:
        invoke(log, stage + ".state", {}, lambda: call_method(robot, PORT, "get_state", {}, **RPC_LIMITS))
    except Exception as error:
        log.error(stage + ".state", error)


def require_ready(robot, log, stage):
    invoke(log, stage + ".readiness", {"robot": robot}, lambda: check_learning_services(robot, 8000))


def clear_queue(robot, log, stage):
    response = invoke(log, stage + ".stop_task", STOP_PARAMETERS,
                      lambda: stop_task(robot, port=PORT, **STOP_PARAMETERS, **RPC_LIMITS),
                      require_log=stage != "finally")
    accepted(response, "Core stop")


def select_object(robot, insertable, log):
    response = invoke(log, "set_grasped_object", {"object": insertable},
                      lambda: call_method(robot, PORT, "set_grasped_object", {"object": insertable}, **RPC_LIMITS))
    try:
        accepted(response, "Select grasped object")
    except RuntimeError:
        # Core can reject robot-parameter application after updating the logical
        # object. Preserve the learning example's verified-readback behavior.
        state = invoke(log, "grasped_object.readback", {},
                       lambda: call_method(robot, PORT, "get_state", {}, **RPC_LIMITS))
        if accepted(state, "Object readback").get("grasped_object") != insertable:
            raise RuntimeError(f"Could not select grasped object {insertable!r}: {response!r}")


def _finite_vector(values, length, label):
    if (not isinstance(values, list) or len(values) != length
            or any(isinstance(value, bool) or not isinstance(value, (int, float))
                   or not math.isfinite(value) for value in values)):
        raise SetupArrivalError(f"{label} must contain {length} finite numbers.")
    return np.asarray(values, dtype=float)


def _setup_pose_and_joints(context, pose_key, label):
    if not isinstance(context, dict):
        raise SetupArrivalError(f"{label} is not an object.")
    pose = _finite_vector(context.get(pose_key), 16, f"{label}.{pose_key}").reshape((4, 4), order="F")
    rotation = pose[:3, :3]
    if (not np.allclose(pose[3], [0, 0, 0, 1], rtol=0, atol=1e-6)
            or not np.allclose(rotation.T @ rotation, np.eye(3), rtol=0, atol=1e-5)
            or not math.isclose(float(np.linalg.det(rotation)), 1.0, rel_tol=0, abs_tol=1e-5)):
        raise SetupArrivalError(f"{label}.{pose_key} is not a rigid column-major transform.")
    joints = _finite_vector(context.get("q"), 7, f"{label}.q")
    return pose, joints


def read_setup_target(robot, log, plan):
    """Save the taught target before any mutation, without moving the robot."""
    try:
        setup = plan["tasks"][0]["request"]["parameters"]
        names = setup["parameters"]["skill_names"]
        types = setup["parameters"]["skill_types"]
        if len(names) != 1 or types != ["MoveToPoseJoint"]:
            raise SetupArrivalError("The arrival check requires one MoveToPoseJoint setup skill.")
        skill = setup["skills"][names[0]]["skill"]
        offset = _finite_vector(skill.get("q_g_offset", [0] * 7), 7, "Setup q_g_offset")
        if np.any(offset != 0):
            raise SetupArrivalError("The diagnostic arrival check requires zero q_g_offset.")
        object_name = skill["objects"]["goal_pose"]
        if (not isinstance(object_name, str) or not object_name.strip()
                or object_name in ("NoneObject", "NullObject")):
            raise SetupArrivalError("Setup requires a named taught goal pose.")
    except (KeyError, IndexError, TypeError) as error:
        raise SetupArrivalError("Cannot identify the diagnostic's taught setup target.") from error
    response = invoke(log, "setup.target", {"object": object_name},
                      lambda: call_method(robot, PORT, "download_object_context",
                                          {"object": object_name}, **RPC_LIMITS))
    try:
        context = accepted(response, "Read setup target").get("context")
        if not isinstance(context, dict) or context.get("name") != object_name:
            raise SetupArrivalError(f"Core did not return setup target {object_name!r}.")
        _setup_pose_and_joints(context, "O_T_OB", "Setup target")
    except RuntimeError as error:
        raise SetupArrivalError(str(error)) from error
    (log.directory / "setup-target.json").write_text(json.dumps(context, indent=2, allow_nan=False) + "\n")
    return deepcopy(context)


def require_setup_arrival(robot, log, target, tolerances):
    """Require measured arrival; a successful trajectory result alone is insufficient."""
    report = {"position_error_m": None, "orientation_error_rad": None,
              "joint_errors_rad": None, "max_joint_error_rad": None,
              "tolerances": deepcopy(tolerances), "passed": False}
    try:
        response = invoke(log, "setup_complete.state", {},
                          lambda: call_method(robot, PORT, "get_state", {}, **RPC_LIMITS))
        state = accepted(response, "Read measured setup arrival")
        if (state.get("status") != "Idle" or state.get("current_task") != "IdleTask"
                or state.get("control_active") is not False):
            raise SetupArrivalError("Core is not Idle with its controller inactive after setup.")
        measured_pose, measured_q = _setup_pose_and_joints(state, "O_T_EE", "Setup state")
        target_pose, target_q = _setup_pose_and_joints(target, "O_T_OB", "Setup target")
        position_error = float(np.linalg.norm(measured_pose[:3, 3] - target_pose[:3, 3]))
        cosine = (float(np.trace(target_pose[:3, :3].T @ measured_pose[:3, :3])) - 1.0) / 2.0
        orientation_error = math.acos(max(-1.0, min(1.0, cosine)))
        joint_errors = np.abs(measured_q - target_q)
        max_joint_error = float(np.max(joint_errors))
        passed = (position_error <= tolerances["position_m"]
                  and orientation_error <= tolerances["orientation_rad"]
                  and max_joint_error <= tolerances["joint_rad"])
        report.update(position_error_m=position_error, orientation_error_rad=orientation_error,
                      joint_errors_rad=joint_errors.tolist(), max_joint_error_rad=max_joint_error,
                      passed=passed)
    except Exception as error:
        report["error"] = str(error)
        log.write("setup.arrival_check", "result", report)
        raise SetupArrivalError(f"Could not confirm measured setup arrival: {error}") from error
    log.write("setup.arrival_check", "result", report)
    if not passed:
        raise SetupArrivalError(
            f"Measured setup missed the taught target: position {position_error * 1000:.3f} mm "
            f"(limit {tolerances['position_m'] * 1000:g} mm), orientation "
            f"{orientation_error:.6f} rad (limit {tolerances['orientation_rad']:g}), "
            f"maximum joint error {max_joint_error:.6f} rad "
            f"(limit {tolerances['joint_rad']:g}). Insertion was not dispatched."
        )


def run_diagnostic(robot, insertable, output, *, run=False, search_profile="nominal"):
    check_transport_api()
    plan = build_plan(robot, insertable, search_profile=search_profile)
    log = RunLog(output, plan)  # Refuse reused output directories before any RPC.
    write_search_preview(log.directory, plan)
    skill = plan["tasks"][1]["request"]["parameters"]["skills"]["insertion"]["skill"]
    time_limit = skill["time_max"]
    print(f"Insertion skill time limit: {time_limit:g} s (includes approach, calibration, and search).")
    speed, acceleration = skill["p0"]["dX_d"], skill["p0"]["ddX_d"]
    print(f"Insertion approach: {speed[0]:g} m/s, {speed[1]:g} rad/s; "
          f"acceleration {acceleration[0]:g} m/s^2, {acceleration[1]:g} rad/s^2.")
    p2 = skill["p2"]
    print(f"Search profile: {search_profile}; XY amplitudes {p2['search_a'][:2]} N, "
          f"frequencies {p2['search_f'][:2]} Hz, phases {p2['search_phi'][:2]} rad; "
          f"forward push {p2['f_push'][2]:g} N.")
    print("Offline search preview saved: search-preview.json and search-preview.csv.")
    if not run:
        log.write("diagnostic", "dry_run", {"plan": "plan.json"})
        return log.directory

    mutation_attempted = False
    failure = None
    try:
        require_ready(robot, log, "preflight")
        invoke(log, "check_taught_objects", {"insertable": insertable},
               lambda: check_taught_insertion_objects(robot, insertable))
        setup_target = read_setup_target(robot, log, plan)
        snapshot(robot, log, "before")
        mutation_attempted = True
        clear_queue(robot, log, "before")
        require_ready(robot, log, "queue_cleared")
        select_object(robot, insertable, log)
        for task in plan["tasks"]:
            stage, request = task["stage"], task["request"]
            if stage == "insertion":
                require_ready(robot, log, "setup_complete")
                require_setup_arrival(robot, log, setup_target, plan["setup_arrival_tolerances"])
            response = invoke(log, stage + ".start_task", request,
                              lambda: start_task(robot, port=PORT, **request, **RPC_LIMITS))
            task_uuid = accepted(response, stage + " start").get("task_uuid")
            if not isinstance(task_uuid, str) or not task_uuid or task_uuid == "INVALID":
                raise RuntimeError(f"{stage} start did not return a valid task UUID.")
            response = invoke(log, stage + ".wait_for_task", {"task_uuid": task_uuid},
                              lambda: wait_for_task(robot, task_uuid, port=PORT, timeout=TASK_WAIT_SECONDS,
                                                    open_timeout=5, close_timeout=0.2))
            completed(response, request["parameters"]["parameters"]["skill_names"])
    except BaseException as error:
        failure = error
        log.error("diagnostic", error)
        raise
    finally:
        cleanup_error = None
        if mutation_attempted:
            try:
                clear_queue(robot, log, "finally")
            except BaseException as error:
                cleanup_error = error
                log.error("cleanup", error)
                print("Core stop unconfirmed; use the physical stop if needed.", file=sys.stderr)
        try:
            snapshot(robot, log, "after")
            if mutation_attempted and failure is None and cleanup_error is None:
                require_ready(robot, log, "after")
        except BaseException as error:
            cleanup_error = cleanup_error or error
            log.error("postflight", error)
        if failure is None and cleanup_error is not None:
            raise RuntimeError(f"Could not confirm diagnostic cleanup: {cleanup_error}") from cleanup_error
    log.write("diagnostic", "completed", {"tasks": ["setup", "insertion"]})
    return log.directory


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--robot", required=True)
    parser.add_argument("--insertable", required=True)
    parser.add_argument("--output", required=True, type=Path, help="New directory for plan and JSON event log")
    parser.add_argument("--search-profile", choices=SEARCH_PROFILES, default="nominal",
                        help="Nominal learning seed or centered XY force search for this diagnostic only")
    parser.add_argument("--run", action="store_true", help="Execute setup and insertion; leaves the object at its final pose")
    arguments = parser.parse_args(argv)
    try:
        directory = run_diagnostic(arguments.robot, arguments.insertable, arguments.output,
                                   run=arguments.run, search_profile=arguments.search_profile)
    except SetupArrivalError as error:
        print(f"Diagnostic setup arrival failed: {error}", file=sys.stderr)
        print(f"Saved plan and events: {arguments.output}. "
              "Keep learning stopped while reviewing setup; insertion was not dispatched.", file=sys.stderr)
        return 1
    except TrialUnsuccessful as error:
        # run_diagnostic has already attempted cleanup and logged the complete
        # Core result. Keep an unsuccessful physical trial distinct from a
        # client failure while preserving a nonzero command exit status.
        print(f"Diagnostic trial unsuccessful: {error}", file=sys.stderr)
        print(f"Saved plan and events: {arguments.output}. "
              "Keep learning stopped while reviewing this attempt.", file=sys.stderr)
        return 1
    if arguments.run:
        print(f"Diagnostic completed: {directory}")
    else:
        print(f"Local transport API check passed. Dry-run plan written: {directory}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
