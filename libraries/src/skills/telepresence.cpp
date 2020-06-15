#include "skills/telepresence.hpp"
#include "strategies/move_to_joint_pose.hpp"
#include "strategies/move_to_pose.hpp"
#include "strategies/null_strategy.hpp"
#include "strategies/remote_twist_strategy.hpp"
#include "strategies/remote_wrench_strategy.hpp"

namespace mios{

using Params=SkillParametersTelepresence;

bool SkillParametersTelepresence::from_json(const nlohmann::json &parameters){
    return true;
}

Telepresence::Telepresence(const std::string &name, Memory *memory, Portal *portal, const Percept &p):Skill("Telepresence",{},name,memory,portal,p){
    if(read_parameters<Params>()->master){
        if(read_parameters<Params>()->mode==TelepresenceMode::tmJoystick){
            m_udp_sender = portal->open_udp_outstream("remote_twist_out",read_parameters<Params>()->peer_ip,read_parameters<Params>()->port_dst);
        }
    }else{
        if(read_parameters<Params>()->mode==TelepresenceMode::tmJoystick){
            m_udp_sender = portal->open_udp_outstream("remote_force_out",read_parameters<Params>()->peer_ip,read_parameters<Params>()->port_dst);
        }
    }
    if(!m_udp_sender->connect()){
        throw SkillException("Could not connect to peer");
    }

}

std::shared_ptr<ManipulationPrimitive> Telepresence::get_initial_mp(const Percept &p_0){
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("handshake",p_0);
    nlohmann::json response;
    mp->create_strategy<NullStrategy>("idle",1);
    return mp;
}

std::optional<std::shared_ptr<ManipulationPrimitive> > Telepresence::graph_transition(const Percept &p){
    if(read_parameters<Params>()->master){
        if(get_active_mp()->get_name()=="handshake"){
            nlohmann::json response,request;
            request["name"]="handshake";
            request["content"]=nlohmann::json();
            if(read_parameters<Params>()->mode==TelepresenceMode::tmDirectCart){
                request["content"]["O_T_EE_master"]=msrm_utils::from_eigen<double,4,4>(p.proprioception.O_T_EE);
            }
            if(read_parameters<Params>()->mode==TelepresenceMode::tmDirectJoint){
                request["content"]["q_master"]=msrm_utils::from_eigen<double,7,1>(p.proprioception.q);
            }
            if(m_handshake_stage==0){
                m_handshake_message_uuid=m_portal->send_message(read_parameters<Params>()->peer_ip,12002,"post_event",request);
                m_handshake_stage=1;
            }
            if(m_handshake_stage==1){
                nlohmann::json response = m_portal->get_message_response(m_handshake_message_uuid);
                if(response.is_boolean()){
                    m_handshake_stage=0;
                    return {};
                }else if(response.is_null()){
                    return {};
                }else{
                    m_handshake_stage=2;
                }
            }
            if(m_handshake_stage==2){
                if(m_memory->get_event("sync_done")!=nullptr){
                    m_memory->remove_event("sync_done");
                    std::shared_ptr<ManipulationPrimitive> mp = create_mp("telepresence",p);
                    if(read_parameters<Params>()->mode==TelepresenceMode::tmDirectCart){

                    }
                    if(read_parameters<Params>()->mode==TelepresenceMode::tmDirectJoint){

                    }
                    if(read_parameters<Params>()->mode==TelepresenceMode::tmJoystick){
                        mp->create_strategy<RemoteWrenchStrategy>("telepresence",1);
                        mp->get_strategy<RemoteWrenchStrategy>("telepresence")->connect(m_portal,"remote_wrench_in",get_parameters<Params>()->port_src,256,0,10000,200);
                    }
                    return mp;
                }
            }
        }
        if(get_active_mp()->get_name()=="telepresence"){
            if(get_active_mp()->get_strategy_interface("telepresence")->finished()){
                m_handshake_stage=0;
                std::shared_ptr<ManipulationPrimitive> mp = create_mp("handshake",p);
                nlohmann::json response;
                mp->create_strategy<NullStrategy>("idle",1);
                return mp;
            }
        }
    }else{
        if(get_active_mp()->get_name()=="handshake"){
            if(m_memory->get_event("handshake")!=nullptr){
                std::shared_ptr<ManipulationPrimitive> mp = create_mp("sync",p);
                if(read_parameters<Params>()->mode==TelepresenceMode::tmDirectCart){
                    Eigen::Matrix<double,4,4> O_T_EE_master;
                    Eigen::Matrix<double,2,1> speed, acc;
                    speed<<0.1,0.5;
                    acc<<0.5,1;
                    msrm_utils::read_json_param<double,4,4>(m_memory->get_event("handshake")->get_content(),"O_T_EE_master",O_T_EE_master);
                    mp->create_strategy<MoveToPoseStrategy>("move",1);
                    mp->get_strategy<MoveToPoseStrategy>("move")->set_goal(O_T_EE_master,speed,acc);
                }
                if(read_parameters<Params>()->mode==TelepresenceMode::tmDirectJoint){
                    Eigen::Matrix<double,7,1> q_master;
                    msrm_utils::read_json_param<double,7,1>(m_memory->get_event("handshake")->get_content(),"q_master",q_master);
                    mp->create_strategy<MoveToJointPoseStrategy>("move",1);
                    mp->get_strategy<MoveToJointPoseStrategy>("move")->set_goal(q_master,0.5,2);
                }
                if(read_parameters<Params>()->mode==TelepresenceMode::tmJoystick){
                    mp->create_strategy<NullStrategy>("move",1);
                }
                m_memory->remove_event("handshake");
                return mp;
            }
            else{
                return {};
            }
        }
        if(get_active_mp()->get_name()=="sync"){
            if(get_active_mp()->get_strategy_interface("move")->finished()){
                std::shared_ptr<ManipulationPrimitive> mp = create_mp("telepresence",p);
                if(read_parameters<Params>()->mode==TelepresenceMode::tmDirectCart){

                }
                if(read_parameters<Params>()->mode==TelepresenceMode::tmDirectJoint){

                }
                if(read_parameters<Params>()->mode==TelepresenceMode::tmJoystick){
                    mp->create_strategy<RemoteTwistStrategy>("telepresence",1);
                }
                nlohmann::json response;
                if(m_handshake_stage==0){
                    m_handshake_message_uuid=m_portal->send_message(read_parameters<Params>()->peer_ip,12002,"post_event",{{"name","sync_done"}});
                    m_handshake_stage++;
                }
                if(m_handshake_stage==1){
                    nlohmann::json response = m_portal->get_message_response(m_handshake_message_uuid);
                    if(response.is_boolean()){
                        m_handshake_stage=0;
                        return {};
                    }else if(response.is_null()){
                        return {};
                    }else{
                        m_handshake_stage=2;
                    }
                }
                return mp;
            }
        }
        if(get_active_mp()->get_name()=="telepresence"){
            if(get_active_mp()->get_strategy_interface("telepresence")->finished()){
                m_handshake_stage=0;
                std::shared_ptr<ManipulationPrimitive> mp = create_mp("handshake",p);
                nlohmann::json response;
                mp->create_strategy<NullStrategy>("idle",1);
                return mp;
            }
        }
    }
    return {};
}

void Telepresence::auxiliaries(const Percept &p){
    std::vector<double> payload;
    if(read_parameters<Params>()->mode==TelepresenceMode::tmDirectCart){

    }
    if(read_parameters<Params>()->mode==TelepresenceMode::tmDirectJoint){

    }
    if(read_parameters<Params>()->mode==TelepresenceMode::tmJoystick){
        for(unsigned i=0;i<6;i++){
            payload.emplace_back(p.proprioception.TF_F_ext_K(i));
        }
    }
    m_udp_sender->send(payload);
}

bool Telepresence::check_local_suc_conditions(const Percept &p){
    return false;
}


}

