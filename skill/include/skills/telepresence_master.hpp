#pragma once

#include <functional>
#include <algorithm>

#include "skill/skill.hpp"

#include "primitives/mp_telepresence.hpp"

namespace mios {

struct ConfigSkill_telepresence_master : public ConfigSkill{
    std::string ip_dst;
    unsigned port_dst;
    unsigned port_recv;
    bool bilateral;

    Eigen::Matrix<double,6,1> K_joystick_on;
    Eigen::Matrix<double,6,1> K_joystick_off;
    Eigen::Matrix<double,6,1> joystick_deadband;
    Eigen::Matrix<double,6,1> joystick_amp;
    Eigen::Matrix<double,6,1> joystick_f_ext_amp;

    TelepresenceMode mode;
};

class telepresence_master : public Skill{
public:
    telepresence_master();

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
