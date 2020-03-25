#pragma once

#include "task/task.hpp"

namespace mios {

class feature_impedance : public Task{
public:
    feature_impedance();
    void initialize_task();
    void execute_task();
    const EvalTask& evaluate_task();
    bool read_parameters(const nlohmann::json& params);
private:

    std::string pose_init;
    Eigen::Matrix<double,6,1> K;

};

}
