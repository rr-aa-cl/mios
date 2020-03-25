#pragma once

#include "task/task.hpp"
namespace mios{
class open_lock : public Task{
public:
open_lock();
~open_lock();
void initialize_task();
void execute_task();
const EvalTask& evaluate_task();
bool read_parameters(const nlohmann::json& params);
private:
bool reverse;
bool release;
double angle;

std::string lock;
std::string key;
};
}
