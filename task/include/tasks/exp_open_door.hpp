#pragma once

#include "task/task.hpp"

#include "tasks/handover_object.hpp"
#include "tasks/move_to_joint_pose.hpp"
#include "tasks/insert_object.hpp"

namespace mios {

class exp_open_door : public Task{
public:
    exp_open_door();
    ~exp_open_door();
    void initialize_task();
    void execute_task();
    const EvalTask& evaluate_task();
    bool read_parameters(const nlohmann::json& params);
private:

    std::string key;
    std::string lock;

};

}
