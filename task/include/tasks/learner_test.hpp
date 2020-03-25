#pragma once

#include "task/task.hpp"
namespace mios{
class learner_test : public Task{
public:
learner_test();
~learner_test();
void initialize_task();
void execute_task();
const EvalTask& evaluate_task();
bool read_parameters(const nlohmann::json& params);
private:
Eigen::Matrix<double,6,1> x;
};
}