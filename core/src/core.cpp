#include "core/core.hpp"

#include <msrm_utils/math.hpp>
#include <msrm_utils/files.hpp>
#include <msrm_utils/network.hpp>
#include <msrm_utils/conversion.hpp>
#include <msrm_utils/json.hpp>
#include <msrm_utils/system.hpp>
#include "utils/exceptions.hpp"
#include "skill/skill.hpp"
#include "skills/nullskill.hpp"
#include "event_publisher/event_publisher.hpp"

#include <iostream>
#include <chrono>
#include <fstream>
#include <thread>

#include <pwd.h>
#include <signal.h>
#include <stdio.h>
#include <limits.h>
#include <unistd.h>
#include <functional>

#include <SDL2/SDL.h>
#include <SDL2/SDL_mixer.h>

#include <spdlog/spdlog.h>

namespace mios {

Core::Core(int argc, char **argv):_active_skill(std::make_shared<NullSkill>(&_kb,std::make_shared<ConfigSkill>())){

    this->_flag_stop_control=false;
    this->_flag_invalid_mode=false;
    this->_flag_gripper=false;
    this->_flag_gripper_connected=false;
    this->_flag_robot_connected=false;
    this->_flag_gripper_busy=false;
    this->_flag_virt_cube_valid=false;
    this->_flag_virt_walls_joint_valid=false;
    this->_flag_lockdown=false;
    this->_flag_logged_in_digital_twin=false;

    this->_flag_run_gripper=false;
    this->_flag_run_led=false;
    this->_flag_run_sound=false;
    this->_flag_run_beacon=false;

    this->_config_internal.path_executable=msrm_utils::get_path_executable(argv);
    this->_config_internal.grasped_object="none";

    spdlog::info("Initializing knowledgebase...");
    if(!this->_kb.initialize(this->_config_internal)){
        spdlog::error("Could not initialize knowledge base, shutting down. Mongodb service must run on port 27017. Check status with <systemctl status mongodb.service>.");
        exit(-1);
    }

    spdlog::info("Initializing MIOS core...");
    if(!this->initialize()){
        spdlog::warn("Could not initialize MIOS core. I may be able to recover...");
    }
}

Core::~Core(){
    this->terminate();
}

bool Core::initialize(){

    if(!this->_kb.load_parameters()){
        spdlog::error("Could not load all parameters. Robot is not operational.");
        return false;
    }

    std::optional<std::string> panda_ip = m_panda_body.get_robot_ip(_kb.get_local_memory()->access_config_system().ip_robot);

    if(this->_kb.get_local_memory()->access_config_system().has_robot && panda_ip.has_value()){
        if(!m_panda_body.connect_to_robot(panda_ip.value())){
            return false;
        }
    }
    if(this->_kb.get_local_memory()->access_config_system().has_gripper && panda_ip.has_value()){
        if(!m_panda_body.connect_to_gripper(panda_ip.value())){
            return false;
        }
    }
    return true;
}

void Core::terminate(){
    m_panda_body.disconnect_from_robot();
    m_panda_body.disconnect_from_gripper();
    this->_kb.terminate();
}

bool Core::has_terminated() const{
    return this->_flag_stop_control;
}

void Core::lockdown(){
    if(!this->_flag_lockdown){
        this->stop_desk_task();
        this->terminate_control_cycle();
        this->_flag_lockdown=true;
    }
}

void Core::lift_lockdown(){
    if(this->_flag_lockdown){
        this->_flag_lockdown=false;
        this->reset();
    }
}

bool Core::check_lockdown() const{
    return this->_flag_lockdown;
}

bool Core::lock_robot_connection(bool force_lock){
    //    if(this->check_lockdown()){
    //        spdlog::error("Core is under lockdown.");
    //        return false;
    //    }
    if(force_lock){
        this->_mtx_control_cycle.lock();
        return true;
    }else{
        return this->_mtx_control_cycle.try_lock();
    }
}

void Core::unlock_robot_connection(){
    this->_mtx_control_cycle.unlock();
}

bool Core::has_robot_connection() const{
    if(this->m_panda_body==nullptr){
        return false;
    }else{
        return true;
    }
}

bool Core::has_gripper_connection() const{
    if(this->m_panda_hand==nullptr){
        return false;
    }else{
        return true;
    }
}

bool Core::wait_for_idle_state(double max_time){
    auto t_start = std::chrono::system_clock::now();
    bool recover_attempt=false;
    while(true){
        if(this->request_percept().robot_mode==franka::RobotMode::kIdle){
            return true;
        }else{
            auto t_now = std::chrono::system_clock::now();
            double t_wait=std::chrono::duration_cast<std::chrono::microseconds>(t_now-t_start).count();
            if(t_wait>max_time/2 && !recover_attempt){
                spdlog::info("Robot does not reach idle state. I will attempt to recover.");
                if(!this->recover()){
                    return false;
                }
                recover_attempt=true;
            }
            if(t_wait>max_time){
                spdlog::error("Reached maximum allowed time when waiting for idle state of robot.");
                return false;
            }
        }
        usleep(100000);
    }
}

bool Core::reset(){
    if(this->check_lockdown()){
        spdlog::error("Core is under lockdown.");
        return false;
    }
    //    if(!this->terminate()){
    //        return false;
    //    }
    if(!this->_kb.load_parameters()){
        return false;
    }
    this->_flag_stop_control=false;
    this->_flag_invalid_mode=false;
    this->_flag_gripper=false;
    //    this->_flag_gripper_connected=false;
    //    this->_flag_robot_connected=false;
    this->_flag_gripper_busy=false;

    //    if(!this->initialize()){
    //        return false;
    //    }
    spdlog::info("Core reset finished.");
    return true;
}

bool Core::write_config_to_robot(){
    //    if(this->check_lockdown()){
    //        spdlog::error("Core is under lockdown.");
    //        return false;
    //    }
    if(!this->_kb.get_local_memory()->access_config_system().has_robot){
        return true;
    }
    if(this->m_panda_body==nullptr){
        spdlog::error("Cannot set global config, no robot connected, CHECK THIS ERROR!");
        return false;
    }
    const ConfigUser& c_user=this->_kb.get_local_memory()->access_config_user();
    const ConfigFrames& c_frames=this->_kb.get_local_memory()->access_config_frames();
    const ConfigLimits& c_limits=this->_kb.get_local_memory()->access_config_limits();
    Object o;
    try{
        if(this->_kb.load_object(this->_kb.get_local_memory()->access_config_user().grasped_object,o) || this->_kb.get_local_memory()->access_config_user().grasped_object=="none"){
            this->m_panda_body->setLoad(o.mass,msrm_utils::convert_to_array<double,3,1>(o.EE_ob_com),msrm_utils::convert_to_array<double,3,3>(o.ob_I));
        }else{
            this->m_panda_body->setLoad(c_user.load_m,msrm_utils::convert_to_array<double,3,1>(c_user.load_com),msrm_utils::convert_to_array<double,3,3>(c_user.load_I));
        }
        if(!this->set_ee()){
            return false;
        }
        this->m_panda_body->setCollisionBehavior(msrm_utils::convert_to_array<double,7,1>(c_user.tau_contact),
                                                 msrm_utils::convert_to_array<double,7,1>(c_limits.tau_ext_max),
                                                 msrm_utils::convert_to_array<double,6,1>(c_user.F_contact),
        {c_limits.F_ext_max(0),c_limits.F_ext_max(0),c_limits.F_ext_max(0),c_limits.F_ext_max(1),c_limits.F_ext_max(1),c_limits.F_ext_max(1)});
        this->m_panda_body->setK(msrm_utils::convert_to_array<double,4,4>(c_frames.EE_T_K));

        this->m_panda_body->setJointImpedance({9000,9000,9000,7500,7500,6000,6000});
    }catch(franka::CommandException& e){
        std::cout<<e.what()<<std::endl;
        return false;
    }catch(franka::NetworkException& e){
        std::cout<<e.what()<<std::endl;
        return false;
    }
    return true;
}

bool Core::set_ee(){
    //    if(this->check_lockdown()){
    //        spdlog::error("Core is under lockdown.");
    //        return false;
    //    }
    if(!this->_kb.get_local_memory()->access_config_system().has_robot){
        return true;
    }
    if(this->m_panda_body==nullptr){
        spdlog::error("Can not set EE, no connection to robot.");
        return false;
    }
    Object obj;
    if(!this->_kb.load_object(this->_percept.mios_state.grasped_object,obj)){
        return false;
    }
    nlohmann::json p_frame;
    msrm_utils::write_json_array<double,4,4>(p_frame["EE_T_TCP"],obj.EE_T_O);
    //    this->_kb.get_local_memory()->modify_config_frames(p_frame);
    this->get_kb()->get_local_memory()->get_persistent_data()->EE_T_TCP=obj.EE_T_O;
    Eigen::Matrix<double,4,4> F_T_TCP=msrm_utils::rotate_matrix(this->get_kb()->get_local_memory()->get_persistent_data()->EE_T_TCP,this->_kb.get_local_memory()->access_config_frames().F_T_EE);
    try{
        this->m_panda_body->setEE(msrm_utils::convert_to_array<double,4,4>(F_T_TCP));
    }catch(franka::CommandException& e){
        std::cout<<e.what()<<std::endl;
        return false;
    }catch(franka::NetworkException& e){
        std::cout<<e.what()<<std::endl;
        return false;
    }
    return true;
}

std::string Core::get_last_error() const{
    return this->_last_error;
}

void Core::set_live_parameter_server(ParameterServer* server){
    this->_kb.set_live_parameter_server(server);
}

KnowledgeBase* Core::get_kb(){
    return &this->_kb;
}

bool Core::validity_check_torque(std::array<double,7>& tau_J){

    const ConfigLimits& c_limits=this->_kb.get_local_memory()->access_config_limits();
    const ConfigFrames& c_frames=this->_kb.get_local_memory()->access_config_frames();

    // check O_R_TF
    Eigen::Matrix<double,3,3> O_R_TF_check;
    O_R_TF_check=msrm_utils::rotate_matrix(c_frames.O_R_TF,c_frames.O_R_TF);
    Eigen::Matrix<double,3,1> O_R_TF_x;
    O_R_TF_x<<c_frames.O_R_TF(0,0),c_frames.O_R_TF(1,0),c_frames.O_R_TF(2,0);
    Eigen::Matrix<double,3,1> O_R_TF_z;
    O_R_TF_z<<c_frames.O_R_TF(0,2),c_frames.O_R_TF(1,2),c_frames.O_R_TF(2,2);
    Eigen::Matrix<double,3,1> O_R_TF_y = O_R_TF_z.cross(O_R_TF_x);

    if(fabs(c_frames.O_R_TF(0,1)-O_R_TF_y(0)+c_frames.O_R_TF(1,1)-O_R_TF_y(1)+c_frames.O_R_TF(2,1)-O_R_TF_y(2))>1e-3){
        spdlog::warn("Warning, O_R_TF not valid. Cross product of z and x does not yield y.");
        return false;
    }

    for(unsigned i=0;i<this->_percept.dq.SizeAtCompileTime;i++){
        if(fabs(this->_percept.dq(i))>c_limits.dq_max(i)){
            spdlog::warn("Maximum allowed joint velocity has been reached at joint "+std::to_string(i+1)+".");
            return false;
        }
    }
    for(unsigned i=0;i<3;i++){
        if(fabs(this->_percept.TF_dX(i))>c_limits.dX_max(0)){
            spdlog::warn("Maximum allowed Cartesian velocity has been reached in dimension "+std::to_string(i+1)+".");
            return false;
        }
        if(fabs(this->_percept.TF_dX(i+3))>c_limits.dX_max(1)){
            spdlog::warn("Maximum allowed Cartesian velocity has been reached in dimension "+std::to_string(i+4)+".");
            return false;
        }
    }

    for(unsigned i=0;i<7;i++){
        if(tau_J[i]!=tau_J[i]){
            spdlog::error("NaN detected in tau_J command at controller stage.");
        }
        if(fabs(tau_J[i])>c_limits.tau_J_max[i]){
            spdlog::warn("Maximum allowed tau_J reached at controller stage.");
            return false;
        }
    }
    return true;
}

bool Core::validity_check_velocity_cart(std::array<double, 6> &O_dP_EE_d){
    const ConfigLimits& c_limits=this->_kb.get_local_memory()->access_config_limits();
    const ConfigFrames& c_frames=this->_kb.get_local_memory()->access_config_frames();

    // check O_R_TF
    Eigen::Matrix<double,3,3> O_R_TF_check;
    O_R_TF_check=msrm_utils::rotate_matrix(c_frames.O_R_TF,c_frames.O_R_TF);
    Eigen::Matrix<double,3,1> O_R_TF_x;
    O_R_TF_x<<c_frames.O_R_TF(0,0),c_frames.O_R_TF(1,0),c_frames.O_R_TF(2,0);
    Eigen::Matrix<double,3,1> O_R_TF_z;
    O_R_TF_z<<c_frames.O_R_TF(0,2),c_frames.O_R_TF(1,2),c_frames.O_R_TF(2,2);
    Eigen::Matrix<double,3,1> O_R_TF_y = O_R_TF_z.cross(O_R_TF_x);

    if(fabs(c_frames.O_R_TF(0,1)-O_R_TF_y(0)+c_frames.O_R_TF(1,1)-O_R_TF_y(1)+c_frames.O_R_TF(2,1)-O_R_TF_y(2))>1e-3){
        spdlog::warn("Warning, O_R_TF not valid. Cross product of z and x does not yield y.");
        return false;
    }

    for(unsigned i=0;i<this->_percept.dq.SizeAtCompileTime;i++){
        if(fabs(this->_percept.dq(i))>c_limits.dq_max(i)){
            spdlog::warn("Maximum allowed joint velocity has been reached at joint "+std::to_string(i+1)+".");
            return false;
        }
    }
    for(unsigned i=0;i<3;i++){
        if(fabs(this->_percept.TF_dX(i))>c_limits.dX_max(0)){
            spdlog::warn("Maximum allowed Cartesian velocity has been reached in dimension "+std::to_string(i+1)+".");
            return false;
        }
        if(fabs(this->_percept.TF_dX(i+3))>c_limits.dX_max(1)){
            spdlog::warn("Maximum allowed Cartesian velocity has been reached in dimension "+std::to_string(i+4)+".");
            return false;
        }
    }

    for(unsigned i=0;i<6;i++){
        if(O_dP_EE_d[i]!=O_dP_EE_d[i]){
            spdlog::error("NaN detected in O_dP_EE_d command at controller stage.");
        }
    }

    return true;
}

bool Core::validity_check_velocity_joint(std::array<double, 7> &dq_d){
    const ConfigLimits& c_limits=this->_kb.get_local_memory()->access_config_limits();
    const ConfigFrames& c_frames=this->_kb.get_local_memory()->access_config_frames();


    for(unsigned i=0;i<this->_percept.dq.SizeAtCompileTime;i++){
        if(fabs(this->_percept.dq(i))>c_limits.dq_max(i)){
            spdlog::warn("Maximum allowed joint velocity has been reached at joint "+std::to_string(i+1)+".");
            return false;
        }
    }

    for(unsigned i=0;i<7;i++){
        if(dq_d[i]!=dq_d[i]){
            spdlog::error("NaN detected in dq_d command at controller stage.");
        }
    }

    return true;
}

MiosState* Core::get_mios_state(){
    return &this->_percept.mios_state;
}

bool Core::load_skill(std::shared_ptr<Skill> skill){
    spdlog::info("Loading skill "+skill->get_id()+".");
    // set active skill and setup
    m_active_skill=skill;
    refresh_percept();
    m_active_skill->write_O_R_TF_to_config(m_percept);
    refresh_percept(m_active_skill->get_config<>()->frames.O_R_TF);
    m_percept.Controller.K_x=m_active_skill->get_config<>()->controller.K_0;
    m_percept.Controller.xi_x=m_active_skill->get_config<>()->controller.xi;
    m_percept.Controller.K_theta=m_active_skill->get_config<>()->controller.K_theta;
    m_percept.Controller.xi_theta=m_active_skill->get_config<>()->controller.xi_theta;
    spdlog::info("Initializing skill "+m_active_skill->get_id);
    if(!m_active_skill->initialize(m_percept)){
        spdlog::info("failed.");
        return false;
    }
    spdlog::info("done.");
    this->_kb.get_local_memory()->upload_config_cntr(m_active_skill->get_config<>()->controller);
    this->_kb.get_local_memory()->upload_config_frames(m_active_skill->get_config<>()->frames);
    this->_kb.get_local_memory()->upload_config_general(m_active_skill->get_config<>()->general);
    this->_kb.get_local_memory()->upload_config_user(m_active_skill->get_config<>()->user);

    return true;
}

void Core::unload_skill(){
    m_active_skill=std::make_shared<NullSkill>(&_kb,std::make_shared<ConfigSkill>());
    this->_kb.load_parameters();
    this->_flag_stop_control=false;
}

void Core::toggle_skill_pause(bool pause){
    this->_active_skill->set_pause(pause);
}

void Core::gripper_cycle(){
    while(true){
        if(!this->_flag_gripper && !this->_flag_gripper_busy){
            try{
                this->_gripper_state=this->m_panda_hand->readOnce();
                this->_flag_gripper=true;
            }catch(const franka::NetworkException& e){
                std::cout<<e.what()<<std::endl;
                spdlog::error("No connection to gripper, check network connection.");
                break;
            }catch(const franka::InvalidOperationException& e){
                std::cout<<e.what()<<std::endl;
            }
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
        if(!this->_flag_run_gripper){
            spdlog::info("Gripper thread has stopped.");
            return;
        }
    }
}

void Core::terminate_gripper(){
    if(this->_thr_gripper.joinable()){
        this->_flag_run_gripper=false;
    }
    this->_flag_gripper=false;
}

void Core::terminate_periphery(){
    if(this->_thr_sound.joinable()){
        this->_flag_run_sound=false;
    }
}

void Core::initialize_control_joint_imp(const Percept &p){
    cntr_joint_var_imp::In_P_cntr_joint_var_imp in_p_joint_imp;
    const ConfigController& c_cntr=this->_kb.get_local_memory()->access_config_cntr();

    in_p_joint_imp.enable_ffwd_acc.setZero();
    in_p_joint_imp.enable_ffwd_vel<<1;

    this->_in_u_joint_imp.theta_d=p.q;

    this->input_control_joint_imp(p);
    this->_in_u_joint_imp.K_theta=c_cntr.K_theta;
    this->_in_u_joint_imp.D_theta=c_cntr.xi_theta;

    this->_cntr_joint_imp.initialize(this->_in_u_joint_imp,in_p_joint_imp);

    this->_percept.K_theta=c_cntr.K_theta;
    this->_percept.xi_theta=c_cntr.xi_theta;
}


void Core::initialize_motion_error(const Percept &p){
    this->_in_u_motion_error_cart.O_T_EE=p.TF_T_EE;
    this->_in_u_motion_error_cart.O_T_EE_d=p.TF_T_EE_d;

    motion_error_cart::In_P_motion_error_cart in_p;
    this->_motion_error_cart.initialize(this->_in_u_motion_error_cart,in_p);
    this->input_motion_error(p);
}

void Core::input_motion_error(const Percept &p){
    this->_in_u_motion_error_cart.O_T_EE=p.TF_T_EE;
    this->_in_u_motion_error_cart.O_T_EE_d=p.TF_T_EE_d;
}

void Core::input_control_joint_imp(const Percept &p){    
    this->_in_u_joint_imp.theta=p.q;
    this->_in_u_joint_imp.theta_d=p.q;
    this->_in_u_joint_imp.dtheta=p.dq;
    this->_in_u_joint_imp.dtheta_d<<0,0,0,0,0,0,0;
    this->_in_u_joint_imp.ddtheta_d<<0,0,0,0,0,0,0;
    this->_in_u_joint_imp.M=p.M;
    this->_in_u_joint_imp.tau_ff.setZero();
}


void Core::input_control_nullspace(const Percept &p){
    this->_in_u_cntr_nullsp_q.theta=p.q;
    //    this->_in_u_cntr_nullsp_q.theta_d=p.q;
    this->_in_u_cntr_nullsp_q.dtheta=p.dq;
    this->_in_u_cntr_nullsp_q.dtheta_d<<0,0,0,0,0,0,0;
    this->_in_u_cntr_nullsp_q.ddtheta_d<<0,0,0,0,0,0,0;
    this->_in_u_cntr_nullsp_q.M=p.M;
    this->_in_u_cntr_nullsp_q.tau_ff.setZero();

    this->_in_u_cntr_nullsp_proj.J=p.B_J_EE;
    this->_in_u_cntr_nullsp_proj.M=p.M;
    this->_in_u_cntr_nullsp_proj.tau_c.setZero();
}

void Core::terminate_control(){
    int mode = this->_kb.get_local_memory()->access_config_general().control_mode;
    switch(mode){
    case 0:
        this->_cntr_aic.terminate();
        this->_cntr_force.terminate();
        this->_cntr_mux.terminate();
        this->_conv_vel2pose.terminate();
        if(this->_kb.get_local_memory()->access_config_cntr().virt_cube_on){
            this->_virt_cube.terminate();
        }
        if(this->_kb.get_local_memory()->access_config_cntr().virt_walls_joint_on){
            this->_virt_walls_joint.terminate();
        }
        if(this->_kb.get_local_memory()->access_config_cntr().nullspace_cntr_on){
            this->_cntr_nullsp_q.terminate();
            this->_cntr_nullsp_proj.terminate();
        }
        break;
    case 2:
        this->_cntr_joint_imp.terminate();
        this->_cntr_mux.terminate();
        if(this->_kb.get_local_memory()->access_config_cntr().nullspace_cntr_on){
            this->_cntr_nullsp_q.terminate();
            this->_cntr_nullsp_proj.terminate();
        }
        break;
    default:break;
    }

}

bool Core::execute_skill(){
    spdlog::debug("CORE: execute_skill");

    this->_flag_stop_control=false;
    this->_flag_virt_cube_valid=false;
    this->_flag_virt_walls_joint_valid=false;
    this->t_event=std::chrono::system_clock::now();

    this->_last_error="none";


    if(!m_panda_body.pre_run_checks()){
        if(!m_panda_body.recover()){
            return false;
        }
    }

    spdlog::debug("CORE: start_control_cycle: while-loop");
    this->_tau_J_old={0,0,0,0,0,0,0};
    refresh_percept(m_active_skill->get_config<>()->frames.O_R_TF);
    this->process_commands(cmd);
    auto config_control = m_active_skill->get_config<>()->control;
    if(!m_panda_body.set_robot_parameters()){
        return false;
    }

    bool result;
    if(this->_kb.get_local_memory()->access_config_general().control_mode==ControlMode::mCartTorque){

        m_controller_pipeline=std::make_unique<CartTorqueControllerPipeline>();
        m_controller_pipeline->initialize(m_percept,_kb);
        result=m_panda_body.torque_control(std::bind(&Core::control_cycle_torque_cart,this,std::placeholders::_1));
    }
    if(this->_kb.get_local_memory()->access_config_general().control_mode==ControlMode::mJointTorque){
        result=m_panda_body.torque_control(std::bind(&Core::control_cycle_torque_cart,this,std::placeholders::_1));
    }
    if(this->_kb.get_local_memory()->access_config_general().control_mode==ControlMode::mCartVelocity){
        result=m_panda_body.torque_control(std::bind(&Core::control_cycle_torque_cart,this,std::placeholders::_1));
    }
    if(this->_kb.get_local_memory()->access_config_general().control_mode==ControlMode::mJointVelocity){
        result=m_panda_body.torque_control(std::bind(&Core::control_cycle_torque_cart,this,std::placeholders::_1));
    }

    this->terminate_gripper();
    this->terminate_control();
    this->terminate_periphery();


    return result;
}

void Core::terminate_control_cycle(){
    this->_flag_stop_control=true;
}

Actuator* Core::control_base_cycle(const franka::RobotState& state){

    franka::GripperState gripper_state;
    m_percept.update(m_panda_body.get_panda_model(),state,gripper_state,m_active_skill->get_config<>()->frames.O_R_TF);

    this->input_motion_error(this->_percept);
    this->_motion_error_cart.step(this->_in_u_motion_error_cart,this->_out_y_motion_error_cart);
    Actuator* cmd=m_active_skill->cycle(m_percept);

    if(cmd->is_stopped()){
        spdlog::info("Skill has terminated.");
        this->terminate_control_cycle();
    }
    return cmd;
}


franka::Torques Core::control_cycle_torque_cart(const franka::RobotState state){
    auto t_s_start = std::chrono::system_clock::now();
    CmdSkill cmd_skill;

    if(!this->control_base_cycle(state,cmd_skill)){
        franka::Torques tau={0,0,0,0,0,0,0};
        return franka::MotionFinished(tau);
    }

    this->input_control_aic(this->_percept);
    this->input_control_force(this->_percept);
    this->input_control_mux(this->_percept);
    this->input_virtual_cube(this->_percept);
    this->input_virtual_walls_joint(this->_percept);
    this->input_control_nullspace(this->_percept);

    this->check_cartesian_velocity_workspace(cmd_skill.TF_dX_d,this->_percept);
    //    this->base_avoidance(cmd_skill.TF_dX_d,this->_percept);

    this->_in_u_vel2pose.TF_dX_d=cmd_skill.TF_dX_d;
    this->_conv_vel2pose.step(this->_in_u_vel2pose,this->_out_y_vel2pose);

    this->_in_u_aic.TF_F_ff=cmd_skill.TF_F_ff;
    this->_in_u_aic.K_x=cmd_skill.K_x;
    this->_in_u_aic.xi_x=cmd_skill.xi_x;

    if(this->get_kb()->get_local_memory()->access_config_general().command_mode==0){
        this->_in_u_aic.TF_T_EE_d=this->_out_y_vel2pose.TF_T_EE_d;
        this->_percept.TF_T_EE_d=this->_out_y_vel2pose.TF_T_EE_d;
    }else if(this->get_kb()->get_local_memory()->access_config_general().command_mode==1){
        this->_in_u_aic.TF_T_EE_d=cmd_skill.TF_T_EE_d;
    }else{
        spdlog::error("Invalid command mode. Can either be 0 for velocity commands or 1 for pose commands.");
        this->terminate_control_cycle();
    }

    this->_cntr_aic.step(this->_in_u_aic,this->_out_y_aic);

    this->_percept.K_x=this->_cntr_aic.get_out_l().K_x;
    this->_percept.xi_x=this->_cntr_aic.get_out_l().xi_x;

    this->_in_u_force.DX<<this->_out_y_vel2pose.TF_T_EE_d(0,3)-this->_percept.TF_T_EE(0,3),this->_out_y_vel2pose.TF_T_EE_d(1,3)-this->_percept.TF_T_EE(1,3),this->_out_y_vel2pose.TF_T_EE_d(2,3)-this->_percept.TF_T_EE(2,3),0,0,0;
    this->_in_u_force.TF_F_d_K=cmd_skill.TF_F_d;
    this->_cntr_force.step(this->_in_u_force,this->_out_y_force);
    this->_percept.rho=this->_cntr_force.get_out_l().rho;

    if(this->_kb.get_local_memory()->access_config_cntr().virt_cube_on){
        this->_virt_cube.step(this->_in_u_virt_cube,this->_out_y_virt_cube);
    }
    if(this->_kb.get_local_memory()->access_config_cntr().virt_walls_joint_on){
        this->_virt_walls_joint.step(this->_in_u_virt_walls_joint,this->_out_y_virt_walls_joint);
    }

    bool cube_valid = this->validity_check_virtual_cube();
    bool walls_joint_valid = this->validity_check_virtual_walls_joint();

    if(this->_kb.get_local_memory()->access_config_cntr().nullspace_cntr_on){
        this->_cntr_nullsp_q.step(this->_in_u_cntr_nullsp_q,this->_out_y_cntr_nullsp_q);
        this->_in_u_cntr_nullsp_proj.tau_c=this->_out_y_cntr_nullsp_q.tau_J_d;
        this->_cntr_nullsp_proj.step(this->_in_u_cntr_nullsp_proj,this->_out_y_cntr_nullsp_proj);
    }
    this->_in_u_mux.tau_J_d.setZero();
    for(unsigned i=0;i<7;i++){
        this->_in_u_mux.tau_J_d(i)+=cmd_skill.tau_ff(i);
        if(cmd_skill.on_cntrl_imp){
            this->_in_u_mux.tau_J_d(i)+=this->_out_y_aic.tau_J_d(i);
        }
        if(cmd_skill.on_cntrl_force){
            this->_in_u_mux.tau_J_d(i)+=this->_out_y_force.tau_J_d(i);
        }
        if(this->get_kb()->get_local_memory()->access_config_cntr().virt_cube_on && cube_valid){
            this->_in_u_mux.tau_J_d(i)+=this->_out_y_virt_cube.tau_vwalls(i);
        }
        if(this->get_kb()->get_local_memory()->access_config_cntr().virt_walls_joint_on && walls_joint_valid){
            this->_in_u_mux.tau_J_d(i)+=this->_out_y_virt_walls_joint.tau_vwalls(i);
        }
        if(this->get_kb()->get_local_memory()->access_config_cntr().nullspace_cntr_on){
            this->_in_u_mux.tau_J_d(i)+=this->_out_y_cntr_nullsp_proj.tau_n(i);
        }
        for(unsigned i=0;i<7;i++){
            if(fabs(this->_percept.dq(i))>0.5){
                this->_in_u_mux.tau_J_d(i)-=this->get_kb()->get_local_memory()->access_config_cntr().D_additional(i)*(fabs(this->_percept.dq(i))-0.5)*msrm_utils::sgn(this->_percept.dq(i));
            }
            //            this->_in_u_mux.tau_J_d(i)-=this->get_kb()->get_local_memory()->access_config_cntr().D_additional(i)*this->_percept.dq(i);
        }
    }

    this->_cntr_mux.step(this->_in_u_mux,this->_out_y_mux);

    franka::Torques tau_J_checked={this->_out_y_mux.tau_J_d_checked[0],this->_out_y_mux.tau_J_d_checked[1],this->_out_y_mux.tau_J_d_checked[2],
                                   this->_out_y_mux.tau_J_d_checked[3],this->_out_y_mux.tau_J_d_checked[4],this->_out_y_mux.tau_J_d_checked[5],
                                   this->_out_y_mux.tau_J_d_checked[6]};


    if(!this->validity_check_torque(tau_J_checked.tau_J)){
        this->terminate_control_cycle();
    }

    auto t_s_end = std::chrono::system_clock::now();
    double t=std::chrono::duration_cast<std::chrono::microseconds>(t_s_end-t_s_start).count();

    if(this->_flag_stop_control){
        spdlog::info("Controller cycle has been terminated.");
        return franka::MotionFinished(tau_J_checked);
    }
    if(this->_kb.get_local_memory()->access_config_general().safe_mode){
        std::cout<<"tau_J=["<<tau_J_checked.tau_J[0]<<","<<tau_J_checked.tau_J[1]<<","<<tau_J_checked.tau_J[2]<<","<<tau_J_checked.tau_J[3]
                <<","<<tau_J_checked.tau_J[4]<<","<<tau_J_checked.tau_J[5]<<","<<tau_J_checked.tau_J[6]<<"]"<<std::endl;
        spdlog::info("Cycle time: "+std::to_string(t));
        tau_J_checked.tau_J={0,0,0,0,0,0,0};
    }

    this->_tau_J_last=tau_J_checked.tau_J;
    return tau_J_checked;
}

franka::Torques Core::control_cycle_torque_joint(const franka::RobotState state){
    auto t_s_start = std::chrono::system_clock::now();
    CmdSkill cmd_skill;
    if(!this->control_base_cycle(state,cmd_skill)){
        franka::Torques tau={0,0,0,0,0,0,0};
        return franka::MotionFinished(tau);
    }

    this->input_control_joint_imp(this->_percept);
    this->input_virtual_walls_joint(this->_percept);
    this->input_control_nullspace(this->_percept);

    this->_in_u_joint_imp.theta_d=cmd_skill.q_d;
    this->_in_u_joint_imp.tau_ff=cmd_skill.tau_ff;
    this->_in_u_joint_imp.K_theta=cmd_skill.K_theta;
    this->_in_u_joint_imp.D_theta=cmd_skill.xi_theta;

    this->_cntr_joint_imp.step(this->_in_u_joint_imp,this->_out_y_joint_imp);

    this->_percept.K_theta=this->_cntr_joint_imp.get_out_l().K_theta;
    this->_percept.xi_theta=this->_cntr_joint_imp.get_out_l().D_theta;

    if(this->_kb.get_local_memory()->access_config_cntr().virt_walls_joint_on){
        this->_virt_walls_joint.step(this->_in_u_virt_walls_joint,this->_out_y_virt_walls_joint);
    }

    bool walls_joint_valid = this->validity_check_virtual_walls_joint();

    if(this->_kb.get_local_memory()->access_config_cntr().nullspace_cntr_on){
        this->_cntr_nullsp_q.step(this->_in_u_cntr_nullsp_q,this->_out_y_cntr_nullsp_q);
        this->_in_u_cntr_nullsp_proj.tau_c=this->_out_y_cntr_nullsp_q.tau_J_d;
        this->_cntr_nullsp_proj.step(this->_in_u_cntr_nullsp_proj,this->_out_y_cntr_nullsp_proj);
    }

    for(unsigned i=0;i<7;i++){
        this->_in_u_mux.tau_J_d(i)=this->_out_y_joint_imp.tau_J_d(i);
        if(this->get_kb()->get_local_memory()->access_config_cntr().virt_walls_joint_on && walls_joint_valid){
            this->_in_u_mux.tau_J_d(i)+=this->_out_y_virt_walls_joint.tau_vwalls(i);
        }
        if(this->get_kb()->get_local_memory()->access_config_cntr().nullspace_cntr_on){
            this->_in_u_mux.tau_J_d(i)+=this->_out_y_cntr_nullsp_proj.tau_n(i);
        }
    }

    this->_cntr_mux.step(this->_in_u_mux,this->_out_y_mux);

    franka::Torques tau_J_checked={this->_out_y_mux.tau_J_d_checked[0],this->_out_y_mux.tau_J_d_checked[1],this->_out_y_mux.tau_J_d_checked[2],
                                   this->_out_y_mux.tau_J_d_checked[3],this->_out_y_mux.tau_J_d_checked[4],this->_out_y_mux.tau_J_d_checked[5],
                                   this->_out_y_mux.tau_J_d_checked[6]};

    if(!this->validity_check_torque(tau_J_checked.tau_J)){
        this->terminate_control_cycle();
    }

    auto t_s_end = std::chrono::system_clock::now();

    double t=std::chrono::duration_cast<std::chrono::microseconds>(t_s_end-t_s_start).count();

    if(this->_flag_stop_control){
        spdlog::info("Controller cycle has been terminated.");
        return franka::MotionFinished(tau_J_checked);
    }
    if(this->_kb.get_local_memory()->access_config_general().safe_mode){
        std::cout<<"tau_J=["<<tau_J_checked.tau_J[0]<<","<<tau_J_checked.tau_J[1]<<","<<tau_J_checked.tau_J[2]<<","<<tau_J_checked.tau_J[3]
                <<","<<tau_J_checked.tau_J[4]<<","<<tau_J_checked.tau_J[5]<<","<<tau_J_checked.tau_J[6]<<"]"<<std::endl;
        spdlog::info("Cycle time: "+std::to_string(t));
        tau_J_checked.tau_J={0,0,0,0,0,0,0};
    }
    this->_tau_J_last=tau_J_checked.tau_J;

    return tau_J_checked;
}

franka::CartesianVelocities Core::control_cycle_velocity_cart(const franka::RobotState state){

    auto t_s_start = std::chrono::system_clock::now();
    CmdSkill cmd_skill;
    if(!this->control_base_cycle(state,cmd_skill)){
        franka::CartesianVelocities O_dP_EE_d={0,0,0,0,0,0};
        return franka::MotionFinished(O_dP_EE_d);
    }
    this->check_cartesian_velocity_workspace(cmd_skill.TF_dX_d,this->_percept);
    this->base_avoidance(cmd_skill.TF_dX_d,this->_percept);

    franka::CartesianVelocities O_dP_EE_d = msrm_utils::convert_to_array<double,6,1>(msrm_utils::rotate_vector(cmd_skill.TF_dX_d,this->_active_skill->get_config<>()->frames.O_R_TF));
    if(!this->validity_check_velocity_cart(O_dP_EE_d.O_dP_EE)){
        this->terminate_control_cycle();
    }

    auto t_s_end = std::chrono::system_clock::now();

    double t=std::chrono::duration_cast<std::chrono::microseconds>(t_s_end-t_s_start).count();

    if(this->_flag_stop_control){
        spdlog::info("Controller cycle has been terminated.");
        return franka::MotionFinished(O_dP_EE_d);
    }
    if(this->_kb.get_local_memory()->access_config_general().safe_mode){
        std::cout<<"O_dP_EE_d=["<<O_dP_EE_d.O_dP_EE[0]<<","<<O_dP_EE_d.O_dP_EE[1]<<","<<O_dP_EE_d.O_dP_EE[2]<<","<<O_dP_EE_d.O_dP_EE[3]<<","<<O_dP_EE_d.O_dP_EE[4]<<","<<O_dP_EE_d.O_dP_EE[5]<<std::endl;
        spdlog::info("Cycle time: "+std::to_string(t));
        O_dP_EE_d={0,0,0,0,0,0};
    }

    return O_dP_EE_d;
}

franka::JointVelocities Core::control_cycle_velocity_joint(const franka::RobotState state){
    auto t_s_start = std::chrono::system_clock::now();
    CmdSkill cmd_skill;
    if(!this->control_base_cycle(state,cmd_skill)){
        franka::JointVelocities dq_d={0,0,0,0,0,0,0};
        return franka::MotionFinished(dq_d);
    }
    franka::JointVelocities dq_d = msrm_utils::convert_to_array<double,7,1>(cmd_skill.dq_d);

    if(!this->validity_check_velocity_joint(dq_d.dq)){
        this->terminate_control_cycle();
    }

    auto t_s_end = std::chrono::system_clock::now();

    double t=std::chrono::duration_cast<std::chrono::microseconds>(t_s_end-t_s_start).count();

    if(this->_flag_stop_control){
        return franka::MotionFinished(dq_d);
    }
    if(this->_kb.get_local_memory()->access_config_general().safe_mode){
        std::cout<<"dq_d=["<<dq_d.dq[0]<<","<<dq_d.dq[1]<<","<<dq_d.dq[2]<<","<<dq_d.dq[3]<<","<<dq_d.dq[4]<<","<<dq_d.dq[5]<<","<<dq_d.dq[6]<<std::endl;
        spdlog::info("Cycle time: "+std::to_string(t));
        dq_d={0,0,0,0,0,0,0};
    }

    return dq_d;
}

void Core::process_commands(const CmdSkill &cmd){
    this->_percept.TF_T_EE_d=cmd.TF_T_EE_d;
    this->_percept.TF_dX_d=cmd.TF_dX_d;
    this->_percept.TF_F_ff=cmd.TF_F_ff;
    this->_percept.q_d=cmd.q_d;
    this->_percept.dq_d=cmd.dq_d;
    this->_percept.tau_ff=cmd.tau_ff;
}

void Core::cycle_led(std::function<LEDCmd(const Percept& p)> callback_led){
    unsigned T;

    while(true){
        LEDCmd led_output = callback_led(this->_percept);
        if(led_output.finished){
            spdlog::info("Unloading LED pattern");
            return;
        }

        if(led_output.f>0){
            T=1/led_output.f*1000;
        }
        if(led_output.f<=0){
            T=std::numeric_limits<unsigned>::max();
        }
        nlohmann::json request;
        for(const auto& led : led_output.led){
            nlohmann::json l;
            l["colors"].emplace_back(std::get<0>(led.second.colors));
            l["colors"].emplace_back(std::get<1>(led.second.colors));
            l["colors"].emplace_back(std::get<2>(led.second.colors));
            l["tt"]=led.second.tt;
            l["id"]=this->_led_panel_id[led.first];
            request.push_back(l);
        }
        nlohmann::json response;
        msrm_utils::JsonRPCClient::call_method("localhost",9000,"set_led",request,response);

        std::this_thread::sleep_for(std::chrono::milliseconds(T));
        if(!this->_flag_run_led){
            spdlog::info("LED thread has been stopped.");
            return;
        }
    }
}

void Core::cycle_led_wrapper(std::shared_ptr<LEDPattern> p){
    this->cycle_led(std::bind(&LEDPattern::cycle_led,p.get(),&this->_percept));
}

void Core::cycle_sound(std::function<SoundCmd(const Percept& p)> callback_sound){

    while(true){
        SoundCmd sound_output = callback_sound(this->_percept);
        if(sound_output.f>10){
            spdlog::warn("Setting the sound cycle frequency to more than 10 Hz may lead to undefined behavior.");
        }
        unsigned T;
        if(sound_output.f>0){
            T=1/sound_output.f*1000;
        }
        if(sound_output.f<=0){
            T=std::numeric_limits<unsigned>::max();
        }
        if(!sound_output.update || sound_output.file==""){
            continue;
        }
        std::string path=this->_config_internal.path_executable+"/../resources/audio/"+sound_output.file;
        Mix_Music* music = Mix_LoadMUS(path.c_str());

        if (music){
            if (Mix_PlayMusic(music, 1) == 0){
                while (Mix_PlayingMusic()){
                    SDL_Delay(10);
                    //                    boost::this_thread::interruption_point();
                }
            }
            else{
                std::cerr << "Mix_PlayMusic ERROR: " << Mix_GetError() << std::endl;
            }

            Mix_FreeMusic(music);
            music = 0;
        }
        else{
            std::cerr << "Mix_LoadMuS ERROR: " << Mix_GetError() << std::endl;
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(T));
        if(!this->_flag_run_sound){
            Mix_HaltMusic();
            spdlog::info("Sound thread has been stopped.");
            return;
        }
    }
}

bool Core::set_grasped_object(const std::string &o){
    if(!this->_kb.get_local_memory()->access_config_system().has_robot){
        return true;
    }
    if(!this->_kb.get_local_memory()->access_config_system().has_gripper){
        spdlog::warn("Gripper not connected.");
        return false;
    }

    Object obj;
    if(!this->_kb.load_object(o,obj)){
        spdlog::error("Cannot find object "+o+" in knowledge base.");
        return false;
    }
    if(!this->lock_robot_connection(false)){
        spdlog::error("Cannot access gripper, another process is blocking the FCI.");
        return false;
    }
    bool result=false;
    try{
        nlohmann::json p;
        p["grasped_object"]=o;
        this->_kb.get_local_memory()->modify_hidden_config_user(p);
        this->_percept.mios_state.grasped_object=o;
        this->m_panda_body->setLoad(obj.mass,msrm_utils::convert_to_array<double,3,1>(obj.EE_ob_com),msrm_utils::convert_to_array<double,3,3>(obj.ob_I));
        nlohmann::json p_frame;
        msrm_utils::write_json_array<double,4,4>(p_frame["EE_T_TCP"],obj.EE_T_O);
        result=true;
    }catch(franka::CommandException& e){
        std::cout<<e.what()<<std::endl;
        result=false;
    }catch(franka::NetworkException& e){
        std::cout<<e.what()<<std::endl;
        result=false;
    }
    if(!this->set_ee()){
        spdlog::error("Could not set end effector configuration.");
        result=false;
    }
    this->unlock_robot_connection();
    return result;
}


bool Core::grasp_object(const std::string &o, double width, double speed, double force, bool check_width){
    //    if(this->check_lockdown()){
    //        spdlog::error("Core is under lockdown.");
    //        return false;
    //    }
    if(!this->_kb.get_local_memory()->access_config_system().has_robot){
        return true;
    }
    if(!this->_kb.get_local_memory()->access_config_system().has_gripper){
        spdlog::warn("Gripper not connected.");
        return false;
    }
    if(!this->has_gripper_connection()){
        spdlog::error("Cannot grasp object. I am currently not connection to the gripper.");
        return false;
    }
    Object obj;
    if(!this->_kb.load_object(o,obj)){
        spdlog::error("Cannot find object "+o+" in knowledge base.");
        return false;
    }
    if(!this->lock_robot_connection(false)){
        spdlog::error("Cannot access gripper, another process is blocking the FCI.");
        return false;
    }
    bool result=false;
    try{
        double max_width=this->m_panda_hand->readOnce().max_width;
        double current_width=this->m_panda_hand->readOnce().width;
        if(width==-1){
            width=0;
        }else{
            if(width<0 || width>max_width){
                spdlog::error("Gripper cannot reach width of "+std::to_string(width)+". Must be between 0 and "+std::to_string(max_width)+".");
                this->unlock_robot_connection();
                return false;
            }
            if(width>current_width){
                spdlog::error("Grasping to a width larger than the current width is invalid.");
                this->unlock_robot_connection();
                return false;
            }
        }
        if(!this->m_panda_hand->readOnce().is_grasped){
            result=this->m_panda_hand->grasp(width,speed,force,1,1);
        }else{
            result=true;
        }
        franka::GripperState gripper_state=this->m_panda_hand->readOnce();
        if(check_width && (gripper_state.width<obj.grasp_width-0.005 || gripper_state.width>obj.grasp_width+0.005)){
            spdlog::error("Dimensions of object "+o+" not within expected limits. Expected: " + std::to_string(obj.grasp_width) + ", but measured: " + std::to_string(gripper_state.width));
            this->m_panda_hand->move(current_width,1);
            this->unlock_robot_connection();
            return false;
        }
        nlohmann::json p;
        p["grasped_object"]=o;
        this->_kb.get_local_memory()->modify_hidden_config_user(p);
        this->_percept.mios_state.grasped_object=o;
        this->m_panda_body->setLoad(obj.mass,msrm_utils::convert_to_array<double,3,1>(obj.EE_ob_com),msrm_utils::convert_to_array<double,3,3>(obj.ob_I));
        nlohmann::json p_frame;
        msrm_utils::write_json_array<double,4,4>(p_frame["EE_T_TCP"],obj.EE_T_O);
    }catch(franka::CommandException& e){
        std::cout<<e.what()<<std::endl;
        result=false;
    }catch(franka::NetworkException& e){
        std::cout<<e.what()<<std::endl;
        result=false;
    }catch(franka::InvalidOperationException& e){
        std::cout<<e.what()<<std::endl;
        result=false;
    }
    if(!this->set_ee()){
        spdlog::error("Could not grasp. Error while setting end effector configuration.");
        result=false;
    }
    this->unlock_robot_connection();
    return result;
}

bool Core::home_gripper(){
    //    if(this->check_lockdown()){
    //        spdlog::error("Core is under lockdown.");
    //        return false;
    //    }
    if(!this->_kb.get_local_memory()->access_config_system().has_robot){
        return true;
    }
    if(!this->_kb.get_local_memory()->access_config_system().has_gripper){
        spdlog::warn("Gripper not connected.");
        return false;
    }
    if(!this->has_gripper_connection()){
        spdlog::error("Cannot home gripper. I am currently not connected to the gripper.");
        return false;
    }
    if(!this->lock_robot_connection(false)) return false;
    bool result=false;
    try{
        if(this->m_panda_hand->readOnce().is_grasped){
            spdlog::error("Cannot home the gripper while grasping.");
            result=false;
        }else{
            result=this->m_panda_hand->homing();
        }
    }catch(franka::CommandException& e){
        std::cout<<e.what()<<std::endl;
        result=false;
    }catch(franka::NetworkException& e){
        std::cout<<e.what()<<std::endl;
        result=false;
    }catch(franka::InvalidOperationException& e){
        std::cout<<e.what()<<std::endl;
        result=false;
    }
    this->unlock_robot_connection();
    return result;
}

bool Core::grasp(double width, double speed, double force){
    //    if(this->check_lockdown()){
    //        spdlog::error("Core is under lockdown.");
    //        return false;
    //    }
    if(!this->_kb.get_local_memory()->access_config_system().has_gripper){
        spdlog::warn("Gripper not connected.");
        return false;
    }
    if(!this->has_gripper_connection()){
        spdlog::error("Cannot move gripper. I am currently not connected to the gripper.");
        return false;
    }
    bool result=false;
    try{
        result=this->m_panda_hand->grasp(width,speed,force,1,1);
    }catch(franka::CommandException& e){
        std::cout<<e.what()<<std::endl;
        return false;
    }catch(franka::NetworkException& e){
        std::cout<<e.what()<<std::endl;
        return false;
    }
    return result;
}

bool Core::move_gripper(double width, double speed){
    //    if(this->check_lockdown()){
    //        spdlog::error("Core is under lockdown.");
    //        return false;
    //    }
    if(!this->_kb.get_local_memory()->access_config_system().has_gripper){
        spdlog::warn("Gripper not connected.");
        return false;
    }
    if(!this->has_gripper_connection()){
        spdlog::error("Cannot move gripper. I am currently not connected to the gripper.");
        return false;
    }
    bool result=false;
    try{
        result=this->m_panda_hand->move(width,speed);
    }catch(franka::CommandException& e){
        std::cout<<e.what()<<std::endl;
        return false;
    }catch(franka::NetworkException& e){
        std::cout<<e.what()<<std::endl;
        return false;
    }
    return result;
}

bool Core::release_object(double width, double speed){
    //    if(this->check_lockdown()){
    //        spdlog::error("Core is under lockdown.");
    //        return false;
    //    }
    if(!this->_kb.get_local_memory()->access_config_system().has_robot){
        return true;
    }
    if(!this->_kb.get_local_memory()->access_config_system().has_gripper){
        spdlog::warn("Gripper not connected.");
        return false;
    }
    if(!this->has_gripper_connection()){
        spdlog::error("Cannot release object. I am currently not connected to the gripper.");
        return false;
    }
    if(!this->lock_robot_connection(false)) return false;
    bool result=false;
    try{
        double max_width=this->m_panda_hand->readOnce().max_width;
        if(width==-1){
            width=max_width;
        }else{
            if(width<0 || width>max_width){
                spdlog::error("Gripper cannot reach width of "+std::to_string(width)+". Must be between 0 and "+std::to_string(max_width)+".");
                this->unlock_robot_connection();
                return false;
            }
        }
        result=this->m_panda_hand->move(width,speed);
        nlohmann::json p;
        p["grasped_object"]="none";
        this->_percept.mios_state.grasped_object="none";
        this->_kb.get_local_memory()->modify_hidden_config_user(p);
        this->m_panda_body->setLoad(0,{0,0,0},{0,0,0,0,0,0,0,0,0});
    }catch(franka::CommandException& e){
        std::cout<<e.what()<<std::endl;
        result=false;
    }catch(franka::NetworkException& e){
        std::cout<<e.what()<<std::endl;
        result=false;
    }
    Eigen::Matrix<double,4,4> EE_T_TCP;
    EE_T_TCP<<1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1;
    nlohmann::json p;
    msrm_utils::write_json_array<double,4,4>(p["EE_T_TCP"],EE_T_TCP);
    this->get_kb()->get_local_memory()->get_persistent_data()->EE_T_TCP=EE_T_TCP;
    if(!this->set_ee()){
        result=false;
    }
    this->unlock_robot_connection();
    return result;
}

void Core::gripper_grasp(double width, double speed, double force, double epsilon_inner, double epsilon_outer){
    if(!this->_flag_gripper_connected){
        spdlog::error("Gripper not connected.");
        return;
    }
    try{
        this->m_panda_hand->grasp(width,speed,force,epsilon_inner,epsilon_outer);
    }catch(franka::CommandException& e){
        std::cout<<e.what()<<std::endl;
    }catch(franka::NetworkException& e){
        std::cout<<e.what()<<std::endl;
    }
    this->_flag_gripper_busy=false;
}

void Core::gripper_move(double width, double speed){
    if(!this->_flag_gripper_connected){
        spdlog::error("Gripper not connected.");
        return;
    }
    try{
        this->m_panda_hand->move(width,speed);
    }catch(franka::CommandException& e){
        std::cout<<e.what()<<std::endl;
    }catch(franka::NetworkException& e){
        std::cout<<e.what()<<std::endl;
    }
    this->_flag_gripper_busy=false;
}

void Core::gripper_homing(){
    if(!this->_flag_gripper_connected){
        spdlog::error("Gripper not connected.");
        return;
    }
    try{
        this->m_panda_hand->homing();
    }catch(franka::CommandException& e){
        std::cout<<e.what()<<std::endl;
    }catch(franka::NetworkException& e){
        std::cout<<e.what()<<std::endl;
    }
    this->_flag_gripper_busy=false;
}

bool Core::is_grasping() const{
    if(!this->_flag_gripper_connected){
        spdlog::error("Gripper not connected.");
        return false;
    }
    try{
        return this->m_panda_hand->readOnce().is_grasped;
    }catch(franka::CommandException& e){
        std::cout<<e.what()<<std::endl;
        return false;
    }catch(franka::NetworkException& e){
        std::cout<<e.what()<<std::endl;
        return false;
    }catch(franka::InvalidOperationException& e){
        std::cout<<e.what()<<std::endl;
        return false;
    }
    return true;
}

void Core::gripper_stop(){
    if(!this->_flag_gripper_connected){
        spdlog::error("Gripper not connected.");
        return;
    }
    try{
        this->m_panda_hand->stop();
    }catch(franka::CommandException& e){
        std::cout<<e.what()<<std::endl;
    }catch(franka::NetworkException& e){
        std::cout<<e.what()<<std::endl;
    }
    this->_flag_gripper_busy=false;
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

const Percept& Core::get_percept() const{
    return m_percept;
}

void Core::check_cartesian_velocity_workspace(Eigen::Matrix<double, 6, 1> &TF_dX_d, const Percept& p){
    Eigen::Matrix<double,6,1> VC_dX_d = msrm_utils::rotate_vector(TF_dX_d,msrm_utils::invert_transformation_matrix(this->get_kb()->get_local_memory()->access_config_frames().O_T_VC));
    Eigen::Matrix<double,3,1> VC_x = msrm_utils::invert_transformation_matrix(this->get_kb()->get_local_memory()->access_config_frames().O_T_VC).block<3,3>(0,0)*p.TF_T_EE.block<3,1>(0,3);
    bool stop=false;
    this->event["wall_hit_O"]={false,false,false,false,false,false};
    double wall_distance=0.01;
    Eigen::Matrix<double,3,1> wall_hit_O_lower, wall_hit_O_upper, wall_hit_EE_lower, wall_hit_EE_upper;
    for(unsigned i=0;i<3;i++){
        double diff_lower = VC_x(i)-this->get_kb()->get_local_memory()->access_config_user().x_limits(2*i);
        double wall_level_lower=1-diff_lower/wall_distance;
        if(wall_level_lower>1)wall_level_lower=1;
        if(wall_level_lower<0)wall_level_lower=0;
        this->event["wall_hit_O"][2*i]=wall_level_lower;
        wall_hit_O_lower(i)=wall_level_lower;
        if(VC_x(i)<=this->get_kb()->get_local_memory()->access_config_user().x_limits(2*i) && VC_dX_d(i)<0){
            VC_dX_d(i)=0;
        }
        double diff_upper = this->get_kb()->get_local_memory()->access_config_user().x_limits(2*i+1)-VC_x(i);
        double wall_level_upper=1-diff_upper/wall_distance;
        if(wall_level_upper>1)wall_level_upper=1;
        if(wall_level_upper<0)wall_level_upper=0;
        this->event["wall_hit_O"][2*i+1]=wall_level_upper;
        if(VC_x(i)>=this->get_kb()->get_local_memory()->access_config_user().x_limits(2*i+1) && VC_dX_d(i)>0){
            VC_dX_d(i)=0;
        }
        wall_hit_O_upper(i)=wall_level_upper;
    }
    wall_hit_EE_lower=p.TF_T_EE.block<3,3>(0,0).transpose()*wall_hit_O_lower;
    wall_hit_EE_upper=p.TF_T_EE.block<3,3>(0,0).transpose()*wall_hit_O_upper;
    Eigen::Matrix<double,6,1> wall_hit_EE;
    wall_hit_EE<<wall_hit_EE_lower(0),wall_hit_EE_upper(0),wall_hit_EE_lower(1),wall_hit_EE_upper(1),wall_hit_EE_lower(2),wall_hit_EE_upper(2);
    for(unsigned i=0;i<6;i++){
        if(wall_hit_EE(i)>1)wall_hit_EE(i)=1;
        if(wall_hit_EE(i)<0)wall_hit_EE(i)=0;
    }
    msrm_utils::write_json_array<double,6,1>(this->event["wall_hit_EE"],wall_hit_EE);
    TF_dX_d=msrm_utils::rotate_vector(VC_dX_d,this->get_kb()->get_local_memory()->access_config_frames().O_T_VC);
}


void Core::base_avoidance(Eigen::Matrix<double, 6, 1> &TF_dX_d, const Percept &p){
    Eigen::Vector3d cp1,cp2,p_ee;
    cp1<<0,0,0;
    cp2<<0,0,0.5;
    p_ee<<p.O_T_EE(0,3),p.O_T_EE(1,3),p.O_T_EE(2,3);
    msrm_utils::Cylinder base_cylinder(this->get_kb()->get_local_memory()->access_config_user().base_cylinder_p1,
                                       this->get_kb()->get_local_memory()->access_config_user().base_cylinder_p2,
                                       this->get_kb()->get_local_memory()->access_config_user().base_cylinder_radius);
    if(base_cylinder.contains(p_ee)){
        Eigen::Matrix<double,3,3> O_R_Cyl = base_cylinder.get_frame(p_ee);
        Eigen::Matrix<double,6,1> Cyl_dX_d = msrm_utils::rotate_vector(TF_dX_d,msrm_utils::invert_matrix(O_R_Cyl));
        if(Cyl_dX_d(0)<0){
            Cyl_dX_d(0)=0.01;
        }
        TF_dX_d=msrm_utils::rotate_vector(Cyl_dX_d,O_R_Cyl);
    }
}

void Core::dummy_control(std::function<franka::Torques (const franka::RobotState &)> control_cycle){
    franka::Torques tau_J={0,0,0,0,0,0,0};
    franka::RobotState state;
    state.K_F_ext_hat_K={0,0,0,0,0,0};
    state.O_F_ext_hat_K={0,0,0,0,0,0};
    state.tau_ext_hat_filtered={0,0,0,0,0,0,0};
    state.q={0,0,0,0,0,0,0};
    state.dq={0,0,0,0,0,0,0};
    while(!tau_J.motion_finished){
        auto t_s_start = std::chrono::system_clock::now();
        tau_J=control_cycle(state);
        auto t_s_end = std::chrono::system_clock::now();
        double t=std::chrono::duration_cast<std::chrono::microseconds>(t_s_end-t_s_start).count();
        std::this_thread::sleep_for(std::chrono::microseconds(1000-static_cast<int>(t)));
    }
}

void Core::dummy_control(std::function<franka::CartesianVelocities (const franka::RobotState &)> control_cycle){
    franka::CartesianVelocities dX_d={0,0,0,0,0,0};
    franka::RobotState state;
    while(!dX_d.motion_finished){
        auto t_s_start = std::chrono::system_clock::now();
        dX_d=control_cycle(state);
        auto t_s_end = std::chrono::system_clock::now();
        double t=std::chrono::duration_cast<std::chrono::microseconds>(t_s_end-t_s_start).count();
        std::this_thread::sleep_for(std::chrono::microseconds(1000-static_cast<int>(t)));
    }
}

void Core::dummy_control(std::function<franka::JointVelocities (const franka::RobotState &)> control_cycle){
    franka::JointVelocities dq_d={0,0,0,0,0,0,0};
    franka::RobotState state;
    while(!dq_d.motion_finished){
        auto t_s_start = std::chrono::system_clock::now();
        dq_d=control_cycle(state);
        auto t_s_end = std::chrono::system_clock::now();
        double t=std::chrono::duration_cast<std::chrono::microseconds>(t_s_end-t_s_start).count();
        std::this_thread::sleep_for(std::chrono::microseconds(1000-static_cast<int>(t)));
    }
}

std::tuple<std::string,std::string,std::string> Core::get_desk_data(){
    return std::tie(this->_kb.get_local_memory()->access_config_system().ip_robot,
                    this->_kb.get_local_memory()->access_config_system().desk_name,
                    this->_kb.get_local_memory()->access_config_system().desk_pwd);
}

void Core::start_desk_task(const std::string &task){
    if(this->check_lockdown()){
        spdlog::error("Core is under lockdown.");
        return;
    }
    if(!this->disconnect_from_gripper()){
        return;
    }
    if(!this->disconnect_from_robot()){
        return;
    }
    auto desk_data=this->get_desk_data();
    nlohmann::json response;
    nlohmann::json request={
        {"ip",std::get<0>(desk_data)},
        {"name",std::get<1>(desk_data)},
        {"password",std::get<2>(desk_data)},
        {"task",task}
    };
    msrm_utils::JsonRPCClient::call_method("localhost",9001,"start_task",request,response);
    if(!this->wait_for_desk_task()){
        // stop signal
    }
    if(!this->connect_to_robot()){
        return;
    }
    if(!this->connect_to_gripper()){
        return;
    }
}

void Core::stop_desk_task(){
    auto desk_data=this->get_desk_data();
    nlohmann::json response;
    nlohmann::json request={
        {"ip",std::get<0>(desk_data)},
        {"name",std::get<1>(desk_data)},
        {"password",std::get<2>(desk_data)}
    };
    if(!msrm_utils::JsonRPCClient::call_method("localhost",9001,"stop_task",request,response)){
        // stop signal
    }
}

bool Core::wait_for_desk_task(){
    nlohmann::json response,request;
    while(true){
        if(!msrm_utils::JsonRPCClient::call_method("localhost",9001,"start_task",request,response)){
            spdlog::error("Connection to desk server faulty, undefined behavior possible.");
            return false;
        }
        bool finished;
        msrm_utils::read_json_param(response,"finished",finished);
        if(finished){
            break;
        }else{
            usleep(10000);
        }
    }
    return true;
}

bool Core::shutdown_robot(){
    if(this->check_lockdown()){
        spdlog::error("Core is under lockdown.");
        return false;
    }
    if(!this->lock_robot_connection()){
        spdlog::error("Robot is busy, cannot shut down.");
        return false;
    }
    this->terminate();
    auto desk_data=this->get_desk_data();
    nlohmann::json response;
    nlohmann::json request={
        {"ip",std::get<0>(desk_data)},
        {"name",std::get<1>(desk_data)},
        {"password",std::get<2>(desk_data)}
    };
    if(!msrm_utils::JsonRPCClient::call_method("localhost",9001,"shutdown",request,response)){
        spdlog::error("Cannot reach local desk server.");
        return false;
    }
    this->unlock_robot_connection();
    return true;
}

bool Core::unlock_brakes(){
    if(this->check_lockdown()){
        spdlog::error("Core is under lockdown.");
        return false;
    }
    if(!this->lock_robot_connection()){
        spdlog::error("Robot is busy, cannot unlock brakes.");
        return false;
    }
    //    this->terminate();
    auto desk_data=this->get_desk_data();
    nlohmann::json response;

    nlohmann::json request={
        {"ip",std::get<0>(desk_data)},
        {"name",std::get<1>(desk_data)},
        {"password",std::get<2>(desk_data)}
    };
    msrm_utils::JsonRPCClient::call_method("localhost",9001,"unlock_brakes",request,response);
    //    if(!this->initialize()){
    //        return false;
    //    }
    this->unlock_robot_connection();
    return true;
}

bool Core::lock_brakes(){
    if(this->check_lockdown()){
        spdlog::error("Core is under lockdown.");
        return false;
    }
    if(!this->lock_robot_connection()){
        spdlog::error("Robot is busy, can not lock brakes.");
        return false;
    }
    //    this->terminate();
    auto desk_data=this->get_desk_data();
    nlohmann::json response;
    nlohmann::json request={
        {"ip",std::get<0>(desk_data)},
        {"name",std::get<1>(desk_data)},
        {"password",std::get<2>(desk_data)}
    };
    msrm_utils::JsonRPCClient::call_method("localhost",9001,"lock_brakes",request,response);
    //    if(!this->initialize()){
    //        return false;
    //    }
    this->unlock_robot_connection();
    return true;
}

bool Core::move_to_pack_pose(){
    if(this->check_lockdown()){
        spdlog::error("Core is under lockdown.");
        return false;
    }
    if(!this->lock_robot_connection()){
        spdlog::error("Robot is busy, can not move to pack pose.");
        return false;
    }
    this->terminate();
    auto desk_data=this->get_desk_data();
    nlohmann::json response;
    nlohmann::json request={
        {"ip",std::get<0>(desk_data)},
        {"name",std::get<1>(desk_data)},
        {"password",std::get<2>(desk_data)}
    };
    msrm_utils::JsonRPCClient::call_method("localhost",9001,"pack_pose",request,response);
    if(!this->initialize()){
        return false;
    }
    this->unlock_robot_connection();
    return true;
}

std::string Core::find_robot() const{
    std::string robot_address="none";
    std::string robot_iface="none";

    std::map<std::string,std::string> ifaces = msrm_utils::get_subnets();
    for(const auto& i : ifaces){
        if(i.first=="lo" || i.first=="docker0" || i.first=="tap0"){
            continue;
        }
        for(unsigned j=1;j<255;j++){
            std::string address=i.second+std::to_string(j);
            if(!msrm_utils::ping(address.c_str())){
                continue;
            }else{
                if(this->test_robot_connection(address)){
                    robot_address=address;
                    break;
                }
            }
        }
        if(robot_address!="none"){
            robot_iface=i.first;
            break;
        }
    }

    if(robot_address=="none"){
        spdlog::error("No connected robot found. Make sure that master controller and this computer share the same network and that the connection is properly configured.");
    }else{
        spdlog::info("Found robot at ip "+robot_address+" at interface "+robot_iface+".");
    }
    return robot_address;
}

bool Core::test_robot_connection(const std::string &ip) const{
    try{
        std::unique_ptr<franka::Robot> robot =  std::make_unique<franka::Robot>(ip);
        return true;
    }catch(const franka::NetworkException& e){
        spdlog::info("Skipping device with ip "+ip+".");
        return false;
    }catch(const franka::IncompatibleVersionException& e){
        spdlog::error("At device with ip "+ip+": ");
        std::cout<<e.what()<<std::endl;
        spdlog::warn("This robot possibly needs an update.");
        return false;
    }
}

std::string Core::find_primary(){
    std::string ip="none";
    //    std::vector<std::string> ifaces = msrm_utils::get_ifaces();
    //    for(unsigned i=0;i<ifaces.size();i++){
    //        std::string ip_subnet = ifaces[i];
    //        std::vector<std::string> ip_tmp = msrm_utils::split_string(ip_subnet,".");
    //        ip_subnet=ip_tmp[0]+"."+ip_tmp[1]+"."+ip_tmp[2]+".";
    //        for(unsigned i=1;i<254;i++){
    //            std::string address = ip_subnet+std::to_string(i);
    //            if(msrm_utils::ping(address.c_str())==1){
    //                continue;
    //            }else{
    //                if(this->test_primary_connection(address)){
    //                    ip=address;
    //                }
    //            }
    //        }

    //    }
    //    if(ip=="none"){
    //        spdlog::error("No primary has been found in this network.");
    //    }else{
    //        spdlog::info("Found primary, I am connected to a collective.");
    //    }
    return ip;
}

bool Core::test_primary_connection(const std::string &ip){
    nlohmann::json request=nlohmann::json();
    nlohmann::json response;
    return false;
    //    return msrm_utils::rpc_call(ip,8390,"is_primary",request,response);
}

bool Core::init_sound(){
    if(!this->_kb.get_local_memory()->access_config_system().has_sound){
        return true;
    }
    if (SDL_Init(SDL_INIT_AUDIO) != 0){
        std::cerr << "SDL_Init ERROR: " << SDL_GetError() << std::endl;
        return false;
    }
    if (Mix_OpenAudio(44100, AUDIO_S16SYS, 2, 2048) != 0){
        std::cerr << "Mix_OpenAudio ERROR: " << Mix_GetError() << std::endl;
        return false;
    }
    Mix_VolumeMusic(100);

    spdlog::info("Sound output initialized.");
    return true;
}

bool Core::init_led(){
    if(!this->_kb.get_local_memory()->access_config_system().has_led){
        return true;
    }
    nlohmann::json response, request;
    if(!msrm_utils::JsonRPCClient::call_method("localhost",9000,"get_panel_id",request,response)){
        spdlog::warn("Could not connect to LED server.");
        return false;
    }
    std::array<std::string,5> panels={"far-right","right","middle","left","far-left"};

    bool valid;
    if(!msrm_utils::read_json_param(response,"valid",valid)){
        spdlog::error("No valid response from LED server.");
        return false;
    }
    if(!valid){
        spdlog::error("Invalid LED configuration.");
        return false;
    }
    if(response.find("id")!=response.end()){
        if(response["id"].is_array()){
            if(panels.size()!=response["id"].size()){
                spdlog::error("Expected number of LED panels is 5 but found "+std::to_string(response["id"].size())+".");
                return false;
            }
        }
    }else{
        spdlog::error("No valid response from LED server.");
        return false;
    }
    for(unsigned i=0;i<response["id"].size();i++){
        unsigned panel_id;
        if(response.find("id")==response.end()){
            spdlog::error("Response from LED server is faulty.");
            return false;
        }
        response["id"][i][0].get_to(panel_id);
        this->_led_panel_id.insert(std::pair<std::string,unsigned>(panels[i],panel_id));
    }
    spdlog::info("LED output initialized.");
    return true;
}

void Core::load_led_pattern(std::shared_ptr<LEDPattern> pattern){
    this->unload_led_pattern();
    if(this->_kb.get_local_memory()->access_config_system().has_led){
        pattern.get()->init_pattern(this->_percept);
        this->_flag_run_led=true;
        this->_thr_led=std::thread(&Core::cycle_led_wrapper,this,pattern);
        this->_thr_led.detach();
    }
}

void Core::unload_led_pattern(){
    if(this->_thr_led.joinable()){
        this->_flag_run_led=false;
    }
}

bool Core::terminate_sound(){
    if(!this->_kb.get_local_memory()->access_config_system().has_sound){
        return true;
    }
    Mix_CloseAudio();
    return true;
}

bool Core::terminate_led(){
    return true;
}

void Core::start_telemetry(){
    if(!this->_kb.get_local_memory()->access_config_system().telemetry_on){
        return;
    }
    ConfigTelemetryUDP config_telemetry;
    config_telemetry.ip_dst=this->_kb.get_local_memory()->access_config_system().telemetry_udp_ip;
    config_telemetry.port_dst=this->_kb.get_local_memory()->access_config_system().telemetry_udp_port;
    config_telemetry.frequency=this->_kb.get_local_memory()->access_config_system().telemetry_udp_frequency;
    if(!this->_telemetry_udp.initialize(config_telemetry)){
        spdlog::error("Could not initialize telemetry.");
        nlohmann::json p;
        p["telemetry_on"]=false;
        this->_kb.get_local_memory()->modify_config_system(p);
    }else{
        this->_flag_logged_in_digital_twin=true;
    }
}

void Core::terminate_telemetry(){
    this->_telemetry_udp.terminate();
}

void Core::login_digital_twin(){
    nlohmann::json response;
    std::string name=this->get_kb()->get_local_memory()->access_config_system().id_robot;
    std::string location=this->get_kb()->get_local_memory()->access_config_system().location;
    std::string ip=this->get_kb()->get_local_memory()->access_config_system().telemetry_udp_ip;
    nlohmann::json request={
        {"name",name},
        {"location",location}
    };
    msrm_utils::JsonRPCClient::call_method(ip,4000,"login",request,response);
    int port;
    msrm_utils::read_json_param(response,"port",port);
    spdlog::info("I am logging into the digital twin with IP "+ip+" and port "+std::to_string(port)+".");
    nlohmann::json params;
    params["telemetry_on"]=true;
    if(port==-1){
        spdlog::warn("I am already logged into the digital twin.");
    }else{
        params["telemetry_udp_port"]=port;
        this->_kb.set_parameter("telemetry_udp_port","system",port);
    }
    this->get_kb()->get_local_memory()->modify_config_system(params);

}

void Core::logout_digital_twin(){
    nlohmann::json params;
    params["telemetry_on"]=false;
    this->get_kb()->get_local_memory()->modify_config_system(params);
    nlohmann::json response;
    std::string name=this->get_kb()->get_local_memory()->access_config_system().id_robot;
    std::string ip=this->get_kb()->get_local_memory()->access_config_system().telemetry_udp_ip;
    nlohmann::json request={
        {"name",name}
    };
    msrm_utils::JsonRPCClient::call_method(ip,4000,"logout",request,response);
    if(this->_flag_logged_in_digital_twin){
        this->terminate_telemetry();
        this->_flag_logged_in_digital_twin=false;
    }
}

bool Core::listen_to_beacons(){
    std::vector<int> s;
    std::vector<struct sockaddr_in> broadcastAddr;
    std::vector<unsigned> ports;

    ports={50001,50002};
    s.resize(ports.size());
    broadcastAddr.resize(ports.size());


    for(unsigned i=0;i<ports.size();i++){
        if ((s[i] = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)) < 0){
            spdlog::error("Could not create socket for listener thread.");
            return false;
        }
        struct timeval tv;
        tv.tv_sec = 0;
        tv.tv_usec = 100000;
        if(setsockopt(s[i], SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv))<0){
            spdlog::error("Could not set options for socket in listener thread.");
            return false;
        }
        int optval=1;
        if(setsockopt(s[i], SOL_SOCKET, SO_REUSEPORT, &optval, sizeof(optval))<0){
            spdlog::error("Could not set options for socket in listener thread.");
            return false;
        }

        memset(&broadcastAddr[i], 0, sizeof(broadcastAddr[i]));
        broadcastAddr[i].sin_family = AF_INET;
        broadcastAddr[i].sin_addr.s_addr = htonl(INADDR_ANY);
        broadcastAddr[i].sin_port = htons(ports[i]);

        if (bind(s[i], (struct sockaddr *) &broadcastAddr[i], sizeof(broadcastAddr[i])) < 0){
            spdlog::error("Binding of socket in listener thread failed.");
            return false;
        }
    }
    while(true){
        std::this_thread::sleep_for(std::chrono::seconds(1));
        for(unsigned i=0;i<s.size();i++){
            char recvString[255];
            int recvStringLen;
            recvStringLen = recvfrom(s[i], recvString, 255, 0, NULL, 0);
            if(recvStringLen<0){
            }else{
                std::string buffer(recvString);
                std::string msg_str=std::string(buffer.begin(),buffer.begin()+recvStringLen);
                nlohmann::json msg;
                try{
                    msg=nlohmann::json::parse(msg_str);
                }catch(const nlohmann::detail::parse_error& e){
                    spdlog::debug(e.what());
                    continue;
                }
                if(msg["designation"]=="digital_twin"){
                    nlohmann::json p;
                    p["telemetry_udp_ip"]=msg["ip"];
                    this->get_kb()->get_local_memory()->modify_config_system(p);
                    std::string ip;
                    msrm_utils::read_json_param(msg,"ip",ip);
                    this->get_kb()->set_parameter("telemetry_udp_ip","system",ip);
                }
            }
        }
    }
    if(!this->_flag_run_beacon){
        for(unsigned i=0;i<s.size();i++){
            close(s[i]);
        }
        return true;
    }

    return true;
}

}

