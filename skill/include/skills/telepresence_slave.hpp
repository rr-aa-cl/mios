#pragma once

#include "skill/skill.hpp"

#include "primitives/mp_telepresence.hpp"
#include "primitives/mp_basic.hpp"

namespace mios {

struct ConfigSkill_telepresence_slave : public ConfigSkill{
    std::string ip_dst;
    unsigned port_dst;
    unsigned port_recv;
    bool repeater;

    Eigen::Matrix<double,3,3> EE_T_J_t;
    Eigen::Matrix<double,3,3> EE_T_J_r;

    bool bilateral;
    TelepresenceMode mode;
};

class telepresence_slave : public Skill{
public:
    telepresence_slave();

    void evaluate();
    bool read_skill_parameters(const nlohmann::json& p);

private:

    void create_config();
    void build_primitives(const Percept& p);
    std::tuple<bool,std::string> check_edges(const Percept &p);

    bool check_local_suc_conditions(const Percept &p);
    bool check_local_ex_conditions(const Percept &p);
    bool check_local_err_conditions(const Percept &p);

};

}
