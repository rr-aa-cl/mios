#pragma once

#include <functional>

#include <franka/robot.h>
#include <franka/gripper.h>
#include <franka/model.h>
#include <franka/robot_state.h>
#include <franka/gripper_state.h>

namespace mios {

class PandaBody{
public:
    bool connect_to_robot(const std::string& ip);
    bool connect_to_gripper(const std::string &ip);
    void disconnect_from_robot();
    void disconnect_from_gripper();
    bool recover();

    bool pre_run_checks();

    bool start_desk_task(const std::string& task, const std::string &ip, const std::string user, const std::string &password);
    void stop_desk_task(const std::string &ip, const std::string user, const std::string &password);
    bool wait_for_desk_task();
    bool shutdown_robot(const std::string& ip, const std::string user, const std::string& password);
    bool move_to_pack_pose(const std::string& ip, const std::string user, const std::string& password);
    bool unlock_brakes(const std::string& ip, const std::string user, const std::string& password);
    bool lock_brakes(const std::string& ip, const std::string user, const std::string& password);


    bool grasp(double width,double speed,double force,double epsilon_inner,double epsilon_outer);
    bool move_to_finger_position(double width, double speed);
    bool home_gripper();

public:
    bool torque_control(std::function<franka::Torques(const franka::RobotState &)> controller_callback);
    bool cartesian_velocity_control(std::function<franka::Finishable*(const franka::RobotState&)> controller_callback);
    bool joint_velocity_control(std::function<franka::Finishable*(const franka::RobotState&)> controller_callback);
    bool cartesian_pose_control(std::function<franka::Finishable*(const franka::RobotState&)> controller_callback);
    bool joint_pose_control(std::function<franka::Finishable*(const franka::RobotState&)> controller_callback);

public:
    bool set_robot_parameters(double load_m,std::array<double,3> load_com,std::array<double,9> load_I,std::array<double,7> tau_ext_contact,std::array<double,7> tau_ext_max,
                              std::array<double,6> F_ext_K_contact,std::array<double,6> F_ext_K_max,std::array<double,16> EE_T_K,std::array<double,6> K_x,std::array<double,7> K_theta,
                              std::array<double,16> F_T_EE);

public:
    bool get_robot_state(franka::RobotState& state) const;
    bool get_gripper_state(franka::GripperState& state) const;
    const std::unique_ptr<franka::Model>& get_panda_model() const;
    std::optional<std::string> get_robot_ip(const std::optional<std::string> last_ip);
private:


    bool is_robot(const std::string& ip);
    std::optional<std::string> find_robot();
private:

    std::unique_ptr<franka::Robot> m_panda_arm;
    std::unique_ptr<franka::Model> m_panda_model;
    std::unique_ptr<franka::Gripper> m_panda_hand;

    std::atomic<bool> m_arm_connected;
    std::atomic<bool> m_hand_connected;
};

}
