#pragma once

#include "task/task.hpp"
namespace mios{
class TestTask3 : public Task{
public:
TestTask3(Core* core);
void initialize_context();
void execute_task();
void recover_task();
void evaluate_task();
bool read_parameters(const nlohmann::json& params);
private:
Eigen::Matrix<double,4,1> m_g;
bool m_h;
double m_i;
std::string m_j;
double m_stop_level;
bool m_success;
bool recovered;
};
}
