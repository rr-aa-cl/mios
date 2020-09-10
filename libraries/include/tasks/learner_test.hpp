#pragma once

#include "task/task.hpp"
namespace mios{
class LearnerTest : public Task{
public:
    LearnerTest(Core* core);
    void initialize_context() override;
    void execute() override;
    bool read_parameters(const nlohmann::json& params) override;
    void get_default_context(nlohmann::json &context) override;

private:
    Eigen::Matrix<double,6,1> m_x;
};
}
