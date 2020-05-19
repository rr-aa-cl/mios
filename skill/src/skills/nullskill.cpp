#include "skills/nullskill.hpp"

namespace mios {


bool SkillParametersNullSkill::read_parameters(const nlohmann::json &parameters){
    return false;
}

NullSkill::NullSkill(Memory *memory, std::shared_ptr<SkillParameters> config):Skill("NullSkill",memory,config){

}

void NullSkill::evaluate(){

}

bool NullSkill::read_skill_parameters(const nlohmann::json &p){
    return false;
}

void NullSkill::create_config(){
    m_config=std::make_shared<SkillParameters_NullSkill>();
}

bool NullSkill::build_primitives(const Percept &p){
    return false;
}

std::tuple<bool,std::string> NullSkill::check_edges(const Percept &p){
    return std::tuple<bool,std::string>(false,"");
}

bool NullSkill::check_local_suc_conditions(const Percept &p){
    return false;
}

bool NullSkill::check_local_err_conditions(const Percept &p){
    return true;
}

}
