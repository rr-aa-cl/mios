#pragma once

#include "skill/skill.hpp"
namespace mios{
class SkillParametersFile : public SkillParameters{
public:
    bool from_json(const nlohmann::json& parameters) override;
    double f_contact;
    double file_amp;
    double file_freq;
    double speed;
    double distance;
    double t_contactless;
};

class File : public Skill{
public:
    File(const std::string& name,Memory* memory, Portal* portal, const Percept& p);
    void evaluate() override;
    Eigen::Matrix<double,3,3> get_O_R_T_0(const Percept& p) const override;
private:
    std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept& p_0) override;
    bool check_local_suc_conditions(const Percept& p) override;
    bool check_local_err_conditions(const Percept &p) override;

private:
    bool m_in_contact;
    std::chrono::high_resolution_clock::time_point m_t_contact_loss;
    Eigen::Matrix<double,4,4> m_T_T_EE_0;
};
}
