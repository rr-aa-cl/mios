#include "task/task_handler.hpp"

#include "core/core.hpp"
#include "task/task_list.hpp"

#include <boost/uuid/uuid_generators.hpp>
#include <boost/uuid/uuid.hpp>
#include <boost/uuid/uuid_io.hpp>

#include <sstream>

namespace mios {

TaskSubscriber::TaskSubscriber(const std::string& id){
    this->_id=id;
    this->_finished=false;
}

const EvalTask& TaskSubscriber::wait(){
    while(true){
        if(this->_finished){
            return this->_e;
        }
        usleep(10000);
    }
}

void TaskSubscriber::finish(const EvalTask& e){
    this->_e=e;
    this->_finished=true;
}

std::string TaskSubscriber::get_id(){
    return this->_id;
}

TaskHandler::TaskHandler(std::shared_ptr<Core> core){
    this->_core=core;
    this->_task_list = std::make_unique<TaskList>();
    this->_active_task=nullptr;
    this->_sub.insert(std::pair<std::string,std::set<std::shared_ptr<TaskSubscriber> > >("idle_task",std::set<std::shared_ptr<TaskSubscriber> >()));
    this->_flag_interrupt=false;
    this->_flag_user_stop=false;
    this->_flag_invalid=false;
    this->_flag_busy=true;
}

TaskHandler::~TaskHandler(){

}
bool TaskHandler::is_busy(){
    return this->_flag_busy;
}

void TaskHandler::reset(){
    //    this->_flag_interrupt=false;
    this->_flag_user_stop=false;
    if(this->_active_task!=nullptr){
        this->_active_task->stop_task(false,false,false,false,0,0);
    }
    while(this->_active_task!=nullptr){
        usleep(1000);
    }
}

std::string TaskHandler::get_active_task_id(){
    if(this->_active_task==nullptr){
        return "none";
    }else{
        return this->_active_task->get_id();
    }
}

void TaskHandler::activity(){
    bool abort=false;
    bool shutdown=false;
    while(true){
        if(this->_flag_interrupt){
            usleep(10000);
            continue;
        }
        franka::RobotMode mode;
        if(!this->_core->has_robot_connection() && !shutdown){
            shutdown=true;
        }else if(!this->_core->has_robot_connection()){
            if(this->_core->initialize()){
                shutdown=false;
            }
            usleep(1000);
            continue;
        }
        try{
            mode=this->_core->request_percept().robot_mode;
        }catch(const CoreException& e){
            std::cout<<e.what()<<std::endl;
            mode=franka::RobotMode::kOther;
        }
        if(mode==franka::RobotMode::kAutomaticErrorRecovery){
            msrm_utils::print_warning("Attempting to recover...");
            sleep(1);
            continue;
        }
        if(this->_flag_user_stop && mode!=franka::RobotMode::kUserStopped){
            this->_flag_user_stop=false;
        }else if(this->_flag_user_stop){
            this->_mtx_task_queue.lock();
            this->_task_queue.clear();
            this->_mtx_task_queue.unlock();
            usleep(1000);
            continue;
        }
        if(this->_flag_invalid && mode!=franka::RobotMode::kOther){
            this->_flag_invalid=false;
        }else if(this->_flag_invalid){
            usleep(1000);
            continue;
        }
        if(mode==franka::RobotMode::kGuiding){
            msrm_utils::print_warning("Waiting for guiding mode to terminate...");
            sleep(1);
            continue;
        }
        if(mode==franka::RobotMode::kMove){
            msrm_utils::print_critical_error("Robot is moving, assuming second libfranka instance, attempting to recover.");
            if(!this->_core->recover()){
                msrm_utils::print_error("Recovery has failed, attempting to reset core...");
                if(!this->_core->reset()){
                    msrm_utils::print_critical_error("Core reset has failed, trying again in 5 seconds.");
                    sleep(5);
                    continue;
                }
            }
        }
        if(mode==franka::RobotMode::kOther){
            msrm_utils::print_error("Undefined mode, attempting to recover.");
            if(!this->_core->recover()){
                msrm_utils::print_error("Recovery has failed, attempting to reset core...");
                if(!this->_core->reset()){
                    msrm_utils::print_critical_error("Core reset has failed, trying again in 5 seconds.");
                    sleep(5);
                    continue;
                }else{
                    msrm_utils::print_success("Core reset successful.");
                }
            }else{
                msrm_utils::print_success("Recovery successful, resuming normal activity.");
                continue;
            }
        }
        if(mode==franka::RobotMode::kReflex){
            msrm_utils::print_error("Unhandled reflex, attempting to recover.");
            if(!this->_core->recover()){
                msrm_utils::print_error("Recovery has failed, attempting to reset core...");
                if(!this->_core->reset()){
                    msrm_utils::print_critical_error("Core reset has failed, trying again in 5 seconds.");
                    sleep(5);
                    continue;
                }
            }
        }
        if(mode==franka::RobotMode::kUserStopped){
            std::map<std::string,std::array<unsigned,3> > colors;
            colors["far-left"]={255,255,0};
            colors["left"]={255,255,0};
            colors["middle"]={255,255,0};
            colors["right"]={255,255,0};
            colors["far-right"]={255,255,0};
            this->_core->load_led_pattern(std::make_shared<pattern_custom>(colors));
            msrm_utils::print_warning("User stop has been pressed, waiting for release...");
            this->_mtx_termination_phase.lock();
            this->terminate_all_tasks();
            this->_mtx_termination_phase.unlock();
            this->_flag_user_stop=true;
            continue;
        }

        abort=false;
        this->_mtx_task_queue.lock();
        if(this->_task_queue.empty()){
            nlohmann::json request_idle;
            this->_task_queue.emplace_back(std::tuple<std::string,std::string,nlohmann::json>("idle_task","idle_task",request_idle));
        }
        std::tuple<std::string,std::string,nlohmann::json> t=this->_task_queue.front();
        std::string task_id=std::get<1>(t);
        msrm_utils::print_info("############################################################");
        msrm_utils::print_info("Loading task "+task_id+"...");
        this->_active_task=this->_task_list->tasks[task_id];
        try{
            if(!this->_active_task->load(std::get<2>(t),this->_core)){
                msrm_utils::print_error("Could not load task "+task_id+".");
                abort=true;
            }
        }catch(const TaskException& e){
            std::cout<<e.what()<<std::endl;
            abort=true;
        }catch(const SkillException& e){
            std::cout<<e.what()<<std::endl;
            abort=true;
        }catch(const CoreException& e){
            std::cout<<e.what()<<std::endl;
            abort=true;
        }
        this->_mtx_task_queue.unlock();
        msrm_utils::print_info("############################################################");
        try{
            mode = this->_core->request_percept().robot_mode;
        }catch(const CoreException& e){
            std::cout<<e.what()<<std::endl;
            mode=franka::RobotMode::kOther;
        }

        if(mode==franka::RobotMode::kOther){
            msrm_utils::print_warning("Robot is in invalid mode, aborting all tasks.");
            this->_mtx_termination_phase.lock();
            this->terminate_all_tasks();
            this->_mtx_termination_phase.unlock();
            this->_flag_invalid=true;
            continue;
        }
        if(!abort){
            msrm_utils::print_info("############################################################");
            msrm_utils::print_info("Executing "+task_id+" with uuid "+std::get<0>(t)+".");
            try{
                if(this->_active_task->get_id()=="idle_task"){
                    this->_flag_busy=false;
                }
                this->_active_task->execute_task();
                this->_flag_busy=true;
                msrm_utils::print_info("Task "+task_id+" has terminated.");
            }catch(const TaskException& e){
                std::cout<<e.what()<<std::endl;
                abort=true;
            }catch(const SkillException& e){
                std::cout<<e.what()<<std::endl;
                abort=true;
            }catch(const CoreException& e){
                std::cout<<e.what()<<std::endl;
                abort=true;
            }
            try{
                if(this->_active_task->do_recovery()){
                    msrm_utils::print_info("Attempting recovery for task "+task_id+".");
                    this->_active_task->start_recovery();
                    this->_active_task->recover_task();
                    this->_active_task->complete_recovery();
                }
            }catch(const TaskException& e){
                std::cout<<e.what()<<std::endl;
                abort=true;
            }catch(const SkillException& e){
                std::cout<<e.what()<<std::endl;
                abort=true;
            }catch(const CoreException& e){
                std::cout<<e.what()<<std::endl;
                abort=true;
            }
        }
        assert(this->_active_task!=nullptr);
        this->_mtx_termination_phase.lock();
        if(!this->_active_task->get_eval().nominal_termination || abort){
            msrm_utils::print_error("Could not execute task "+task_id+" nominally. Emptying remaining task queue...");
            this->_active_task->get_eval().last_error=this->_core->get_last_error();
            this->terminate_all_tasks();
        }else if(this->_active_task->get_eval().empty_queue){
            msrm_utils::print_info("Emptying remaining task queue as requested.");
            this->terminate_all_tasks();
        }else{
            try{
                this->terminate_task(std::get<0>(t),this->_active_task->evaluate_task());
                this->_sub.erase(std::get<0>(t));
            }catch(const TaskException& e){
                std::cout<<e.what()<<std::endl;
            }catch(const SkillException& e){
                std::cout<<e.what()<<std::endl;
            }catch(const CoreException& e){
                std::cout<<e.what()<<std::endl;
            }
            this->_mtx_task_queue.lock();
            this->_task_queue.pop_front();
            this->_mtx_task_queue.unlock();
        }
        this->_active_task=nullptr;
        msrm_utils::print_info("End of lifecycle of task "+task_id+".");
        msrm_utils::print_info("############################################################");
        this->_mtx_termination_phase.unlock();
    }
}

void TaskHandler::set_interrupt(bool on){
    this->_flag_interrupt=on;
}

std::pair<bool,std::string> TaskHandler::start_task(const std::string &task, const nlohmann::json &parameters, bool queue_task){
    this->_mtx_termination_phase.lock();
    this->_mtx_termination_phase.unlock();
    std::string err="";
    if(this->_active_task!=nullptr){
        if(!queue_task && this->_active_task->get_recovery_flag()){
            msrm_utils::print_warning("A task with id "+this->_active_task->get_id()+" is currently running its recovery procedure. To queue a task set the parameter 'queue_task' to true.");
            err="A task with id "+this->_active_task->get_id()+" is currently running its recovery procedure. To queue a task set the parameter 'queue_task' to true.";
            return std::pair<bool,std::string>(false,err);
        }
        if(!queue_task && this->_active_task->get_id()!="idle_task"){
            msrm_utils::print_warning("Another task with id "+this->_active_task->get_id()+" is currently running. To queue a task set the parameter 'queue_task' to true.");
            err="Another task with id "+this->_active_task->get_id()+" is currenlty running. To queue a task set the parameter 'queue_task' to true.";
            return std::pair<bool,std::string>(false,err);
        }
    }
    if(this->_task_list->tasks.find(task)==this->_task_list->tasks.end()){
        msrm_utils::print_error("No implementation of task "+task+" found.");
        err="No implementation of task "+task+" found.";
        return std::pair<bool,std::string>(false,err);
    }
    if(this->_flag_invalid){
        msrm_utils::print_error("Cannot start task while in invalid mode.");
        err="Cannot start task while in invalid mode.";
        return std::pair<bool,std::string>(false,err);
    }
    if(this->_flag_user_stop){
        msrm_utils::print_error("Cannot start task while user-stop is pressed.");
        err="Cannot start task while user-stop is pressed.";
        return std::pair<bool,std::string>(false,err);
    }
    this->_mtx_task_queue.lock();
    std::string unique_id=this->get_unique_task_id();
    if(!this->add_id(unique_id)){
        msrm_utils::print_error("Task handler could not queue task "+task+" with uuid "+unique_id+".");
        err="Task handler could not queue task "+task+" with uuid "+unique_id+".";
        this->_mtx_task_queue.unlock();
        return std::pair<bool,std::string>(false,err);
    }
    this->_task_queue.emplace_back(std::tuple<std::string,std::string,nlohmann::json>(unique_id,task,parameters));
    msrm_utils::print_info("Queued task "+task+" with uuid "+unique_id+".");
    this->_mtx_task_queue.unlock();
    if(this->_active_task!=nullptr){
        if(this->_active_task->get_id()=="idle_task"){
            this->_active_task->stop_task(true);
        }
    }
    return std::pair<bool,std::string>(true,unique_id);
}

std::pair<bool,std::string> TaskHandler::stop_task(bool nominal, bool success, bool recover,bool empty_queue, double cost_suc, double cost_err){
    if(this->_active_task!=nullptr){
        if(this->_active_task->get_id()=="idle_task"){
            return std::pair<bool,std::string>(true,"");
        }
        msrm_utils::print_info("Stopping active task.");
        this->_active_task->stop_task(nominal,success,recover,empty_queue,cost_suc,cost_err);
        return std::pair<bool,std::string>(true,"");
    }else{
        return std::pair<bool,std::string>(true,"No active task to stop.");
    }
}

std::pair<bool,std::string> TaskHandler::remove_task(const std::string& id){
    this->_mtx_task_queue.lock();
    std::list<std::tuple<std::string,std::string,nlohmann::json> >::iterator it;
    for(it=this->_task_queue.begin();it!=this->_task_queue.end();++it){
        if(std::get<0>(*it)==id){
//            if(it==this->_task_queue.begin()){
//                this->_mtx_task_queue.unlock();
//                return std::pair<bool,std::string>(false,"Cannot remove active task from queue.");
//            }
            EvalTask e;
            e.last_error=this->_core->get_last_error();
            this->terminate_task(id,e);
            this->_sub.erase(id);
            this->_task_queue.erase(it);
            this->_mtx_task_queue.unlock();
            return std::pair<bool,std::string>(true,"Removed task with uuid "+id+" from queue.");
        }
    }
    this->_mtx_task_queue.unlock();
    return std::pair<bool,std::string>(false,"No task with uuid "+id+" in queue.");
}

std::pair<bool,std::string> TaskHandler::terminate_all_tasks(){
    if(this->_active_task!=nullptr && this->_active_task->get_id()!="idle_task"){
        this->_active_task->abort_task();
    }
    std::list<std::tuple<std::string,std::string,nlohmann::json> > tmp_task_queue=this->_task_queue;
    for(const auto& t : tmp_task_queue){
        if(std::get<0>(t)=="idle_task"){
            continue;
        }
        std::pair<bool,std::string> rtn = this->remove_task(std::get<0>(t));
        msrm_utils::print_info(rtn.second);
    }
    this->_mtx_task_queue.lock();
    this->_task_queue.clear();
    this->_mtx_task_queue.unlock();
    return std::pair<bool,std::string>(true,"Task queue is cleared.");
}

bool TaskHandler::add_id(const std::string &id){
    if(this->_sub.find(id)!=this->_sub.end()){
        msrm_utils::print_critical_error("uuid "+id+" has already been given to a task. The routine to create a uuid seems to be faulty.");
        return false;
    }
    this->_sub.insert(std::pair<std::string,std::set<std::shared_ptr<TaskSubscriber> > >(id,std::set<std::shared_ptr<TaskSubscriber> >()));
    return true;
}

bool TaskHandler::terminate_task(const std::string &id, const EvalTask &e){
    std::map<std::string,std::set<std::shared_ptr<TaskSubscriber> > >::iterator it=this->_sub.find(id);
    if(it==this->_sub.end() && id!="idle_task"){
        msrm_utils::print_critical_error("In terminate_task: uuid "+id+" is not known to the task handler. There is a critical error in the task handling routine.");
        return false;
    }

    msrm_utils::print_info("Finished task with uuid "+id+", informing subscribers.");
    this->_eval_storage.insert(std::pair<std::string,EvalTask>(id,e));

    for(auto& t : this->_sub[id]){

        t->finish(e);
    }
    return true;
}

bool TaskHandler::subscribe(std::shared_ptr<TaskSubscriber> sub){
    if(this->_sub.find(sub->get_id())==this->_sub.end()){
        msrm_utils::print_warning("Cannot subscribe to task with uuid "+sub->get_id()+" because it is not known to the task handler. "
                                                                                     "The task may have terminated already or was discarded due to an error. "
                                                                                     "I will attempt to look up the task evaluation for this uuid from memory.");
        return false;
    }else{
        msrm_utils::print_info("Subscribing to task with uuid "+sub->get_id()+".");
        this->_sub[sub->get_id()].insert(sub);
        return true;
    }
}

void TaskHandler::unsubcribe(const std::string &task_uuid, const std::set<std::shared_ptr<TaskSubscriber> >::iterator &it){
    if(this->_sub.find(task_uuid)==this->_sub.end()){
        msrm_utils::print_warning("No task with uuid "+task_uuid+" is active or has been active in the past.");
        return;
    }
    if(it==this->_sub[task_uuid].end()){
        msrm_utils::print_warning("Cannot unsubscribe, invalid task subscriber.");
        return;
    }
    this->_sub[task_uuid].erase(it);
}

bool TaskHandler::is_valid_subscriber(const std::string &task_uuid, const std::set<std::shared_ptr<TaskSubscriber> >::iterator &it){
    if(it==this->_sub[task_uuid].end()){
        return false;
    }else{
        return true;
    }
}

std::pair<EvalTask,bool> TaskHandler::wait_for_task(const std::string &task_uuid){
//    TaskSubscriber sub(task_uuid);
    std::shared_ptr<TaskSubscriber> sub = std::make_shared<TaskSubscriber>(task_uuid);
    EvalTask e;
    bool result=false;
    if(this->subscribe(sub)){
        e = sub->wait();
        result=true;
    }else if(this->request_eval(task_uuid,e)){
        msrm_utils::print_info("Loaded task evaluation for task with uuid "+task_uuid+" from memory.");
        result=true;
    }else{
        result=false;
    }
    //    this->unsubcribe(task_uuid,sub_it);
    return std::pair<EvalTask,bool>(e,result);
}

std::pair<EvalTask, bool> TaskHandler::check_if_finished(const std::string &task_uuid){
    EvalTask e;
    if(this->request_eval(task_uuid,e)){
        return std::pair<EvalTask,bool>(e,true);
    }else{
        return std::pair<EvalTask,bool>(e,false);
    }
}

bool TaskHandler::request_eval(const std::string &id, EvalTask &e){
    if(this->_eval_storage.find(id)==this->_eval_storage.end()){
        //        msrm_utils::print_error("Task with uuid "+id+" has not been executed in the past.");
        return false;
    }
    e=this->_eval_storage[id];
    return true;
}

std::string TaskHandler::get_unique_task_id(){
    boost::uuids::uuid task_uuid = boost::uuids::random_generator()();
    std::stringstream ss;
    ss<<task_uuid;
    return ss.str();
    return std::to_string(886);
}

bool TaskHandler::has_id(const std::string &id){
    if(this->_sub.find(id)!=this->_sub.end()){
        return true;
    }else{
        return false;
    }
}

const std::list<std::tuple<std::string, std::string, nlohmann::json> > *TaskHandler::get_task_queue(){
    return &this->_task_queue;
}

}
