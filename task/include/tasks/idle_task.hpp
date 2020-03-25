#pragma once

#include "task/task.hpp"

namespace mios {

class idle_task : public Task{
public:
    idle_task();
    ~idle_task();
    void initialize_task();
    void execute_task();
    void recover_task();
    const EvalTask& evaluate_task();
    bool read_parameters(const nlohmann::json &params);
private:
std::string idle_mode;

};

}
