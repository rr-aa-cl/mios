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
};
class TestSkill1 : public Skill{
public:
    TestSkill1(const std::string& name, Memory* memory, const Percept& p);
    void evaluate();

    bool read_skill_parameters(const nlohmann::json& p);
    Eigen::Matrix<double,3,3> get_O_R_T_0(const Percept &p);
private:
    std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept &p_0) override;
    std::optional<std::shared_ptr<ManipulationPrimitive> > graph_transition(const Percept &p) override;
    void create_config();
    void build_primitives(const Percept& p);
    std::tuple<bool,std::string> check_edges(const Percept& p);
    bool check_local_suc_conditions(const Percept& p);
    bool check_local_err_conditions(const Percept &p);
    void auxiliaries(const Percept& p);
    void parallels();
};
}
