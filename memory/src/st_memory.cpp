#include "memory/st_memory.hpp"
#include "memory/lt_memory.hpp"
#include <spdlog/spdlog.h>

#include <msrm_utils/system.hpp>
#include <msrm_utils/math.hpp>

namespace mios {

bool STMemory::is_ok() const{
    return true;
}

void STMemory::link_to_lt_memory(LTMemory *lt_memory){
    m_lt_memory=lt_memory;
}

bool STMemory::initialize(){
    spdlog::info("Initializing short-term memory...");
    if(!syncronize_with_lt_memory()){
        return false;
    }
    return true;
}

bool STMemory::syncronize_with_lt_memory(){
    if(!m_lt_memory->load_environment(m_environment)){
        return false;
    }else{
        return true;
    }
}

void STMemory::put_task(const std::string &name, const nlohmann::json &context){
    m_task_data.name=name;
    m_task_data.context=context;
}

void STMemory::put_subtask(const std::string &name, const nlohmann::json &context){
    if(m_task_data.context.find("subtasks")==m_task_data.context.end()){
        m_task_data.context["subtasks"]=nlohmann::json();
    }
    m_task_data.context["subtasks"][name]=context;
}

LiveContext* STMemory::get_live_context(){
    return &m_live_context;
}

Parameters* STMemory::get_parameters(){
    return &m_parameters;
}

const Parameters* STMemory::read_parameters() const{
    return &m_parameters;
}

const TaskData* STMemory::get_task_data() const{
    return &m_task_data;
}

void STMemory::store_task_result(const std::string& uuid, const TaskResult& result){
    m_task_data.result=result;
    m_lt_memory->save_task_data(uuid,m_task_data);
}

void STMemory::set_live_parameter(const std::string &key, const nlohmann::json &value){
    m_live_context.live_parameters[key]=value;
}

std::optional<nlohmann::json> STMemory::get_live_parameter(const std::string &parameter) const{
    if(m_live_context.live_parameters.find(parameter)==m_live_context.live_parameters.end()){
        return {};
    }else{
        return m_live_context.live_parameters[parameter];
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
    if(!m_parameters.skill->read_global_skill_parameters(m_task_data.context["skills"][skill_id]["skill"])){
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
    merge_live_context();
    return true;
}

void STMemory::merge_live_context(){
    if(m_live_context.grasped_object->name!="NullObject"){
        m_parameters.user.load_m=m_live_context.grasped_object->mass;
        m_parameters.user.load_com=(m_parameters.frames.F_T_EE*msrm_utils::invert_transformation_matrix(m_live_context.grasped_object->OB_T_gp)).block<3,1>(0,3);
        m_parameters.user.load_I=m_live_context.grasped_object->OB_I;
        m_parameters.frames.EE_T_TCP=msrm_utils::invert_transformation_matrix(m_live_context.grasped_object->OB_T_gp)*m_live_context.grasped_object->OB_T_TCP;
    }
}

bool STMemory::update_object(const std::string &name, bool teach_width, const Percept& p){
    if(name=="NullObject"){
        spdlog::error("Cannot overwrite NullObject");
        return false;
    }
    if(m_environment.find(name)==m_environment.end()){
        m_environment.insert(std::make_pair(name,Object(name)));
    }
    m_environment.at(name).O_T_OB=p.proprioception.O_T_EE*msrm_utils::invert_transformation_matrix(m_environment.at(name).OB_T_gp);
    m_environment.at(name).q=p.proprioception.q;
    if(teach_width){
        m_environment.at(name).grasp_width=p.proprioception.finger_width;
    }
    if(!m_lt_memory->upload_environment_element(m_environment.at(name))){
        return false;
    }
    return true;
}

const Object* STMemory::get_object(const std::string &name) const{
    if(m_environment.find(name)==m_environment.end()){
        return &m_environment.at("NullObject");
    }else{
        return &m_environment.at(name);
    }
}

}
