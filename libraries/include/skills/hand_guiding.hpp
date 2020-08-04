#pragma once
#include "skill/skill.hpp"

namespace mios{
class SkillParametersHandGuiding: public SkillParameters{
public:
    bool from_json(const nlohmann::json &parameters) override;
    std::string skill;
    Eigen::Matrix<double,6,1> fix_dim;
    Eigen::Matrix<double,6,1> dist_walls;
    bool use_walls;
};

class HandGuiding : public Skill{
public:
    HandGuiding(const std::string& id, Memory *memory, Portal *portal, const Percept& p);
    std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept &p_0) override;
private:
    bool check_local_suc_conditions(const Percept& p);
};
}
