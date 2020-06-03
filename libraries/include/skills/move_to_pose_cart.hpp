#pragma once

#include "skill/skill.hpp"

namespace mios {

struct SkillParametersMoveToPoseCart : public SkillParameters{
    bool read_parameters(const nlohmann::json &parameters) override;
    Eigen::Matrix<double,2,1> speed;
    Eigen::Matrix<double,2,1> acc;
    Eigen::Matrix<double,4,4> TF_T_EE_g;
    Eigen::Matrix<double,4,4> TF_g_offset;
};

class MoveToPoseCart : public Skill{
public:
    MoveToPoseCart(const std::string& id,Memory *memory, const Percept& p);

    std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept &p_0) override;

    void evaluate();

private:
    bool check_local_suc_conditions(const Percept &p);
    bool check_local_ex_conditions(const Percept &p);
};

}
