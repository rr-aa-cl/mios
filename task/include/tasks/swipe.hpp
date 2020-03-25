#pragma once

#include "task/task.hpp"

#include "tasks/move_to_cart_pose.hpp"

namespace mios{
class swipe : public Task{
public:
swipe();
~swipe();
void initialize_task();
void execute_task();
const EvalTask& evaluate_task();
bool read_parameters(const nlohmann::json& params);
private:
std::vector<std::string> locations;
};
}
