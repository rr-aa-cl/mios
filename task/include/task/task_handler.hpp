#pragma once

#include <map>
#include <list>
#include <atomic>

#include "task/task.hpp"
#include "cpp_utils/json.hpp"

namespace mios {

class Core;
class TaskList;

class TaskSubscriber{
public:
    TaskSubscriber(const std::string &id);

    const EvalTask &wait();
    void finish(const EvalTask &e);
    std::string get_id();
private:
    EvalTask _e;
    std::atomic<bool> _finished;
    std::string _id;
};

class TaskHandler{
public:
    TaskHandler(std::shared_ptr<Core> core);
    ~TaskHandler();

    void activity();
    void set_interrupt(bool on);

    std::string get_active_task_id();

    std::pair<bool, std::string> start_task(const std::string& task, const nlohmann::json &parameters, bool queue_task=false);
    std::pair<bool, std::string> stop_task(bool nominal=false, bool success=false, bool recover=true, bool empty_queue=false, double cost_suc=0, double cost_err=0);
    std::pair<bool, std::string> terminate_all_tasks();
    std::pair<bool, std::string> remove_task(const std::string &id);
    bool has_id(const std::string& id);
    bool subscribe(std::shared_ptr<TaskSubscriber> sub);
    void unsubcribe(const std::string& task_uuid, const std::set<std::shared_ptr<TaskSubscriber> >::iterator& it);
    bool is_valid_subscriber(const std::string& task_uuid,const std::set<std::shared_ptr<TaskSubscriber> >::iterator& it);
    bool request_eval(const std::string& id,EvalTask& e);
    const std::list<std::tuple<std::string,std::string,nlohmann::json> >* get_task_queue();
    std::pair<EvalTask, bool> wait_for_task(const std::string& task_uuid);
    std::pair<EvalTask, bool> check_if_finished(const std::string& task_uuid);

    bool is_busy();
    void reset();

private:
    bool add_id(const std::string& id);
    bool terminate_task(const std::string& id, const EvalTask& e);

    std::string get_unique_task_id();

    std::unique_ptr<TaskList> _task_list;
    std::list<std::tuple<std::string,std::string,nlohmann::json> > _task_queue;
    std::map<std::string,std::set<std::shared_ptr<TaskSubscriber> > > _sub;
    std::map<std::string,EvalTask> _eval_storage;
    std::shared_ptr<Task> _active_task;

    std::mutex _mtx_task_queue;
    std::mutex _mtx_termination_phase;

    std::shared_ptr<Core> _core;

    std::atomic<bool> _flag_interrupt;
    std::atomic<bool> _flag_user_stop;
    std::atomic<bool> _flag_invalid;
    std::atomic<bool> _flag_shutdown;
    std::atomic<bool> _flag_busy;

};

}
