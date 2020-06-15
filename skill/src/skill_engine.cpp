#include "skill/skill_engine.hpp"
//#include "skill/skill.hpp"
#include "skills/nullskill.hpp"
#include "core/core.hpp"
#include "memory/memory.hpp"

namespace mios{

SkillEngine::SkillEngine(Core* core):m_core(core),m_memory(core->get_memory()),m_active_skill(std::make_shared<NullSkill>("NullSkill",m_memory,m_core->get_portal(),*m_core->get_percept())){

}

bool SkillEngine::load_skill(const nlohmann::json task_context, std::shared_ptr<Skill> skill){
    spdlog::info("Loading skill "+skill->get_id()+".");
    m_active_skill=skill;
    spdlog::info("Applying skill context...");
    if(!m_memory->apply_skill_context(task_context,m_active_skill->get_id())){
        return false;
    }
    if(!m_active_skill->ground_objects()){
        return false;
    }
    if(!m_core->refresh_percept({})){
        return false;
    }
    m_memory->get_parameters()->frames.O_R_T=m_active_skill->get_O_R_T_0(*m_core->get_percept());
    if(!m_core->refresh_percept(m_memory->read_parameters()->frames.O_R_T)){
        return false;
    }
    spdlog::info("Initializing skill...");
    if(!m_active_skill->initialize(*m_core->get_percept())){
        return false;
    }
    return true;
}

void SkillEngine::unload_skill(){
    m_active_skill=std::make_shared<NullSkill>("NullSkill",m_memory,m_core->get_portal(),*m_core->get_percept());
}

bool SkillEngine::execute_skill(const nlohmann::json& task_context, std::shared_ptr<Skill> skill){
    if(!load_skill(task_context, skill)){
        spdlog::error("Skill could not be loaded.");
        return false;
    }
    bool result=false;
    m_core->get_ros_node()->start();
    try{
         result = m_core->execute_skill();
    }catch(const SkillException& e){
        spdlog::debug(e.what());
        result=false;
    }
    m_core->get_ros_node()->stop();
    unload_skill();
    if(!m_core->refresh_percept({})){
        return false;
    }
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
