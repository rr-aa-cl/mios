#pragma once

#include "mios/strategy/primitive_strategy.hpp"
namespace mios{

class DesiredWrenchStrategy : public PrimitiveStrategy{
public:
    DesiredWrenchStrategy();
    void initialize(const Percept& p_0) override;
    void get_next_command(Actuator& cmd, const Percept& p) override;
    void terminate(const Percept& p) override;
    bool finished() override;

    void set_TF_F_d(const Eigen::Matrix<double,6,1>& TF_F_d, Eigen::Matrix<double,2,1> dF_max);

private:
    Eigen::Matrix<double,2,1> m_dF_max;
    Eigen::Matrix<double,6,1> m_TF_F_d;
    Eigen::Matrix<double,6,1> m_TF_F_d_limiter;

};
}
