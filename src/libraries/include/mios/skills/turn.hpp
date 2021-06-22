#pragma once

#include "mios/skill/skill.hpp"
namespace mios{
class SkillParametersTurn : public SkillParameters{
public:
bool from_json(const nlohmann::json& parameters) override;
std::map<std::string, std::set<std::string> > get_parameter_list() override;
double phi;
double dphi;
};

class Turn : public Skill{
public:
Turn(const std::string& id,Memory* memory, Portal* portal);
Eigen::Matrix<double,3,3> get_O_R_T_0(const Percept& p) const override;
private:
std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept& p_0) override;
bool check_local_suc_conditions(const Percept& p) override;

bool m_finished;
std::chrono::high_resolution_clock::time_point m_t_finished;
Eigen::Matrix<double,4,4> m_T_T_EE_0;
};

}
