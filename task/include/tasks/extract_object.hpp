#pragma once

#include "task/task.hpp"

namespace mios {

class extract_object : public Task{
public:
    extract_object();
    void initialize_task();
    void execute_task();
    void recover_task();
    const EvalTask& evaluate_task();
    bool read_parameters(const nlohmann::json& params);
private:
    std::string _object;
    std::string _hole;
    bool _joint;
};

}
