#include "skill/skill_engine.hpp"
//#include "skill/skill.hpp"
#include "skills/null_skill.hpp"
#include "core/core.hpp"
#include "memory/memory.hpp"

namespace mios{

SkillEngine::SkillEngine(Core* core):m_core(core),m_memory(core->get_memory()),m_active_skill(std::make_shared<NullSkill>("NullSkill",m_memory,m_core->get_portal())){

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

void SkillEngine::unload_skill(){
    m_active_skill=std::make_shared<NullSkill>("NullSkill",m_memory,m_core->get_portal());
}

bool SkillEngine::execute_skill(std::shared_ptr<Skill> skill){
    if(!load_skill( skill)){
        spdlog::error("Skill could not be loaded.");
        return false;
    }
    bool result=false;
    try{
        spdlog::info("Executing skill...");
        result = m_core->execute_skill();
        spdlog::info("Skill ran nominally.");
    }catch(const SkillException& e){
        spdlog::debug(e.what());
        result=false;
        spdlog::warn("A skill exception occured.");
    }
    spdlog::info("Unloading skill...");
    unload_skill();
    if(!m_core->refresh_percept({})){
        return false;
    }
    spdlog::info("Terminating skill...");
    skill->terminate(*m_core->get_percept());
    return result;
}

void SkillEngine::stop_skill(){
    m_active_skill->invoke_failure();
}

Actuator* SkillEngine::get_next_command(const Percept& percept){
    Actuator* cmd = m_active_skill->cycle(percept);
    return cmd;
}

}
