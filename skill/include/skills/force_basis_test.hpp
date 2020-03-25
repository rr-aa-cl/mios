#pragma once
#include "skill/skill.hpp"
#include "motion_error_cart/motion_error_cart_wrapper.hpp"

namespace mios{
struct ConfigSkill_force_basis_test: public ConfigSkill{
std::string skill;
Eigen::Matrix<double,6,1> F_h_p;
Eigen::Matrix<double,6,1> F_h_d;
Eigen::Matrix<double,6,1> F_h_e;
Eigen::Matrix<double,6,1> ff_fourier_a_a;
Eigen::Matrix<double,6,1> ff_fourier_b_a;
Eigen::Matrix<double,6,1> ff_fourier_a_f;
Eigen::Matrix<double,6,1> ff_fourier_b_f;
Eigen::Matrix<double,6,1> ff_fourier_a_phi;
Eigen::Matrix<double,6,1> ff_fourier_b_phi;

Eigen::Matrix<double,4,4> TF_T_EE_g;

};class force_basis_test : public Skill{
public:
force_basis_test();
~force_basis_test();
void evaluate();
bool read_skill_parameters(const nlohmann::json& p);
private:
void create_config();
void build_primitives(const Percept& p);
std::tuple<bool,std::string> check_edges(const Percept& p);
bool check_local_suc_conditions(const Percept& p);

};
}
