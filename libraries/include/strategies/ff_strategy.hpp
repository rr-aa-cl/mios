#pragma once

#include "strategy/primitive_strategy.hpp"

namespace mios {

class FFStrategy : public PrimitiveStrategy{
public:
    FFStrategy();
    void initialize(const Percept &p_0) override;
    void get_next_command(Actuator &cmd, const Percept &p) override;
    void terminate(const Percept &p) override;
    bool finished() override;

    void set_TF_F_ff(const Eigen::Matrix<double,6,1>& TF_F_ff, Eigen::Matrix<double,2,1> dF_max);
    void set_frame(bool EE);

private:
    Eigen::Matrix<double,2,1> m_dF_max;
    Eigen::Matrix<double,6,1> m_TF_F_ff;
    Eigen::Matrix<double,6,1> m_TF_F_ff_limiter;
    bool m_EE;
};

}

