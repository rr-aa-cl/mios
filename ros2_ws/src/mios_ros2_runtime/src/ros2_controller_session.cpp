#include "mios_ros2_runtime/ros2_controller_session.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <utility>

#include "rcl_interfaces/msg/parameter_type.hpp"

namespace mios_ros2_runtime {
namespace {

std::string absolute_name(std::string name) {
  if (name.empty()) {
    throw std::invalid_argument("Controller and controller-manager names must not be empty.");
  }
  if (name.front() != '/') name.insert(name.begin(), '/');
  while (name.size() > 1 && name.back() == '/') name.pop_back();
  return name;
}

template <typename Service>
typename Service::Response::SharedPtr request(
    const typename rclcpp::Client<Service>::SharedPtr& client,
    const typename Service::Request::SharedPtr& message,
    const std::chrono::milliseconds timeout) {
  if (!client->wait_for_service(timeout)) {
    throw std::runtime_error(std::string("ROS service unavailable: ") + client->get_service_name());
  }
  auto response = client->async_send_request(message);
  if (response.wait_for(timeout) != std::future_status::ready) {
    client->remove_pending_request(response.request_id);
    throw std::runtime_error(std::string("ROS service timed out: ") + client->get_service_name());
  }
  return response.get();
}

mios::ControlReturnType success() { return {false, "None", ""}; }

}  // namespace

Ros2ControllerSession::Ros2ControllerSession(
    rclcpp::Node& node, std::string manager_namespace, std::string effort_controller,
    std::string position_controller, const std::chrono::milliseconds timeout)
    : effort_controller_(std::move(effort_controller)), timeout_(timeout) {
  if (timeout_ <= std::chrono::milliseconds::zero()) {
    throw std::invalid_argument("Controller-manager timeout must be positive.");
  }
  const auto manager = absolute_name(std::move(manager_namespace));
  list_client_ = node.create_client<List>(manager + "/list_controllers");
  switch_client_ = node.create_client<Switch>(manager + "/switch_controller");
  effort_parameters_ = node.create_client<Parameters>(absolute_name(effort_controller_) + "/get_parameters");
  position_parameters_ = node.create_client<Parameters>(absolute_name(std::move(position_controller)) + "/get_parameters");
}

Ros2ControllerSession::List::Response::SharedPtr Ros2ControllerSession::controllers() {
  return request<List>(list_client_, std::make_shared<List::Request>(), timeout_);
}

void Ros2ControllerSession::require_exclusive(const List::Response& states,
                                             const std::string& expected_state) const {
  std::size_t matches = 0;
  for (const auto& controller : states.controller) {
    if (controller.name == effort_controller_) {
      ++matches;
      if (controller.state != expected_state ||
          controller.type != "mios_ros2_control/MiosEffortController") {
        throw std::runtime_error(effort_controller_ + " must be configured and " + expected_state +
                                 "; found " + controller.state + ".");
      }
    } else if (controller.state == "active" &&
               (!controller.claimed_interfaces.empty() ||
                controller.type.find("Broadcaster") == std::string::npos)) {
      throw std::runtime_error("Another controller already owns command interfaces: " + controller.name);
    }
  }
  if (matches != 1) {
    throw std::runtime_error(effort_controller_ + " must be loaded and configured by Control startup.");
  }
}

double Ros2ControllerSession::check_gates() {
  auto query = std::make_shared<Parameters::Request>();
  query->names = {"allow_effort_activation", "allow_zero_effort_activation",
                  "allow_runtime_effort_commands", "allow_runtime_actuator_commands",
                  "allow_runtime_cartesian_actuator_commands", "robot_state_safety_enabled",
                  "robot_state_source", "activation_velocity_threshold"};
  const auto response = request<Parameters>(effort_parameters_, query, timeout_);
  if (response->values.size() != query->names.size()) {
    throw std::runtime_error("Effort controller returned incomplete commissioning parameters.");
  }
  for (std::size_t index = 0; index < 6; ++index) {
    const auto& value = response->values[index];
    if (value.type != rcl_interfaces::msg::ParameterType::PARAMETER_BOOL || !value.bool_value) {
      throw std::runtime_error(effort_controller_ + "/" + query->names[index] + " must be true.");
    }
  }
  if (response->values[6].type != rcl_interfaces::msg::ParameterType::PARAMETER_STRING ||
      response->values[6].string_value != "hardware") {
    throw std::runtime_error("Effort controller robot_state_source must be hardware.");
  }
  const auto& threshold = response->values.back();
  if (threshold.type != rcl_interfaces::msg::ParameterType::PARAMETER_DOUBLE ||
      !std::isfinite(threshold.double_value) || threshold.double_value <= 0.0) {
    throw std::runtime_error("Effort activation_velocity_threshold must be a finite positive double.");
  }
  query->names = {"allow_runtime_joint_position_commands"};
  const auto position = request<Parameters>(position_parameters_, query, timeout_);
  if (position->values.size() != 1 ||
      position->values[0].type != rcl_interfaces::msg::ParameterType::PARAMETER_BOOL ||
      position->values[0].bool_value) {
    throw std::runtime_error("Native joint-position commands must remain disabled for effort tasks.");
  }
  return threshold.double_value;
}

bool Ros2ControllerSession::switch_effort(const bool activate) {
  if (!switch_client_->wait_for_service(timeout_)) {
    throw std::runtime_error("Controller-manager switch service is unavailable.");
  }
  auto message = std::make_shared<Switch::Request>();
  message->strictness = Switch::Request::STRICT;
  message->activate_asap = false;
  const auto nanoseconds = std::chrono::duration_cast<std::chrono::nanoseconds>(timeout_).count();
  message->timeout.sec = static_cast<std::int32_t>(nanoseconds / 1000000000);
  message->timeout.nanosec = static_cast<std::uint32_t>(nanoseconds % 1000000000);
  if (activate) {
    message->activate_controllers = {effort_controller_};
    // Record before sending: a rejected or timed-out reply can still have side effects.
    activation_attempted_ = true;
  } else {
    message->deactivate_controllers = {effort_controller_};
  }
  auto response = switch_client_->async_send_request(message);
  auto shared = response.future.share();
  if (activate) pending_activation_ = shared;
  if (shared.wait_for(timeout_ + std::chrono::milliseconds(250)) != std::future_status::ready) {
    if (!activate) switch_client_->remove_pending_request(response.request_id);
    throw std::runtime_error("Controller-manager switch timed out; controller ownership is uncertain.");
  }
  const bool ok = shared.get()->ok;
  if (activate) pending_activation_ = {};
  return ok;
}

mios::ControlReturnType Ros2ControllerSession::acquire(const StationaryCheck& stationary) {
  std::lock_guard<std::mutex> lock(mutex_);
  if (activation_attempted_) {
    return {true, "ControllerOwnershipUnresolved", "The previous effort-controller release is unconfirmed."};
  }
  try {
    require_exclusive(*controllers(), "inactive");
    const double threshold = check_gates();
    if (!stationary || !stationary(threshold)) {
      throw std::runtime_error("Fresh stationary robot state and fresh gripper feedback are required before activation.");
    }
    // Recheck ownership after parameter-service waits; STRICT never stops a competing owner.
    require_exclusive(*controllers(), "inactive");
    if (!switch_effort(true)) {
      throw std::runtime_error("Controller-manager rejected effort activation; inspect Control lifecycle diagnostics.");
    }
    require_exclusive(*controllers(), "active");
    return success();
  } catch (const std::exception& error) {
    return {true, "ControllerActivationFailed", error.what()};
  }
}

mios::ControlReturnType Ros2ControllerSession::release() {
  std::lock_guard<std::mutex> lock(mutex_);
  if (!activation_attempted_) return success();
  try {
    // Never certify release while an earlier activation can still complete later.
    bool activation_resolved = true;
    if (pending_activation_.valid()) {
      activation_resolved = pending_activation_.wait_for(timeout_) == std::future_status::ready;
      if (activation_resolved) {
        (void)pending_activation_.get();
        pending_activation_ = {};
      }
    }
    const auto before = controllers();
    const auto found = std::find_if(before->controller.begin(), before->controller.end(),
                                    [this](const auto& item) { return item.name == effort_controller_; });
    if (found == before->controller.end()) {
      throw std::runtime_error("Cannot verify the owned effort controller during release.");
    }
    if (found->state == "active" || !activation_resolved) {
      // Only this session's attempted controller is ever stopped.
      (void)switch_effort(false);
    }
    const auto after = controllers();
    const auto released = std::find_if(after->controller.begin(), after->controller.end(),
                                       [this](const auto& item) { return item.name == effort_controller_; });
    if (!activation_resolved || released == after->controller.end() || released->state != "inactive") {
      throw std::runtime_error("Effort-controller release is unconfirmed; further Core control is blocked.");
    }
    activation_attempted_ = false;
    return success();
  } catch (const std::exception& error) {
    return {true, "ControllerReleaseFailed", error.what()};
  }
}

}  // namespace mios_ros2_runtime
