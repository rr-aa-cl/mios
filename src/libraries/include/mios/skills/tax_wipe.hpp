#pragma once

#include "mios/skill/skill.hpp"
namespace mios{
class SkillParametersTaxWipe : public SkillParameters{
public:
    bool from_json(const nlohmann::json& parameters) override;
    std::map<std::string, std::set<std::string> > get_parameter_list() override;
    Eigen::Matrix<double,2,1> approach_speed;
    Eigen::Matrix<double,2,1> approach_acc;
    Eigen::Matrix<double,2,1> wipe_speed;
    Eigen::Matrix<double,2,1> wipe_acc;

    Eigen::Matrix<double,6,1> ROI_x;
    Eigen::Matrix<double,6,1> ROI_phi;
};

class TaxWipe : public Skill{
public:
    TaxWipe(const std::string& name, Memory* memory, Portal* portal);
    Eigen::Matrix<double,3,3> get_O_R_T_0(const Percept& p) const override;

private:
    std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept& p_0) override;
    std::optional<std::shared_ptr<ManipulationPrimitive> > graph_transition(const Percept &p) override;
    bool check_local_pre_conditions(const Percept &p) override;
    bool check_local_suc_conditions(const Percept& p) override;
    bool check_local_ex_conditions(const Percept &p) override;
    bool check_local_err_conditions(const Percept &p) override;

    void update_internal_models(const Percept &p) override;

    std::shared_ptr<ManipulationPrimitive> create_approach_mp(const Percept& p);
    std::shared_ptr<ManipulationPrimitive> create_wipe_mp(const Percept& p);

private:
    Eigen::Matrix<double,4,4> m_T_T_wipe;
    Eigen::Matrix<double,3,1> m_ROI_center;
};
}
