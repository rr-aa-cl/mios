#pragma once

#include "task/task.hpp"
namespace mios{
class locate_object : public Task{
public:
locate_object();
~locate_object();
void initialize_task();
void execute_task();
const EvalTask& evaluate_task();
bool read_parameters(const nlohmann::json& params);
private:
std::string object;
std::string pose_failsafe;
std::vector<std::string> search_poses;

};
}
