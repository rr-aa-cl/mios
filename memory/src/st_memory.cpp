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

ShortTermParameters *STMemory::get_parameters(){
    return &m_param;
}

void STMemory::put_task(const std::string &name, const std::string& uuid, const nlohmann::json &context){
    TaskData data;
    data.name=name;
    data.context=context;
    data.result=nlohmann::json();
    m_task_data.insert(std::make_pair(uuid,data));
}

std::optional<PrototypeData*> STMemory::get_prototype_data(std::string prototype_uuid){
    if(m_prototype_data.find(prototype_uuid)==m_prototype_data.end()){
        return {};
    }else{
        return &m_prototype_data[prototype_uuid];
    }
}

bool STMemory::store_prototype_result(const std::string &prototype_uuid, const nlohmann::json &prototype_result){
    if(m_prototype_data.find(prototype_uuid)!=m_prototype_data.end()){
        return false;
    }else{
        m_prototype_data[prototype_uuid].result=prototype_result;
        return true;
    }
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
    if(m_task_data.find("skills")==m_task_data.end()){
        spdlog::error("The current task context contains no skills");
        return false;
    }
    if(m_task_data["skills"].find(skill_id)==m_task_data["skills"].end()){
        spdlog::error("The current task context contains no skill with id " + skill_id);
        return false;
    }
    if(!m_parameters.control.read_parameters(m_task_data.context["skills"][skill_id]["control"])){
        spdlog::error("Could not apply controller parameters from context for skill " + skill_id);
        return false;
    }
    m_parameters.frames.read_parameters(m_task_data.context["skills"][skill_id]["frames"]);
    m_parameters.general.read_parameters(m_task_data.context["skills"][skill_id]["general"]);
    m_parameters.limits.read_parameters(m_task_data.context["skills"][skill_id]["limits"]);
    m_parameters.skill->read_parameters(m_task_data.context["skills"][skill_id]["skill"]);
    m_parameters.system.read_parameters(m_task_data.context["skills"][skill_id]["system"]);
    m_parameters.user.read_parameters(m_task_data.context["skills"][skill_id]["user"]);
}

}
