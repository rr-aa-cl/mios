#include "mios_ros2_runtime/ros2_error_recovery_client.hpp"

#include <algorithm>
#include <condition_variable>
#include <memory>
#include <utility>

namespace mios_ros2_runtime {

Ros2ErrorRecoveryClient::Ros2ErrorRecoveryClient(rclcpp::Node& node, std::string action_name)
    : action_name_(std::move(action_name)) {
  client_ = rclcpp_action::create_client<ErrorRecovery>(&node, action_name_);
}

ErrorRecoveryResult Ros2ErrorRecoveryClient::recover(
    const std::chrono::milliseconds timeout) const {
  using GoalHandle = rclcpp_action::ClientGoalHandle<ErrorRecovery>;
  std::lock_guard<std::mutex> recover_lock(recover_mutex_);

  const auto deadline =
      std::chrono::steady_clock::now() + std::max(timeout, std::chrono::milliseconds(1));
  // Discovery of an action server that was just (re)started may lag.
  const auto discovery_budget = std::min<std::chrono::milliseconds>(
      std::max(timeout, std::chrono::milliseconds(1)), std::chrono::milliseconds(1000));
  if (!client_ || !client_->wait_for_action_server(discovery_budget)) {
    return {false, false, "Error-recovery action server " + action_name_ + " is not available."};
  }

  struct Completion {
    std::mutex mutex;
    std::condition_variable condition;
    bool complete{false};
    ErrorRecoveryResult result;
  };
  const auto completion = std::make_shared<Completion>();
  const auto finish = [completion](ErrorRecoveryResult result) {
    std::lock_guard<std::mutex> lock(completion->mutex);
    if (completion->complete) {
      return;
    }
    completion->result = std::move(result);
    completion->complete = true;
    completion->condition.notify_all();
  };

  rclcpp_action::Client<ErrorRecovery>::SendGoalOptions options;
  options.goal_response_callback = [finish](std::shared_ptr<GoalHandle> goal_handle) {
    if (!goal_handle) {
      finish({false, false, "Error-recovery goal was rejected."});
    }
  };
  options.result_callback = [finish](const GoalHandle::WrappedResult& result) {
    switch (result.code) {
      case rclcpp_action::ResultCode::SUCCEEDED:
        finish({true, true, "Automatic error recovery succeeded."});
        break;
      case rclcpp_action::ResultCode::ABORTED:
        // The server aborts when libfranka throws, e.g. while the user stop
        // is pressed or the brakes are closed.
        finish({true, false, "Automatic error recovery was aborted by the robot."});
        break;
      case rclcpp_action::ResultCode::CANCELED:
        finish({true, false, "Automatic error recovery was canceled."});
        break;
      default:
        finish({true, false, "Automatic error recovery ended with an unknown result."});
        break;
    }
  };
  client_->async_send_goal(ErrorRecovery::Goal(), options);

  std::unique_lock<std::mutex> lock(completion->mutex);
  if (!completion->condition.wait_until(lock, deadline,
                                        [&completion] { return completion->complete; })) {
    // The goal may still complete on the robot; it is reported as a failure
    // here so the caller does not resume control on an unconfirmed recovery.
    return {false, false, "Automatic error recovery timed out."};
  }
  return completion->result;
}

}  // namespace mios_ros2_runtime
