#pragma once

#include "skill/skill.hpp"

namespace mios {

struct SkillParametersTaxHammer : public SkillParameters{
    bool from_json(const nlohmann::json &parameters) override;
    std::map<std::string, std::set<std::string> > get_parameter_list() override;
    Eigen::Matrix<double,2,1> approach_speed;
    Eigen::Matrix<double,2,1> approach_acc;
    Eigen::Matrix<double,2,1> down_speed;
    Eigen::Matrix<double,2,1> down_acc;
    Eigen::Matrix<double,2,1> up_speed;
    Eigen::Matrix<double,2,1> up_acc;
    Eigen::Matrix<double,2,1> down_wrench;
    Eigen::Matrix<double,2,1> up_wrench;
    double n_max;
    double f_h;

    Eigen::Matrix<double,6,1> ROI_x;
    Eigen::Matrix<double,6,1> ROI_phi;
};

class TaxHammer : public Skill{
public:
    TaxHammer(const std::string& id, Memory *memory, Portal *portal);

    Eigen::Matrix<double, 3, 3> get_O_R_T_0(const Percept &p) const override;
    std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept &p_0) override;
    std::optional<std::shared_ptr<ManipulationPrimitive> > graph_transition(const Percept &p) override;

private:
    std::shared_ptr<ManipulationPrimitive> create_approach_mp(const Percept& p);
    std::shared_ptr<ManipulationPrimitive> create_down_mp(const Percept& p);
    std::shared_ptr<ManipulationPrimitive> create_up_mp(const Percept& p);

    bool check_local_pre_conditions(const Percept &p) override;
    bool check_local_suc_conditions(const Percept &p);
    bool check_local_ex_conditions(const Percept &p);
    bool check_local_err_conditions(const Percept &p);

private:

    unsigned m_n_cnt;
};

}
