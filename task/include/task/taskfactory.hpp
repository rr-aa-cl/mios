#pragma once
#include <memory>

namespace mios{
class Task;
class Core;
enum TaskName{TaskNameNullTask,TaskNameGenericTask,TaskNameTestTask2,TaskNameTestTask1,TaskNameIdleTask,TaskNameLearnerTest,TaskNameTestTask3,TaskNameMoveToCartPose,TaskNameMoveToJointPose};
class TaskFactory{
public:
static TaskName get_task_name(const std::string& task);
static std::shared_ptr<Task> create_task(TaskName task, Core* core);
};
}
