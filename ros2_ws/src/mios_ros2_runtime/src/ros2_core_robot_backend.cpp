#include "mios_ros2_runtime/ros2_core_robot_backend.hpp"

#include <algorithm>
#include <cmath>
#include <exception>
#include <functional>
#include <thread>
#include <utility>

#include "mios_ros2_runtime/mios_parameter_snapshot_translation.hpp"
#include "mios_ros2_runtime/robot_state_translation.hpp"

namespace mios_ros2_runtime {

Ros2CoreRobotBackend::Ros2CoreRobotBackend(
    Ros2RobotBackend& robot_backend, Ros2ArmCommandDispatcher& command_dispatcher,
    Ros2GripperClient& gripper_client, const std::chrono::milliseconds state_timeout,
    const std::chrono::milliseconds gripper_timeout, const bool allow_task_execution)
    : Ros2CoreRobotBackend(robot_backend, command_dispatcher, gripper_client,
                           nullptr, {}, state_timeout, gripper_timeout,
                           std::chrono::milliseconds(1), allow_task_execution, false) {}

Ros2CoreRobotBackend::Ros2CoreRobotBackend(
    Ros2RobotBackend& robot_backend, Ros2ArmCommandDispatcher& command_dispatcher,
    Ros2GripperClient& gripper_client, Ros2RobotParameterClient* parameter_client,
    ParameterSnapshotProvider parameter_snapshot_provider,
    const std::chrono::milliseconds state_timeout,
    const std::chrono::milliseconds gripper_timeout,
    const std::chrono::milliseconds parameter_timeout, const bool allow_task_execution,
    const bool allow_controller_owned_move_mode, ControllerSession* controller_session)
    : robot_backend_(robot_backend),
      command_dispatcher_(command_dispatcher),
      gripper_client_(gripper_client),
      parameter_client_(parameter_client),
      parameter_snapshot_provider_(std::move(parameter_snapshot_provider)),
      state_timeout_(std::max(state_timeout, std::chrono::milliseconds(1))),
      gripper_timeout_(std::max(gripper_timeout, std::chrono::milliseconds(1))),
      parameter_timeout_(std::max(parameter_timeout, std::chrono::milliseconds(1))),
      allow_task_execution_(allow_task_execution),
      allow_controller_owned_move_mode_(allow_controller_owned_move_mode),
      controller_session_(controller_session),
      state_observer_id_(robot_backend_.add_state_observer(
          [this](const RobotSnapshot& snapshot) { receive_state(snapshot); })) {}

Ros2CoreRobotBackend::~Ros2CoreRobotBackend() {
  stop_active_control();
  robot_backend_.remove_state_observer(state_observer_id_);
}

bool Ros2CoreRobotBackend::state_and_model_are_fresh() const {
  return robot_backend_.has_fresh_robot_state(state_timeout_) &&
         robot_backend_.has_fresh_robot_model(state_timeout_);
}

bool Ros2CoreRobotBackend::initialize() { return state_and_model_are_fresh(); }

bool Ros2CoreRobotBackend::connect_to_robot(const std::optional<std::string>& /*ip*/) {
  // ROS discovery and franka_hardware own the physical connection.
  return state_and_model_are_fresh();
}

bool Ros2CoreRobotBackend::connect_to_gripper(const std::optional<std::string>& /*ip*/) {
  // A gripper action server is checked only when a gripper request is made.
  return true;
}

void Ros2CoreRobotBackend::disconnect_from_robot() {
  stop_active_control();
  // The Core node calls this before stopping its ROS executor. Retry an earlier
  // uncertain release after any in-flight control call has finished cleanup.
  std::lock_guard<std::mutex> session_lock(session_mutex_);
  if (controller_session_) {
    const auto released = controller_session_->release();
    if (released.exception) {
      RCLCPP_ERROR(rclcpp::get_logger("mios_ros2_core"), "Controller release at shutdown failed: %s",
                   released.error_msg.c_str());
    }
  }
}

void Ros2CoreRobotBackend::disconnect_from_gripper() {
  if (!allow_task_execution_) {
    return;
  }
  (void)wait_for_gripper_operation(
      [this](Ros2GripperClient::CompletionCallback completion) {
        return gripper_client_.stop(std::move(completion));
      });
}

mios::ControlReturnType Ros2CoreRobotBackend::recover() {
  return {true, "Ros2RecoveryNotConfigured",
          "ROS error recovery is intentionally delegated to the operator/Desk adapter."};
}

bool Ros2CoreRobotBackend::pre_run_checks() const {
  if (!state_and_model_are_fresh()) {
    return false;
  }
  const auto state = robot_backend_.latest_mios_robot_state();
  return state.has_value() &&
         is_pre_run_robot_mode_permitted(state->robot_mode, allow_controller_owned_move_mode_) &&
         !state->user_stopped;
}

bool Ros2CoreRobotBackend::is_pre_run_robot_mode_permitted(
    const mios::control::RobotMode mode, const bool allow_controller_owned_move_mode) {
  return mode == mios::control::RobotMode::kIdle ||
         (allow_controller_owned_move_mode && mode == mios::control::RobotMode::kMove);
}

mios::ControlReturnType Ros2CoreRobotBackend::control(const mios::control::CommandMode mode,
                                                       ControlCallback callback) {
  if (!allow_task_execution_) {
    return {true, "TaskExecutionDisabled",
            "Set enable_core_task_execution only after hardware commissioning."};
  }
  if (!callback) {
    return {true, "InvalidControlCallback", "MIOS Core supplied an empty control callback."};
  }
  if (mode != mios::control::CommandMode::kTorque) {
    return {true, "UnsupportedControlMode", "Core manages only the commissioned effort controller; use torque control modes."};
  }
  if (!allow_controller_owned_move_mode_ || !controller_session_) {
    return {true, "ControllerManagementUnavailable", "Native controller management and commissioned MOVE ownership are required."};
  }
  if (!pre_run_checks()) {
    return {true, "RobotNotReady",
            "Fresh permitted ROS robot state and model data are required."};
  }
  std::unique_lock<std::mutex> session_lock(session_mutex_, std::try_to_lock);
  if (!session_lock.owns_lock()) {
    return {true, "ControlAlreadyActive", "Only one MIOS Core control callback may run at once."};
  }
  {
    std::lock_guard<std::mutex> lock(control_mutex_);
    stop_requested_ = false;
  }
  auto result = controller_session_->acquire([this](const double threshold) {
    const auto state = robot_backend_.latest_mios_robot_state();
    if (!pre_run_checks() || !state || state->robot_mode != mios::control::RobotMode::kIdle ||
        !gripper_client_.fresh_state()) return false;
    for (std::size_t index = 0; index < state->position.size(); ++index) {
      if (!std::isfinite(state->position[index]) || !std::isfinite(state->velocity[index]) ||
          std::abs(state->velocity[index]) > threshold) return false;
    }
    std::lock_guard<std::mutex> lock(control_mutex_);
    return !stop_requested_;
  });
  if (!result.exception) {
    std::unique_lock<std::mutex> lock(control_mutex_);
    if (stop_requested_) {
      result = {true, "ControlStopped", "Control was stopped while acquiring its controller."};
    } else {
      const std::uint64_t generation = next_control_generation_++;
      active_control_.emplace(ActiveControl{generation, mode, std::move(callback)});
      while (!active_control_->complete) {
        control_complete_.wait_for(lock, std::chrono::milliseconds(20));
        if (active_control_->complete) break;
        lock.unlock();
        const bool fresh = pre_run_checks() && gripper_client_.fresh_state().has_value();
        lock.lock();
        if (!fresh && !active_control_->complete) {
          active_control_->result = {true, "RobotFeedbackLost", "Fresh permitted arm/model/gripper feedback was lost during control."};
          active_control_->complete = true;
        }
      }
      result = active_control_->result;
    }
  }
  // Wait for a copied callback to finish before Core tears down its executor.
  // No service call runs while a state/dispatch/control mutex is held.
  {
    std::lock_guard<std::mutex> callback_lock(callback_mutex_);
    std::lock_guard<std::mutex> dispatch_lock(dispatch_mutex_);
    std::lock_guard<std::mutex> lock(control_mutex_);
    active_control_.reset();
  }
  const auto state_before_release = robot_backend_.latest_snapshot();
  const auto released = controller_session_->release();
  if (released.exception) {
    if (!result.exception) return released;
    result.error_msg += " Release also failed: " + released.error_msg;
  } else if (!result.exception) {
    // controller_manager acknowledgement and state publication are asynchronous.
    // A following skill must not attempt acquisition against the previous MOVE sample.
    const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(1);
    bool settled = false;
    do {
      const auto state = robot_backend_.latest_snapshot();
      settled = state && robot_backend_.has_fresh_robot_state(state_timeout_) &&
                state->robot_mode == RobotRuntimeMode::kIdle && !state->user_stopped &&
                (!state_before_release || state->stamp_nanoseconds > state_before_release->stamp_nanoseconds);
      if (!settled) std::this_thread::sleep_for(std::chrono::milliseconds(5));
    } while (!settled && std::chrono::steady_clock::now() < deadline);
    if (!settled) {
      return {true, "ControllerReleasedRobotNotIdle", "Effort controller is inactive but a new IDLE robot state was not observed."};
    }
  }
  return result;
}

bool Ros2CoreRobotBackend::is_control_active() const {
  std::lock_guard<std::mutex> lock(control_mutex_);
  return active_control_ && !active_control_->complete && active_control_->command_dispatched;
}

void Ros2CoreRobotBackend::set_robot_parameter_provider(
    ParameterSnapshotProvider provider) {
  std::lock_guard<std::mutex> lock(parameter_provider_mutex_);
  parameter_snapshot_provider_ = std::move(provider);
}

bool Ros2CoreRobotBackend::set_robot_parameters() {
  if (!allow_task_execution_ || !parameter_client_) {
    return false;
  }
  // Franka parameter services are only valid when no FCI motion is active.
  // In the ROS-only deployment an arm command controller owns FCI throughout
  // a Core task, so a disabled parameter client deliberately preserves the
  // Desk-provisioned parameters and lets task setup continue.  Returning
  // false here would make unrelated operations such as selecting the active
  // grasped object fail even though they do not require a parameter update.
  if (!parameter_client_->parameter_application_enabled()) {
    return true;
  }
  ParameterSnapshotProvider provider;
  {
    std::lock_guard<std::mutex> lock(parameter_provider_mutex_);
    provider = parameter_snapshot_provider_;
  }
  if (!provider) {
    return false;
  }
  std::optional<mios::control::RobotParameters> parameters;
  try {
    parameters = provider();
  } catch (...) {
    return false;
  }
  if (!parameters) {
    return false;
  }
  const auto snapshot = make_robot_parameter_snapshot(*parameters);
  if (!snapshot) {
    return false;
  }
  return wait_for_parameter_operation(*snapshot);
}

bool Ros2CoreRobotBackend::get_robot_snapshot(mios::control::RobotState& robot_state,
                                              mios::control::RobotModel& robot_model,
                                              mios::control::GripperState& gripper_state) const {
  if (!state_and_model_are_fresh()) {
    return false;
  }
  const auto state = robot_backend_.latest_mios_robot_state();
  const auto model = robot_backend_.latest_robot_model();
  if (!state || !model) {
    return false;
  }
  robot_state = *state;
  robot_model = model->model;
  // JointState exposes the opening width while action results maintain the
  // grasp flag. Fields not published upstream (temperature) remain neutral.
  const auto gripper = gripper_client_.fresh_state();
  if (allow_task_execution_ && !gripper) return false;
  gripper_state = gripper ? gripper->state : mios::control::GripperState{};
  return true;
}

bool Ros2CoreRobotBackend::wait_for_gripper_operation(
    const std::function<bool(Ros2GripperClient::CompletionCallback)>& start_operation) const {
  if (!allow_task_execution_) {
    return false;
  }
  struct Completion {
    std::mutex mutex;
    std::condition_variable condition;
    bool complete{false};
    GripperOperationResult result;
  };
  const auto completion = std::make_shared<Completion>();
  const bool sent = start_operation([completion](const GripperOperationResult& result) {
    std::lock_guard<std::mutex> lock(completion->mutex);
    completion->result = result;
    completion->complete = true;
    completion->condition.notify_all();
  });
  if (!sent) {
    return false;
  }
  std::unique_lock<std::mutex> lock(completion->mutex);
  if (!completion->condition.wait_for(lock, gripper_timeout_,
                                       [&completion] { return completion->complete; })) {
    return false;
  }
  return completion->result.accepted && completion->result.success;
}

bool Ros2CoreRobotBackend::wait_for_parameter_operation(
    const RobotParameterSnapshot& snapshot) const {
  struct Completion {
    std::mutex mutex;
    std::condition_variable condition;
    bool complete{false};
    RobotParameterOperationResult result;
  };
  const auto completion = std::make_shared<Completion>();
  const bool sent = parameter_client_->apply(snapshot, [completion](
                                                       const RobotParameterOperationResult& result) {
    std::lock_guard<std::mutex> lock(completion->mutex);
    completion->result = result;
    completion->complete = true;
    completion->condition.notify_all();
  });
  if (!sent) {
    return false;
  }
  std::unique_lock<std::mutex> lock(completion->mutex);
  if (!completion->condition.wait_for(lock, parameter_timeout_,
                                       [&completion] { return completion->complete; })) {
    return false;
  }
  return completion->result.accepted && completion->result.success;
}

bool Ros2CoreRobotBackend::grasp(const double width, const double speed, const double force,
                                 const double epsilon_inner, const double epsilon_outer) const {
  return wait_for_gripper_operation([this, width, speed, force, epsilon_inner, epsilon_outer](
                                        Ros2GripperClient::CompletionCallback completion) {
    return gripper_client_.grasp(width, speed, force, epsilon_inner, epsilon_outer,
                                 std::move(completion));
  });
}

bool Ros2CoreRobotBackend::move_to_finger_position(
    const double width, const double speed) const {
  return wait_for_gripper_operation([this, width, speed](Ros2GripperClient::CompletionCallback completion) {
    return gripper_client_.move(width, speed, std::move(completion));
  });
}

bool Ros2CoreRobotBackend::home_gripper() const {
  return wait_for_gripper_operation([this](Ros2GripperClient::CompletionCallback completion) {
    return gripper_client_.home(std::move(completion));
  });
}

bool Ros2CoreRobotBackend::unlock_brakes() { return false; }
bool Ros2CoreRobotBackend::lock_brakes() { return false; }
bool Ros2CoreRobotBackend::shutdown_robot() { return false; }
bool Ros2CoreRobotBackend::reboot_robot() { return false; }

void Ros2CoreRobotBackend::complete_active_control(const std::uint64_t generation,
                                                   mios::ControlReturnType result) {
  std::lock_guard<std::mutex> lock(control_mutex_);
  if (!active_control_ || active_control_->generation != generation || active_control_->complete) {
    return;
  }
  active_control_->result = std::move(result);
  active_control_->complete = true;
  control_complete_.notify_all();
}

void Ros2CoreRobotBackend::receive_state(const RobotSnapshot& snapshot) {
  std::lock_guard<std::mutex> callback_lock(callback_mutex_);
  ControlCallback callback;
  mios::control::CommandMode mode{};
  std::uint64_t generation = 0;
  double period_seconds = 0.001;
  {
    std::lock_guard<std::mutex> lock(control_mutex_);
    if (!active_control_ || active_control_->complete) {
      return;
    }
    generation = active_control_->generation;
    mode = active_control_->mode;
    callback = active_control_->callback;
    if (snapshot.stamp_nanoseconds > active_control_->previous_stamp_nanoseconds) {
      const std::int64_t delta = snapshot.stamp_nanoseconds - active_control_->previous_stamp_nanoseconds;
      if (active_control_->previous_stamp_nanoseconds > 0 && delta > 0 && delta <= 100000000) {
        period_seconds = static_cast<double>(delta) / 1.0e9;
      }
      active_control_->previous_stamp_nanoseconds = snapshot.stamp_nanoseconds;
    }
  }

  const auto model = robot_backend_.latest_robot_model();
  if (!model || !robot_backend_.has_fresh_robot_model(state_timeout_)) {
    complete_active_control(generation,
                            {true, "RobotModelUnavailable", "The ROS model snapshot is absent or stale."});
    return;
  }
  const auto gripper = gripper_client_.fresh_state();
  if (!gripper) {
    complete_active_control(generation, {true, "GripperFeedbackUnavailable", "Fresh valid gripper feedback is required during control."});
    return;
  }

  mios::control::ArmCommand command;
  try {
    command = callback(to_mios_robot_state(snapshot), model->model, gripper->state, period_seconds);
  } catch (const std::exception& error) {
    complete_active_control(generation, {true, "ControlCallbackException", error.what()});
    return;
  } catch (...) {
    complete_active_control(generation,
                            {true, "ControlCallbackException", "Unknown exception from MIOS Core callback."});
    return;
  }
  if (command.mode != mode) {
    complete_active_control(generation,
                            {true, "CommandModeMismatch", "MIOS Core callback changed its control mode."});
    return;
  }

  std::lock_guard<std::mutex> dispatch_lock(dispatch_mutex_);
  {
    std::lock_guard<std::mutex> control_lock(control_mutex_);
    if (!active_control_ || active_control_->generation != generation || active_control_->complete) {
      return;
    }
  }
  if (!command_dispatcher_.dispatch(command, snapshot.user_stopped)) {
    complete_active_control(generation,
                            {true, "CommandDispatchFailed", "ROS rejected the translated MIOS command."});
    return;
  }
  {
    std::lock_guard<std::mutex> lock(control_mutex_);
    if (active_control_ && active_control_->generation == generation && !active_control_->complete) {
      active_control_->command_dispatched = true;
    }
  }
  if (command.motion_finished) {
    complete_active_control(generation, {false, "None", ""});
  }
}

void Ros2CoreRobotBackend::stop_active_control() {
  std::lock_guard<std::mutex> dispatch_lock(dispatch_mutex_);
  mios::control::ArmCommand stop_command;
  bool should_dispatch = false;
  {
    std::lock_guard<std::mutex> lock(control_mutex_);
    stop_requested_ = true;
    if (!active_control_ || active_control_->complete) {
      return;
    }
    stop_command.mode = active_control_->mode;
    stop_command.motion_finished = true;
    active_control_->result = {true, "ControlStopped", "MIOS Core control was stopped."};
    active_control_->complete = true;
    should_dispatch = true;
    control_complete_.notify_all();
  }
  if (should_dispatch) {
    (void)command_dispatcher_.dispatch(stop_command, true);
  }
}

}  // namespace mios_ros2_runtime
