#pragma once

#include "strategy/primitive_strategy.hpp"

namespace mios {

class TwistStrategy : public PrimitiveStrategy{
public:
    TwistStrategy();
    void initialize(const Percept &p_0) override;
    void get_next_command(Actuator &cmd, const Percept &p) override;
    void terminate(const Percept &p) override;
    bool finished() override;

    void set_TF_dX_d(const Eigen::Matrix<double,6,1>& TF_dX_d);

private:
    Eigen::Matrix<double,6,1> m_TF_dX_d;
};

}

