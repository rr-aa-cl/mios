#pragma once

#include "task/task.hpp"
namespace mios{
class move_until_contact : public Task{
public:
move_until_contact();
~move_until_contact();
void initialize_task();
void execute_task();
const EvalTask& evaluate_task();
bool read_parameters(const nlohmann::json &params);
private:
std::string surface;
double speed;
};
}
