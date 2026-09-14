// These checks must execute in the Release builds used by the Control image.
#ifdef NDEBUG
#undef NDEBUG
#endif
#include <cassert>
#include <chrono>
#include <cmath>
#include <functional>
#include <limits>
#include <memory>
#include <thread>
#include <vector>

#include "mios_ros2_runtime/ros2_gripper_client.hpp"

namespace {
using namespace std::chrono_literals;
using Grasp = franka_msgs::action::Grasp;
using Move = franka_msgs::action::Move;

bool spin_until(rclcpp::executors::SingleThreadedExecutor& executor,
                const std::function<bool()>& predicate) {
  const auto deadline = std::chrono::steady_clock::now() + 2s;
  while (std::chrono::steady_clock::now() < deadline) {
    executor.spin_some();
    if (predicate()) {
      return true;
    }
    std::this_thread::sleep_for(2ms);
  }
  return predicate();
}

void spin_for(rclcpp::executors::SingleThreadedExecutor& executor,
              const std::chrono::milliseconds duration) {
  const auto deadline = std::chrono::steady_clock::now() + duration;
  while (std::chrono::steady_clock::now() < deadline) {
    executor.spin_some();
    std::this_thread::sleep_for(2ms);
  }
}
}  // namespace

int main(int argc, char* argv[]) {
  rclcpp::init(argc, argv);
  {
    auto node = std::make_shared<rclcpp::Node>("test_ros2_gripper_client");
    auto fake_node = std::make_shared<rclcpp::Node>("test_ros2_gripper_server");
    mios_ros2_runtime::Ros2GripperClient client(
        *node, "/test/grasp", "/test/move", "/test/homing", "/test/stop",
        "/test/joint_states", 0.08);

    bool callback_called = false;
    mios_ros2_runtime::GripperOperationResult result;
    const auto capture = [&callback_called, &result](
                             const mios_ros2_runtime::GripperOperationResult& callback_result) {
      callback_called = true;
      result = callback_result;
    };

    // Reject malformed requests before discovery or any ROS action request.
    assert(!client.grasp(-0.01, 0.1, 1.0, 0.005, 0.005, capture));
    assert(callback_called && !result.accepted && !result.success);
    assert(result.message == "Invalid gripper grasp values.");
    callback_called = false;
    assert(!client.move(0.01, 0.0, capture));
    assert(callback_called && !result.accepted && !result.success);
    assert(result.message == "Invalid gripper move values.");

    // Homing and stopping retain their server checks, independent of feedback.
    callback_called = false;
    assert(!client.home(capture));
    assert(callback_called && !result.accepted);
    assert(result.message == "Gripper action server is not ready.");
    callback_called = false;
    assert(!client.stop(capture));
    assert(callback_called && !result.accepted);
    assert(result.message == "Gripper stop service is not ready.");

    std::vector<std::shared_ptr<rclcpp_action::ServerGoalHandle<Grasp>>> grasps;
    std::vector<std::shared_ptr<rclcpp_action::ServerGoalHandle<Move>>> moves;
    auto grasp_server = rclcpp_action::create_server<Grasp>(
        fake_node, "/test/grasp",
        [](const rclcpp_action::GoalUUID&, std::shared_ptr<const Grasp::Goal>) {
          return rclcpp_action::GoalResponse::ACCEPT_AND_EXECUTE;
        },
        [](std::shared_ptr<rclcpp_action::ServerGoalHandle<Grasp>>) {
          return rclcpp_action::CancelResponse::REJECT;
        },
        [&grasps](std::shared_ptr<rclcpp_action::ServerGoalHandle<Grasp>> goal) {
          grasps.push_back(std::move(goal));
        });
    auto move_server = rclcpp_action::create_server<Move>(
        fake_node, "/test/move",
        [](const rclcpp_action::GoalUUID&, std::shared_ptr<const Move::Goal>) {
          return rclcpp_action::GoalResponse::ACCEPT_AND_EXECUTE;
        },
        [](std::shared_ptr<rclcpp_action::ServerGoalHandle<Move>>) {
          return rclcpp_action::CancelResponse::REJECT;
        },
        [&moves](std::shared_ptr<rclcpp_action::ServerGoalHandle<Move>> goal) {
          moves.push_back(std::move(goal));
        });
    auto publisher = fake_node->create_publisher<sensor_msgs::msg::JointState>(
        "/test/joint_states", rclcpp::QoS(1));
    auto grasp_discovery = rclcpp_action::create_client<Grasp>(node, "/test/grasp");
    auto move_discovery = rclcpp_action::create_client<Move>(node, "/test/move");
    rclcpp::executors::SingleThreadedExecutor executor;
    executor.add_node(node);
    executor.add_node(fake_node);
    assert(spin_until(executor, [&] {
      return publisher->get_subscription_count() > 0 &&
             grasp_discovery->action_server_is_ready() && move_discovery->action_server_is_ready();
    }));

    const auto assert_feedback_rejected = [&] {
      callback_called = false;
      assert(!client.grasp(0.02, 0.1, 5.0, 0.005, 0.005, capture));
      assert(callback_called && !result.accepted && !result.success);
      assert(result.message.find("feedback") != std::string::npos);
      callback_called = false;
      assert(!client.move(0.04, 0.1, capture));
      assert(callback_called && !result.accepted && !result.success);
      assert(result.message.find("feedback") != std::string::npos);
    };

    // A ready action server alone is insufficient. Nothing reaches either server.
    assert(!client.latest_state());
    assert(!client.fresh_state());
    assert_feedback_rejected();
    spin_for(executor, 30ms);
    assert(grasps.empty() && moves.empty());

    int stamp_seconds = 0;
    const auto publish_valid = [&](const double finger_position = 0.02) {
      sensor_msgs::msg::JointState message;
      message.header.stamp.sec = ++stamp_seconds;
      message.position = {finger_position, finger_position};
      publisher->publish(message);
      assert(spin_until(executor, [&] {
        const auto state = client.fresh_state();
        return state && state->stamp_nanoseconds == stamp_seconds * 1000000000LL;
      }));
    };
    publish_valid();
    assert(client.has_fresh_state(500ms));
    assert(!client.fresh_state(0ns));
    assert(!client.fresh_state(-1ns));
    assert(std::abs(client.fresh_state()->state.width - 0.04) < 1e-12);

    // Valid feedback permits the unchanged goal, and success updates only grasp status.
    callback_called = false;
    assert(client.grasp(0.02, 0.1, 5.0, 0.005, 0.006, capture));
    assert(spin_until(executor, [&] { return grasps.size() == 1; }));
    assert(grasps[0]->get_goal()->width == 0.02);
    assert(grasps[0]->get_goal()->speed == 0.1);
    assert(grasps[0]->get_goal()->force == 5.0);
    assert(grasps[0]->get_goal()->epsilon.inner == 0.005);
    assert(grasps[0]->get_goal()->epsilon.outer == 0.006);
    auto grasp_result = std::make_shared<Grasp::Result>();
    grasp_result->success = true;
    grasps[0]->succeed(grasp_result);
    assert(spin_until(executor, [&] { return callback_called; }));
    assert(result.accepted && result.success);
    assert(client.fresh_state()->state.is_grasped);
    assert(std::abs(client.fresh_state()->state.width - 0.04) < 1e-12);

    publish_valid();
    callback_called = false;
    assert(client.move(0.06, 0.1, capture));
    assert(spin_until(executor, [&] { return moves.size() == 1; }));
    assert(moves[0]->get_goal()->width == 0.06);
    assert(moves[0]->get_goal()->speed == 0.1);
    // Delay the result beyond the feedback budget. It cannot refresh the width.
    spin_for(executor, 550ms);
    assert(!client.fresh_state());
    assert(!client.has_fresh_state(500ms));
    assert(client.latest_state());  // History remains available for diagnostics.
    auto move_result = std::make_shared<Move::Result>();
    move_result->success = true;
    moves[0]->succeed(move_result);
    assert(spin_until(executor, [&] { return callback_called; }));
    assert(result.accepted && result.success);
    assert(!client.latest_state()->state.is_grasped);
    assert(!client.fresh_state());
    assert_feedback_rejected();
    spin_for(executor, 30ms);
    assert(grasps.size() == 1 && moves.size() == 1);

    // Invalid feedback immediately invalidates a previously fresh opening;
    // another valid sample is required before any new command can be sent.
    const std::vector<std::vector<double>> invalid_positions{
        {0.01}, {0.01, std::numeric_limits<double>::quiet_NaN()},
        {-0.01, 0.01}, {0.05, 0.05}};
    for (const auto& positions : invalid_positions) {
      publish_valid();
      sensor_msgs::msg::JointState invalid;
      invalid.position = positions;
      publisher->publish(invalid);
      assert(spin_until(executor, [&] { return !client.latest_state(); }));
      assert(!client.fresh_state());
      assert_feedback_rejected();
    }
    spin_for(executor, 30ms);
    assert(grasps.size() == 1 && moves.size() == 1);

    // Calibrated open-stop overtravel remains valid feedback, without clamping.
    publish_valid(0.040526);
    assert(std::abs(client.fresh_state()->state.width - 0.081052) < 1e-12);
    callback_called = false;
    assert(client.move(0.08, 0.1, capture));
    assert(spin_until(executor, [&] { return moves.size() == 2; }));
    moves[1]->succeed(move_result);
    assert(spin_until(executor, [&] { return callback_called; }));
    assert(result.accepted && result.success);

    executor.remove_node(fake_node);
    executor.remove_node(node);
    (void)grasp_server;
    (void)move_server;
  }
  rclcpp::shutdown();
  return 0;
}
