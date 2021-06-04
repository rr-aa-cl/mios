#pragma once

#include <map>
#include <list>
#include <atomic>

#include "task/task.hpp"
#include <msrm_cpp_utils/json.hpp>

namespace mios {

class Core;
class Memory;

enum TaskLifeCycle{PreChecks,Startup,Termination,Execution,Recovery,Switch,Idle};


class TaskEngine{
public:
    TaskEngine(Core* core);

    void life_cycle();

    std::string get_active_task_id() const;
    bool is_busy() const;

    std::tuple<bool, std::string, std::string> start_task(const std::string& task_id, const nlohmann::json &parameters, bool queue_task=false);
    std::pair<bool, std::string> stop_task(bool raise_exception, bool recover, bool empty_queue);
    std::pair<bool, std::string> remove_task(const std::string &uuid);
    bool subscribe(const std::string &task_uuid, std::shared_ptr<TaskObserver> observer);
    const std::list<std::tuple<std::string, std::shared_ptr<Task>, nlohmann::json> > *get_task_queue();
    std::tuple<bool, TaskResult, std::string> wait_for_task(const std::string& task_uuid);

    void reset();
    void stop();

private:
    std::atomic<bool> m_keep_running;

    Core* m_core;
    Memory* m_memory;

    std::mutex m_mtx_task_queue;
    std::list<std::tuple<std::string,std::shared_ptr<Task>,nlohmann::json> > m_task_queue;
    TaskLifeCycle m_task_life_cycle;
    std::shared_ptr<Task> m_active_task;
};

}
