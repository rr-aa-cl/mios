// Copyright 2026 MIOS contributors
// SPDX-License-Identifier: Apache-2.0

// Exercise the production manager and upstream fake hardware, with no robot I/O.
// The barrier controller only determines when the non-RT switch can finish.
#include <atomic>
#include <chrono>
#include <condition_variable>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <future>
#include <mutex>
#include <thread>

#include "controller_manager_test_common.hpp"
#include "lifecycle_msgs/msg/state.hpp"
#include "rcutils/logging.h"
#include "ros2_control_test_assets/test_hardware_interface_constants.hpp"
#include "test_controller/test_controller.hpp"

namespace
{
using namespace std::chrono_literals;
using controller_interface::return_type;
using lifecycle_msgs::msg::State;
using namespace ros2_control_test_assets;

// A deadlock must fail the test process, not leave an async-future destructor
// waiting forever. CTest supplies a second, outer timeout as well.
class Watchdog
{
public:
  Watchdog() : worker_([this] {
    std::unique_lock<std::mutex> lock(mutex_);
    if (!cv_.wait_for(lock, 12s, [this] { return finished_; }))
    {
      std::fputs("DEADLOCK WATCHDOG: controller-manager test did not finish\n", stderr);
      std::fflush(stderr);
      std::_Exit(124);
    }
  }) {}
  ~Watchdog()
  {
    {
      std::lock_guard<std::mutex> lock(mutex_);
      finished_ = true;
    }
    cv_.notify_all();
    worker_.join();
  }
private:
  std::mutex mutex_;
  std::condition_variable cv_;
  bool finished_ = false;
  std::thread worker_;
};

class BarrierController : public test_controller::TestController
{
public:
  CallbackReturn on_deactivate(const rclcpp_lifecycle::State &) override
  {
    entered.store(true);
    std::unique_lock<std::mutex> lock(mutex);
    cv.wait(lock, [this] { return may_finish; });
    return CallbackReturn::SUCCESS;
  }
  std::atomic<bool> entered{false};
  std::mutex mutex;
  std::condition_variable cv;
  bool may_finish = false;
};

std::atomic<bool> switch_succeeded{false};
rcutils_logging_output_handler_t previous_log_handler = nullptr;

void observe_switch_log(
  const rcutils_log_location_t * location, int severity, const char * name,
  rcutils_time_point_value_t timestamp, const char * format, va_list * arguments)
{
  // Never block a logging callback: doing so would add an artificial log-lock
  // dependency. The real manager still owns its list mutex at this log site.
  if (std::strcmp(format, "Successfully switched controllers!") == 0)
  {
    switch_succeeded.store(true);
  }
  previous_log_handler(location, severity, name, timestamp, format, arguments);
}

class ObserveSwitchLog
{
public:
  ObserveSwitchLog()
  {
    switch_succeeded.store(false);
    previous_log_handler = rcutils_logging_get_output_handler();
    rcutils_logging_set_output_handler(observe_switch_log);
  }
  ~ObserveSwitchLog() { rcutils_logging_set_output_handler(previous_log_handler); }
};

class TestableManager : public controller_manager::ControllerManager
{
public:
  using ControllerManager::ControllerManager;
  unsigned int actuator_state() const
  {
    return resource_manager_->get_components_status().at(TEST_ACTUATOR_HARDWARE_NAME).state.id();
  }
};

class DeactivateSwitchTest : public ControllerManagerFixture<TestableManager>,
  public testing::WithParamInterface<bool>
{
public:
  DeactivateSwitchTest()
  : ControllerManagerFixture<TestableManager>(minimal_robot_urdf_no_limits) {}

  void configure(
    const std::shared_ptr<test_controller::TestController> & controller,
    const std::string & name, const std::vector<std::string> & commands,
    const std::vector<std::string> & states)
  {
    ASSERT_NE(nullptr, cm_->add_controller(controller, name, test_controller::TEST_CONTROLLER_CLASS_NAME));
    controller->set_command_interface_configuration(
      {controller_interface::interface_configuration_type::INDIVIDUAL, commands});
    controller->set_state_interface_configuration(
      {controller_interface::interface_configuration_type::INDIVIDUAL, states});
    ASSERT_EQ(return_type::OK, cm_->configure_controller(name));
  }
};

TEST_P(DeactivateSwitchTest, hardware_deactivate_does_not_deadlock_non_realtime_switch)
{
  Watchdog watchdog;
  auto barrier = std::make_shared<BarrierController>();
  std::shared_ptr<test_controller::TestController> actuator =
    GetParam() ? barrier : std::make_shared<test_controller::TestController>();
  std::shared_ptr<test_controller::TestController> switching =
    GetParam() ? std::make_shared<test_controller::TestController>() : barrier;
  auto broadcaster = std::make_shared<test_controller::TestController>();
  configure(actuator, "actuator", TEST_ACTUATOR_HARDWARE_COMMAND_INTERFACES,
    TEST_ACTUATOR_HARDWARE_STATE_INTERFACES);
  configure(switching, "switching", TEST_SYSTEM_HARDWARE_COMMAND_INTERFACES,
    TEST_SYSTEM_HARDWARE_STATE_INTERFACES);
  configure(broadcaster, "broadcaster", {}, TEST_ACTUATOR_HARDWARE_STATE_INTERFACES);
  switch_test_controllers({"actuator", "switching", "broadcaster"}, {}, STRICT);
  ASSERT_EQ(State::PRIMARY_STATE_ACTIVE, actuator->get_lifecycle_state().id());

  // The fake hardware's command remains set until the next write, even if
  // the switch releases the actuator's loaned command interface beforehand.
  std::vector<double> commands(TEST_ACTUATOR_HARDWARE_COMMAND_INTERFACES.size(), 0.0);
  commands.at(0) = test_constants::WRITE_DEACTIVATE_VALUE;
  actuator->set_external_commands_for_testing(commands);
  ASSERT_EQ(return_type::OK, cm_->update(time_, PERIOD));

  ObserveSwitchLog observe;
  auto switching_future = std::async(std::launch::async, [this] {
    return cm_->switch_controller(
      {}, {GetParam() ? "actuator" : "switching"}, STRICT, false, rclcpp::Duration(2, 0));
  });
  std::atomic<bool> run_update{true};
  std::thread updater([&] {
    while (run_update.load() && !barrier->entered.load())
    {
      cm_->update(time_, PERIOD);
      std::this_thread::sleep_for(1ms);
    }
  });
  const auto deadline = std::chrono::steady_clock::now() + 3s;
  while (!barrier->entered.load() && std::chrono::steady_clock::now() < deadline)
  {
    std::this_thread::sleep_for(1ms);
  }
  run_update.store(false);
  updater.join();
  ASSERT_TRUE(barrier->entered.load());
  {
    std::lock_guard<std::mutex> lock(barrier->mutex);
    barrier->may_finish = true;
  }
  barrier->cv.notify_all();
  while (!switch_succeeded.load() && std::chrono::steady_clock::now() < deadline)
  {
    std::this_thread::sleep_for(1ms);
  }
  ASSERT_TRUE(switch_succeeded.load());
  ASSERT_EQ(std::future_status::timeout, switching_future.wait_for(0ms));

  std::fputs("ENTERING WRITE: hardware DEACTIVATE while non-RT switch awaits RT list\n", stderr);
  std::fflush(stderr);
  cm_->write(time_, PERIOD);  // Unpatched 4.47 deadlocks on the controller-list mutex here.
  // The success log precedes publication of the new list. Keep the RT reader
  // advancing until the service has finished, without assuming log latency or
  // which thread the scheduler runs immediately after that log message.
  const auto switch_deadline = std::chrono::steady_clock::now() + 2s;
  while (switching_future.wait_for(0ms) != std::future_status::ready &&
    std::chrono::steady_clock::now() < switch_deadline)
  {
    cm_->update(time_, PERIOD);
    std::this_thread::sleep_for(1ms);
  }
  ASSERT_EQ(std::future_status::ready, switching_future.wait_for(2s));
  EXPECT_EQ(return_type::OK, switching_future.get());
  EXPECT_EQ(State::PRIMARY_STATE_INACTIVE, actuator->get_lifecycle_state().id());
  EXPECT_EQ(GetParam() ? State::PRIMARY_STATE_ACTIVE : State::PRIMARY_STATE_INACTIVE,
    switching->get_lifecycle_state().id());
  EXPECT_EQ(State::PRIMARY_STATE_ACTIVE, broadcaster->get_lifecycle_state().id());
  EXPECT_EQ(State::PRIMARY_STATE_INACTIVE, cm_->actuator_state());
  // This takes the same controller-list mutex used by the list service.
  EXPECT_EQ(3u, cm_->get_loaded_controllers().size());

  // Run the actual executor and services after the fault. The coalesced activity
  // notification must still publish the final inactive hardware/controller,
  // while retaining the state-only broadcaster.
  auto client_node = std::make_shared<rclcpp::Node>("deactivate_switch_client");
  controller_manager_msgs::msg::ControllerManagerActivity::SharedPtr activity;
  auto subscription = client_node->create_subscription<
    controller_manager_msgs::msg::ControllerManagerActivity>(
    "/test_controller_manager/activity", rclcpp::QoS(1).reliable().transient_local(),
    [&](controller_manager_msgs::msg::ControllerManagerActivity::SharedPtr message) {
      activity = message;
    });
  executor_->add_node(cm_);
  executor_->add_node(client_node);
  auto controllers_client = client_node->create_client<
    controller_manager_msgs::srv::ListControllers>("/test_controller_manager/list_controllers");
  auto hardware_client = client_node->create_client<
    controller_manager_msgs::srv::ListHardwareComponents>(
    "/test_controller_manager/list_hardware_components");
  ASSERT_TRUE(controllers_client->wait_for_service(2s));
  ASSERT_TRUE(hardware_client->wait_for_service(2s));
  auto controllers_reply = controllers_client->async_send_request(
    std::make_shared<controller_manager_msgs::srv::ListControllers::Request>());
  ASSERT_EQ(rclcpp::FutureReturnCode::SUCCESS,
    executor_->spin_until_future_complete(controllers_reply, 2s));
  EXPECT_EQ(3u, controllers_reply.get()->controller.size());
  auto hardware_reply = hardware_client->async_send_request(
    std::make_shared<controller_manager_msgs::srv::ListHardwareComponents::Request>());
  ASSERT_EQ(rclcpp::FutureReturnCode::SUCCESS,
    executor_->spin_until_future_complete(hardware_reply, 2s));
  EXPECT_EQ(3u, hardware_reply.get()->component.size());
  const auto activity_deadline = std::chrono::steady_clock::now() + 2s;
  while (!activity && std::chrono::steady_clock::now() < activity_deadline)
  {
    executor_->spin_some();
    std::this_thread::sleep_for(1ms);
  }
  ASSERT_NE(nullptr, activity);
  auto state_of = [](const auto & components, const std::string & name) {
    for (const auto & component : components)
    {
      if (component.name == name) { return component.state.id; }
    }
    return State::PRIMARY_STATE_UNKNOWN;
  };
  EXPECT_EQ(State::PRIMARY_STATE_INACTIVE, state_of(activity->controllers, "actuator"));
  EXPECT_EQ(State::PRIMARY_STATE_ACTIVE, state_of(activity->controllers, "broadcaster"));
  EXPECT_EQ(State::PRIMARY_STATE_INACTIVE,
    state_of(activity->hardware_components, TEST_ACTUATOR_HARDWARE_NAME));
  executor_->remove_node(client_node);
  executor_->remove_node(cm_);
}

INSTANTIATE_TEST_SUITE_P(
  SwitchTarget, DeactivateSwitchTest, testing::Bool(),
  [](const testing::TestParamInfo<bool> & parameter) {
    return parameter.param ? "SameController" : "UnrelatedController";
  });
}  // namespace
