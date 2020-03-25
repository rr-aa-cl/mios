#pragma once

#include "task/task.hpp"
namespace mios{
class react_to_event : public Task{
public:
react_to_event();
void initialize_task();
void execute_task();
const EvalTask& evaluate_task();
bool read_parameters(const nlohmann::json& params);
private:
std::string event;
};
}
