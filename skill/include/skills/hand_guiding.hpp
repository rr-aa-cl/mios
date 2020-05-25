#pragma once
#include "skill/skill.hpp"

#include "primitives/mp_basic.hpp"

namespace mios{
class SkillParametersHandGuiding: public SkillParameters{
public:
    bool read_parameters(const nlohmann::json &parameters) override;
    std::string skill;
    Eigen::Matrix<double,6,1> fix_dim;
    Eigen::Matrix<double,6,1> dist_walls;
    Eigen::Matrix<double,6,1> use_walls;
};

class HandGuiding : public Skill{
public:
    HandGuiding(const std::string& id,Memory *memory, const Percept& p);
    std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept &p_0) override;
private:
    bool check_local_suc_conditions(const Percept& p);
};
}
