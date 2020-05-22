#pragma once

#include <nlohmann/json.hpp>
#include <memory>
#include <unordered_map>

#include "mongodb_client/mongodb_client.hpp"
#include "data_structures/parameters.hpp"
#include "data_structures/task_data.hpp"



namespace mios {

class STMemory;
class Task;
class Core;

class LTMemory{
public:
    LTMemory();
    bool is_ok() const;
    void link_to_st_memory(STMemory* st_memory);
    bool initialize();
    bool load_default_parameters(const nlohmann::json& parameters);

    bool get_task_data(const std::string uuid,TaskData& data) const;

    std::shared_ptr<Task> load_task(const std::string& task_id, const nlohmann::json& user_context, mios::Core *core);
    std::shared_ptr<Task> load_subtask(const std::string& task_id, const nlohmann::json& user_context, mios::Core *core);
    bool load_default_task_context(const std::string task_id, nlohmann::json &task_context);
    bool load_default_skill_context(const std::string skill_id, nlohmann::json &skill_context);

    void save_task_data(const std::string& uuid,const TaskData& data);

    bool load_environment(std::unordered_map<std::string,Object>& environment);
    bool upload_environment_element(const Object &element);

private:
    bool make_database_consistent();

    MongodbClient m_mongodb_client;
    STMemory* m_st_memory;

    std::unordered_map<std::string,TaskData> m_task_data;
};

}
