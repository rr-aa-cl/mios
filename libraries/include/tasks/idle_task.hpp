#pragma once

#include "task/task.hpp"

namespace mios {

class IdleTask : public Task{
public:
    IdleTask(Core* core);
    void initialize_context();
    void execute();
    void recover_task();
    void evaluate();
    bool read_parameters(const nlohmann::json &params);
private:
std::string idle_mode;

};

}
