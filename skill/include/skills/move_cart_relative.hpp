#pragma once

#include "skill/skill.hpp"

#include "primitives/mp_basic.hpp"

namespace mios {

struct Config_move_cart_relative : public ConfigSkill{
    double speed;
    double acc;
    Eigen::Matrix<double,6,1> DX;
    bool EE;
};

class move_cart_relative : public Skill{
public:
    move_cart_relative();
    ~move_cart_relative();

    void evaluate();
    bool read_skill_parameters(const nlohmann::json& p);

private:

    void create_config();
    void build_primitives(const Percept& p);
    std::tuple<bool,std::string> check_edges(const Percept &p);

    bool check_local_suc_conditions(const Percept &p);
    bool check_local_ex_conditions(const Percept &p);

};

}
