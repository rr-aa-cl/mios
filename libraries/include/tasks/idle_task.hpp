#pragma once

#include "task/task.hpp"

namespace mios {

class IdleTask : public Task{
public:
    IdleTask(Core* core);
    void initialize_context();
    void execute();
    void recover_task();
    bool read_parameters(const nlohmann::json &params);
    void get_default_context(nlohmann::json &context) override;

private:
std::string idle_mode;

};

}
