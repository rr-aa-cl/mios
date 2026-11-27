#pragma once

#include <array>

#include "mios_ros2_control/mios_control_core.hpp"

namespace mios_ros2_control {

// Turns a conditioned joint-velocity reference into the joint-impedance
// request that makes the effort controller follow it. In Franka's combined
// velocity + effort session the velocity only drives the desired trajectory
// reported by the robot; the external torque is what moves the arm, so the
// reference has to be tracked here. No ROS handles or hardware interfaces.
class MiosVelocityTrackingCore {
 public:
  using Joints = std::array<double, 7>;

  void configure(const Joints& stiffness, const Joints& damping,
                 const Joints& position_error_limit);
  // Forgets the integrated reference. The next step() starts again from the
  // measured joint position, so a new motion never pulls toward an old target.
  void reset();
  bool tracking() const { return tracking_; }
  const Joints& reference_position() const { return reference_position_; }

  // Integrates the velocity reference into a position reference and fills a
  // joint-impedance request for it. The position reference is kept within
  // position_error_limit of the measured position: an arm that is blocked or
  // torque-limited then lags instead of storing a growing spring error.
  // Returns false and resets for non-finite input or an invalid period.
  [[nodiscard]] bool step(const Joints& measured_position, const Joints& velocity_reference,
                          double period_seconds, MiosJointImpedanceRequest& request);

 private:
  Joints stiffness_{};
  Joints damping_{};
  Joints position_error_limit_{};
  Joints reference_position_{};
  bool tracking_{false};
};

}  // namespace mios_ros2_control
