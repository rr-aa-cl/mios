#pragma once

#include <optional>

#include "data_structures/parameters.hpp"
#include "data_structures/task_data.hpp"
#include "data_structures/object.hpp"

namespace mios {

class LTMemory;

class STMemory{
public:
    bool initialize();
    bool is_ok() const;
    void link_to_lt_memory(LTMemory* lt_memory);

    void put_task(const std::string& name, const nlohmann::json& context);
    void put_subtask(const std::string& name, const nlohmann::json& context);
    void store_task_result(const std::string& uuid, const TaskResult &result);

    LiveContext* get_live_context();
    Parameters* get_parameters();
    const Parameters* const read_parameters() const;
    const TaskData* const get_task_data() const;
    void set_live_parameter(const std::string& key, const nlohmann::json& value);
    std::optional<nlohmann::json> get_live_parameter(const std::string& parameter)const;
    bool apply_skill_context(const std::string& skill_id);

    bool set_default_parameters();

private:
    LiveContext m_live_context;
    Parameters m_parameters;
    TaskData m_task_data;
    std::unordered_map<std::string,Object> m_objects;

    LTMemory* m_lt_memory;

};

}
