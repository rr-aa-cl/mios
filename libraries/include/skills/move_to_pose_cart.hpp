#pragma once

#include "skill/skill.hpp"

namespace mios {

struct SkillParametersMoveToPoseCart : public SkillParameters{
    bool from_json(const nlohmann::json &parameters) override;
    std::map<std::string, std::set<std::string> > get_parameter_list() override;
    double t_settle;
    Eigen::Matrix<double,2,1> speed;
    Eigen::Matrix<double,2,1> acc;
    Eigen::Matrix<double,4,4> T_T_EE_g;
    Eigen::Matrix<double,4,4> T_T_EE_g_offset;
};

class MoveToPoseCart : public Skill{
public:
    MoveToPoseCart(const std::string& id, Memory *memory, Portal* portal);

    std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept &p_0) override;

private:
    bool check_local_suc_conditions(const Percept &p) override;
    bool check_local_ex_conditions(const Percept &p) override;

private:
    bool m_finished;
    std::chrono::high_resolution_clock::time_point m_t_finished;
};

}
