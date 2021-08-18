#pragma once

#include "mios/skill/skill.hpp"

namespace mios {

struct SkillParametersTaxMove : public SkillParameters{
    bool from_json(const nlohmann::json &parameters) override;
    std::map<std::string, std::set<std::string> > get_parameter_list() override;
    struct P0{
        double t_settle;
        Eigen::Matrix<double,2,1> dX_d;
        Eigen::Matrix<double,2,1> ddX_d;
        Eigen::Matrix<double,4,4> T_T_EE_g;
        Eigen::Matrix<double,4,4> T_T_EE_g_offset;
        double finger_width;
        double finger_speed;
        Eigen::Matrix<double,6,1> K_x;
    }p0;


};

class TaxMove : public Skill{
public:
    TaxMove(const std::string& id, Memory *memory, Portal* portal);

    std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept &p_0) override;

private:

    std::shared_ptr<ManipulationPrimitive> create_move_mp(const Percept& p);

    bool check_local_suc_conditions(const Percept &p) override;
    bool check_local_ex_conditions(const Percept &p) override;

    double get_goal_heuristic(const Percept &p) override;

private:
    Eigen::Matrix<double,4,4> m_T_T_EE_g;
    bool m_finished;
    std::chrono::high_resolution_clock::time_point m_t_finished;
};

}
