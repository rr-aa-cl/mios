#pragma once

#include "task/task.hpp"
namespace mios{
class test_task_2 : public Task{
public:
test_task_2();
~test_task_2();
void initialize_task();
void execute_task();
void recover_task();
const EvalTask& evaluate_task();
bool read_parameters(const nlohmann::json& params);
private:
Eigen::Matrix<double,2,1> d;
bool e;
double f;
unsigned stop_level;
bool success;
};
}
