#pragma once

#include "task/task.hpp"

namespace mios {

class IdleTask : public Task{
public:
    IdleTask(Core* core);
    void initialize_context();
    void execute_task();
    void recover_task();
    void evaluate_task();
    bool read_parameters(const nlohmann::json &params);
private:
std::string idle_mode;

};

}
