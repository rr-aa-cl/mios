#pragma once

#include "task/task.hpp"
namespace mios{
class observe : public Task{
public:
observe();
~observe();
void initialize_task();
void execute_task();
const EvalTask& evaluate_task();
bool read_parameters(const nlohmann::json& params);
private:
std::vector<std::string> watch_poses;
};
}
