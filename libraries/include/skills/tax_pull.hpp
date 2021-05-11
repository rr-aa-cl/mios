#pragma once

#include "skill/skill.hpp"
namespace mios{
class SkillParametersTaxPull : public SkillParameters{
public:
    bool from_json(const nlohmann::json& parameters) override;
    std::map<std::string, std::set<std::string> > get_parameter_list() override;
    struct P0{
        Eigen::Matrix<double,6,1> K_x;
        double f_pull;
        double duration;
    }p0;
};

class TaxPull : public Skill{
public:
    TaxPull(const std::string& name, Memory* memory, Portal* portal);
    Eigen::Matrix<double,3,3> get_O_R_T_0(const Percept& p) const override;

private:
    std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept& p_0) override;
    bool check_local_pre_conditions(const Percept &p) override;
    bool check_local_suc_conditions(const Percept& p) override;
    bool check_local_err_conditions(const Percept &p) override;

    std::shared_ptr<ManipulationPrimitive> create_pull_mp(const Percept& p);

private:

};
}
