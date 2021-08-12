#include "mios/skill/skill_engine.hpp"
#include "mios/skills/null_skill.hpp"
#include "mios/core/core.hpp"
#include "mios/memory/memory.hpp"
#include "msrm_cpp_utils/files/files.hpp"
#include "boost/filesystem.hpp"

namespace mios{

SkillEngine::SkillEngine(Core* core):m_core(core),m_memory(core->get_memory()),m_active_skill(std::make_shared<NullSkill>("NullSkill",m_memory,m_core->get_portal())),m_queue(false){
spdlog::trace("SkillEngine::SkillEngine");
}

bool SkillEngine::apply_skill_context(const nlohmann::json &task_context, const std::string &skill_name){
    spdlog::trace("SkillEngine::apply_skill_context");
    spdlog::info("Applying skill context...");
    return m_memory->apply_skill_context(task_context,skill_name);
}

bool SkillEngine::load_skill(std::shared_ptr<Skill> skill){
    spdlog::trace("SkillEngine::load_skill");
    spdlog::info("Loading skill "+skill->get_id()+"...");
    m_active_skill=skill;

    if(m_active_skill->get_valid_control_modes()->find(m_memory->read_parameters()->control.control_mode)==m_active_skill->get_valid_control_modes()->end()){
        spdlog::error("Skill of type " + m_active_skill->get_type() + " is not compatible with the chosen controller pipeline.");
        return false;
    }

    if(!m_active_skill->ground_objects()){
        return false;
    }
    if(!m_active_skill->modify_objects()){
        return false;
    }
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
    spdlog::trace("SkillEngine::blend_skill_stage_1");
    m_active_skill->terminate(*m_core->get_percept());
    m_results.insert(std::pair<std::string,SkillResult>(m_active_skill->get_id(),m_active_skill->get_result()));

    m_active_skill=*m_it_skill_queue;
    ++m_it_skill_queue;
    m_memory->apply_reserved_skill_context(m_active_skill->get_id());
    if(!m_active_skill->ground_objects()){
        return false;
    }
    if(!m_active_skill->modify_objects()){
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
    spdlog::trace("SkillEngine::blend_skill_stage_2");
    spdlog::info("Initializing...");
    if(!m_active_skill->initialize(*m_core->get_percept())){
        return false;
    }
    return true;
}

bool SkillEngine::is_last_skill(){
    spdlog::trace("SkillEngine::is_last_skill");
    return m_it_skill_queue==m_skill_queue.end();
}

bool SkillEngine::add_skill(std::shared_ptr<Skill> skill){
    spdlog::trace("SkillEngine::add_skill");
    m_skill_queue.push_back(skill);
    return true;
}

void SkillEngine::clear_skill_queue(){
    spdlog::trace("SkillEngine::clear_skill_queue");
    m_skill_queue.clear();
}

void SkillEngine::clear_results(){
    spdlog::trace("SkillEngine::clear_results");
    m_results.clear();
}

ControlReturnType SkillEngine::execute_skill_queue(){
    spdlog::trace("SkillEngine::execute_skill_queue");
    m_queue=true;
    m_it_skill_queue=m_skill_queue.begin();
    m_active_skill=*m_it_skill_queue;
    ++m_it_skill_queue;

    ControlReturnType result(false,"None","");
    m_memory->apply_reserved_skill_context(m_active_skill->get_id());
    if(!m_active_skill->ground_objects()){
        return result;
    }
    if(!m_active_skill->modify_objects()){
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
    init_logs();
    try{
        spdlog::info("Executing skill...");
        result = m_core->execute_skill();
        if(!result.exception){
            spdlog::info("Skill ran nominally.");
        }else{
            spdlog::error("An error occured during skill execution: (" + result.error + ", " + result.error_msg + ")");
            m_active_skill->append_error(result.error);
        }
    }catch(const SkillException& e){
        spdlog::debug(e.what());
        result = {true,"SkillException",e.what()};
        spdlog::error("A skill exception occured");
    }
    m_core->post_execution();
    spdlog::info("Unloading skill...");
    m_active_skill->terminate(*m_core->get_percept());
    m_results.insert(std::pair<std::string,SkillResult>(m_active_skill->get_id(),m_active_skill->get_result()));
    unload_skill();
    write_logs();
    if(!m_core->refresh_percept({})){
        clear_skill_queue();
        return {true,"PerceptError","Could not refresh the perception"};
    }
    if(!result.exception){
        spdlog::info("Skill terminated nominally...");
    }else{
        spdlog::warn("Errors occured during skill execution, check above messages for more information.");
    }
    clear_skill_queue();
    return result;
}

bool SkillEngine::is_running_queue(){
    return m_queue;
}

void SkillEngine::unload_skill(){
    spdlog::trace("SkillEngine::unload_skill");
    m_active_skill=std::make_shared<NullSkill>("NullSkill",m_memory,m_core->get_portal());
    m_core->get_portal()->remove_messages();
}

ControlReturnType SkillEngine::execute_skill(std::shared_ptr<Skill> skill){
    spdlog::trace("SkillEngine::execute_skill");
    m_queue=false;
    if(!load_skill( skill)){
        spdlog::error("Skill could not be loaded.");
        return {true,"SkillLoadError","Skill could not be loaded."};
    }
    ControlReturnType result(false,"None","");
    init_logs();
    try{
        spdlog::info("Executing skill...");
        result = m_core->execute_skill();
        if(!result.exception){
            spdlog::info("Skill ran nominally.");
        }else{
            spdlog::error("An error occured during skill execution: (" + result.error + ", " + result.error_msg + ")");
            m_active_skill->append_error(result.error);
        }
    }catch(const SkillException& e){
        spdlog::debug(e.what());
        result = {true,"SkillException",e.what()};
        spdlog::error("A skill exception occured: " + std::string(e.what()));
    }
    m_core->post_execution();
    spdlog::info("Unloading skill...");
    skill->terminate(*m_core->get_percept());
    unload_skill();
    write_logs();
    if(!m_core->refresh_percept({},true)){
        return {true,"PerceptError","Could not refresh the perception"};
    }
    if(!result.exception){
        spdlog::info("Skill terminated nominally...");
    }else{
        spdlog::warn("Errors occured during skill execution, check above messages for more information.");
    }
    return result;
}

void SkillEngine::stop_skill(){
    spdlog::trace("SkillEngine::stop_skill");
    m_active_skill->invoke_failure();
}

Actuator* SkillEngine::get_next_command(const Percept& percept){
    Actuator* cmd = m_active_skill->cycle(percept);
    return cmd;
}

std::unordered_map<std::string,SkillResult> SkillEngine::get_results(){
    spdlog::trace("SkillEngine::get_results");
    return m_results;
}

void SkillEngine::log_data(const Percept &p){
    if(m_log_cnt>=m_data_log.size()){
        return;
    }
    m_data_log[m_log_cnt]["time"]=std::chrono::duration<double>(std::chrono::high_resolution_clock::now().time_since_epoch()).count();
    m_data_log[m_log_cnt]["q"]=msrm_utils::from_eigen<double,7,1>(p.proprioception.q);
    m_data_log[m_log_cnt]["dq"]=msrm_utils::from_eigen<double,7,1>(p.proprioception.dq);
    m_data_log[m_log_cnt]["O_T_EE"]=msrm_utils::from_eigen<double,4,4>(p.proprioception.O_T_EE);
    m_data_log[m_log_cnt]["dX"]=msrm_utils::from_eigen<double,6,1>(p.proprioception.O_dX_EE);
    m_data_log[m_log_cnt]["tau_ext"]=msrm_utils::from_eigen<double,7,1>(p.proprioception.tau_ext);
    m_data_log[m_log_cnt]["F_ext"]=msrm_utils::from_eigen<double,6,1>(p.proprioception.K_F_ext_K);


    m_log_cnt++;
}

void SkillEngine::init_logs(){
    spdlog::trace("SkillEngine::init_logs");
    m_log_cnt=0;
    nlohmann::json data_log;
    m_data_log.resize(m_memory->read_parameters()->skill->data_length);
}

void SkillEngine::write_logs(){
    spdlog::trace("SkillEngine::write_logs");
    if(!m_memory->read_parameters()->skill->log_data || m_data_log.size()==0){
        return;
    }
    spdlog::info("Writing logs into file...");
    std::string log_file = boost::filesystem::path(boost::filesystem::current_path()).string()+"/../logs/logs_"+m_memory->read_parameters()->skill->log_name+".txt";
    boost::filesystem::create_directories(boost::filesystem::path(boost::filesystem::current_path()).string()+"/../logs/");
    std::remove(log_file.c_str());
    try{
        for(const auto& el : m_data_log[0].items()){
            if(m_data_log[0][el.key()].is_array()){
                for(unsigned i=0;i<m_data_log[0][el.key()].size();i++){
                    msrm_utils::write_data_to_file(el.key(),log_file);
                }
            }else{
                msrm_utils::write_data_to_file(el.key(),log_file);
            }
        }
        msrm_utils::write_endl_to_file(log_file);
        if(m_log_cnt>=m_data_log.size()){
            m_log_cnt=m_data_log.size();
        }
        for(unsigned i=0;i<m_log_cnt;i++){
            for(const auto& el : m_data_log[i].items()){
                if(m_data_log[i][el.key()].is_array()){
                    for(unsigned j=0;j<m_data_log[i][el.key()].size();j++){
                        msrm_utils::write_data_to_file(m_data_log[i][el.key()][j],log_file);
                    }
                }else{
                    msrm_utils::write_data_to_file(m_data_log[i][el.key()],log_file);
                }
            }
            msrm_utils::write_endl_to_file(log_file);
        }
    }catch(const nlohmann::json::exception& e){
        spdlog::debug(e.what());
    }
    spdlog::info("Logs have been written to "+log_file+".");
}

}
