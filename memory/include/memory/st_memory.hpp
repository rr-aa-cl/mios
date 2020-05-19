#pragma once

#include <optional>

#include "data_structures/parameters.hpp"
#include "data_structures/task_data.hpp"

namespace mios {

class LTMemory;

class STMemory{
public:
    bool is_ok() const;
    void link_to_lt_memory(LTMemory* lt_memory);
    bool initialize();
    ShortTermParameters* get_parameters();
    void put_task(const std::string& name, const std::string &uuid, const nlohmann::json& context);
    std::optional<TaskData*> get_task_data(std::string task_uuid);
    bool store_task_result(const std::string& task_uuid,const nlohmann::json& task_result);

    void set_live_parameter(const std::string& key, const nlohmann::json& value);
    std::optional<nlohmann::json> get_live_parameter(const std::string& parameter)const;
    bool apply_skill_context(const std::string& skill_id);

private:
    ShortTermParameters m_param;
    Parameters m_parameters;
    LTMemory* m_lt_memory;

    TaskData m_task_data;
};

}
