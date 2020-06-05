#pragma once

#include "skill/skill.hpp"

namespace mios {

class SkillParametersInsertion : public SkillParameters{
public:
    bool read_parameters(const nlohmann::json &parameters) override;
    Eigen::Matrix<double,2,1> traj_speed;
    Eigen::Matrix<double,2,1> traj_acc;
    Eigen::Matrix<double,6,1> search_a;
    Eigen::Matrix<double,6,1> search_f;
    double F_limit;

    Eigen::Matrix<double,6,1> ROI_x;
    Eigen::Matrix<double,6,1> ROI_phi;
};

class Insertion : public Skill{
public:
    Insertion(const std::string& id, Memory *memory, const Percept& p);

    Eigen::Matrix<double, 3, 3> get_O_R_T_0(const Percept &p) const override;
    std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept &p_0) override;
    std::optional<std::shared_ptr<ManipulationPrimitive> > graph_transition(const Percept &p) override;

    void evaluate();
private:
    bool is_stuck(const Percept& p);
    std::shared_ptr<ManipulationPrimitive> create_move_mp(const Percept& p);
    std::shared_ptr<ManipulationPrimitive> create_wiggle_mp(const Percept& p);

    bool check_local_suc_conditions(const Percept &p);
    bool check_local_ex_conditions(const Percept &p);
    bool check_local_err_conditions(const Percept &p);
    void auxiliaries(const Percept &p);

    Eigen::Matrix<double,4,4> TF_T_hole_est;
    Eigen::Matrix<double,3,1> dir_hole;

    double m_cf1_sum_force;
    double m_cf1_cnt;

};

}
