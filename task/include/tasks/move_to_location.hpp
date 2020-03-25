#pragma once

#include <vector>

#include "task/task.hpp"
namespace mios{
class move_to_location : public Task{
public:
move_to_location();
~move_to_location();
void initialize_task();
void execute_task();
const EvalTask& evaluate_task();
bool read_parameters(const nlohmann::json& params);
private:
std::string loc_goal;
std::vector<std::string> loc_intermediate;
std::vector<int> loc_cart;
};
}
