#pragma once

#include "mios/skill/skill.hpp"

namespace mios {

class SkillParametersDraw : public SkillParameters{
public:
    bool from_json(const nlohmann::json &parameters) override;
    std::map<std::string, std::set<std::string> > get_parameter_list() override;
    std::string path_file;
    double f_draw;

    bool file_mode;
    unsigned port_src;

    Eigen::Matrix<double,2,1> approach_speed;
    Eigen::Matrix<double,2,1> approach_acc;
    Eigen::Matrix<double,2,1> contact_speed;
    Eigen::Matrix<double,2,1> contact_acc;

};

class Draw : public Skill{
public:
    Draw(const std::string& id, Memory *memory, Portal* portal);

    Eigen::Matrix<double, 3, 3> get_O_R_T_0(const Percept &p) const override;
    std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept &p_0) override;
    std::optional<std::shared_ptr<ManipulationPrimitive> > graph_transition(const Percept &p) override;

private:
    std::shared_ptr<ManipulationPrimitive> create_approach_mp(const Percept& p);
    std::shared_ptr<ManipulationPrimitive> create_contact_mp(const Percept& p);
    std::shared_ptr<ManipulationPrimitive> create_draw_mp(const Percept& p);
    std::shared_ptr<ManipulationPrimitive> create_retract_mp(const Percept& p);

    bool check_local_pre_conditions(const Percept &p) override;
    bool check_local_suc_conditions(const Percept &p) override;
    bool check_local_err_conditions(const Percept &p) override;

    void update_policies(const Percept &p) override;

private:

    std::vector<Eigen::Matrix<double,3,1> > m_positions;
    std::vector<bool> m_start_positions;

};

}
