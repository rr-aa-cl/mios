#include "strategy/move_to_joint_pose.hpp"

namespace mios{

void MoveToJointPoseStrategy::initialize(const Percept &p_0){
    mogen_p2p_joint::In_P_mogen_p2p_joint mogen_p2p_joint_in_p;
    mogen_p2p_joint_in_p.dq_max<<m_dq_max;
    mogen_p2p_joint_in_p.ddq_max<<m_ddq_max;
    mogen_p2p_joint_in_p.q_0=p_0.proprioception.q;
    mogen_p2p_joint_in_p.q_g=m_q_g;
    m_mogen_p2p_joint.initialize(m_mogen_p2p_joint_in_u,mogen_p2p_joint_in_p);
}

void MoveToJointPoseStrategy::get_next_command(Actuator &cmd, const Percept &p){
    m_mogen_p2p_joint.step(m_mogen_p2p_joint_in_u,m_mogen_p2p_joint_out_y);
    cmd.dq_d=m_mogen_p2p_joint_out_y.dq_d;
}

void MoveToJointPoseStrategy::terminate(const Percept &p){
    m_mogen_p2p_joint.terminate();
}

bool MoveToJointPoseStrategy::finished(){
    return m_mogen_p2p_joint.get_out_l().arrived(0)==1;
}

void MoveToJointPoseStrategy::set_goal(const Eigen::Matrix<double, 7, 1> &q_g, double dq_max, double ddq_max){
    m_q_g=q_g;
    m_dq_max=dq_max;
    m_ddq_max=ddq_max;
}

}
