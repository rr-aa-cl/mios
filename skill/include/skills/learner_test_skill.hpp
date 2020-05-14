#pragma once
#include "skill/skill.hpp"
#include "primitives/mp_basic.hpp"
namespace mios{
struct SkillParameters_learner_test_skill: public SkillParameters{
std::string skill;
Eigen::Matrix<double,6,1> x;
double A;
double selector;
};class learner_test_skill : public Skill{
public:
learner_test_skill();
~learner_test_skill();
void evaluate();
bool read_skill_parameters(const nlohmann::json& p);
private:
void create_config();
void build_primitives(const Percept& p);
std::tuple<bool,std::string> check_edges(const Percept& p);
bool check_local_suc_conditions(const Percept& p);
};
}
