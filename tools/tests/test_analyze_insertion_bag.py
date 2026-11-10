"""Offline bag analysis regressions; ROS modules and messages are simulated."""

import contextlib
import importlib.util
import io
import json
import math
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace as NS
import unittest
from unittest import mock


SOURCE = Path(__file__).resolve().parents[1] / "analyze_insertion_bag.py"
SPEC = importlib.util.spec_from_file_location("insertion_bag_tested", SOURCE)
bag = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bag)
START = bag.utc_ns("2026-09-16T12:00:00Z")
END = START + 2 * bag.SECOND


def stamp(value):
    seconds, nanoseconds = divmod(value, bag.SECOND)
    return NS(sec=seconds, nanosec=nanoseconds)


class Errors:
    def __init__(self, **fields):
        self.fields = fields
        self.__dict__.update(fields)

    def get_fields_and_field_types(self):
        return dict.fromkeys(self.fields, "boolean")


def state(position=(0, 0, 0), source=START, desired=None, velocity=None,
          mode=2, current=None, last=None):
    return NS(
        header=NS(stamp=stamp(source)),
        o_t_ee=NS(pose=NS(position=NS(**dict(zip(("x", "y", "z"), position))))),
        desired_joint_state=NS(effort=[0] * 7 if desired is None else desired),
        measured_joint_state=NS(velocity=[0] * 7 if velocity is None else velocity),
        robot_mode=mode,
        current_errors=Errors(**(current or {})),
        last_motion_errors=Errors(**(last or {})),
    )


def effort(source=START, values=None, stopped=False):
    return NS(stamp=stamp(source), effort=[0] * 7 if values is None else values,
              user_stopped=stopped)


def analyze(records, **kwargs):
    return bag.analyze(records, START, END, (0, 0, 0), (0, 0, 1), **kwargs)


class GeometryAndSignalsTests(unittest.TestCase):
    def test_utc_parser_preserves_nanoseconds_and_converts_timezone_offsets(self):
        expected = START + 123_456_789
        for value in ("2026-09-16T12:00:00.123456789Z",
                      "2026-09-16T14:00:00.123456789+02:00",
                      "2026-09-16T06:30:00.123456789-05:30"):
            with self.subTest(value=value):
                self.assertEqual(expected, bag.utc_ns(value))
        self.assertEqual("2026-09-16T12:00:00.123456789Z", bag.utc_text(expected))
        self.assertEqual(START + 100_000_000, bag.utc_ns("2026-09-16T12:00:00.1Z"))
        with self.assertRaisesRegex(ValueError, "nine fractional"):
            bag.utc_ns("2026-09-16T12:00:00.1234567891Z")

    def test_taught_rotated_axis_matches_actual_final_pose(self):
        axis = (.9998961088589333, -.010074761474690302, .010308766657195712)
        target = (.6263790726661682, .09641637653112411, .6374954581260681)
        final = (.5949344635009766, .09699784219264984, .6301131248474121)
        records = [(bag.STATE, state(final), START), (bag.EFFORT, effort(), START)]
        result = bag.analyze(records, START, END, target, axis)["overall"]
        self.assertAlmostEqual(-31.523303, result["last_pose"]["depth_error_mm"], places=6)
        self.assertAlmostEqual(7.062701, result["last_pose"]["lateral_error_mm"], places=6)
        self.assertEqual(0, result["samples_meeting_position_success"])

    def test_success_requires_depth_and_lateral_in_the_same_sample(self):
        records = [(bag.EFFORT, effort(), START)]
        positions = [(0.004, 0, 0), (0, 0, -0.004)]
        records += [(bag.STATE, state(p), START + i) for i, p in enumerate(positions)]
        result = analyze(records)["overall"]
        self.assertEqual([-4.0, 0.0], result["depth_error_mm_range"])
        self.assertEqual([0.0, 4.0], result["lateral_error_mm_range"])
        self.assertEqual(0, result["samples_meeting_position_success"])
        records += [(bag.STATE, state((0.001, 0, -0.001)), START + 2)]
        self.assertEqual(1, analyze(records)["overall"]["samples_meeting_position_success"])

    def test_success_tolerances_use_strict_boundaries(self):
        records = [(bag.EFFORT, effort(), START)]
        records += [(bag.STATE, state(p), START + i) for i, p in enumerate(
            [(0, 0, -0.002), (0.003, 0, 0), (0.0029, 0, -0.0019)])]
        self.assertEqual(1, analyze(records)["overall"]["samples_meeting_position_success"])

    def test_window_includes_start_and_excludes_end_before_parsing_messages(self):
        records = [
            (bag.STATE, object(), START - 1),
            (bag.STATE, state(), START),
            (bag.EFFORT, effort(), START),
            (bag.STATE, state((0, 0, -0.001)), END - 1),
            (bag.STATE, object(), END),
            (bag.EFFORT, object(), END + 1),
        ]
        report = analyze(records)
        result = report["overall"]
        self.assertEqual(2, result["topics"][bag.STATE]["count"])
        self.assertEqual(1, result["topics"][bag.EFFORT]["count"])
        self.assertEqual(0, result["topics"][bag.ACTUATOR]["count"])
        self.assertEqual(bag.utc_text(END - 1), result["last_pose"]["bag_time_utc"])
        self.assertEqual(bag.utc_text(END), report["window_end_exclusive_utc"])
        self.assertEqual(2, len(report["one_second_windows"]))

    def test_window_requires_both_state_and_effort_messages(self):
        for records in ([], [(bag.STATE, state(), START)], [(bag.EFFORT, effort(), START)],
                        [(bag.STATE, state(), START), (bag.EFFORT, effort(), END)]):
            with self.subTest(records=records), self.assertRaisesRegex(
                    ValueError, "both robot states and MIOS effort commands"):
                analyze(records)

    def test_source_stamp_paths_and_requested_vs_franka_desired_are_separate(self):
        records = [
            (bag.STATE, state(source=START - 10_000_000,
                              desired=[-1, 2, -3, 4, -5, 6, -7],
                              velocity=[-.1, .2, -.3, .4, -.5, .6, -.7],
                              current={"joint_reflex": True, "communication": False}), START),
            (bag.EFFORT, effort(source=START - 20_000_000,
                                values=[10, -20, 30, -40, 50, -60, 70], stopped=True), START),
            (bag.ACTUATOR, NS(stamp=stamp(START - 30_000_000)), START),
            (bag.STATE, state(source=START + 15_000_000,
                              desired=[8, 0, 0, 0, 0, 0, 0], mode=4,
                              last={"tau_j_range_violation": True}), START + 20_000_000),
        ]
        report = analyze(records)
        result = report["overall"]
        self.assertEqual("bag receive timestamp", report["time_basis"])
        self.assertEqual([10, 20, 30, 40, 50, 60, 70], result["requested_effort_abs_max_nm"])
        self.assertEqual([8, 2, 3, 4, 5, 6, 7], result["franka_desired_effort_abs_max_nm"])
        self.assertEqual([.1, .2, .3, .4, .5, .6, .7], result["joint_velocity_abs_max_rad_s"])
        self.assertEqual(1, result["user_stopped_effort_commands"])
        self.assertEqual({"MOVE": 1, "REFLEX": 1}, result["robot_modes"])
        self.assertEqual(["joint_reflex"], result["current_errors"])
        self.assertEqual(["tau_j_range_violation"], result["last_motion_errors"])
        for topic, expected in [(bag.STATE, [5.0, 10.0]), (bag.EFFORT, [20.0, 20.0]),
                                (bag.ACTUATOR, [30.0, 30.0])]:
            self.assertEqual(expected, result["topics"][topic]["source_to_bag_timestamp_difference_ms"])
        self.assertEqual(20.0, result["topics"][bag.STATE]["max_internal_recorded_gap_ms"])


class ForceAndLimitTests(unittest.TestCase):
    @staticmethod
    def force_state(force, stiffness_z, quaternion, source=START, desired=None, mode=2):
        message = state(source=source, desired=desired, mode=mode)
        message.o_f_ext_hat_k = NS(wrench=NS(force=NS(**dict(zip("xyz", force)))))
        message.k_f_ext_hat_k = NS(wrench=NS(force=NS(x=0, y=0, z=stiffness_z)))
        message.o_t_ee.pose.orientation = NS(**dict(zip("xyzw", quaternion)))
        return message

    def test_force_projection_preserves_sign_and_tool_axis_angle(self):
        # Rotation about base Y takes tool Z onto the Container's base +X axis.
        quaternion = (0, math.sqrt(0.5), 0, math.sqrt(0.5))
        first = self.force_state((-8, 3, 4), 12, quaternion)
        second = self.force_state((4, 0, 5), 8, (0, 0, 0, 1), source=START + 1)
        records = [(bag.STATE, first, START), (bag.EFFORT, effort(), START),
                   (bag.STATE, second, START + 1)]
        report = bag.analyze(records, START, END, (0, 0, 0), (1, 0, 0))
        values = report["overall"]["force_and_limits"]
        self.assertEqual({"samples": 2, "range": [-8, 4], "mean": -2}, values["base_axial_force_n"])
        self.assertEqual({"samples": 2, "range": [5, 5], "mean": 5}, values["base_lateral_force_n"])
        self.assertEqual({"samples": 2, "range": [8, 12], "mean": 10}, values["stiffness_frame_z_force_n"])
        self.assertAlmostEqual(0, values["tool_z_alignment_deg"]["range"][0], places=5)
        self.assertAlmostEqual(90, values["tool_z_alignment_deg"]["range"][1], places=5)
        self.assertAlmostEqual(45, values["tool_z_alignment_deg"]["mean"], places=5)

    def test_slew_before_and_after_amplitude_clipping_are_distinct(self):
        records = [(bag.STATE, state(), START)]
        for index, value in enumerate((0, 3, 3.005)):
            when = START + index * 1_000_000
            records.append((bag.EFFORT, effort(source=when, values=[value] + [0]*6), when))
        values = analyze(records, effort_limits=[2]*7, effort_rate_limit=10)["overall"]["force_and_limits"]
        requests = values["nonstop_requested_effort"]
        self.assertEqual(3, requests["samples"])
        self.assertEqual([2] + [0]*6, requests["above_limit_count"])
        self.assertAlmostEqual(2/3, requests["above_limit_fraction"][0], places=6)
        raw, clipped = values["raw_requested_slew"], values["amplitude_clipped_requested_slew"]
        self.assertEqual(2, raw["samples"])
        self.assertEqual(2, clipped["samples"])
        self.assertAlmostEqual(3000, raw["abs_max_nm_s"][0])
        self.assertAlmostEqual(2000, clipped["abs_max_nm_s"][0])
        self.assertEqual([1] + [0]*6, raw["above_rate_limit_count"])
        self.assertEqual([1] + [0]*6, clipped["above_rate_limit_count"])
        self.assertEqual([0.5] + [0]*6, raw["above_rate_limit_fraction"])

    def test_source_timestamps_determine_slew_and_stop_markers_break_history(self):
        records = [(bag.STATE, state(), START)]
        # Every recording timestamp differs by 1 ms; source intervals control
        # this diagnostic. Stops, gaps >10ms and duplicate/reversed source
        # timestamps must not generate artificial derivative spikes.
        cases = [(0, 0, False), (1, 100, True), (2, 2, False),
                 (20, 2, False), (20, 2, False), (19, 2, False), (21, 2.04, False)]
        for index, (source_ms, value, stopped) in enumerate(cases):
            message = effort(source=START + source_ms * 1_000_000,
                             values=[value] + [0]*6, stopped=stopped)
            records.append((bag.EFFORT, message, START + index * 1_000_000))
        values = analyze(records, effort_limits=[3]*7, effort_rate_limit=10)["overall"]["force_and_limits"]
        self.assertEqual(6, values["nonstop_requested_effort"]["samples"])
        self.assertEqual([0]*7, values["nonstop_requested_effort"]["above_limit_count"])
        self.assertEqual(1, values["raw_requested_slew"]["samples"])
        self.assertAlmostEqual(20, values["raw_requested_slew"]["abs_max_nm_s"][0], places=6)
        self.assertEqual([1] + [0]*6, values["raw_requested_slew"]["above_rate_limit_count"])

    def test_desired_limit_occupancy_only_counts_move_states(self):
        records = [(bag.EFFORT, effort(), START),
                   (bag.STATE, state(desired=[20]*7, mode=1), START),
                   (bag.STATE, state(desired=[2, -2, 1.9995, 1, 0, 0, 0]), START + 1),
                   (bag.STATE, state(desired=[0]*7), START + 2)]
        values = analyze(records, effort_limits=[2]*7)["overall"]["force_and_limits"]
        result = values["move_franka_desired_effort"]
        self.assertEqual(2, result["samples"])
        self.assertEqual([1, 1, 1, 0, 0, 0, 0], result["at_or_above_limit_count"])
        self.assertEqual([.5, .5, .5, 0, 0, 0, 0], result["at_or_above_limit_fraction"])

    def test_missing_optional_signals_are_marked_unavailable(self):
        result = analyze([(bag.STATE, state(), START), (bag.EFFORT, effort(), START)])
        for values in (result["overall"]["force_and_limits"],
                       result["one_second_windows"][0]["force_and_limits"]):
            for field in ("base_axial_force_n", "base_lateral_force_n",
                          "stiffness_frame_z_force_n", "tool_z_alignment_deg"):
                self.assertEqual({"samples": 0, "range": None, "mean": None}, values[field])
            self.assertIsNone(values["nonstop_requested_effort"]["above_limit_fraction"])
            self.assertIsNone(values["raw_requested_slew"]["above_rate_limit_fraction"])


class ReaderContractTests(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.reader = mock.Mock()
        self.rosbag = ModuleType("rosbag2_py")
        self.rosbag.SequentialReader = mock.Mock(return_value=self.reader)
        self.rosbag.StorageOptions = mock.Mock(side_effect=lambda **kw: NS(**kw))
        self.rosbag.ConverterOptions = mock.Mock(side_effect=lambda *args: args)
        self.rosbag.StorageFilter = mock.Mock(side_effect=lambda **kw: NS(**kw))
        self.rclpy = ModuleType("rclpy")
        self.rclpy.init = mock.Mock(side_effect=AssertionError("ROS must remain uninitialized"))
        self.rclpy.create_node = mock.Mock(side_effect=AssertionError("No ROS nodes permitted"))
        self.serialization = ModuleType("rclpy.serialization")
        self.serialization.deserialize_message = mock.Mock(side_effect=lambda data, cls: data)
        self.utilities = ModuleType("rosidl_runtime_py.utilities")
        self.utilities.get_message = mock.Mock(side_effect=lambda name: "class:" + name)
        self.stack.enter_context(mock.patch.dict(sys.modules, {
            "rosbag2_py": self.rosbag, "rclpy": self.rclpy,
            "rclpy.serialization": self.serialization,
            "rosidl_runtime_py": ModuleType("rosidl_runtime_py"),
            "rosidl_runtime_py.utilities": self.utilities,
        }))
        self.reader.get_all_topics_and_types.return_value = [
            NS(name=topic, type="type:" + topic) for topic in (*bag.TOPICS, "/unrelated")]

    def records(self, records):
        self.reader.has_next.side_effect = [True] * len(records) + [False]
        self.reader.read_next.side_effect = records

    def test_reader_filters_seeks_and_stops_at_end_without_deserializing_excluded_records(self):
        inside = [(bag.STATE, state(), START), (bag.EFFORT, effort(), END - 1)]
        self.records([(bag.STATE, object(), START - 1), *inside,
                      (bag.STATE, object(), END), (bag.EFFORT, object(), END + 1)])
        self.assertEqual(inside, list(bag.read_records(Path("recording"), START, END)))
        self.rosbag.StorageOptions.assert_called_once_with(uri="recording", storage_id="mcap")
        self.rosbag.ConverterOptions.assert_called_once_with("", "")
        self.reader.open.assert_called_once()
        self.rosbag.StorageFilter.assert_called_once_with(topics=list(bag.TOPICS))
        self.assertEqual(list(bag.TOPICS), self.reader.set_filter.call_args.args[0].topics)
        self.reader.seek.assert_called_once_with(START)
        self.assertEqual(4, self.reader.read_next.call_count)
        self.assertEqual([mock.call(message, "class:type:" + topic) for topic, message, _ in inside],
                         self.serialization.deserialize_message.call_args_list)
        self.assertEqual([mock.call("type:" + topic) for topic in bag.TOPICS],
                         self.utilities.get_message.call_args_list)
        self.rclpy.init.assert_not_called()
        self.rclpy.create_node.assert_not_called()

    def test_missing_required_bag_topic_fails_before_seek_or_deserialization(self):
        for missing in (bag.STATE, bag.EFFORT):
            with self.subTest(missing=missing):
                self.reader.get_all_topics_and_types.return_value = [
                    NS(name=topic, type="type:" + topic) for topic in bag.TOPICS if topic != missing]
                with self.assertRaisesRegex(ValueError, "Required topic absent"):
                    list(bag.read_records(Path("recording"), START, END))
                self.reader.seek.assert_not_called()
                self.reader.set_filter.assert_not_called()
                self.serialization.deserialize_message.assert_not_called()

    def cli(self, **overrides):
        options = {"--start": ["2026-09-16T12:00:00Z"],
                   "--end": ["2026-09-16T12:00:02Z"],
                   "--target-xyz": ["0", "0", "0"], "--axis": ["0", "0", "1"]}
        options.update(overrides)
        return ["recording"] + [part for key, values in options.items() for part in [key, *values]]

    def test_invalid_cli_inputs_fail_before_opening_bag(self):
        invalid = [
            {"--start": ["2026-09-16T12:00:00"]},
            {"--start": ["2026-09-16T12:00:00.1234567891Z"]},
            {"--end": ["2026-09-16T12:00:00Z"]},
            {"--end": ["2026-09-16T11:59:59Z"]},
            {"--target-xyz": ["nan", "0", "0"]},
            {"--axis": ["0", "0", "0"]},
            {"--axis": ["0", "0", "2"]},
            {"--axis": ["0", "0", "inf"]},
            {"--depth-tolerance-mm": ["0"]},
            {"--depth-tolerance-mm": ["nan"]},
            {"--lateral-tolerance-mm": ["-1"]},
            {"--lateral-tolerance-mm": ["inf"]},
            {"--effort-limits": ["2"]*6},
            {"--effort-limits": ["2"]*6 + ["0"]},
            {"--effort-limits": ["2"]*6 + ["-1"]},
            {"--effort-limits": ["2"]*6 + ["nan"]},
            {"--effort-rate-limit": ["0"]},
            {"--effort-rate-limit": ["-10"]},
            {"--effort-rate-limit": ["inf"]},
        ]
        for options in invalid:
            with self.subTest(options=options), contextlib.redirect_stderr(io.StringIO()), \
                    self.assertRaises(SystemExit) as error:
                bag.main(self.cli(**options))
            self.assertEqual(2, error.exception.code)
            self.rosbag.SequentialReader.assert_not_called()
            self.reader.open.assert_not_called()

    def test_cli_outputs_valid_json_without_optional_actuator_topic(self):
        self.reader.get_all_topics_and_types.return_value = [
            NS(name=topic, type="type:" + topic) for topic in (bag.STATE, bag.EFFORT)]
        self.records([(bag.STATE, state(), START), (bag.EFFORT, effort(), START)])
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(0, bag.main(self.cli(**{
                "--effort-limits": ["2"]*7, "--effort-rate-limit": ["10"]})))
        result = json.loads(output.getvalue())
        self.assertEqual(1, result["overall"]["topics"][bag.STATE]["count"])
        self.assertEqual(0, result["overall"]["topics"][bag.ACTUATOR]["count"])
        self.assertEqual(1, len(result["one_second_windows"]))
        self.assertEqual([2]*7, result["overall"]["force_and_limits"]["reference_effort_limits_nm"])
        self.assertEqual(10, result["overall"]["force_and_limits"]["reference_effort_rate_limit_nm_s"])
        self.assertEqual([bag.STATE, bag.EFFORT], self.reader.set_filter.call_args.args[0].topics)
        self.rclpy.init.assert_not_called()
        self.rclpy.create_node.assert_not_called()


if __name__ == "__main__":
    unittest.main()
