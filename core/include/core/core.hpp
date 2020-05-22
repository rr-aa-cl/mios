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
#include "controller_pipeline/controller_pipeline.hpp"


namespace mios {

class Skill;

class Core{
public:
    Core(int argc, char **argv);
    ~Core();

    bool initialize();
    void terminate();

    bool reset();
    bool has_terminated() const;

    bool execute_skill();
    void terminate_control_cycle();

    bool load_skill(std::shared_ptr<Skill> skill);
    void unload_skill();

    // Gripper
    bool grasp_object(const std::string& name, double speed=1);
    bool release_object(double width=-1,double speed=1);
    bool grasp(double width, double speed, double force, double epsilon_inner, double epsilon_outer);
    bool move_gripper(double width,double speed);
    bool is_grasping() const;
    bool home_gripper();
    bool set_grasped_object(const std::string& name);

    bool refresh_percept(std::optional<Eigen::Matrix<double, 3, 3> > O_R_TF);

public:
    Memory* get_memory();
    const Percept * const get_percept() const;

private:

    bool set_robot_parameters();

    void check_cartesian_velocity_workspace(Eigen::Matrix<double,6,1>& TF_dX_d, const Percept& p);
    void base_avoidance(Eigen::Matrix<double,6,1>& TF_dX_d, const Percept& p);

    franka::Finishable *control_base_cycle(const franka::RobotState& state);
    franka::Torques cart_torque_controller_pipeline(const franka::RobotState& state);
    franka::Torques joint_torque_controller_pipeline(const franka::RobotState& state);
    franka::CartesianVelocities cart_velocity_controller_pipeline(const franka::RobotState& state);
    franka::JointPositions joint_velocity_controller_pipeline(const franka::RobotState& state);

    std::tuple<std::string,std::string,std::string> get_desk_data() const;

private:
    Percept m_percept;
    Memory m_memory;
    std::shared_ptr<Skill> m_active_skill;
    PandaBody m_panda_body;
    std::unique_ptr<ControllerPipeline> m_controller_pipeline;
};

}
