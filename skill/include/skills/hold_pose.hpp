#pragma once

#include "skill/skill.hpp"

#include "primitives/mp_basic.hpp"

namespace mios {

struct SkillParameters_hold_pose : public SkillParameters{
    double t_max;
};

class hold_pose : public Skill{
public:
    hold_pose(KnowledgeBase *kb, std::shared_ptr<SkillParameters> config);

    void evaluate();
    bool read_skill_parameters(const nlohmann::json& p);

private:

    void create_config();
    void build_primitives(const Percept& p);
    std::tuple<bool,std::string> check_edges(const Percept &p);

    bool check_local_suc_conditions(const Percept &p);
    bool check_local_ex_conditions(const Percept &p);

};

}
