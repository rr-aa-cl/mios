#pragma once

#include <chrono>
#include <functional>
#include <future>
#include <mutex>
#include <string>

#include "controller_manager_msgs/srv/list_controllers.hpp"
#include "controller_manager_msgs/srv/set_hardware_component_state.hpp"
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
  virtual bool switch_effort(bool activate) = 0;
  // After a robot error has been cleared: bring the hardware component and
  // the effort controller back to active.  Sessions that cannot do this
  // fail closed.
  virtual mios::ControlReturnType reactivate() {
    return {true, "ControllerReactivationUnsupported",
            "This controller session cannot reactivate hardware."};
  }
};

class Ros2ControllerSession final : public ControllerSession {
 public:
  Ros2ControllerSession(rclcpp::Node& node, std::string manager_namespace,
                        std::string effort_controller, std::string position_controller,
                        std::chrono::milliseconds timeout,
                        std::string hardware_component = "FrankaHardwareInterface");
  mios::ControlReturnType acquire(const StationaryCheck& stationary) override;
  mios::ControlReturnType release() override;
  bool switch_effort(bool activate);
  mios::ControlReturnType reactivate() override;

 private:
  using List = controller_manager_msgs::srv::ListControllers;
  using Switch = controller_manager_msgs::srv::SwitchController;
  using SetHardwareState = controller_manager_msgs::srv::SetHardwareComponentState;
  using Parameters = rcl_interfaces::srv::GetParameters;

  List::Response::SharedPtr controllers();
  double check_gates();
  void require_exclusive(const List::Response& controllers, const std::string& state) const;

  rclcpp::Client<List>::SharedPtr list_client_;
  rclcpp::Client<Switch>::SharedPtr switch_client_;
  rclcpp::Client<SetHardwareState>::SharedPtr hardware_state_client_;
  rclcpp::Client<Parameters>::SharedPtr effort_parameters_;
  rclcpp::Client<Parameters>::SharedPtr position_parameters_;
  const std::string effort_controller_;
  const std::string hardware_component_;
  const std::chrono::milliseconds timeout_;
  std::mutex mutex_;
  bool activation_attempted_{false};
  std::shared_future<Switch::Response::SharedPtr> pending_activation_;
};

}  // namespace mios_ros2_runtime
