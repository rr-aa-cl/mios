#pragma once

#include "skill/skill.hpp"

namespace mios {

class SkillParametersHoldPose : public SkillParameters{
public:
    bool from_json(const nlohmann::json &parameters) override;
    std::map<std::string, std::set<std::string> > get_parameter_list() override;
    double t_max;
};

class HoldPose : public Skill{
public:
    HoldPose(const std::string& id, Memory *memory, Portal* portal);

    std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept &p_0) override;

private:
    bool check_local_suc_conditions(const Percept &p) override;
    bool check_local_ex_conditions(const Percept &p) override;

};

}
