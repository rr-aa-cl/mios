#include "panda/panda_body.hpp"
#include <spdlog/spdlog.h>
#include <msrm_utils/network.hpp>

#include <franka/exception.h>

namespace mios {

PandaBody::PandaBody():m_panda_arm(nullptr),m_panda_model(nullptr),m_panda_hand(nullptr),m_arm_connected(false),m_hand_connected(false){

}

std::optional<std::string> PandaBody::get_robot_ip(const std::optional<std::string>& last_ip){
    std::optional<std::string> new_ip={};
    spdlog::debug("PandaBody: get_robot_ip("+last_ip.value_or("127.0.0.1")+")");
    if(last_ip.has_value()){
        if(msrm_utils::ping(last_ip.value().c_str())==false){
            spdlog::warn("IP was set to "+last_ip.value()+" but no device has been found. Searching for new connection...");
        }else{
            if(!is_robot(last_ip.value())){
                spdlog::warn("IP was set to "+last_ip.value()+" but no compatible robot seems to be connected. Searching for new connection...");
            }else{
                new_ip=last_ip;
            }
        }
    }
    if(!new_ip.has_value()){
        new_ip=this->find_robot();
    }
    return new_ip;
}

bool PandaBody::connect_to_robot(const std::optional<std::string> &ip){
    if(!ip.has_value()){
        return false;
    }
    try{
        m_panda_arm = std::make_unique<franka::Robot>(ip.value());
        m_panda_model = std::make_unique<franka::Model>(m_panda_arm->loadModel());
        m_arm_connected=true;
        return true;
    }catch(const franka::NetworkException& e){
        spdlog::debug(e.what());
        spdlog::error("Cannot connect to robot at IP "+ip.value());
        return false;
    }catch(const franka::IncompatibleVersionException& e){
        spdlog::debug(e.what());
        spdlog::error("Panda: Detected incompatible version on robot at IP "+ip.value());
        return false;
    }catch(const franka::ModelException& e){
        spdlog::debug(e.what());
        spdlog::error("Panda: Model could not be loaded.");
        return false;
    }
}

bool PandaBody::connect_to_gripper(const std::optional<std::string> &ip){
    if(!ip.has_value()){
        return false;
    }
    try{
        m_panda_hand = std::make_unique<franka::Gripper>(ip.value());
        m_hand_connected=true;
        return true;
    }catch(const franka::NetworkException& e){
        spdlog::debug(e.what());
        spdlog::error("Can not connect to gripper at IP " + ip.value());
        return false;
    }catch(const franka::IncompatibleVersionException& e){
        spdlog::debug(e.what());
        spdlog::error("Panda: Detected incompatible version on robot at IP "+ip.value());
        return false;
    }
}

void PandaBody::disconnect_from_robot(){
    m_arm_connected=false;
    m_panda_model.release();
    m_panda_arm.release();
}

void PandaBody::disconnect_from_gripper(){
    m_hand_connected=false;
    m_panda_hand.release();
}

bool PandaBody::recover(){
    if(!m_arm_connected){
        return true;
    }
    try{
        m_panda_arm->automaticErrorRecovery();
        return true;
    }catch(const franka::NetworkException& e){
        spdlog::debug(e.what());
        return false;
    }catch(const franka::CommandException& e){
        spdlog::debug(e.what());
        return false;
    }
}

bool PandaBody::pre_run_checks() const{
    franka::RobotState state;
    if(!get_robot_state(state)){
        return false;
    }
    if(state.robot_mode!=franka::RobotMode::kIdle){
        return false;
    }
    return true;
}

bool PandaBody::is_robot(const std::string &ip){
    try{
        spdlog::debug("panda_body: is_robot("+ip+")");
        std::unique_ptr<franka::Robot> robot =  std::make_unique<franka::Robot>(ip);
        return true;
    }catch(const franka::NetworkException& e){
        spdlog::info("Skipping device with ip "+ip+".");
        return false;
    }catch(const franka::IncompatibleVersionException& e){
        spdlog::error("At device with ip "+ip+": ");
        spdlog::debug(e.what());
        spdlog::error("Panda: Detected incompatible version on robot at IP "+ip);
        return false;
    }
}

std::optional<std::string> PandaBody::find_robot(){
    std::optional<std::string> robot_address={};
    std::string robot_iface="none";

    std::map<std::string,std::string> ifaces = msrm_utils::get_subnets();
    spdlog::debug("panda_body: find_robot");
    for(const auto& i : ifaces){
        if(i.first=="lo" || i.first=="docker0" || i.first=="tap0"){
            continue;
        }
        for(unsigned j=1;j<255;j++){
            std::string address=i.second+std::to_string(j);
            if(!msrm_utils::ping(address.c_str())){
                continue;
            }else{
                if(is_robot(address)){
                    robot_address=address;
                    break;
                }
            }
        }
        if(robot_address.has_value()){
            robot_iface=i.first;
            break;
        }
    }

    if(!robot_address.has_value()){
        spdlog::error("No connected robot found. Make sure that master controller and this computer share the same network and that the connection is properly configured.");
    }else{
        spdlog::info("Found robot at ip "+robot_address.value()+" at interface "+robot_iface+".");
    }
    return robot_address;
}

bool PandaBody::control(std::function<franka::Torques (const franka::RobotState&,franka::Duration)> controller_callback){
    try{
        if(m_arm_connected){
            spdlog::debug("PandaBody: control<Torques>");
            m_panda_arm->control(controller_callback);
            return true;
        }else{
            dummy_control(controller_callback);
            return true;
        }
    }catch(const franka::ControlException& e){
        spdlog::debug(e.what());
        return false;
    }catch(const franka::InvalidOperationException& e){
        spdlog::debug(e.what());
        return false;
    }catch(const franka::NetworkException& e){
        spdlog::debug(e.what());
        return false;
    }catch(const franka::RealtimeException& e){
        spdlog::debug(e.what());
        return false;
    }catch(const std::invalid_argument& e){
        spdlog::debug(e.what());
        return false;
    }

}

bool PandaBody::control(std::function<franka::CartesianVelocities (const franka::RobotState &,franka::Duration)> controller_callback){
    if(m_arm_connected){
        try{
            spdlog::debug("PandaBody: control<CartesianVelocities>");
            m_panda_arm->control(controller_callback);
            return true;
        }catch(const franka::ControlException& e){
            spdlog::debug(e.what());
            return false;
        }catch(const franka::InvalidOperationException& e){
            spdlog::debug(e.what());
            return false;
        }catch(const franka::NetworkException& e){
            spdlog::debug(e.what());
            return false;
        }catch(const franka::RealtimeException& e){
            spdlog::debug(e.what());
            return false;
        }catch(const std::invalid_argument& e){
            spdlog::debug(e.what());
            return false;
        }
    }else{
        dummy_control(controller_callback);
        return true;
    }
}

bool PandaBody::control(std::function<franka::JointVelocities (const franka::RobotState &,franka::Duration)> controller_callback){
    if(m_arm_connected){
        try{
            spdlog::debug("PandaBody: control<JointVelocities>");
            m_panda_arm->control(controller_callback);
            return true;
        }catch(const franka::ControlException& e){
            spdlog::debug(e.what());
            return false;
        }catch(const franka::InvalidOperationException& e){
            spdlog::debug(e.what());
            return false;
        }catch(const franka::NetworkException& e){
            spdlog::debug(e.what());
            return false;
        }catch(const franka::RealtimeException& e){
            spdlog::debug(e.what());
            return false;
        }catch(const std::invalid_argument& e){
            spdlog::debug(e.what());
            return false;
        }
    }else{
        dummy_control(controller_callback);
        return true;
    }
}

bool PandaBody::control(std::function<franka::CartesianPose (const franka::RobotState &,franka::Duration)> controller_callback){
    if(m_arm_connected){
        try{
            spdlog::debug("PandaBody: control<CartesianPose>");
            m_panda_arm->control(controller_callback);
            return true;
        }catch(const franka::ControlException& e){
            spdlog::debug(e.what());
            return false;
        }catch(const franka::InvalidOperationException& e){
            spdlog::debug(e.what());
            return false;
        }catch(const franka::NetworkException& e){
            spdlog::debug(e.what());
            return false;
        }catch(const franka::RealtimeException& e){
            spdlog::debug(e.what());
            return false;
        }catch(const std::invalid_argument& e){
            spdlog::debug(e.what());
            return false;
        }
    }else{
        dummy_control(controller_callback);
        return true;
    }
}

bool PandaBody::control(std::function<franka::JointPositions (const franka::RobotState &,franka::Duration)> controller_callback){
    if(m_arm_connected){
        try{
            spdlog::debug("PandaBody: control<JointPositions>");
            m_panda_arm->control(controller_callback);
            return true;
        }catch(const franka::ControlException& e){
            spdlog::debug(e.what());
            return false;
        }catch(const franka::InvalidOperationException& e){
            spdlog::debug(e.what());
            return false;
        }catch(const franka::NetworkException& e){
            spdlog::debug(e.what());
            return false;
        }catch(const franka::RealtimeException& e){
            spdlog::debug(e.what());
            return false;
        }catch(const std::invalid_argument& e){
            spdlog::debug(e.what());
            return false;
        }
    }else{
        dummy_control(controller_callback);
        return true;
    }
}

void PandaBody::dummy_control(std::function<franka::Torques (const franka::RobotState &,franka::Duration)> controller_callback){
    franka::Torques tau_J={0,0,0,0,0,0,0};
    franka::RobotState state;

    state.K_F_ext_hat_K={0,0,0,0,0,0};
    state.O_F_ext_hat_K={0,0,0,0,0,0};
    state.tau_ext_hat_filtered={0,0,0,0,0,0,0};
    state.q={0,0,0,0,0,0,0};
    state.dq={0,0,0,0,0,0,0};
    std::chrono::high_resolution_clock::time_point t_0;
    franka::Duration duration(std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::high_resolution_clock::now()-t_0));
    while(!tau_J.motion_finished){
        auto t_s_start = std::chrono::system_clock::now();
        tau_J=controller_callback(state,duration);
        auto t_s_end = std::chrono::system_clock::now();
        double t=std::chrono::duration_cast<std::chrono::microseconds>(t_s_end-t_s_start).count();
        duration=franka::Duration(t);
        std::this_thread::sleep_for(std::chrono::microseconds(1000-static_cast<int>(t)));
    }
}

void PandaBody::dummy_control(std::function<franka::CartesianVelocities (const franka::RobotState &,franka::Duration)> controller_callback){
    franka::CartesianVelocities tau_J={0,0,0,0,0,0,0};
    franka::RobotState state;
    state.K_F_ext_hat_K={0,0,0,0,0,0};
    state.O_F_ext_hat_K={0,0,0,0,0,0};
    state.tau_ext_hat_filtered={0,0,0,0,0,0,0};
    state.q={0,0,0,0,0,0,0};
    state.dq={0,0,0,0,0,0,0};
    std::chrono::high_resolution_clock::time_point t_0;
    franka::Duration duration(std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::high_resolution_clock::now()-t_0));
    while(!tau_J.motion_finished){
        auto t_s_start = std::chrono::system_clock::now();
        tau_J=controller_callback(state,duration);
        auto t_s_end = std::chrono::system_clock::now();
        double t=std::chrono::duration_cast<std::chrono::microseconds>(t_s_end-t_s_start).count();
        duration=franka::Duration(t);
        std::this_thread::sleep_for(std::chrono::microseconds(1000-static_cast<int>(t)));
    }
}

void PandaBody::dummy_control(std::function<franka::JointVelocities (const franka::RobotState &,franka::Duration)> controller_callback){
    franka::JointVelocities tau_J={0,0,0,0,0,0,0};
    franka::RobotState state;
    state.K_F_ext_hat_K={0,0,0,0,0,0};
    state.O_F_ext_hat_K={0,0,0,0,0,0};
    state.tau_ext_hat_filtered={0,0,0,0,0,0,0};
    state.q={0,0,0,0,0,0,0};
    state.dq={0,0,0,0,0,0,0};
    std::chrono::high_resolution_clock::time_point t_0;
    franka::Duration duration(std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::high_resolution_clock::now()-t_0));
    while(!tau_J.motion_finished){
        auto t_s_start = std::chrono::system_clock::now();
        tau_J=controller_callback(state,duration);
        auto t_s_end = std::chrono::system_clock::now();
        double t=std::chrono::duration_cast<std::chrono::microseconds>(t_s_end-t_s_start).count();
        duration=franka::Duration(t);
        std::this_thread::sleep_for(std::chrono::microseconds(1000-static_cast<int>(t)));
    }
}

void PandaBody::dummy_control(std::function<franka::CartesianPose (const franka::RobotState &,franka::Duration)> controller_callback){
    franka::CartesianPose tau_J={0,0,0,0,0,0,0};
    franka::RobotState state;
    state.K_F_ext_hat_K={0,0,0,0,0,0};
    state.O_F_ext_hat_K={0,0,0,0,0,0};
    state.tau_ext_hat_filtered={0,0,0,0,0,0,0};
    state.q={0,0,0,0,0,0,0};
    state.dq={0,0,0,0,0,0,0};
    std::chrono::high_resolution_clock::time_point t_0;
    franka::Duration duration(std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::high_resolution_clock::now()-t_0));
    while(!tau_J.motion_finished){
        auto t_s_start = std::chrono::system_clock::now();
        tau_J=controller_callback(state,duration);
        auto t_s_end = std::chrono::system_clock::now();
        double t=std::chrono::duration_cast<std::chrono::microseconds>(t_s_end-t_s_start).count();
        duration=franka::Duration(t);
        std::this_thread::sleep_for(std::chrono::microseconds(1000-static_cast<int>(t)));
    }
}

void PandaBody::dummy_control(std::function<franka::JointPositions (const franka::RobotState &,franka::Duration)> controller_callback){
    franka::JointPositions tau_J={0,0,0,0,0,0,0};
    franka::RobotState state;
    state.K_F_ext_hat_K={0,0,0,0,0,0};
    state.O_F_ext_hat_K={0,0,0,0,0,0};
    state.tau_ext_hat_filtered={0,0,0,0,0,0,0};
    state.q={0,0,0,0,0,0,0};
    state.dq={0,0,0,0,0,0,0};
    std::chrono::high_resolution_clock::time_point t_0;
    franka::Duration duration(std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::high_resolution_clock::now()-t_0));
    while(!tau_J.motion_finished){
        auto t_s_start = std::chrono::system_clock::now();
        tau_J=controller_callback(state,duration);
        auto t_s_end = std::chrono::system_clock::now();
        double t=std::chrono::duration_cast<std::chrono::microseconds>(t_s_end-t_s_start).count();
        duration=franka::Duration(t);
        std::this_thread::sleep_for(std::chrono::microseconds(1000-static_cast<int>(t)));
    }
}

bool PandaBody::set_robot_parameters(double load_m,std::array<double,3> load_com,std::array<double,9> load_I,std::array<double,7> tau_ext_contact,std::array<double,7> tau_ext_max,
                                     std::array<double,6> F_ext_K_contact,std::array<double,6> F_ext_K_max,std::array<double,16> EE_T_K,std::array<double,6> K_x,std::array<double,7> K_theta,
                                     std::array<double,16> F_T_EE){
    if(!m_arm_connected){
        return true;
    }
    try{
        m_panda_arm->setLoad(load_m,load_com,load_I);
        m_panda_arm->setEE(F_T_EE);
        m_panda_arm->setCollisionBehavior(tau_ext_contact,tau_ext_max,F_ext_K_contact,F_ext_K_max);
        m_panda_arm->setK(EE_T_K);
        m_panda_arm->setCartesianImpedance(K_x);
        m_panda_arm->setJointImpedance(K_theta);
    }catch(franka::CommandException& e){
        spdlog::debug(e.what());
        return false;
    }catch(franka::NetworkException& e){
        spdlog::debug(e.what());
        return false;
    }
    return true;
}

bool PandaBody::set_load(double load_m, std::array<double, 3> load_com, std::array<double, 9> load_I){
    try{
        m_panda_arm->setLoad(load_m,load_com,load_I);
        return true;
    }catch(franka::CommandException& e){
        spdlog::debug(e.what());
        return false;
    }catch(franka::NetworkException& e){
        spdlog::debug(e.what());
        return false;
    }
}

bool PandaBody::set_ee(std::array<double, 16> F_T_EE){
    try{
        m_panda_arm->setEE(F_T_EE);
        return true;
    }catch(franka::CommandException& e){
        spdlog::debug(e.what());
        return false;
    }catch(franka::NetworkException& e){
        spdlog::debug(e.what());
        return false;
    }
}

bool PandaBody::get_robot_state(franka::RobotState &state) const{
    if(m_arm_connected){
        try{
            state=m_panda_arm->readOnce();
            return true;
        }catch(const franka::InvalidOperationException& e){
            spdlog::debug(e.what());
            return false;
        }catch(const franka::NetworkException& e){
            spdlog::debug(e.what());
            return false;
        }
    }else{
        get_default_robot_state(state);
        return true;
    }
}

bool PandaBody::get_gripper_state(franka::GripperState &state) const{
    if(m_hand_connected){
        try{
            state=m_panda_hand->readOnce();
            return true;
        }catch(const franka::InvalidOperationException& e){
            spdlog::debug(e.what());
            return false;
        }catch(const franka::NetworkException& e){
            spdlog::debug(e.what());
            return false;
        }
    }else{
        get_default_gripper_state(state);
        return true;
    }
}

const std::unique_ptr<franka::Model>& PandaBody::get_panda_model() const{
    return m_panda_model;
}

bool PandaBody::start_desk_task(const std::string &task,const std::optional<std::string> &ip, const std::string user, const std::string& password){
    disconnect_from_gripper();
    disconnect_from_robot();
    if(!ip.has_value()){
        return false;
    }

    nlohmann::json response;
    nlohmann::json request={
        {"ip",ip.value()},
        {"user",user},
        {"password",password},
        {"task",task}
    };
    if(!msrm_utils::JsonUDPClient::call_method("localhost",9001,"start_task",request,response)){
        return false;
    }
    if(!this->wait_for_desk_task()){
        return false;
    }
    if(!this->connect_to_robot(get_robot_ip(ip))){
        return false;
    }
    if(!this->connect_to_gripper(get_robot_ip(ip))){
        return false;
    }
    return true;
}

void PandaBody::stop_desk_task(const std::optional<std::string> &ip, const std::string user, const std::string& password){
    nlohmann::json response;
    nlohmann::json request={
        {"ip",ip.value()},
        {"user",user},
        {"password",password}
    };
    msrm_utils::JsonUDPClient::call_method("localhost",9001,"stop_task",request,response);
}

bool PandaBody::wait_for_desk_task(){
    nlohmann::json response,request;
    while(true){
        if(!msrm_utils::JsonUDPClient::call_method("localhost",9001,"wait_for_task",request,response)){
            return false;
        }
        bool finished;
        if(response.is_null() || response.find("finished")==response.end()){
            return false;
        }
        response["finished"].get_to(finished);
        if(finished){
            break;
        }else{
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
    }
    return true;
}

bool PandaBody::shutdown_robot(const std::optional<std::string> &ip, const std::string user, const std::string& password){
    disconnect_from_gripper();
    disconnect_from_robot();
    nlohmann::json response;
    nlohmann::json request={
        {"ip",ip.value()},
        {"user",user},
        {"password",password}
    };
    if(!msrm_utils::JsonUDPClient::call_method("localhost",9001,"shutdown",request,response)){
        return false;
    }
    return true;
}

bool PandaBody::unlock_brakes(const std::optional<std::string> &ip, const std::string user, const std::string& password){
    disconnect_from_gripper();
    disconnect_from_robot();
    nlohmann::json response;
    nlohmann::json request={
        {"ip",ip.value()},
        {"user",user},
        {"password",password}
    };
    if(!msrm_utils::JsonUDPClient::call_method("localhost",9001,"unlock_brakes",request,response)){
        return false;
    }
    if(!this->connect_to_robot(get_robot_ip(ip))){
        return false;
    }
    if(!this->connect_to_gripper(get_robot_ip(ip))){
        return false;
    }
    return true;
}

bool PandaBody::lock_brakes(const std::optional<std::string> &ip, const std::string user, const std::string& password){

    disconnect_from_gripper();
    disconnect_from_robot();
    nlohmann::json response;
    nlohmann::json request={
        {"ip",ip.value()},
        {"user",user},
        {"password",password}
    };
    if(!msrm_utils::JsonUDPClient::call_method("localhost",9001,"lock_brakes",request,response)){
        return false;
    }
    if(!this->connect_to_robot(get_robot_ip(ip))){
        return false;
    }
    if(!this->connect_to_gripper(get_robot_ip(ip))){
        return false;
    }
    return true;
}

bool PandaBody::move_to_pack_pose(const std::optional<std::string> &ip, const std::string user, const std::string& password){
    disconnect_from_gripper();
    disconnect_from_robot();
    nlohmann::json response;
    nlohmann::json request={
        {"ip",ip.value()},
        {"user",user},
        {"password",password}
    };
    if(!msrm_utils::JsonRPCClient::call_method("localhost",9001,"pack_pose",request,response)){
        return false;
    }
    if(!this->connect_to_robot(get_robot_ip(ip))){
        return false;
    }
    if(!this->connect_to_gripper(get_robot_ip(ip))){
        return false;
    }
    return true;
}

bool PandaBody::grasp(double width, double speed, double force, double epsilon_inner, double epsilon_outer) const{
    if(!m_hand_connected){
        return false;
    }
    try{
        franka::GripperState state = m_panda_hand->readOnce();
        double max_width=state.max_width;
        double current_width=state.width;

        if(width<0 || width>max_width){
            spdlog::error("Gripper cannot reach width of "+std::to_string(width)+". Must be between 0 and "+std::to_string(max_width)+".");
            return false;
        }
        if(width>=current_width){
            spdlog::error("Grasping to a width larger than the current width is not possible.");
            return false;
        }

        if(state.is_grasped){
            spdlog::error("I am already grasping something.");
            return false;
        }
        return this->m_panda_hand->grasp(width,speed,force,epsilon_inner,epsilon_outer);
    }catch(franka::CommandException& e){
        spdlog::debug(e.what());
        return false;
    }catch(franka::NetworkException& e){
        spdlog::debug(e.what());
        return false;
    }catch(franka::InvalidOperationException& e){
        spdlog::debug(e.what());
        return false;
    }
}

bool PandaBody::move_to_finger_position(double width, double speed) const{
    if(!m_hand_connected){
        return false;
    }
    try{
        franka::GripperState state = m_panda_hand->readOnce();
        double max_width=state.max_width;

        if(width<0 || width>max_width){
            spdlog::error("Gripper cannot reach width of "+std::to_string(width)+". Must be between 0 and "+std::to_string(max_width)+".");
            return false;
        }
        return this->m_panda_hand->move(width,speed);
    }catch(franka::CommandException& e){
        spdlog::debug(e.what());
        return false;
    }catch(franka::NetworkException& e){
        spdlog::debug(e.what());
        return false;
    }catch(franka::InvalidOperationException& e){
        spdlog::debug(e.what());
        return false;
    }
}

bool PandaBody::home_gripper() const{
    if(!m_hand_connected){
        return false;
    }
    try{
        return this->m_panda_hand->homing();
    }catch(franka::CommandException& e){
        spdlog::debug(e.what());
        return false;
    }catch(franka::NetworkException& e){
        spdlog::debug(e.what());
        return false;
    }
}

void PandaBody::get_default_robot_state(franka::RobotState &state) const{
    state.robot_mode=franka::RobotMode::kIdle;
}

void PandaBody::get_default_gripper_state(franka::GripperState &state) const{

}

}
