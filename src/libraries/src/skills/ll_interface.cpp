#include "mios/skills/ll_interface.hpp"
#include "mios/strategies/move_to_joint_pose.hpp"
#include "mios/strategies/move_to_pose.hpp"
#include "mios/strategies/idle_strategy.hpp"
#include "mios/strategies/cart_compliance_strategy.hpp"
#include "mios/strategies/joint_compliance_strategy.hpp"
#include "mios/strategies/remote_twist_strategy.hpp"
#include "mios/strategies/remote_cart_pose_strategy.hpp"
#include "mios/strategies/remote_wrench_strategy.hpp"
#include "mios/strategies/remote_joint_pose_strategy.hpp"
#include "mios/strategies/remote_torque_strategy.hpp"
#include "mios/strategies/ff_strategy.hpp"

#include "mirmi_cpp_utils/math/math.hpp"

namespace mios{

using Params=SkillParametersLLInterface;

bool SkillParametersLLInterface::from_json(const nlohmann::json &parameters){
    if(!mirmi_utils::read_json_param(parameters,"multicast",multicast)){
        multicast=false;
    }
    if(!mirmi_utils::read_json_param(parameters, "host", host)){
        host.reset();
    }
    if(!mirmi_utils::read_json_param(parameters, "multicast_ip", multicast_ip)){
        multicast_ip = "255.0.0.1";
    }
    if(!mirmi_utils::read_json_param(parameters,"ip_dst",ip_dst)){
        spdlog::error("Missing parameter: ip_dst");
        return false;
    }
    if(!mirmi_utils::read_json_param(parameters,"port_dst",port_dst)){
        spdlog::error("Missing parameter: port_dst");
        return false;
    }
    if(!mirmi_utils::read_json_param(parameters,"port_src",port_src)){
        spdlog::error("Missing parameter: port_src");
        return false;
    }
    if(!mirmi_utils::read_json_param(parameters,"remote_event_protocol",remote_event_protocol)){
        remote_event_protocol="udp";
    }
    if(!mirmi_utils::read_json_param(parameters,"terminate_when_loc",terminate_when_loc)){
        terminate_when_loc=false;
    }
    std::string LLInterface_mode;
    if(!mirmi_utils::read_json_param(parameters,"LLInterface_mode",LLInterface_mode)){
        spdlog::error("Missing parameter: LLInterface_mode");
        return false;
    }
    if(LLInterface_mode=="Twist"){
        mode=LLInterfaceMode::llTwist;
    }else if(LLInterface_mode=="Wrench"){
        mode=LLInterfaceMode::llWrench;
    }else if(LLInterface_mode=="Torque"){
        mode=LLInterfaceMode::llTorque;
    }else if(LLInterface_mode=="CartPose"){
        mode=LLInterfaceMode::llCartPose;
    }else if(LLInterface_mode=="JointPose"){
        mode=LLInterfaceMode::llJointPose;
    }else{
        spdlog::error("Invalid LowLevelInterface mode.");
        return false;
    }

    if(parameters.find("twist")!=parameters.end() && mode==LLInterfaceMode::llTwist){
        if(!mirmi_utils::read_json_param(parameters["twist"],"static_frame",static_frame)){
            static_frame=false;
        }
    }

    if(multicast){
        if(std::stoi(multicast_ip.substr(0,3)) < 224 && std::stoi(multicast_ip.substr(0,3)) > 239){
            spdlog::error("Multicast IP "+multicast_ip+" is not within the range 224.0.0.1 to 239.255.255.255");
            return false;
        }
    }

    return true;
}

std::map<std::string,std::set<std::string> > SkillParametersLLInterface::get_parameter_list(){
    return {{"ip_dst",{}},{"port_dst",{}},{"host",{}},{"multicast_ip",{}},{"port_src",{}},{"remote_event_protocol",{}},{"terminate_when_loc",{}},{"multicast",{}},{"multicast_group",{}},{"LLInterface_mode",{}},
        {"twist",{"static_frame"}}};
}

LLInterface::LLInterface(const std::string &name, Memory *memory, Portal *portal):Skill("LLInterface",{},name,memory,portal,
{ControlMode::mCartTorque,ControlMode::mJointTorque,ControlMode::mCartVelocity,ControlMode::mJointVelocity}),m_handshake_stage(0){
    m_memory->remove_event("init_done");
    m_previous_payload.assign(6,0);
}

LLInterface::~LLInterface(){
    if(read_parameters<Params>()->mode==LLInterfaceMode::llCartPose){
        m_portal->close_udp_instream("remote_cart_pose_in");
    }
    if(read_parameters<Params>()->mode==LLInterfaceMode::llJointPose){
        m_portal->close_udp_instream("remote_joint_pose_in");
    }
    if(read_parameters<Params>()->mode==LLInterfaceMode::llTwist){
        m_portal->close_udp_instream("remote_twist_in");
    }
        if(read_parameters<Params>()->mode==LLInterfaceMode::llTorque){
        m_portal->close_udp_instream("remote_torque_in");
    }
        if(read_parameters<Params>()->mode==LLInterfaceMode::llWrench){
        m_portal->close_udp_instream("remote_wrench_in");
    }
}

std::shared_ptr<ManipulationPrimitive> LLInterface::get_initial_mp(const Percept &p_0){
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("handshake",p_0);
    nlohmann::json response;
    mp->create_strategy<IdleStrategy>("idle",1);
    return mp;
}

std::optional<std::shared_ptr<ManipulationPrimitive> > LLInterface::graph_transition(const Percept &p){
    if(get_active_mp()->get_name()=="handshake"){
        spdlog::debug("LLInterface: waiting for handshake");
        if(m_memory->get_event("handshake")!=nullptr){
            spdlog::debug("LLInterface: Received handshake (slave)");
            std::shared_ptr<ManipulationPrimitive> mp = create_mp("receive",p);
            mirmi_utils::read_json_param<double,7,1>(m_memory->get_event("handshake")->get_content(),"q_init",m_q_init);
            mp->create_strategy<MoveToJointPoseStrategy>("initial_move",1);
            mp->get_strategy<MoveToJointPoseStrategy>("initial_move")->set_goal(m_q_init,0.5,2);
            m_memory->remove_event("handshake");
            return mp;
        }
        else{
            return {};
        }
    }
    if(get_active_mp()->get_name()=="receive"){
        if(get_active_mp()->get_strategy_interface("initial_move")->finished()){
            spdlog::debug("LL_interface::graph_transition()  initial move succeded.");
            if(read_parameters<Params>()->mode==LLInterfaceMode::llJointPose && (m_q_init-p.proprioception.q).norm()>0.1){
                spdlog::error("The init pose not reached after handshake.");
                invoke_failure();
                return {};
            }
            nlohmann::json response;
            if(m_handshake_stage==0){
                spdlog::debug("LLInterface: Sending init_done (slave)");
                m_handshake_message_uuid=m_portal->send_message(read_parameters<Params>()->ip_dst,read_parameters<Params>()->port_dst,"post_event",{{"name","init_done"}},read_parameters<Params>()->remote_event_protocol,5,true);
                m_handshake_stage++;
            }
            if(m_handshake_stage!=1){
                return{};
            }
            std::shared_ptr<ManipulationPrimitive> mp = create_mp("LLInterface",p);
            if(read_parameters<Params>()->mode==LLInterfaceMode::llCartPose){
                mp->create_strategy<RemoteCartPoseStrategy>("LLInterface",1);
                if(!mp->get_strategy<RemoteCartPoseStrategy>("LLInterface")->connect(m_portal,"remote_cart_pose_in",get_parameters<Params>()->port_src,256,3,10000,20,read_parameters<Params>()->multicast, read_parameters<Params>()->host, read_parameters<Params>()->multicast_ip)){
                    spdlog::error("Could not open incoming udp channel.");
                    //return{};
                    throw SkillException();
                }
            }
            if(read_parameters<Params>()->mode==LLInterfaceMode::llJointPose){
                mp->create_strategy<RemoteJointPoseStrategy>("LLInterface",1);
                if(!mp->get_strategy<RemoteJointPoseStrategy>("LLInterface")->connect(m_portal,"remote_joint_pose_in",get_parameters<Params>()->port_src,256,3,10000,20,read_parameters<Params>()->multicast, read_parameters<Params>()->host, read_parameters<Params>()->multicast_ip)){
                    spdlog::error("Could not open incoming udp channel.");
                    //return{};
                    throw SkillException();
                    
                }
            }
            if(read_parameters<Params>()->mode==LLInterfaceMode::llTwist){
                mp->create_strategy<RemoteTwistStrategy>("LLInterface",1);
                if(!mp->get_strategy<RemoteTwistStrategy>("LLInterface")->connect(m_portal,"remote_twist_in",get_parameters<Params>()->port_src,256,3,10000,200,read_parameters<Params>()->multicast, read_parameters<Params>()->host, read_parameters<Params>()->multicast_ip)){
                    spdlog::error("Could not open incoming udp channel.");
                    //return{};
                    throw SkillException();
                }
            }
            if(read_parameters<Params>()->mode==LLInterfaceMode::llTorque){
                mp->create_strategy<RemoteTorqueStrategy>("LLInterface",1);
                if (0){
                    mp->get_strategy<RemoteTorqueStrategy>("LLInterface")->StartDSInterpolation();
                }
                if(!mp->get_strategy<RemoteTorqueStrategy>("LLInterface")->connect(m_portal,"remote_torque_in",get_parameters<Params>()->port_src,256,3,10000,200,read_parameters<Params>()->multicast, read_parameters<Params>()->host, read_parameters<Params>()->multicast_ip)){
                    spdlog::error("Could not open incoming udp channel.");
                    //return{};
                    throw SkillException();
                }
            }
            if(read_parameters<Params>()->mode==LLInterfaceMode::llWrench){
                mp->create_strategy<RemoteWrenchStrategy>("LLInterface",1);
                if(!mp->get_strategy<RemoteWrenchStrategy>("LLInterface")->connect(m_portal,"remote_wrench_in",get_parameters<Params>()->port_src,256,3,10000,200,read_parameters<Params>()->multicast, read_parameters<Params>()->host, read_parameters<Params>()->multicast_ip)){
                    spdlog::error("Could not open incoming udp channel.");
                    //return{};
                    throw SkillException();
                }
            }
            return mp;
        }
    }
    if(get_active_mp()->get_name()=="LLInterface"){
        if(get_active_mp()->get_strategy_interface("LLInterface")->finished()){
            if(read_parameters<Params>()->terminate_when_loc){
                invoke_failure();
            }
            m_handshake_stage=0;
            spdlog::debug("LLInterface: Terminating LLInterface (slave)");
            std::shared_ptr<ManipulationPrimitive> mp = create_mp("handshake",p);
            if(read_parameters<Params>()->mode==LLInterfaceMode::llCartPose){
                m_portal->close_udp_instream("remote_cart_pose_in");
            }
            if(read_parameters<Params>()->mode==LLInterfaceMode::llJointPose){
                m_portal->close_udp_instream("remote_joint_pose_in");
            }
            if(read_parameters<Params>()->mode==LLInterfaceMode::llTwist){
                m_portal->close_udp_instream("remote_twist_in");
            }
            if(read_parameters<Params>()->mode==LLInterfaceMode::llTorque){
                m_portal->close_udp_instream("remote_torque_in");
            }
            if(read_parameters<Params>()->mode==LLInterfaceMode::llWrench){
                m_portal->close_udp_instream("remote_wrench_in");
            }
            nlohmann::json response;
            mp->create_strategy<IdleStrategy>("idle",1);
            return mp;
        }
    }
    return {};
}

bool LLInterface::check_local_suc_conditions(const Percept &p){
    return false;
}

}

