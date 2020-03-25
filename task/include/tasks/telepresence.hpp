#pragma once

#include <algorithm>
#include <array>
#include <cmath>

#include <franka/exception.h>
#include <franka/robot.h>

#include "task/task.hpp"
#include "tasks/move_to_joint_pose.hpp"
#include "tasks/move_to_cart_pose.hpp"

#include "cpp_utils/network.hpp"

namespace mios {

class telepresence : public Task{
public:
    telepresence();
    void initialize_task();
    void execute_task();
    const EvalTask& evaluate_task();
    bool read_parameters(const nlohmann::json& params);
private:
    bool _master;
    bool _repeater;
    bool _bilateral;
    TelepresenceMode _mode;

    std::string _alias_peer;
    Eigen::Matrix<double,7,1> _q_0;
    Eigen::Matrix<double,4,4> _TF_T_EE_0;


};


}
