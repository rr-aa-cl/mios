#pragma once

#include "task/task.hpp"
#include "tasks/handover_object.hpp"

namespace mios {

class feature_force_control : public Task{
public:
    feature_force_control();
    void initialize_task();
    void execute_task();
    const EvalTask& evaluate_task();
    bool read_parameters(const nlohmann::json& params);
    void recover_task();
private:

    std::string pose_init;
    Eigen::Matrix<double,7,1> q_g;

};

}
