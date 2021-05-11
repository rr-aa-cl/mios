#pragma once

#include "skill/skill.hpp"
namespace mios{
class SkillParametersTaxPush : public SkillParameters{
public:
    bool from_json(const nlohmann::json& parameters) override;
    std::map<std::string, std::set<std::string> > get_parameter_list() override;

    struct P0{
        Eigen::Matrix<double,6,1> K_x;
        Eigen::Matrix<double,2,1> dX_d;
        Eigen::Matrix<double,2,1> ddX_d;
    }p0;
    struct P1{
        Eigen::Matrix<double,6,1> K_x;
        Eigen::Matrix<double,2,1> dX_d;
        Eigen::Matrix<double,2,1> ddX_d;
    }p1;
    struct P2{
        Eigen::Matrix<double,6,1> K_x;
        double f_push;
        double duration;
    }p2;
};

class TaxPush : public Skill{
public:
    TaxPush(const std::string& name, Memory* memory, Portal* portal);
    Eigen::Matrix<double,3,3> get_O_R_T_0(const Percept& p) const override;

private:
    std::optional<std::shared_ptr<ManipulationPrimitive> > graph_transition(const Percept &p) override;
    std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept& p_0) override;
    bool check_local_pre_conditions(const Percept &p) override;
    bool check_local_err_conditions(const Percept &p) override;
    bool check_local_suc_conditions(const Percept& p) override;

    std::shared_ptr<ManipulationPrimitive> create_approach_mp(const Percept& p);
    std::shared_ptr<ManipulationPrimitive> create_contact_mp(const Percept& p);
    std::shared_ptr<ManipulationPrimitive> create_push_mp(const Percept& p);

private:
    Eigen::Matrix<double,4,4> m_T_T_EE_contact;

};
}
