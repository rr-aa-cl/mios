#pragma once
#include "skill/skill.hpp"

namespace mios{

class SkillParametersMLTestSkill: public SkillParameters{
public:
    bool from_json(const nlohmann::json &parameters) override;
    std::map<std::string, std::set<std::string> > get_parameter_list() override;
    Eigen::Matrix<double,6,1> x;
    double A;
    Eigen::Matrix<double,2,1> weights;
};

class MLTestSkill : public Skill{
public:
    MLTestSkill(const std::string& id, Memory *memory, Portal *portal);
    std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept &p_0) override;

private:
    double get_custom_cost(const Percept &p) override;
    bool check_local_suc_conditions(const Percept& p);

};
}
