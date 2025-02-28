#pragma once

#include "mios/skill/skill.hpp"

namespace mios {

struct SkillParametersMoveTrajectory : public SkillParameters{
    bool from_json(const nlohmann::json &parameters) override;
    std::map<std::string, std::set<std::string> > get_parameter_list() override;
    std::string file;
    bool plane;
    Eigen::Matrix<double,6,1> F_ff;
    bool joint_mode;
};

class MoveTrajectory : public Skill{
public:
    MoveTrajectory(const std::string& id, Memory *memory, Portal *portal);

    std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept &p_0) override;
    std::optional<std::shared_ptr<ManipulationPrimitive> > graph_transition(const Percept &p) override;

private:
    bool check_local_suc_conditions(const Percept &p);
    bool read_trajectory_from_file(const std::string &file, std::vector<std::array<double, 16> > &data);
    bool read_trajectory_from_file(const std::string &file, std::vector<std::array<double, 7> > &data);

private:
    bool m_finished;
    std::chrono::high_resolution_clock::time_point m_t_finished;

    std::vector<std::array<double,16> > m_data;
    std::vector<std::array<double,7> > m_data_joint;

    std::string m_file;
};

}
