#pragma once

#include "mios/memory/lt_memory.hpp"
#include "mios/memory/st_memory.hpp"
#include "mios/data_structures/event.hpp"
#include "mios/data_structures/parameters.hpp"
#include "mios/data_structures/task_data.hpp"
#include "mios/data_structures/percept.hpp"

#include "nlohmann/json.hpp"

#include <optional>
#include <memory>
#include <string>

namespace mios {

class Task;
class Core;

class Memory{
public:
    Memory(unsigned database_port, std::string robot_arm);
    Memory(const Memory&) = delete;
    void operator=(Memory const&) = delete;
    bool is_ok() const;

    bool initialize(SkillLibrary* skill_library, unsigned robot_configuration);
    bool load_default_parameters(nlohmann::json& parameters);
    bool set_default_parameters();
    bool apply_skill_context(const nlohmann::json& context, const std::string skill_id);
    bool apply_reserved_skill_context(const std::string skill_id);

    void store_task_data(const std::string& uuid, const std::string& task_id, const nlohmann::json& context, const TaskResult& result);
    std::shared_ptr<Task> load_task(const std::string& task_id, const nlohmann::json& parameters,Core* core);
    std::shared_ptr<Task> load_subtask(const std::string& task_id, const nlohmann::json& parameters,Core* core);
    bool load_default_task_context(const std::string task_id, nlohmann::json &task_context);
    bool load_default_skill_context(const std::string skill_type, nlohmann::json &skill_context);

    void set_live_parameter(const std::string& key, const nlohmann::json& value);

    bool update_object(const std::string& name, bool teach_width, const Percept& p);
    bool update_object(const std::string& name, const nlohmann::json& description);
    bool update_partial_object(const std::string& name, const nlohmann::json& description);

    void internal_update(const Percept& p);

    bool update_database();
    void post_event(const std::string& name, const nlohmann::json& content);
    void remove_event(const std::string& name);

    void clear_reserved_skills();
    void clear_skill_parameters();
    template<typename T>bool reserve_skill_context(const nlohmann::json task_context, const std::string& skill_id){
        return m_st_memory.reserve_skill_context<T>(task_context,skill_id);
    }

public:
    std::optional<nlohmann::json> get_live_parameter(const std::string& parameter);
    Parameters* get_parameters();
    const Parameters *read_parameters() const;
    LiveContext* get_live_context();
    bool get_task_data(const std::string uuid,TaskData& data) const;
    Object *get_object(const std::string& name);
    const Event* get_event(const std::string& name);
    std::string m_robot_arm;

    LTMemory m_lt_memory;
private:
    
    STMemory m_st_memory;

};

}
