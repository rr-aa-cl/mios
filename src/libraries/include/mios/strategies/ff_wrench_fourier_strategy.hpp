#pragma once

#include "mios/strategy/primitive_strategy.hpp"

namespace mios {

class FFWrenchFourierStrategy : public PrimitiveStrategy{
public:
    FFWrenchFourierStrategy();
    void initialize(const Percept &p_0) override;
    void get_next_command(Actuator &cmd, const Percept &p) override;
    void terminate(const Percept &p) override;
    bool finished() override;

    void set_params(const Eigen::Matrix<double,6,1>& a0, const Eigen::Matrix<double,6,1>& a1, const Eigen::Matrix<double,6,1>& a2,
                    const Eigen::Matrix<double,6,1>& b1, const Eigen::Matrix<double,6,1>& b2, const Eigen::Matrix<double,6,1>& f, Eigen::Matrix<double,2,1> dF_max);

private:
    Eigen::Matrix<double,6,1> m_a0;
    Eigen::Matrix<double,6,1> m_f;
    Eigen::Matrix<double,6,1> m_a1;
    Eigen::Matrix<double,6,1> m_a2;
    Eigen::Matrix<double,6,1> m_b1;
    Eigen::Matrix<double,6,1> m_b2;
};

}

