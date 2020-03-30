#include "core/core.hpp"

#include "cpp_utils/math.hpp"
#include "cpp_utils/files.hpp"
#include "cpp_utils/network.hpp"
#include "cpp_utils/conversion.hpp"
#include "cpp_utils/json.hpp"
#include "cpp_utils/system.hpp"
#include "utils/exceptions.hpp"
#include "skill/skill.hpp"

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

Core::Core(int argc, char **argv){

    this->_robot=nullptr;
    this->_model=nullptr;
    this->_gripper=nullptr;
    this->_kb=nullptr;

    this->_sim_interface=nullptr;

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

    this->_config_internal.path_executable=cpp_utils::get_path_executable(argv);
    this->_config_internal.grasped_object="none";

    this->_active_skill=nullptr;

    spdlog::info("Initializing knowledgebase...");
    this->_kb = std::make_shared<KnowledgeBase>();
    if(!this->_kb->initialize(this->_config_internal)){
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

bool Core::initialize(bool silent){

    if(!this->_kb->load_parameters()){
        spdlog::error("Could not load all parameters. Robot is not operational.");
        return false;
    }
    this->_flag_run_beacon=true;
    this->_thr_beacons = std::thread(&Core::listen_to_beacons,this);
    this->_thr_beacons.detach();
    this->start_sim_interface();
    this->init_sound();
    if(!this->init_led()){
        nlohmann::json p;
        p["has_led"]=false;
        this->get_kb()->get_local_memory()->modify_config_system(p);
    }
    if(!this->_kb->get_local_memory()->access_config_system().has_robot){

    }else if(!this->connect_to_robot()){
        return false;
    }
    if(!this->_kb->get_local_memory()->access_config_system().has_gripper){

    }else if(!this->connect_to_gripper()){
        return false;
    }
    if(!this->set_ee()){
        return false;
    }
    return true;
}

bool Core::terminate(){
    this->terminate_sound();
    this->terminate_led();
    this->terminate_sim_interface();
    if(this->_thr_beacons.joinable()){
        this->_flag_run_beacon=false;
    }
    //    this->terminate_telemetry();
    if(!this->_kb->get_local_memory()->access_config_system().has_gripper){

    }else if(!this->disconnect_from_gripper()){
        return false;
    }
    if(!this->_kb->get_local_memory()->access_config_system().has_robot){

    }else if(!this->disconnect_from_robot()){
        return false;
    }
    this->_kb->terminate();
    return true;
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

bool Core::recover(){
    if(this->_kb->get_local_memory()->access_config_system().has_robot){
        if(this->_robot==nullptr){
            spdlog::error("Robot is not connected, attempting to reinitialize.");
            if(!this->terminate()){
                spdlog::error("Re-initialization has failed.");
                return false;
            }
            if(!this->initialize()){
                spdlog::error("Re-initialization has failed.");
                return false;
            }
        }
    }else{
        return true;
    }
    try{
        this->_robot->automaticErrorRecovery();
    }catch(const franka::NetworkException& e){
        std::cout<<e.what()<<std::endl;
        return false;
    }catch(const franka::CommandException& e){
        std::cout<<e.what()<<std::endl;
        return false;
    }
    return true;
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
    if(this->_robot==nullptr){
        return false;
    }else{
        return true;
    }
}

bool Core::has_gripper_connection() const{
    if(this->_gripper==nullptr){
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
    if(!this->_kb->load_parameters()){
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
    if(!this->_kb->get_local_memory()->access_config_system().has_robot){
        return true;
    }
    if(this->_robot==nullptr){
        spdlog::error("Cannot set global config, no robot connected, CHECK THIS ERROR!");
        return false;
    }
    const ConfigUser& c_user=this->_kb->get_local_memory()->access_config_user();
    const ConfigFrames& c_frames=this->_kb->get_local_memory()->access_config_frames();
    const ConfigLimits& c_limits=this->_kb->get_local_memory()->access_config_limits();
    Object o;
    try{
        if(this->_kb->load_object(this->_kb->get_local_memory()->access_config_user().grasped_object,o) || this->_kb->get_local_memory()->access_config_user().grasped_object=="none"){
            this->_robot->setLoad(o.mass,cpp_utils::convert_to_array<double,3,1>(o.EE_ob_com),cpp_utils::convert_to_array<double,3,3>(o.ob_I));
        }else{
            this->_robot->setLoad(c_user.load_m,cpp_utils::convert_to_array<double,3,1>(c_user.load_com),cpp_utils::convert_to_array<double,3,3>(c_user.load_I));
        }
        if(!this->set_ee()){
            return false;
        }
        this->_robot->setCollisionBehavior(cpp_utils::convert_to_array<double,7,1>(c_user.tau_contact),
                                           cpp_utils::convert_to_array<double,7,1>(c_limits.tau_ext_max),
                                           cpp_utils::convert_to_array<double,6,1>(c_user.F_contact),
        {c_limits.F_ext_max(0),c_limits.F_ext_max(0),c_limits.F_ext_max(0),c_limits.F_ext_max(1),c_limits.F_ext_max(1),c_limits.F_ext_max(1)});
        this->_robot->setK(cpp_utils::convert_to_array<double,4,4>(c_frames.EE_T_K));

        this->_robot->setJointImpedance({9000,9000,9000,7500,7500,6000,6000});
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
    if(!this->_kb->get_local_memory()->access_config_system().has_robot){
        return true;
    }
    if(this->_robot==nullptr){
        spdlog::error("Can not set EE, no connection to robot.");
        return false;
    }
    Object obj;
    if(!this->_kb->load_object(this->_percept.mios_state.grasped_object,obj)){
        return false;
    }
    nlohmann::json p_frame;
    cpp_utils::write_json_array<double,4,4>(p_frame["EE_T_TCP"],obj.EE_T_O);
    //    this->_kb->get_local_memory()->modify_config_frames(p_frame);
    this->get_kb()->get_local_memory()->get_persistent_data()->EE_T_TCP=obj.EE_T_O;
    Eigen::Matrix<double,4,4> F_T_TCP=cpp_utils::rotate_matrix(this->get_kb()->get_local_memory()->get_persistent_data()->EE_T_TCP,this->_kb->get_local_memory()->access_config_frames().F_T_EE);
    try{
        this->_robot->setEE(cpp_utils::convert_to_array<double,4,4>(F_T_TCP));
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

void Core::set_live_parameter_server(std::shared_ptr<ParameterServer> server){
    this->_kb->set_live_parameter_server(server);
}

std::shared_ptr<KnowledgeBase> Core::get_kb(){
    return this->_kb;
}

bool Core::validity_check_torque(std::array<double,7>& tau_J){

    const ConfigLimits& c_limits=this->_kb->get_local_memory()->access_config_limits();
    const ConfigFrames& c_frames=this->_kb->get_local_memory()->access_config_frames();

    // check O_R_TF
    Eigen::Matrix<double,3,3> O_R_TF_check;
    O_R_TF_check=cpp_utils::rotate_matrix(c_frames.O_R_TF,c_frames.O_R_TF);
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

bool Core::validity_check_virtual_cube(){
    std::array<bool,3> in_cube={false,false,false};
    Eigen::Matrix<double,6,1> dist_walls = this->get_kb()->get_local_memory()->access_config_cntr().virt_cube_walls;
    bool safe_activation=true;
    for(unsigned i=0;i<6;i++){
        if(fabs(this->_out_y_virt_cube.wall_flag(i))>0){
            safe_activation=false;
            break;
        }
    }
    for(unsigned i=0;i<3;i++){
        if(this->_percept.O_T_EE(i,3)>dist_walls(i*2) || this->_percept.O_T_EE(i,3)<dist_walls(i*2+1)){
            in_cube[i]=false;
        }else{
            in_cube[i]=true;
        }
    }
    if(in_cube[0] && in_cube[1] && in_cube[2] && safe_activation){
        this->_flag_virt_cube_valid=true;
    }
    return this->_flag_virt_cube_valid;
}

bool Core::validity_check_virtual_walls_joint(){
    std::array<bool,7> in_walls={false,false,false,false,false,false,false};
    Eigen::Matrix<double,14,1> dist_walls = this->get_kb()->get_local_memory()->access_config_cntr().virt_walls_joint_walls;

    bool safe_activation=true;
    for(unsigned i=0;i<7;i++){
        if(fabs(this->_out_y_virt_walls_joint.wall_flag(i))>0){
            safe_activation=false;
            break;
        }
    }
    for(unsigned i=0;i<7;i++){
        if(this->_percept.q(i)>dist_walls(i*2) || this->_percept.q(i)<dist_walls(i*2+1)){
            in_walls[i]=false;
        }else{
            in_walls[i]=true;
        }
    }
    if(in_walls[0] && in_walls[1] && in_walls[2] && in_walls[3] && in_walls[4] && in_walls[5] && in_walls[6] && safe_activation){
        this->_flag_virt_walls_joint_valid=true;
    }
    return this->_flag_virt_walls_joint_valid;
}

bool Core::validity_check_velocity_cart(std::array<double, 6> &O_dP_EE_d){
    const ConfigLimits& c_limits=this->_kb->get_local_memory()->access_config_limits();
    const ConfigFrames& c_frames=this->_kb->get_local_memory()->access_config_frames();

    // check O_R_TF
    Eigen::Matrix<double,3,3> O_R_TF_check;
    O_R_TF_check=cpp_utils::rotate_matrix(c_frames.O_R_TF,c_frames.O_R_TF);
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
    const ConfigLimits& c_limits=this->_kb->get_local_memory()->access_config_limits();
    const ConfigFrames& c_frames=this->_kb->get_local_memory()->access_config_frames();


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

std::string Core::get_ip_robot(){
    const ConfigSystem& c=this->_kb->get_local_memory()->access_config_system();
    if(c.ip_robot!="none"){
        if(cpp_utils::ping(c.ip_robot.c_str())==1){
            spdlog::warn("IP was set to "+c.ip_robot+" but no device has been found. Searching for new connection...");
            nlohmann::json p;
            p["ip_robot"]="none";
            this->_kb->get_local_memory()->modify_config_system(p);
            this->_kb->set_parameter("ip_robot","system","none");
        }else{
            if(!this->test_robot_connection(c.ip_robot)){
                spdlog::warn("IP was set to "+c.ip_robot+" but no compatible robot seems to be connected. Searching for new connection...");
                nlohmann::json p;
                p["ip_robot"]="none";
                this->_kb->get_local_memory()->modify_config_system(p);
                this->_kb->set_parameter("ip_robot","system","none");
            }
        }
    }

    if(c.ip_robot=="none"){
        std::string ip=this->find_robot();
        if(ip=="none"){
            spdlog::error("No robot seems to be connected.");
        }else{
            nlohmann::json p;
            p["ip_robot"]=ip;
            this->_kb->get_local_memory()->modify_config_system(p);
            this->_kb->set_parameter("ip_robot","system",ip);
        }
    }
    return c.ip_robot;
}

std::string Core::get_ip_primary(){
    //    ConfigGlobal* c=this->_kb->get_local_memory()->get_config_global();
    //    if(c->ip_primary!="none"){
    //        if(cpp_utils::ping(c->ip_primary.c_str())==1){
    //            spdlog::warn("Last known IP of primary was "+c->ip_primary+" but I can not ping it. Searching for new connection...");
    //            c->ip_primary="none";
    //            this->_kb->set_parameter("ip_primary",c->ip_primary);
    //        }else{
    //            if(!this->test_primary_connection(c->ip_primary)){
    //                spdlog::warn("Last known IP of primary was "+c->ip_primary+" but I do not receive any response. Searching for new connection...");
    //                c->ip_primary="none";
    //                this->_kb->set_parameter("ip_primary",c->ip_primary);
    //            }
    //        }
    //    }
    //    if(c->ip_primary=="none"){
    //        std::string ip=this->find_primary();
    //        c->ip_primary=ip;
    //        this->_kb->set_parameter("ip_primary",c->ip_primary);
    //    }
    //    return c->ip_primary;
    return "void";
}

bool Core::connect_to_robot(){
    std::string ip=this->get_ip_robot();
    if(ip=="none"){
        return false;
    }
    try{
        this->_robot = std::make_unique<franka::Robot>(ip);
        this->_model = std::make_unique<franka::Model>(this->_robot->loadModel());
        this->_flag_robot_connected=true;
    }catch(const franka::NetworkException& e){
        std::cout << e.what() << std::endl;
        spdlog::error("Cannot connect to robot at IP "+ip);
        return false;
    }catch(const franka::IncompatibleVersionException& e){
        std::cout<<e.what()<<std::endl;
        spdlog::error("Cannot connect to robot at IP "+ip);
        exit(-1);
    }catch(const franka::ModelException& e){
        std::cout<<e.what()<<std::endl;
        spdlog::error("Model could not be loaded.");
        return false;
    }
    //    cpp_utils::print_success("done");
    return true;
}

bool Core::connect_to_gripper(){
    try{
        this->_gripper = std::make_unique<franka::Gripper>(this->_kb->get_local_memory()->access_config_system().ip_robot);
        this->_flag_gripper_connected=true;
    }catch(const franka::NetworkException& e){
        std::cout << e.what() << std::endl;
        spdlog::error("Can not connect to gripper");
        return false;
    }catch(const franka::IncompatibleVersionException& e){
        std::cout<<e.what()<<std::endl;
        spdlog::error("Can not connect to gripper");
        return false;
    }
    //    cpp_utils::print_success("done");
    return true;
}

bool Core::conncet_to_primary(){
    return true;
}

bool Core::disconnect_from_robot(){
    this->_model=nullptr;
    this->_robot=nullptr;
    this->_flag_robot_connected=false;
    return true;
}

bool Core::disconnect_from_gripper(){
    this->terminate_gripper();
    this->_gripper=nullptr;
    this->_flag_gripper_connected=false;
    return true;
}

MiosState* Core::get_mios_state(){
    return &this->_percept.mios_state;
}

bool Core::load_skill(std::shared_ptr<Skill> skill,bool log){
    if(this->check_lockdown()){
        spdlog::error("Core is under lockdown.");
        return false;
    }
    spdlog::info("Loading skill "+skill->get_id()+".");
    // set active skill and setup
    this->_active_skill=skill;
    this->_active_skill->reset();
    try{
        if(this->_kb->get_local_memory()->access_config_system().has_robot){
            this->lock_robot_connection();
            if(this->_kb->get_local_memory()->access_config_system().has_gripper){
                this->_gripper->readOnce();
                this->_gripper_state=this->_gripper->readOnce();
            }
            franka::RobotState state=this->_robot->readOnce();
            this->process_percept(state,this->_gripper_state);
            this->unlock_robot_connection();
        }
        this->_active_skill->write_O_R_TF(this->_percept);
        if(this->_kb->get_local_memory()->access_config_system().has_robot){
            this->lock_robot_connection();
            if(this->_kb->get_local_memory()->access_config_system().has_gripper){
                this->_gripper_state=this->_gripper->readOnce();
            }
            this->process_percept(this->_robot->readOnce(),this->_gripper_state);
            this->unlock_robot_connection();
        }
        this->_percept.K_x=this->_active_skill->get_config<>()->controller.K_0;
        this->_percept.xi_x=this->_active_skill->get_config<>()->controller.xi;
        this->_percept.K_theta=this->_active_skill->get_config<>()->controller.K_theta;
        this->_percept.xi_theta=this->_active_skill->get_config<>()->controller.xi_theta;
        spdlog::info("Initializing skill "+this->_active_skill->get_id()+"...",false);
        if(!this->_active_skill->initialize(this->_percept)){
            spdlog::info("failed.");
            return false;
        }
        spdlog::info("done.");
        this->_kb->get_local_memory()->upload_config_cntr(this->_active_skill->get_config<>()->controller);
        this->_kb->get_local_memory()->upload_config_frames(this->_active_skill->get_config<>()->frames);
        this->_kb->get_local_memory()->upload_config_general(this->_active_skill->get_config<>()->general);
        this->_kb->get_local_memory()->upload_config_user(this->_active_skill->get_config<>()->user);

        this->start_telemetry();
    }catch(const franka::InvalidOperationException& e){
        std::cout<<e.what()<<std::endl;
        this->unlock_robot_connection();
        return false;
    }catch(const franka::NetworkException& e){
        std::cout<<e.what()<<std::endl;
        this->unlock_robot_connection();
        return false;
    }
    return true;
}

void Core::unload_skill(){
    this->_active_skill=nullptr;
    this->_kb->load_parameters();
    this->_flag_stop_control=false;
    this->terminate_telemetry();
}

void Core::toggle_skill_pause(bool pause){
    if(this->_active_skill!=nullptr){
        this->_active_skill->set_pause(pause);
    }else{
        spdlog::warn("Cannot pause, no active skill.");
    }
}

void Core::gripper_cycle(){
    while(true){
        if(!this->_flag_gripper && !this->_flag_gripper_busy){
            try{
                this->_gripper_state=this->_gripper->readOnce();
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

void Core::initialize_control_aic(const Percept& p){

    cntr_aic::In_P_cntr_aic in_p_aic;
    conv_vel2pose::In_P_conv_vel2pose in_p_vel2pose;
    const ConfigController& c_cntr=this->_kb->get_local_memory()->access_config_cntr();
    const ConfigFrames& c_frames=this->_kb->get_local_memory()->access_config_frames();
    in_p_aic.alpha=c_cntr.alpha;
    in_p_aic.beta=c_cntr.beta;
    in_p_aic.gamma_a=c_cntr.gamma_a;
    in_p_aic.gamma_b=c_cntr.gamma_b;
    in_p_aic.L=c_cntr.L;
    in_p_aic.K_0=c_cntr.K_0;
    in_p_aic.F_ff_0=c_cntr.F_ff_0;
    in_p_aic.xi=c_cntr.xi;
    in_p_aic.F_ff_max=c_cntr.F_ff_max;
    in_p_aic.dF_ff_max=c_cntr.dF_ff_max;
    in_p_aic.K_max=c_cntr.K_max;
    in_p_aic.dK_max=c_cntr.dK_max;
    in_p_aic.O_R_TF=c_frames.O_R_TF;
    in_p_aic.EE_T_K=c_frames.EE_T_K;
    in_p_aic.dtau_max<<1000,1000,1000,1000,1000,1000,1000;
    in_p_aic.tau_max<<87,87,87,87,12,12,12;
    in_p_aic.TF_control<<c_cntr.TF_control;
    in_p_aic.kappa<<c_cntr.kappa;

    this->input_control_aic(p);

    this->_in_u_aic.K_x=c_cntr.K_0;
    this->_in_u_aic.xi_x=c_cntr.xi;

    this->_cntr_aic.initialize(this->_in_u_aic,in_p_aic);
    this->_conv_vel2pose.initialize(this->_in_u_vel2pose,in_p_vel2pose);

    this->_percept.K_x=c_cntr.K_0;
    this->_percept.xi_x=c_cntr.xi;

}

void Core::initialize_control_joint_imp(const Percept &p){
    cntr_joint_var_imp::In_P_cntr_joint_var_imp in_p_joint_imp;
    const ConfigController& c_cntr=this->_kb->get_local_memory()->access_config_cntr();

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

void Core::initialize_control_force(const Percept &p){
    cntr_force::In_P_cntr_force in_p_force;
    const ConfigController& c_cntr=this->_kb->get_local_memory()->access_config_cntr();
    in_p_force.active=c_cntr.f_cntr_active;
    in_p_force.dF_d_max=c_cntr.dF_c_max;
    in_p_force.F_d_max=c_cntr.F_c_max;
    in_p_force.dtau_max<<std::numeric_limits<double>::max(),std::numeric_limits<double>::max(),std::numeric_limits<double>::max(),std::numeric_limits<double>::max(),
            std::numeric_limits<double>::max(),std::numeric_limits<double>::max(),std::numeric_limits<double>::max();
    in_p_force.tau_max<<std::numeric_limits<double>::max(),std::numeric_limits<double>::max(),std::numeric_limits<double>::max(),std::numeric_limits<double>::max(),
            std::numeric_limits<double>::max(),std::numeric_limits<double>::max(),std::numeric_limits<double>::max();
    in_p_force.k_p=c_cntr.f_cntr_k_p;
    in_p_force.k_i=c_cntr.f_cntr_k_i;
    in_p_force.k_d=c_cntr.f_cntr_k_d;
    in_p_force.k_d_N=c_cntr.f_cntr_k_d_N;
    in_p_force.d_max=c_cntr.f_cntr_d_max;
    in_p_force.phi_max=c_cntr.f_cntr_phi_max;
    in_p_force.sf_on<<c_cntr.f_cntr_sf_on;

    this->input_control_force(p);

    this->_cntr_force.initialize(this->_in_u_force,in_p_force);
}

void Core::initialize_control_mux(const Percept &p){
    cntr_mux::In_P_cntr_mux in_p_mux;
    const ConfigController& c_cntr=this->_kb->get_local_memory()->access_config_cntr();

    in_p_mux.dtau_max=c_cntr.dtau_c_max;
    in_p_mux.tau_max=c_cntr.tau_c_max;
    this->_cntr_mux.initialize(this->_in_u_mux,in_p_mux);
}

void Core::initialize_virtual_cube(const Percept &p){
    virtual_cube::In_P_virtual_cube in_p_virt_cube;
    const ConfigController& c_cntr=this->_kb->get_local_memory()->access_config_cntr();
    in_p_virt_cube.damping_distance=c_cntr.virt_cube_damp_dist;
    in_p_virt_cube.damping_factor=c_cntr.virt_cube_damp;
    in_p_virt_cube.eta=c_cntr.virt_cube_eta;
    in_p_virt_cube.rho_min=c_cntr.virt_cube_rho_min;
    in_p_virt_cube.cube_walls=c_cntr.virt_cube_walls;
    in_p_virt_cube.f_max=c_cntr.virt_cube_f_max;
    this->_virt_cube.initialize(this->_in_u_virt_cube,in_p_virt_cube);

    this->_flag_virt_cube_valid=false;
}

void Core::initialize_virtual_walls_joint(const Percept &p){
    virtual_walls_joint::In_P_virtual_walls_joint in_p_virt_walls_joint;
    const ConfigController& c_cntr=this->_kb->get_local_memory()->access_config_cntr();
    in_p_virt_walls_joint.damping_distance=c_cntr.virt_walls_joint_damp_dist;
    in_p_virt_walls_joint.damping_factor=c_cntr.virt_walls_joint_damp;
    in_p_virt_walls_joint.eta=c_cntr.virt_walls_joint_eta;
    in_p_virt_walls_joint.rho_min=c_cntr.virt_walls_joint_rho_min;
    in_p_virt_walls_joint.tau_max=c_cntr.virt_walls_joint_tau_max;
    in_p_virt_walls_joint.walls=c_cntr.virt_walls_joint_walls;
    this->_virt_walls_joint.initialize(this->_in_u_virt_walls_joint,in_p_virt_walls_joint);

    this->_flag_virt_walls_joint_valid=false;
}

void Core::initialize_control_nullspace(const Percept &p){
    const ConfigController& c_cntr=this->_kb->get_local_memory()->access_config_cntr();

    this->_in_u_cntr_nullsp_q.theta_d=p.q;

    cntr_joint_var_imp::In_P_cntr_joint_var_imp in_p_cntr_nullsp_q;

    in_p_cntr_nullsp_q.enable_ffwd_acc.setZero();
    in_p_cntr_nullsp_q.enable_ffwd_vel.setZero();

    this->_cntr_nullsp_q.initialize(this->_in_u_cntr_nullsp_q,in_p_cntr_nullsp_q);
    this->input_control_nullspace(p);
    this->_in_u_cntr_nullsp_q.K_theta=c_cntr.K_theta;
    this->_in_u_cntr_nullsp_q.D_theta=c_cntr.xi_theta;

    cntr_nullsp_proj::In_P_cntr_nullsp_proj in_p_cntr_nullsp_proj;
    in_p_cntr_nullsp_proj.singlr_comp_mode.setZero();
    in_p_cntr_nullsp_proj.singlr_threshold.setZero();
    this->_cntr_nullsp_proj.initialize(this->_in_u_cntr_nullsp_proj,in_p_cntr_nullsp_proj);
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

void Core::input_control_aic(const Percept &p){
    this->_in_u_aic.B_J_EE=p.B_J_EE;
    this->_in_u_aic.dtheta=p.dtheta;
    this->_in_u_aic.M=p.M;
    this->_in_u_aic.TF_F_ext=p.TF_F_ext;
    this->_in_u_aic.TF_F_ff<<0,0,0,0,0,0;
    this->_in_u_aic.TF_T_EE=p.TF_T_EE;
    this->_in_u_aic.TF_T_EE_d=p.TF_T_EE;

    this->_in_u_vel2pose.TF_dX_d<<0,0,0,0,0,0;
    this->_in_u_vel2pose.TF_T_EE=p.TF_T_EE;
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

void Core::input_control_force(const Percept &p){
    this->_in_u_force.B_J_EE=p.B_J_EE;
    this->_in_u_force.DX<<0,0,0,0,0,0;
    this->_in_u_force.TF_F_d_K<<0,0,0,0,0,0;
    this->_in_u_force.TF_F_ext_K=-p.TF_F_ext;
}

void Core::input_control_mux(const Percept &p){
    this->_in_u_mux.B_J_EE=p.B_J_EE;
    this->_in_u_mux.tau_J_d<<0,0,0,0,0,0,0;
}

void Core::input_virtual_cube(const Percept &p){
    this->_in_u_virt_cube.dx_EE=p.O_dX;
    this->_in_u_virt_cube.p_EE=p.O_T_EE.block<3,1>(0,3);
    this->_in_u_virt_cube.Jacobian_EE=p.B_J_O;
}

void Core::input_virtual_walls_joint(const Percept &p){
    this->_in_u_virt_walls_joint.dq=p.dq;
    this->_in_u_virt_walls_joint.q=p.q;
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
    int mode = this->_kb->get_local_memory()->access_config_general().control_mode;
    switch(mode){
    case 0:
        this->_cntr_aic.terminate();
        this->_cntr_force.terminate();
        this->_cntr_mux.terminate();
        this->_conv_vel2pose.terminate();
        if(this->_kb->get_local_memory()->access_config_cntr().virt_cube_on){
            this->_virt_cube.terminate();
        }
        if(this->_kb->get_local_memory()->access_config_cntr().virt_walls_joint_on){
            this->_virt_walls_joint.terminate();
        }
        if(this->_kb->get_local_memory()->access_config_cntr().nullspace_cntr_on){
            this->_cntr_nullsp_q.terminate();
            this->_cntr_nullsp_proj.terminate();
        }
        break;
    case 2:
        this->_cntr_joint_imp.terminate();
        this->_cntr_mux.terminate();
        if(this->_kb->get_local_memory()->access_config_cntr().nullspace_cntr_on){
            this->_cntr_nullsp_q.terminate();
            this->_cntr_nullsp_proj.terminate();
        }
        break;
    default:break;
    }

}

bool Core::start_control_cycle(){
    if(this->check_lockdown()){
        spdlog::error("Core is under lockdown.");
        return false;
    }

    this->_flag_stop_control=false;
    this->_flag_virt_cube_valid=false;
    this->_flag_virt_walls_joint_valid=false;

    this->_last_error="none";

    if(this->_active_skill==nullptr){
        spdlog::warn("No skill has been loaded, can not start control.");
        return false;
    }

    if(this->_flag_invalid_mode){
        //        spdlog::warn("Robot is in invalid mode, attempting automatic error recovery...");
        try{
            this->_robot->automaticErrorRecovery();
            this->_flag_invalid_mode=false;
            //            cpp_utils::print_success("Recovery successful.");
        }catch(const franka::CommandException& e){
            spdlog::error("Automatic error recovery failed, check the user-stop.");
            return false;
        }catch(const franka::NetworkException& e){
            spdlog::error("Automatic error recovery failed, check the network connection.");
            return false;
        }
    }

    bool valid=true;
    bool flag_recovery=false;
    this->lock_robot_connection();

    while(!this->_flag_stop_control){
        try{
            this->_tau_J_old={0,0,0,0,0,0,0};
            if(this->_kb->get_local_memory()->access_config_system().has_robot){
                if(this->_kb->get_local_memory()->access_config_system().has_gripper){
                    this->_gripper_state=this->_gripper->readOnce();
                }
                this->process_percept(this->_robot->readOnce(),this->_gripper_state);
                CmdSkill cmd;
                cmd.set_0(this->_percept);
                this->process_commands(cmd);

                if(this->_percept.robot_mode!=franka::RobotMode::kIdle){
                    spdlog::error("INVALID MODE");
                    this->unlock_robot_connection();
                    throw CoreException("Robot is in invalid mode.");
                }

                if(!this->write_config_to_robot()){
                    spdlog::error("Could not set robot configuration.");
                    this->terminate_control_cycle();
                    valid=false;
                    break;
                }
            }
            if(this->_kb->get_local_memory()->access_config_system().has_gripper){
                this->_flag_run_gripper=true;
                //                this->_thr_gripper=std::thread(&Core::gripper_cycle,this);
//                this->_thr_gripper.detach();
            }
            if(this->_kb->get_local_memory()->access_config_general().control_mode==0){
                this->input_control_aic(this->_percept);
                this->input_control_force(this->_percept);
                this->input_control_mux(this->_percept);
                this->input_virtual_cube(this->_percept);
                this->input_virtual_walls_joint(this->_percept);
                this->input_control_nullspace(this->_percept);
                this->initialize_control_aic(this->_percept);
                this->initialize_control_force(this->_percept);
                this->initialize_control_mux(this->_percept);
                this->initialize_virtual_cube(this->_percept);
                if(this->_kb->get_local_memory()->access_config_cntr().virt_walls_joint_on){
                    this->initialize_virtual_walls_joint(this->_percept);
                }
                if(this->_kb->get_local_memory()->access_config_cntr().nullspace_cntr_on){
                    this->initialize_control_nullspace(this->_percept);
                }

                if(this->_kb->get_local_memory()->access_config_system().has_simulation){
                    this->sim_control(std::bind(&Core::control_cycle_torque_cart,this,std::placeholders::_1));
                }else if(this->_kb->get_local_memory()->access_config_system().has_robot){
                    this->_robot->control(std::bind(&Core::control_cycle_torque_cart,this,std::placeholders::_1));
                }else{
                    this->dummy_control(std::bind(&Core::control_cycle_torque_cart,this,std::placeholders::_1));
                }
            }
            else if(this->_kb->get_local_memory()->access_config_general().control_mode==1){
                if(this->_kb->get_local_memory()->access_config_system().has_robot){
                    this->_robot->control(std::bind(&Core::control_cycle_velocity_cart,this,std::placeholders::_1));
                }else{
                    this->dummy_control(std::bind(&Core::control_cycle_velocity_cart,this,std::placeholders::_1));
                }
            }
            else if(this->_kb->get_local_memory()->access_config_general().control_mode==2){
                this->input_control_joint_imp(this->_percept);
                this->input_control_mux(this->_percept);
                this->input_control_nullspace(this->_percept);
                this->initialize_control_joint_imp(this->_percept);
                this->initialize_control_mux(this->_percept);
                if(this->_kb->get_local_memory()->access_config_cntr().virt_walls_joint_on){
                    this->initialize_virtual_walls_joint(this->_percept);
                }
                if(this->_kb->get_local_memory()->access_config_cntr().nullspace_cntr_on){
                    this->initialize_control_nullspace(this->_percept);
                }

                if(this->_kb->get_local_memory()->access_config_system().has_simulation){
                    this->sim_control(std::bind(&Core::control_cycle_torque_joint,this,std::placeholders::_1));
                }else if(this->_kb->get_local_memory()->access_config_system().has_robot){
                    this->_robot->control(std::bind(&Core::control_cycle_torque_joint,this,std::placeholders::_1));
                }else{
                    this->dummy_control(std::bind(&Core::control_cycle_torque_joint,this,std::placeholders::_1));
                }
            }
            else if(this->_kb->get_local_memory()->access_config_general().control_mode==3){
                if(this->_kb->get_local_memory()->access_config_system().has_robot){
                    this->_robot->control(std::bind(&Core::control_cycle_velocity_joint,this,std::placeholders::_1));
                }else{
                    this->dummy_control(std::bind(&Core::control_cycle_velocity_joint,this,std::placeholders::_1));
                }
            }
            else{
                spdlog::error("There is no control mode "+std::to_string(this->_kb->get_local_memory()->access_config_general().control_mode)+". Choose between 0 (torque), 1 (Cartesian velocity)");
                this->terminate_control_cycle();
                valid=false;
            }
        }catch (const franka::ControlException& e) {
            std::cout << e.what() << std::endl;
            flag_recovery=true;
            if(!this->_kb->get_local_memory()->access_config_general().instant_recovery){
                this->terminate_control_cycle();
                valid=false;
                this->_last_error="control_exception";
            }
            this->_active_skill->append_error("control_exception");
        }catch (const franka::InvalidOperationException& e){
            std::cout << e.what() << std::endl;
            spdlog::error("A conflicting operation is already running.");
            flag_recovery=true;
            this->terminate_control_cycle();
            valid=false;
            this->_active_skill->append_error("invalid_operation_exception");
        }catch(const franka::NetworkException& e){
            std::cout << e.what() << std::endl;
            spdlog::error("Check connections and ip settings.");
            flag_recovery=true;
            this->terminate_control_cycle();
            valid=false;
            this->_active_skill->append_error("network_exception");
        }catch(const franka::RealtimeException& e){
            std::cout << e.what() << std::endl;
            spdlog::error("Realtime priority could not be set. Check for other running instances of libfranka.");
            flag_recovery=true;
            this->terminate_control_cycle();
            valid=false;
            this->_active_skill->append_error("realtime_exception");
        }catch(const SkillException& e){
            std::cout<<e.what()<<std::endl;
            spdlog::error("Skill exception has been thrown during core activity.");
            flag_recovery=true;
            this->terminate_control_cycle();
            valid=false;
            this->_active_skill->append_error("skill_exception");
        }
        flag_recovery=true;
        if(flag_recovery){
            try{
                spdlog::info("Attempting automatic error recovery...",false);
                this->_robot->automaticErrorRecovery();
                spdlog::info("done.");
            }catch(const franka::CommandException& e){
                spdlog::info("failed.");
                spdlog::error("Automatic error recovery failed, check the user-stop.");
                this->_flag_invalid_mode=true;
                flag_recovery=false;
                valid=false;
                this->_active_skill->append_error("command_exception");
            }catch(const franka::NetworkException& e){
                spdlog::info("failed.");
                spdlog::error("Automatic error recovery failed, check the network connection.");
                this->_flag_invalid_mode=true;
                flag_recovery=false;
                valid=false;
                this->_active_skill->append_error("network_exception");
            }
        }
        this->terminate_gripper();
        this->terminate_control();
        this->terminate_periphery();
    }

    this->unlock_robot_connection();
    return valid;
}

void Core::terminate_control_cycle(){
    this->_flag_stop_control=true;
}

bool Core::control_base_cycle(const franka::RobotState state,CmdSkill& cmd){

    this->process_percept(state,this->_gripper_state);
    if(this->_active_skill==nullptr){
        spdlog::warn("No skill has been loaded, terminating control.");
        this->terminate_control_cycle();
        return false;
    }

    this->input_motion_error(this->_percept);
    this->_motion_error_cart.step(this->_in_u_motion_error_cart,this->_out_y_motion_error_cart);
    cmd=this->_active_skill->cycle(this->_percept);
    if(!cmd.validity_check()){
        spdlog::error("Validity check of robot command has failed.");
        this->terminate_control_cycle();
        return false;
    }
    this->process_commands(cmd);

    if(this->_active_skill->get_flag_terminate()){
        spdlog::info("Skill has terminated nominally.");
        this->terminate_control_cycle();
    }

    if(this->_kb->get_local_memory()->access_config_system().telemetry_on){
        this->_telemetry_udp.send_telemetry(this->_percept);
    }

    return true;
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

    if(this->_kb->get_local_memory()->access_config_cntr().virt_cube_on){
        this->_virt_cube.step(this->_in_u_virt_cube,this->_out_y_virt_cube);
    }
    if(this->_kb->get_local_memory()->access_config_cntr().virt_walls_joint_on){
        this->_virt_walls_joint.step(this->_in_u_virt_walls_joint,this->_out_y_virt_walls_joint);
    }

    bool cube_valid = this->validity_check_virtual_cube();
    bool walls_joint_valid = this->validity_check_virtual_walls_joint();

    if(this->_kb->get_local_memory()->access_config_cntr().nullspace_cntr_on){
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
    if(this->_kb->get_local_memory()->access_config_general().safe_mode){
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

    if(this->_kb->get_local_memory()->access_config_cntr().virt_walls_joint_on){
        this->_virt_walls_joint.step(this->_in_u_virt_walls_joint,this->_out_y_virt_walls_joint);
    }

    bool walls_joint_valid = this->validity_check_virtual_walls_joint();

    if(this->_kb->get_local_memory()->access_config_cntr().nullspace_cntr_on){
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
    if(this->_kb->get_local_memory()->access_config_general().safe_mode){
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

    franka::CartesianVelocities O_dP_EE_d = cpp_utils::convert_to_array<double,6,1>(cpp_utils::rotate_vector(cmd_skill.TF_dX_d,this->_active_skill->get_config<>()->frames.O_R_TF));
    if(!this->validity_check_velocity_cart(O_dP_EE_d.O_dP_EE)){
        this->terminate_control_cycle();
    }

    auto t_s_end = std::chrono::system_clock::now();

    double t=std::chrono::duration_cast<std::chrono::microseconds>(t_s_end-t_s_start).count();

    if(this->_flag_stop_control){
        spdlog::info("Controller cycle has been terminated.");
        return franka::MotionFinished(O_dP_EE_d);
    }
    if(this->_kb->get_local_memory()->access_config_general().safe_mode){
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
    franka::JointVelocities dq_d = cpp_utils::convert_to_array<double,7,1>(cmd_skill.dq_d);

    if(!this->validity_check_velocity_joint(dq_d.dq)){
        this->terminate_control_cycle();
    }

    auto t_s_end = std::chrono::system_clock::now();

    double t=std::chrono::duration_cast<std::chrono::microseconds>(t_s_end-t_s_start).count();

    if(this->_flag_stop_control){
        return franka::MotionFinished(dq_d);
    }
    if(this->_kb->get_local_memory()->access_config_general().safe_mode){
        std::cout<<"dq_d=["<<dq_d.dq[0]<<","<<dq_d.dq[1]<<","<<dq_d.dq[2]<<","<<dq_d.dq[3]<<","<<dq_d.dq[4]<<","<<dq_d.dq[5]<<","<<dq_d.dq[6]<<std::endl;
        spdlog::info("Cycle time: "+std::to_string(t));
        dq_d={0,0,0,0,0,0,0};
    }

    return dq_d;
}

void Core::process_percept(const franka::RobotState &state, const franka::GripperState &state_gripper,Eigen::Matrix<double,3,3> O_R_TF){
    if(!this->_kb->get_local_memory()->access_config_system().has_robot){
        this->_percept.set_0();
        this->_percept.time+=0.001;
        return;
    }

    this->_percept.B_J_EE=Eigen::Map<Eigen::Matrix<double,6,7> > (this->_model->bodyJacobian(franka::Frame::kEndEffector,state).data());
    this->_percept.B_J_O=Eigen::Map<Eigen::Matrix<double,6,7> >(this->_model->zeroJacobian(franka::Frame::kEndEffector,state).data());
    this->_percept.M=Eigen::Map<Eigen::Matrix<double,7,7> >(this->_model->mass(state).data());
    this->_percept.C=Eigen::Map<Eigen::Matrix<double,7,1> >(this->_model->coriolis(state).data());
    this->_percept.G=Eigen::Map<Eigen::Matrix<double,7,1> >(this->_model->gravity(state).data());

    this->_percept.q=Eigen::Map<Eigen::Matrix<double,7,1> >(std::array<double,7>(state.q).data());
    this->_percept.dq=Eigen::Map<Eigen::Matrix<double,7,1> >(std::array<double,7>(state.dq).data());
    this->_percept.theta=Eigen::Map<Eigen::Matrix<double,7,1> >(std::array<double,7>(state.theta).data());
    this->_percept.dtheta=Eigen::Map<Eigen::Matrix<double,7,1> >(std::array<double,7>(state.dtheta).data());

    this->_percept.O_dX=this->_percept.B_J_O*this->_percept.dq;
    this->_percept.O_T_EE=Eigen::Matrix<double,4,4>(Eigen::Map<Eigen::Matrix<double,4,4> >(std::array<double,16>(state.O_T_EE).data()));

    this->_percept.K_F_ext=Eigen::Map<Eigen::Matrix<double,6,1> >(std::array<double,6>(state.K_F_ext_hat_K).data());
    this->_percept.O_F_ext=Eigen::Map<Eigen::Matrix<double,6,1> >(std::array<double,6>(state.O_F_ext_hat_K).data());

    if(this->_active_skill==nullptr && O_R_TF.isZero(0)){
        this->_percept.TF_dX=cpp_utils::rotate_vector(this->_percept.O_dX,cpp_utils::invert_matrix(this->_kb->get_local_memory()->access_config_frames().O_R_TF));
        if(this->_kb->get_local_memory()->access_config_cntr().TF_control){
            this->_percept.TF_F_ext=cpp_utils::rotate_vector(this->_percept.K_F_ext,cpp_utils::invert_matrix(this->_kb->get_local_memory()->access_config_frames().O_R_TF));
        }else{
            this->_percept.TF_F_ext=this->_percept.K_F_ext;
        }
        this->_percept.TF_T_EE=cpp_utils::rotate_matrix(Eigen::Matrix<double,4,4>(Eigen::Map<Eigen::Matrix<double,4,4> >(std::array<double,16>(state.O_T_EE).data())),cpp_utils::invert_matrix(this->_kb->get_local_memory()->access_config_frames().O_R_TF));
    }else if(this->_active_skill==nullptr && !O_R_TF.isZero(0)){
        this->_percept.TF_dX=cpp_utils::rotate_vector(this->_percept.O_dX,cpp_utils::invert_matrix(O_R_TF));
        if(this->_kb->get_local_memory()->access_config_cntr().TF_control){
            this->_percept.TF_F_ext=cpp_utils::rotate_vector(this->_percept.K_F_ext,cpp_utils::invert_matrix(O_R_TF));
        }else{
            this->_percept.TF_F_ext=this->_percept.K_F_ext;
        }
        this->_percept.TF_T_EE=cpp_utils::rotate_matrix(Eigen::Matrix<double,4,4>(Eigen::Map<Eigen::Matrix<double,4,4> >(std::array<double,16>(state.O_T_EE).data())),cpp_utils::invert_matrix(O_R_TF));
    }else if(this->_active_skill!=nullptr){
        this->_percept.TF_dX=cpp_utils::rotate_vector(this->_percept.O_dX,cpp_utils::invert_matrix(this->_active_skill->get_config<>()->frames.O_R_TF));
        if(this->_kb->get_local_memory()->access_config_cntr().TF_control){
            Eigen::Matrix<double,3,3> O_R_EE = this->_percept.O_T_EE.block<3,3>(0,0);
            Eigen::Matrix<double,6,1> O_F_ext_hat_K_ = cpp_utils::rotate_vector(this->_percept.K_F_ext,O_R_EE);
            this->_percept.TF_F_ext=cpp_utils::rotate_vector(O_F_ext_hat_K_,cpp_utils::invert_matrix(this->_active_skill->get_config<>()->frames.O_R_TF));
        }else{
            this->_percept.TF_F_ext=this->_percept.K_F_ext;
        }
        this->_percept.TF_T_EE=cpp_utils::rotate_matrix(Eigen::Matrix<double,4,4>(Eigen::Map<Eigen::Matrix<double,4,4> >(std::array<double,16>(state.O_T_EE).data())),cpp_utils::invert_matrix(this->_active_skill->get_config<>()->frames.O_R_TF));
    }

    this->_percept.tau_ext=Eigen::Map<Eigen::Matrix<double,7,1> >(std::array<double,7>(state.tau_ext_hat_filtered).data());
    this->_percept.tau_j=Eigen::Map<Eigen::Matrix<double,7,1> >(std::array<double,7>(state.tau_J).data());

    this->_percept.robot_mode=state.robot_mode;

    this->_percept.e=this->_out_y_motion_error_cart.e;

    this->_percept.time=state.time.toSec();

    if(this->_flag_gripper){
        this->_percept.gripper_width=state_gripper.width;
        this->_percept.is_grasping=state_gripper.is_grasped;
        this->_flag_gripper=false;
    }

    // update mios state
    if(this->_active_skill!=nullptr){
        this->_percept.mios_state.active_skill=this->_active_skill->get_id();
    }else{
        this->_percept.mios_state.active_skill="none";
    }

    // post telemetry
    this->_telemetry.q[0]={state.q[0],state.q[1],state.q[2],state.q[3],state.q[4],state.q[5],state.q[6]};
    this->_telemetry.tau_ext[0]={state.tau_ext_hat_filtered[0],state.tau_ext_hat_filtered[1],state.tau_ext_hat_filtered[2],state.tau_ext_hat_filtered[3],state.tau_ext_hat_filtered[4],state.tau_ext_hat_filtered[5],state.tau_ext_hat_filtered[6]};

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
        cpp_utils::rpc_call("localhost",9000,"set_led",{request},response);

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
    if(!this->_kb->get_local_memory()->access_config_system().has_robot){
        return true;
    }
    if(!this->_kb->get_local_memory()->access_config_system().has_gripper){
        spdlog::warn("Gripper not connected.");
        return false;
    }

    Object obj;
    if(!this->_kb->load_object(o,obj)){
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
        this->_kb->get_local_memory()->modify_hidden_config_user(p);
        this->_percept.mios_state.grasped_object=o;
        this->_robot->setLoad(obj.mass,cpp_utils::convert_to_array<double,3,1>(obj.EE_ob_com),cpp_utils::convert_to_array<double,3,3>(obj.ob_I));
        nlohmann::json p_frame;
        cpp_utils::write_json_array<double,4,4>(p_frame["EE_T_TCP"],obj.EE_T_O);
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
    if(!this->_kb->get_local_memory()->access_config_system().has_robot){
        return true;
    }
    if(!this->_kb->get_local_memory()->access_config_system().has_gripper){
        spdlog::warn("Gripper not connected.");
        return false;
    }
    if(!this->has_gripper_connection()){
        spdlog::error("Cannot grasp object. I am currently not connection to the gripper.");
        return false;
    }
    Object obj;
    if(!this->_kb->load_object(o,obj)){
        spdlog::error("Cannot find object "+o+" in knowledge base.");
        return false;
    }
    if(!this->lock_robot_connection(false)){
        spdlog::error("Cannot access gripper, another process is blocking the FCI.");
        return false;
    }
    bool result=false;
    try{
        double max_width=this->_gripper->readOnce().max_width;
        double current_width=this->_gripper->readOnce().width;
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
        if(!this->_gripper->readOnce().is_grasped){
            result=this->_gripper->grasp(width,speed,force,1,1);
        }else{
            result=true;
        }
        franka::GripperState gripper_state=this->_gripper->readOnce();
        if(check_width && (gripper_state.width<obj.grasp_width-0.005 || gripper_state.width>obj.grasp_width+0.005)){
            spdlog::error("Dimensions of object "+o+" not within expected limits. Expected: " + std::to_string(obj.grasp_width) + ", but measured: " + std::to_string(gripper_state.width));
            this->_gripper->move(current_width,1);
            this->unlock_robot_connection();
            return false;
        }
        nlohmann::json p;
        p["grasped_object"]=o;
        this->_kb->get_local_memory()->modify_hidden_config_user(p);
        this->_percept.mios_state.grasped_object=o;
        this->_robot->setLoad(obj.mass,cpp_utils::convert_to_array<double,3,1>(obj.EE_ob_com),cpp_utils::convert_to_array<double,3,3>(obj.ob_I));
        nlohmann::json p_frame;
        cpp_utils::write_json_array<double,4,4>(p_frame["EE_T_TCP"],obj.EE_T_O);
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
    if(!this->_kb->get_local_memory()->access_config_system().has_robot){
        return true;
    }
    if(!this->_kb->get_local_memory()->access_config_system().has_gripper){
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
        if(this->_gripper->readOnce().is_grasped){
            spdlog::error("Cannot home the gripper while grasping.");
            result=false;
        }else{
            result=this->_gripper->homing();
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
    if(!this->_kb->get_local_memory()->access_config_system().has_gripper){
        spdlog::warn("Gripper not connected.");
        return false;
    }
    if(!this->has_gripper_connection()){
        spdlog::error("Cannot move gripper. I am currently not connected to the gripper.");
        return false;
    }
    bool result=false;
    try{
        result=this->_gripper->grasp(width,speed,force,1,1);
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
    if(!this->_kb->get_local_memory()->access_config_system().has_gripper){
        spdlog::warn("Gripper not connected.");
        return false;
    }
    if(!this->has_gripper_connection()){
        spdlog::error("Cannot move gripper. I am currently not connected to the gripper.");
        return false;
    }
    bool result=false;
    try{
        result=this->_gripper->move(width,speed);
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
    if(!this->_kb->get_local_memory()->access_config_system().has_robot){
        return true;
    }
    if(!this->_kb->get_local_memory()->access_config_system().has_gripper){
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
        double max_width=this->_gripper->readOnce().max_width;
        if(width==-1){
            width=max_width;
        }else{
            if(width<0 || width>max_width){
                spdlog::error("Gripper cannot reach width of "+std::to_string(width)+". Must be between 0 and "+std::to_string(max_width)+".");
                this->unlock_robot_connection();
                return false;
            }
        }
        result=this->_gripper->move(width,speed);
        nlohmann::json p;
        p["grasped_object"]="none";
        this->_percept.mios_state.grasped_object="none";
        this->_kb->get_local_memory()->modify_hidden_config_user(p);
        this->_robot->setLoad(0,{0,0,0},{0,0,0,0,0,0,0,0,0});
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
    cpp_utils::write_json_array<double,4,4>(p["EE_T_TCP"],EE_T_TCP);
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
        this->_gripper->grasp(width,speed,force,epsilon_inner,epsilon_outer);
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
        this->_gripper->move(width,speed);
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
        this->_gripper->homing();
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
        return this->_gripper->readOnce().is_grasped;
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
        this->_gripper->stop();
    }catch(franka::CommandException& e){
        std::cout<<e.what()<<std::endl;
    }catch(franka::NetworkException& e){
        std::cout<<e.what()<<std::endl;
    }
    this->_flag_gripper_busy=false;
}

const Percept& Core::request_percept(Eigen::Matrix<double,3,3> O_R_TF, bool wait){
    if(!this->_kb->get_local_memory()->access_config_system().has_robot){
        this->_percept.robot_mode=franka::RobotMode::kIdle;
        return this->_percept;
    }
    if(!this->has_robot_connection()){
        spdlog::warn("Not connected to robot, could not refresh perception.");
        return this->_percept;
    }
    if(!this->lock_robot_connection(wait)){
        return this->_percept;
    }
    try{
        franka::RobotState state_robot;
        franka::GripperState state_gripper;
        if(this->_kb->get_local_memory()->access_config_system().has_robot){
            state_robot=this->_robot->readOnce();
        }
        if(this->_kb->get_local_memory()->access_config_system().has_gripper){
            state_gripper=this->_gripper->readOnce();
        }
        this->_flag_gripper=true;
        this->process_percept(state_robot,state_gripper,O_R_TF);
        this->_flag_gripper=false;
    }catch(franka::InvalidOperationException& e){
        std::cout<<e.what()<<std::endl;
        this->unlock_robot_connection();
        spdlog::warn("Cannot read robot state, another operation is blocking. Unpredictable behavior possible.");
        return this->_percept;
    }catch(franka::NetworkException& e){
        std::cout<<e.what()<<std::endl;
        this->unlock_robot_connection();
        throw CoreException("Encountered network problems.");
    }
    this->unlock_robot_connection();
    return this->_percept;
}

void Core::check_cartesian_velocity_workspace(Eigen::Matrix<double, 6, 1> &TF_dX_d, const Percept& p){
    for(unsigned i=0;i<3;i++){
        if(p.TF_T_EE(i,3)<=this->get_kb()->get_local_memory()->access_config_user().x_limits(2*i) && TF_dX_d(i)<0){
            TF_dX_d(i)=0;
        }
        if(p.TF_T_EE(i,3)>=this->get_kb()->get_local_memory()->access_config_user().x_limits(2*i+1) && TF_dX_d(i)>0){
            TF_dX_d(i)=0;
        }
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
        usleep(1000-t);
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
        usleep(1000-t);
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
        usleep(1000-t);
    }
}

void Core::sim_control(std::function<franka::Torques (const franka::RobotState &)> control_cycle){
    if(this->_sim_interface==nullptr){
        spdlog::critical("Simulation interface does not exist. Please inform a developer about this error.");
        this->terminate_control_cycle();
    }
    if(!this->_sim_interface->connect_to_sim(this->get_kb()->get_local_memory()->access_config_system().ip_simulation,this->get_kb()->get_local_memory()->access_config_system().port_simulation)){
        spdlog::error("Could not connect to simulation environment.");
        this->terminate_control_cycle();
    }
    franka::Torques tau_J_d={0,0,0,0,0,0,0};
    franka::RobotState state;
    while(!tau_J_d.motion_finished){
        auto t_s_start = std::chrono::system_clock::now();
        tau_J_d=control_cycle(state);
        this->_sim_interface->send_cmd_torques(tau_J_d.tau_J);
        auto t_s_end = std::chrono::system_clock::now();
        double t=std::chrono::duration_cast<std::chrono::microseconds>(t_s_end-t_s_start).count();
        usleep(1000-t);
    }
}

std::tuple<std::string,std::string,std::string> Core::get_desk_data(){
    return std::tie(this->_kb->get_local_memory()->access_config_system().ip_robot,
                    this->_kb->get_local_memory()->access_config_system().desk_name,
                    this->_kb->get_local_memory()->access_config_system().desk_pwd);
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
    cpp_utils::rpc_call("localhost",9001,"start_task",{std::get<0>(desk_data),std::get<1>(desk_data),std::get<2>(desk_data),task},response);
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
    if(!cpp_utils::rpc_call("localhost",9001,"stop_task",{std::get<0>(desk_data),std::get<1>(desk_data),std::get<2>(desk_data)},response)){
        // stop signal
    }
}

bool Core::wait_for_desk_task(){
    nlohmann::json response;
    while(true){
        if(!cpp_utils::rpc_call("localhost",9001,"check_task",{},response)){
            spdlog::error("Connection to desk server faulty, undefined behavior possible.");
            return false;
        }
        bool finished;
        cpp_utils::read_json_param(response,"finished",finished);
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
    if(!cpp_utils::rpc_call("localhost",9001,"shutdown",{std::get<0>(desk_data),std::get<1>(desk_data),std::get<2>(desk_data)},response)){
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
    cpp_utils::rpc_call("localhost",9001,"unlock_brakes",{std::get<0>(desk_data),std::get<1>(desk_data),std::get<2>(desk_data)},response,10);
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
    cpp_utils::rpc_call("localhost",9001,"lock_brakes",{std::get<0>(desk_data),std::get<1>(desk_data),std::get<2>(desk_data)},response);
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
    cpp_utils::rpc_call("localhost",9001,"pack_pose",{std::get<0>(desk_data),std::get<1>(desk_data),std::get<2>(desk_data)},response);
    if(!this->initialize()){
        return false;
    }
    this->unlock_robot_connection();
    return true;
}

std::string Core::find_robot() const{
    std::string robot_address="none";
    std::string robot_iface="none";

    std::map<std::string,std::string> ifaces = cpp_utils::get_subnets();
    for(const auto& i : ifaces){
        if(i.first=="lo" || i.first=="docker0" || i.first=="tap0"){
            continue;
        }
        for(unsigned j=1;j<255;j++){
            std::string address=i.second+std::to_string(j);
            if(cpp_utils::ping(address.c_str())==1){
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
    std::vector<std::string> ifaces = cpp_utils::get_ifaces();
    for(unsigned i=0;i<ifaces.size();i++){
        std::string ip_subnet = ifaces[i];
        std::vector<std::string> ip_tmp = cpp_utils::split_string(ip_subnet,".");
        ip_subnet=ip_tmp[0]+"."+ip_tmp[1]+"."+ip_tmp[2]+".";
        for(unsigned i=1;i<254;i++){
            std::string address = ip_subnet+std::to_string(i);
            if(cpp_utils::ping(address.c_str())==1){
                continue;
            }else{
                if(this->test_primary_connection(address)){
                    ip=address;
                }
            }
        }

    }
    if(ip=="none"){
        spdlog::error("No primary has been found in this network.");
    }else{
        spdlog::info("Found primary, I am connected to a collective.");
    }
    return ip;
}

bool Core::test_primary_connection(const std::string &ip){
    nlohmann::json request=nlohmann::json();
    nlohmann::json response;
    return cpp_utils::rpc_call(ip,8390,"is_primary",request,response);
}

bool Core::init_sound(){
    if(!this->_kb->get_local_memory()->access_config_system().has_sound){
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
    if(!this->_kb->get_local_memory()->access_config_system().has_led){
        return true;
    }
    nlohmann::json response;
    if(!cpp_utils::rpc_call("localhost",9000,"get_panel_id",{},response)){
        spdlog::warn("Could not connect to LED server.");
        return false;
    }
    std::array<std::string,5> panels={"far-right","right","middle","left","far-left"};

    bool valid;
    if(!cpp_utils::read_json_param(response,"valid",valid)){
        spdlog::error("No valid response from LED server.");
        return false;
    }
    if(!valid){
        spdlog::error("Invalid LED configuration.");
        return false;
    }
    if(cpp_utils::find_json_value(response,"id")){
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
        if(!cpp_utils::find_json_value(response,"id")){
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
    if(this->_kb->get_local_memory()->access_config_system().has_led){
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
    if(!this->_kb->get_local_memory()->access_config_system().has_sound){
        return true;
    }
    Mix_CloseAudio();
    return true;
}

bool Core::terminate_led(){
    return true;
}

void Core::start_telemetry(){
    if(!this->_kb->get_local_memory()->access_config_system().telemetry_on){
        return;
    }
    ConfigTelemetryUDP config_telemetry;
    config_telemetry.ip_dst=this->_kb->get_local_memory()->access_config_system().telemetry_udp_ip;
    config_telemetry.port_dst=this->_kb->get_local_memory()->access_config_system().telemetry_udp_port;
    config_telemetry.frequency=this->_kb->get_local_memory()->access_config_system().telemetry_udp_frequency;
    if(!this->_telemetry_udp.initialize(config_telemetry)){
        spdlog::error("Could not initialize telemetry.");
        nlohmann::json p;
        p["telemetry_on"]=false;
        this->_kb->get_local_memory()->modify_config_system(p);
    }else{
        this->_flag_logged_in_digital_twin=true;
    }
}

void Core::terminate_telemetry(){
    this->_telemetry_udp.terminate();
}

bool Core::start_sim_interface(){
    //    this->_sim_interface=new SimInterface();
    return true;
}

bool Core::terminate_sim_interface(){
    //    if(this->_sim_interface!=nullptr){
    //        delete this->_sim_interface;
    //    }
    //    this->_sim_interface=nullptr;
    return true;
}

void Core::login_digital_twin(){
    nlohmann::json response;
    std::string name=this->get_kb()->get_local_memory()->access_config_system().id_robot;
    std::string location=this->get_kb()->get_local_memory()->access_config_system().location;
    std::string ip=this->get_kb()->get_local_memory()->access_config_system().telemetry_udp_ip;
    cpp_utils::rpc_call(ip,4000,"login",{name,location},response);
    int port;
    cpp_utils::read_json_param(response,"port",port);
    spdlog::info("I am logging into the digital twin with IP "+ip+" and port "+std::to_string(port)+".");
    nlohmann::json params;
    params["telemetry_on"]=true;
    if(port==-1){
        spdlog::warn("I am already logged into the digital twin.");
    }else{
        params["telemetry_udp_port"]=port;
        this->_kb->set_parameter("telemetry_udp_port","system",port);
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
    cpp_utils::rpc_call(ip,4000,"logout",{name},response);
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
        for(unsigned i=0;i<s.size();i++){
            char recvString[255];
            int recvStringLen;
            recvStringLen = recvfrom(s[i], recvString, 255, 0, NULL, 0);
            if(recvStringLen<0){
            }else{
                std::string buffer(recvString);
                std::string msg_str=std::string(buffer.begin(),buffer.begin()+recvStringLen);
                nlohmann::json msg=nlohmann::json::parse(msg_str);
                if(msg["designation"]=="digital_twin"){
                    nlohmann::json p;
                    p["telemetry_udp_ip"]=msg["ip"];
                    this->get_kb()->get_local_memory()->modify_config_system(p);
                    std::string ip;
                    cpp_utils::read_json_param(msg,"ip",ip);
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

