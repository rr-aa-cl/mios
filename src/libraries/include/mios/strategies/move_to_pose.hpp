#pragma once

#include "mios/strategy/primitive_strategy.hpp"
#include "mogen_p2p_wrapper.hpp"
#include "eigen3/Eigen/Core"

namespace mios {

class MoveToPoseStrategy : public PrimitiveStrategy{
public:
    MoveToPoseStrategy();
    void initialize(const Percept &p_0) override;
    void get_next_command(Actuator &cmd, const Percept &p) override;
    void terminate(const Percept &p) override;
    bool finished() override;

public:
    void set_goal(const Eigen::Matrix<double,4,4>& T_EE_d, const Eigen::Matrix<double,2,1>& dX_max, const Eigen::Matrix<double,2,1>& ddX_max);
    void set_scale(Eigen::Matrix<double,2,1> t_scale);

private:
    Eigen::Matrix<double,4,4> m_T_EE_d;
    Eigen::Matrix<double,2,1> m_dX_max;
    Eigen::Matrix<double,2,1> m_ddX_max;
    Eigen::Matrix<double,2,1> m_t_scale;

    mogen_p2p::mogen_p2p m_mogen_p2p;

};

}
