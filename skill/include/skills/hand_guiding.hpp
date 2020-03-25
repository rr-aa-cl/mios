#pragma once
#include "skill/skill.hpp"

#include "primitives/mp_basic.hpp"

namespace mios{
struct ConfigSkill_hand_guiding: public ConfigSkill{
std::string skill;
Eigen::Matrix<double,6,1> fix_dim;
Eigen::Matrix<double,6,1> dist_walls;
Eigen::Matrix<double,6,1> use_walls;
};class hand_guiding : public Skill{
public:
hand_guiding();
void evaluate();
bool read_skill_parameters(const nlohmann::json& p);
private:
void create_config();
void build_primitives(const Percept& p);
std::tuple<bool,std::string> check_edges(const Percept& p);
bool check_local_suc_conditions(const Percept& p);
};
}
