#pragma once

#include "skill/skill.hpp"

namespace mios {

class SkillParametersTaxInsertion : public SkillParameters{
public:
    bool from_json(const nlohmann::json &parameters) override;
    std::map<std::string, std::set<std::string> > get_parameter_list() override;
    Eigen::Matrix<double,2,1> insertion_speed;
    Eigen::Matrix<double,2,1> insertion_acc;
    Eigen::Matrix<double,2,1> approach_speed;
    Eigen::Matrix<double,2,1> approach_acc;
    Eigen::Matrix<double,6,1> search_a;
    Eigen::Matrix<double,6,1> search_f;
    Eigen::Matrix<double,6,1> DeltaX;
    double f_max_push;

    Eigen::Matrix<double,6,1> ROI_x;
    Eigen::Matrix<double,6,1> ROI_phi;

    double stuck_dx_thr;
};

class TaxInsertion : public Skill{
public:
    TaxInsertion(const std::string& id, Memory *memory, Portal* portal);

    Eigen::Matrix<double, 3, 3> get_O_R_T_0(const Percept &p) const override;
    std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept &p_0) override;
    std::optional<std::shared_ptr<ManipulationPrimitive> > graph_transition(const Percept &p) override;

    double get_goal_heuristic(const Percept &p) override;

private:
    bool is_stuck(const Percept& p);
    std::shared_ptr<ManipulationPrimitive> create_approach_mp(const Percept& p);
    std::shared_ptr<ManipulationPrimitive> create_contact_mp(const Percept& p);
    std::shared_ptr<ManipulationPrimitive> create_insert_mp(const Percept& p);
    std::shared_ptr<ManipulationPrimitive> create_wiggle_mp(const Percept& p);

    bool check_local_pre_conditions(const Percept &p) override;
    bool check_local_suc_conditions(const Percept &p) override;
    bool check_local_ex_conditions(const Percept &p) override;
    bool check_local_err_conditions(const Percept &p) override;

    void update_policies(const Percept &p) override;

private:

    Eigen::Matrix<double,6,1> m_insert_dir;

    double m_dx_avg;
    unsigned m_dx_avg_last;
    std::vector<double> m_dx_avg_mem;

    bool m_is_stuck;
};

}
