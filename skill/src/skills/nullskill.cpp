#include "skills/nullskill.hpp"
#include "primitives/nullprimitive.hpp"

namespace mios {

SkillParametersNullSkill::SkillParametersNullSkill():SkillParameters(){

}

bool SkillParametersNullSkill::read_parameters(const nlohmann::json &parameters){
    return false;
}

NullSkill::NullSkill(const std::string& id, Memory *memory, const Percept& p):Skill("NullSkill",{},id,memory,p){

}

std::shared_ptr<ManipulationPrimitive> NullSkill::get_initial_mp(const Percept &p_0){
    return create_mp<NullPrimitive,MPParametersNullPrimitive,NullAttractor>("null",p_0);
}

bool NullSkill::check_local_suc_conditions(const Percept &p){
    return false;
}

bool NullSkill::check_local_err_conditions(const Percept &p){
    return true;
}

}
