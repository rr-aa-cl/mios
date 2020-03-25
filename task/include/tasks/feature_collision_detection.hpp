#pragma once

#include "task/task.hpp"

namespace mios {

class feature_collision_detection : public Task{
public:
    feature_collision_detection();
    void initialize_task();
    void execute_task();
    const EvalTask& evaluate_task();
    bool read_parameters(const nlohmann::json& params);
private:

    std::string pose_init;

};

}
