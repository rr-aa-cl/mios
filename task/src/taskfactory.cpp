#include "task/taskfactory.hpp"
#include "task/task.hpp"
#include "tasks/idle_task.hpp"
#include "tasks/test_task_1.hpp"
#include "tasks/test_task_2.hpp"
#include "tasks/test_task_3.hpp"
#include "tasks/nulltask.hpp"
//#include "tasks/learner_test.hpp"
//#include "tasks/external.hpp"
//#include "tasks/move_to_joint_pose.hpp"
//#include "tasks/move_to_cart_pose.hpp"
//#include "tasks/insert_object.hpp"
//#include "tasks/extract_object.hpp"
//#include "tasks/react_to_event.hpp"
//#include "tasks/feature_impedance.hpp"
//#include "tasks/feature_collision_detection.hpp"
//#include "tasks/feature_force_control.hpp"
//#include "tasks/telepresence.hpp"
//#include "tasks/place_object.hpp"
//#include "tasks/move_trajectory.hpp"
//#include "tasks/move_to_location.hpp"
//#include "tasks/fetch_object.hpp"
//#include "tasks/guiding_mode.hpp"
//#include "tasks/handover_object.hpp"

#include <msrm_utils/files.hpp>
#include <spdlog/spdlog.h>

namespace mios{

TaskName TaskFactory::get_task_name(const std::string &task){
    switch(msrm_utils::str_to_int(task.c_str())){
    case msrm_utils::str_to_int("IdleTask"):
        return TaskName::TaskName_IdleTask;
    case msrm_utils::str_to_int("TestTask1"):
        return TaskName::TaskName_TestTask1;
    case msrm_utils::str_to_int("TestTask2"):
        return TaskName::TaskName_TestTask2;
    case msrm_utils::str_to_int("TestTask3"):
        return TaskName::TaskName_TestTask3;
    default:
        spdlog::error("Task with id " + task + " does not exist.");
        return TaskName::TaskName_NullTask;
    }
}

std::shared_ptr<Task> TaskFactory::create_task(TaskName task,Core* core){
    switch(task){
    case TaskName::TaskName_IdleTask:
        return std::make_shared<IdleTask>(core);
    case TaskName::TaskName_TestTask1:
        return std::make_shared<TestTask1>(core);
    case TaskName::TaskName_TestTask2:
        return std::make_shared<TestTask2>(core);
    case TaskName::TaskName_TestTask3:
        return std::make_shared<TestTask3>(core);
    default:
        return std::make_shared<NullTask>(core);

    }
}



}
