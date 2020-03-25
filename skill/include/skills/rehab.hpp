#pragma once
#include "skill/skill.hpp"

#include "primitives/mp_basic.hpp"

//#include "primitives/mp_rehab.hpp"

namespace mios{


struct ConfigSkill_rehab : public ConfigSkill{
    double a_z;
    double a_y;
    double a_x;
    double a_r;
    double f_z;
    double f_y;
    double f_x;
    double f_r;
    double phi_x;
    double phi_y;
    double stiffness; //Range 150 ... 1200
    double speed;     //Range 0.2 ... 1.0
    std::string motion;
};

class rehab : public Skill{
public:
    rehab();
    ~rehab();
    void evaluate();
    bool read_skill_parameters(const nlohmann::json& p);

private:
    void create_config();
    void build_primitives(const Percept& p);
    std::tuple<bool,std::string> check_edges(const Percept& p);
    bool check_local_suc_conditions(const Percept& p);

};
}
