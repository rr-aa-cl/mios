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
    }else{
        return true;
    }
}

bool load_parameters(){

}

bool LTMemory::make_database_consistent(){
    nlohmann::json default_values;
    default_values=SystemParameters::get_default_values();
    default_values["name"]="system";
    if(!m_mongodb_client.make_document_consistent("system","parameters",default_values)){
        return false;
    }
    default_values=ControlParameters::get_default_values();
    default_values["name"]="control";
    if(!m_mongodb_client.make_document_consistent("control","parameters",default_values)){
        return false;
    }
    default_values=LimitParameters::get_default_values();
    default_values["name"]="limits";
    if(!m_mongodb_client.make_document_consistent("limits","parameters",default_values)){
        return false;
    }
    default_values=FramesParameters::get_default_values();
    default_values["name"]="frames";
    if(!m_mongodb_client.make_document_consistent("frames","parameters",default_values)){
        return false;
    }
    default_values=UserParameters::get_default_values();
    default_values["name"]="user";
    if(!m_mongodb_client.make_document_consistent("user","parameters",default_values)){
        return false;
    }
    if(!m_mongodb_client.health_check()){
        spdlog::error("Could not check database health.");
        return false;
    }
    return true;
}

bool LTMemory::get_task_data(const std::string uuid, TaskData &data) const{
    if(m_task_data.find(uuid)==m_task_data.end()){
        return false;
    }else{
        data=m_task_data.at(uuid);
        return true;
    }
}

std::shared_ptr<Task> LTMemory::load_task(const std::string& task_id, const nlohmann::json& user_context,Core* core){
    std::shared_ptr<Task> task = TaskFactory::create_task(TaskFactory::get_task_name(task_id),core);
    nlohmann::json active_context;
    task->initialize_task();
    if(!task->load_context(user_context,active_context)){
        return TaskFactory::create_task(TaskName::TaskName_IdleTask,core);
    }
    m_st_memory->put_task(task_id,active_context);
    return task;
}

std::shared_ptr<Task> LTMemory::load_subtask(const std::string& task_id, const nlohmann::json& user_context,Core* core){
    std::shared_ptr<Task> task = TaskFactory::create_task(TaskFactory::get_task_name(task_id),core);
    nlohmann::json active_context;
    task->initialize_task();
    if(!task->load_context(user_context,active_context)){
        return TaskFactory::create_task(TaskName::TaskName_IdleTask,core);
    }
    m_st_memory->put_subtask(task_id,active_context);
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

void LTMemory::save_task_data(const std::string &uuid, const TaskData &data){
    m_task_data.insert(std::make_pair(uuid,data));
}


}
