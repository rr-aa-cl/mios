#pragma once

#include "task/task.hpp"

namespace mios {

class handover_object : public Task{
public:
    handover_object();
    ~handover_object();
    void initialize_task();
    void execute_task();
    const EvalTask& evaluate_task();
    bool read_parameters(const nlohmann::json& params);
private:

    std::string _object;
    bool wait_for_relax;

};

}
