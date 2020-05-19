#pragma once

#include <map>
#include <list>
#include <atomic>

#include "task/task.hpp"
#include <msrm_utils/json.hpp>

namespace mios {

class Core;
class TaskList;
class Memory;

enum TaskLifeCycle{PreChecks,Startup,Termination,Execution,Recovery,Switch,Idle};


class TaskEngine{
public:
    TaskEngine(Core* core,);

    void life_cycle();

    std::string get_active_task_id() const;
    bool is_busy() const;

    std::tuple<bool, std::string, std::string> start_task(const std::string& task_id, const nlohmann::json &parameters, bool queue_task=false);
    std::pair<bool, std::string> stop_task(bool nominal=false, bool success=false, bool recover=true, bool empty_queue=false, double cost_suc=0, double cost_err=0);
    std::pair<bool, std::string> remove_task(const std::string &uuid);
    bool subscribe(const std::string &task_uuid, std::shared_ptr<TaskObserver> observer);
    bool request_eval(const std::string& id,EvalTask& e) const;
    const std::list<std::tuple<std::string, std::shared_ptr<Task>, nlohmann::json> > *get_task_queue();
    std::tuple<bool, EvalTask, std::string> wait_for_task(const std::string& task_uuid);
    std::pair<EvalTask, bool> check_if_finished(const std::string& task_uuid);

    void reset();

private:
    std::mutex m_mtx_task_queue;
    std::list<std::tuple<std::string,std::shared_ptr<Task>,nlohmann::json> > m_task_queue;
    TaskLifeCycle m_task_life_cycle;
    std::shared_ptr<Task> m_active_task;
    std::map<std::string,EvalTask> m_eval_storage;

    Core* m_core;
    Memory* m_memory;
};

}
