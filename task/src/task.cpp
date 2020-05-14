#include "task/task.hpp"

#include "core/core.hpp"

#include <random>
#include <sstream>
#include <spdlog/spdlog.h>

namespace mios {

Task::Task(const std::string& id, Core* core):m_id(id),m_uuid(Task::generate_uuid()),m_core(core),m_kb(core->get_kb()),m_flag_stop(false),m_flag_in_recovery(false),m_flag_recover(false){
    m_skills.clear();
    m_subtasks.clear();
}

Task::~Task(){
    notify_observers();
}

void Task::recover_task(){
    msrm_utils::print_warning("Recovery routine of task "+m_id+" is empty.");
}

void Task::stop_task(bool nominal,bool success,bool recover, bool empty_queue, double cost_suc, double cost_err){
    if(m_flag_stop){
        return;
    }
    if(m_flag_in_recovery && nominal){
        spdlog::warn("Can not invoke nominal stop while in recovery mode.");
        return;
    }
    if(!nominal){
        spdlog::warn("Non-nominal stop invoked. I will not attempt to recover task " + m_id + ".");
    }
    m_eval_task.nominal_termination=nominal;
    m_eval_task.empty_queue=empty_queue;
    m_flag_recover=recover && nominal;
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

bool Task::load(const nlohmann::json &parameters){
    try{
        nlohmann::json task_descr;
        spdlog::info("Loading description for task " + m_id + "...");
        if(!m_core->get_kb()->load_task(m_id,task_descr)){
            spdlog::error("Could not load a valid task description for "+m_id+".");
            return false;
        }

        // merge default task parameters with instance task parameters
        if(task_descr.find("parameters")!=task_descr.end() && parameters.find("parameters")!=parameters.end()){
            for(const auto& el : parameters["parameters"].items()){
                if((task_descr["parameters"].find(el.key())==task_descr["parameters"].end())){
                    spdlog::error("Task parameter "+el.key()+" given by user does not exist in task description.");
                    return false;
                }
                msrm_utils::overwrite_valid_json(parameters["parameters"][el.key()],task_descr["parameters"][el.key()]);
            }
        }
        // read task parameters from description
        if(task_descr.find("parameters")!=task_descr.end()){
            if(!this->read_parameters(task_descr["parameters"])){
                spdlog::error("Could not load task parameters for task "+m_id+".");
                return false;
            }
        }
        if(!msrm_utils::read_json_param<double>(parameters,"w_cost_function",m_w_cost_function)){
            m_w_cost_function.resize(10);
            m_w_cost_function[0]=1;
        }
        this->initialize_task();
        spdlog::info("Checking user input for task " + m_id + "...");
        if(!this->check_user_input(parameters, task_descr)){
            spdlog::error("User input contains errors for task " + m_id + ".");
            return false;
        }

        for(auto& t : m_subtasks){
            nlohmann::json parameters_sub=nlohmann::json();
            if(parameters.find("subtasks")!=parameters.end()){
                if(parameters["subtasks"].find(t.first)!=parameters["subtasks"].end()){
                    parameters_sub=parameters["subtasks"][t.first];
                }
            }
            if(!t.second->load(parameters_sub)){
                spdlog::error("Loading of subtask "+t.first+" has failed.");
                return false;
            }
        }
        for(auto& s : m_context){
            if(!m_core->get_kb()->load_parameters()){
                spdlog::error("Could not load parameters from knowledge base");
                return false;
            }
            std::string id_skill=s.first;
            std::string skill_type=task_descr["skills"][id_skill]["type"];
            s.second->controller=m_core->get_kb()->get_local_memory()->access_config_cntr();
            s.second->->frames=m_core->get_kb()->get_local_memory()->access_config_frames();
            s.second->general=m_core->get_kb()->get_local_memory()->access_config_general();
            s.second->limits=m_core->get_kb()->get_local_memory()->access_config_limits();
            s.second->system=m_core->get_kb()->get_local_memory()->access_config_system();
            s.second->user=m_core->get_kb()->get_local_memory()->access_config_user();

            nlohmann::json skill_descr;
            if(!m_core->get_kb()->load_skill(skill_type,skill_descr)){
                spdlog::error("Could not load a valid skill description for "+id_skill+".");
                return false;
            }

            // overwrite task description with user specified parameters
            load_description_category(parameters,"skill",id_skill,task_descr);
            load_description_category(parameters,"control",id_skill,task_descr);
            load_description_category(parameters,"frames",id_skill,task_descr);
            load_description_category(parameters,"general",id_skill,task_descr);
            load_description_category(parameters,"user",id_skill,task_descr);
            load_description_category(parameters,"system",id_skill,task_descr);
            if(parameters.find("skills")!=parameters.end() && task_descr.find("skills")!=task_descr.end()){
                if((parameters["skills"].find(id_skill)!=parameters["skills"].end()) && task_descr["skills"].find(id_skill)!=task_descr["skills"].end()){
                    // Read objects
                    if(parameters["skills"][id_skill].find("objects")!=parameters["skills"][id_skill].end() && task_descr["skills"][id_skill].find("objects")!=task_descr["skills"][id_skill].end()){
                        if(parameters["skills"][id_skill]["objects"].size()!=task_descr["skills"][id_skill]["objects"].size()){
                            spdlog::error("Number of given objects for skill "+id_skill+" and number of objects defined by the task description are different.");
                            return false;
                        }
                        for(unsigned i=0;i<parameters["skills"][id_skill]["objects"].size();i++){
                            msrm_utils::overwrite_valid_json(parameters["skills"][id_skill]["objects"][i],task_descr["skills"][id_skill]["objects"][i]);
                        }
                    }else if(parameters["skills"][id_skill].find("objects")!=parameters["skills"][id_skill].end()){
                        task_descr["skills"][id_skill]["objects"]=parameters["skills"][id_skill]["objects"];
                    }
                }else if(parameters["skills"].find(id_skill)!=parameters["skills"].end()){
                    task_descr["skills"][id_skill]=parameters["skills"][id_skill];
                }
            }

            if(task_descr.find("skills")!=task_descr.end()){
                if(task_descr["skills"].find(id_skill)!=task_descr["skills"].end()){
                    if(task_descr["skills"][id_skill].find("control")!=task_descr["skills"][id_skill].end()){
                        s.second->controller.read_parameters(task_descr["skills"][id_skill]["control"]);
                    }
                    if(task_descr["skills"][id_skill].find("frames")!=task_descr["skills"][id_skill].end()){
                        s.second->frames.read_parameters(task_descr["skills"][id_skill]["frames"]);
                    }
                    if(task_descr["skills"][id_skill].find("genral")!=task_descr["skills"][id_skill].end()){
                        s.second->general.read_parameters(task_descr["skills"][id_skill]["general"]);
                    }
                    if(task_descr["skills"][id_skill].find("user")!=task_descr["skills"][id_skill].end()){
                        s.second->user.read_parameters(task_descr["skills"][id_skill]["user"]);
                    }
                }
            }

            // Read skill parameters
            if(task_descr.find("skills")==task_descr.end()){
                task_descr["skills"]=nlohmann::json();
            }
            if(task_descr["skills"].find(id_skill)==task_descr["skills"].end()){
                task_descr["skills"][id_skill]=nlohmann::json();
            }
            nlohmann::json skill_params_tmp;
            if(task_descr["skills"][id_skill].find("skill")!=task_descr["skills"][id_skill].end()){
                skill_params_tmp=task_descr["skills"][id_skill]["skill"];
            }
            task_descr["skills"][id_skill]["skill"]=skill_descr;
            std::set<std::string> global_skill={"time_max","w_cost_function","parallels_frequency"};
            for(const auto& el : skill_params_tmp.items()){
                if(task_descr["skills"][id_skill]["skill"].find(el.key())!=task_descr["skills"][id_skill]["skill"].end() || global_skill.find(el.key())!=global_skill.end()){
                    task_descr["skills"][id_skill]["skill"][el.key()]=skill_params_tmp[el.key()];
                }else{
                    spdlog::error("Skill "+id_skill+" does not have parameter "+el.key());
                    return false;
                }
            }

            if(!s.second->read_parameters(task_descr["skills"][id_skill]["skill"])){
                spdlog::error("Could not load skill parameters from task description for skill "+id_skill+".");
                return false;
            }
            s.second->read_global_skill_parameters(task_descr["skills"][id_skill]["skill"]);
            s.second->read_configuration(task_descr["skills"][id_skill]);
            if(skill_descr.find("objects")!=skill_descr.end()){
                if(task_descr["skills"][id_skill].find("objects")!=task_descr["skills"][id_skill].end() || skill_descr["objects"].size()>0){
                    if(skill_descr["objects"].size()!=task_descr["skills"][id_skill]["objects"].size()){
                        msrm_utils::print_error(std::to_string(task_descr["skills"][id_skill]["objects"].size())+" objects have been specified for skill "+ id_skill +" although "+ std::to_string(skill_descr["objects"].size()) +" are expected.");
                        return false;
                    }
                    std::map<std::string,std::string> objects;
                    for(unsigned i=0;i<skill_descr["objects"].size();i++){
                        objects.insert(std::pair<std::string,std::string>(skill_descr["objects"][i],task_descr["skills"][id_skill]["objects"][i]));
                    }
                    if(!s.second->objects=objects){
                        spdlog::error("Could not load objects for skill "+id_skill);
                        return false;
                    }
                }
            }
        }
        spdlog::info("Checking task description for consistency...",false);
        if(!this->check_task_description(task_descr)){
            spdlog::error("Detected errors in task description, aborting execution of task "+get_id()+" with uuid " +get_uuid());
            return false;
        }
    }catch(const nlohmann::detail::type_error& e){
        std::cout<<e.what()<<std::endl;
        return false;
    }
    spdlog::info("Task configuration loaded.");
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

void Task::execute_skill(const std::string& s,bool log){
    if(m_skills.find(s)==m_skills.end()){
        spdlog::error("Skill with id "+s+" not in this task. Check your task description for consistency. Stopping task.");
        this->abort_task();
        throw TaskException("Skill with id "+s+" not in this task. Check your task description for consistency. Stopping task.");
    }
    if(m_flag_stop){
        //        msrm_utils::print_info("Task has been stopped recently, aborting skill execution.");
        return;
    }
    if(!m_core->load_skill(m_skills[s],log)){
        throw TaskException("Skill could not be loaded into core.");
    }
    if(!m_core->wait_for_idle_state(2)){
        throw TaskException("Robot did not reach idle state in time.");
    }
    spdlog::info("Executing skill "+s+".");
    bool valid=m_core->start_control_cycle();
    m_skills[s]->terminate();
    m_core->unload_skill();
    if(!valid){
        throw TaskException("Skill execution was not nominal.");
    }
}

void Task::execute_subtask(const std::string& t){
    if(m_subtasks.find(t)==m_subtasks.end()){
        this->abort_task();
        throw TaskException("Subtask with id "+t+" not in task "+ m_id +". Stopping task.");
    }
    if(m_flag_stop){
        //        if(this->_kb->get_local_memory()->access_config_global()->verbosity>1){
        //            msrm_utils::print_info("Task has been stopped recently, aborting subtask execution.");
        //        }
        return;
    }
    spdlog::info("Executing subtask "+t+".");
    this->get_subtask(t)->reset_soft();
    this->get_subtask(t)->execute_task();
    spdlog::info("Subtask "+t+" has terminated.");
    this->get_subtask(t)->evaluate_task();
    if(this->get_subtask(t)->do_recovery()){
        this->get_subtask(t)->start_recovery();
        spdlog::info("Subtask "+t+" is attempting recovery.");
        this->get_subtask(t)->recover_task();
    }
    spdlog::info("End of lifecycle of subtask "+t+".");
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

void Task::load_led_pattern(std::shared_ptr<LEDPattern> pattern){
    m_core->load_led_pattern(pattern);
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

bool Task::check_task_description(const nlohmann::json &description) const{

    std::set<std::string> valid_syntax_top={"name","parameters","skills","mapping","_id","id_parameters","subtasks"};
    std::set<std::string> valid_syntax_skill={"skill","control","general","frames","user","objects","type"};
    std::set<std::string> valid_syntax_skill_parameters={"time_max","k_h_p","k_h_d","w_cost_function","parallels_frequency"};

    try{
        for(nlohmann::json::const_iterator itr=description.begin();itr!=description.end();++itr){
            if(valid_syntax_top.find(itr.key())==valid_syntax_top.end()){
                spdlog::error("Syntax error in task description. Symbol with value "+itr.key()+" is not valid on top level.");
                return false;
            }
        }
        if(description.find("skills")!=description.end()){
            for(const auto& el_skill : description["skills"].items()){
                std::string skill=el_skill.key();
                if(description["skills"][skill].find("type")==description["skills"][skill].end()){
                    spdlog::error("Syntax error in task description for task "+get_id()+". Skill " + skill + " is missing a type definition.");
                    return false;
                }else{
                    std::string type;
                    msrm_utils::read_json_param(description["skills"][skill],"type",type);
                    if(type!=this->get_skill(skill)->get_type()){
                        spdlog::error("Syntax error in task description for task "+get_id()+". Type of skill " + skill + " ("+get_skill(skill)->get_type()+") is different from type definition in skill description ("+type+").");
                        return false;
                    }
                }
                for(nlohmann::json::const_iterator itr=description["skills"][skill].begin();itr!=description["skills"][skill].end();++itr){
                    if(valid_syntax_skill.find(itr.key())==valid_syntax_skill.end()){
                        spdlog::error("Syntax error in task description for task "+get_id()+". Symbol with value "+itr.key()+" is not valid on skill level for skill " +skill+" of type "+get_skill(skill)->get_type() +".");
                        return false;
                    }
                }
                if(m_skills.find(skill)==m_skills.end()){
                    spdlog::error("Task description for task "+ get_id() +" contains skill "+skill+" of type "+get_skill(skill)->get_id()+" which is not contained in the task implementation.");
                    return false;
                }
                nlohmann::json skill_descr;
                if(!m_core->get_kb()->load_skill(get_skill(skill)->get_type(),skill_descr)){
                    spdlog::error("Could not load a valid skill description for "+get_skill(skill)->get_id()+".");
                    return false;
                }
                if(description["skills"][skill].find("skill")==description["skills"][skill].end()){
                    for(const auto& el_p : description["skills"][skill]["skill"].items()){
                        if(skill_descr.find(el_p.key())==skill_descr.end() && valid_syntax_skill_parameters.find(el_p.key())==valid_syntax_skill_parameters.end()){
                            spdlog::error("Syntax error in task description for task "+get_id()+". Symbol with value "+el_p.key()+" is not valid in skill description for skill "+get_skill(skill)->get_id()+" of type "+this->get_skill(skill)->get_type()+".");
                            return false;
                        }
                    }
                }
            }
        }
    }catch(const nlohmann::detail::type_error& e){
        spdlog::debug(e.what());
        return false;
    }
    return true;
}

bool Task::check_user_input(const nlohmann::json &parameters, const nlohmann::json& description) const{
    std::set<std::string> valid_syntax_top={"parameters","skills","subtasks","domain","identity","mapping","id_parameters","name","_id","queue_task","task","w_cost_function","type"};
    std::set<std::string> valid_syntax_skill={"skill","control","general","frames","user","objects","type"};
    std::set<std::string> valid_syntax_skill_parameters={"time_max","k_h_p","k_h_d","w_cost_function","parallels_frequency"};

    try{
        if(parameters.is_null()){
            return true;
        }
        for(nlohmann::json::const_iterator itr=parameters.begin();itr!=parameters.end();++itr){
            if(valid_syntax_top.find(itr.key())==valid_syntax_top.end()){
                spdlog::error("Syntax error in user input. Symbol with value "+itr.key()+" is not valid on top level.");
                return false;
            }
        }
        if(parameters.find("parameters")!=parameters.end()){
            if(description.find("parameters")==description.end()){
                spdlog::error("Task " + m_id + " has no parameters but some where given by user input.");
                return false;
            }else{
                for(const auto& el : parameters["parameters"].items()){
                    if(description["parameters"].find(el.key())==description["parameters"].end()){
                        spdlog::error("Task " + m_id + " does not have a parameter " + el.key() + " as provided by user input.");
                        return false;
                    }
                }
            }
        }
        if(parameters.find("skills")!=parameters.end()){
            for(const auto& el_skill : parameters["skills"].items()){
                std::string skill=el_skill.key();
                if(description["skills"].find(skill)==description["skills"].end()){
                    spdlog::error("Syntax error in user input for task "+get_id()+". Skill " + skill + " does not exist in task description.");
                    return false;
                }
                for(const auto& el : parameters["skills"][skill].items()){
                    if(valid_syntax_skill.find(el.key())==valid_syntax_skill.end()){
                        spdlog::error("Syntax error in user input for task "+get_id()+". Symbol with value "+el.key()+" is not valid on skill level for skill " +skill+" of type "+get_skill(skill)->get_type() +".");
                        return false;
                    }
                }
                if(m_skills.find(skill)==m_skills.end()){
                    spdlog::error("User input for task "+ get_id() +" contains skill "+skill+" of type "+get_skill(skill)->get_id()+" which is not contained in the task implementation.");
                    return false;
                }
                nlohmann::json skill_descr;
                if(!m_core->get_kb()->load_skill(get_skill(skill)->get_type(),skill_descr)){
                    spdlog::error("Could not load a valid skill description for "+get_skill(skill)->get_id()+".");
                    return false;
                }
                if(description["skills"][skill].find("skill")!=description["skills"][skill].end()){
                    for(const auto& el_p : description["skills"][skill]["skill"].items()){
                        if(skill_descr.find(el_p.key())==skill_descr.end() && valid_syntax_skill_parameters.find(el_p.key())==valid_syntax_skill_parameters.end()){
                            spdlog::error("Syntax error in user input for task "+get_id()+". Symbol with value "+el_p.key()+" is not valid in skill description for skill "+get_skill(skill)->get_id()+" of type "+this->get_skill(skill)->get_type()+".");
                            return false;
                        }
                    }
                }
            }
        }
    }catch(const nlohmann::detail::type_error& e){
        spdlog::debug(e.what());
        return false;
    }
    return true;
}

void Task::load_description_category(const nlohmann::json &parameters, const std::string &category, const std::string &id_skill, nlohmann::json &task_descr) const{
    if(parameters.find("skills")==parameters.end()){
        return;
    }
    if(task_descr.find("skills")==task_descr.end()){
        task_descr["skills"]=parameters["skills"];
        return;
    }
    if(parameters["skills"].find(id_skill)==parameters["skills"].end()){
        return;
    }
    if(task_descr["skills"].find(id_skill)==task_descr["skills"].end()){
        task_descr["skills"][id_skill]=parameters["skills"][id_skill];
        return;
    }
    if(parameters["skills"][id_skill].find(category)!=parameters["skills"][id_skill].end() && task_descr["skills"][id_skill].find(category)!=task_descr["skills"][id_skill].end()){

        for(nlohmann::json::const_iterator itr = parameters["skills"][id_skill][category].begin();itr != parameters["skills"][id_skill][category].end();itr++){
            msrm_utils::overwrite_valid_json(parameters["skills"][id_skill][category][itr.key()],task_descr["skills"][id_skill][category][itr.key()]);
        }
    }else if(parameters["skills"][id_skill].find(category)!=parameters["skills"][id_skill].end()){
        task_descr["skills"][id_skill][category]=parameters["skills"][id_skill][category];
    }
}

void Task::notify_observers(){
    for(auto& o : m_observers){
        o->finish();
    }
}

void Task::subscribe(std::shared_ptr<TaskObserver> observer){
    m_observers.insert(observer);
}

std::string Task::generate_uuid(){
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
