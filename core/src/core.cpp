#include "core/core.hpp"

#include <msrm_utils/math.hpp>
#include <msrm_utils/conversion.hpp>
#include <msrm_utils/json.hpp>
#include <msrm_utils/system.hpp>
#include "utils/exceptions.hpp"
#include "skill/skill.hpp"
#include "skills/nullskill.hpp"
#include "event_publisher/event_publisher.hpp"
#include "controller_pipeline/cart_torque_pipeline.hpp"
#include "controller_pipeline/joint_torque_pipeline.hpp"
#include "controller_pipeline/cart_velocity_pipeline.hpp"
#include "controller_pipeline/joint_velocity_pipeline.hpp"

#include <iostream>
#include <chrono>
#include <thread>

#include <functional>

#include <spdlog/spdlog.h>

namespace mios {

Core::Core(int argc, char **argv):m_active_skill(std::make_shared<NullSkill>(&m_memory,std::make_shared<SkillParametersNullSkill>())){

    this->_config_internal.path_executable=msrm_utils::get_path_executable(argv);
    this->_config_internal.grasped_object="none";

    spdlog::info("Initializing knowledgebase...");
    if(!m_memory.initialize()){
        spdlog::error("Could not initialize memory, shutting down. Mongodb service must run on port 27017. Check status with <systemctl status mongodb.service>.");
        exit(-1);
    }

    spdlog::info("Initializing MIOS core...");
    if(!initialize()){
        spdlog::warn("Could not initialize MIOS core. I may be able to recover...");
    }
}

Core::~Core(){
    terminate();
}

bool Core::initialize(){
    if(!m_memory.set_default_parameters()){
        return false;
    }

    std::optional<std::string> panda_ip = m_panda_body.get_robot_ip(m_memory.read_parameters()->system.robot_ip);

    if(m_memory.read_parameters()->system.has_robot){
        if(!m_panda_body.connect_to_robot(panda_ip.value())){
            return false;
        }
    }
    if(m_memory.read_parameters()->system.has_gripper){
        if(!m_panda_body.connect_to_gripper(panda_ip.value())){
            return false;
        }
    }
    return true;
}

void Core::terminate(){
    m_panda_body.disconnect_from_robot();
    m_panda_body.disconnect_from_gripper();
}

bool Core::reset(){
    if(!m_memory.load_parameters()){
        return false;
    }
    spdlog::info("Core reset finished.");
    return true;
}

Memory* Core::get_memory(){
    return &m_memory;
}

bool Core::load_skill(std::shared_ptr<Skill> skill){
    spdlog::info("Loading skill "+skill->get_id()+".");
    m_active_skill=skill;
    refresh_percept({});
    m_active_skill->write_O_R_TF_to_config(m_percept);
    refresh_percept(m_memory.read_parameters()->frames.O_R_T);
    m_controller_pipeline->update_percept(m_percept.controller);
    spdlog::info("Applying skill context...");
    m_memory.apply_skill_context(m_active_skill->get_id());
    m_active_skill->ground_objects();
    spdlog::info("Initializing skill...");
    if(!m_active_skill->initialize(m_percept)){
        return false;
    }
    return true;
}

void Core::unload_skill(){
    m_active_skill=std::make_shared<NullSkill>(&m_memory,std::make_shared<SkillParametersNullSkill>());
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
    set_robot_parameters();

    bool result;
    if(m_memory.read_parameters()->control.control_mode==ControlMode::mCartTorque){
        m_controller_pipeline=std::make_unique<CartTorqueControllerPipeline>();
        m_controller_pipeline->initialize(m_percept,&m_memory);
        result=m_panda_body.control(std::bind(&Core::cart_torque_controller_pipeline,this,std::placeholders::_1));
    }
    if(m_memory.read_parameters()->control.control_mode==ControlMode::mJointTorque){
        m_controller_pipeline=std::make_unique<JointTorqueControllerPipeline>();
        m_controller_pipeline->initialize(m_percept,&m_memory);
        result=m_panda_body.control(std::bind(&Core::joint_torque_controller_pipeline,this,std::placeholders::_1));
    }
    if(m_memory.read_parameters()->control.control_mode==ControlMode::mCartVelocity){
        m_controller_pipeline=std::make_unique<CartVelocityControllerPipeline>();
        m_controller_pipeline->initialize(m_percept,&m_memory);
        result=m_panda_body.control(std::bind(&Core::joint_torque_controller_pipeline,this,std::placeholders::_1));
    }
    if(m_memory.read_parameters()->control.control_mode==ControlMode::mJointVelocity){
        m_controller_pipeline=std::make_unique<JointVelocityControllerPipeline>();
        m_controller_pipeline->initialize(m_percept,&m_memory);
        result=m_panda_body.control(std::bind(&Core::joint_torque_controller_pipeline,this,std::placeholders::_1));
    }

    m_controller_pipeline->terminate();
    return result;
}

bool Core::set_robot_parameters(){
    ControlParameters controller= m_memory.read_parameters()->controller;
    UserParameters user= m_memory.read_parameters()->user;
    FramesParameters frames =m_memory.read_parameters()->frames;

    std::array<double,3> load_com = msrm_utils::convert_to_array<double,3,1>(user.load_com);
    std::array<double,9> load_I = msrm_utils::convert_to_array<double,3,3>(user.load_I);
    std::array<double,7> tau_contact = msrm_utils::convert_to_array<double,7,1>(user.tau_ext_contact);
    std::array<double,7> tau_max = msrm_utils::convert_to_array<double,7,1>(user.tau_ext_max);
    std::array<double,6> F_contact = msrm_utils::convert_to_array<double,6,1>(user.F_ext_contact);
    std::array<double,6> F_max = msrm_utils::convert_to_array<double,6,1>(user.F_ext_max);
    std::array<double,16> EE_T_K = msrm_utils::convert_to_array<double,4,4>(frames.EE_T_K);
    std::array<double,7> K_theta = msrm_utils::convert_to_array<double,7,1>(controller.joint_imp.K_theta);
    std::array<double,6> K_x = msrm_utils::convert_to_array<double,6,1>(controller.cart_imp.K_x);
    std::array<double,16> F_T_EE = msrm_utils::convert_to_array<double,4,4>(frames.F_T_EE);

    return m_panda_body.set_robot_parameters(user.load_m,load_com,load_I,tau_contact,tau_max,F_contact,F_max,EE_T_K,K_x,K_theta,F_T_EE);
}

franka::Finishable* Core::control_base_cycle(const franka::RobotState& state){

    franka::GripperState gripper_state;
    m_percept.update(m_panda_body.get_panda_model(),state,gripper_state,m_memory.read_parameters()->frames.O_R_T);
    Actuator* cmd=m_active_skill->cycle(m_percept);
    franka::Finishable* panda_cmd=m_controller_pipeline->step(m_percept,*cmd);
    if(!m_controller_pipeline->is_valid_command(panda_cmd)){
        cmd->stop();
    }
    m_controller_pipeline->update_percept(m_percept.controller);
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
    Object* object=m_memory.get_object(name);
    if(object=="NullObject"){
        spdlog::error("Cannot find object "+name+" in knowledge base.");
        return false;
    }
    if(m_panda_body.grasp(object->grasp_width,speed,object->grasp_force,0.005,0.005)){
        m_memory.get_live_context()->grasped_object=object;
        m_memory.get_parameters()->user.load_m=object->mass;
        m_memory.get_parameters()->user.load_com=m_memory.read_parameters()->frames.F_T_EE*msrm_utils::invert_transformation_matrix(object->OB_T_gp);
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

bool Core::home_gripper(){
    return m_panda_body.home_gripper();
}

bool Core::grasp(double width, double speed, double force,double epsilon_inner,double epsilon_outer){
    return m_panda_body.grasp(width,speed,force,epsilon_inner,epsilon_outer);
}

bool Core::move_gripper(double width, double speed){
    return m_panda_body.move_to_finger_position(width,speed);
}

bool Core::is_grasping() const{
    refresh_percept({});
    return m_percept.proprioception.is_grasping;
}

bool Core::set_grasped_object(const std::string &name){
    Object* object=m_memory.get_object(name);
    if(object->name=="NullObject"){
        spdlog::error("Cannot find object "+name+" in knowledge base.");
        return false;
    }
    m_memory.get_live_context()->grasped_object=object;
    m_memory.get_parameters()->user.load_m=object->mass;
    m_memory.get_parameters()->user.load_com=m_memory.read_parameters()->frames.F_T_EE*msrm_utils::invert_transformation_matrix(object->OB_T_gp);
    m_memory.get_parameters()->user.load_I=object->OB_I;
    m_memory.get_parameters()->frames.EE_T_TCP=msrm_utils::invert_transformation_matrix(object->OB_T_gp)*object->OB_T_TCP;
    return set_robot_parameters();
}

bool Core::release_object(double width, double speed){
    Object* object=m_memory.get_live_context()->grasped_object;
    if(object->name=="NullObject"){
        spdlog::error("I am not grasping anything.");
        return false;
    }
    Object* object=m_memory.get_object("NullObject");
    if(m_panda_body.move_to_finger_position(m_percept.internal_model.max_finger_width,speed)){
        m_memory.get_live_context()->grasped_object=object;
        m_memory.get_parameters()->user.load_m=object->mass;
        m_memory.get_parameters()->user.load_com=m_memory.read_parameters()->frames.F_T_EE*msrm_utils::invert_transformation_matrix(object->OB_T_gp);
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
    return true;
}

const Percept* const Core::get_percept() const{
    return m_percept;
}

//void Core::check_cartesian_velocity_workspace(Eigen::Matrix<double, 6, 1> &TF_dX_d, const Percept& p){
//    Eigen::Matrix<double,6,1> VC_dX_d = msrm_utils::rotate_vector(TF_dX_d,msrm_utils::invert_transformation_matrix(this->get_kb()->get_local_memory()->access_config_frames().O_T_VC));
//    Eigen::Matrix<double,3,1> VC_x = msrm_utils::invert_transformation_matrix(this->get_kb()->get_local_memory()->access_config_frames().O_T_VC).block<3,3>(0,0)*p.TF_T_EE.block<3,1>(0,3);
//    bool stop=false;
//    this->event["wall_hit_O"]={false,false,false,false,false,false};
//    double wall_distance=0.01;
//    Eigen::Matrix<double,3,1> wall_hit_O_lower, wall_hit_O_upper, wall_hit_EE_lower, wall_hit_EE_upper;
//    for(unsigned i=0;i<3;i++){
//        double diff_lower = VC_x(i)-this->get_kb()->get_local_memory()->access_config_user().x_limits(2*i);
//        double wall_level_lower=1-diff_lower/wall_distance;
//        if(wall_level_lower>1)wall_level_lower=1;
//        if(wall_level_lower<0)wall_level_lower=0;
//        this->event["wall_hit_O"][2*i]=wall_level_lower;
//        wall_hit_O_lower(i)=wall_level_lower;
//        if(VC_x(i)<=this->get_kb()->get_local_memory()->access_config_user().x_limits(2*i) && VC_dX_d(i)<0){
//            VC_dX_d(i)=0;
//        }
//        double diff_upper = this->get_kb()->get_local_memory()->access_config_user().x_limits(2*i+1)-VC_x(i);
//        double wall_level_upper=1-diff_upper/wall_distance;
//        if(wall_level_upper>1)wall_level_upper=1;
//        if(wall_level_upper<0)wall_level_upper=0;
//        this->event["wall_hit_O"][2*i+1]=wall_level_upper;
//        if(VC_x(i)>=this->get_kb()->get_local_memory()->access_config_user().x_limits(2*i+1) && VC_dX_d(i)>0){
//            VC_dX_d(i)=0;
//        }
//        wall_hit_O_upper(i)=wall_level_upper;
//    }
//    wall_hit_EE_lower=p.TF_T_EE.block<3,3>(0,0).transpose()*wall_hit_O_lower;
//    wall_hit_EE_upper=p.TF_T_EE.block<3,3>(0,0).transpose()*wall_hit_O_upper;
//    Eigen::Matrix<double,6,1> wall_hit_EE;
//    wall_hit_EE<<wall_hit_EE_lower(0),wall_hit_EE_upper(0),wall_hit_EE_lower(1),wall_hit_EE_upper(1),wall_hit_EE_lower(2),wall_hit_EE_upper(2);
//    for(unsigned i=0;i<6;i++){
//        if(wall_hit_EE(i)>1)wall_hit_EE(i)=1;
//        if(wall_hit_EE(i)<0)wall_hit_EE(i)=0;
//    }
//    msrm_utils::write_json_array<double,6,1>(this->event["wall_hit_EE"],wall_hit_EE);
//    TF_dX_d=msrm_utils::rotate_vector(VC_dX_d,this->get_kb()->get_local_memory()->access_config_frames().O_T_VC);
//}


//void Core::base_avoidance(Eigen::Matrix<double, 6, 1> &TF_dX_d, const Percept &p){
//    Eigen::Vector3d cp1,cp2,p_ee;
//    cp1<<0,0,0;
//    cp2<<0,0,0.5;
//    p_ee<<p.O_T_EE(0,3),p.O_T_EE(1,3),p.O_T_EE(2,3);
//    msrm_utils::Cylinder base_cylinder(this->get_kb()->get_local_memory()->access_config_user().base_cylinder_p1,
//                                       this->get_kb()->get_local_memory()->access_config_user().base_cylinder_p2,
//                                       this->get_kb()->get_local_memory()->access_config_user().base_cylinder_radius);
//    if(base_cylinder.contains(p_ee)){
//        Eigen::Matrix<double,3,3> O_R_Cyl = base_cylinder.get_frame(p_ee);
//        Eigen::Matrix<double,6,1> Cyl_dX_d = msrm_utils::rotate_vector(TF_dX_d,msrm_utils::invert_matrix(O_R_Cyl));
//        if(Cyl_dX_d(0)<0){
//            Cyl_dX_d(0)=0.01;
//        }
//        TF_dX_d=msrm_utils::rotate_vector(Cyl_dX_d,O_R_Cyl);
//    }
//}

std::tuple<std::string,std::string,std::string> Core::get_desk_data() const{
    return std::make_tuple(m_memory.read_parameters()->system.desk_name,
                           m_memory.read_parameters()->system.desk_pwd,
                           m_memory.read_parameters()->system.robot_ip);
}

}

