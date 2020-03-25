#pragma once

#include "task/task.hpp"

#include "tasks/move_to_cart_pose.hpp"

namespace mios{
class push_button : public Task{
public:
push_button();
~push_button();
void initialize_task();
void execute_task();
const EvalTask& evaluate_task();
bool read_parameters(const nlohmann::json& params);
private:
bool contact;
std::string button;
};
}
