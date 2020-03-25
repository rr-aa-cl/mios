#pragma once

#include "task/task.hpp"
namespace mios{
class test_task_1 : public Task{
public:
test_task_1();
~test_task_1();
void initialize_task();
void execute_task();
void recover_task();
const EvalTask& evaluate_task();
bool read_parameters(const nlohmann::json& params);
private:
Eigen::Matrix<double,3,1> a;
bool b;
bool success;
std::string exception;
unsigned skill_test;
};
}
