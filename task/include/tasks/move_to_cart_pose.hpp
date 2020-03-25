#pragma once

#include "task/task.hpp"
namespace mios{
class move_to_cart_pose : public Task{
public:
move_to_cart_pose();
void initialize_task();
void execute_task();
const EvalTask& evaluate_task();
bool read_parameters(const nlohmann::json& params);
private:
std::string pose;
Eigen::Matrix<double,4,4> TF_T_EE_g;
double speed;
double acc;
};
}
