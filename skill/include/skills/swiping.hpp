#pragma once

#include "skill/skill.hpp"

#include "primitives/mp_basic.hpp"

namespace mios{
struct ConfigSkill_swiping: public ConfigSkill{
std::string skill;
double F_c;
Eigen::Matrix<double,2,1> speed;
Eigen::Matrix<double,2,1> acc;
std::vector<std::string> locations;
};
class swiping : public Skill{
public:
swiping();
void evaluate();
bool read_skill_parameters(const nlohmann::json& p);
private:
void create_config();
void build_primitives(const Percept& p);
std::tuple<bool,std::string> check_edges(const Percept& p);
bool check_local_suc_conditions(const Percept& p);
bool check_local_err_conditions(const Percept &p);
void auxiliaries(const Percept& p);

unsigned _n_p;
};
}
