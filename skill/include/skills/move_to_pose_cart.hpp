#pragma once

#include "skill/skill.hpp"

#include "primitives/mp_basic.hpp"

namespace mios {

struct SkillParameters_move_to_pose_cart : public SkillParameters{
    Eigen::Matrix<double,1,1> speed;
    Eigen::Matrix<double,1,1> acc;
    Eigen::Matrix<double,4,4> TF_T_EE_g;
    Eigen::Matrix<double,4,4> TF_g_offset;
    double t_settle;
};

class move_to_pose_cart : public Skill{
public:
    move_to_pose_cart();

    void evaluate();
    bool read_skill_parameters(const nlohmann::json& p);

private:

    void create_config();
    void build_primitives(const Percept& p);
    std::tuple<bool,std::string> check_edges(const Percept &p);

    bool check_local_suc_conditions(const Percept &p);
    bool check_local_ex_conditions(const Percept &p);

    double _t_settle;
    bool _flag_settle;

};

}
