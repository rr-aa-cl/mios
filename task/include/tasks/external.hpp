#pragma once

#include "task/task.hpp"
namespace mios{
class external : public Task{
public:
external();
void initialize_task();
void execute_task();
const EvalTask& evaluate_task();
bool read_parameters(const nlohmann::json& params);
private:
std::string mode;
};
}
