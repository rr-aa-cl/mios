#pragma once

#include "task/task.hpp"

namespace mios {

class NullTask : public Task{
public:
    NullTask(Core* core);

    void initialize_context() override;
    void execute_task() override;
    void evaluate_task() override;
};

}
