#pragma once

#include "task/task.hpp"
namespace mios{
class TestTask2 : public Task{
public:
TestTask2(Core* core);
void initialize_context();
void execute();
void recover_task();
void evaluate();
bool read_parameters(const nlohmann::json& params);
private:
Eigen::Matrix<double,2,1> m_d;
bool m_e;
double m_f;
unsigned m_stop_level;
bool m_success;
};
}
