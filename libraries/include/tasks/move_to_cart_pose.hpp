#pragma once

#include "task/task.hpp"

namespace mios {

class MoveToCartPose : public Task{
public:
    MoveToCartPose(Core* core);

    void initialize_context() override;
    void execute() override;
    bool read_parameters(const nlohmann::json &params) override;
    void evaluate() override;

private:
    std::optional<std::string> m_pose;
    Eigen::Matrix<double,4,4> m_T_EE_g;
    Eigen::Matrix<double,2,1> m_speed;
    Eigen::Matrix<double,2,1> m_acc;
};

}
