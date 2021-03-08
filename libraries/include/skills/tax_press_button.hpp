#pragma once

#include "skill/skill.hpp"
namespace mios{
class SkillParametersTaxPressButton : public SkillParameters{
public:
    bool from_json(const nlohmann::json& parameters) override;
    std::map<std::string, std::set<std::string> > get_parameter_list() override;
    Eigen::Matrix<double,2,1> approach_speed;
    Eigen::Matrix<double,2,1> approach_acc;
    Eigen::Matrix<double,2,1> press_speed;
    Eigen::Matrix<double,2,1> press_acc;
    double f_push;
    double duration;

    Eigen::Matrix<double,6,1> ROI_x;
    Eigen::Matrix<double,6,1> ROI_phi;
};

class TaxPressButton : public Skill{
public:
    TaxPressButton(const std::string& name, Memory* memory, Portal* portal);
    Eigen::Matrix<double,3,3> get_O_R_T_0(const Percept& p) const override;

private:
    std::optional<std::shared_ptr<ManipulationPrimitive> > graph_transition(const Percept &p) override;
    std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept& p_0) override;
    bool check_local_pre_conditions(const Percept &p) override;
    bool check_local_err_conditions(const Percept &p) override;
    bool check_local_suc_conditions(const Percept& p) override;
    bool check_local_ex_conditions(const Percept &p) override;

    std::shared_ptr<ManipulationPrimitive> create_approach_mp(const Percept& p);
    std::shared_ptr<ManipulationPrimitive> create_contact_mp(const Percept& p);
    std::shared_ptr<ManipulationPrimitive> create_push_mp(const Percept& p);
    std::shared_ptr<ManipulationPrimitive> create_retract_mp(const Percept& p);

    double get_goal_heuristic(const Percept &p) override;

private:
    std::chrono::high_resolution_clock::time_point m_press_t_0;
    bool m_press_started;

};
}
