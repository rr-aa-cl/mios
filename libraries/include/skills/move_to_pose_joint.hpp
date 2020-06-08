#pragma once

#include "skill/skill.hpp"

namespace mios {

struct SkillParametersMoveToPoseJoint : public SkillParameters{
    bool read_parameters(const nlohmann::json &parameters) override;
    double speed;
    double acc;
    Eigen::Matrix<double,7,1> q_g;
    Eigen::Matrix<double,7,1> q_g_offset;
};

class MoveToPoseJoint : public Skill{
public:
    MoveToPoseJoint(const std::string& id,Memory *memory, const Percept& p);

    std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept &p_0) override;
    void evaluate();

private:
    bool check_local_suc_conditions(const Percept &p);
    bool check_local_ex_conditions(const Percept &p);
};

}
