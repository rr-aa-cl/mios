#pragma once

#include "skill/skill.hpp"
#include "primitives/mp_basic.hpp"
#include "primitives/mp_basic_joint.hpp"


namespace mios{
struct ConfigSkill_follow_trajectory: public ConfigSkill{
std::vector<std::string> locations;
bool flag_cart;
Eigen::Matrix<double,2,1> speed;
Eigen::Matrix<double,2,1> acc;
double t_settle;
};class follow_trajectory : public Skill{
public:
follow_trajectory();
void evaluate();
bool read_skill_parameters(const nlohmann::json& p);
private:
void create_config();
void build_primitives(const Percept& p);
std::tuple<bool,std::string> check_edges(const Percept& p);
bool check_local_suc_conditions(const Percept& p);
bool check_local_ex_conditions(const Percept &p);

double _t_settle;
bool _flag_settle;
unsigned _cnt_mp;

};
}
