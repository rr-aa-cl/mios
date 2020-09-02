#pragma once

#include <memory>
#include <atomic>

#include "data_structures/percept.hpp"
#include "skill/skill.hpp"

namespace mios {
class Core;
class Actuator;

class SkillEngine{
public:
    SkillEngine(Core* core);

    bool apply_skill_context(const nlohmann::json& task_context, const std::string& skill_name);
    bool execute_skill(std::shared_ptr<Skill> skill);
    void stop_skill();
    Actuator* get_next_command(const Percept& percept);

private:
    bool get_percept(const Percept& p);
    bool load_skill(std::shared_ptr<Skill> skill);
    void unload_skill();
    Core* m_core;
    Memory* m_memory;

    std::shared_ptr<Skill> m_active_skill;
};

}
