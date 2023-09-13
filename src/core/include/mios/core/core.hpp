#pragma once

#include <string>
#include <set>
#include <mutex>

#include "mios/controller_pipeline/controller_pipeline.hpp"
#include "mios/interface/interface.hpp"
//#include "mios/interface/ros_node.hpp"
#include "mios/learning_module/learning_module.hpp"
#include "mios/memory/memory.hpp"
#include "mios/panda/panda_body.hpp"
#include "mios/portal/portal.hpp"
#include "mios/safety_stage_1/safety_module_stage_1.hpp"
#include "mios/safety_stage_2/safety_module_stage_2.hpp"
#include "mios/skill/skill_engine.hpp"
#include "mios/skill/skill_library.hpp"
#include "mios/task/task_engine.hpp"
#include "mios/telemetry/telemetry_udp.hpp"

#include "mios/data_structures/actuator.hpp"
#include "mios/data_structures/percept.hpp"



namespace mios {

class Skill;

class Core{
public:
    Core(unsigned database_port, unsigned robot_configuration, std::string robot_arm);
    ~Core();

    bool initialize();
    void start();
    void terminate();

    ControlReturnType execute_skill();
    void post_execution();
    void terminate_control_cycle();

    bool refresh_percept(std::optional<Eigen::Matrix<double, 3, 3> > O_R_TF, bool wait=true);
    bool try_refresh_percept(std::optional<Eigen::Matrix<double, 3, 3> > O_R_TF, bool wait=true);

    // Gripper
    bool grasp_object(const std::string& name, double speed=1);
    bool release_object(std::optional<double> width, double speed=1);
    bool grasp(double width, double speed, double force, double epsilon_inner, double epsilon_outer, std::string object_name="NullObject");
    bool move_gripper(double width,double speed);
    bool is_grasping();
    bool home_gripper();
    bool set_grasped_object(const std::string& name);

    bool lock_body();
    bool unlock_body();
    bool shutdown_body();
    bool reboot_body();
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
    //RosNode* get_ros_node();
    LearningModule* get_learning_module();
    TelemetryUDP* get_telemetry();
    const Percept *get_percept() const;
    bool is_ready() const;
    bool is_busy();

private:
    franka::Finishable *control_base_cycle(const franka::RobotState& state);
    franka::Torques cart_torque_controller_pipeline(const franka::RobotState& state);
    franka::Torques joint_torque_controller_pipeline(const franka::RobotState& state);
    franka::CartesianVelocities cart_velocity_controller_pipeline(const franka::RobotState& state);
    franka::JointVelocities joint_velocity_controller_pipeline(const franka::RobotState& state);

    void handle_gripper(Actuator* cmd);

private:
    Percept m_percept;

    Memory m_memory;
    SkillEngine m_skill_engine;
    PandaBody m_panda_body;
    Portal m_portal;
    SkillLibrary m_skill_library;
    TaskEngine m_task_engine;
    CommandInterface m_command_interface;
    //RosNode m_ros_node;
    LearningModule m_learning_module;
    TelemetryUDP m_telemetry;
    std::unique_ptr<ControllerPipeline> m_controller_pipeline;
    std::set<std::unique_ptr<SafetyModuleStage1> > m_safety_stage_1;
    std::set<std::unique_ptr<SafetyModuleStage2> > m_safety_stage_2;

private:
    bool m_is_ready;
    unsigned m_robot_configuration;
    bool m_blend_skill;
    std::string m_robot_arm;
    std::mutex m_mtx_is_busy;
    std::mutex m_mtx_FCI;

private:
    unsigned m_hand_grace_period;
};

}
