#include "memory/st_memory.hpp"
#include <spdlog/spdlog.h>

#include <msrm_utils/system.hpp>

#include <sstream>
#include <boost/uuid/uuid_generators.hpp>
#include <boost/uuid/uuid.hpp>
#include <boost/uuid/uuid_io.hpp>

namespace mios {

bool STMemory::is_ok() const{
    return true;
}

void STMemory::link_to_lt_memory(LTMemory *lt_memory){
    m_lt_memory=lt_memory;
}

bool STMemory::initialize(){
    spdlog::info("Initializing short-term memory...");
    return true;
}

LiveContext *STMemory::get_parameters(){
    return &m_param;
}

void STMemory::put_task(const std::string &name, const nlohmann::json &context){
    m_task_data.name=name;
    m_task_data.context=context;
    m_task_data.result=nlohmann::json();
}

void STMemory::put_subtask(const std::string &name, const nlohmann::json &context){
    if(m_task_data.context.find("subtasks")==m_task_data.context.end()){
        m_task_data.context["subtasks"]=nlohmann::json();
    }
    if(m_task_data.result.find("subtasks")==m_task_data.result.end()){
        m_task_data.result["subtasks"]=nlohmann::json();
    }
    m_task_data.context["subtasks"][name]=context;
    m_task_data.result["subtasks"][name]=nlohmann::json();
}

LiveContext* STMemory::get_live_context(){
    return &m_live_context;
}

Parameters* STMemory::get_parameters(){
    return &m_parameters;
}

const Parameters* const STMemory::read_parameters() const{
    return &m_parameters;
}

const TaskData* const STMemory::get_task_data() const{
    return &m_task_data;
}

void STMemory::store_task_result(const std::string uuid, const TaskResult& result){
    m_task_data.result=result;
    m_lt_memory->save_task_data(uuid,m_task_data);
}

void STMemory::set_live_parameter(const std::string &key, const nlohmann::json &value){
    m_param.live_parameters[key]=value;
}

std::optional<nlohmann::json> STMemory::get_live_parameter(const std::string &parameter) const{
    if(m_param.live_parameters.find(parameter)==m_param.live_parameters.end()){
        return {};
    }else{
        return m_param.live_parameters[parameter];
    }
}

bool STMemory::apply_skill_context(const std::string &skill_id){
    if(m_task_data.context.find("skills")==m_task_data.context.end()){
        spdlog::error("The current task context contains no skills");
        return false;
    }
    if(m_task_data.context["skills"].find(skill_id)==m_task_data.context["skills"].end()){
        spdlog::error("The current task context contains no skill with id " + skill_id);
        return false;
    }
    if(!m_parameters.control.read_parameters(m_task_data.context["skills"][skill_id]["control"])){
        spdlog::error("Could not apply controller parameters from context for skill " + skill_id);
        return false;
    }
    if(!m_parameters.frames.read_parameters(m_task_data.context["skills"][skill_id]["frames"])){
        return false;
    }
    if(!m_parameters.limits.read_parameters(m_task_data.context["skills"][skill_id]["limits"])){
        return false;
    }
    if(!m_parameters.skill->read_parameters(m_task_data.context["skills"][skill_id]["skill"])){
        return false;
    }
    if(!m_parameters.system.read_parameters(m_task_data.context["skills"][skill_id]["system"])){
        return false;
    }
    if(!m_parameters.user.read_parameters(m_task_data.context["skills"][skill_id]["user"])){
        return false;
    }
    return true;
}

bool STMemory::set_default_parameters(){
    nlohmann::json default_parameters;
    if(!m_lt_memory->load_default_parameters(default_parameters)){
        return false;
    }
    if(!m_parameters.control.read_parameters(default_parameters["control"])){
        return false;
    }
    if(!m_parameters.frames.read_parameters(default_parameters["frames"])){
        return false;
    }
    if(!m_parameters.limits.read_parameters(default_parameters["limits"])){
        return false;
    }
    if(!m_parameters.system.read_parameters(default_parameters["system"])){
        return false;
    }
    if(!m_parameters.user.read_parameters(default_parameters["user"])){
        return false;
    }
    return true;
}

}
