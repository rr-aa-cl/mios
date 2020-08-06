#pragma once

#include "task/task.hpp"

namespace mios {

class NullTask : public Task{
public:
    NullTask(Core* core);

    void initialize_context() override;
    void execute() override;
    void evaluate() override;
};

}
