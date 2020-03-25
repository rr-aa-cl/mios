#pragma once

#include "task/task.hpp"
namespace mios{
class gesture : public Task{
public:
gesture();
~gesture();
void initialize_task();
void execute_task();
const EvalTask& evaluate_task();
bool read_parameters(const nlohmann::json& params);
private:
int direction;
double F_thr;
};
}
