#!/usr/bin/env python3
"""Summarize a recorded insertion without creating ROS nodes or replaying commands.

Run using the Python environment sourced by the Control image. ROS imports are
lazy so the calculations and reader contract can also be tested without ROS.
All time windows use bag receive timestamps, not message source timestamps.
"""

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import sys


STATE = "/franka_robot_state_broadcaster/robot_state"
EFFORT = "/mios_effort_controller/mios_effort_command"
ACTUATOR = "/mios_effort_controller/mios_actuator_command"
TOPICS = (STATE, EFFORT, ACTUATOR)
MODES = {0: "OTHER", 1: "IDLE", 2: "MOVE", 3: "GUIDING", 4: "REFLEX",
         5: "USER_STOPPED", 6: "AUTOMATIC_RECOVERY"}
SECOND = 1_000_000_000


def utc_ns(value):
    fraction = re.search(r"[T ]\d{2}:\d{2}:\d{2}[.,](\d+)", value)
    digits = fraction.group(1) if fraction else ""
    if len(digits) > 9:
        raise ValueError("Timestamps support at most nine fractional second digits.")
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("Timestamps must include Z or a UTC offset.")
    delta = stamp.astimezone(timezone.utc) - datetime(1970, 1, 1, tzinfo=timezone.utc)
    remainder = int(digits.ljust(9, "0")) % 1000
    return (delta.days * 86400 + delta.seconds) * SECOND + delta.microseconds * 1000 + remainder


def utc_text(stamp):
    seconds, ns = divmod(stamp, SECOND)
    return datetime.fromtimestamp(seconds, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S") + f".{ns:09d}Z"


def finite_vector(values, size):
    result = tuple(float(x) for x in values)
    if len(result) != size or not all(math.isfinite(x) for x in result):
        raise ValueError(f"Expected {size} finite values, got {values!r}.")
    return result


def geometry(position, target, axis):
    """Return signed depth error and radial error, in metres, in target axes."""
    offset = [x - y for x, y in zip(finite_vector(position, 3), target)]
    depth = sum(x * z for x, z in zip(offset, axis))
    lateral = math.sqrt(sum((x - depth * z) ** 2 for x, z in zip(offset, axis)))
    return depth, lateral


def active_errors(message):
    return [name for name in message.get_fields_and_field_types()
            if getattr(message, name) is True]


class Range:
    def __init__(self):
        self.low = None
        self.high = None

    def add(self, value):
        self.low = value if self.low is None else min(self.low, value)
        self.high = value if self.high is None else max(self.high, value)

    def result(self):
        return None if self.low is None else [round(self.low, 6), round(self.high, 6)]


class SampleRange(Range):
    def __init__(self):
        super().__init__()
        self.samples, self.total = 0, 0.0

    def add(self, value):
        super().add(value)
        self.samples += 1
        self.total += value

    def result(self):
        return {"samples": self.samples, "range": super().result(),
                "mean": round(self.total / self.samples, 6) if self.samples else None}


def fractions(counts, samples):
    return [round(count / samples, 6) for count in counts] if samples else None


class RequestSlew:
    def __init__(self, rate_limit):
        self.rate_limit, self.samples = rate_limit, 0
        self.maximum, self.above = [0.0] * 7, [0] * 7

    def add(self, previous, current, dt):
        rates = [abs(b - a) / dt for a, b in zip(previous, current)]
        self.samples += 1
        self.maximum = [max(a, b) for a, b in zip(self.maximum, rates)]
        if self.rate_limit is not None:
            self.above = [count + (rate > self.rate_limit) for count, rate in zip(self.above, rates)]

    def result(self):
        return {"samples": self.samples,
                "abs_max_nm_s": [round(x, 6) for x in self.maximum] if self.samples else None,
                "above_rate_limit_count": self.above if self.rate_limit is not None else None,
                "above_rate_limit_fraction": fractions(self.above, self.samples) if self.rate_limit is not None else None}


class ForceAndLimits:
    """Recorded force estimates and demand comparisons, not controller telemetry."""
    def __init__(self, axis, effort_limits, rate_limit):
        self.axis, self.limits, self.rate_limit = axis, effort_limits, rate_limit
        self.force = {name: SampleRange() for name in (
            "base_axial_force_n", "base_lateral_force_n", "stiffness_frame_z_force_n", "tool_z_alignment_deg")}
        self.request_samples, self.move_samples = 0, 0
        self.request_above, self.desired_at_limit = [0] * 7, [0] * 7
        self.raw_slew, self.clipped_slew = RequestSlew(rate_limit), RequestSlew(rate_limit)
        self.previous = None

    def add_state(self, message, desired):
        for field in ("o_f_ext_hat_k", "k_f_ext_hat_k"):
            try:
                force = getattr(message, field).wrench.force
                xyz = finite_vector((force.x, force.y, force.z), 3)
            except (AttributeError, TypeError, ValueError):
                continue  # Older message schemas may omit optional wrench data.
            if field == "o_f_ext_hat_k":
                axial = sum(x * z for x, z in zip(xyz, self.axis))
                lateral = math.sqrt(sum((x - axial * z) ** 2 for x, z in zip(xyz, self.axis)))
                self.force["base_axial_force_n"].add(axial)
                self.force["base_lateral_force_n"].add(lateral)
            else:
                self.force["stiffness_frame_z_force_n"].add(xyz[2])
        try:
            q = message.o_t_ee.pose.orientation
            quaternion = finite_vector((q.x, q.y, q.z, q.w), 4)
            norm = math.sqrt(sum(x*x for x in quaternion))
            if norm == 0:
                raise ValueError("Orientation quaternion has zero length.")
            x, y, z, w = (value / norm for value in quaternion)
            tool_z = (2 * (x*z + y*w), 2 * (y*z - x*w), 1 - 2 * (x*x + y*y))
            cosine = sum(a * b for a, b in zip(tool_z, self.axis))
            self.force["tool_z_alignment_deg"].add(math.degrees(math.acos(max(-1.0, min(1.0, cosine)))))
        except (AttributeError, TypeError, ValueError):
            pass
        if message.robot_mode == 2:  # Compare desired torque only while Franka reports MOVE.
            self.move_samples += 1
            if self.limits is not None:
                self.desired_at_limit = [count + (abs(value) >= limit - min(0.001, limit * 0.001))
                    for count, value, limit in zip(self.desired_at_limit, desired, self.limits)]

    def add_request(self, values, source_ns, stopped):
        if stopped:
            self.previous = None
            return
        self.request_samples += 1
        if self.limits is not None:
            self.request_above = [count + (abs(value) > limit)
                for count, value, limit in zip(self.request_above, values, self.limits)]
        if self.previous is not None:
            previous_ns, previous_values = self.previous
            delta_ns = source_ns - previous_ns
            if 0 < delta_ns <= 10_000_000:
                dt = delta_ns / SECOND
                self.raw_slew.add(previous_values, values, dt)
                if self.limits is not None:
                    clipped = [[max(-limit, min(limit, value)) for value, limit in zip(row, self.limits)]
                               for row in (previous_values, values)]
                    self.clipped_slew.add(*clipped, dt)
        # Invalid intervals are skipped; the next interval starts at this sample.
        self.previous = (source_ns, values)

    def result(self):
        return {**{name: stats.result() for name, stats in self.force.items()},
                "reference_effort_limits_nm": self.limits,
                "reference_effort_rate_limit_nm_s": self.rate_limit,
                "nonstop_requested_effort": {"samples": self.request_samples,
                    "above_limit_count": self.request_above if self.limits is not None else None,
                    "above_limit_fraction": fractions(self.request_above, self.request_samples) if self.limits is not None else None},
                "raw_requested_slew": self.raw_slew.result(),
                "amplitude_clipped_requested_slew": self.clipped_slew.result(),
                "move_franka_desired_effort": {"samples": self.move_samples,
                    "at_or_above_limit_count": self.desired_at_limit if self.limits is not None else None,
                    "at_or_above_limit_fraction": fractions(self.desired_at_limit, self.move_samples) if self.limits is not None else None}}


class Window:
    def __init__(self, target, axis, depth_tolerance, lateral_tolerance, effort_limits=None, effort_rate_limit=None):
        self.target, self.axis = target, axis
        self.depth_tolerance, self.lateral_tolerance = depth_tolerance, lateral_tolerance
        self.counts = Counter()
        self.modes = Counter()
        self.errors = {"current_errors": set(), "last_motion_errors": set()}
        self.first = {}
        self.last = {}
        self.max_gap_ms = {}
        self.source_to_bag_ms = {topic: Range() for topic in TOPICS}
        self.depth, self.lateral = Range(), Range()
        self.first_pose = self.last_pose = self.greatest_depth = None
        self.success_samples = 0
        self.request_max = [0.0] * 7
        self.desired_max = [0.0] * 7
        self.velocity_max = [0.0] * 7
        self.user_stop_commands = 0
        self.force_and_limits = ForceAndLimits(axis, effort_limits, effort_rate_limit)

    def add(self, topic, message, stamp):
        if topic not in TOPICS:
            raise ValueError(f"Unexpected topic {topic}")
        if topic in self.last:
            if stamp < self.last[topic]:
                raise ValueError("Bag receive timestamps are out of order for a topic.")
            gap = (stamp - self.last[topic]) / 1e6
            self.max_gap_ms[topic] = max(gap, self.max_gap_ms.get(topic, 0.0))
        self.first.setdefault(topic, stamp)
        self.last[topic] = stamp
        self.counts[topic] += 1
        source = message.header.stamp if topic == STATE else message.stamp
        source_ns = source.sec * SECOND + source.nanosec
        self.source_to_bag_ms[topic].add((stamp - source_ns) / 1e6)
        if topic == EFFORT:
            values = finite_vector(message.effort, 7)
            self.request_max = [max(a, abs(b)) for a, b in zip(self.request_max, values)]
            self.user_stop_commands += bool(message.user_stopped)
            self.force_and_limits.add_request(values, source_ns, message.user_stopped)
        elif topic == STATE:
            pos = message.o_t_ee.pose.position
            xyz = finite_vector((pos.x, pos.y, pos.z), 3)
            depth, lateral = geometry(xyz, self.target, self.axis)
            self.depth.add(depth * 1000)
            self.lateral.add(lateral * 1000)
            sample = {"bag_time_utc": utc_text(stamp), "xyz_m": list(xyz),
                      "depth_error_mm": round(depth * 1000, 6),
                      "lateral_error_mm": round(lateral * 1000, 6)}
            if self.first_pose is None:
                self.first_pose = sample
            self.last_pose = sample
            if self.greatest_depth is None or depth > self.greatest_depth[0]:
                self.greatest_depth = (depth, sample)
            self.success_samples += (depth > -self.depth_tolerance and lateral < self.lateral_tolerance)
            self.modes[MODES.get(message.robot_mode, str(message.robot_mode))] += 1
            for field in self.errors:
                self.errors[field].update(active_errors(getattr(message, field)))
            # Franka's desired link-side torque excludes gravity. It is still
            # downstream of ROS/FCI processing, not the raw MIOS torque request.
            desired = finite_vector(message.desired_joint_state.effort, 7)
            velocity = finite_vector(message.measured_joint_state.velocity, 7)
            self.desired_max = [max(a, abs(b)) for a, b in zip(self.desired_max, desired)]
            self.velocity_max = [max(a, abs(b)) for a, b in zip(self.velocity_max, velocity)]
            self.force_and_limits.add_state(message, desired)

    def result(self):
        topics = {}
        for topic in TOPICS:
            topics[topic] = {"count": self.counts[topic]}
            if self.counts[topic]:
                topics[topic].update({"first_bag_time_utc": utc_text(self.first[topic]),
                    "last_bag_time_utc": utc_text(self.last[topic]),
                    "max_internal_recorded_gap_ms": round(self.max_gap_ms.get(topic, 0.0), 6),
                    "source_to_bag_timestamp_difference_ms": self.source_to_bag_ms[topic].result()})
        return {"topics": topics, "robot_modes": dict(self.modes),
                **{k: sorted(v) for k, v in self.errors.items()},
                "depth_error_mm_range": self.depth.result(),
                "lateral_error_mm_range": self.lateral.result(),
                "samples_meeting_position_success": self.success_samples,
                "first_pose": self.first_pose, "last_pose": self.last_pose,
                "greatest_depth_pose": None if self.greatest_depth is None else self.greatest_depth[1],
                "requested_effort_abs_max_nm": self.request_max if self.counts[EFFORT] else None,
                "franka_desired_effort_abs_max_nm": self.desired_max if self.counts[STATE] else None,
                "joint_velocity_abs_max_rad_s": self.velocity_max if self.counts[STATE] else None,
                "user_stopped_effort_commands": self.user_stop_commands,
                "force_and_limits": self.force_and_limits.result()}

    def compact_result(self):
        """Keep per-second rows small enough to paste for remote diagnosis."""
        return {"states": self.counts[STATE], "commands": self.counts[EFFORT],
                "actuator_commands": self.counts[ACTUATOR], "modes": dict(self.modes),
                "depth_mm": self.depth.result(), "lateral_mm": self.lateral.result(),
                "last_pose": self.last_pose,
                "lateral_at_greatest_depth_mm": (None if self.greatest_depth is None else
                                                 self.greatest_depth[1]["lateral_error_mm"]),
                "success_samples": self.success_samples,
                "requested_abs_max_nm": self.request_max if self.counts[EFFORT] else None,
                "franka_desired_abs_max_nm": self.desired_max if self.counts[STATE] else None,
                "force_and_limits": self.force_and_limits.result()}


def read_records(path, start, end):
    # No rclpy.init(), ROS node, network request, subscription, or publisher.
    import rosbag2_py
    from rclpy.serialization import deserialize_message
    from rosidl_runtime_py.utilities import get_message

    reader = rosbag2_py.SequentialReader()
    reader.open(rosbag2_py.StorageOptions(uri=str(path), storage_id="mcap"),
                rosbag2_py.ConverterOptions("", ""))
    types = {item.name: item.type for item in reader.get_all_topics_and_types()}
    for required in (STATE, EFFORT):
        if required not in types:
            raise ValueError(f"Required topic absent from bag: {required}")
    selected = [topic for topic in TOPICS if topic in types]
    message_types = {topic: get_message(types[topic]) for topic in selected}
    reader.set_filter(rosbag2_py.StorageFilter(topics=selected))
    reader.seek(start)
    while reader.has_next():
        topic, data, stamp = reader.read_next()
        if stamp >= end:
            break
        if stamp >= start:
            yield topic, deserialize_message(data, message_types[topic]), stamp


def analyze(records, start, end, target, axis, depth_tolerance=0.002, lateral_tolerance=0.003,
            effort_limits=None, effort_rate_limit=None):
    if end <= start:
        raise ValueError("End time must be after start time.")
    target = finite_vector(target, 3)
    axis = finite_vector(axis, 3)
    length = math.sqrt(sum(x*x for x in axis))
    if abs(length - 1) > 0.001:
        raise ValueError("Insertion axis must be a unit vector from the taught Container rotation.")
    axis = tuple(x / length for x in axis)
    if not all(math.isfinite(x) and x > 0 for x in (depth_tolerance, lateral_tolerance)):
        raise ValueError("Success tolerances must be positive finite values.")
    if effort_limits is not None:
        effort_limits = finite_vector(effort_limits, 7)
        if any(value <= 0 for value in effort_limits):
            raise ValueError("Effort limits must be seven positive finite values.")
    if effort_rate_limit is not None:
        effort_rate_limit = float(effort_rate_limit)
        if not math.isfinite(effort_rate_limit) or effort_rate_limit <= 0:
            raise ValueError("Effort rate limit must be a positive finite value.")
    arguments = (target, axis, depth_tolerance, lateral_tolerance, effort_limits, effort_rate_limit)
    total = Window(*arguments)
    bins = {}
    for topic, message, stamp in records:
        if not start <= stamp < end:
            continue
        total.add(topic, message, stamp)
        index = (stamp - start) // SECOND
        if index not in bins:
            bins[index] = Window(*arguments)
        bins[index].add(topic, message, stamp)
    if not total.counts[STATE] or not total.counts[EFFORT]:
        raise ValueError("Window must contain both robot states and MIOS effort commands; check its UTC times.")
    return {"window_start_utc": utc_text(start), "window_end_exclusive_utc": utc_text(end),
            "time_basis": "bag receive timestamp",
            "target_xyz_m": target, "insertion_axis_in_base": axis,
            "depth_tolerance_m": depth_tolerance, "lateral_tolerance_m": lateral_tolerance,
            "interpretation": [
                "Negative depth error means short of the taught depth. Success requires both tolerances in the same sample.",
                "Use phase timestamps from Core to separate setup, insertion, and controller release.",
                "Requested and Franka desired torque are different signals. Separate maxima do not establish saturation.",
                "Recorded gaps and source timestamp differences are not controller receipt latency or proof of packet loss.",
                "Force values are recorded Franka estimates; stiffness-frame Z is not a bias-corrected Core force.",
                "Tool-Z alignment measures only axis alignment, not the complete orientation error.",
                "Limit comparisons and amplitude-clipped request slew are demand reference calculations, not proof of controller clipping or saturation.",
                "Slew uses consecutive non-stop command source stamps within each window, with 0 < dt <= 10 ms; it does not measure controller receipt or update intervals.",
                "A user_stopped command can mark Core task completion; the flag alone does not establish a physical stop or fault.",
                "A zero actuator-command count is compatible with the raw effort-command path."],
            "overall": total.result(),
            "one_second_windows": [{"start_utc": utc_text(start + index * SECOND),
                                    **window.compact_result()} for index, window in sorted(bins.items())]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bag", type=Path)
    parser.add_argument("--start", required=True, help="UTC ISO timestamp, inclusive")
    parser.add_argument("--end", required=True, help="UTC ISO timestamp, exclusive")
    parser.add_argument("--target-xyz", required=True, nargs=3, type=float, metavar=("X", "Y", "Z"))
    parser.add_argument("--axis", required=True, nargs=3, type=float, metavar=("X", "Y", "Z"))
    parser.add_argument("--depth-tolerance-mm", type=float, default=2.0)
    parser.add_argument("--lateral-tolerance-mm", type=float, default=3.0)
    parser.add_argument("--effort-limits", nargs=7, type=float, metavar="NM",
                        help="Seven positive reference joint effort limits; does not change the controller")
    parser.add_argument("--effort-rate-limit", type=float, metavar="NM_PER_S",
                        help="Positive reference request slew limit; does not change the controller")
    args = parser.parse_args(argv)
    try:
        start, end = utc_ns(args.start), utc_ns(args.end)
        result = analyze(read_records(args.bag, start, end), start, end, args.target_xyz, args.axis,
                         args.depth_tolerance_mm / 1000, args.lateral_tolerance_mm / 1000,
                         effort_limits=args.effort_limits, effort_rate_limit=args.effort_rate_limit)
    except ImportError as error:
        parser.exit(2, f"Source /opt/ros/jazzy/setup.bash and /ws/install/setup.bash, then use system python3: {error}\n")
    except (ValueError, RuntimeError, AttributeError) as error:
        parser.exit(2, f"Bag analysis failed: {error}\n")
    # One JSON row per second keeps a complete, valid JSON report concise.
    windows = result.pop("one_second_windows")
    prefix = json.dumps(result, indent=2, allow_nan=False)
    print(prefix[:-2] + ',\n  "one_second_windows": [')
    print(",\n".join("    " + json.dumps(row, allow_nan=False) for row in windows))
    print("  ]\n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
