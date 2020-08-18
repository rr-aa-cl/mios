#pragma once

#include <optional>
#include <mutex>

#include "data_structures/parameters.hpp"
#include "data_structures/task_data.hpp"
#include "data_structures/object.hpp"
#include "data_structures/percept.hpp"
#include "data_structures/event.hpp"

namespace mios {

class LTMemory;

class STMemory{
public:
    STMemory();
    bool initialize();
    bool is_ok() const;
    void link_to_lt_memory(LTMemory* lt_memory);
    bool syncronize_with_lt_memory();

    bool apply_skill_context(const nlohmann::json task_context, const std::string& skill_id);
    bool update_object(const std::string& name, bool teach_width, const Percept& p);
    bool update_object(const std::string& name, const nlohmann::json& description);

    void internal_update(const Percept& p);

public:
    bool set_default_parameters();
    void put_task(const std::string& name, const nlohmann::json& context, const TaskResult& result);
    void put_subtask(const std::string& name, const nlohmann::json& context);
    void set_live_parameter(const std::string& key, const nlohmann::json& value);
    void post_event(const std::string& name, const nlohmann::json& content);
    void remove_event(const std::string& name);

public:
    LiveContext* get_live_context();
    Parameters* get_parameters();
    const Parameters* read_parameters() const;
    const TaskData* get_task_data() const;
    std::optional<nlohmann::json> get_live_parameter(const std::string& parameter);
    Object *get_object(const std::string& name);
    const Event* get_event(const std::string& name) const;
    const std::map<std::string, Object>* get_environment() const;

private:

    void merge_live_context();

private:
    std::mutex m_mtx_live_context;
    std::map<std::string,Object> m_environment;
    std::unordered_map<std::string,Event> m_events;
    LiveContext m_live_context;
    Parameters m_parameters;

    LTMemory* m_lt_memory;

};

}
