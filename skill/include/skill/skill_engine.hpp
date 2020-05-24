#pragma once

#include <memory>
#include <atomic>

#include "data_structures/percept.hpp"
#include "skill/skill.hpp"

namespace mios {
class Core;
class Memory;
class Percept;
class Actuator;

class SkillEngine{
public:
    SkillEngine(Core* core);

    bool execute_skill(std::shared_ptr<Skill> skill);
    void stop_skill(bool success);
    Actuator* get_next_command(const Percept& percept);

//    template<typename T>void execute_skill(const std::string &name){
//        Percept p;
//        if(!get_percept(p)){
//            return false;
//        }

//        std::shared_ptr<Skill> skill = std::make_shared<T>(name,m_memory,m_context[name],p);
//        spdlog::info("Executing skill "+name+".");
//        if(!m_skill_engine->execute_skill(skill)){
//            throw TaskException("Could not execute skill " + name + ".");
//        }
//        m_result.m_skill_results.emplace(std::make_pair(name,skill->get_result()));
//        m_flag_stop = skill->get_result().exception;
//    }

private:
    bool get_percept(const Percept& p);
    bool load_skill(std::shared_ptr<Skill> skill);
    void unload_skill();
    Core* m_core;
    Memory* m_memory;

    std::shared_ptr<Skill> m_active_skill;
};

}
