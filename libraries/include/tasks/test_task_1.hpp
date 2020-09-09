#pragma once

#include "task/task.hpp"
namespace mios{
class TestTask1 : public Task{
public:
    TestTask1(Core *core);
    void initialize_context();
    void execute();
    void recover_task();
    void write_custom_results(nlohmann::json &custom_results) override;
    bool read_parameters(const nlohmann::json& params);

private:
    void get_default_context(nlohmann::json &context) override;

private:
    bool recovered;
    Eigen::Matrix<double,3,1> m_a;
    bool m_b;
    bool m_success;
    std::string m_exception;
    unsigned m_skill_test;
    int m_queue_number;
    int m_result_code;
    std::vector<int> m_mp_sequence;
};
}
