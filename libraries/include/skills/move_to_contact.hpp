#pragma once

#include "skill/skill.hpp"

namespace mios {

struct SkillParametersMoveToContact : public SkillParameters{
    bool from_json(const nlohmann::json &parameters) override;
    std::map<std::string, std::set<std::string> > get_parameter_list() override;
    double speed;
};

class MoveToContact : public Skill{
public:
    MoveToContact(const std::string& id, Memory *memory, Portal *portal);

    std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept &p_0) override;
//    Eigen::Matrix<double, 3, 3> get_O_R_T_0(const Percept &p) const override;

private:
    bool check_local_suc_conditions(const Percept &p) override;
    bool check_local_ex_conditions(const Percept &p) override;
    bool check_local_err_conditions(const Percept &p) override;
};

}
