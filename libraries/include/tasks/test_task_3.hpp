#pragma once

#include "task/task.hpp"
namespace mios{
class TestTask3 : public Task{
public:
    TestTask3(Core* core);
    void initialize_context();
    void execute();
    void recover_task();
    void write_custom_results(nlohmann::json &custom_results) override;
    bool read_parameters(const nlohmann::json& params);
    void get_default_context(nlohmann::json &context) override;

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
