#pragma once

#include "task/task.hpp"
namespace mios{
class guiding_task : public Task{
public:
guiding_task();
~guiding_task();
void initialize_task();
void execute_task();
const EvalTask& evaluate_task();
};
}
