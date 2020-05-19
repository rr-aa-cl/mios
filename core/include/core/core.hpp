#pragma once

#include <atomic>
#include <string.h>
#include <tuple>
#include <memory>
#include <chrono>

#include <franka/robot.h>
#include <franka/gripper.h>
#include <franka/model.h>
#include <franka/exception.h>

#include "memory/memory.hpp"
#include "led_pattern/led_pattern.hpp"
#include "telemetry/telemetry_udp.hpp"
#include "interface/parameter_server.hpp"
#include "panda/panda_body.hpp"

#include "utils/types.hpp"
#include "data_structures/percept.hpp"
#include "data_structures/actuator.hpp"

#include <msrm_utils/geometry.hpp>
#include "controller_pipeline/torque_pipeline.hpp"


namespace mios {

enum ControlMode{mCartTorque,mJointTorque,mCartVelocity,mJointVelocity};

class Skill;

class Core{
public:
    Core(int argc, char **argv);
    ~Core();

    bool initialize();
    void terminate();

    bool reset();
    bool has_terminated() const;

    std::string get_last_error() const;

    Memory* get_memory();
    void set_live_parameter_server(ParameterServer *server);

    bool execute_skill();
    void terminate_control_cycle();

    bool load_skill(std::shared_ptr<Skill> skill);
    void unload_skill();

    // Gripper
//    bool grasp_object(const std::string& o, double width=-1, double speed=1, double force=30, bool check_width=false);
//    bool release_object(double width=-1,double speed=1);
//    bool grasp(double width,double speed,double force);
//    bool move_gripper(double width,double speed);
//    bool is_grasping() const;
//    bool home_gripper();
//    bool set_grasped_object(const std::string& o);

    bool refresh_percept(std::optional<Eigen::Matrix<double, 3, 3> > O_R_TF);
    const Percept& get_percept() const;

private:

    bool set_ee();

    void check_cartesian_velocity_workspace(Eigen::Matrix<double,6,1>& TF_dX_d, const Percept& p);
    void base_avoidance(Eigen::Matrix<double,6,1>& TF_dX_d, const Percept& p);

    void dummy_control(std::function<franka::Torques(const franka::RobotState& state)> control_cycle);
    void dummy_control(std::function<franka::CartesianVelocities(const franka::RobotState& state)> control_cycle);
    void dummy_control(std::function<franka::JointVelocities(const franka::RobotState& state)> control_cycle);

    franka::Finishable *control_base_cycle(const franka::RobotState& state);
    franka::Torques cart_torque_controller_pipeline(const franka::RobotState& state);

    void terminate_periphery();

    void start_telemetry();
    void terminate_telemetry();

    bool validity_check_torque(std::array<double, 7>& tau_J);
    bool validity_check_velocity_cart(std::array<double, 6>& O_dP_EE_d);
    bool validity_check_velocity_joint(std::array<double, 7>& dq_d);

    std::tuple<std::string,std::string,std::string> get_desk_data();

    ConfigInternal _config_internal;

    Percept m_percept;
    std::array<double,7> _tau_J_old;
    std::array<double,7> _tau_J_last;
//    CmdSkill _skill_last;

    bool _flag_stop_control;
    bool _flag_invalid_mode;
    bool _flag_robot_connected;
    bool _flag_gripper_connected;
    bool _flag_gripper_busy;
    bool _flag_virt_cube_valid;
    bool _flag_virt_walls_joint_valid;
    bool _flag_lockdown;
    bool _flag_logged_in_digital_twin;

    std::atomic<bool> _flag_run_gripper;
    std::atomic<bool> _flag_run_led;
    std::atomic<bool> _flag_run_sound;
    std::atomic<bool> _flag_run_beacon;

    std::string _last_error;

    std::mutex _mtx_control_cycle;
    std::mutex m_mtx_robot;
    std::thread _thr_beacons;

    Memory m_memory;
    std::shared_ptr<Skill> m_active_skill;

    std::map<std::string,unsigned> _led_panel_id;
    nlohmann::json event;
    std::chrono::system_clock::time_point t_event;

    PandaBody m_panda_body;

    std::unique_ptr<ControllerPipeline> m_controller_pipeline;

};

}
