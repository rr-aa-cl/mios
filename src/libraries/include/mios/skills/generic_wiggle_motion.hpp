#pragma once

#include "mios/skill/skill.hpp"

namespace mios {

class SkillParametersGenericWiggleMotion : public SkillParameters{
public:
    bool from_json(const nlohmann::json &parameters) override;
    std::map<std::string, std::set<std::string> > get_parameter_list() override;
    Eigen::Matrix<double,6,1> dX_fourier_a_a;
    Eigen::Matrix<double,6,1> dX_fourier_b_a;
    Eigen::Matrix<double,6,1> dX_fourier_a_f;
    Eigen::Matrix<double,6,1> dX_fourier_b_f;
    Eigen::Matrix<double,6,1> dX_fourier_a_phi;
    Eigen::Matrix<double,6,1> dX_fourier_b_phi;
    bool use_EE;
    bool tap_to_finish;
};

class GenericWiggleMotion : public Skill{
public:
    GenericWiggleMotion(const std::string& id, Memory *memory, Portal *portal);

    std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept &p_0) override;

    Eigen::Matrix<double,3,3> get_O_R_T_0(const Percept& p) const override;

private:
    bool check_local_suc_conditions(const Percept &p);
    bool check_local_ex_conditions(const Percept &p);
};

}
