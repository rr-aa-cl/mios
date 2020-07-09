#pragma once

#include "strategy/primitive_strategy.hpp"

namespace mios {

class JointComplianceStrategy : public PrimitiveStrategy{
public:
    JointComplianceStrategy();
    void initialize(const Percept &p_0) override;
    void get_next_command(Actuator &cmd, const Percept &p) override;
    void terminate(const Percept &p) override;
    bool finished() override;

    void set_complicance(const Eigen::Matrix<double,7,1>& K_theta, const Eigen::Matrix<double,7,1>& xi_theta);

private:
    Eigen::Matrix<double,7,1> m_K_theta;
    Eigen::Matrix<double,7,1> m_xi_theta;
};

}

