#pragma once


#include "franka/robot.h"
#include "franka/gripper.h"
#include "franka/model.h"
#include "franka/robot_state.h"
#include "franka/gripper_state.h"
#include "mios/softhand2/softhand2.hpp"

#include "mios/data_structures/parameters.hpp"
#include "mios/utils/types.hpp"

#include <string>
#include <optional>
#include <memory>
#include <functional>
#include <atomic>
#include <mutex>

namespace mios {

class Memory;

class PandaBody{
public:
    PandaBody(Memory* memory);
    bool initialize();
    bool connect_to_robot(const std::optional<std::string> &ip);
    bool connect_to_gripper(const std::optional<std::string> &ip);
    void disconnect_from_robot();
    void disconnect_from_gripper();
    ControlReturnType recover();

    bool pre_run_checks() const;

    bool start_desk_task(const std::string& task, const std::optional<std::string> &ip, const std::string user, const std::string &password);
    bool stop_desk_task(const std::optional<std::string> &ip, const std::string user, const std::string &password);
    void wait_for_desk_task(const std::optional<std::string> &ip, const std::string user, const std::string& password);
    bool shutdown_robot(const std::optional<std::string> &ip, const std::string user, const std::string& password);
    bool move_to_pack_pose(const std::optional<std::string> &ip, const std::string user, const std::string& password);
    bool unlock_brakes(const std::optional<std::string> &ip, const std::string user, const std::string& password);
    bool lock_brakes(const std::optional<std::string> &ip, const std::string user, const std::string& password);


    bool grasp(double width,double speed,double force,double epsilon_inner,double epsilon_outer) const;
    bool move_to_finger_position(double width, double speed) const;
    bool stop_gripper();
    bool home_gripper() const;
    bool is_hand_active();
    bool activate_fci();
    bool deactivate_fci();

public:
    ControlReturnType control(std::function<franka::Torques(const franka::RobotState &, franka::Duration)> controller_callback);
    ControlReturnType control(std::function<franka::CartesianVelocities(const franka::RobotState&, franka::Duration)> controller_callback);
    ControlReturnType control(std::function<franka::JointVelocities(const franka::RobotState&, franka::Duration)> controller_callback);
    ControlReturnType control(std::function<franka::CartesianPose(const franka::RobotState&, franka::Duration)> controller_callback);
    ControlReturnType control(std::function<franka::JointPositions(const franka::RobotState&, franka::Duration)> controller_callback);

    void dummy_control(std::function<franka::Torques(const franka::RobotState& state,franka::Duration)> controller_callback);
    void dummy_control(std::function<franka::CartesianVelocities(const franka::RobotState& state,franka::Duration)> controller_callback);
    void dummy_control(std::function<franka::JointVelocities(const franka::RobotState& state,franka::Duration)> controller_callback);
    void dummy_control(std::function<franka::CartesianPose(const franka::RobotState& state,franka::Duration)> controller_callback);
    void dummy_control(std::function<franka::JointPositions(const franka::RobotState& state,franka::Duration)> controller_callback);

public:
    bool set_robot_parameters();
    bool set_load(double load_m,std::array<double,3> load_com,std::array<double,9> load_I);
    bool set_ee(std::array<double,16> F_T_EE);

public:
    bool get_robot_state(franka::RobotState& state) const;
    bool get_gripper_state(franka::GripperState& state) const;
    const std::unique_ptr<franka::Model>& get_panda_model() const;

private:
    void load_gripper_configuration();
    std::optional<std::string> get_robot_ip(const std::optional<std::string>& last_ip);
    bool is_robot(const std::string& ip);
    std::optional<std::string> find_robot();
    std::optional<std::string> find_device(const std::string &network_interface);
    std::optional<std::string> ping_robot(const std::optional<std::string> &last_ip);
    void get_default_robot_state(franka::RobotState& state) const;
    void get_default_gripper_state(franka::GripperState& state) const;

private:
    std::unique_ptr<franka::Robot> m_panda_arm;
    std::unique_ptr<franka::Model> m_panda_model;
    std::unique_ptr<franka::Gripper> m_panda_hand;
    std::unique_ptr<Softhand2> m_softhand2;
    franka::RobotState m_robot_state;
    franka::GripperState m_gripper_state;

    bool m_has_arm;
    PandaHand m_hand;

    std::atomic<bool> m_arm_connected;
    std::atomic<bool> m_hand_connected;

    mutable std::mutex m_mtx_hand_active;

private:
    Memory* m_memory;
};

}
