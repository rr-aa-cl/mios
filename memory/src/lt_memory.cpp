#include "memory/lt_memory.hpp"
#include "task/task.hpp"
#include "task/taskfactory.hpp"
#include <spdlog/spdlog.h>
#include <msrm_utils/json.hpp>


namespace mios {

LTMemory::LTMemory():m_mongodb_client("mios"){
}

bool LTMemory::is_ok() const{
    if(!m_mongodb_client.health_check()){
        spdlog::error("Database health check failed.");
        return false;
    }
    return true;
}

void LTMemory::link_to_st_memory(STMemory *st_memory){
    m_st_memory=st_memory;
}

bool LTMemory::initialize(){
    spdlog::info("Initializing long-term memory...");
    if(!make_database_consistent()){
        return false;
    }
    return true;
}

bool load_parameters(){

}

bool LTMemory::make_database_consistent(){
    nlohmann::json default_values;
    default_values=m_param.system.get_default_values();
    default_values["name"]="system";
    if(!m_mongodb_client.make_document_consistent("system","parameters",default_values)){
        return false;
    }
    default_values=m_param.control.get_default_values();
    default_values["name"]="control";
    if(!m_mongodb_client.make_document_consistent("control","parameters",default_values)){
        return false;
    }
    default_values=m_param.limits.get_default_values();
    default_values["name"]="limits";
    if(!m_mongodb_client.make_document_consistent("limits","parameters",default_values)){
        return false;
    }
    if(!make_basic_prototypes_consistent()){
        return false;
    }
    if(!m_mongodb_client.health_check()){
        spdlog::error("Could not check database health.");
        return false;
    }
    return true;
}

Parameters* LTMemory::get_parameters(){
    return &m_param;
}

const Parameters* const LTMemory::read_parameters() const{
    return &m_param;
}

std::shared_ptr<Task> LTMemory::load_task(const std::string& task_id, const nlohmann::json& user_context,Core* core){
    std::shared_ptr<Task> task = TaskFactory::create_task(TaskFactory::get_task_name(task_id),core);
    nlohmann::json active_context;
    if(!task->load_context(user_context,active_context)){
        return TaskFactory::create_task(TaskName::TaskName_IdleTask,core);
    }
    m_st_memory->put_task(task_id,task->get_uuid(),active_context);
    return task;
}

bool LTMemory::load_default_parameters(const nlohmann::json &parameters){
    if(!m_mongodb_client.read_document("control","parameters",parameters["control"])){
        return false;
    }
    if(!m_mongodb_client.read_document("frames","parameters",parameters["frames"])){
        return false;
    }
    if(!m_mongodb_client.read_document("system","parameters",parameters["system"])){
        return false;
    }
    if(!m_mongodb_client.read_document("user","parameters",parameters["user"])){
        return false;
    }
    if(!m_mongodb_client.read_document("limits","parameters",parameters["limits"])){
        return false;
    }
    return true;
}

bool LTMemory::load_default_task_context(const std::string task_id,nlohmann::json& task_context){
    return m_mongodb_client.read_document(task_id,"tasks",task_context);
}

bool LTMemory::load_default_skill_context(const std::string skill_type,nlohmann::json& skill_context){
    return m_mongodb_client.read_document(skill_type,"skills",skill_context);
}


}
