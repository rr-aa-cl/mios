#pragma once

#include "skill/skill.hpp"

#include "primitives/mp_basic.hpp"

namespace mios {

struct Config_look_at : public ConfigSkill{
    Eigen::Matrix<double,4,4> TF_T_look_at;
    Eigen::Matrix<double,4,4> TF_T_look_from;

    double speed;
    double acc;

    double hover_a;
    double hover_f;
    double wink_a;
    double wink_f;

    double t_hover;
    double t_wink;

    double r_poses;
    double F_confirm;
};

class look_at : public Skill{
public:
    look_at();
    ~look_at();

    Eigen::Matrix<double,3,3> get_O_R_TF(const Percept& p);

    void evaluate();
    bool read_skill_parameters(const nlohmann::json& p);

private:

    void create_config();
    void build_primitives(const Percept& p);
    std::tuple<bool,std::string> check_edges(const Percept &p);

    bool check_local_suc_conditions(const Percept &p);
    bool check_local_ex_conditions(const Percept &p);
    bool check_local_err_conditions(const Percept &p);

    double _t_look_start;
    double _t_wink_start;

    int color;
    int cnt_color;

};

}
