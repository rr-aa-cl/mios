"""Display alignment against a saved seated reference; send no motion commands."""

import argparse
import json
import math
from pathlib import Path
import sys
import time

import numpy as np
from scipy.spatial.transform import Rotation

from diagnose_insertion import RPC_LIMITS, _setup_pose_and_joints, accepted
from utils.ws_client import call_method


def read_reference(path):
    raw = json.loads(Path(path).read_text())
    state = accepted(raw["state"], "Saved seated state")
    context = accepted(raw["container"], "Saved container").get("context")
    if (state.get("status") != "Idle" or state.get("control_active") is not False
            or state.get("current_task") != "IdleTask"):
        raise ValueError("The reference must have been recorded after handguiding returned to Idle.")
    name = state.get("grasped_object")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("The reference does not identify the grasped object.")
    if not isinstance(context, dict) or context.get("name") != name + "_container":
        raise ValueError("The saved container does not match the reference's grasped object.")
    seated, _ = _setup_pose_and_joints(state, "O_T_EE", "Seated reference")
    container, _ = _setup_pose_and_joints(context, "O_T_OB", "Saved container")
    return {"seated": seated, "container": container, "object": name}


def alignment(reference, state):
    if state.get("grasped_object") != reference["object"]:
        raise ValueError(
            f"Core reports grasped_object={state.get('grasped_object')!r}; "
            f"the seated reference expects {reference['object']!r}. "
            "Confirm the physical grasp and object selection before using this reference."
        )
    if state.get("status") not in ("Idle", "Move"):
        raise ValueError(f"Cannot review alignment in robot state {state.get('status')!r}.")
    measured, _ = _setup_pose_and_joints(state, "O_T_EE", "Current state")
    seated = reference["seated"]
    offset = 1000 * reference["container"][:3, :3].T @ (measured[:3, 3] - seated[:3, 3])
    # Left-multiplying the measured orientation by this base-frame rotation
    # recovers the seated orientation. Express its axis-angle vector in the
    # fixed Container axes, not the changing measured tool axes.
    correction_base = Rotation.from_matrix(seated[:3, :3] @ measured[:3, :3].T).as_rotvec()
    correction_deg = np.degrees(reference["container"][:3, :3].T @ correction_base)
    angle = float(np.linalg.norm(correction_deg))
    return {"offset_mm": offset.tolist(), "lateral_mm": float(np.linalg.norm(offset[:2])),
            "orientation_change_deg": angle, "orientation_correction_deg": correction_deg.tolist(),
            "status": state["status"]}


def positive_seconds(value):
    seconds = float(value)
    if not math.isfinite(seconds) or seconds <= 0:
        raise argparse.ArgumentTypeError("Duration must be positive and finite.")
    return seconds


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--robot", required=True)
    parser.add_argument("--reference", required=True, type=Path,
                        help="seated-reference-*.json saved with the current grasp")
    parser.add_argument("--duration", type=positive_seconds, default=60.0)
    args = parser.parse_args(argv)
    try:
        reference = read_reference(args.reference)
        print("Read-only display: each sample calls get_state; no teaching or motion commands.")
        print("X/Y: sideways offset from a line through the seated position along saved Container Z.")
        print("Negative Z: withdrawn. Rotation: change from the actual seated orientation.")
        print("Rot correction [Rx,Ry,Rz]: signed axis-angle vector toward seated orientation,"
              " in fixed Container axes (right-hand signs; not Euler angles or joint commands).")
        print("These are reference differences, not verified physical fit tolerances.")
        print("Ctrl-C or the duration limit stops ONLY this display; finish handguiding in its terminal.",
              flush=True)
        deadline = time.monotonic() + args.duration
        while time.monotonic() < deadline:
            response = call_method(args.robot, 12000, "get_state", {}, **RPC_LIMITS)
            result = alignment(reference, accepted(response, "Read current state"))
            x, y, z = result["offset_mm"]
            rx, ry, rz = result["orientation_correction_deg"]
            print(f"{result['status']:4s}  X {x:+7.3f}  Y {y:+7.3f}  Z {z:+8.3f} mm"
                  f"  lateral {result['lateral_mm']:.3f} mm"
                  f"  rotation {result['orientation_change_deg']:.3f} deg"
                  f"  rot correction [{rx:+.3f}, {ry:+.3f}, {rz:+.3f}] deg", flush=True)
            time.sleep(max(0.0, min(0.5, deadline - time.monotonic())))
    except KeyboardInterrupt:
        print("\nDisplay stopped. Robot control is unchanged.")
        return 0
    except Exception as error:
        print(f"Alignment display stopped: {error}", file=sys.stderr)
        print("Robot control is unchanged.", file=sys.stderr)
        return 1
    print("Display finished. Robot control is unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
