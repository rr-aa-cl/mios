#pragma once

#include "skill/skill.hpp"

#include "primitives/mp_basic_joint.hpp"

namespace mios {

struct ConfigSkill_move_to_pose_joint : public ConfigSkill{
    Eigen::Matrix<double,1,1> speed;
    Eigen::Matrix<double,1,1> acc;
    Eigen::Matrix<double,7,1> q_g;
    Eigen::Matrix<double,7,1> q_g_offset;
};

class move_to_pose_joint : public Skill{
public:
    move_to_pose_joint();
    ~move_to_pose_joint();

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
