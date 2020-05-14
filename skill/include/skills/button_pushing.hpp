#pragma once
#include "skill/skill.hpp"

#include "primitives/mp_basic.hpp"

namespace mios{
struct SkillParameters_button_pushing: public SkillParameters{
std::string skill;
Eigen::Matrix<double,1,1> speed;
Eigen::Matrix<double,1,1> acc;
double t_hold;
std::array<std::string,1> objects;
};class button_pushing : public Skill{
public:
button_pushing();
~button_pushing();
void evaluate();
bool read_skill_parameters(const nlohmann::json& p);
Eigen::Matrix<double,3,3> get_O_R_TF(const Percept& p);
private:
void create_config();
void build_primitives(const Percept& p);
std::tuple<bool,std::string> check_edges(const Percept& p);
bool check_local_suc_conditions(const Percept& p);
bool check_local_ex_conditions(const Percept &p);
bool check_local_err_conditions(const Percept &p);

bool _push_blind;
double _button_radius;
double _button_height;
double _t_start_hold;
};
}
