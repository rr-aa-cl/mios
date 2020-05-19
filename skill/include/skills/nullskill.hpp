#pragma once

#include "skill/skill.hpp"

namespace mios {

struct SkillParametersNullSkill : public SkillParameters{
    bool read_parameters(const nlohmann::json &parameters);

};

class NullSkill : public Skill{
public:
    NullSkill(Memory *memory, std::shared_ptr<SkillParameters> config);
    void evaluate();
private:
    bool build_primitives(const Percept& p);
    std::tuple<bool,std::string> check_edges(const Percept& p);
    bool check_local_suc_conditions(const Percept& p);
    bool check_local_err_conditions(const Percept &p);
};

}
