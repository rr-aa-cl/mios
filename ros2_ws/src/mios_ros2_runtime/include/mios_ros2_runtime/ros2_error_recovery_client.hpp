#pragma once

#include <chrono>
#include <mutex>
#include <string>

#include "franka_msgs/action/error_recovery.hpp"
#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"

namespace mios_ros2_runtime {

struct ErrorRecoveryResult {
  // The action server took the goal.
  bool accepted{false};
  // libfranka's automaticErrorRecovery() returned without an exception.
  bool success{false};
  std::string message;
};

// Non-real-time client for franka_hardware's `~/error_recovery` action
// (franka_msgs/action/ErrorRecovery).  It owns no libfranka object; the
// action server in the Control container performs the recovery.
class Ros2ErrorRecoveryClient {
 public:
  Ros2ErrorRecoveryClient(rclcpp::Node& node, std::string action_name);

  // Sends one recovery goal and blocks until its result or `timeout`.
  // Call from a thread that is not spinning the node: the node's executor
  // delivers the goal response and the result.  Concurrent calls are
  // serialized, so one robot error produces one recovery at a time.
  ErrorRecoveryResult recover(std::chrono::milliseconds timeout) const;

  const std::string& action_name() const { return action_name_; }

 private:
  using ErrorRecovery = franka_msgs::action::ErrorRecovery;

  const std::string action_name_;
  rclcpp_action::Client<ErrorRecovery>::SharedPtr client_;
  mutable std::mutex recover_mutex_;
};

}  // namespace mios_ros2_runtime
