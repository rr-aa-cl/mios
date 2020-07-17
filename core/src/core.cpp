#include "core/core.hpp"

#include <msrm_utils/math.hpp>
#include <msrm_utils/conversion.hpp>
#include <msrm_utils/json.hpp>
#include <msrm_utils/system.hpp>
#include "utils/exceptions.hpp"
#include "skill/skill.hpp"
#include "skills/nullskill.hpp"

#include "controller_pipeline/cart_torque_pipeline.hpp"
#include "controller_pipeline/joint_torque_pipeline.hpp"
#include "controller_pipeline/cart_velocity_pipeline.hpp"
#include "controller_pipeline/joint_velocity_pipeline.hpp"
#include "controller_pipeline/null_pipeline.hpp"

#include "safety_stage_1/velocity_walls.hpp"
#include "safety_stage_2/virtual_cube.hpp"
#include "safety_stage_2/virtual_joint_walls.hpp"

#include <iostream>
#include <chrono>
#include <thread>

#include <functional>

#include <spdlog/spdlog.h>

namespace mios {

Core::Core():m_skill_engine(SkillEngine(this)),m_portal(Portal("0.0.0.0",12000,"mios/core","0.0.0.0",12001,12002)),m_task_engine(TaskEngine(this)),
    m_command_interface(CommandInterface(this,&m_task_engine,&m_portal,&m_memory)),m_ros_node(this,&m_task_engine,&m_portal,&m_memory),
    m_controller_pipeline(std::make_unique<NullControllerPipeline>()),m_is_ready(false){
}

Core::~Core(){
    terminate();
}

bool Core::initialize(){
    spdlog::info("Initializing MIOS core...");
    if(!m_memory.initialize()){
        spdlog::error("Could not initialize memory.");
        return false;
    }
    spdlog::debug("Core: initialize.m_memory.set_default_parameters");
    if(!m_memory.set_default_parameters()){
        return false;
    }
    spdlog::debug("Core: initialize.check_if_robot");
    m_panda_body.set_arm(m_memory.read_parameters()->system.has_robot);
    m_panda_body.set_hand(m_memory.read_parameters()->system.gripper);
    m_memory.get_parameters()->system.robot_ip = m_panda_body.get_robot_ip(m_memory.read_parameters()->system.robot_ip).value_or("127.0.0.1");
    if(!m_memory.update_database()){
        spdlog::warn("Could not update database.");
    }
    spdlog::debug("Core: initialize.check_if_robot2");
    spdlog::debug("Core: initialize.connect_to_robot");
    if(!m_panda_body.connect_to_robot(m_memory.read_parameters()->system.robot_ip)){
        return false;
    }
    spdlog::debug("Core: initialize.check_if_gripper");
    spdlog::debug("Core: initialize.connect_to_gripper");
    if(!m_panda_body.connect_to_gripper(m_memory.read_parameters()->system.robot_ip)){
        return false;
    }
    m_panda_body.get_gripper_configuration(m_memory.get_parameters()->frames.F_T_EE);
    if(!m_memory.update_database()){
        return false;
    }
    if(!set_robot_parameters()){
        return false;
    }
    spdlog::debug("Core: initialize.set_time");
    m_is_ready=true;

    if(!refresh_percept({})){
        spdlog::error("Could not acquire iniital percept.");
        return false;
    }
    m_ros_node.start();

    return true;
}

void Core::terminate(){
    m_panda_body.disconnect_from_robot();
    m_panda_body.disconnect_from_gripper();
}

Memory* Core::get_memory(){
    return &m_memory;
}

SkillEngine* Core::get_skill_engine(){
    return &m_skill_engine;
}

Portal* Core::get_portal(){
    return &m_portal;
}

TaskEngine* Core::get_task_engine(){
    return &m_task_engine;
}

CommandInterface* Core::get_command_interface(){
    return &m_command_interface;
}

RosNode* Core::get_ros_node(){
    return &m_ros_node;
}

bool Core::execute_skill(){
    spdlog::debug("CORE: execute_skill");

    if(!m_panda_body.pre_run_checks()){
        if(!m_panda_body.recover()){
            return false;
        }
    }

    spdlog::debug("CORE: start_control_cycle: while-loop");
    refresh_percept(m_memory.read_parameters()->frames.O_R_T);
    m_percept.update_controller();
    set_robot_parameters();

    bool result=false;
    spdlog::debug("CORE: EXECUTE_SKILL.control_mode: ");
    if(m_memory.read_parameters()->control.control_mode==ControlMode::mCartTorque){
        m_controller_pipeline=std::make_unique<CartTorqueControllerPipeline>();
        m_safety_stage_1.insert(std::make_unique<VelocityWallsSafetyModule>());
        m_safety_stage_2.insert(std::make_unique<VirtualCubeSafetyModule>());
        m_safety_stage_2.insert(std::make_unique<VirtualJointWallsSafetyModule>());
        m_controller_pipeline->initialize(m_percept,&m_memory);
        for(auto& m : m_safety_stage_1){
            m->initialize(m_percept,&m_memory);
        }
        for(auto& m : m_safety_stage_2){
            m->initialize(m_percept,&m_memory);
        }
        result=m_panda_body.control(std::bind(&Core::cart_torque_controller_pipeline,this,std::placeholders::_1));
    }
    if(m_memory.read_parameters()->control.control_mode==ControlMode::mJointTorque){
        m_controller_pipeline=std::make_unique<JointTorqueControllerPipeline>();
        m_safety_stage_1.insert(std::make_unique<VelocityWallsSafetyModule>());
        m_safety_stage_2.insert(std::make_unique<VirtualCubeSafetyModule>());
        m_safety_stage_2.insert(std::make_unique<VirtualJointWallsSafetyModule>());
        m_controller_pipeline->initialize(m_percept,&m_memory);
        for(auto& m : m_safety_stage_1){
            m->initialize(m_percept,&m_memory);
        }
        for(auto& m : m_safety_stage_2){
            m->initialize(m_percept,&m_memory);
        }
        result=m_panda_body.control(std::bind(&Core::joint_torque_controller_pipeline,this,std::placeholders::_1));
    }
    if(m_memory.read_parameters()->control.control_mode==ControlMode::mCartVelocity){
        m_controller_pipeline=std::make_unique<CartVelocityControllerPipeline>();
        m_controller_pipeline->initialize(m_percept,&m_memory);
        result=m_panda_body.control(std::bind(&Core::cart_velocity_controller_pipeline,this,std::placeholders::_1));
    }
    if(m_memory.read_parameters()->control.control_mode==ControlMode::mJointVelocity){
        m_controller_pipeline=std::make_unique<JointVelocityControllerPipeline>();
        m_controller_pipeline->initialize(m_percept,&m_memory);
        result=m_panda_body.control(std::bind(&Core::joint_velocity_controller_pipeline,this,std::placeholders::_1));
    }
    if(m_memory.read_parameters()->control.control_mode==ControlMode::mNoControl){
        spdlog::error("No control mode has been selected.");
    }

    m_controller_pipeline->terminate();
    m_controller_pipeline=std::make_unique<NullControllerPipeline>();
    for(auto& m : m_safety_stage_1){
        m->terminate();
    }
    for(auto& m : m_safety_stage_2){
        m->terminate();
    }
    m_safety_stage_1.clear();
    m_safety_stage_2.clear();
    return result;
}

bool Core::set_robot_parameters(){
    ControlParameters control= m_memory.read_parameters()->control;
    UserParameters user= m_memory.read_parameters()->user;
    FramesParameters frames =m_memory.read_parameters()->frames;

    std::array<double,3> load_com = msrm_utils::convert_to_array<double,3,1>(user.load_com);
    std::array<double,9> load_I = msrm_utils::convert_to_array<double,3,3>(user.load_I);
    std::array<double,7> tau_contact = msrm_utils::convert_to_array<double,7,1>(user.tau_ext_contact);
    std::array<double,7> tau_max = msrm_utils::convert_to_array<double,7,1>(user.tau_ext_max);
    std::array<double,6> F_contact = {user.F_ext_contact(0),user.F_ext_contact(0),user.F_ext_contact(0),user.F_ext_contact(1),user.F_ext_contact(1),user.F_ext_contact(1)};
    std::array<double,6> F_max = {user.F_ext_max(0),user.F_ext_max(0),user.F_ext_max(0),user.F_ext_max(1),user.F_ext_max(1),user.F_ext_max(1)};
    std::array<double,16> EE_T_K = msrm_utils::convert_to_array<double,4,4>(frames.EE_T_K);
    std::array<double,7> K_theta = msrm_utils::convert_to_array<double,7,1>(control.joint_imp.K_theta);
    std::array<double,6> K_x = msrm_utils::convert_to_array<double,6,1>(control.cart_imp.K_x);
    std::array<double,16> F_T_EE = msrm_utils::convert_to_array<double,4,4>(frames.F_T_EE);

    return m_panda_body.set_robot_parameters(user.load_m,load_com,load_I,tau_contact,tau_max,F_contact,F_max,EE_T_K,K_x,K_theta,F_T_EE);
}

franka::Finishable* Core::control_base_cycle(const franka::RobotState& state){

    franka::GripperState gripper_state;
    m_percept.update(m_panda_body.get_panda_model(),state,gripper_state,m_memory.read_parameters()->frames.O_R_T);
    m_memory.internal_update(m_percept);
    Actuator* cmd=m_skill_engine.get_next_command(m_percept);
    m_memory.get_parameters()->frames.O_R_T=cmd->O_R_T;
    for(auto& m : m_safety_stage_1){
        m->step(m_percept,*cmd);
    }
    cmd->limit_output_rate(m_memory.read_parameters()->limits);
    cmd->limit_output(m_memory.read_parameters()->limits);
    if(cmd->is_new()){
        m_controller_pipeline->context_switch(m_percept);
    }
    franka::Finishable* panda_cmd=m_controller_pipeline->step(m_percept,*cmd);
    if(!m_controller_pipeline->is_valid_command(panda_cmd)){
        cmd->stop();
    }
    m_percept.update_controller();
    m_controller_pipeline->update_percept(m_percept.controller);
    for(auto& m : m_safety_stage_2){
        m->step(m_percept,panda_cmd);
    }
    if(cmd->is_stopped()){
        panda_cmd->motion_finished=true;
    }
    return panda_cmd;
}

franka::Torques Core::cart_torque_controller_pipeline(const franka::RobotState& state){
    return *static_cast<franka::Torques*>(control_base_cycle(state));
}

franka::Torques Core::joint_torque_controller_pipeline(const franka::RobotState& state){
    return *static_cast<franka::Torques*>(control_base_cycle(state));
}

franka::CartesianVelocities Core::cart_velocity_controller_pipeline(const franka::RobotState& state){
    return *static_cast<franka::CartesianVelocities*>(control_base_cycle(state));
}

franka::JointVelocities Core::joint_velocity_controller_pipeline(const franka::RobotState& state){
    return *static_cast<franka::JointVelocities*>(control_base_cycle(state));
}

bool Core::grasp_object(const std::string &name,double speed){
    const Object* object=m_memory.get_object(name);
    if(object->name=="NullObject"){
        spdlog::error("Cannot find object "+name+" in knowledge base.");
        return false;
    }
    if(m_panda_body.grasp(object->grasp_width,speed,object->grasp_force,0.005,0.005)){
        m_memory.get_live_context()->grasped_object=object;
        m_memory.get_parameters()->user.load_m=object->mass;
        m_memory.get_parameters()->user.load_com=(m_memory.read_parameters()->frames.F_T_EE*msrm_utils::invert_transformation_matrix(object->OB_T_gp)).block<3,1>(0,3);
        m_memory.get_parameters()->user.load_I=object->OB_I;
        m_memory.get_parameters()->frames.EE_T_TCP=msrm_utils::invert_transformation_matrix(object->OB_T_gp)*object->OB_T_TCP;
        if(!set_robot_parameters()){
            return false;
        }
        return true;
    }else{
        return false;
    }
}

bool Core::home_gripper() const{
    return m_panda_body.home_gripper();
}

bool Core::grasp(double width, double speed, double force,double epsilon_inner,double epsilon_outer) const{
    return m_panda_body.grasp(width,speed,force,epsilon_inner,epsilon_outer);
}

bool Core::move_gripper(double width, double speed) const{
    return m_panda_body.move_to_finger_position(width,speed);
}

bool Core::is_grasping(){
    refresh_percept({});
    return m_percept.proprioception.is_grasping;
}

bool Core::set_grasped_object(const std::string &name){
    const Object* object=m_memory.get_object(name);
    if(object->name=="NullObject"){
        spdlog::error("Cannot find object "+name+" in knowledge base.");
        return false;
    }
    m_memory.get_live_context()->grasped_object=object;
    m_memory.get_parameters()->user.load_m=object->mass;
    m_memory.get_parameters()->user.load_com=(m_memory.read_parameters()->frames.F_T_EE*msrm_utils::invert_transformation_matrix(object->OB_T_gp)).block<3,1>(0,3);
    m_memory.get_parameters()->user.load_I=object->OB_I;
    m_memory.get_parameters()->frames.EE_T_TCP=msrm_utils::invert_transformation_matrix(object->OB_T_gp)*object->OB_T_TCP;
    return set_robot_parameters();
}

bool Core::release_object(double speed){
    const Object* object=m_memory.get_live_context()->grasped_object;
    if(object->name=="NullObject"){
        spdlog::error("I am not grasping anything.");
        return false;
    }
    object=m_memory.get_object("NullObject");
    if(m_panda_body.move_to_finger_position(m_percept.internal_model.max_finger_width,speed)){
        m_memory.get_live_context()->grasped_object=object;
        m_memory.get_parameters()->user.load_m=object->mass;
        m_memory.get_parameters()->user.load_com=(m_memory.read_parameters()->frames.F_T_EE*msrm_utils::invert_transformation_matrix(object->OB_T_gp)).block<3,1>(0,3);
        m_memory.get_parameters()->user.load_I=object->OB_I;
        m_memory.get_parameters()->frames.EE_T_TCP=msrm_utils::invert_transformation_matrix(object->OB_T_gp)*object->OB_T_TCP;
        set_robot_parameters();
        return true;
    }else{
        return false;
    }
}

bool Core::refresh_percept(std::optional<Eigen::Matrix<double,3,3> > O_R_TF){
    franka::RobotState robot_state;
    franka::GripperState gripper_state;
    if(!m_panda_body.get_robot_state(robot_state)){
        return false;
    }
    if(!m_panda_body.get_gripper_state(gripper_state)){
        return false;
    }
    m_percept.update(m_panda_body.get_panda_model(),robot_state,gripper_state,O_R_TF);
    m_controller_pipeline->update_percept(m_percept.controller);
    m_memory.internal_update(m_percept);
    return true;
}

bool Core::unlock_body(){
    return m_panda_body.unlock_brakes(m_memory.read_parameters()->system.robot_ip,m_memory.read_parameters()->system.desk_user,m_memory.read_parameters()->system.desk_pwd);
}

bool Core::lock_body(){
    return m_panda_body.lock_brakes(m_memory.read_parameters()->system.robot_ip,m_memory.read_parameters()->system.desk_user,m_memory.read_parameters()->system.desk_pwd);
}

bool Core::shutdown_body(){
    return m_panda_body.shutdown_robot(m_memory.read_parameters()->system.robot_ip,m_memory.read_parameters()->system.desk_user,m_memory.read_parameters()->system.desk_pwd);
}

bool Core::pack_body(){
    return m_panda_body.move_to_pack_pose(m_memory.read_parameters()->system.robot_ip,m_memory.read_parameters()->system.desk_user,m_memory.read_parameters()->system.desk_pwd);
}

bool Core::start_desk_task(const std::string &task){
    return m_panda_body.start_desk_task(task,m_memory.read_parameters()->system.robot_ip,m_memory.read_parameters()->system.desk_user,m_memory.read_parameters()->system.desk_pwd);
}

bool Core::stop_desk_task(){
    return m_panda_body.stop_desk_task(m_memory.read_parameters()->system.robot_ip,m_memory.read_parameters()->system.desk_user,m_memory.read_parameters()->system.desk_pwd);
}

bool Core::recover_body(){
    return m_panda_body.recover();
}

const Percept* Core::get_percept() const{
    return &m_percept;
}

bool Core::is_ready() const{
    return m_is_ready;
}

}

