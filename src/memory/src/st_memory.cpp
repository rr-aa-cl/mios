#include "mios/memory/st_memory.hpp"
#include "mios/memory/lt_memory.hpp"
#include "spdlog/spdlog.h"

#include "mirmi_cpp_utils/json/json.hpp"
#include "mirmi_cpp_utils/math/math.hpp"

namespace mios {

STMemory::STMemory():m_environment({{"NullObject",Object("NullObject")},{"EndEffector",Object("EndEffector")},{"NoneObject",Object("NoneObject")}}),m_live_context(LiveContext(&m_environment.at("NullObject"))){
    spdlog::trace("STMemory::STMemory");
}

bool STMemory::is_ok() const{
    spdlog::trace("STMemory::is_ok");
    return true;
}

void STMemory::link_to_lt_memory(LTMemory *lt_memory){
    spdlog::trace("STMemory::link_to_lt_memory");
    m_lt_memory=lt_memory;
}

bool STMemory::initialize(){
    spdlog::trace("STMemory::initialize");
    if(!syncronize_with_lt_memory()){
        return false;
    }
    return true;
}

bool STMemory::syncronize_with_lt_memory(){
    spdlog::trace("STMemory::syncronize_with_lt_memory");
    if(!m_lt_memory->load_environment(m_environment)){
        return false;
    }else{
        return true;
    }
}

void STMemory::put_subtask(const std::string &name, const nlohmann::json &context){
//    if(m_task_data.context.find("subtasks")==m_task_data.context.end()){
//        m_task_data.context["subtasks"]=nlohmann::json();
//    }
//    m_task_data.context["subtasks"][name]=context;
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

void STMemory::set_live_parameter(const std::string &key, const nlohmann::json &value){
    spdlog::trace("STMemory::set_live_parameter");
    std::scoped_lock<std::mutex> lock(m_mtx_live_context);
    m_live_context.live_parameters[key]=value;
}

void STMemory::post_event(const std::string &name, const nlohmann::json &content){
    spdlog::trace("STMemory::post_event");
    if(m_events.find(name)==m_events.end()){
        spdlog::debug("STMemory::post_event("+name+","+content.dump()+")");
        m_events.emplace(std::make_pair(name,Event(name,content)));
    }else{
        spdlog::debug("STMemory::post_event("+name+","+content.dump()+")");
        m_events.erase(m_events.find(name));
        m_events.emplace(std::make_pair(name,Event(name,content)));
    }
}

const Event* STMemory::get_event(const std::string &name) const{
    spdlog::trace("STMemory::get_event");
    if(m_events.find(name)==m_events.end()){
        return nullptr;
    }else{
        return &m_events.at(name);
    }
}

void STMemory::remove_event(const std::string &name){
    spdlog::trace("STMemory::remove_event");
    if(m_events.find(name)!=m_events.end()){
        m_events.erase(m_events.find(name));
    }
}

const std::unordered_map<std::string,Object>* STMemory::get_environment() const{
    spdlog::trace("STMemory::get_environment");
    return &m_environment;
}

std::optional<nlohmann::json> STMemory::get_live_parameter(const std::string &parameter) {
    spdlog::trace("STMemory::get_live_parameter");
    if(!m_mtx_live_context.try_lock()){
        return {};
    }
    if(m_live_context.live_parameters.find(parameter)==m_live_context.live_parameters.end()){
        m_mtx_live_context.unlock();
        return {};
    }else{
        m_mtx_live_context.unlock();
        return m_live_context.live_parameters[parameter];
    }
}

bool STMemory::apply_skill_context(const nlohmann::json task_context, const std::string &skill_id){
    spdlog::trace("STMemory::apply_skill_context");
    if(task_context.find("skills")==task_context.end()){
        spdlog::error("The current task context contains no skills");
        return false;
    }
    if(task_context["skills"].find(skill_id)==task_context["skills"].end()){
        spdlog::error("The current task context contains no skill with id " + skill_id);
        return false;
    }
    if(!m_parameters.control.from_json(task_context["skills"][skill_id]["control"])){
        spdlog::error("Could not apply control parameters from context for skill " + skill_id);
        return false;
    }
    if(!m_parameters.frames.from_json(task_context["skills"][skill_id]["frames"])){
        spdlog::error("Could not apply frames parameters from context for skill " + skill_id);
        return false;
    }
    if(!m_parameters.limits.from_json(task_context["skills"][skill_id]["limits"])){
        spdlog::error("Could not apply limits parameters from context for skill " + skill_id);
        return false;
    }
    if(!m_parameters.skill->from_json(task_context["skills"][skill_id]["skill"])){
        spdlog::error("Could not apply skill parameters from context for skill " + skill_id);
        return false;
    }
    if(!m_parameters.skill->read_global_skill_parameters(task_context["skills"][skill_id]["skill"])){
        spdlog::error("Could not apply global skill parameters from context for skill " + skill_id);
        return false;
    }
    if(!m_parameters.safety.from_json(task_context["skills"][skill_id]["safety"])){
        spdlog::error("Could not apply safety parameters from context for skill " + skill_id);
        return false;
    }
    if(!m_parameters.system.from_json(task_context["skills"][skill_id]["system"])){
        spdlog::error("Could not apply system parameters from context for skill " + skill_id);
        return false;
    }
    if(!m_parameters.user.from_json(task_context["skills"][skill_id]["user"])){
        spdlog::error("Could not apply user parameters from context for skill " + skill_id);
        return false;
    }
    return true;
}

bool STMemory::apply_reserved_skill_context(const std::string& skill_id){
    spdlog::trace("STMemory::apply_reserved_skill_context");
    if(m_reserved_parameters.find(skill_id)==m_reserved_parameters.end()){
        spdlog::error("No parameters reserved for skill with id " + skill_id + ".");
        return false;
    }
    m_parameters=m_reserved_parameters[skill_id];
    return true;
}

bool STMemory::reserve_parameters(const nlohmann::json task_context, const std::string &skill_id){
    spdlog::trace("STMemory::reserve_parameters");
    if(task_context.find("skills")==task_context.end()){
        spdlog::error("The current task context contains no skills");
        return false;
    }
    if(task_context["skills"].find(skill_id)==task_context["skills"].end()){
        spdlog::error("The current task context contains no skill with id " + skill_id);
        return false;
    }
    if(!m_reserved_parameters[skill_id].control.from_json(task_context["skills"][skill_id]["control"])){
        spdlog::error("Could not apply control parameters from context for skill " + skill_id);
        return false;
    }
    if(!m_reserved_parameters[skill_id].frames.from_json(task_context["skills"][skill_id]["frames"])){
        spdlog::error("Could not apply frames parameters from context for skill " + skill_id);
        return false;
    }
    if(!m_reserved_parameters[skill_id].limits.from_json(task_context["skills"][skill_id]["limits"])){
        spdlog::error("Could not apply limits parameters from context for skill " + skill_id);
        return false;
    }
    if(!m_reserved_parameters[skill_id].skill->from_json(task_context["skills"][skill_id]["skill"])){
        spdlog::error("Could not apply skill parameters from context for skill " + skill_id);
        return false;
    }
    if(!m_reserved_parameters[skill_id].skill->read_global_skill_parameters(task_context["skills"][skill_id]["skill"])){
        spdlog::error("Could not apply global skill parameters from context for skill " + skill_id);
        return false;
    }
    if(!m_reserved_parameters[skill_id].safety.from_json(task_context["skills"][skill_id]["safety"])){
        spdlog::error("Could not apply safety parameters from context for skill " + skill_id);
        return false;
    }
    if(!m_reserved_parameters[skill_id].system.from_json(task_context["skills"][skill_id]["system"])){
        spdlog::error("Could not apply system parameters from context for skill " + skill_id);
        return false;
    }
    if(!m_reserved_parameters[skill_id].user.from_json(task_context["skills"][skill_id]["user"])){
        spdlog::error("Could not apply user parameters from context for skill " + skill_id);
        return false;
    }
    return true;
}

void STMemory::clear_reserved_skills(){
    spdlog::trace("STMemory::clear_reserved_skills");
    m_reserved_parameters.clear();
}

void STMemory::clear_skill_parameters(){
    spdlog::trace("STMemory::clear_skill_parameters");
    m_parameters.clear_skill_parameters();
}

bool STMemory::set_default_parameters(){
    spdlog::trace("STMemory::set_default_parameters");
    nlohmann::json default_parameters;
    if(!m_lt_memory->load_default_parameters(default_parameters)){
        return false;
    }
    if(!m_parameters.control.from_json(default_parameters["control"])){
        return false;
    }
    if(!m_parameters.frames.from_json(default_parameters["frames"])){
        return false;
    }
    if(!m_parameters.limits.from_json(default_parameters["limits"])){
        return false;
    }
    if(!m_parameters.system.from_json(default_parameters["system"])){
        return false;
    }
    if(!m_parameters.safety.from_json(default_parameters["safety"])){
        return false;
    }
    if(!m_parameters.user.from_json(default_parameters["user"])){
        return false;
    }
    merge_live_context();
    return true;
}

void STMemory::merge_live_context(){
    spdlog::trace("STMemory::merge_live_context");
    if(m_live_context.grasped_object->name!="NullObject"){
        m_parameters.user.load_m=m_live_context.grasped_object->mass;
        m_parameters.user.load_com=(m_parameters.frames.F_T_EE*mirmi_utils::invert_transformation_matrix(m_live_context.grasped_object->OB_T_gp)).block<3,1>(0,3);
        m_parameters.user.load_I=m_live_context.grasped_object->OB_I;
        m_parameters.frames.EE_T_TCP=mirmi_utils::invert_transformation_matrix(m_live_context.grasped_object->OB_T_gp)*m_live_context.grasped_object->OB_T_TCP;
    }
}

bool STMemory::update_object(const std::string &name, bool teach_width, double teach_force, const Percept& p){
    spdlog::trace("STMemory::update_object(string,bool,Percept)");
    if(name=="NullObject" || name=="NoneObject"){
        spdlog::error("Cannot overwrite NullObject or NoneObject.");
        return false;
    }
    if(m_environment.find(name)==m_environment.end()){
        m_environment.insert(std::make_pair(name,Object(name)));
    }
    m_environment.at(name).O_T_OB=p.proprioception.O_T_EE;//*mirmi_utils::invert_transformation_matrix(m_environment.at(name).OB_T_gp);
    m_environment.at(name).q=p.proprioception.q;
    if(teach_width){
        m_environment.at(name).grasp_width=p.proprioception.finger_width;
    }
    m_environment.at(name).grasp_force=teach_force;
    if(!m_lt_memory->upload_environment_element(m_environment.at(name))){
        return false;
    }
    return true;
}

bool STMemory::update_object(const std::string &name, const nlohmann::json &description){
    spdlog::trace("STMemory::update_object(string,json)");
    if(name=="NullObject" || name=="NoneObject"){
        spdlog::error("Cannot overwrite NullObject or NoneObject");
        return false;
    }
    if(m_environment.find(name)==m_environment.end()){
        m_environment.insert(std::make_pair(name,Object(name)));
    }
    m_environment.at(name).update(description);
    if(!m_lt_memory->upload_environment_element(m_environment.at(name))){
        return false;
    }
    return true;
}

bool STMemory::update_partial_object(const std::string &name, const nlohmann::json &description){
    spdlog::trace("STMemory::update_partial_object");
    if(name=="NullObject" || name=="NoneObject"){
        spdlog::error("Cannot overwrite NullObject or NoneObject.");
        return false;
    }
    if(m_environment.find(name)==m_environment.end()){
        spdlog::error("No object with name " + name + " exists.");
        return false;
    }
    std::optional<double> x,y,z={};
    std::optional<Eigen::Matrix<double,3,3> > R={};
    if(description.find("x")!=description.end()){
        double x_tmp;
        description["x"].get_to(x_tmp);
        x=x_tmp;
    }
    if(description.find("y")!=description.end()){
        double y_tmp;
        description["y"].get_to(y_tmp);
        y=y_tmp;
    }
    if(description.find("z")!=description.end()){
        double z_tmp;
        description["z"].get_to(z_tmp);
        z=z_tmp;
    }
    if(description.find("R")!=description.end()){
        Eigen::Matrix<double,3,3> R_tmp;
        if(!mirmi_utils::read_json_param<double,3,3>(description,"R",R_tmp)){
            spdlog::error("Partial object data update: Rotation matrix is invalid.");
            return false;
        }
        R=R_tmp;
    }
    m_environment.at(name).set_pose(x,y,z,R);
    if(!m_lt_memory->upload_environment_element(m_environment.at(name))){
        return false;
    }
    return true;
}

void STMemory::internal_update(const Percept &p){
//    spdlog::trace("STMemory::internal_update");
    if(m_environment.find("EndEffector")==m_environment.end()){
        m_environment.insert(std::make_pair("EndEffector",Object("EndEffector")));
    }
    m_environment.at("EndEffector").O_T_OB=p.proprioception.O_T_EE;
    m_environment.at("EndEffector").q=p.proprioception.q;

//    m_environment.at(m_live_context.grasped_object->name).O_T_OB=p.proprioception.O_T_EE*mirmi_utils::invert_transformation_matrix(m_live_context.grasped_object->OB_T_gp);
//    m_environment.at(m_live_context.grasped_object->name).q=p.proprioception.q;
}

Object* STMemory::get_object(const std::string &name){
    spdlog::trace("STMemory::get_object");
    if(m_environment.find(name)==m_environment.end()){
        return &m_environment.at("NullObject");
    }else{
        return &m_environment.at(name);
    }
}

}
