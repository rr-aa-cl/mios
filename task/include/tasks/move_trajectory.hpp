#pragma once

#include "task/task.hpp"
namespace mios{
class move_trajectory : public Task{
public:
move_trajectory();
~move_trajectory();
void initialize_task();
void execute_task();
const EvalTask& evaluate_task();
bool read_parameters(const nlohmann::json& params);
private:
std::vector<std::string> locations;
Eigen::Matrix<double,2,1> speed;
Eigen::Matrix<double,2,1> acc;
bool flag_cart;
};
}
