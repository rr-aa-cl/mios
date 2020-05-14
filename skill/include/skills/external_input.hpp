#pragma once

#include "skill/skill.hpp"
#include "primitives/mp_external.hpp"

namespace mios{
struct SkillParameters_external_input: public SkillParameters{
    std::string name;
    std::string mode;
    unsigned port_recv;
    unsigned port_dst;
    double input_frequency;
    std::string ip_dst;
};class external_input : public Skill{
public:
    external_input();
    void evaluate();
    bool read_skill_parameters(const nlohmann::json& p);
private:
    void create_config();
    void build_primitives(const Percept& p);
    std::tuple<bool,std::string> check_edges(const Percept& p);
    bool check_local_suc_conditions(const Percept& p);
};
}
