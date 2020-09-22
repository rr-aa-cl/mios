#include "memory/st_memory.hpp"
#include "memory/lt_memory.hpp"
#include <spdlog/spdlog.h>

#include "msrm_utils/json.hpp"
#include "msrm_utils/system.hpp"
#include "msrm_utils/math.hpp"

namespace mios {

STMemory::STMemory():m_environment({{"NullObject",Object("NullObject")},{"EndEffector",Object("EndEffector")}}),m_live_context(LiveContext(&m_environment.at("NullObject"))){

}

bool STMemory::is_ok() const{
    return true;
}

void STMemory::link_to_lt_memory(LTMemory *lt_memory){
    m_lt_memory=lt_memory;
}

bool STMemory::initialize(){
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
    std::scoped_lock<std::mutex> lock(m_mtx_live_context);
    m_live_context.live_parameters[key]=value;
}

void STMemory::post_event(const std::string &name, const nlohmann::json &content){
    if(m_events.find(name)==m_events.end()){
        m_events.emplace(std::make_pair(name,Event(name,content)));
    }else{
        m_events.erase(m_events.find(name));
        m_events.emplace(std::make_pair(name,Event(name,content)));
    }
}

const Event* STMemory::get_event(const std::string &name) const{
    if(m_events.find(name)==m_events.end()){
        return nullptr;
    }else{
        return &m_events.at(name);
    }
}

void STMemory::remove_event(const std::string &name){
    if(m_events.find(name)!=m_events.end()){
        m_events.erase(m_events.find(name));
    }
}

const std::map<std::string,Object>* STMemory::get_environment() const{
    return &m_environment;
}

std::optional<nlohmann::json> STMemory::get_live_parameter(const std::string &parameter) {
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

bool STMemory::set_default_parameters(){
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

bool STMemory::update_object(const std::string &name, const nlohmann::json &description){
    if(name=="NullObject"){
        spdlog::error("Cannot overwrite NullObject");
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
    if(name=="NullObject"){
        spdlog::error("Cannot overwrite NullObject");
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
        if(!msrm_utils::read_json_param<double,3,3>(description,"R",R_tmp)){
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
    // Update special objects
//    spdlog::debug("STMemory::internal_update()");
    if(m_environment.find("EndEffector")==m_environment.end()){
        m_environment.insert(std::make_pair("EndEffector",Object("EndEffector")));
    }
    m_environment.at("EndEffector").O_T_OB=p.proprioception.O_T_EE;
    m_environment.at("EndEffector").q=p.proprioception.q;

    m_environment.at(m_live_context.grasped_object->name).O_T_OB=p.proprioception.O_T_EE*msrm_utils::invert_transformation_matrix(m_live_context.grasped_object->OB_T_gp);
    m_environment.at(m_live_context.grasped_object->name).q=p.proprioception.q;
}

Object* STMemory::get_object(const std::string &name){
    spdlog::debug("STMemory: get_object("+name+")");
    if(m_environment.find(name)==m_environment.end()){
        return &m_environment.at("NullObject");
    }else{
        return &m_environment.at(name);
    }
}

}
