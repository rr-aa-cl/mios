#pragma once

#include "task/task.hpp"

namespace mios {

class insert_object : public Task{
public:
    insert_object();
    ~insert_object();
    void initialize_task();
    void execute_task();
    void recover_task();
    const EvalTask& evaluate_task();
    bool read_parameters(const nlohmann::json& params);
private:

    std::string _object;
    std::string _hole;
    bool _joint;
    bool _release;
    bool _emotions;
    bool _extract;

};

}
