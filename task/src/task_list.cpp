#include "task/task_list.hpp"
namespace mios{
TaskList::TaskList(){
this->tasks.insert(std::pair<std::string,std::shared_ptr<Task> >("idle_task",std::make_shared<idle_task>()));
this->tasks.insert(std::pair<std::string,std::shared_ptr<Task> >("test_task_1",std::make_shared<test_task_1>()));
this->tasks.insert(std::pair<std::string,std::shared_ptr<Task> >("test_task_2",std::make_shared<test_task_2>()));
this->tasks.insert(std::pair<std::string,std::shared_ptr<Task> >("test_task_3",std::make_shared<test_task_3>()));
this->tasks.insert(std::pair<std::string,std::shared_ptr<Task> >("learner_test",std::make_shared<learner_test>()));
this->tasks.insert(std::pair<std::string,std::shared_ptr<Task> >("external",std::make_shared<external>()));
this->tasks.insert(std::pair<std::string,std::shared_ptr<Task> >("move_to_joint_pose",std::make_shared<move_to_joint_pose>()));
this->tasks.insert(std::pair<std::string,std::shared_ptr<Task> >("move_to_cart_pose",std::make_shared<move_to_cart_pose>()));
this->tasks.insert(std::pair<std::string,std::shared_ptr<Task> >("insert_object",std::make_shared<insert_object>()));
this->tasks.insert(std::pair<std::string,std::shared_ptr<Task> >("extract_object",std::make_shared<extract_object>()));
this->tasks.insert(std::pair<std::string,std::shared_ptr<Task> >("react_to_event",std::make_shared<react_to_event>()));
this->tasks.insert(std::pair<std::string,std::shared_ptr<Task> >("feature_impedance",std::make_shared<feature_impedance>()));
this->tasks.insert(std::pair<std::string,std::shared_ptr<Task> >("feature_collision_detection",std::make_shared<feature_collision_detection>()));
this->tasks.insert(std::pair<std::string,std::shared_ptr<Task> >("feature_force_control",std::make_shared<feature_force_control>()));
this->tasks.insert(std::pair<std::string,std::shared_ptr<Task> >("telepresence",std::make_shared<telepresence>()));
}
}
