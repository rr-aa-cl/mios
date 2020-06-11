#include "task/taskfactory.hpp"
#include "task/task.hpp"
#include <msrm_utils/files.hpp>
#include <spdlog/spdlog.h>
#include "tasks/nulltask.hpp"
#include "tasks/generic_task.hpp"
#include "tasks/test_task_2.hpp"
#include "tasks/test_task_1.hpp"
#include "tasks/idle_task.hpp"
#include "tasks/learner_test.hpp"
#include "tasks/test_task_3.hpp"
#include "tasks/move_to_cart_pose.hpp"
#include "tasks/move_to_joint_pose.hpp"
namespace mios{

TaskName TaskFactory::get_task_name(const std::string& task){
switch(msrm_utils::str_to_int(task.c_str())){
case msrm_utils::str_to_int("NullTask"):
return TaskNameNullTask;
case msrm_utils::str_to_int("GenericTask"):
return TaskNameGenericTask;
case msrm_utils::str_to_int("TestTask2"):
return TaskNameTestTask2;
case msrm_utils::str_to_int("TestTask1"):
return TaskNameTestTask1;
case msrm_utils::str_to_int("IdleTask"):
return TaskNameIdleTask;
case msrm_utils::str_to_int("LearnerTest"):
return TaskNameLearnerTest;
case msrm_utils::str_to_int("TestTask3"):
return TaskNameTestTask3;
case msrm_utils::str_to_int("MoveToCartPose"):
return TaskNameMoveToCartPose;
case msrm_utils::str_to_int("MoveToJointPose"):
return TaskNameMoveToJointPose;
default:
spdlog::error("Task with id " + task + " does not exist.");
return TaskNameNullTask;
}
}

std::shared_ptr<Task> TaskFactory::create_task(TaskName task, Core* core){
switch(task){
case TaskNameNullTask:
return std::make_shared<NullTask>(core);
case TaskNameGenericTask:
return std::make_shared<GenericTask>(core);
case TaskNameTestTask2:
return std::make_shared<TestTask2>(core);
case TaskNameTestTask1:
return std::make_shared<TestTask1>(core);
case TaskNameIdleTask:
return std::make_shared<IdleTask>(core);
case TaskNameLearnerTest:
return std::make_shared<LearnerTest>(core);
case TaskNameTestTask3:
return std::make_shared<TestTask3>(core);
case TaskNameMoveToCartPose:
return std::make_shared<MoveToCartPose>(core);
case TaskNameMoveToJointPose:
return std::make_shared<MoveToJointPose>(core);
default:
return std::make_shared<NullTask>(core);
}
}
}
