#include <cassert>
#include <cmath>
#include <limits>

#include "mios_ros2_control/mios_control_core.hpp"
#include "mios_ros2_control/mios_velocity_tracking_core.hpp"

namespace {
bool almost_equal(const double left, const double right) {
  return std::abs(left - right) < 1.0e-12;
}
}  // namespace

int main() {
  using mios_ros2_control::MiosJointImpedanceRequest;
  using mios_ros2_control::MiosVelocityTrackingCore;

  MiosVelocityTrackingCore core;
  MiosVelocityTrackingCore::Joints stiffness{};
  MiosVelocityTrackingCore::Joints damping{};
  MiosVelocityTrackingCore::Joints error_limit{};
  stiffness.fill(20.0);
  damping.fill(2.0);
  error_limit.fill(0.05);
  core.configure(stiffness, damping, error_limit);
  assert(!core.tracking());

  MiosVelocityTrackingCore::Joints measured{};
  measured.fill(0.3);
  MiosVelocityTrackingCore::Joints velocity{};
  velocity[2] = 0.1;
  MiosJointImpedanceRequest request;

  // The first step starts from the measured pose and integrates one period.
  assert(core.step(measured, velocity, 0.001, request));
  assert(core.tracking());
  assert(almost_equal(request.position[0], 0.3));
  assert(almost_equal(request.position[2], 0.3 + 0.1 * 0.001));
  assert(almost_equal(request.velocity[2], 0.1));
  assert(almost_equal(request.stiffness[5], 20.0));
  assert(almost_equal(request.damping[5], 2.0));
  for (const double feedforward : request.feedforward_effort) {
    assert(feedforward == 0.0);
  }

  // The reference keeps integrating while the measured joint follows.
  assert(core.step(measured, velocity, 0.001, request));
  assert(almost_equal(request.position[2], 0.3 + 0.1 * 0.002));

  // A joint that does not follow cannot be led by more than the error limit.
  for (int cycle = 0; cycle < 2000; ++cycle) {
    assert(core.step(measured, velocity, 0.001, request));
  }
  assert(almost_equal(request.position[2], 0.3 + 0.05));
  assert(almost_equal(request.position[1], 0.3));

  // The same bound applies when the joint is pushed away from its reference.
  measured[2] = 0.5;
  velocity[2] = 0.0;
  assert(core.step(measured, velocity, 0.001, request));
  assert(almost_equal(request.position[2], 0.5 - 0.05));

  // After a reset the next motion starts from the then-measured pose instead
  // of pulling back toward the previous reference.
  core.reset();
  assert(!core.tracking());
  measured.fill(-0.2);
  assert(core.step(measured, velocity, 0.001, request));
  assert(almost_equal(request.position[2], -0.2));

  // Invalid input is rejected and drops the reference.
  velocity[0] = std::numeric_limits<double>::quiet_NaN();
  assert(!core.step(measured, velocity, 0.001, request));
  assert(!core.tracking());
  velocity[0] = 0.0;
  assert(!core.step(measured, velocity, 0.0, request));
  measured[3] = std::numeric_limits<double>::infinity();
  assert(!core.step(measured, velocity, 0.001, request));
  return 0;
}
