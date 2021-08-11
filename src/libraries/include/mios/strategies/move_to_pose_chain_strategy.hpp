#pragma once

#include "mios/strategy/primitive_strategy.hpp"
#include "Eigen/Core"

namespace mios {

class MoveToPoseChainStrategy : public PrimitiveStrategy{
public:
    MoveToPoseChainStrategy();
    void initialize(const Percept &p_0) override;
    void get_next_command(Actuator &cmd, const Percept &p) override;
    void terminate(const Percept &p) override;
    bool finished() override;

public:
    void set_goal(const std::vector<Eigen::Matrix<double,4,4> >& T_EE_d_chain, const Eigen::Matrix<double,2,1>& dX_d, const Eigen::Matrix<double,2,1>& ddX_d);

private:
    std::vector<Eigen::Matrix<double,4,4> > m_T_EE_d_chain;
    Eigen::Matrix<double,2,1> m_dX_d;
    Eigen::Matrix<double,2,1> m_ddX_d;

    unsigned m_cnt;
    double m_path_pos;
    double m_path_length;

    Eigen::Matrix<double,6,1> m_TF_dX_d;
    Eigen::Matrix<double,6,1> m_TF_dX_d_limiter;

};

}
