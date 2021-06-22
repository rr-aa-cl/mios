#pragma once

#include "mios/skill/skill.hpp"
namespace mios{
class SkillParametersShove : public SkillParameters{
public:
    bool from_json(const nlohmann::json& parameters) override;
    std::map<std::string, std::set<std::string> > get_parameter_list() override;
    Eigen::Matrix<double,4,4> O_T_OB_g;
    double speed;
    double acceleration;
    double t_contactless;
    double delta_x;
};

class Shove : public Skill{
public:
    Shove(const std::string& name, Memory* memory, Portal* portal);

private:
    std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept& p_0) override;
    bool check_local_suc_conditions(const Percept& p) override;
    bool check_local_err_conditions(const Percept &p) override;
    bool check_local_pre_conditions(const Percept &p) override;
    void update_policies(const Percept &p) override;
    void update_internal_models(const Percept &p) override;

private:
    bool m_in_contact;
    std::chrono::high_resolution_clock::time_point m_t_contact_loss;
};
}
