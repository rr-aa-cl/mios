#include "panda/panda_body.hpp"
#include <spdlog/spdlog.h>
#include <msrm_utils/network.hpp>

#include <franka/exception.h>

namespace mios {


std::optional<std::string> PandaBody::get_robot_ip(const std::optional<std::string> last_ip){
    std::optional<std::stirng> new_ip={};
    if(last_ip.has_value()){
        if(msrm_utils::ping(last_ip.value().c_str())==false){
            spdlog::warn("IP was set to "+last_ip.value()+" but no device has been found. Searching for new connection...");
        }else{
            if(!is_robot(last_ip.value())){
                spdlog::warn("IP was set to "+last_ip.value()+" but no compatible robot seems to be connected. Searching for new connection...");
                last_ip={};
            }
        }
    }
    if(new_ip.has_value()){
        new_ip=this->find_robot();
    }
    return new_ip;
}

bool PandaBody::connect_to_robot(const std::string& ip){
    try{
        m_panda_arm = std::make_unique<franka::Robot>(ip);
        m_panda_model = std::make_unique<franka::Model>(m_panda_arm->loadModel());
        return true;
    }catch(const franka::NetworkException& e){
        spdlog::debug(e.what());
        spdlog::error("Cannot connect to robot at IP "+ip);
        return false;
    }catch(const franka::IncompatibleVersionException& e){
        spdlog::debug(e.what());
        spdlog::error("Panda: Detected incompatible version on robot at IP "+ip);
        return false;
    }catch(const franka::ModelException& e){
        spdlog::debug(e.what());
        spdlog::error("Panda: Model could not be loaded.");
        return false;
    }
}

bool PandaBody::connect_to_gripper(const std::string &ip){
    try{
        m_panda_hand = std::make_unique<franka::Gripper>(ip);
    }catch(const franka::NetworkException& e){
        spdlog::debug(e.what());
        spdlog::error("Can not connect to gripper at IP " + ip);
        return false;
    }catch(const franka::IncompatibleVersionException& e){
        spdlog::debug(e.what());
        spdlog::error("Panda: Detected incompatible version on robot at IP "+ip);
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
    if(m_arm_connected){
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

bool PandaBody::pre_run_checks(){
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

bool PandaBody::torque_control(std::functional<franka::Torques (const franka::RobotState &)> controller_callback){
    if(m_arm_connected){
        try{
            m_panda_arm->control(controller_callback);
            return true;
        }catch(const franka::ControlException& e){
            spdlog::debug(e.what());
        }
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
        return false;
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
        return false;
    }
}

const std::unique_ptr<franka::Model>& PandaBody::get_panda_model() const{
    return m_panda_model;
}

}
