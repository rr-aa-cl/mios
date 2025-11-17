#include "mios/memory/memory.hpp"
#include "spdlog/spdlog.h"

namespace mios {

Memory::Memory(const MiosContext &context):m_lt_memory(context),m_context(context){
    spdlog::trace("Memory::Memory");
    m_st_memory.link_to_lt_memory(&m_lt_memory);
    m_lt_memory.link_to_st_memory(&m_st_memory);
}

bool Memory::is_ok() const{
    spdlog::trace("Memory::is_ok");
    if(!m_lt_memory.is_ok()){
        spdlog::error("Long-term memory state is not ok");
        return false;
    }
    if(!m_st_memory.is_ok()){
        spdlog::error("Short-term memory state is not ok");
        return false;
    }
    return true;
}

bool Memory::initialize(SkillLibrary *skill_library){
    spdlog::trace("Memory::initialize");
    spdlog::info("Initializing long-term memory...");
    m_lt_memory.link_to_skill_library(skill_library);
    if(!m_lt_memory.initialize()){
        spdlog::error("Could not initialize long-term memory.");
        return false;
    }
    spdlog::info("Initializing short-term memory...");
    if(!m_st_memory.initialize()){
        spdlog::error("Could not initialize short-term memory.");
        return false;
    }
    if(!set_default_parameters()){
        spdlog::error("Could not set default parameters.");
        return false;
    }
    return true;
}

bool Memory::load_default_parameters(nlohmann::json& parameters){
    return m_lt_memory.load_default_parameters(parameters);
}

bool Memory::set_default_parameters(){
    return m_st_memory.set_default_parameters();
}

bool Memory::apply_skill_context(const nlohmann::json& context, const std::string skill_id){
    return m_st_memory.apply_skill_context(context, skill_id);
}

bool Memory::apply_reserved_skill_context(const std::string skill_id){
    return m_st_memory.apply_reserved_skill_context(skill_id);
}

void Memory::clear_reserved_skills(){
    m_st_memory.clear_reserved_skills();
}

void Memory::clear_skill_parameters(){
    m_st_memory.clear_skill_parameters();
}

std::shared_ptr<Task> Memory::load_task(const std::string &task_id, const nlohmann::json &parameters,Core* core){
    return m_lt_memory.load_task(task_id,parameters,core);
}

std::shared_ptr<Task> Memory::load_subtask(const std::string &task_id, const nlohmann::json &parameters,Core* core){
    return m_lt_memory.load_subtask(task_id,parameters,core);
}

bool Memory::load_default_task_context(const std::string task_id, nlohmann::json &task_context){
    return m_lt_memory.load_default_task_context(task_id,task_context);
}

bool Memory::load_default_skill_context(const std::string skill_type, nlohmann::json &skill_context){
    return m_lt_memory.load_default_skill_context(skill_type,skill_context);
}

Parameters* Memory::get_parameters(){
    return m_st_memory.get_parameters();
}

const Parameters* Memory::read_parameters() const{
    return m_st_memory.read_parameters();
}

LiveContext *Memory::get_live_context(){
    return m_st_memory.get_live_context();
}

bool Memory::get_task_data(const std::string uuid, TaskData &data) const{
    return m_lt_memory.get_task_data(uuid,data);
}

void Memory::store_task_data(const std::string &uuid, const std::string& task_id, const nlohmann::json& context, const TaskResult& result){
    m_lt_memory.store_task_data(uuid, task_id, context, result);
}

void Memory::store_log_data(const nlohmann::json &content){
    if(!m_lt_memory.upload_log_element(content)){
        spdlog::error("Error uploading datalog to storage.");
    }
    else{
        
        spdlog::info("Datalog successfully uploaded to data storage");
    }
}

void  Memory::set_live_parameter(const std::string &key, const nlohmann::json &value){
    m_st_memory.set_live_parameter(key,value);
}

std::optional<nlohmann::json> Memory::get_live_parameter(const std::string &parameter){
    return m_st_memory.get_live_parameter(parameter);
}

bool Memory::update_object(const std::string &name, bool teach_width,double teach_force, const Percept &p){
    return m_st_memory.update_object(name,teach_width,teach_force,p);
}

bool Memory::update_object(const std::string &name, const nlohmann::json &description){
    return m_st_memory.update_object(name, description);
}

bool Memory::update_partial_object(const std::string &name, const nlohmann::json &description){
    return m_st_memory.update_partial_object(name,description);
}

Object* Memory::get_object(const std::string& name){
    return m_st_memory.get_object(name);
}

bool Memory::update_database(){
    return m_lt_memory.update_database();
}

void Memory::internal_update(const Percept &p){
    m_st_memory.internal_update(p);
}

void Memory::post_event(const std::string &name, const nlohmann::json &content){
    m_st_memory.post_event(name,content);
}

const Event* Memory::get_event(const std::string &name){
    return m_st_memory.get_event(name);
}

void Memory::remove_event(const std::string &name){
    m_st_memory.remove_event(name);
}

}
