#pragma once

#include "task/task.hpp"
namespace mios{
class manipulation_test : public Task{
public:
manipulation_test();
~manipulation_test();
void initialize_task();
void execute_task();
const EvalTask& evaluate_task();
};
}
