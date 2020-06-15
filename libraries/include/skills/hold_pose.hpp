#pragma once

#include "skill/skill.hpp"

namespace mios {

class SkillParametersHoldPose : public SkillParameters{
public:
    bool from_json(const nlohmann::json &parameters) override;
    double t_max;
};

class HoldPose : public Skill{
public:
    HoldPose(const std::string& id,Memory *memory, Portal* portal, const Percept& p);

    std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept &p_0) override;
    void evaluate();

private:
    bool check_local_suc_conditions(const Percept &p);
    bool check_local_ex_conditions(const Percept &p);

};

}
