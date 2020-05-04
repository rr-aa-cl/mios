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

#include "knowledge_base/knowledge_base.hpp"
#include "led_pattern/led_pattern.hpp"
#include "telemetry/telemetry_udp.hpp"
#include "interface/parameter_server.hpp"
#include "interface/sim_interface.hpp"

#include "utils/types.hpp"

#include "cntr_aic/cntr_aic_wrapper.hpp"
#include "cntr_force/cntr_force_wrapper.hpp"
#include "cntr_joint_var_imp/cntr_joint_var_imp_wrapper.hpp"
#include "cntr_mux/cntr_mux_wrapper.hpp"
#include "conv_vel2pose/conv_vel2pose_wrapper.hpp"
#include "virtual_cube/virtual_cube_wrapper.hpp"
#include "virtual_walls_joint/virtual_walls_joint_wrapper.hpp"
#include "cntr_nullsp_proj/cntr_nullsp_proj_wrapper.hpp"
#include "motion_error_cart/motion_error_cart_wrapper.hpp"

#include <msrm_utils/geometry.hpp>


namespace mios {

class Skill;
class CmdSkill;

class Core{
public:
    Core(int argc, char **argv);
    ~Core();

    bool initialize(bool silent=false);
    bool terminate();
    bool reset();
    bool write_config_to_robot();
//    void stop();
    bool recover();
    bool has_terminated() const;

    void login_digital_twin();
    void logout_digital_twin();

    void lockdown();
    void lift_lockdown();
    bool check_lockdown() const;

    bool lock_robot_connection(bool force_lock=true);
    void unlock_robot_connection();
    bool has_robot_connection() const;
    bool has_gripper_connection() const;

    bool wait_for_idle_state(double max_time);

    std::string get_last_error() const;

    std::shared_ptr<KnowledgeBase> get_kb();
    void set_live_parameter_server(std::shared_ptr<ParameterServer> server);

    std::string get_ip_primary();

    bool start_control_cycle();
    void terminate_control_cycle();

    MiosState* get_mios_state();

    bool load_skill(std::shared_ptr<Skill> skill, bool log=false);
    void unload_skill();
    void toggle_skill_pause(bool pause);

    // Gripper
    bool grasp_object(const std::string& o, double width=-1, double speed=1, double force=30, bool check_width=false);
    bool release_object(double width=-1,double speed=1);
    bool grasp(double width,double speed,double force);
    bool move_gripper(double width,double speed);
    bool is_grasping() const;
    bool home_gripper();
    bool set_grasped_object(const std::string& o);

    const Percept& request_percept(Eigen::Matrix<double, 3, 3> O_R_TF=Eigen::Matrix<double,3,3>::Zero(3,3), bool wait=false);

    // Sound output
    bool init_sound();
    bool terminate_sound();

    // LEDs
    bool init_led();
    bool terminate_led();
    void load_led_pattern(std::shared_ptr<LEDPattern> pattern);
    void unload_led_pattern();

    // Desk
    void start_desk_task(const std::string& task);
    void stop_desk_task();
    bool wait_for_desk_task();
    bool shutdown_robot();
    bool move_to_pack_pose();
    bool unlock_brakes();
    bool lock_brakes();

private:

    std::string get_ip_robot();
    bool listen_to_beacons();

    bool set_ee();

    // controller
    void initialize_control_aic(const Percept &p);
    void initialize_control_joint_imp(const Percept &p);
    void initialize_control_force(const Percept &p);
    void initialize_control_mux(const Percept &p);
    void initialize_virtual_cube(const Percept &p);
    void initialize_virtual_walls_joint(const Percept &p);
    void initialize_control_nullspace(const Percept &p);
    void initialize_motion_error(const Percept &p);
    void input_control_aic(const Percept &p);
    void input_control_joint_imp(const Percept &p);
    void input_control_force(const Percept &p);
    void input_control_mux(const Percept &p);
    void input_virtual_cube(const Percept &p);
    void input_virtual_walls_joint(const Percept &p);
    void input_control_nullspace(const Percept &p);
    void input_motion_error(const Percept &p);
    void terminate_control();

    void check_cartesian_velocity_workspace(Eigen::Matrix<double,6,1>& TF_dX_d, const Percept& p);
    void base_avoidance(Eigen::Matrix<double,6,1>& TF_dX_d, const Percept& p);

    void dummy_control(std::function<franka::Torques(const franka::RobotState& state)> control_cycle);
    void dummy_control(std::function<franka::CartesianVelocities(const franka::RobotState& state)> control_cycle);
    void dummy_control(std::function<franka::JointVelocities(const franka::RobotState& state)> control_cycle);

    void sim_control(std::function<franka::Torques(const franka::RobotState& state)> control_cycle);

    void gripper_cycle();
    void terminate_gripper();

    bool control_base_cycle(const franka::RobotState state, CmdSkill &cmd);
    franka::Torques control_cycle_torque_cart(const franka::RobotState state);
    franka::Torques control_cycle_torque_joint(const franka::RobotState state);
    franka::CartesianVelocities control_cycle_velocity_cart(const franka::RobotState state);
    franka::JointVelocities control_cycle_velocity_joint(const franka::RobotState state);
//    bool gripper_commands(CmdSkill& cmd);

    void cycle_led(std::function<LEDCmd(const Percept &)> callback_led);
    void cycle_led_wrapper(std::shared_ptr<LEDPattern> p);
    void cycle_sound(std::function<SoundCmd(const Percept &)> callback_sound);
//    void cycle_sound_wrapper(Skill *s);
    void terminate_periphery();

    void start_telemetry();
    void terminate_telemetry();

    bool start_sim_interface();
    bool terminate_sim_interface();

    void gripper_grasp(double width,double speed, double force,double epsilon_inner=0.005,double epsilon_outer=0.005);
    void gripper_move(double width,double speed);
    void gripper_stop();
    void gripper_homing();

    bool connect_to_robot();
    bool connect_to_gripper();
    bool disconnect_from_robot();
    bool disconnect_from_gripper();

    bool conncet_to_primary();

    void process_percept(const franka::RobotState& state, const franka::GripperState &state_gripper, Eigen::Matrix<double, 3, 3> O_R_TF=Eigen::Matrix<double,3,3>::Zero(3,3));
    void process_commands(const CmdSkill& cmd);
    bool validity_check_torque(std::array<double, 7>& tau_J);
    bool validity_check_virtual_cube();
    bool validity_check_virtual_walls_joint();
    bool validity_check_velocity_cart(std::array<double, 6>& O_dP_EE_d);
    bool validity_check_velocity_joint(std::array<double, 7>& dq_d);

    std::tuple<std::string,std::string,std::string> get_desk_data();

    // network
    std::string find_robot() const;
    bool test_robot_connection(const std::string& ip) const;
    std::string find_primary();
    bool test_primary_connection(const std::string& ip);

    std::unique_ptr<franka::Robot> _robot;
    std::unique_ptr<franka::Model> _model;
    std::unique_ptr<franka::Gripper> _gripper;

    std::thread _thr_gripper;
    std::thread _thr_led;
    std::thread _thr_telemetry;
    std::thread _thr_sound;

    franka::GripperState _gripper_state;
    std::atomic<bool> _flag_gripper;
    std::atomic<bool> _flag_gripper_active;
    std::mutex _mtx_gripper;

    Telemetry _telemetry;

    Telemetry_UDP _telemetry_udp;
    std::shared_ptr<SimInterface> _sim_interface;

    ConfigInternal _config_internal;

    Percept _percept;
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
    std::thread _thr_beacons;

    cntr_aic::cntr_aic _cntr_aic;
    cntr_force::cntr_force _cntr_force;
    cntr_joint_var_imp::cntr_joint_var_imp _cntr_joint_imp;
    cntr_mux::cntr_mux _cntr_mux;
    conv_vel2pose::conv_vel2pose _conv_vel2pose;
    virtual_cube::virtual_cube _virt_cube;
    virtual_walls_joint::virtual_walls_joint _virt_walls_joint;
    cntr_joint_var_imp::cntr_joint_var_imp _cntr_nullsp_q;
    cntr_nullsp_proj::cntr_nullsp_proj _cntr_nullsp_proj;
    motion_error_cart::motion_error_cart _motion_error_cart;

    cntr_aic::In_U_cntr_aic _in_u_aic;
    cntr_joint_var_imp::In_U_cntr_joint_var_imp _in_u_joint_imp;
    cntr_force::In_U_cntr_force _in_u_force;
    cntr_mux::In_U_cntr_mux _in_u_mux;
    conv_vel2pose::In_U_conv_vel2pose _in_u_vel2pose;
    virtual_cube::In_U_virtual_cube _in_u_virt_cube;
    virtual_walls_joint::In_U_virtual_walls_joint _in_u_virt_walls_joint;
    cntr_joint_var_imp::In_U_cntr_joint_var_imp _in_u_cntr_nullsp_q;
    cntr_nullsp_proj::In_U_cntr_nullsp_proj _in_u_cntr_nullsp_proj;
    motion_error_cart::In_U_motion_error_cart _in_u_motion_error_cart;

    cntr_aic::Out_Y_cntr_aic _out_y_aic;
    cntr_joint_var_imp::Out_Y_cntr_joint_var_imp _out_y_joint_imp;
    cntr_force::Out_Y_cntr_force _out_y_force;
    cntr_mux::Out_Y_cntr_mux _out_y_mux;
    conv_vel2pose::Out_Y_conv_vel2pose _out_y_vel2pose;
    virtual_cube::Out_Y_virtual_cube _out_y_virt_cube;
    virtual_walls_joint::Out_Y_virtual_walls_joint _out_y_virt_walls_joint;
    cntr_joint_var_imp::Out_Y_cntr_joint_var_imp _out_y_cntr_nullsp_q;
    cntr_nullsp_proj::Out_Y_cntr_nullsp_proj _out_y_cntr_nullsp_proj;
    motion_error_cart::Out_Y_motion_error_cart _out_y_motion_error_cart;

    std::shared_ptr<KnowledgeBase> _kb;
    std::shared_ptr<Skill> _active_skill;

    std::map<std::string,unsigned> _led_panel_id;
    nlohmann::json event;
    std::chrono::system_clock::time_point t_event;

};

}
