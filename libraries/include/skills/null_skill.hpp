#pragma once

#include "skill/skill.hpp"

namespace mios {

class SkillParametersNullSkill : public SkillParameters{
public:
    SkillParametersNullSkill();
    bool from_json(const nlohmann::json &parameters);
    std::map<std::string, std::set<std::string> > get_parameter_list() override;
};

class NullSkill : public Skill{
public:
    NullSkill(const std::string& id, Memory *memory, Portal* portal);
    std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept &p_0) override;
private:
    bool check_local_suc_conditions(const Percept& p);
    bool check_local_err_conditions(const Percept &p);
};

}
