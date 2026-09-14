#ifdef NDEBUG
#undef NDEBUG
#endif
#include <atomic>
#include <cassert>
#include <chrono>
#include <future>
#include <memory>
#include <stdexcept>
#include <thread>

#include "mios_ros2_runtime/ros2_core_robot_backend.hpp"
#include "rclcpp/executors/single_threaded_executor.hpp"

using namespace std::chrono_literals;
using mios::control::CommandMode;

namespace {

template <typename Predicate>
void wait_until(Predicate predicate) {
  const auto deadline = std::chrono::steady_clock::now() + 3s;
  while (!predicate() && std::chrono::steady_clock::now() < deadline) std::this_thread::sleep_for(5ms);
  assert(predicate());
}

class FakeSession final : public mios_ros2_runtime::ControllerSession {
 public:
  mios::ControlReturnType acquire(const StationaryCheck& stationary) override {
    ++acquire_calls;
    while (block_acquire) std::this_thread::sleep_for(1ms);
    if (!stationary(0.01)) return {true, "NotStationary", "No current stationary state."};
    owned = true;
    if (fail_acquire) return {true, "InjectedActivationFailure", "Activation had a side effect."};
    return {false, "None", ""};
  }
  mios::ControlReturnType release() override {
    ++release_calls;
    owned = false;
    return fail_release ? mios::ControlReturnType{true, "InjectedReleaseFailure", "Release failed."}
                        : mios::ControlReturnType{false, "None", ""};
  }
  std::atomic<bool> owned{false}, block_acquire{false}, fail_acquire{false}, fail_release{false};
  std::atomic<int> acquire_calls{0}, release_calls{0};
};

}  // namespace

int main(int argc, char* argv[]) {
  rclcpp::init(argc, argv);
  auto node = std::make_shared<rclcpp::Node>("core_controller_lifecycle_test");
  auto state_pub = node->create_publisher<franka_msgs::msg::FrankaRobotState>("/lifecycle_test/state", 1);
  auto model_pub = node->create_publisher<mios_msgs::msg::MiosRobotModel>("/lifecycle_test/model", 1);
  auto gripper_pub = node->create_publisher<sensor_msgs::msg::JointState>("/lifecycle_test/gripper", 1);
  FakeSession session;
  std::atomic<bool> publish_robot{true}, publish_gripper{true};
  auto timer = node->create_wall_timer(10ms, [&] {
    if (publish_gripper) {
      sensor_msgs::msg::JointState gripper;
      gripper.header.stamp = node->now();
      gripper.position = {0.01, 0.01};
      gripper_pub->publish(gripper);
    }
    if (!publish_robot) return;
    mios_msgs::msg::MiosRobotModel model;
    model.stamp = node->now();
    model_pub->publish(model);
    franka_msgs::msg::FrankaRobotState state;
    state.header.stamp = node->now();
    state.robot_mode = session.owned ? state.ROBOT_MODE_MOVE : state.ROBOT_MODE_IDLE;
    state.measured_joint_state.position.assign(7, 0.0);
    state.measured_joint_state.velocity.assign(7, 0.0);
    state.measured_joint_state.effort.assign(7, 0.0);
    state.measured_joint_motor_state.position.assign(7, 0.0);
    state.measured_joint_motor_state.velocity.assign(7, 0.0);
    state.tau_ext_hat_filtered.effort.assign(7, 0.0);
    state.o_t_ee.pose.orientation.w = 1.0;
    state_pub->publish(state);
  });
  mios_ros2_runtime::Ros2RobotBackend robot(
      *node, "/lifecycle_test/state", "/lifecycle_test/model", "/lifecycle_test/effort",
      "/lifecycle_test/actuator", "/lifecycle_test/jv", "/lifecycle_test/cv",
      "/lifecycle_test/jp", "/lifecycle_test/cp");
  mios_ros2_runtime::Ros2ArmCommandDispatcher dispatcher(robot);
  mios_ros2_runtime::Ros2GripperClient gripper(
      *node, "/lifecycle_test/grasp", "/lifecycle_test/move", "/lifecycle_test/home",
      "/lifecycle_test/stop", "/lifecycle_test/gripper", 0.08);
  mios_ros2_runtime::Ros2CoreRobotBackend backend(
      robot, dispatcher, gripper, nullptr, {}, 100ms, 100ms, 100ms, true, true, &session);
  rclcpp::executors::SingleThreadedExecutor executor;
  executor.add_node(node);
  std::thread spin([&] { executor.spin(); });
  auto ready = [&] {
    const auto state = robot.latest_mios_robot_state();
    return backend.pre_run_checks() && gripper.fresh_state() && state &&
           state->robot_mode == mios::control::RobotMode::kIdle;
  };
  wait_until(ready);

  std::atomic<int> callbacks{0};
  std::atomic<bool> finish{false}, fail_callback{false};
  auto callback = [&](const auto&, const auto&, const auto& feedback, double) {
    ++callbacks;
    assert(session.owned);
    assert(feedback.width == 0.02);
    if (fail_callback) throw std::runtime_error("Injected callback failure");
    mios::control::ArmCommand command;
    command.mode = CommandMode::kTorque;
    command.motion_finished = finish;
    return command;
  };
  auto start = [&] { return std::async(std::launch::async, [&] { return backend.control(CommandMode::kTorque, callback); }); };
  auto done = [](auto& future) {
    assert(future.wait_for(3s) == std::future_status::ready);
    return future.get();
  };

  // Acquiring a controller cannot run callbacks or report control readiness.
  session.block_acquire = true;
  auto running = start();
  wait_until([&] { return session.acquire_calls == 1; });
  std::this_thread::sleep_for(40ms);
  assert(callbacks == 0 && !backend.is_control_active());
  session.block_acquire = false;
  wait_until([&] { return backend.is_control_active(); });
  assert(session.release_calls == 0 && session.owned);
  finish = true;
  assert(!done(running).exception);
  assert(session.release_calls == 1 && !session.owned && !backend.is_control_active());
  assert(ready());

  // Unsupported native command modes never claim the effort controller.
  const int acquired = session.acquire_calls;
  const auto unsupported = backend.control(CommandMode::kJointPosition, callback);
  assert(unsupported.exception && unsupported.error == "UnsupportedControlMode");
  assert(session.acquire_calls == acquired);

  // A failed activation reply can follow a side effect; release still runs.
  const int before_callbacks = callbacks;
  const int before_release = session.release_calls;
  session.fail_acquire = true;
  auto activation_failure = start();
  assert(done(activation_failure).error == "InjectedActivationFailure");
  assert(callbacks == before_callbacks && session.release_calls == before_release + 1 && !session.owned);
  session.fail_acquire = false;
  wait_until(ready);

  fail_callback = true;
  auto callback_failure = start();
  assert(done(callback_failure).error == "ControlCallbackException");
  assert(!session.owned && !backend.is_control_active());
  fail_callback = false;
  finish = false;
  wait_until(ready);

  auto stopped = start();
  wait_until([&] { return backend.is_control_active(); });
  backend.stop_active_control();
  assert(done(stopped).error == "ControlStopped");
  assert(!session.owned && !backend.is_control_active());
  wait_until(ready);

  // No state callbacks must not leave the Core worker blocked forever.
  auto feedback_lost = start();
  wait_until([&] { return backend.is_control_active(); });
  publish_robot = false;
  assert(done(feedback_lost).error == "RobotFeedbackLost");
  assert(!session.owned);
  publish_robot = true;
  wait_until(ready);

  // Commissioned snapshots cannot manufacture zero width from missing feedback.
  publish_gripper = false;
  std::this_thread::sleep_for(550ms);
  mios::control::RobotState state;
  mios::control::RobotModel model;
  mios::control::GripperState grip;
  assert(!backend.get_robot_snapshot(state, model, grip));
  auto missing_gripper = start();
  assert(done(missing_gripper).exception && !session.owned);
  publish_gripper = true;
  wait_until(ready);

  session.fail_release = true;
  finish = true;
  auto release_failure = start();
  assert(done(release_failure).error == "InjectedReleaseFailure");
  assert(!backend.is_control_active());
  session.fail_release = false;
  const int release_before_shutdown = session.release_calls;
  backend.disconnect_from_robot();
  assert(session.release_calls == release_before_shutdown + 1);

  executor.cancel();
  spin.join();
  executor.remove_node(node);
  rclcpp::shutdown();
  return 0;
}
