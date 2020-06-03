#pragma once

#include "skill/skill.hpp"

#include "primitives/mp_basic.hpp"

namespace mios {

struct SkillParametersMoveToContact : public SkillParameters{
    bool read_parameters(const nlohmann::json &parameters) override;
    Eigen::Matrix<double,1,1> speed;
};

class MoveToContact : public Skill{
public:
    MoveToContact(const std::string& id,Memory *memory, const Percept& p);

    std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept &p_0) override;
    void evaluate();
    Eigen::Matrix<double, 3, 3> get_O_R_T_0(const Percept &p) const override;

private:
    bool check_local_suc_conditions(const Percept &p) override;
    bool check_local_ex_conditions(const Percept &p) override;
    bool check_local_err_conditions(const Percept &p) override;
};

}
