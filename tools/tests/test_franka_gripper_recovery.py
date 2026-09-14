"""Exercise the patched read callback without ROS, libfranka, or robot access."""

import ast
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


PATCH = Path(__file__).resolve().parents[2] / "docker/ros2/franka_gripper_recovery.patch"


def patched_fragment(filename):
    """Read the changed file's postimage from the patch, including its context."""
    selected = False
    result = []
    for line in PATCH.read_text().splitlines(keepends=True):
        if line.startswith("diff --git "):
            selected = line.rstrip().endswith(" b/" + filename)
        elif selected and not line.startswith(("+++", "---", "@@")) and line[:1] in ("+", " "):
            result.append(line[1:])
    return "".join(result)


def gripper_launch_nodes():
    fragment = patched_fragment("franka_gripper/launch/gripper.launch.py")
    function = "def generate_robot_nodes" + fragment.split("def generate_robot_nodes", 1)[1]
    function = function.split("def generate_launch_description", 1)[0]
    context = {"robot_ip": "192.0.2.1", "use_fake_hardware": "false", "robot_type": "fr3", "namespace": ""}

    class Configuration:
        def __init__(self, name):
            self.name = name

        def perform(self, values):
            return values[self.name]

    namespace = dict(os=os, LaunchConfiguration=Configuration, Node=lambda **kwargs: kwargs,
                     get_package_share_directory=lambda _: "/fake/share",
                     UnlessCondition=lambda value: ("unless", value), IfCondition=lambda value: ("if", value))
    exec(compile(ast.parse(function), "patched-gripper-launch", "exec"), namespace)
    return namespace["generate_robot_nodes"](context)


HARNESS = r'''
#include <cassert>
#include <exception>
#include <memory>
#include <mutex>
#include <stdexcept>
#include <string>
#include <vector>
int fatal_logs = 0;
#define RCLCPP_FATAL(...) (++fatal_logs)
namespace sensor_msgs { namespace msg {
struct JointState {
  struct { int stamp; } header;
  std::vector<std::string> name;
  std::vector<double> position, velocity, effort;
};
}}
struct State { double width = 0.04; };
struct PocoLikeException : std::exception {};
struct Gripper {
  int failure = 0;
  State readOnce() {
    if (failure == 1) throw std::runtime_error("UDP receive timeout");
    if (failure == 2) throw PocoLikeException();
    return State{};
  }
};
struct Publisher {
  std::vector<sensor_msgs::msg::JointState> samples;
  void publish(const sensor_msgs::msg::JointState& sample) { samples.push_back(sample); }
};
struct GripperActionServer {
  std::mutex gripper_state_mutex_;
  std::unique_ptr<Gripper> gripper_ = std::make_unique<Gripper>();
  std::unique_ptr<Publisher> joint_states_publisher_ = std::make_unique<Publisher>();
  std::vector<std::string> joint_names_{"finger1", "finger2"};
  State current_gripper_state_;
  int stamps = 0;
  int now() { return ++stamps; }
  void publishGripperState();
};
__READ_METHOD__
int main() {
  GripperActionServer node;
  node.publishGripperState();
  assert(node.joint_states_publisher_->samples.size() == 1);
  const auto sample = node.joint_states_publisher_->samples.back();
  assert(sample.position.size() == 2);
  assert(sample.position[0] == 0.02 && sample.position[1] == 0.02);
  for (const auto failure : {1, 2}) {
    node.gripper_->failure = failure;
    bool caught = false;
    try { node.publishGripperState(); }
    catch (const std::exception&) { caught = true; }
    assert(caught);  // Reaches the process supervisor instead of masking failure.
    assert(node.joint_states_publisher_->samples.size() == 1);
    assert(node.stamps == 1);  // No new timestamp for the previous width.
  }
  assert(fatal_logs == 2);
  node.gripper_->failure = 0;
  node.publishGripperState();  // The callback releases its mutex on exceptions.
  assert(node.joint_states_publisher_->samples.size() == 2);
}
'''


class GripperRecoveryTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("c++"), "C++ compiler required for callback behavior test")
    def test_read_failures_escape_without_publishing_or_restamping_cached_width(self):
        fragment = patched_fragment("franka_gripper/src/gripper_action_server.cpp")
        method = re.search(r"^void GripperActionServer::publishGripperState\(\) \{.*?^\}", fragment, re.M | re.S)
        self.assertIsNotNone(method)
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "read_callback.cpp"
            executable = Path(directory) / "read_callback"
            source.write_text(HARNESS.replace("__READ_METHOD__", method[0]))
            compiled = subprocess.run(["c++", "-std=c++17", "-Wall", "-Wextra", str(source), "-o", str(executable)],
                                      capture_output=True, text=True, timeout=20, check=False)
            self.assertEqual(compiled.returncode, 0, compiled.stderr)
            result = subprocess.run([str(executable)], capture_output=True, text=True, timeout=5, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_only_real_gripper_node_has_bounded_delayed_respawn(self):
        nodes = gripper_launch_nodes()
        self.assertEqual(len(nodes), 2)
        real, fake = nodes
        self.assertEqual(real["executable"], "franka_gripper_node")
        self.assertEqual(real["condition"], ("unless", "false"))
        self.assertIs(real["respawn"], True)
        self.assertEqual(real["respawn_delay"], 2.0)
        self.assertEqual(real["respawn_max_retries"], 5)
        self.assertEqual(fake["executable"], "fake_gripper_state_publisher.py")
        self.assertEqual(fake["condition"], ("if", "false"))
        self.assertFalse(any(key.startswith("respawn") for key in fake))


if __name__ == "__main__":
    unittest.main()
