#pragma once

#include "mios/skill/skill.hpp"
namespace mios{
class SkillParametersTaxFile : public SkillParameters{
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
        double f_file;
        double amp_file;
        double freq_file;
        Eigen::Matrix<double,2,1> dX_d;
        Eigen::Matrix<double,2,1> ddX_d;
    }p2;
    struct P3{
        Eigen::Matrix<double,6,1> K_x;
        Eigen::Matrix<double,2,1> dX_d;
        Eigen::Matrix<double,2,1> ddX_d;
    }p3;

};

class TaxFile : public Skill{
public:
    TaxFile(const std::string& name, Memory* memory, Portal* portal);
    Eigen::Matrix<double,3,3> get_O_R_T_0(const Percept& p) const override;

private:
    std::optional<std::shared_ptr<ManipulationPrimitive> > graph_transition(const Percept &p) override;
    std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept& p_0) override;
    bool check_local_pre_conditions(const Percept &p) override;
    bool check_local_err_conditions(const Percept &p) override;
    bool check_local_suc_conditions(const Percept& p) override;

    std::shared_ptr<ManipulationPrimitive> create_approach_mp(const Percept& p);
    std::shared_ptr<ManipulationPrimitive> create_contact_mp(const Percept& p);
    std::shared_ptr<ManipulationPrimitive> create_file_mp(const Percept& p);
    std::shared_ptr<ManipulationPrimitive> create_retract_mp(const Percept& p);

};
}
