#pragma once

#include "mios/skill/skill.hpp"
namespace mios{
class SkillParametersTaxSpoon : public SkillParameters{
public:
    bool from_json(const nlohmann::json& parameters) override;
    std::map<std::string, std::set<std::string> > get_parameter_list() override;
    Eigen::Matrix<double,2,1> dip_speed;
    Eigen::Matrix<double,2,1> dip_acc;
    Eigen::Matrix<double,2,1> gather_speed;
    Eigen::Matrix<double,2,1> gather_acc;
    Eigen::Matrix<double,2,1> emerge_speed;
    Eigen::Matrix<double,2,1> emerge_acc;
    double liquid_weight;

    Eigen::Matrix<double,6,1> ROI_x;
    Eigen::Matrix<double,6,1> ROI_phi;
};

class TaxSpoon : public Skill{
public:
    TaxSpoon(const std::string& name, Memory* memory, Portal* portal);
    Eigen::Matrix<double,3,3> get_O_R_T_0(const Percept& p) const override;

private:
    std::optional<std::shared_ptr<ManipulationPrimitive> > graph_transition(const Percept &p) override;
    std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept& p_0) override;
    bool check_local_pre_conditions(const Percept &p) override;
    bool check_local_err_conditions(const Percept &p) override;
    bool check_local_suc_conditions(const Percept& p) override;

    std::shared_ptr<ManipulationPrimitive> create_approach_mp(const Percept& p);
    std::shared_ptr<ManipulationPrimitive> create_dip_mp(const Percept& p);
    std::shared_ptr<ManipulationPrimitive> create_gather_mp(const Percept& p);
    std::shared_ptr<ManipulationPrimitive> create_emerge_mp(const Percept& p);
    std::shared_ptr<ManipulationPrimitive> create_check_mp(const Percept& p);

};
}
