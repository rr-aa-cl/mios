#pragma once

#include "mios/skill/skill.hpp"

namespace mios {

class SkillParametersCrank: public SkillParameters{
public:
    bool from_json(const nlohmann::json &parameters) override;
    std::map<std::string, std::set<std::string> > get_parameter_list() override;
    double radius;
    double n_turns;
    bool clockwise;

    Eigen::Matrix<double,2,1> crank_speed;
    Eigen::Matrix<double,2,1> crank_acc;

};

class Crank : public Skill{
public:
    Crank(const std::string& id, Memory *memory, Portal* portal);

    Eigen::Matrix<double, 3, 3> get_O_R_T_0(const Percept &p) const override;
    std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept &p_0) override;
    std::optional<std::shared_ptr<ManipulationPrimitive> > graph_transition(const Percept &p) override;

private:
    std::shared_ptr<ManipulationPrimitive> create_crank_mp(const Percept& p);

    bool check_local_pre_conditions(const Percept &p) override;
    bool check_local_suc_conditions(const Percept &p) override;
    bool check_local_err_conditions(const Percept &p) override;

private:


};

}
