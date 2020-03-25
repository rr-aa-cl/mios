#pragma once

#include "task/task.hpp"

#include "tasks/handover_object.hpp"

namespace mios {

class polish_object : public Task{
public:
    polish_object();
    ~polish_object();
    void initialize_task();
    void execute_task();
    const EvalTask& evaluate_task();
    bool read_parameters(const nlohmann::json& params);
private:

    std::string object;

};

}
