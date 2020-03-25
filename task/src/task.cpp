#include "task/task.hpp"

#include "core/core.hpp"

namespace mios {

Task::Task(const std::string& id):_id(id){
    this->_core=nullptr;
    this->_kb=nullptr;
    this->reset();
}

Task::~Task(){
    //    for(std::pair<std::string,Skill*> s : this->_skill){
    //        delete s.second;
    //    }
    //    for(std::pair<std::string,EvalSkill*> e : this->_eval){
    //        delete e.second;
    //    }
}

void Task::recover_task(){
    cpp_utils::print_warning("Recovery routine of task "+this->_id+" is empty.");
}

void Task::stop_task(bool nominal,bool success,bool recover, bool empty_queue, double cost_suc, double cost_err){
    if(this->_flag_stop){
        cpp_utils::print_warning("Task "+this->_id+ " has already been stopped.");
        return;
    }
    if(this->_flag_in_recovery && nominal){
        cpp_utils::print_warning("Can not invoke nominal stop while in recovery mode.");
        return;
    }
    if(!nominal){
        cpp_utils::print_warning("Non-nominal stop invoked. I will not attempt to recover task " + this->_id + ".");
    }
    this->_eval_task.nominal_termination=nominal;
    this->_eval_task.empty_queue=empty_queue;
    this->_flag_recover=recover && nominal;
    for(std::pair<std::string,std::shared_ptr<Skill> > s : this->_skill){
        if(success && nominal){
            s.second->invoke_success();
        }else{
            s.second->invoke_failure();
        }
    }
    for(std::pair<std::string,std::shared_ptr<Task> > t : this->_subtask){
        t.second->stop_task(nominal,success,recover,empty_queue,cost_suc,cost_err);
    }
    this->_flag_stop=true;
}

void Task::abort_task(){
    this->_eval_task.nominal_termination=false;
    for(std::pair<std::string,std::shared_ptr<Skill> > s : this->_skill){
        s.second->stop_skill();
    }
    for(std::pair<std::string,std::shared_ptr<Task> > t : this->_subtask){
        t.second->abort_task();
    }
    this->_flag_stop=true;
}

void Task::execute_desk_timeline(const std::string &id){
    if(this->_flag_stop){
        return;
    }
    this->_core->start_desk_task(id);
}

void Task::reset(){
    this->_core=nullptr;
    this->_kb=nullptr;
    this->_skill.clear();
    this->_subtask.clear();
    this->_eval_task=EvalTask();
    this->_flag_stop=false;
    this->_flag_in_recovery=false;
    this->_flag_recover=false;
}

void Task::reset_soft(){
    this->_eval_task=EvalTask();
    this->_flag_stop=false;
    this->_flag_in_recovery=false;
    this->_flag_recover=false;
    for(std::pair<std::string, std::shared_ptr<Skill> > s : this->_skill){
        s.second->reset();
    }
    for(std::pair<std::string, std::shared_ptr<Task> > t : this->_subtask){
        t.second->reset_soft();
    }
}

bool Task::load(const nlohmann::json &parameters, std::shared_ptr<Core> core){
    try{
        nlohmann::json task_descr;
        cpp_utils::print_info("Loading description for task " + this->_id + "...",false);
        if(!core->get_kb()->load_task(this->_id,task_descr)){
            cpp_utils::print_info("failed.");
            cpp_utils::print_error("Could not load a valid task description for "+this->_id+".");
            return false;
        }
        cpp_utils::print_info("done.");
        this->reset();
        this->_core=core;
        this->_kb=this->_core->get_kb();

        // merge default task parameters with instance task parameters
        if(cpp_utils::find_json_value(task_descr,"parameters") && cpp_utils::find_json_value(parameters,"parameters")){
            for(nlohmann::json::const_iterator itr = parameters["parameters"].begin();itr != parameters["parameters"].end();itr++){
                if(!cpp_utils::find_json_value(task_descr["parameters"],itr.key())){
                    cpp_utils::print_error("Task parameter "+itr.key()+" given by user does not exist in task description.");
                    return false;
                }
                cpp_utils::overwrite_valid_json(parameters["parameters"][itr.key()],task_descr["parameters"][itr.key()]);
            }
        }
        // read task parameters from description
        if(cpp_utils::find_json_value(task_descr,"parameters")){
            if(!this->read_parameters(task_descr["parameters"])){
                cpp_utils::print_error("Could not load task parameters for task "+this->_id+".");
                return false;
            }
        }
        if(!cpp_utils::read_json_param<double>(parameters,"w_cost_function",this->_w_cost_function)){
            this->_w_cost_function.resize(10);
            this->_w_cost_function[0]=1;
        }
        this->initialize_task();
        cpp_utils::print_info("Checking user input for task " + this->_id + "...",false);
        if(!this->check_user_input(parameters, task_descr)){
            cpp_utils::print_info("failed.");
            cpp_utils::print_error("User input contains errors for task " + this->_id + ".");
            return false;
        }
        cpp_utils::print_info("done.");

        for(std::pair<std::string,std::shared_ptr<Skill> > s : this->_skill){
            s.second->create_config();
            s.second->set_kb(this->_kb);
            s.second->get_config()->w_cost_function=this->_w_cost_function;
        }

        for(std::pair<std::string, std::shared_ptr<Task> > t : this->_subtask){
            nlohmann::json parameters_sub=nlohmann::json();
            if(cpp_utils::find_json_value(parameters,"subtasks")){
                if(cpp_utils::find_json_value(parameters["subtasks"],t.first)){
                    parameters_sub=parameters["subtasks"][t.first];
                }
            }
            if(!t.second->load(parameters_sub,this->_core)){
                cpp_utils::print_error("Loading of subtask "+t.first+" has failed.");
                return false;
            }
        }
        for(std::pair<std::string,std::shared_ptr<Skill> > s : this->_skill){
            if(!this->_core->get_kb()->load_parameters()){
                cpp_utils::print_error("Could not load parameters from knowledge base");
                return false;
            }
            if(s.second->get_config()==nullptr){
                cpp_utils::print_error("Skill of type "+s.second->get_type()+" has invalid config object. Please implement the function 'get_config' properly.");
                return false;
            }
            std::string id_skill=s.second->get_id();
            s.second->get_config()->controller=this->_core->get_kb()->get_local_memory()->access_config_cntr();
            s.second->get_config()->frames=this->_core->get_kb()->get_local_memory()->access_config_frames();
            s.second->get_config()->general=this->_core->get_kb()->get_local_memory()->access_config_general();
            s.second->get_config()->limits=this->_core->get_kb()->get_local_memory()->access_config_limits();
            s.second->get_config()->system=this->_core->get_kb()->get_local_memory()->access_config_system();
            s.second->get_config()->user=this->_core->get_kb()->get_local_memory()->access_config_user();

            nlohmann::json skill_descr;
            if(!this->_core->get_kb()->load_skill(s.second->get_type(),skill_descr)){
                cpp_utils::print_error("Could not load a valid skill description for "+id_skill+".");
                return false;
            }

            // overwrite task description with user specified parameters
            this->load_description_category(parameters,"skill",id_skill,task_descr);
            this->load_description_category(parameters,"control",id_skill,task_descr);
            this->load_description_category(parameters,"frames",id_skill,task_descr);
            this->load_description_category(parameters,"general",id_skill,task_descr);
            this->load_description_category(parameters,"user",id_skill,task_descr);
            this->load_description_category(parameters,"system",id_skill,task_descr);
            if(cpp_utils::find_json_value(parameters,"skills") && cpp_utils::find_json_value(task_descr,"skills")){
                if(cpp_utils::find_json_value(parameters["skills"],id_skill) && cpp_utils::find_json_value(task_descr["skills"],id_skill)){
                    // Read objects
                    if(cpp_utils::find_json_value(parameters["skills"][id_skill],"objects") && cpp_utils::find_json_value(task_descr["skills"][id_skill],"objects")){
                        if(parameters["skills"][id_skill]["objects"].size()!=task_descr["skills"][id_skill]["objects"].size()){
                            cpp_utils::print_error("Number of given objects for skill "+id_skill+" and number of objects defined by the task description are different.");
                            return false;
                        }
                        for(unsigned i=0;i<parameters["skills"][id_skill]["objects"].size();i++){
                            cpp_utils::overwrite_valid_json(parameters["skills"][id_skill]["objects"][i],task_descr["skills"][id_skill]["objects"][i]);
                        }
                    }else if(cpp_utils::find_json_value(parameters["skills"][id_skill],"objects")){
                        task_descr["skills"][id_skill]["objects"]=parameters["skills"][id_skill]["objects"];
                    }
                }else if(cpp_utils::find_json_value(parameters["skills"],id_skill)){
                    task_descr["skills"][id_skill]=parameters["skills"][id_skill];
                }
            }

            if(cpp_utils::find_json_value(task_descr,"skills")){
                if(cpp_utils::find_json_value(task_descr["skills"],id_skill)){
                    if(cpp_utils::find_json_value(task_descr["skills"][id_skill],"control")){
                        s.second->get_config()->controller.read_parameters(task_descr["skills"][id_skill]["control"]);
                    }
                    if(cpp_utils::find_json_value(task_descr["skills"][id_skill],"frames")){
                        s.second->get_config()->frames.read_parameters(task_descr["skills"][id_skill]["frames"]);
                    }
                    if(cpp_utils::find_json_value(task_descr["skills"][id_skill],"genral")){
                        s.second->get_config()->general.read_parameters(task_descr["skills"][id_skill]["general"]);
                    }
                    if(cpp_utils::find_json_value(task_descr["skills"][id_skill],"user")){
                        s.second->get_config()->user.read_parameters(task_descr["skills"][id_skill]["user"]);
                    }
                }
            }

            // Read skill parameters
            if(!cpp_utils::find_json_value(task_descr,"skills")){
                task_descr["skills"]=nlohmann::json();
            }
            if(!cpp_utils::find_json_value(task_descr["skills"],id_skill)){
                task_descr["skills"][id_skill]=nlohmann::json();
            }
            nlohmann::json skill_params_tmp;
            if(cpp_utils::find_json_value(task_descr["skills"][id_skill],"skill")){
                skill_params_tmp=task_descr["skills"][id_skill]["skill"];
            }
            task_descr["skills"][id_skill]["skill"]=skill_descr;
            std::set<std::string> global_skill={"time_max","w_cost_function","parallels_frequency"};
            for(nlohmann::json::const_iterator itr=skill_params_tmp.begin();itr!=skill_params_tmp.end();++itr){
                if(cpp_utils::find_json_value(task_descr["skills"][id_skill]["skill"],itr.key()) || global_skill.find(itr.key())!=global_skill.end()){
                    task_descr["skills"][id_skill]["skill"][itr.key()]=skill_params_tmp[itr.key()];
                }else{
                    cpp_utils::print_error("Skill "+id_skill+" does not have parameter "+itr.key());
                    return false;
                }
            }

            if(!s.second->read_skill_parameters(task_descr["skills"][id_skill]["skill"])){
                cpp_utils::print_error("Could not load skill parameters from task description for skill "+id_skill+".");
                return false;
            }
            s.second->read_global_skill_parameters(task_descr["skills"][id_skill]["skill"]);
            s.second->read_configuration(task_descr["skills"][id_skill]);
            if(cpp_utils::find_json_value(skill_descr,"objects")){
                if(cpp_utils::find_json_value(task_descr["skills"][id_skill],"objects") || skill_descr["objects"].size()>0){
                    if(skill_descr["objects"].size()!=task_descr["skills"][id_skill]["objects"].size()){
                        cpp_utils::print_error(std::to_string(task_descr["skills"][id_skill]["objects"].size())+" objects have been specified for skill "+ id_skill +" although "+ std::to_string(skill_descr["objects"].size()) +" are expected.");
                        return false;
                    }
                    std::map<std::string,std::string> objects;
                    for(unsigned i=0;i<skill_descr["objects"].size();i++){
                        objects.insert(std::pair<std::string,std::string>(skill_descr["objects"][i],task_descr["skills"][id_skill]["objects"][i]));
                    }
                    if(!s.second->load_objects(objects)){
                        cpp_utils::print_error("Could not load objects for skill "+id_skill);
                        return false;
                    }
                }
            }
        }
        cpp_utils::print_info("Checking task description for consistency...",false);
        if(!this->check_task_description(task_descr)){
            cpp_utils::print_info("failed.");
            cpp_utils::print_error("Detected errors in task description, aborting execution of task "+this->get_id()+".");
            return false;
        }
        cpp_utils::print_info("done.");
    }catch(const nlohmann::detail::type_error& e){
        std::cout<<e.what()<<std::endl;
        return false;
    }
    cpp_utils::print_info("Task configuration loaded.");

    this->_core->get_mios_state()->active_task=this->get_id();

    return true;
}

bool Task::grasp_object(const std::string &o, double width, double speed, double force, bool check_width){
    if(this->_core==nullptr){
        throw TaskException("Task "+ this->get_id() +" is not yet connected to the core.");
    }
    if(!this->_flag_stop){
        return this->_core->grasp_object(o,width,speed,force,check_width);
    }else{
        return true;
    }
}

bool Task::release_object(double width, double speed){
    if(this->_core==nullptr){
        throw TaskException("Task "+ this->get_id() +" is not yet connected to the core.");
    }
    if(!this->_flag_stop){
        return this->_core->release_object(width,speed);
    }else{
        return true;
    }
}

bool Task::move_gripper(double width, double speed){
    if(this->_core==nullptr){
        throw TaskException("Task "+ this->get_id() +" is not yet connected to the core.");
    }
    if(!this->_flag_stop){
        return this->_core->move_gripper(width,speed);
    }else{
        return true;
    }
}

const Percept& Task::request_percept(Eigen::Matrix<double, 3, 3> O_R_TF){
    if(this->_core==nullptr){
        throw TaskException("Could not request percept, task is not yet connected to the core.");
    }
    return this->_core->request_percept(O_R_TF);
}

void Task::set_state(const std::string& state){
    if(!this->_flag_stop){
        this->_state=state;
    }
}

std::string Task::get_state() const{
    return this->_state;
}

void Task::execute_skill(const std::string& s,bool log){
    if(this->_core==nullptr){
        throw TaskException("Task "+ this->get_id() +" is not yet connected to the core.");
    }
    if(this->_kb==nullptr){
        cpp_utils::print_critical_error("Task is not connected with knowledge base.");
        throw TaskException("Task is not connected with knowledge base.");
    }
    if(this->_skill.find(s)==this->_skill.end()){
        cpp_utils::print_error("Skill with id "+s+" not in this task. Check your task description for consistency. Stopping task.");
        this->abort_task();
        throw TaskException("Skill with id "+s+" not in this task. Check your task description for consistency. Stopping task.");
    }
    if(this->_flag_stop){
        //        cpp_utils::print_info("Task has been stopped recently, aborting skill execution.");
        return;
    }
    if(!this->_core->load_skill(this->_skill[s],log)){
        throw TaskException("Skill could not be loaded into core.");
    }
    if(!this->_core->wait_for_idle_state(2)){
        throw TaskException("Robot did not reach idle state in time.");
    }
    cpp_utils::print_info("Executing skill "+s+".");
    bool valid=this->_core->start_control_cycle();
    this->_skill[s]->terminate();
    this->_core->unload_skill();
    if(!valid){
        throw TaskException("Skill execution was not nominal.");
    }
}

void Task::execute_subtask(const std::string& t){
    if(this->_core==nullptr){
        throw TaskException("Task "+ this->get_id() +" is not yet connected to the core.");
    }
    if(this->_kb==nullptr){
        throw TaskException("Task is not connected with knowledge base.");
    }
    if(this->_subtask.find(t)==this->_subtask.end()){
        this->abort_task();
        throw TaskException("Subtask with id "+t+" not in task "+ this->_id +". Stopping task.");
    }
    if(this->_flag_stop){
        //        if(this->_kb->get_local_memory()->access_config_global()->verbosity>1){
        //            cpp_utils::print_info("Task has been stopped recently, aborting subtask execution.");
        //        }
        return;
    }
    cpp_utils::print_info("Executing subtask "+t+".");
    this->get_subtask(t)->reset_soft();
    this->get_subtask(t)->execute_task();
    cpp_utils::print_info("Subtask "+t+" has terminated.");
    this->get_subtask(t)->evaluate_task();
    if(this->get_subtask(t)->do_recovery()){
        this->get_subtask(t)->start_recovery();
        cpp_utils::print_info("Subtask "+t+" is attempting recovery.");
        this->get_subtask(t)->recover_task();
    }
    cpp_utils::print_info("End of lifecycle of subtask "+t+".");
}

bool Task::read_parameters(const nlohmann::json &params){
    if(params.is_null()){
        return true;
    }
    cpp_utils::print_error("This task has not overwritten the read_parameters method, yet the task description contains user-defined parameters. Undefined behavior is possible, aborting...");
    return false;
}

void Task::start_recovery(){
    this->_flag_in_recovery=true;
    this->_flag_stop=false;
}

void Task::complete_recovery(){
    this->_flag_in_recovery=false;
}

std::shared_ptr<Skill> Task::get_skill(const std::string& id) const{
    if(this->_skill.find(id)==this->_skill.end()){
        throw TaskException("Skill with id "+id+" not in task "+ this->get_id() +". Check your task configuration file and cpp-file for consistency.");
    }else{
        return this->_skill.at(id);
    }
}

bool Task::do_recovery() const{
    return this->_flag_recover;
}

std::shared_ptr<Task> Task::get_subtask(const std::string& id) const{
    if(this->_subtask.find(id)==this->_subtask.end()){
        throw TaskException("Subtask with id "+id+" not in task "+ this->get_id() +". Check your cpp-file for consistency.");
    }else{
        return this->_subtask.at(id);
    }
}

EvalTask Task::get_eval() const{
    return this->_eval_task;
}

//void Task::create_skill(Skill* s, std::string name){
//    if(this->_skill.find(name)!=this->_skill.end()){
//        throw TaskException("Skill with name "+name+" already exists, aborting...");
//    }else{
//        s->set_id(name);
//        this->_skill.insert(std::pair<std::string,std::shared_ptr<Skill> >(name,std::shared_ptr<Skill>(s)));
//    }
//}

//void Task::create_subtask(std::shared_ptr<Task> t, std::string name){
//    if(this->get_id()==t->get_id()){
//        throw TaskException("Can not create subtask of same type as parent task.");
//    }
//    if(this->_subtask.find(name)!=this->_subtask.end()){
//        throw TaskException("Subtask with name "+name+" already exists, aborting...");
//    }else{
//        this->_subtask.insert(std::pair<std::string,std::shared_ptr<Task> >(name,t));
//    }
//}

void Task::sleep_1ms() const{
    while(!this->_flag_stop){
        usleep(1000);
    }
}

bool Task::is_grasping(){
    if(this->_core==nullptr){
        throw TaskException("Task "+ this->get_id() +" is not yet connected to the core.");
    }
    return this->_core->is_grasping();
}

void Task::load_led_pattern(std::shared_ptr<LEDPattern> pattern){
    if(this->_core==nullptr){
        throw TaskException("Task "+ this->get_id() +" is not yet connected to the core.");
    }
    this->_core->load_led_pattern(pattern);
}

std::string Task::get_id() const{
    return this->_id;
}

bool Task::get_stop_flag() const{
    return this->_flag_stop || this->_core->has_terminated();
}

bool Task::get_recovery_flag() const{
    return this->_flag_in_recovery;
}

bool Task::check_task_description(const nlohmann::json &description) const{

    std::set<std::string> valid_syntax_top={"name","parameters","skills","mapping","_id","id_parameters","subtasks"};
    std::set<std::string> valid_syntax_skill={"skill","control","general","frames","user","objects","type"};
    std::set<std::string> valid_syntax_skill_parameters={"time_max","k_h_p","k_h_d","w_cost_function","parallels_frequency"};

    try{
        for(nlohmann::json::const_iterator itr=description.begin();itr!=description.end();++itr){
            if(valid_syntax_top.find(itr.key())==valid_syntax_top.end()){
                cpp_utils::print_error("Syntax error in task description. Symbol with value "+itr.key()+" is not valid on top level.");
                return false;
            }
        }
        if(cpp_utils::find_json_value(description,"skills")){
            for(nlohmann::json::const_iterator itr_skill=description["skills"].begin();itr_skill!=description["skills"].end();++itr_skill){
                std::string skill=itr_skill.key();
                if(!cpp_utils::find_json_value(description["skills"][skill],"type")){
                    cpp_utils::print_error("Syntax error in task description for task "+this->get_id()+". Skill " + skill + " is missing a type definition.");
                    return false;
                }else{
                    std::string type;
                    cpp_utils::read_json_param(description["skills"][skill],"type",type);
                    if(type!=this->get_skill(skill)->get_type()){
                        cpp_utils::print_error("Syntax error in task description for task "+this->get_id()+". Type of skill " + skill + " ("+this->get_skill(skill)->get_type()+") is different from type definition in skill description ("+type+").");
                        return false;
                    }
                }
                for(nlohmann::json::const_iterator itr=description["skills"][skill].begin();itr!=description["skills"][skill].end();++itr){
                    if(valid_syntax_skill.find(itr.key())==valid_syntax_skill.end()){
                        cpp_utils::print_error("Syntax error in task description for task "+this->get_id()+". Symbol with value "+itr.key()+" is not valid on skill level for skill " +skill+" of type "+this->get_skill(skill)->get_type() +".");
                        return false;
                    }
                }
                if(this->_skill.find(skill)==this->_skill.end()){
                    cpp_utils::print_error("Task description for task "+ this->get_id() +" contains skill "+skill+" of type "+this->get_skill(skill)->get_id()+" which is not contained in the task implementation.");
                    return false;
                }
                nlohmann::json skill_descr;
                if(!this->_core->get_kb()->load_skill(this->get_skill(skill)->get_type(),skill_descr)){
                    cpp_utils::print_error("Could not load a valid skill description for "+this->get_skill(skill)->get_id()+".");
                    return false;
                }
                if(cpp_utils::find_json_value(description["skills"][skill],"skill")){
                    for(nlohmann::json::const_iterator itr_p=description["skills"][skill]["skill"].begin();itr_p!=description["skills"][skill]["skill"].end();++itr_p){
                        if(!cpp_utils::find_json_value(skill_descr,itr_p.key()) && valid_syntax_skill_parameters.find(itr_p.key())==valid_syntax_skill_parameters.end()){
                            cpp_utils::print_error("Syntax error in task description for task "+this->get_id()+". Symbol with value "+itr_p.key()+" is not valid in skill description for skill "+this->get_skill(skill)->get_id()+" of type "+this->get_skill(skill)->get_type()+".");
                            return false;
                        }
                    }
                }
            }
        }
    }catch(const nlohmann::detail::type_error& e){
        std::cout<<e.what()<<std::endl;
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
                cpp_utils::print_error("Syntax error in user input. Symbol with value "+itr.key()+" is not valid on top level.");
                return false;
            }
        }
        if(cpp_utils::find_json_value(parameters, "parameters")){
            if(!cpp_utils::find_json_value(description, "parameters")){
                cpp_utils::print_error("Task " + this->_id + " has no parameters but some where given by user input.");
                return false;
            }else{
                for(nlohmann::json::const_iterator itr=parameters["parameters"].begin();itr!=parameters["parameters"].end();++itr){
                    if(!cpp_utils::find_json_value(description["parameters"], itr.key())){
                        cpp_utils::print_error("Task " + this->_id + " does not have a parameter " + itr.key() + " as provided by user input.");
                        return false;
                    }
                }
            }
        }
        if(cpp_utils::find_json_value(parameters,"skills")){
            for(nlohmann::json::const_iterator itr_skill=parameters["skills"].begin();itr_skill!=parameters["skills"].end();++itr_skill){
                std::string skill=itr_skill.key();
                std::cout<<description<<std::endl;
                if(!cpp_utils::find_json_value(description["skills"],skill)){
                    cpp_utils::print_error("Syntax error in user input for task "+this->get_id()+". Skill " + skill + " does not exist in task description.");
                    return false;
                }
                for(nlohmann::json::const_iterator itr=parameters["skills"][skill].begin();itr!=parameters["skills"][skill].end();++itr){
                    if(valid_syntax_skill.find(itr.key())==valid_syntax_skill.end()){
                        cpp_utils::print_error("Syntax error in user input for task "+this->get_id()+". Symbol with value "+itr.key()+" is not valid on skill level for skill " +skill+" of type "+this->get_skill(skill)->get_type() +".");
                        return false;
                    }
                }
                if(this->_skill.find(skill)==this->_skill.end()){
                    cpp_utils::print_error("User input for task "+ this->get_id() +" contains skill "+skill+" of type "+this->get_skill(skill)->get_id()+" which is not contained in the task implementation.");
                    return false;
                }
                nlohmann::json skill_descr;
                if(!this->_core->get_kb()->load_skill(this->get_skill(skill)->get_type(),skill_descr)){
                    cpp_utils::print_error("Could not load a valid skill description for "+this->get_skill(skill)->get_id()+".");
                    return false;
                }
                if(cpp_utils::find_json_value(description["skills"][skill],"skill")){
                    for(nlohmann::json::const_iterator itr_p=description["skills"][skill]["skill"].begin();itr_p!=description["skills"][skill]["skill"].end();++itr_p){
                        if(!cpp_utils::find_json_value(skill_descr,itr_p.key()) && valid_syntax_skill_parameters.find(itr_p.key())==valid_syntax_skill_parameters.end()){
                            cpp_utils::print_error("Syntax error in user input for task "+this->get_id()+". Symbol with value "+itr_p.key()+" is not valid in skill description for skill "+this->get_skill(skill)->get_id()+" of type "+this->get_skill(skill)->get_type()+".");
                            return false;
                        }
                    }
                }
            }
        }
    }catch(const nlohmann::detail::type_error& e){
        std::cout<<e.what()<<std::endl;
        return false;
    }
    return true;
}

void Task::load_description_category(const nlohmann::json &parameters, const std::string &category, const std::string &id_skill, nlohmann::json &task_descr) const{
    if(!cpp_utils::find_json_value(parameters,"skills")){
        return;
    }
    if(!cpp_utils::find_json_value(task_descr,"skills")){
        task_descr["skills"]=parameters["skills"];
        return;
    }
    if(!cpp_utils::find_json_value(parameters["skills"],id_skill)){
        return;
    }
    if(!cpp_utils::find_json_value(task_descr["skills"],id_skill)){
        task_descr["skills"][id_skill]=parameters["skills"][id_skill];
        return;
    }
    if(cpp_utils::find_json_value(parameters["skills"][id_skill],category) && cpp_utils::find_json_value(task_descr["skills"][id_skill],category)){

        for(nlohmann::json::const_iterator itr = parameters["skills"][id_skill][category].begin();itr != parameters["skills"][id_skill][category].end();itr++){
            cpp_utils::overwrite_valid_json(parameters["skills"][id_skill][category][itr.key()],task_descr["skills"][id_skill][category][itr.key()]);
        }
    }else if(cpp_utils::find_json_value(parameters["skills"][id_skill],category)){
        task_descr["skills"][id_skill][category]=parameters["skills"][id_skill][category];
    }
}

}
