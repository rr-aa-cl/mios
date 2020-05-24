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
#include "interface/parameter_server.hpp"
#include "panda/panda_body.hpp"
#include "controller_pipeline/controller_pipeline.hpp"
#include "skill/skill_engine.hpp"
#include "task/task_engine.hpp"
#include "portal/portal.hpp"
#include "interface/interface.hpp"

#include "utils/types.hpp"
#include "data_structures/percept.hpp"
#include "data_structures/actuator.hpp"

#include <msrm_utils/geometry.hpp>


namespace mios {

class Skill;

class Core{
public:
    Core();
    ~Core();

    bool initialize();
    void terminate();

    bool execute_skill();
    void terminate_control_cycle();

    bool refresh_percept(std::optional<Eigen::Matrix<double, 3, 3> > O_R_TF);

    // Gripper
    bool grasp_object(const std::string& name, double speed=1);
    bool release_object(double speed=1);
    bool grasp(double width, double speed, double force, double epsilon_inner, double epsilon_outer) const;
    bool move_gripper(double width,double speed) const;
    bool is_grasping();
    bool home_gripper() const;
    bool set_grasped_object(const std::string& name);


    bool lock_body();
    bool unlock_body();
    bool shutdown_body();
    bool pack_body();

    bool recover_body();

public:
    Memory* get_memory();
    SkillEngine* get_skill_engine();
    Portal* get_portal();
    TaskEngine* get_task_engine();
    CommandInterface* get_command_interface();
    const Percept *get_percept() const;

private:

    bool set_robot_parameters();

    void check_cartesian_velocity_workspace(Eigen::Matrix<double,6,1>& TF_dX_d, const Percept& p);
    void base_avoidance(Eigen::Matrix<double,6,1>& TF_dX_d, const Percept& p);

    franka::Finishable *control_base_cycle(const franka::RobotState& state);
    franka::Torques cart_torque_controller_pipeline(const franka::RobotState& state);
    franka::Torques joint_torque_controller_pipeline(const franka::RobotState& state);
    franka::CartesianVelocities cart_velocity_controller_pipeline(const franka::RobotState& state);
    franka::JointVelocities joint_velocity_controller_pipeline(const franka::RobotState& state);

    std::tuple<std::string,std::string,std::string> get_desk_data() const;

private:
    Percept m_percept;

    Memory m_memory;
    SkillEngine m_skill_engine;
    PandaBody m_panda_body;
    Portal m_portal;
    TaskEngine m_task_engine;
    CommandInterface m_command_interface;
    std::unique_ptr<ControllerPipeline> m_controller_pipeline;
};

}
