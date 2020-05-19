#pragma once

#include <nlohmann/json.hpp>
#include <memory>

#include "mongodb_client/mongodb_client.hpp"
#include "data_structures/parameters.hpp"



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

    Parameters* get_parameters();
    const Parameters* const read_parameters() const;

    std::shared_ptr<Task> load_task(const std::string& task_id, const nlohmann::json& user_context, mios::Core *core);
    bool load_default_task_context(const std::string task_id, nlohmann::json &task_context);
    bool load_default_skill_context(const std::string skill_id, nlohmann::json &skill_context);


private:
    bool make_database_consistent();
    bool make_basic_prototypes_consistent();

    MongodbClient m_mongodb_client;
    STMemory* m_st_memory;
};

}
