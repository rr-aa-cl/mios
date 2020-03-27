#pragma once

#include "task/task.hpp"
#include "tasks/idle_task.hpp"
#include "tasks/test_task_1.hpp"
#include "tasks/test_task_2.hpp"
#include "tasks/test_task_3.hpp"
#include "tasks/learner_test.hpp"
#include "tasks/external.hpp"
#include "tasks/move_to_joint_pose.hpp"
#include "tasks/move_to_cart_pose.hpp"
#include "tasks/insert_object.hpp"
#include "tasks/extract_object.hpp"
#include "tasks/react_to_event.hpp"
#include "tasks/feature_impedance.hpp"
#include "tasks/feature_collision_detection.hpp"
#include "tasks/feature_force_control.hpp"
#include "tasks/telepresence.hpp"
#include "tasks/place_object.hpp"
#include "tasks/move_trajectory.hpp"
#include "tasks/move_to_location.hpp"
#include "tasks/fetch_object.hpp"
#include "tasks/guiding_mode.hpp"
namespace mios{
struct TaskList{
TaskList();
std::map<std::string,std::shared_ptr<Task> > tasks;
};
}
