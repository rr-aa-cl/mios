#pragma once

#include <chrono>
#include <functional>
#include <future>
#include <mutex>
#include <string>

#include "controller_manager_msgs/srv/list_controllers.hpp"
#include "controller_manager_msgs/srv/switch_controller.hpp"
#include "mios/utils/types.hpp"
#include "rcl_interfaces/srv/get_parameters.hpp"
#include "rclcpp/rclcpp.hpp"

namespace mios_ros2_runtime {

// Called by the Core worker, never by a ROS callback or the hardware update loop.
class ControllerSession {
 public:
  using StationaryCheck = std::function<bool(double velocity_threshold)>;
  virtual ~ControllerSession() = default;
  virtual mios::ControlReturnType acquire(const StationaryCheck& stationary) = 0;
  virtual mios::ControlReturnType release() = 0;
};

class Ros2ControllerSession final : public ControllerSession {
 public:
  Ros2ControllerSession(rclcpp::Node& node, std::string manager_namespace,
                        std::string effort_controller, std::string position_controller,
                        std::chrono::milliseconds timeout);
  mios::ControlReturnType acquire(const StationaryCheck& stationary) override;
  mios::ControlReturnType release() override;

 private:
  using List = controller_manager_msgs::srv::ListControllers;
  using Switch = controller_manager_msgs::srv::SwitchController;
  using Parameters = rcl_interfaces::srv::GetParameters;

  List::Response::SharedPtr controllers();
  double check_gates();
  bool switch_effort(bool activate);
  void require_exclusive(const List::Response& controllers, const std::string& state) const;

  rclcpp::Client<List>::SharedPtr list_client_;
  rclcpp::Client<Switch>::SharedPtr switch_client_;
  rclcpp::Client<Parameters>::SharedPtr effort_parameters_;
  rclcpp::Client<Parameters>::SharedPtr position_parameters_;
  const std::string effort_controller_;
  const std::chrono::milliseconds timeout_;
  std::mutex mutex_;
  bool activation_attempted_{false};
  std::shared_future<Switch::Response::SharedPtr> pending_activation_;
};

}  // namespace mios_ros2_runtime
