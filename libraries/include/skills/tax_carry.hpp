#pragma once

#include "skill/skill.hpp"

namespace mios {

struct SkillParametersTaxCarry : public SkillParameters{
    bool from_json(const nlohmann::json &parameters) override;
    std::map<std::string, std::set<std::string> > get_parameter_list() override;
    struct P0{
        Eigen::Matrix<double,2,1> dX_d;
        Eigen::Matrix<double,2,1> ddX_d;
        Eigen::Matrix<double,6,1> K_x;
    }p0;
};

class TaxCarry : public Skill{
public:
    TaxCarry(const std::string& id, Memory *memory, Portal* portal);

    std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept &p_0) override;

private:

    std::shared_ptr<ManipulationPrimitive> create_move_mp(const Percept& p);

    bool check_local_pre_conditions(const Percept &p) override;
    bool check_local_suc_conditions(const Percept &p) override;
    bool check_local_err_conditions(const Percept &p) override;

private:
    bool m_finished;
    std::chrono::high_resolution_clock::time_point m_t_finished;
};

}
