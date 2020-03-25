#pragma once

#include "task/task.hpp"
namespace mios{
class test_task_3 : public Task{
public:
test_task_3();
~test_task_3();
void initialize_task();
void execute_task();
void recover_task();
const EvalTask& evaluate_task();
bool read_parameters(const nlohmann::json& params);
private:
Eigen::Matrix<double,4,1> g;
bool h;
double i;
std::string j;
double stop_level;
bool success;
};
}
