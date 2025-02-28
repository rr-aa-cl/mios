#pragma once

#include "mios/data_structures/percept.hpp"
#include "mios/skill/skill.hpp"
#include "mios/utils/types.hpp"
#include "mios/data_structures/results.hpp"

#include "nlohmann/json.hpp"
#include "spdlog/spdlog.h"

#include <memory>
#include <list>
#include <unordered_map>
#include <string>


namespace mios {
class Core;
class Actuator;

class SkillEngine{
public:
    SkillEngine(Core* core);

    bool apply_skill_context(const nlohmann::json& task_context, const std::string& skill_name);
    ControlReturnType execute_skill(std::shared_ptr<Skill> skill);
    void stop_skill();
    Actuator* get_next_command(const Percept& percept);
    bool add_skill(std::shared_ptr<Skill> skill);
    void clear_skill_queue();
    void clear_results();
    ControlReturnType execute_skill_queue();
    bool blend_skill_stage_1();
    bool blend_skill_stage_2();
    bool is_last_skill();

    bool is_running_queue();
    template<typename T>bool reserve_skill_context(const nlohmann::json task_context, const std::string& skill_id){
        spdlog::trace("SkillEngine::reserve_skill_context");
        return m_memory->reserve_skill_context<T>(task_context,skill_id);
    }
    std::unordered_map<std::string, SkillResult> get_results();

    void log_data(const Percept& p);

private:
    void init_logs(const nlohmann::json& log_meta);
    void write_logs();
    bool get_percept(const Percept& p);
    bool load_skill(std::shared_ptr<Skill> skill);
    void unload_skill();
    Core* m_core;
    Memory* m_memory;

    std::shared_ptr<Skill> m_active_skill;
    std::list<std::shared_ptr<Skill> > m_skill_queue;
    std::list<std::shared_ptr<Skill> >::iterator m_it_skill_queue;
    std::unordered_map<std::string,SkillResult> m_results;
    bool m_queue;

    std::vector<nlohmann::json> m_data_log;
    nlohmann::json m_log_meta;
    long m_log_cnt;

};

}
