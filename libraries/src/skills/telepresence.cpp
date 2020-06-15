#include "skills/telepresence.hpp"

namespace mios{

bool SkillParametersTelepresence::from_json(const nlohmann::json &parameters){
    return true;
}

Telepresence::Telepresence(const std::string &name, Memory *memory, Portal *portal, const Percept &p):Skill("Telepresence",{},name,memory,portal,p){
    if(get_parameters<SkillParametersTelepresence>()->master){
        if(get_parameters<SkillParametersTelepresence>()->mode==TelepresenceMode::tmJoystick){
            m_udp_sender = portal->open_udp_outstream("remote_twist_out",get_parameters<SkillParametersTelepresence>()->peer_ip,get_parameters<SkillParametersTelepresence>()->peer_port);
        }
    }else{
        if(get_parameters<SkillParametersTelepresence>()->mode==TelepresenceMode::tmJoystick){
            m_udp_sender = portal->open_udp_outstream("remote_force_out",get_parameters<SkillParametersTelepresence>()->peer_ip,get_parameters<SkillParametersTelepresence>()->peer_port);
        }
    }

}

std::shared_ptr<ManipulationPrimitive> Telepresence::get_initial_mp(const Percept &p_0){
    return create_mp("sync",p_0);
}

std::optional<std::shared_ptr<ManipulationPrimitive> > Telepresence::graph_transition(const Percept &p){
    return {};
}

bool Telepresence::check_local_suc_conditions(const Percept &p){
    return false;
}


}

