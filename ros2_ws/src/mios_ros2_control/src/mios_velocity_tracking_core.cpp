#include "mios_ros2_control/mios_velocity_tracking_core.hpp"

#include <algorithm>
#include <cmath>

namespace mios_ros2_control {
namespace {

bool all_finite(const std::array<double, 7>& values) {
  return std::all_of(values.begin(), values.end(),
                     [](double value) { return std::isfinite(value); });
}

}  // namespace

void MiosVelocityTrackingCore::configure(const Joints& stiffness, const Joints& damping,
                                         const Joints& position_error_limit) {
  stiffness_ = stiffness;
  damping_ = damping;
  position_error_limit_ = position_error_limit;
  reset();
}

void MiosVelocityTrackingCore::reset() {
  reference_position_.fill(0.0);
  tracking_ = false;
}

bool MiosVelocityTrackingCore::step(const Joints& measured_position,
                                    const Joints& velocity_reference,
                                    const double period_seconds,
                                    MiosJointImpedanceRequest& request) {
  if (!all_finite(measured_position) || !all_finite(velocity_reference) ||
      !std::isfinite(period_seconds) || period_seconds <= 0.0) {
    reset();
    return false;
  }
  if (!tracking_) {
    reference_position_ = measured_position;
    tracking_ = true;
  }
  for (std::size_t index = 0; index < reference_position_.size(); ++index) {
    reference_position_[index] += velocity_reference[index] * period_seconds;
    reference_position_[index] =
        std::clamp(reference_position_[index],
                   measured_position[index] - position_error_limit_[index],
                   measured_position[index] + position_error_limit_[index]);
  }
  request.position = reference_position_;
  request.velocity = velocity_reference;
  request.feedforward_effort.fill(0.0);
  request.stiffness = stiffness_;
  request.damping = damping_;
  return true;
}

}  // namespace mios_ros2_control
