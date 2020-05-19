#include "task/task_handler.hpp"
#include "task/taskfactory.hpp"
#include "core/core.hpp"
#include "memory/memory.hpp"

#include <sstream>
#include <spdlog/spdlog.h>

namespace mios {



TaskEngine::TaskEngine(Core *core):m_core(core),m_memory(core->get_memory()),m_task_life_cycle(TaskLifeCycle::Switch),m_active_task(TaskFactory::create_task(TaskName::TaskName_IdleTask,core)){
}

void TaskEngine::reset(){

}

std::string TaskEngine::get_active_task_id() const{
    return m_active_task->get_id();
}

void TaskEngine::life_cycle(){
    while(true){
        bool exceptional_event=false;
        bool user_stop=false;
        bool invalid_mode=false;
        bool guiding=false;
        bool reflex=false;
        bool recovery=false;
        if(m_task_life_cycle==TaskLifeCycle::PreChecks){
            franka::RobotMode mode;
            try{
                mode=m_core->request_percept().robot_mode;
            }catch(const CoreException& e){
                std::cout<<e.what()<<std::endl;
                mode=franka::RobotMode::kOther;
            }
            if(mode==franka::RobotMode::kMove){
                spdlog::critical("Robot is moving but it is not expected that it moves in the current state.");
                std::this_thread::sleep_for(std::chrono::seconds(1));
                continue;
            }
            // Handle reflex
            if(reflex && mode!=franka::RobotMode::kReflex){
                reflex=false;
            }
            if(!reflex && mode==franka::RobotMode::kReflex){
                spdlog::warn("Robot has executed a reflex, attempting to recover...");
                if(!m_core->recover()){
                    spdlog::error("Automatic recovery failed, please toggle the user stop...");
                }
                m_mtx_task_queue.lock();
                m_task_queue.clear();
                m_mtx_task_queue.unlock();
                reflex=true;
                continue;
            }
            if(reflex && mode==franka::RobotMode::kReflex){
                std::this_thread::sleep_for(std::chrono::milliseconds(10));
            }
            // Handle other mode
            if(invalid_mode && mode!=franka::RobotMode::kOther){
                invalid_mode=false;
            }
            if(!invalid_mode && mode==franka::RobotMode::kOther){
                spdlog::warn("Robot is in invalid mode, attempting to recover...");
                if(!m_core->recover()){
                    spdlog::error("Automatic recovery failed, please toggle the user stop...");
                }
                m_mtx_task_queue.lock();
                m_task_queue.clear();
                m_mtx_task_queue.unlock();
                invalid_mode=true;
                continue;
            }
            if(invalid_mode && mode==franka::RobotMode::kOther){
                std::this_thread::sleep_for(std::chrono::milliseconds(10));
            }
            // Handle automatic error recovery
            if(recovery && mode!=franka::RobotMode::kAutomaticErrorRecovery){
                recovery=false;
            }
            if(!recovery && mode==franka::RobotMode::kAutomaticErrorRecovery){
                spdlog::warn("Performing automatic error recovery, please wait...");
                m_mtx_task_queue.lock();
                m_task_queue.clear();
                m_mtx_task_queue.unlock();
                recovery=true;
                continue;
            }
            if(recovery && mode==franka::RobotMode::kAutomaticErrorRecovery){
                std::this_thread::sleep_for(std::chrono::milliseconds(10));
            }
            // Handle guiding mode
            if(guiding && mode!=franka::RobotMode::kGuiding){
                guiding=false;
            }
            if(!guiding && mode==franka::RobotMode::kGuiding){
                spdlog::warn("Robot is in guiding mode, waiting for stop...");
                m_mtx_task_queue.lock();
                m_task_queue.clear();
                m_mtx_task_queue.unlock();
                guiding=true;
                continue;
            }
            if(guiding && mode==franka::RobotMode::kGuiding){
                std::this_thread::sleep_for(std::chrono::milliseconds(10));
            }
            // Handle user stop
            if(user_stop && mode!=franka::RobotMode::kUserStopped){
                user_stop=false;
            }
            if(!user_stop && mode==franka::RobotMode::kUserStopped){
                spdlog::warn("User stop has been pressed, waiting for release...");
                m_mtx_task_queue.lock();
                m_task_queue.clear();
                m_mtx_task_queue.unlock();
                user_stop=true;
                continue;
            }
            if(user_stop && mode==franka::RobotMode::kUserStopped){
                std::this_thread::sleep_for(std::chrono::milliseconds(10));
            }
            m_task_life_cycle=TaskLifeCycle::Startup;
        }
        if(m_task_life_cycle==TaskLifeCycle::Startup){
            spdlog::debug("TaskLifeCycle: startup, task_uuid: "+m_active_task->get_uuid());
            try{
                spdlog::info("Loading task " + m_active_task->get_id() + " with uuid " + m_active_task->get_uuid());
                std::scoped_lock<std::mutex> queue_lock(m_mtx_task_queue);
                if(!m_active_task->load(std::get<2>(m_task_queue.front()))){
                    spdlog::error("Could not load task "+m_active_task->get_id()+".");
                    m_task_life_cycle=TaskLifeCycle::Termination;
                    exceptional_event=true;
                }else{
                    m_task_life_cycle=TaskLifeCycle::Execution;
                }
            }catch(const std::exception& e){
                std::cout<<e.what()<<std::endl;
                exceptional_event=true;
                m_task_life_cycle=TaskLifeCycle::Termination;
            }
        }
        if(m_task_life_cycle==TaskLifeCycle::Execution){
            spdlog::debug("TaskLifeCycle: execution, task_uuid: "+m_active_task->get_uuid());
            try{
                spdlog::info("Executing task " + m_active_task->get_id() + " with uuid " + m_active_task->get_uuid());
                m_active_task->execute_task();
            }catch(const std::exception& e){
                std::cout<<e.what()<<std::endl;
                exceptional_event=true;
            }
            m_task_life_cycle=TaskLifeCycle::Recovery;
        }
        if(m_task_life_cycle==TaskLifeCycle::Recovery){
            spdlog::debug("TaskLifeCycle: recovery, task_uuid: "+m_active_task->get_uuid());
            try{
                if(m_active_task->do_recovery()){
                    spdlog::info("Recovering task " + m_active_task->get_id() + " with uuid " + m_active_task->get_uuid());
                    m_active_task->start_recovery();
                    m_active_task->recover_task();
                    m_active_task->complete_recovery();
                }
            }catch(const std::exception& e){
                std::cout<<e.what()<<std::endl;
                exceptional_event=true;
            }
            m_task_life_cycle=TaskLifeCycle::Termination;
        }
        if(m_task_life_cycle==TaskLifeCycle::Termination){
            spdlog::debug("TaskLifeCycle: termination, task_uuid: "+m_active_task->get_uuid());
            try{
                spdlog::info("Terminating task " + m_active_task->get_id() + " with uuid " + m_active_task->get_uuid());
                m_active_task->evaluate_task();
            }catch(const std::exception& e){
                std::cout<<e.what()<<std::endl;
            }
            m_eval_storage.emplace(std::pair<std::string,EvalTask>(m_active_task->get_uuid(),m_active_task->get_eval()));
            m_task_life_cycle=TaskLifeCycle::Switch;
        }
        if(m_task_life_cycle==TaskLifeCycle::Switch){
            std::scoped_lock<std::mutex> queue_lock(m_mtx_task_queue);
            spdlog::debug("TaskLifeCycle: switch, task_uuid: "+m_active_task->get_uuid());
            if(!m_task_queue.empty()){
                m_task_queue.pop_front();
            }
            if(!m_active_task->get_eval().nominal_termination || exceptional_event || m_active_task->get_eval().empty_queue){
                m_task_queue.clear();
            }
            if(m_task_queue.empty()){
                m_task_queue.emplace_back(std::make_tuple("IdleTask",m_memory->load_task("IdleTask",nlohmann::json(),m_core),nlohmann::json()));
            }
            m_active_task = std::get<1>(m_task_queue.front());
            m_task_life_cycle = TaskLifeCycle::Startup;
            spdlog::debug("TaskLifeCycle: switched to task "+m_active_task->get_id() + " with uuid " + m_active_task->get_uuid());
        }
    }
}

std::tuple<bool,std::string,std::string> TaskEngine::start_task(const std::string &task_id, const nlohmann::json &parameters, bool queue_task){
    std::scoped_lock<std::mutex> queue_lock(m_mtx_task_queue);
    std::string err="";
    std::string task_uuid="INVALID";
    bool result=false;

    if(!queue_task){
        if(m_active_task->get_id()=="IdleTask" && m_task_queue.size()==1){
            queue_task=true;
        }else{
            err="Cannot start new task while another task is still active. In order to queue a new task set the argument queue to true.";
            task_uuid="INVALID";
            result=false;
        }
    }
    if(queue_task){
        TaskName task_name = TaskFactory::get_task_name(task_id);
        if(task_name==TaskName::TaskName_None){
            task_name=TaskName::TaskName_IdleTask;
            err="No task with name " + task_id + " exists.";
            task_uuid="INVALID";
            result=false;
        }else{
            std::shared_ptr<Task> new_task=m_memory->load_task(task_id,parameters,m_core);
            spdlog::info("Queuing task with uuid " + new_task->get_uuid());

            m_task_queue.emplace_back(std::tuple<std::string,std::shared_ptr<Task>,nlohmann::json>(new_task->get_uuid(),new_task,parameters));
            result=true;
            task_uuid=new_task->get_uuid();
            if(m_active_task->get_id()=="IdleTask"){
                spdlog::debug("Stopping IdleTask with uuid " +m_active_task->get_uuid());
                m_active_task->stop_task(true,true,true);
            }
        }
    }
    return std::make_tuple(result,task_uuid,err);
}

std::pair<bool,std::string> TaskEngine::stop_task(bool nominal, bool success, bool recover,bool empty_queue, double cost_suc, double cost_err){
    if(m_active_task->get_id()=="IdleTask"){
        return std::pair<bool,std::string>(true,"");
    }
    spdlog::info("Stopping active task.");
    m_active_task->stop_task(nominal,success,recover,empty_queue,cost_suc,cost_err);
    return std::pair<bool,std::string>(true,"");
}

std::pair<bool,std::string> TaskEngine::remove_task(const std::string& uuid){
    std::scoped_lock<std::mutex> lock(m_mtx_task_queue);
    auto it=m_task_queue.begin();
    while(it!=m_task_queue.end()){
        if(std::get<1>(*it)->get_uuid()==uuid){
            m_task_queue.erase(it++);
            return std::pair<bool,std::string>(true,"Removed task with uuid "+uuid+" from queue.");
        }else{
            ++it;
        }
    }
    return std::pair<bool,std::string>(false,"No task with uuid "+uuid+" in queue.");
}

bool TaskEngine::subscribe(const std::string& task_uuid, std::shared_ptr<TaskObserver> observer){
    bool found_uuid=false;
    for(const auto& t : m_task_queue){
        if(std::get<1>(t)->get_uuid()==task_uuid){
            std::get<1>(t)->subscribe(observer);
            found_uuid=true;
        }
    }
    if(!found_uuid){
        return false;
    }else{
        spdlog::info("Subscribing to task with uuid "+task_uuid+".");
        return true;
    }
}

std::tuple<bool,EvalTask,std::string> TaskEngine::wait_for_task(const std::string &task_uuid){
    std::shared_ptr<TaskObserver> observer = std::make_shared<TaskObserver>();
    EvalTask e;
    std::string err="";
    bool result=false;
    if(this->subscribe(task_uuid,observer)){
        observer->wait_for_finish();
    }
    if(this->request_eval(task_uuid,e)){
        msrm_utils::print_info("Loaded task evaluation for task with uuid "+task_uuid+" from memory.");
        result=true;
    }else{
        err="I have no memory of a task with uuid " + task_uuid;
        result=false;
    }
    return std::make_tuple(result,e,err);
}

std::pair<EvalTask, bool> TaskEngine::check_if_finished(const std::string &task_uuid){
    EvalTask e;
    if(this->request_eval(task_uuid,e)){
        return std::pair<EvalTask,bool>(e,true);
    }else{
        return std::pair<EvalTask,bool>(e,false);
    }
}

bool TaskEngine::request_eval(const std::string &id, EvalTask &e) const{
    if(m_eval_storage.find(id)==m_eval_storage.end()){
        return false;
    }else{
        e=m_eval_storage.at(id);
        return true;
    }
}

bool TaskEngine::is_busy() const{
    if((m_task_life_cycle==TaskLifeCycle::Startup || m_task_life_cycle==TaskLifeCycle::Execution) && m_active_task->get_id()=="IdleTask"){
        return false;
    }else{
        return true;
    }
}

const std::list<std::tuple<std::string, std::shared_ptr<Task>, nlohmann::json> > *TaskEngine::get_task_queue(){
    return &m_task_queue;
}

}
