#pragma once

#include <map>
#include <memory>


namespace mios{
class Task;
class Core;

enum TaskName{TaskName_IdleTask,TaskName_TestTask1,TaskName_TestTask2,TaskName_TestTask3,TaskName_NullTask};

class TaskFactory{
public:
    static TaskName get_task_name(const std::string& task);
    static std::shared_ptr<Task> create_task(TaskName task, mios::Core *core);
};
}
