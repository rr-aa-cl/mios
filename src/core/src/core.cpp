#include "mios/core/core.hpp"

#include "mirmi_cpp_utils/math/math.hpp"
#include "mirmi_cpp_utils/conversion/conversion.hpp"
#include "mirmi_cpp_utils/json/json.hpp"
#include "mirmi_cpp_utils/system/system.hpp"
#include "mios/utils/exceptions.hpp"
#include "mios/skill/skill.hpp"

#include "mios/controller_pipeline/cart_torque_pipeline.hpp"
#include "mios/controller_pipeline/joint_torque_pipeline.hpp"
#include "mios/controller_pipeline/cart_velocity_pipeline.hpp"
#include "mios/controller_pipeline/joint_velocity_pipeline.hpp"
#include "mios/controller_pipeline/null_pipeline.hpp"

#include "mios/safety_stage_1/velocity_walls.hpp"
#include "mios/safety_stage_2/virtual_cube.hpp"
#include "mios/safety_stage_2/virtual_joint_walls.hpp"
#include "mios/safety_stage_2/cartesian_velocity_damping.hpp"

#include <functional>

#include "spdlog/spdlog.h"

#include <thread>

namespace mios {

Core::Core(unsigned database_port, unsigned robot_configuration, std::string robot_arm):m_memory(database_port, robot_arm),m_skill_engine(SkillEngine(this)),m_panda_body(PandaBody(&m_memory)),
    m_portal(Portal("0.0.0.0",(robot_arm == "left") ? 12000 : 13000,"mios/core","0.0.0.0",(robot_arm == "left") ? 12001 : 13001,(robot_arm == "left") ? 12002 : 13002)),m_task_engine(TaskEngine(this)),
    m_command_interface(CommandInterface(this,&m_task_engine,&m_portal,&m_memory)),//m_ros_node(this,&m_task_engine,&m_portal,&m_memory),
    m_telemetry(TelemetryUDP(this,&m_portal)),m_controller_pipeline(std::make_unique<NullControllerPipeline>()),m_is_ready(false),
    m_robot_configuration(robot_configuration),m_robot_arm(robot_arm) ,m_blend_skill(false),m_hand_grace_period(0){
    spdlog::trace("Core::Core()");
}

Core::~Core(){
    spdlog::trace("Core::~Core()");
    terminate();
}

bool Core::initialize(){
    spdlog::trace("Core::initialize()");
    spdlog::info("Initializing memory...");
    if(!m_memory.initialize(&m_skill_library,m_robot_configuration)){
        spdlog::error("Could not initialize memory.");
        return false;
    }
    spdlog::info("Initializing robot...");
    if(!m_panda_body.initialize()){
        spdlog::error("Could not initialize robot.");
        return false;
    }
    spdlog::info("Updating database...");
    if(!m_memory.update_database()){
        spdlog::error("Could not update datebase.");
        return false;
    }

    spdlog::info("Acquiring initial percept...");
    if(!refresh_percept({})){
        spdlog::error("Could not acquire iniital percept.");
        return false;
    }
    spdlog::info("Initializing interfaces...");
    if(!m_portal.initialize()){
        spdlog::error("Could not initialize portal.");
        return false;
    }
    //m_ros_node.start();

    m_is_ready=true;
    return true;
}

void Core::start(){
    spdlog::trace("Core::start()");
    spdlog::info("Starting task engine...");
    m_task_engine.life_cycle();
}

void Core::terminate(){
    spdlog::trace("Core::terminate()");
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
/*
RosNode* Core::get_ros_node(){
    return &m_ros_node;
}
*/
LearningModule* Core::get_learning_module(){
    return &m_learning_module;
}

TelemetryUDP* Core::get_telemetry(){
    return &m_telemetry;
}

ControlReturnType Core::execute_skill(){
    spdlog::trace("Core:execute_skill()");

    if(!m_panda_body.pre_run_checks()){
        if(ControlReturnType result=m_panda_body.recover();result.exception){
            return result;
        }
    }
    ControlReturnType result(false,"None","");

    refresh_percept(m_memory.read_parameters()->frames.O_R_T);
    std::scoped_lock<std::mutex> busy_lock(m_mtx_is_busy);
    m_percept.update_controller();
    m_panda_body.set_robot_parameters();

    spdlog::trace("CORE:execute_skill.start_control_cycle");
    if(m_memory.read_parameters()->control.control_mode==ControlMode::mCartTorque){
        m_controller_pipeline=std::make_unique<CartTorqueControllerPipeline>();
        m_safety_stage_1.insert(std::make_unique<VelocityWallsSafetyModule>());
        m_safety_stage_2.insert(std::make_unique<VirtualCubeSafetyModule>());
        m_safety_stage_2.insert(std::make_unique<VirtualJointWallsSafetyModule>());
        m_safety_stage_2.insert(std::make_unique<CartesianVelocityDampingSafetyModule>());
        m_controller_pipeline->initialize(m_percept,&m_memory);
        m_controller_pipeline->update_percept(m_percept.controller);
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
        m_controller_pipeline->update_percept(m_percept.controller);
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
        m_controller_pipeline->update_percept(m_percept.controller);
        result=m_panda_body.control(std::bind(&Core::cart_velocity_controller_pipeline,this,std::placeholders::_1));
    }
    if(m_memory.read_parameters()->control.control_mode==ControlMode::mJointVelocity){
        m_controller_pipeline=std::make_unique<JointVelocityControllerPipeline>();
        m_controller_pipeline->initialize(m_percept,&m_memory);
        m_controller_pipeline->update_percept(m_percept.controller);
        result=m_panda_body.control(std::bind(&Core::joint_velocity_controller_pipeline,this,std::placeholders::_1));
    }
    if(m_memory.read_parameters()->control.control_mode==ControlMode::mNoControl){
        spdlog::error("No control mode has been selected.");
    }

    m_blend_skill=false;
    //    m_panda_body.stop_gripper();
    return result;
}

void Core::post_execution(){
    spdlog::trace("Core::post_execution()");
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
    if(!m_memory.update_database()){
        spdlog::warn("Could not update datebase.");
    }
}

void Core::handle_gripper(Actuator* cmd){
    if(m_percept.internal_model.hand_activity_state==HandActivityState::hsIdle && cmd->get_gripper_request()!=GripperRequest::None){
        m_percept.internal_model.hand_activity_state=HandActivityState::hsBusy;
        if(cmd->get_gripper_request()==GripperRequest::Grasp){
            std::thread gripper(&Core::grasp,this,cmd->gripper_width,cmd->gripper_speed,cmd->gripper_force,0.1,0.1,cmd->gripper_object);
            gripper.detach();
        }
        if(cmd->get_gripper_request()==GripperRequest::Move){
            std::thread gripper(&Core::move_gripper,this,cmd->gripper_width,cmd->gripper_speed);
            gripper.detach();
        }
        cmd->accecpt_gripper_request();
    }
    if(m_percept.internal_model.hand_activity_state==HandActivityState::hsFinished){
        if(m_hand_grace_period==0){
            m_hand_grace_period++;
        }else{
            m_hand_grace_period=0;
            m_percept.internal_model.hand_activity_state=HandActivityState::hsIdle;
        }
    }
}

franka::Finishable* Core::control_base_cycle(const franka::RobotState& state){
    bool exception=false;
    if(m_skill_engine.is_running_queue() && m_blend_skill){
        if(!m_skill_engine.blend_skill_stage_1()){
            spdlog::error("First stage of skill blending failed.");
            exception=true;
        }
    }
    franka::GripperState gripper_state;
    m_percept.update(m_panda_body.get_panda_model(),state,gripper_state,m_memory.read_parameters()->frames.O_R_T);
    m_memory.internal_update(m_percept);
    if(m_skill_engine.is_running_queue() && m_blend_skill){
        if(!m_skill_engine.blend_skill_stage_2()){
            spdlog::error("Second stage of skill blending failed.");
            exception=true;
        }
        m_blend_skill=false;
    }

    Actuator* cmd=m_skill_engine.get_next_command(m_percept);
    if(!cmd->is_valid()){
        exception=true;
    }
    if(exception){
        cmd->stop();
    }

    handle_gripper(cmd);


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
        spdlog::error("Invalid command from controller pipeline.");
        cmd->stop();
    }
    m_percept.update_controller();
    m_controller_pipeline->update_percept(m_percept.controller);
    for(auto& m : m_safety_stage_2){
        m->step(m_percept,panda_cmd);
    }

    m_skill_engine.log_data(m_percept);

    if(cmd->is_stopped()){
        if(m_skill_engine.is_running_queue()){
            m_blend_skill=true;
            if(m_skill_engine.is_last_skill()){
                spdlog::trace("Core::control_base_cycle.stopped");
                panda_cmd->motion_finished=true;
            }
        }else{
            spdlog::trace("Core::control_base_cycle.stopped");
            panda_cmd->motion_finished=true;
        }
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
    spdlog::trace("Core::grasp_object()");
    const Object* object=m_memory.get_object(name);
    if(object->name=="NullObject"){
        spdlog::error("Cannot find object "+name+" in knowledge base.");
        return false;
    }
    if(!refresh_percept({})){
        spdlog::error("Could not refresh my perception. Discrepancy between real world and believe state is possible.");
        return false;
    }
    if(m_percept.robot_mode==franka::RobotMode::kUserStopped){
        spdlog::error("Action is not permitted while in user mode.");
        return false;
    }
    if(m_panda_body.grasp(object->grasp_width,speed,object->grasp_force,0.005,0.005)){
        m_memory.get_live_context()->grasped_object=object;
        m_memory.internal_update(m_percept);
        m_memory.get_parameters()->user.load_m=object->mass;
        m_memory.get_parameters()->user.load_com=(m_memory.read_parameters()->frames.F_T_EE*mirmi_utils::invert_transformation_matrix(object->OB_T_gp)).block<3,1>(0,3);
        m_memory.get_parameters()->user.load_I=object->OB_I;
        m_memory.get_parameters()->frames.EE_T_TCP=mirmi_utils::invert_transformation_matrix(object->OB_T_gp)*object->OB_T_TCP;
        if(!m_panda_body.set_robot_parameters()){
            return false;
        }
        if(!m_memory.update_database()){
            spdlog::warn("Could not update datebase.");
        }
        return true;
    }else{
        return false;
    }
}

bool Core::home_gripper(){
    spdlog::trace("Core::home_gripper()");
    if(!refresh_percept({})){
        spdlog::error("Could not refresh my perception. Discrepancy between real world and believe state is possible.");
        return false;
    }
    if(m_percept.robot_mode==franka::RobotMode::kUserStopped){
        spdlog::error("Action is not permitted while in user mode.");
        return false;
    }
    return m_panda_body.home_gripper();
}

bool Core::grasp(double width, double speed, double force,double epsilon_inner,double epsilon_outer,std::string object_name){
    spdlog::trace("Core::grasp()");
    if(m_percept.robot_mode==franka::RobotMode::kUserStopped){
        spdlog::error("Action is not permitted while in user mode.");
        return false;
    }
    m_percept.internal_model.hand_activity_state=HandActivityState::hsBusy;
    bool result = m_panda_body.grasp(width,speed,force,epsilon_inner,epsilon_outer);
    const Object* object=m_memory.get_object(object_name);
    if(object->name=="NullObject"){
        spdlog::warn("Cannot find object "+object_name+" in knowledge base.");
    }
    m_memory.get_live_context()->grasped_object=object;
    m_memory.internal_update(m_percept);
    if(!m_memory.update_database()){
        spdlog::warn("Could not update datebase.");
    }
    m_memory.get_parameters()->user.load_m=object->mass;
    m_memory.get_parameters()->user.load_com=(m_memory.read_parameters()->frames.F_T_EE*mirmi_utils::invert_transformation_matrix(object->OB_T_gp)).block<3,1>(0,3);
    m_memory.get_parameters()->user.load_I=object->OB_I;
    m_memory.get_parameters()->frames.EE_T_TCP=mirmi_utils::invert_transformation_matrix(object->OB_T_gp)*object->OB_T_TCP;
    m_percept.internal_model.hand_activity_state=HandActivityState::hsFinished;
    return result;
}

bool Core::move_gripper(double width, double speed){
    spdlog::trace("Core::move_gripper()");
    if(m_percept.robot_mode==franka::RobotMode::kUserStopped){
        spdlog::error("Action is not permitted while in user mode.");
        return false;
    }
    m_percept.internal_model.hand_activity_state=HandActivityState::hsBusy;
    bool result = m_panda_body.move_to_finger_position(width,speed);
    const Object* object=m_memory.get_object("NullObject");
    m_memory.get_live_context()->grasped_object=object;
    m_memory.internal_update(m_percept);
    if(!m_memory.update_database()){
        spdlog::warn("Could not update datebase.");
    }
    m_memory.get_parameters()->user.load_m=object->mass;
    m_memory.get_parameters()->user.load_com=(m_memory.read_parameters()->frames.F_T_EE*mirmi_utils::invert_transformation_matrix(object->OB_T_gp)).block<3,1>(0,3);
    m_memory.get_parameters()->user.load_I=object->OB_I;
    m_memory.get_parameters()->frames.EE_T_TCP=mirmi_utils::invert_transformation_matrix(object->OB_T_gp)*object->OB_T_TCP;
    m_percept.internal_model.hand_activity_state=HandActivityState::hsFinished;
    return result;
}

bool Core::is_grasping(){
    spdlog::trace("Core::is_grasping()");
    refresh_percept({});
    return m_percept.proprioception.is_grasping;
}

bool Core::set_grasped_object(const std::string &name){
    spdlog::trace("Core::set_grasped_object()");
    const Object* object=m_memory.get_object(name);
    if(object->name=="NullObject"){
        spdlog::error("Cannot find object "+name+" in knowledge base.");
        return false;
    }
    if(!refresh_percept({})){
        spdlog::warn("Could not refresh my perception. Discrepancy between real world and believe state is possible.");
    }
    if(m_percept.robot_mode==franka::RobotMode::kUserStopped){
        spdlog::error("Action is not permitted while in user mode.");
        return false;
    }
    m_memory.get_live_context()->grasped_object=object;
    m_memory.internal_update(m_percept);
    if(!m_memory.update_database()){
        spdlog::warn("Could not update datebase.");
    }
    m_memory.get_parameters()->user.load_m=object->mass;
    m_memory.get_parameters()->user.load_com=(m_memory.read_parameters()->frames.F_T_EE*mirmi_utils::invert_transformation_matrix(object->OB_T_gp)).block<3,1>(0,3);
    m_memory.get_parameters()->user.load_I=object->OB_I;
    m_memory.get_parameters()->frames.EE_T_TCP=mirmi_utils::invert_transformation_matrix(object->OB_T_gp)*object->OB_T_TCP;
    return m_panda_body.set_robot_parameters();
}

bool Core::release_object(std::optional<double> width, double speed){
    spdlog::trace("Core::release_object()");
    const Object* object=m_memory.get_live_context()->grasped_object;
    if(object->name=="NullObject" && !is_grasping()){
        spdlog::error("I am not grasping anything.");
        return false;
    }
    if(!refresh_percept({})){
        spdlog::error("Could not refresh my perception. Discrepancy between real world and believe state is possible.");
        return false;
    }
    if(m_percept.robot_mode==franka::RobotMode::kUserStopped){
        spdlog::error("Action is not permitted while in user mode.");
        return false;
    }
    if(!m_memory.update_database()){
        spdlog::warn("Could not update datebase.");
    }
    object=m_memory.get_object("NullObject");
    if(m_panda_body.move_to_finger_position(width.value_or(m_percept.internal_model.max_finger_width),speed)){
        m_memory.get_live_context()->grasped_object=object;
        m_memory.internal_update(m_percept);
        m_memory.get_parameters()->user.load_m=object->mass;
        m_memory.get_parameters()->user.load_com=(m_memory.read_parameters()->frames.F_T_EE*mirmi_utils::invert_transformation_matrix(object->OB_T_gp)).block<3,1>(0,3);
        m_memory.get_parameters()->user.load_I=object->OB_I;
        m_memory.get_parameters()->frames.EE_T_TCP=mirmi_utils::invert_transformation_matrix(object->OB_T_gp)*object->OB_T_TCP;
        m_panda_body.set_robot_parameters();
        return true;
    }else{
        return false;
    }
}

bool Core::refresh_percept(std::optional<Eigen::Matrix<double,3,3> > O_R_TF, bool wait){
    franka::RobotState robot_state;
    franka::GripperState gripper_state;
    if(is_busy()){
        return true;
    }
    bool read_successful=false;
    int count=0;
    if(wait){
        while(!read_successful){
            if(is_busy()){
                return true;
            }
            read_successful=true;
            if(!m_panda_body.get_robot_state(robot_state)){
                spdlog::debug("Core::refresh_percept.failed_to_acquire_robot_state");
                read_successful=false;
            }
            if(!m_panda_body.get_gripper_state(gripper_state)){
                spdlog::debug("Core::refresh_percept.failed_to_acquire_gripper_state");
                read_successful=false;
            }
            if(!read_successful){
                spdlog::debug("Waiting for valid perception...");
                std::this_thread::sleep_for(std::chrono::milliseconds(100));
            }else{
                break;
            }
            if(count>6){
                count = 0;
                spdlog::debug("reconnecting to Robot and Gripper");
                m_panda_body.connect_to_robot(m_memory.get_parameters()->system.robot_ip);
                m_panda_body.connect_to_gripper(m_memory.get_parameters()->system.robot_ip);
            }
            count++;
        }
    }else{
        if(!m_panda_body.get_robot_state(robot_state)){
            spdlog::debug("Core::refresh_percept.failed_to_acquire_robot_state");
            spdlog::debug("reconnecting to Robot");
            m_panda_body.connect_to_robot(m_memory.get_parameters()->system.robot_ip);
            if(!m_panda_body.get_robot_state(robot_state)){
                return false;
            }
        }
        if(!m_panda_body.get_gripper_state(gripper_state)){
            spdlog::debug("Core::refresh_percept.failed_to_acquire_gripper_state");
            spdlog::debug("reconnecting to Gripper");
            m_panda_body.connect_to_gripper(m_memory.get_parameters()->system.robot_ip);
            if(!m_panda_body.get_gripper_state(gripper_state)){
                return false;
            }
        }

    }
    m_percept.update(m_panda_body.get_panda_model(),robot_state,gripper_state,O_R_TF);
    m_controller_pipeline->update_percept(m_percept.controller);
    m_memory.internal_update(m_percept);
    return true;
}

bool Core::unlock_body(){
    spdlog::trace("Core::unlock_body()");
    return m_panda_body.unlock_brakes(m_memory.read_parameters()->system.robot_ip,m_memory.read_parameters()->system.desk_user,m_memory.read_parameters()->system.desk_pwd);
}

bool Core::lock_body(){
    spdlog::trace("Core::lock_body()");
    return m_panda_body.lock_brakes(m_memory.read_parameters()->system.robot_ip,m_memory.read_parameters()->system.desk_user,m_memory.read_parameters()->system.desk_pwd);
}

bool Core::shutdown_body(){
    spdlog::trace("Core::shutdown_body()");
    return m_panda_body.shutdown_robot(m_memory.read_parameters()->system.robot_ip,m_memory.read_parameters()->system.desk_user,m_memory.read_parameters()->system.desk_pwd);
}

bool Core::pack_body(){
    spdlog::trace("Core::pack_body()");
    return m_panda_body.move_to_pack_pose(m_memory.read_parameters()->system.robot_ip,m_memory.read_parameters()->system.desk_user,m_memory.read_parameters()->system.desk_pwd);
}

bool Core::start_desk_task(const std::string &task){
    spdlog::trace("Core::start_desk_task()");
    return m_panda_body.start_desk_task(task,m_memory.read_parameters()->system.robot_ip,m_memory.read_parameters()->system.desk_user,m_memory.read_parameters()->system.desk_pwd);
}

bool Core::stop_desk_task(){
    spdlog::trace("Core::stop_desk_task()");
    return m_panda_body.stop_desk_task(m_memory.read_parameters()->system.robot_ip,m_memory.read_parameters()->system.desk_user,m_memory.read_parameters()->system.desk_pwd);
}

bool Core::recover_body(){
    spdlog::trace("Core::recover_body()");
    return !m_panda_body.recover().exception;
}

const Percept* Core::get_percept() const{
    return &m_percept;
}

bool Core::is_ready() const{
    return m_is_ready;
}

bool Core::is_busy(){
    if(m_mtx_is_busy.try_lock()){
        m_mtx_is_busy.unlock();
        return false;
    }else{
        return true;
    }
}

}

