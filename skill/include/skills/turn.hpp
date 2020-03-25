#pragma once
#include "skill/skill.hpp"
#include "primitives/mp_basic.hpp"
namespace mios{
struct ConfigSkill_turn: public ConfigSkill{
std::string skill;
Eigen::Matrix<double,1,1> angle;
Eigen::Matrix<double,1,1> speed;
Eigen::Matrix<double,1,1> F_z;
bool clockwise;
std::array<std::string,1> objects;
};class turn : public Skill{
public:
turn();
void evaluate();
bool read_skill_parameters(const nlohmann::json& p);
private:
void create_config();
void build_primitives(const Percept& p);
std::tuple<bool,std::string> check_edges(const Percept& p);
bool check_local_suc_conditions(const Percept& p);
Eigen::Matrix<double,3,3> get_O_R_TF(const Percept &p);
};
}
