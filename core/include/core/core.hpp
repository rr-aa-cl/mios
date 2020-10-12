#pragma once

#include <atomic>
#include <string>
#include <tuple>
#include <memory>
#include <chrono>
#include <unordered_set>
#include <set>

#include "memory/memory.hpp"
#include "panda/panda_body.hpp"
#include "controller_pipeline/controller_pipeline.hpp"
#include "safety_stage_1/safety_module_stage_1.hpp"
#include "safety_stage_2/safety_module_stage_2.hpp"
#include "skill/skill_engine.hpp"
#include "task/task_engine.hpp"
#include "portal/portal.hpp"
#include "skill/skill_library.hpp"
#include "interface/interface.hpp"
#include "interface/ros_node.hpp"
#include "learning_module/learning_module.hpp"

#include "data_structures/percept.hpp"
#include "data_structures/actuator.hpp"



namespace mios {

class Skill;

class Core{
public:
    Core(unsigned database_port);
    ~Core();

    bool initialize();
    void start();
    void terminate();

    ControlReturnType execute_skill();
    void terminate_control_cycle();

    bool refresh_percept(std::optional<Eigen::Matrix<double, 3, 3> > O_R_TF);

    // Gripper
    bool grasp_object(const std::string& name, double speed=1);
    bool release_object(double speed=1);
    bool grasp(double width, double speed, double force, double epsilon_inner, double epsilon_outer);
    bool move_gripper(double width,double speed);
    bool is_grasping();
    bool home_gripper();
    bool set_grasped_object(const std::string& name);

    bool lock_body();
    bool unlock_body();
    bool shutdown_body();
    bool pack_body();

    bool start_desk_task(const std::string& task);
    bool stop_desk_task();

    bool recover_body();

public:
    Memory* get_memory();
    SkillEngine* get_skill_engine();
    Portal* get_portal();
    TaskEngine* get_task_engine();
    CommandInterface* get_command_interface();
    RosNode* get_ros_node();
    LearningModule* get_learning_module();
    const Percept *get_percept() const;
    bool is_ready() const;

private:
    franka::Finishable *control_base_cycle(const franka::RobotState& state);
    franka::Torques cart_torque_controller_pipeline(const franka::RobotState& state);
    franka::Torques joint_torque_controller_pipeline(const franka::RobotState& state);
    franka::CartesianVelocities cart_velocity_controller_pipeline(const franka::RobotState& state);
    franka::JointVelocities joint_velocity_controller_pipeline(const franka::RobotState& state);

private:
    Percept m_percept;

    Memory m_memory;
    SkillEngine m_skill_engine;
    PandaBody m_panda_body;
    Portal m_portal;
    SkillLibrary m_skill_library;
    TaskEngine m_task_engine;
    CommandInterface m_command_interface;
    RosNode m_ros_node;
    LearningModule m_learning_module;
    std::unique_ptr<ControllerPipeline> m_controller_pipeline;
    std::set<std::unique_ptr<SafetyModuleStage1> > m_safety_stage_1;
    std::set<std::unique_ptr<SafetyModuleStage2> > m_safety_stage_2;

private:
    bool m_is_ready;
};

}
