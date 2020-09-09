#include "skills/null_skill.hpp"
#include "strategies/null_strategy.hpp"

namespace mios {

SkillParametersNullSkill::SkillParametersNullSkill():SkillParameters(){

}

bool SkillParametersNullSkill::from_json(const nlohmann::json &parameters){
    return false;
}

std::map<std::string, std::set<std::string> > SkillParametersNullSkill::get_parameter_list(){
    return {};
}

NullSkill::NullSkill(const std::string& id, Memory *memory, Portal* portal):Skill("NullSkill",{},id,memory,portal,{ControlMode::mNoControl}){

}

std::shared_ptr<ManipulationPrimitive> NullSkill::get_initial_mp(const Percept &p_0){
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("null",p_0);
    mp->create_strategy<NullStrategy>("null",1);
    return mp;
}

bool NullSkill::check_local_suc_conditions(const Percept &p){
    return false;
}

bool NullSkill::check_local_err_conditions(const Percept &p){
    return true;
}

}
