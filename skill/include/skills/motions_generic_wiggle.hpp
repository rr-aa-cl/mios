#pragma once

#include "skill/skill.hpp"

#include "primitives/mp_basic.hpp"

namespace mios {

struct ConfigSkill_motions_generic_wiggle : public ConfigSkill{
    Eigen::Matrix<double,6,1> dX_fourier_a_a;
    Eigen::Matrix<double,6,1> dX_fourier_b_a;
    Eigen::Matrix<double,6,1> dX_fourier_a_f;
    Eigen::Matrix<double,6,1> dX_fourier_b_f;
    Eigen::Matrix<double,6,1> dX_fourier_a_phi;
    Eigen::Matrix<double,6,1> dX_fourier_b_phi;
    bool use_EE;
    bool tap_to_finish;
};

class motions_generic_wiggle : public Skill{
public:
    motions_generic_wiggle();
    ~motions_generic_wiggle();

    void evaluate();
    bool read_skill_parameters(const nlohmann::json& p);
    Eigen::Matrix<double,3,3> get_O_R_TF(const Percept& p);

private:

    void create_config();
    void build_primitives(const Percept& p);
    std::tuple<bool,std::string> check_edges(const Percept &p);

    bool check_local_suc_conditions(const Percept &p);
    bool check_local_ex_conditions(const Percept &p);
};

}
