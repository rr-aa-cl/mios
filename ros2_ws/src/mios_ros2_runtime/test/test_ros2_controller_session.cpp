// The production image builds Release; keep these offline checks executable.
#ifdef NDEBUG
#undef NDEBUG
#endif
#include <cassert>
#include <chrono>
#include <functional>
#include <future>
#include <limits>
#include <map>
#include <memory>
#include <string>
#include <thread>
#include <utility>
#include <vector>

#include "mios_ros2_runtime/ros2_controller_session.hpp"
#include "rcl_interfaces/msg/parameter_type.hpp"

namespace {
using namespace std::chrono_literals;
using List = controller_manager_msgs::srv::ListControllers;
using Switch = controller_manager_msgs::srv::SwitchController;
using Parameters = rcl_interfaces::srv::GetParameters;
using Value = rcl_interfaces::msg::ParameterValue;
using ParameterType = rcl_interfaces::msg::ParameterType;
using Controller = controller_manager_msgs::msg::ControllerState;
using Session = mios_ros2_runtime::Ros2ControllerSession;

Value boolean(const bool value) {
  Value result;
  result.type = ParameterType::PARAMETER_BOOL;
  result.bool_value = value;
  return result;
}
Value number(const double value) {
  Value result;
  result.type = ParameterType::PARAMETER_DOUBLE;
  result.double_value = value;
  return result;
}
Value string(const std::string& value) {
  Value result;
  result.type = ParameterType::PARAMETER_STRING;
  result.string_value = value;
  return result;
}

class Fixture {
 public:
  Fixture() {
    static unsigned next_id = 0;
    const std::string suffix = std::to_string(++next_id);
    effort = "test_effort_" + suffix;
    position = "test_position_" + suffix;
    manager = "/test_manager_" + suffix;
    node = std::make_shared<rclcpp::Node>("controller_client_test_" + suffix);
    server_node = std::make_shared<rclcpp::Node>("controller_server_test_" + suffix);
    executor.add_node(node);
    executor.add_node(server_node);

    Controller command;
    command.name = effort;
    command.state = "inactive";
    command.type = "mios_ros2_control/MiosEffortController";
    states.controller.push_back(command);
    Controller native_position;
    native_position.name = position;
    native_position.state = "inactive";
    native_position.type = "mios_ros2_control/MiosJointPositionController";
    states.controller.push_back(native_position);
    Controller broadcaster;
    broadcaster.name = "test_state_broadcaster";
    broadcaster.state = "active";
    broadcaster.type = "franka_robot_state_broadcaster/FrankaRobotStateBroadcaster";
    states.controller.push_back(broadcaster);

    for (const auto& name : {"allow_effort_activation", "allow_zero_effort_activation",
                             "allow_runtime_effort_commands", "allow_runtime_actuator_commands",
                             "allow_runtime_cartesian_actuator_commands"}) {
      gates[name] = boolean(true);
    }
    gates["robot_state_safety_enabled"] = boolean(true);
    gates["robot_state_source"] = string("hardware");
    gates["activation_velocity_threshold"] = number(0.02);
    gates["allow_runtime_joint_position_commands"] = boolean(false);

    // Deferred responses let tests reproduce a request whose reply arrives
    // after the worker's timeout, without sleeping in an executor callback.
    list_service = server_node->create_service<List>(manager + "/list_controllers",
        [this](std::shared_ptr<rmw_request_id_t> header, std::shared_ptr<List::Request>) {
          ++list_calls;
          if (hold_list) return;
          if (foreign_on_second_list && list_calls == 2) add_foreign_owner();
          list_service->send_response(*header, states);
        });
    const auto parameters = [this](std::shared_ptr<rclcpp::Service<Parameters>> service,
                                  std::shared_ptr<rmw_request_id_t> header,
                                  std::shared_ptr<Parameters::Request> query) {
      ++parameter_calls;
      if (hold_parameters) return;
      Parameters::Response response;
      for (const auto& name : query->names) response.values.push_back(gates.at(name));
      if (incomplete_parameters && !response.values.empty()) response.values.pop_back();
      service->send_response(*header, response);
    };
    effort_service = server_node->create_service<Parameters>(
        "/" + effort + "/get_parameters", parameters);
    position_service = server_node->create_service<Parameters>(
        "/" + position + "/get_parameters", parameters);
    switch_service = server_node->create_service<Switch>(manager + "/switch_controller",
        [this](std::shared_ptr<rmw_request_id_t> header, std::shared_ptr<Switch::Request> request) {
          switches.push_back(*request);
          assert(request->strictness == Switch::Request::STRICT);
          assert(!request->activate_asap);
          assert(request->timeout.sec == 0 && request->timeout.nanosec == 80000000);
          if (!request->activate_controllers.empty()) {
            assert(request->activate_controllers == std::vector<std::string>{effort});
            assert(request->deactivate_controllers.empty());
            if (hold_activation) {
              pending_activation = std::move(header);
              return;
            }
            if (activation_side_effect) states.controller[0].state = "active";
            Switch::Response response;
            response.ok = activation_ok;
            switch_service->send_response(*header, response);
          } else {
            assert(request->deactivate_controllers == std::vector<std::string>{effort});
            assert(request->activate_controllers.empty());
            if (deactivation_side_effect) states.controller[0].state = "inactive";
            Switch::Response response;
            response.ok = deactivation_ok;
            switch_service->send_response(*header, response);
          }
        });
    session = std::make_unique<Session>(*node, manager, effort, position, 80ms);
  }

  ~Fixture() {
    session.reset();
    executor.remove_node(server_node);
    executor.remove_node(node);
  }

  mios::ControlReturnType run(const std::function<mios::ControlReturnType()>& operation) {
    auto future = std::async(std::launch::async, operation);
    const auto deadline = std::chrono::steady_clock::now() + 3s;
    while (future.wait_for(0ms) != std::future_status::ready &&
           std::chrono::steady_clock::now() < deadline) {
      executor.spin_some();
      std::this_thread::sleep_for(1ms);
    }
    assert(future.wait_for(0ms) == std::future_status::ready);
    return future.get();
  }

  mios::ControlReturnType acquire(const bool stationary = true) {
    return run([&] {
      return session->acquire([&](const double threshold) {
        ++stationary_calls;
        assert(threshold == 0.02);
        return stationary;
      });
    });
  }

  mios::ControlReturnType release() { return run([&] { return session->release(); }); }

  void add_foreign_owner() {
    Controller foreign;
    foreign.name = "foreign_controller";
    foreign.state = "active";
    foreign.type = "other/PositionController";
    foreign.claimed_interfaces = {"fr3_joint1/position"};
    states.controller.push_back(foreign);
  }

  void complete_late_activation() {
    assert(pending_activation);
    states.controller[0].state = "active";
    Switch::Response response;
    response.ok = true;
    switch_service->send_response(*pending_activation, response);
    pending_activation.reset();
    // The subsequent release drives the client executor while waiting for the
    // late response; no hardware or external ROS participant is involved.
  }

  std::string effort, position, manager;
  std::shared_ptr<rclcpp::Node> node, server_node;
  rclcpp::executors::SingleThreadedExecutor executor;
  rclcpp::Service<List>::SharedPtr list_service;
  rclcpp::Service<Switch>::SharedPtr switch_service;
  rclcpp::Service<Parameters>::SharedPtr effort_service, position_service;
  std::unique_ptr<Session> session;
  List::Response states;
  std::map<std::string, Value> gates;
  std::vector<Switch::Request> switches;
  std::shared_ptr<rmw_request_id_t> pending_activation;
  unsigned list_calls{0}, parameter_calls{0}, stationary_calls{0};
  bool hold_list{false}, hold_parameters{false}, incomplete_parameters{false};
  bool foreign_on_second_list{false}, hold_activation{false};
  bool activation_ok{true}, activation_side_effect{true};
  bool deactivation_ok{true}, deactivation_side_effect{true};
};

void assert_rejected_without_switch(Fixture& fixture) {
  const auto result = fixture.acquire();
  assert(result.exception && result.error == "ControllerActivationFailed");
  assert(fixture.switches.empty());
  assert(!fixture.release().exception);
  assert(fixture.switches.empty());
}

void test_success_and_stationary_check() {
  Fixture fixture;
  assert(!fixture.acquire().exception);
  assert(fixture.stationary_calls == 1);
  assert(fixture.states.controller[0].state == "active");
  assert(fixture.list_calls == 3);
  assert(fixture.switches.size() == 1);
  assert(!fixture.release().exception);
  assert(fixture.states.controller[0].state == "inactive");
  assert(fixture.switches.size() == 2);
  assert(!fixture.release().exception);
  assert(fixture.switches.size() == 2);
  assert(!fixture.acquire().exception);
  assert(!fixture.release().exception);

  Fixture moving;
  const auto refused = moving.acquire(false);
  assert(refused.exception);
  assert(refused.error_msg.find("stationary") != std::string::npos);
  assert(moving.switches.empty());
}

void test_gates_and_foreign_owners() {
  for (const auto& name : {"allow_effort_activation", "allow_zero_effort_activation",
                           "allow_runtime_effort_commands", "allow_runtime_actuator_commands",
                           "allow_runtime_cartesian_actuator_commands", "robot_state_safety_enabled"}) {
    Fixture fixture;
    fixture.gates[name] = boolean(false);
    assert_rejected_without_switch(fixture);
    assert(fixture.stationary_calls == 0);
  }
  {
    Fixture fixture;
    fixture.gates["allow_effort_activation"] = number(1.0);
    assert_rejected_without_switch(fixture);
  }
  {
    Fixture fixture;
    fixture.gates["robot_state_safety_enabled"] = number(1.0);
    assert_rejected_without_switch(fixture);
  }
  for (const auto& invalid_source : {string("topic"), boolean(true)}) {
    Fixture fixture;
    fixture.gates["robot_state_source"] = invalid_source;
    assert_rejected_without_switch(fixture);
  }
  for (const auto value : {0.0, -0.1, std::numeric_limits<double>::quiet_NaN()}) {
    Fixture fixture;
    fixture.gates["activation_velocity_threshold"] = number(value);
    assert_rejected_without_switch(fixture);
  }
  {
    Fixture fixture;
    fixture.incomplete_parameters = true;
    assert_rejected_without_switch(fixture);
  }
  {
    Fixture fixture;
    fixture.gates["allow_runtime_joint_position_commands"] = boolean(true);
    assert_rejected_without_switch(fixture);
  }
  {
    Fixture fixture;
    fixture.add_foreign_owner();
    assert_rejected_without_switch(fixture);
    assert(fixture.parameter_calls == 0);
  }
  {
    Fixture fixture;
    fixture.foreign_on_second_list = true;
    assert_rejected_without_switch(fixture);
    assert(fixture.stationary_calls == 1);
  }
  {
    Fixture fixture;
    fixture.states.controller[0].state = "active";
    assert_rejected_without_switch(fixture);
  }
  {
    Fixture fixture;
    fixture.states.controller[0].type = "other/EffortController";
    assert_rejected_without_switch(fixture);
  }
}

void test_read_timeouts_never_activate() {
  {
    Fixture fixture;
    fixture.hold_list = true;
    assert_rejected_without_switch(fixture);
    assert(fixture.parameter_calls == 0 && fixture.stationary_calls == 0);
  }
  {
    Fixture fixture;
    fixture.hold_parameters = true;
    assert_rejected_without_switch(fixture);
    assert(fixture.stationary_calls == 0);
  }
}

void test_failed_activation_side_effect_is_released() {
  Fixture fixture;
  fixture.activation_ok = false;
  const auto result = fixture.acquire();
  assert(result.exception);
  assert(fixture.states.controller[0].state == "active");
  assert(fixture.switches.size() == 1);
  assert(!fixture.release().exception);
  assert(fixture.states.controller[0].state == "inactive");
  assert(fixture.switches.size() == 2);
}

void test_late_activation_blocks_reacquire_until_release_verified() {
  Fixture fixture;
  fixture.hold_activation = true;
  const auto activation = fixture.acquire();
  assert(activation.exception && activation.error_msg.find("timed out") != std::string::npos);
  assert(fixture.pending_activation);
  const auto incomplete = fixture.release();
  assert(incomplete.exception && incomplete.error == "ControllerReleaseFailed");
  assert(fixture.states.controller[0].state == "inactive");
  assert(fixture.switches.size() == 2);  // A stop was attempted even with an unresolved start.
  const auto blocked = fixture.acquire();
  assert(blocked.exception && blocked.error == "ControllerOwnershipUnresolved");
  assert(fixture.switches.size() == 2);
  fixture.complete_late_activation();
  assert(!fixture.release().exception);
  assert(fixture.states.controller[0].state == "inactive");
  assert(fixture.switches.size() == 3);
  fixture.hold_activation = false;
  assert(!fixture.acquire().exception);
  assert(!fixture.release().exception);
}

void test_failed_release_keeps_ownership_blocked() {
  Fixture fixture;
  assert(!fixture.acquire().exception);
  fixture.deactivation_ok = false;
  fixture.deactivation_side_effect = false;
  assert(fixture.release().exception);
  assert(fixture.acquire().error == "ControllerOwnershipUnresolved");
  fixture.deactivation_ok = true;
  fixture.deactivation_side_effect = true;
  assert(!fixture.release().exception);
}
}  // namespace

int main(int argc, char* argv[]) {
  rclcpp::init(argc, argv);
  test_success_and_stationary_check();
  test_gates_and_foreign_owners();
  test_read_timeouts_never_activate();
  test_failed_activation_side_effect_is_released();
  test_late_activation_blocks_reacquire_until_release_verified();
  test_failed_release_keeps_ownership_blocked();
  rclcpp::shutdown();
  return 0;
}
