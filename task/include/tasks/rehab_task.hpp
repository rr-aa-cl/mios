#pragma once

#include "task/task.hpp"
namespace mios{
class rehab_task :
        public Task{
public:
    rehab_task();
    ~rehab_task();
    void initialize_task();
    void execute_task();
    const EvalTask& evaluate_task();
    bool read_parameters(const nlohmann::json& params);

private:
    std::string pose;
    Eigen::Matrix<double,7,1> q_g;

    double stiffness;
    double speed;
    std::string motion;
    std::shared_ptr<pattern_rehab> _rehabPattern;

};
}
