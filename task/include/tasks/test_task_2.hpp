#pragma once

#include "task/task.hpp"
namespace mios{
class TestTask2 : public Task{
public:
TestTask2(Core* core);
void initialize_context();
void execute_task();
void recover_task();
void evaluate_task();
bool read_parameters(const nlohmann::json& params);
private:
Eigen::Matrix<double,2,1> d;
bool e;
double f;
unsigned stop_level;
bool success;
};
}
