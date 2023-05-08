#pragma once

#include "mios/mongodb_client/mongodb_client.hpp"
#include "mios/data_structures/object.hpp"
#include "mios/data_structures/task_data.hpp"

#include "nlohmann/json.hpp"

#include <string>
#include <memory>
#include <unordered_map>


namespace mios {

class STMemory;
class Task;
class Core;
class SkillLibrary;

class LTMemory{
public:
    LTMemory(unsigned database_port, std::string robot_arm);
    bool is_ok() const;
    void link_to_st_memory(STMemory* st_memory);
    void link_to_skill_library(SkillLibrary* skill_library);
    bool initialize(unsigned robot_configuration);
    bool load_default_parameters(nlohmann::json &parameters);

    bool get_task_data(const std::string uuid,TaskData& data) const;

    std::shared_ptr<Task> load_task(const std::string& task_id, const nlohmann::json& user_context, Core *core);
    std::shared_ptr<Task> load_subtask(const std::string& task_id, const nlohmann::json& user_context, Core *core);
    bool load_default_task_context(const std::string task_id, nlohmann::json &task_context);
    bool load_default_skill_context(const std::string skill_id, nlohmann::json &skill_context);

    void store_task_data(const std::string& uuid, const std::string& task_id, const nlohmann::json& context, const TaskResult& result);

    bool load_environment(std::unordered_map<std::string, Object> &environment);
    bool upload_environment_element(const Object &element);

    bool update_database();

    unsigned m_database_port;

private:
    bool make_database_consistent();
    bool make_default_skills_consistent();
    bool make_default_tasks_consistent();
    bool make_default_environment_consistent();

    MongodbClient m_mongodb_client;
    STMemory* m_st_memory;

    std::unordered_map<std::string,TaskData> m_task_data;

    SkillLibrary* m_skill_library;
};

}
