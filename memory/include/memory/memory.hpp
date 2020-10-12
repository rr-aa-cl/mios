#pragma once

#include "memory/lt_memory.hpp"
#include "memory/st_memory.hpp"

namespace mios {

class Task;
class Core;

class Memory{
public:
    Memory(unsigned database_port);
    Memory(const Memory&) = delete;
    void operator=(Memory const&) = delete;
    bool is_ok() const;

    bool initialize(SkillLibrary* skill_library);
    bool load_default_parameters(nlohmann::json& parameters);
    bool set_default_parameters();
    bool apply_skill_context(const nlohmann::json& context, const std::string skill_id);

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

public:
    std::optional<nlohmann::json> get_live_parameter(const std::string& parameter);
    Parameters* get_parameters();
    const Parameters *read_parameters() const;
    LiveContext* get_live_context();
    bool get_task_data(const std::string uuid,TaskData& data) const;
    Object *get_object(const std::string& name);
    const Event* get_event(const std::string& name);

private:
    LTMemory m_lt_memory;
    STMemory m_st_memory;

};

}
