#include "memory/memory.hpp"
#include <spdlog/spdlog.h>

namespace mios {

Memory::Memory(){
    m_st_memory.link_to_lt_memory(&m_lt_memory);
    m_lt_memory.link_to_st_memory(&m_st_memory);
}

bool Memory::is_ok() const{
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

bool Memory::initialize(){
    if(!m_lt_memory.initialize()) return false;
    if(!m_st_memory.initialize()) return false;
    return true;
}

bool Memory::load_default_parameters(nlohmann::json& parameters){
    return m_lt_memory.load_default_parameters(parameters);
}

bool Memory::set_default_parameters(){
    return m_st_memory.set_default_parameters();
}

bool Memory::apply_skill_context(const std::string skill_id){
    return m_st_memory.apply_skill_context(skill_id);
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

const Parameters* const Memory::read_parameters() const{
    return m_st_memory.read_parameters();
}

LiveContext *Memory::get_live_context(){
    return m_st_memory.get_live_context();
}

bool Memory::get_task_data(const std::string uuid, TaskData &data) const{
    return m_lt_memory.get_task_data(uuid,data);
}

bool Memory::store_task_result(const std::string &uuid, const nlohmann::json &result){
    return m_st_memory.store_task_result(uuid,result);
}

void  Memory::set_live_parameter(const std::string &key, const nlohmann::json &value){
    m_st_memory.set_live_parameter(key,value);
}

std::optional<nlohmann::json> Memory::get_live_parameter(const std::string &parameter) const{
    return m_st_memory.get_live_parameter(parameter);
}

}
