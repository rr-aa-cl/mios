#pragma once
#include "skill/skill.hpp"

#include "primitives/mp_basic.hpp"
namespace mios{
class SkillParametersTestSkill1: public SkillParameters{
public:
    bool read_parameters(const nlohmann::json &parameters) override;
    std::string skill;
    double run_time;
    bool success;
    double t_exception;
    std::string exception;
    double cost_err;
    double cost_suc;
    std::vector<int> mp_sequence;
};
class TestSkill1 : public Skill{
public:
    TestSkill1(const std::string& name, Memory* memory, const Percept& p);
    void evaluate();

    Eigen::Matrix<double,3,3> get_O_R_T_0(const Percept &p) const override;
private:
    std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept &p_0) override;
    std::optional<std::shared_ptr<ManipulationPrimitive> > graph_transition(const Percept &p) override;
    bool check_local_suc_conditions(const Percept& p) override;
    bool check_local_err_conditions(const Percept &p) override;
    void auxiliaries(const Percept& p) override;
    void parallels() override;
private:
    int m_result_code;
    int m_sequence_index;
    std::vector<std::string> m_mp_graph;
    std::vector<std::string> m_result_graph;
};
}
