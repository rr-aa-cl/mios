#pragma once

#include "strategy/primitive_strategy.hpp"

namespace mios {

class TwistWiggleStrategy : public PrimitiveStrategy{
public:
    TwistWiggleStrategy();
    void initialize(const Percept &p_0) override;
    void get_next_command(Actuator &cmd, const Percept &p) override;
    void terminate(const Percept &p) override;
    bool finished() override;

    void set_coefficients(Eigen::Matrix<double,6,1> a_a, Eigen::Matrix<double,6,1> b_a, Eigen::Matrix<double,6,1> a_f, Eigen::Matrix<double,6,1> b_f, Eigen::Matrix<double,6,1> a_phi, Eigen::Matrix<double,6,1> b_phi);

private:
    Eigen::Matrix<double,6,1> m_a_a;
    Eigen::Matrix<double,6,1> m_b_a;
    Eigen::Matrix<double,6,1> m_a_f;
    Eigen::Matrix<double,6,1> m_b_f;
    Eigen::Matrix<double,6,1> m_a_phi;
    Eigen::Matrix<double,6,1> m_b_phi;

    Eigen::Matrix<double,6,1> m_X_d_old;
    Eigen::Matrix<double,6,1> m_X_d;
};

}

