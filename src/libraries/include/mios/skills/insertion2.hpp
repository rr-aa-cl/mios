#pragma once

#include "mios/skill/skill.hpp"

namespace mios {

class SkillParametersInsertion2 : public SkillParameters{
public:
    bool from_json(const nlohmann::json &parameters) override;
    std::map<std::string, std::set<std::string> > get_parameter_list() override;

    struct P0{
        Eigen::Matrix<double,6,1> K_x;
        Eigen::Matrix<double,6,1> DeltaX;
        Eigen::Matrix<double,2,1> dX_d;
        Eigen::Matrix<double,2,1> ddX_d;
    }p0;

    struct P1{
        Eigen::Matrix<double,6,1> K_x;
        Eigen::Matrix<double,2,1> dX_d;
        Eigen::Matrix<double,2,1> ddX_d;
    }p1;

    struct P2{
        Eigen::Matrix<double,6,1> K_x;
        Eigen::Matrix<double,6,1> search_c;
        Eigen::Matrix<double,6,1> search_a;
        Eigen::Matrix<double,6,1> search_f;
        Eigen::Matrix<double,6,1> search_phi;
        Eigen::Matrix<double,6,1> delta_a;
        Eigen::Matrix<double,6,1> delta_f;
        Eigen::Matrix<double,6,1> delta_phi;
        double t_d;
    }p2;

};

class Insertion2 : public Skill{
public:
    Insertion2(const std::string& id, Memory *memory, Portal* portal);

    Eigen::Matrix<double, 3, 3> get_O_R_T_0(const Percept &p) const override;
    std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept &p_0) override;
    std::optional<std::shared_ptr<ManipulationPrimitive> > graph_transition(const Percept &p) override;

    double get_goal_heuristic(const Percept &p) override;

private:
    std::shared_ptr<ManipulationPrimitive> create_approach_mp(const Percept& p);
    std::shared_ptr<ManipulationPrimitive> create_contact_mp(const Percept& p);
    std::shared_ptr<ManipulationPrimitive> create_wiggle_mp(const Percept& p);


    bool check_local_pre_conditions(const Percept &p) override;
    bool check_local_suc_conditions(const Percept &p) override;
    bool check_local_err_conditions(const Percept &p) override;

    void update_policies(const Percept &p) override;

private:

    Eigen::Matrix<double,6,1> m_insert_dir;

    double m_E_avg;

    double m_dx_avg;
    unsigned m_dx_avg_last;
    std::vector<double> m_dx_avg_mem;

    bool m_is_stuck;
    Eigen::Matrix<double,6,1> Bias;
    int dataCount;
};

}
