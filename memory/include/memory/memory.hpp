#pragma once

#include "memory/lt_memory.hpp"
#include "memory/st_memory.hpp"

namespace mios {

class Task;
class Core;

class Memory{
public:
    Memory();
    Memory(const Memory&) = delete;
    void operator=(Memory const&) = delete;
    bool is_ok() const;

    bool initialize();
    bool load_default_parameters(nlohmann::json& parameters);
    bool set_default_parameters();
    bool apply_skill_context(const std::string skill_id);

    Parameters* get_parameters();
    const Parameters* const read_parameters() const;
    LiveContext* get_live_context();
    bool get_task_data(const std::string uuid,TaskData& data) const;
    bool store_task_result(const std::string& uuid, const nlohmann::json& result);
    std::shared_ptr<Task> load_task(const std::string& task_id, const nlohmann::json& parameters,Core* core);
    std::shared_ptr<Task> load_subtask(const std::string& task_id, const nlohmann::json& parameters,Core* core);
    bool load_default_task_context(const std::string task_id, nlohmann::json &task_context);
    bool load_default_skill_context(const std::string skill_type, nlohmann::json &skill_context);

    void set_live_parameter(const std::string& key, const nlohmann::json& value);
    std::optional<nlohmann::json> get_live_parameter(const std::string& parameter)const;

    bool update_object(const std::string& name,const Percept& p);
    const Object* const get_object(const std::string& name) const;

private:

    LTMemory m_lt_memory;
    STMemory m_st_memory;

};

}
