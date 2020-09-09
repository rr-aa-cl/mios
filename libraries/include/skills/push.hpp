#pragma once

#include "skill/skill.hpp"
namespace mios{
class SkillParametersPush : public SkillParameters{
public:
    bool from_json(const nlohmann::json& parameters) override;
    std::map<std::string, std::set<std::string> > get_parameter_list() override;
    Eigen::Matrix<double,3,1> F_push;
    Eigen::Matrix<double,3,1> DX_max;
    double duration;
};

class Push : public Skill{
public:
    Push(const std::string& name, Memory* memory, Portal* portal);
    Eigen::Matrix<double,3,3> get_O_R_T_0(const Percept& p) const override;

private:
    std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept& p_0) override;
    bool check_local_suc_conditions(const Percept& p) override;

private:
    Eigen::Matrix<double,4,4> m_TF_T_EE_0;
};
}
