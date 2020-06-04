#pragma once
#include "skill/skill.hpp"
#include "primitives/mp_basic.hpp"
namespace mios{

class SkillParametersMLTestSkill: public SkillParameters{
public:
    bool read_parameters(const nlohmann::json &parameters) override;
    std::string skill;
    Eigen::Matrix<double,6,1> x;
    double A;
    double selector;
};

class MLTestSkill : public Skill{
public:
    MLTestSkill(const std::string& id, Memory *memory, const Percept& p);
    void evaluate();
    std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept &p_0) override;
private:
    bool check_local_suc_conditions(const Percept& p);
};
}
