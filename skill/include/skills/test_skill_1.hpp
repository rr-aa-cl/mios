#pragma once
#include "skill/skill.hpp"

#include "primitives/mp_basic.hpp"
namespace mios{
struct SkillParameters_test_skill_1: public SkillParameters{
    std::string skill;
    double run_time;
    bool success;
    double t_exception;
    std::string exception;
};
class test_skill_1 : public Skill{
public:
    test_skill_1(KnowledgeBase *kb, std::shared_ptr<SkillParameters> config);
    void evaluate();
    bool read_skill_parameters(const nlohmann::json& p);
    Eigen::Matrix<double,3,3> get_O_R_TF(const Percept &p);
private:
    void create_config();
    void build_primitives(const Percept& p);
    std::tuple<bool,std::string> check_edges(const Percept& p);
    bool check_local_suc_conditions(const Percept& p);
    bool check_local_err_conditions(const Percept &p);
    void auxiliaries(const Percept& p);
    void parallels();
};
}
