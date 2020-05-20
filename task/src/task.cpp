#include "task/task.hpp"

#include "core/core.hpp"
#include "memory/memory.hpp"

#include <random>
#include <sstream>
#include <spdlog/spdlog.h>

namespace mios {

Task::Task(const std::string& id, Core* core,Memory* memory):m_id(id),m_memory(memory),m_uuid(Task::generate_uuid()),m_core(core),m_flag_stop(false),m_flag_in_recovery(false),m_flag_recover(false){

}

Task::~Task(){
    notify_observers();
}

void Task::recover_task(){
    msrm_utils::print_warning("Recovery routine of task "+m_id+" is empty.");
}

void Task::stop_task(bool raise_exception,bool success,bool recover, bool empty_queue, double cost_suc, double cost_err){
    if(m_flag_stop){
        return;
    }
    if(m_flag_in_recovery && !raise_exception){
        spdlog::warn("Can not invoke nominal stop while in recovery mode.");
        return;
    }
    if(raise_exception){
        spdlog::warn("Exception has been raised. I will not attempt to recover task " + m_id + ".");
    }
    m_result.exception=raise_exception;
    m_result.empty_queue=empty_queue;
    m_flag_recover=recover && !raise_exception;
    for(auto& s : m_skills){
        if(success && nominal){
            s.second->invoke_success();
        }else{
            s.second->invoke_failure();
        }
    }
    for(auto& t : m_subtasks){
        t.second->stop_task(nominal,success,recover,empty_queue,cost_suc,cost_err);
    }
    m_flag_stop=true;
}

void Task::abort_task(){
    m_eval_task.nominal_termination=false;
    for(auto& s : m_skills){
        s.second->stop_skill();
    }
    for(auto& t : m_subtasks){
        t.second->abort_task();
    }
    m_flag_stop=true;
}

void Task::execute_desk_timeline(const std::string &id){
    if(m_flag_stop){
        return;
    }
    m_core->start_desk_task(id);
}

void Task::write_result(bool success, double cost_suc, double cost_err, nlohmann::json custom_results){
    m_result.success=success;
    m_result.cost_suc=cost_suc;
    m_result.cost_err=cost_err;
    m_result.custom_results=custom_results;
}

void Task::reset_soft(){
    m_eval_task=EvalTask();
    m_flag_stop=false;
    m_flag_in_recovery=false;
    m_flag_recover=false;
    for(auto& s : m_skills){
        s.second->reset();
    }
    for(auto& t : m_subtasks){
        t.second->reset_soft();
    }
}

bool Task::load_context(const nlohmann::json &user_context, nlohmann::json& active_context){
    try{
        spdlog::info("Loading description for task " + m_id + "...");
        if(!m_memory->load_default_task_context(m_id,m_context)){
            spdlog::error("Could not load a valid task description for "+m_id+".");
            return false;
        }

        // merge default task parameters with user task parameters
        if(m_context.find("parameters")!=m_context.end() && user_context.find("parameters")!=user_context.end()){
            for(const auto& el : user_context["parameters"].items()){
                if((m_context["parameters"].find(el.key())==m_context["parameters"].end())){
                    spdlog::error("Task parameter "+el.key()+" given by user does not exist in task description.");
                    return false;
                }
                msrm_utils::overwrite_valid_json(user_context["parameters"][el.key()],m_context["parameters"][el.key()]);
            }
        }

        if(user_context.find("subtasks")!=user_context.end()){
            m_context["subtasks"]=user_context["subtasks"];
        }

        nlohmann::json default_parameters;
        if(!m_memory->load_default_parameters(default_parameters)){
            return false;
        }
        if(m_context.find("skills")!=m_context.end()){
            for(auto& s : m_context["skills"].items()){
                std::string id_skill=s.key();
                // CHECK: skill has type
                if(m_context["skills"][id_skill].find("type")==m_context.end()){
                    spdlog::error("Skill " + id_skill + " in task " + m_id + " has no type.");
                    return false;
                }
                std::string skill_type=m_context["skills"][id_skill]["type"];
                // CHECK: skill has valid context
                default_parameters["skill"]=nlohmann::json();
                if(!m_memory->load_default_skill_context(skill_type,default_parameters["skill"])){
                    spdlog::error("Could not load a valid skill context for "+id_skill+".");
                    return false;
                }
                nlohmann::json tmp_params;
                for(auto& cat : default_parameters.items()){
                    if(m_context["skills"][id_skill].find(cat.key())!=m_context["skills"][id_skill].end()){
                        tmp_params = m_context["skills"][id_skill][cat.key()];
                    }
                    m_context["skills"][id_skill][cat.key]=cat.value();
                    for(auto& p : tmp_params.items()){
                        m_context["skills"][id_skill][cat.key()][p.first]=p.second;
                    }
                }

            }
        }

        if(user_context.find("skills")!=user_context.end()){
            for(auto& s : user_context["skills"].items()){
                std::string id_skill=s.first;
                for(auto& cat : user_context["skills"][id_skill].items()){
                    for(auto& p: user_context["skills"][id_skill][cat.first].items()){
                        m_context["skills"][id_skill][cat.first][p.first]=p.second;
                    }
                }

            }
        }

        spdlog::info("Checking task context for consistency...");
        if(!check_context(m_context,user_context)){
            spdlog::error("Detected errors in task context, aborting execution of task "+ m_id +" with uuid " + m_uuid);
            return false;
        }
    }catch(const nlohmann::detail::type_error& e){
        spdlog::debug(e.what());
        spdlog::critical("An exception occured in Task::load_context");
        return false;
    }
    spdlog::info("Task context has been loaded");
    return true;
}

bool Task::grasp_object(const std::string &o, double width, double speed, double force, bool check_width){
    if(!m_flag_stop){
        return m_core->grasp_object(o,width,speed,force,check_width);
    }else{
        return true;
    }
}

bool Task::release_object(double width, double speed){
    if(!m_flag_stop){
        return m_core->release_object(width,speed);
    }else{
        return true;
    }
}

bool Task::move_gripper(double width, double speed){
    if(!m_flag_stop){
        return m_core->move_gripper(width,speed);
    }else{
        return true;
    }
}

const Percept& Task::request_percept(Eigen::Matrix<double, 3, 3> O_R_TF){
    return m_core->request_percept(O_R_TF);
}

void Task::set_state(const std::string& state){
    if(!m_flag_stop){
        m_state=state;
    }
}

std::string Task::get_state() const{
    return m_state;
}

bool Task::reserve_skill(const std::string &name){
    if(m_reserved_skills.find(name)==m_reserved_skills.end()){
        m_reserved_skills.insert(name);
        return true;
    }else{
        spdlog::error("A skill with name " + name + " has already been reserved");
        return false;
    }
}

bool Task::reserve_subtask(const std::string &name){
    if(m_reserved_subtasks.find(name)==m_reserved_subtasks.end()){
        m_reserved_subtasks.insert(name);
        return true;
    }else{
        spdlog::error("A skill with name " + name + " has already been reserved");
        return false;
    }
}

void Task::execute_subtask(const std::string& task_id,const std::string task_name){
    if(m_reserved_subtasks.find(task_name)==m_reserved_subtasks.end()){
        this->abort_task();
        throw TaskException("Subtask with id "+t+" not in task "+ m_id +". Stopping task.");
    }
    if(m_flag_stop){
        return;
    }
    spdlog::info("Executing subtask "+task_name+"...");
    std::shared_ptr<Task> subtask = m_memory->load_subtask(task_id,m_context["subtasks"][t],m_core);
    if(subtask->get_id()=="IdleTask"){
        throw TaskException("Error when loading subtask with name " + task_name);
    }
    spdlog::info("Executing subtask "+task_name+"...");
    subtask->execute_task();
    spdlog::info("Subtask "+t+" has terminated.");
    subtask->evaluate_task();
    if(subtask->do_recovery()){
        subtask->start_recovery();
        spdlog::info("Subtask "+task_name+" is attempting recovery.");
        subtask->recover_task();
    }
    m_result.m_subtask_results.insert(std::make_pair(task_name,subtask->get_result()));
    spdlog::info("End of lifecycle of subtask "+task_name+".");
}

bool Task::read_parameters(const nlohmann::json &params){
    if(params.is_null()){
        return true;
    }
    spdlog::error("This task has not overwritten the read_parameters method, yet the task description contains user-defined parameters. Undefined behavior is possible, aborting...");
    return false;
}

void Task::start_recovery(){
    m_flag_in_recovery=true;
    m_flag_stop=false;
}

void Task::complete_recovery(){
    m_flag_in_recovery=false;
}

std::shared_ptr<Skill> Task::get_skill(const std::string& id) const{
    if(m_skills.find(id)==m_skills.end()){
        throw TaskException("Skill with id "+id+" not in task "+ get_id() +". Check your task configuration file and cpp-file for consistency.");
    }else{
        return m_skills.at(id);
    }
}

bool Task::do_recovery() const{
    return m_flag_recover;
}

std::shared_ptr<Task> Task::get_subtask(const std::string& id) const{
    if(m_subtasks.find(id)==m_subtasks.end()){
        throw TaskException("Subtask with id "+id+" not in task "+ get_id() +". Check your cpp-file for consistency.");
    }else{
        return m_subtasks.at(id);
    }
}

EvalTask Task::get_eval() const{
    return m_eval_task;
}

void Task::sleep_1ms() const{
    while(!m_flag_stop){
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    }
}

bool Task::is_grasping() const{
    return m_core->is_grasping();
}

std::string Task::get_id() const{
    return m_id;
}

bool Task::get_stop_flag() const{
    return m_flag_stop || m_core->has_terminated();
}

bool Task::get_recovery_flag() const{
    return m_flag_in_recovery;
}

std::string Task::get_uuid() const{
    return m_uuid;
}

TaskResult Task::get_result() const{
    return m_result;
}

bool Task::check_context(const nlohmann::json &default_context, const nlohmann::json &user_context) const{

    std::unordered_set<std::string> top_level={"name","parameters","skills","_id","subtasks"};
    std::unordered_set<std::string> skill_level={"skill","control","general","frames","user","objects","type"};
    std::unordered_set<std::string> common_skill_parameters={"time_max","parallels_frequency"};

    try{
        for(const auto& el : default_context.items()){
            if(top_level.find(itr.key())==top_level.end()){
                spdlog::error("Syntax error in default task context. Symbol with value "+el.key()+" is not valid on top level.");
                return false;
            }
        }
        for(const auto& el : user_context.items()){
            if(top_level.find(itr.key())==top_level.end()){
                spdlog::error("Syntax error in user task context. Symbol with value "+el.key()+" is not valid on top level.");
                return false;
            }
        }
        if(user_context.find("parameters")!=user_context.end()){
            if(default_context.find("parameters")==default_context.end()){
                spdlog::error("Task " + m_id + " has no parameters but some where given by user input.");
                return false;
            }else{
                for(const auto& el : user_context["parameters"].items()){
                    if(default_context["parameters"].find(el.key())==default_context["parameters"].end()){
                        spdlog::error("Task " + m_id + " does not have a parameter " + el.key() + " as provided by user input.");
                        return false;
                    }
                }
            }
        }
        if(default_context.find("skills")!=default_context.end()){
            std::string skill=el_skill.key();
            for(const auto& el_skill : default_context["skills"].items()){
                if(default_context["skills"][skill].find("type")==default_context["skills"][skill].end()){
                    spdlog::error("Syntax error in task context for task "+m_id+". Skill " + skill + " is missing a type definition.");
                    return false;
                }
                std::string skill_type=default_context["skills"][skill]["type"];
                nlohmann::json skill_context;
                if(!m_memory->load_default_skill_context(skill_type,skill_context)){
                    spdlog::error("Could not load a valid skill context for "+skill+" of type " + skill_type +".");
                    return false;
                }
                if(user_context["skills"].find(skill)==user_context["skills"].end()){
                    for(const auto& el_cat : user_context["skills"][skill].items()){
                        if(skill_level.find(el_cat.key())==skill_level.end()){
                            spdlog::error("Syntax error in user input for task "+m_id+". Symbol with value "+el_cat.key()+" is not valid on skill level for skill " +skill+" of type "+skill_type +".");
                            return false;
                        }
                    }
                    if(user_context["skills"][skill].find("skill")==user_context["skills"][skill].end()){
                        for(const auto& el_p : user_context["skills"][skill]["skill"].items()){
                            if(skill_context.find(el_p.key())==skill_context.end() && common_skill_parameters.find(el_p.key())==common_skill_parameters.end()){
                                spdlog::error("Syntax error in user task context for task "+m_id+". Symbol with value "+el_p.key()+" is not valid in skill context for skill "+skill+" of type "+skill_type+".");
                                return false;
                            }
                        }
                    }
                }
                for(const auto& el_cat : default_context["skills"][skill].items()){
                    if(skill_level.find(el_cat.key())==skill_level.end()){
                        spdlog::error("Syntax error in task context for task "+m_id+". Symbol with value "+el_cat.key()+" is not valid on skill level for skill " +skill+" of type "+default_context["skills"][skill]["type"] +".");
                        return false;
                    }
                }
                if(default_context["skills"][skill].find("skill")==default_context["skills"][skill].end()){
                    for(const auto& el_p : default_context["skills"][skill]["skill"].items()){
                        if(skill_context.find(el_p.key())==skill_context.end() && common_skill_parameters.find(el_p.key())==common_skill_parameters.end()){
                            spdlog::error("Syntax error in task context for task "+m_id+". Symbol with value "+el_p.key()+" is not valid in skill context for skill "+skill+" of type "+skill_type+".");
                            return false;
                        }
                    }
                }

            }
            for(const auto& el_skill : user_context["skills"].items()){
                std::string skill=el_skill.key();
                if(default_context["skills"].find(skill)==default_context["skills"].end()){
                    spdlog::error("Syntax error in user input for task "+m_id+". Skill " + skill + " does not exist in default task context.");
                    return false;
                }
            }
        }
    }catch(const nlohmann::detail::type_error& e){
        spdlog::debug(e.what());
        return false;
    }
    return true;
}

void Task::notify_observers(){
    for(auto& o : m_observers){
        o->finish();
    }
}

void Task::subscribe(std::shared_ptr<TaskObserver> observer){
    m_observers.insert(observer);
}

std::string Task::generate_uuid() const{
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<> dis(0, 15);
    std::uniform_int_distribution<> dis2(8, 11);
    std::stringstream ss;
    int i;
    ss << std::hex;
    for (i = 0; i < 8; i++) {
        ss << dis(gen);
    }
    ss << "-";
    for (i = 0; i < 4; i++) {
        ss << dis(gen);
    }
    ss << "-4";
    for (i = 0; i < 3; i++) {
        ss << dis(gen);
    }
    ss << "-";
    ss << dis2(gen);
    for (i = 0; i < 3; i++) {
        ss << dis(gen);
    }
    ss << "-";
    for (i = 0; i < 12; i++) {
        ss << dis(gen);
    };
    return ss.str();
}

}
