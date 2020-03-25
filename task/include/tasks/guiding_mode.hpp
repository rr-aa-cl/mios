#pragma once

#include "task/task.hpp"
namespace mios{
class guiding_mode : public Task{
public:
guiding_mode();
~guiding_mode();
void initialize_task();
void execute_task();
const EvalTask& evaluate_task();
bool read_parameters(const nlohmann::json& params);
private:
Eigen::Matrix<double,6,1> mode;
Eigen::Matrix<double,6,1> walls;
};
}
