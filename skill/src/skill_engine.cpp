#include "skill/skill_engine.hpp"
//#include "skill/skill.hpp"
#include "skills/nullskill.hpp"
#include "core/core.hpp"
#include "memory/memory.hpp"

namespace mios{

SkillEngine::SkillEngine(Core* core):m_core(core),m_memory(core->get_memory()){

}

bool SkillEngine::load_skill(std::shared_ptr<Skill> skill){
    spdlog::info("Loading skill "+skill->get_id()+".");
    m_active_skill=skill;
    m_core->refresh_percept({});
    m_active_skill->write_O_R_TF_to_config(*m_core->get_percept());
    m_core->refresh_percept(m_memory->read_parameters()->frames.O_R_T);
    spdlog::info("Applying skill context...");
    m_memory->apply_skill_context(m_active_skill->get_id());
    m_active_skill->ground_objects();
    spdlog::info("Initializing skill...");
    if(!m_active_skill->initialize(*m_core->get_percept())){
        return false;
    }
    return true;
}

void SkillEngine::unload_skill(){
    m_active_skill=std::make_shared<NullSkill>("NullSkill",m_memory,*m_core->get_percept());
}

bool SkillEngine::execute_skill(std::shared_ptr<Skill> skill){
    if(!load_skill(skill)){
        spdlog::error("Skill could not be loaded.");
        return false;
    }
    return m_core->execute_skill();
    unload_skill();
    skill->terminate();
}

void SkillEngine::stop_skill(bool success){
    if(success){
        m_active_skill->invoke_success();
    }else{
        m_active_skill->invoke_failure();
    }
}

Actuator* SkillEngine::get_next_command(const Percept& percept){
    Actuator* cmd = m_active_skill->cycle(percept);
    return cmd;
}

}
