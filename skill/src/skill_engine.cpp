#include "skill/skill_engine.hpp"
//#include "skill/skill.hpp"
#include "skills/null_skill.hpp"
#include "core/core.hpp"
#include "memory/memory.hpp"

namespace mios{

SkillEngine::SkillEngine(Core* core):m_core(core),m_memory(core->get_memory()),m_active_skill(std::make_shared<NullSkill>("NullSkill",m_memory,m_core->get_portal())),m_queue(false){

}

bool SkillEngine::apply_skill_context(const nlohmann::json &task_context, const std::string &skill_name){
    spdlog::info("Applying skill context...");
    return m_memory->apply_skill_context(task_context,skill_name);
}

bool SkillEngine::load_skill(std::shared_ptr<Skill> skill){
    spdlog::info("Loading skill "+skill->get_id()+"...");
    m_active_skill=skill;

    if(m_active_skill->get_valid_control_modes()->find(m_memory->read_parameters()->control.control_mode)==m_active_skill->get_valid_control_modes()->end()){
        spdlog::error("Skill of type " + m_active_skill->get_type() + " is not compatible with the chosen controller pipeline.");
        return false;
    }

    spdlog::info("Grounding objects...");
    if(!m_active_skill->ground_objects()){
        return false;
    }
    spdlog::info("Refreshing percept...");
    if(!m_core->refresh_percept({})){
        return false;
    }
    m_memory->get_parameters()->frames.O_R_T=m_active_skill->get_O_R_T_0(*m_core->get_percept());
    if(!m_core->refresh_percept(m_memory->read_parameters()->frames.O_R_T)){
        return false;
    }
    spdlog::info("Initializing...");
    if(!m_active_skill->initialize(*m_core->get_percept())){
        return false;
    }
    return true;
}

bool SkillEngine::blend_skill_stage_1(){
    m_active_skill->terminate(*m_core->get_percept());
    m_results.insert(std::pair<std::string,SkillResult>(m_active_skill->get_id(),m_active_skill->get_result()));

    m_active_skill=*m_it_skill_queue;
    ++m_it_skill_queue;
    m_memory->apply_reserved_skill_context(m_active_skill->get_id());
    if(!m_active_skill->ground_objects()){
        return false;
    }
    if(m_active_skill->get_valid_control_modes()->find(m_memory->read_parameters()->control.control_mode)==m_active_skill->get_valid_control_modes()->end()){
        spdlog::error("Skill of type " + m_active_skill->get_type() + " is not compatible with the chosen controller pipeline.");
        return false;
    }
    m_memory->get_parameters()->frames.O_R_T=m_active_skill->get_O_R_T_0(*m_core->get_percept());
    return true;
}

bool SkillEngine::blend_skill_stage_2(){
    spdlog::info("Initializing...");
    if(!m_active_skill->initialize(*m_core->get_percept())){
        return false;
    }
    return true;
}

bool SkillEngine::is_last_skill(){
    return m_it_skill_queue==m_skill_queue.end();
}

bool SkillEngine::add_skill(std::shared_ptr<Skill> skill){
    m_skill_queue.push_back(skill);
    return true;
}

void SkillEngine::clear_skill_queue(){
    m_skill_queue.clear();
}

void SkillEngine::clear_results(){
    m_results.clear();
}

ControlReturnType SkillEngine::execute_skill_queue(){
    m_queue=true;
    m_it_skill_queue=m_skill_queue.begin();
    m_active_skill=*m_it_skill_queue;
    ++m_it_skill_queue;

    ControlReturnType result=ControlReturnType::crtException;
    m_memory->apply_reserved_skill_context(m_active_skill->get_id());
    if(!m_active_skill->ground_objects()){
        return result;
    }
    m_memory->get_parameters()->frames.O_R_T=m_active_skill->get_O_R_T_0(*m_core->get_percept());
    if(!m_core->refresh_percept(m_memory->read_parameters()->frames.O_R_T)){
        clear_skill_queue();
        return result;
    }
    spdlog::info("Initializing...");
    if(!m_active_skill->initialize(*m_core->get_percept())){
        clear_skill_queue();
        return result;
    }

    try{
        spdlog::info("Executing skill...");
        result = m_core->execute_skill();
        spdlog::info("Skill ran nominally.");
    }catch(const SkillException& e){
        spdlog::debug(e.what());
        result=ControlReturnType::crtException;
        spdlog::warn("A skill exception occured.");
        m_core->post_execution();
    }
    spdlog::info("Unloading skill...");
    m_active_skill->terminate(*m_core->get_percept());
    m_results.insert(std::pair<std::string,SkillResult>(m_active_skill->get_id(),m_active_skill->get_result()));
    unload_skill();
    if(!m_core->refresh_percept({})){
        clear_skill_queue();
        return ControlReturnType::crtException;
    }
    spdlog::info("Terminating skill...");
    clear_skill_queue();
    return result;
}

bool SkillEngine::is_running_queue(){
    return m_queue;
}

void SkillEngine::unload_skill(){
    m_active_skill=std::make_shared<NullSkill>("NullSkill",m_memory,m_core->get_portal());
}

ControlReturnType SkillEngine::execute_skill(std::shared_ptr<Skill> skill){
    m_queue=false;
    if(!load_skill( skill)){
        spdlog::error("Skill could not be loaded.");
        return ControlReturnType::crtException;
    }
    ControlReturnType result=ControlReturnType::crtException;
    try{
        spdlog::info("Executing skill...");
        result = m_core->execute_skill();
        spdlog::info("Skill ran nominally.");
    }catch(const SkillException& e){
        spdlog::debug(e.what());
        result=ControlReturnType::crtException;
        spdlog::warn("A skill exception occured.");
        m_core->post_execution();
    }
    spdlog::info("Unloading skill...");
    skill->terminate(*m_core->get_percept());
    unload_skill();
    if(!m_core->refresh_percept({})){
        return ControlReturnType::crtException;
    }
    spdlog::info("Terminating skill...");
    return result;
}

void SkillEngine::stop_skill(){
    m_active_skill->invoke_failure();
}

Actuator* SkillEngine::get_next_command(const Percept& percept){
    Actuator* cmd = m_active_skill->cycle(percept);
    return cmd;
}

std::unordered_map<std::string,SkillResult> SkillEngine::get_results(){
    return m_results;
}

}
