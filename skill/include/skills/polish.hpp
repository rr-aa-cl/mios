#pragma once

#include "skill/skill.hpp"

#include "primitives/mp_basic.hpp"

namespace mios {

struct ConfigSkill_polish : public ConfigSkill{
    double a_x;
    double a_y;
    double f_x;
    double f_y;
    double F_d;
    double t_max;
};

class polish : public Skill{
public:
    polish();
    void evaluate();
    bool read_skill_parameters(const nlohmann::json& p);
    Eigen::Matrix<double,3,3> get_O_R_TF(const Percept& p);

private:

    void create_config();
    void build_primitives(const Percept& p);
    std::tuple<bool,std::string> check_edges(const Percept &p);

    bool check_local_suc_conditions(const Percept &p);
    bool check_local_ex_conditions(const Percept &p);
    void auxiliaries(const Percept& p);
};

}
