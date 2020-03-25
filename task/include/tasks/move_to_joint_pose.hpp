#pragma once

#include "task/task.hpp"

namespace mios {

class move_to_joint_pose : public Task{
public:
    move_to_joint_pose();
    void initialize_task();
    void execute_task();
    const EvalTask& evaluate_task();
    bool read_parameters(const nlohmann::json& params);
private:

    std::string pose;
    Eigen::Matrix<double,7,1> q_g;
    double speed;
    double acc;

};

}
