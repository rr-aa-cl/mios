#include "panda/panda_body.hpp"
#include <spdlog/spdlog.h>
#include <msrm_utils/network.hpp>
#include <msrm_utils/conversion.hpp>

#include <mutex>
#include <thread>

#include <franka/exception.h>
#include <pybind11/pybind11.h>
#include <pybind11/embed.h>

#include "plugins/conv_vel2pose_wrapper.hpp"

namespace mios {

PandaBody::PandaBody(Memory *memory):m_panda_arm(nullptr),m_panda_model(nullptr),m_panda_hand(nullptr),m_has_arm(false),m_hand(PandaHandNone),m_arm_connected(false),m_hand_connected(false),
m_memory(memory){
    m_robot_state.O_T_EE={1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1};
}

bool PandaBody::initialize(){
    spdlog::trace("PandaBody::initialize()");
    m_has_arm=m_memory->read_parameters()->system.has_robot;
    m_hand=m_memory->read_parameters()->system.gripper;
    m_memory->get_parameters()->system.robot_ip = get_robot_ip(m_memory->read_parameters()->system.robot_ip).value_or("127.0.0.1");

    if(!connect_to_robot(m_memory->read_parameters()->system.robot_ip)){
        return false;
    }
    if(!connect_to_gripper(m_memory->read_parameters()->system.robot_ip)){
        return false;
    }
    load_gripper_configuration();
    if(!set_robot_parameters()){
        spdlog::warn("Could not set robot parameters in current mode.");
    }
    return true;
}

std::optional<std::string> PandaBody::get_robot_ip(const std::optional<std::string>& last_ip){
    spdlog::trace("PandaBody::get_robot_ip()");
    if(!m_has_arm && m_hand!=PandaHandDefault){
        return {};
    }
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

void PandaBody::load_gripper_configuration(){
    spdlog::trace("PandaBody::load_gripper_configuration()");
    if(m_hand==PandaHandDefault){
        m_memory->get_parameters()->frames.F_T_EE<<0.7071,-0.7071,0,0,0.7071,0.7071,0,0,0,0,1,0,0,0,0.1034,1;
        m_memory->get_parameters()->frames.F_T_EE.transposeInPlace();
    }
    if(m_hand==PandaHandSofthand2){
        m_memory->get_parameters()->frames.F_T_EE.setIdentity();
    }
}

bool PandaBody::connect_to_robot(const std::optional<std::string> &ip){
    spdlog::trace("PandaBody::connect_to_robot()");
    if(!m_has_arm){
        m_arm_connected=false;
        return true;
    }
    if(!ip.has_value()){
        m_arm_connected=false;
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
    spdlog::trace("PandaBody::connect_to_gripper()");
    if(m_hand==PandaHandNone){
        m_hand_connected=false;
        return true;
    }
    if(m_hand==PandaHandDefault){
        if(!ip.has_value()){
            m_hand_connected=false;
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
    if(m_hand==PandaHandSofthand2){
        m_softhand2 = std::make_unique<Softhand2>();
        if(!m_softhand2->initialize()){
            return false;
        }else{
            m_hand_connected=true;
            return true;
        }
    }
    return false;
}

void PandaBody::disconnect_from_robot(){
    spdlog::trace("PandaBody::disconnect_from_robot()");
    m_arm_connected=false;
    m_panda_model.release();
    m_panda_arm.release();
}

void PandaBody::disconnect_from_gripper(){
    spdlog::trace("PandaBody::disconnect_from_gripper()");
    m_hand_connected=false;
    if(m_hand==PandaHandDefault){
        m_panda_hand.release();
    }
    if(m_hand==PandaHandSofthand2){
        m_softhand2.release();
    }
}

bool PandaBody::recover(){
    spdlog::trace("PandaBody::recover()");
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
    spdlog::trace("PandaBody::pre_run_checks()");
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
    spdlog::trace("PandaBody::is_robot()");
    try{
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
    spdlog::trace("PandaBody::find_robot()");
    std::optional<std::string> robot_address={};
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

ControlReturnType PandaBody::control(std::function<franka::Torques (const franka::RobotState&,franka::Duration)> controller_callback){
    try{
        if(m_arm_connected){
            spdlog::debug("PandaBody: control<Torques>");
            m_panda_arm->control(controller_callback);
            return ControlReturnType::crtNominal;
        }else{
            dummy_control(controller_callback);
            return ControlReturnType::crtNominal;
        }
    }catch(const franka::ControlException& e){
        spdlog::debug(e.what());
        return ControlReturnType::crtCollision;
    }catch(const franka::InvalidOperationException& e){
        spdlog::debug(e.what());
        return ControlReturnType::crtException;
    }catch(const franka::NetworkException& e){
        spdlog::debug(e.what());
        return ControlReturnType::crtException;
    }catch(const franka::RealtimeException& e){
        spdlog::debug(e.what());
        return ControlReturnType::crtException;
    }catch(const std::invalid_argument& e){
        spdlog::debug(e.what());
        return ControlReturnType::crtException;
    }

}

ControlReturnType PandaBody::control(std::function<franka::CartesianVelocities (const franka::RobotState &,franka::Duration)> controller_callback){
    if(m_arm_connected){
        try{
            spdlog::debug("PandaBody: control<CartesianVelocities>");
            m_panda_arm->control(controller_callback);
            return ControlReturnType::crtNominal;
        }catch(const franka::ControlException& e){
            spdlog::debug(e.what());
            return ControlReturnType::crtCollision;
        }catch(const franka::InvalidOperationException& e){
            spdlog::debug(e.what());
            return ControlReturnType::crtException;
        }catch(const franka::NetworkException& e){
            spdlog::debug(e.what());
            return ControlReturnType::crtException;
        }catch(const franka::RealtimeException& e){
            spdlog::debug(e.what());
            return ControlReturnType::crtException;
        }catch(const std::invalid_argument& e){
            spdlog::debug(e.what());
            return ControlReturnType::crtException;
        }
    }else{
        dummy_control(controller_callback);
        return ControlReturnType::crtNominal;
    }
}

ControlReturnType PandaBody::control(std::function<franka::JointVelocities (const franka::RobotState &,franka::Duration)> controller_callback){
    if(m_arm_connected){
        try{
            spdlog::debug("PandaBody: control<JointVelocities>");
            m_panda_arm->control(controller_callback);
            return ControlReturnType::crtNominal;
        }catch(const franka::ControlException& e){
            spdlog::debug(e.what());
            return ControlReturnType::crtCollision;
        }catch(const franka::InvalidOperationException& e){
            spdlog::debug(e.what());
            return ControlReturnType::crtException;
        }catch(const franka::NetworkException& e){
            spdlog::debug(e.what());
            return ControlReturnType::crtException;
        }catch(const franka::RealtimeException& e){
            spdlog::debug(e.what());
            return ControlReturnType::crtException;
        }catch(const std::invalid_argument& e){
            spdlog::debug(e.what());
            return ControlReturnType::crtException;
        }
    }else{
        dummy_control(controller_callback);
        return ControlReturnType::crtNominal;
    }
}

ControlReturnType PandaBody::control(std::function<franka::CartesianPose (const franka::RobotState &,franka::Duration)> controller_callback){
    if(m_arm_connected){
        try{
            spdlog::debug("PandaBody: control<CartesianPose>");
            m_panda_arm->control(controller_callback);
            return ControlReturnType::crtNominal;
        }catch(const franka::ControlException& e){
            spdlog::debug(e.what());
            return ControlReturnType::crtCollision;
        }catch(const franka::InvalidOperationException& e){
            spdlog::debug(e.what());
            return ControlReturnType::crtException;
        }catch(const franka::NetworkException& e){
            spdlog::debug(e.what());
            return ControlReturnType::crtException;
        }catch(const franka::RealtimeException& e){
            spdlog::debug(e.what());
            return ControlReturnType::crtException;
        }catch(const std::invalid_argument& e){
            spdlog::debug(e.what());
            return ControlReturnType::crtException;
        }
    }else{
        dummy_control(controller_callback);
        return ControlReturnType::crtNominal;
    }
}

ControlReturnType PandaBody::control(std::function<franka::JointPositions (const franka::RobotState &,franka::Duration)> controller_callback){
    if(m_arm_connected){
        try{
            spdlog::debug("PandaBody: control<JointPositions>");
            m_panda_arm->control(controller_callback);
            return ControlReturnType::crtNominal;
        }catch(const franka::ControlException& e){
            spdlog::debug(e.what());
            return ControlReturnType::crtCollision;
        }catch(const franka::InvalidOperationException& e){
            spdlog::debug(e.what());
            return ControlReturnType::crtException;
        }catch(const franka::NetworkException& e){
            spdlog::debug(e.what());
            return ControlReturnType::crtException;
        }catch(const franka::RealtimeException& e){
            spdlog::debug(e.what());
            return ControlReturnType::crtException;
        }catch(const std::invalid_argument& e){
            spdlog::debug(e.what());
            return ControlReturnType::crtException;
        }
    }else{
        dummy_control(controller_callback);
        return ControlReturnType::crtNominal;
    }
}

void PandaBody::dummy_control(std::function<franka::Torques (const franka::RobotState &,franka::Duration)> controller_callback){
    franka::Torques tau_J={0,0,0,0,0,0,0};

    m_robot_state.K_F_ext_hat_K={0,0,0,0,0,0};
    m_robot_state.O_F_ext_hat_K={0,0,0,0,0,0};
    m_robot_state.tau_ext_hat_filtered={0,0,0,0,0,0,0};
    m_robot_state.dq={0,0,0,0,0,0,0};
    std::chrono::high_resolution_clock::time_point t_0;
    franka::Duration duration(std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::high_resolution_clock::now()-t_0));
    while(!tau_J.motion_finished){
        auto t_s_start = std::chrono::system_clock::now();
        tau_J=controller_callback(m_robot_state,duration);
        auto t_s_end = std::chrono::system_clock::now();
        double t=std::chrono::duration_cast<std::chrono::microseconds>(t_s_end-t_s_start).count();
        duration=franka::Duration(t);
        std::this_thread::sleep_for(std::chrono::microseconds(1000-static_cast<int>(t)));
    }
}

void PandaBody::dummy_control(std::function<franka::CartesianVelocities (const franka::RobotState &,franka::Duration)> controller_callback){
    franka::CartesianVelocities dX_d={0,0,0,0,0,0};
    m_robot_state.K_F_ext_hat_K={0,0,0,0,0,0};
    m_robot_state.O_F_ext_hat_K={0,0,0,0,0,0};
    m_robot_state.tau_ext_hat_filtered={0,0,0,0,0,0,0};
    m_robot_state.dq={0,0,0,0,0,0,0};
    std::chrono::high_resolution_clock::time_point t_0;
    franka::Duration duration(std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::high_resolution_clock::now()-t_0));
    conv_vel2pose::conv_vel2pose conv;
    conv.u.TF_T_EE=Eigen::Matrix<double,4,4>(m_robot_state.O_T_EE.data());
    conv.u.TF_dX_d.setZero();
    conv.initialize();
    while(!dX_d.motion_finished){
        auto t_s_start = std::chrono::system_clock::now();
        dX_d=controller_callback(m_robot_state,duration);
        conv.u.TF_T_EE=Eigen::Matrix<double,4,4>(m_robot_state.O_T_EE.data());
        conv.u.TF_dX_d=Eigen::Matrix<double,6,1>(dX_d.O_dP_EE.data());
        conv.step();
        m_robot_state.O_T_EE=msrm_utils::convert_to_array<double,4,4>(conv.y.TF_T_EE_d);
        auto t_s_end = std::chrono::system_clock::now();
        double t=std::chrono::duration_cast<std::chrono::microseconds>(t_s_end-t_s_start).count();
        duration=franka::Duration(t);
        std::this_thread::sleep_for(std::chrono::microseconds(1000-static_cast<int>(t)));
    }
    conv.terminate();
}

void PandaBody::dummy_control(std::function<franka::JointVelocities (const franka::RobotState &,franka::Duration)> controller_callback){
    franka::JointVelocities dq_d={0,0,0,0,0,0,0};
    m_robot_state.K_F_ext_hat_K={0,0,0,0,0,0};
    m_robot_state.O_F_ext_hat_K={0,0,0,0,0,0};
    m_robot_state.tau_ext_hat_filtered={0,0,0,0,0,0,0};
    m_robot_state.dq={0,0,0,0,0,0,0};
    std::chrono::high_resolution_clock::time_point t_0;
    franka::Duration duration(std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::high_resolution_clock::now()-t_0));
    while(!dq_d.motion_finished){
        auto t_s_start = std::chrono::system_clock::now();
        dq_d=controller_callback(m_robot_state,duration);
        for(unsigned i=0;i<7;i++){
            m_robot_state.q[i]+=dq_d.dq[i]*0.001;
        }
        m_robot_state.dq=dq_d.dq;
        auto t_s_end = std::chrono::system_clock::now();
        double t=std::chrono::duration_cast<std::chrono::microseconds>(t_s_end-t_s_start).count();
        duration=franka::Duration(t);
        std::this_thread::sleep_for(std::chrono::microseconds(1000-static_cast<int>(t)));
    }
}

void PandaBody::dummy_control(std::function<franka::CartesianPose (const franka::RobotState &,franka::Duration)> controller_callback){
    franka::CartesianPose O_T_EE_d={1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1};
    m_robot_state.K_F_ext_hat_K={0,0,0,0,0,0};
    m_robot_state.O_F_ext_hat_K={0,0,0,0,0,0};
    m_robot_state.tau_ext_hat_filtered={0,0,0,0,0,0,0};
    m_robot_state.dq={0,0,0,0,0,0,0};
    std::chrono::high_resolution_clock::time_point t_0;
    franka::Duration duration(std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::high_resolution_clock::now()-t_0));
    while(!O_T_EE_d.motion_finished){
        auto t_s_start = std::chrono::system_clock::now();
        O_T_EE_d=controller_callback(m_robot_state,duration);
        m_robot_state.O_T_EE=O_T_EE_d.O_T_EE;
        auto t_s_end = std::chrono::system_clock::now();
        double t=std::chrono::duration_cast<std::chrono::microseconds>(t_s_end-t_s_start).count();
        duration=franka::Duration(t);
        std::this_thread::sleep_for(std::chrono::microseconds(1000-static_cast<int>(t)));
    }
}

void PandaBody::dummy_control(std::function<franka::JointPositions (const franka::RobotState &,franka::Duration)> controller_callback){
    franka::JointPositions q_d={0,0,0,0,0,0,0};
    franka::RobotState m_robot_state;
    m_robot_state.K_F_ext_hat_K={0,0,0,0,0,0};
    m_robot_state.O_F_ext_hat_K={0,0,0,0,0,0};
    m_robot_state.tau_ext_hat_filtered={0,0,0,0,0,0,0};
    m_robot_state.dq={0,0,0,0,0,0,0};
    std::chrono::high_resolution_clock::time_point t_0;
    franka::Duration duration(std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::high_resolution_clock::now()-t_0));
    while(!q_d.motion_finished){
        auto t_s_start = std::chrono::system_clock::now();
        q_d=controller_callback(m_robot_state,duration);
        m_robot_state.q=q_d.q;
        auto t_s_end = std::chrono::system_clock::now();
        double t=std::chrono::duration_cast<std::chrono::microseconds>(t_s_end-t_s_start).count();
        duration=franka::Duration(t);
        std::this_thread::sleep_for(std::chrono::microseconds(1000-static_cast<int>(t)));
    }
}

bool PandaBody::set_robot_parameters(){
    if(!m_arm_connected){
        return true;
    }
    ControlParameters control= m_memory->read_parameters()->control;
    UserParameters user= m_memory->read_parameters()->user;
    FramesParameters frames =m_memory->read_parameters()->frames;

    std::array<double,3> load_com = msrm_utils::convert_to_array<double,3,1>(user.load_com);
    std::array<double,9> load_I = msrm_utils::convert_to_array<double,3,3>(user.load_I);
    std::array<double,7> tau_ext_contact = msrm_utils::convert_to_array<double,7,1>(user.tau_ext_contact);
    std::array<double,7> tau_ext_max = msrm_utils::convert_to_array<double,7,1>(user.tau_ext_max);
    std::array<double,6> F_ext_K_contact = {user.F_ext_contact(0),user.F_ext_contact(0),user.F_ext_contact(0),user.F_ext_contact(1),user.F_ext_contact(1),user.F_ext_contact(1)};
    std::array<double,6> F_ext_K_max = {user.F_ext_max(0),user.F_ext_max(0),user.F_ext_max(0),user.F_ext_max(1),user.F_ext_max(1),user.F_ext_max(1)};
    std::array<double,16> EE_T_K = msrm_utils::convert_to_array<double,4,4>(frames.EE_T_K);
    std::array<double,7> K_theta = msrm_utils::convert_to_array<double,7,1>(control.joint_imp.K_theta);
    std::array<double,6> K_x = msrm_utils::convert_to_array<double,6,1>(control.cart_imp.K_x);
    std::array<double,16> NE_T_TCP = msrm_utils::convert_to_array<double,4,4>(frames.EE_T_TCP);

    try{
        m_panda_arm->setLoad(user.load_m,load_com,load_I);
        m_panda_arm->setEE(NE_T_TCP);
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
    if(m_hand_connected && m_hand==PandaHandDefault){
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

    bool result;
    try{
        pybind11::module desk_client = pybind11::module::import("desk_client");
        pybind11::object py_result = desk_client.attr("start_task")(ip.value(), user, password, task);
        result = py_result.cast<bool>();
    }catch(const pybind11::error_already_set& e){
        spdlog::debug(e.what());
        spdlog::warn("Cannot start desk task, error when calling the python desk client.");
        result=false;
    }

    if(result){
        wait_for_desk_task(ip,user,password);
    }

    if(!this->connect_to_robot(get_robot_ip(ip))){
        return false;
    }
    if(!this->connect_to_gripper(get_robot_ip(ip))){
        return false;
    }
    return true;
}

bool PandaBody::stop_desk_task(const std::optional<std::string> &ip, const std::string user, const std::string& password){
    nlohmann::json response;
    bool result;
    try{
        pybind11::module desk_client = pybind11::module::import("desk_client");
        pybind11::object py_result = desk_client.attr("stop_task")(ip.value(), user, password);
        result = py_result.cast<bool>();
    }catch(const pybind11::error_already_set& e){
        spdlog::debug(e.what());
        spdlog::warn("Cannot stop desk task, error when calling the python desk client.");
        result=false;
    }
    return result;
}

void PandaBody::wait_for_desk_task(const std::optional<std::string> &ip, const std::string user, const std::string& password){
    bool result;
    try{
        pybind11::module desk_client = pybind11::module::import("desk_client");
        while(true){
            pybind11::object py_result = desk_client.attr("is_busy")(ip.value(), user, password);
            result = py_result.cast<bool>();
            if(result){
                return;
            }else{
                std::this_thread::sleep_for(std::chrono::milliseconds(100));
            }
        }
    }catch(const pybind11::error_already_set& e){
        spdlog::debug(e.what());
        spdlog::warn("Cannot wait for desk task, error when calling the python desk client.");
        result=false;
        return;
    }
}

bool PandaBody::shutdown_robot(const std::optional<std::string> &ip, const std::string user, const std::string& password){
    disconnect_from_gripper();
    disconnect_from_robot();

    bool result;
    try{
        pybind11::module desk_client = pybind11::module::import("desk_client");
        pybind11::object py_result = desk_client.attr("shutdown")(ip.value(), user, password);
        result = py_result.cast<bool>();
    }catch(const pybind11::error_already_set& e){
        spdlog::debug(e.what());
        spdlog::warn("Cannot shutdown, error when calling the python desk client.");
        result=false;
    }
    return result;
}

bool PandaBody::unlock_brakes(const std::optional<std::string> &ip, const std::string user, const std::string& password){

    bool result;
    try{
        pybind11::module desk_client = pybind11::module::import("desk_client");
        pybind11::object py_result = desk_client.attr("unlock_brakes")(ip.value(), user, password);
        result = py_result.cast<bool>();
    }catch(const pybind11::error_already_set& e){
        spdlog::debug(e.what());
        spdlog::warn("Cannot unlock brakes, error when calling the python desk client.");
        result=false;
    }

    return result;
}

bool PandaBody::lock_brakes(const std::optional<std::string> &ip, const std::string user, const std::string& password){

    bool result;
    try{
        pybind11::module desk_client = pybind11::module::import("desk_client");
        pybind11::object py_result = desk_client.attr("lock_brakes")(ip.value(), user, password);
        result = py_result.cast<bool>();
    }catch(const pybind11::error_already_set& e){
        spdlog::debug(e.what());
        spdlog::warn("Cannot lock brakes, error when calling the python desk client.");
        result=false;
    }
    return result;
}

bool PandaBody::move_to_pack_pose(const std::optional<std::string> &ip, const std::string user, const std::string& password){
    disconnect_from_gripper();
    disconnect_from_robot();

    bool result;
    try{
        pybind11::module desk_client = pybind11::module::import("desk_client");
        pybind11::object py_result = desk_client.attr("pack_pose")(ip.value(), user, password);
        result = py_result.cast<bool>();
    }catch(const pybind11::error_already_set& e){
        spdlog::debug(e.what());
        spdlog::warn("Cannot move to pack pose, error when calling the python desk client.");
        result=false;
    }

    if(!this->connect_to_robot(get_robot_ip(ip))){
        return false;
    }
    if(!this->connect_to_gripper(get_robot_ip(ip))){
        return false;
    }
    return result;
}

bool PandaBody::grasp(double width, double speed, double force, double epsilon_inner, double epsilon_outer) const{
    std::scoped_lock<std::mutex> lock(m_mtx_hand_active);
    if(!m_hand_connected){
        spdlog::error("No gripper connected.");
        return false;
    }
    if(m_hand==PandaHandDefault){
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
                spdlog::debug("Current width is " + std::to_string(current_width) + ", desired width is " + std::to_string(width));
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
    if(m_hand==PandaHandSofthand2){
        return m_softhand2->move(width);
    }
    return false;
}

bool PandaBody::move_to_finger_position(double width, double speed) const{
    std::scoped_lock<std::mutex> lock(m_mtx_hand_active);
    if(!m_hand_connected){
        return false;
    }
    if(m_hand==PandaHandDefault){

        try{
            franka::GripperState state = m_panda_hand->readOnce();
            double max_width=state.max_width;

            if(width<0 || width>max_width){
                spdlog::warn("Gripper cannot reach width of "+std::to_string(width)+". Must be between 0 and "+std::to_string(max_width)+".");
                if(width<0){
                    width=0;
                }
                if(width>max_width){
                    width=max_width;
                }
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
    if(m_hand==PandaHandSofthand2){
        return m_softhand2->move(width);
    }
    return false;
}

bool PandaBody::stop_gripper(){
//    std::scoped_lock<std::mutex> lock(m_mtx_hand_active);
    if(!m_hand_connected){
        return false;
    }
    if(m_hand==PandaHandDefault){
        try{
            return this->m_panda_hand->stop();
        }catch(franka::CommandException& e){
            spdlog::debug(e.what());
            return false;
        }catch(franka::NetworkException& e){
            spdlog::debug(e.what());
            return false;
        }
    }
    if(m_hand==PandaHandSofthand2){
        return true;
    }
    return false;
}

bool PandaBody::home_gripper() const{
    std::scoped_lock<std::mutex> lock(m_mtx_hand_active);
    if(!m_hand_connected){
        return false;
    }
    if(m_hand==PandaHandDefault){

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
    if(m_hand==PandaHandSofthand2){
        return true;
    }
    return false;
}

bool PandaBody::is_hand_active(){
    if(m_mtx_hand_active.try_lock()){
        m_mtx_hand_active.unlock();
        return false;
    }else{
        return true;
    }
}

void PandaBody::get_default_robot_state(franka::RobotState &state) const{
    state=m_robot_state;
    state.robot_mode=franka::RobotMode::kIdle;
}

void PandaBody::get_default_gripper_state(franka::GripperState &state) const{
    state=m_gripper_state;
}

}
