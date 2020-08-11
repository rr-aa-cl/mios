#pragma once
#include "skill/skill.hpp"

namespace mios{

class SkillParametersMLTestSkill: public SkillParameters{
public:
    bool from_json(const nlohmann::json &parameters) override;
    Eigen::Matrix<double,6,1> x;
    double A;
    double selector;
};

class MLTestSkill : public Skill{
public:
    MLTestSkill(const std::string& id, Memory *memory, Portal *portal, const Percept& p);
    void evaluate();
    std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept &p_0) override;
private:
    bool check_local_suc_conditions(const Percept& p);
};
}
