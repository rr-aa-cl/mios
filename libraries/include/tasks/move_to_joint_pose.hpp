#pragma once

#include "task/task.hpp"

namespace mios {

class MoveToJointPose : public Task{
public:
    MoveToJointPose(Core* core);

    void initialize_context() override;
    void execute() override;
    bool read_parameters(const nlohmann::json &params) override;
    void evaluate() override;

private:
    std::optional<std::string> m_pose;
    Eigen::Matrix<double,7,1> m_q_g;
    double m_speed;
    double m_acc;
};

}
