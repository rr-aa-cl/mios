#pragma once

#include "skill/skill.hpp"

#include "primitives/mp_basic.hpp"

namespace mios {

struct SkillParameters_gesture_haptic : public SkillParameters{
    Eigen::Matrix<double,6,1> F_trigger;
    Eigen::Matrix<int,6,1> dir_trigger;
    bool wait_for_relax;
};

class gesture_haptic : public Skill{
public:
    gesture_haptic();

    void evaluate();
    bool read_skill_parameters(const nlohmann::json& p);

private:

    void create_config();
    void build_primitives(const Percept& p);
    std::tuple<bool,std::string> check_edges(const Percept &p);

    bool check_local_suc_conditions(const Percept &p);
    bool check_local_ex_conditions(const Percept &p);
    void auxiliaries(const Percept& p);

    Eigen::Matrix<double,6,1> _triggered;
    Eigen::Matrix<double,6,1> _confirmed;
};

}
