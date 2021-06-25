#pragma once

#include "mios/strategy/primitive_strategy.hpp"
#include "mogen_p2p_joint_wrapper.hpp"
#include <eigen3/Eigen/Core>

namespace mios {

class MoveToJointPoseStrategy : public PrimitiveStrategy{
public:
    MoveToJointPoseStrategy();
    void initialize(const Percept &p_0) override;
    void get_next_command(Actuator &cmd, const Percept &p) override;
    void terminate(const Percept &p) override;
    bool finished() override;

public:
    void set_goal(const Eigen::Matrix<double,7,1>& q_g, double dq_max, double ddq_max);

private:
    Eigen::Matrix<double,7,1> m_q_g;
    double m_dq_max;
    double m_ddq_max;

    mogen_p2p_joint::mogen_p2p_joint m_mogen_p2p_joint;

};

}
