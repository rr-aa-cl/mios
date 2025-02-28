#include "mios/strategies/move_in_nullspace.hpp"
#include <iostream>

namespace mios{

MoveInNullspaceStrategy::MoveInNullspaceStrategy():PrimitiveStrategy({CommandPatternJointVelocities}){

}

void MoveInNullspaceStrategy::initialize(const Percept &p_0){
    m_mogen_p2p_joint.p.dq_max<<m_dq_max;
    m_mogen_p2p_joint.p.ddq_max<<m_ddq_max;
    m_mogen_p2p_joint.p.q_0=p_0.controller.q_d;
    m_mogen_p2p_joint.p.q_g=m_q_g;
    m_mogen_p2p_joint.initialize();
}

void MoveInNullspaceStrategy::get_next_command(Actuator &cmd, [[maybe_unused]] const Percept &p){
    m_mogen_p2p_joint.step();
    cmd.q_d_nullspace=m_mogen_p2p_joint.y.dq_d;
}

void MoveInNullspaceStrategy::terminate([[maybe_unused]] const Percept &p){
    m_mogen_p2p_joint.terminate();
}

bool MoveInNullspaceStrategy::finished(){
    return m_mogen_p2p_joint.l.arrived(0)==1;
}

void MoveInNullspaceStrategy::set_goal(const Eigen::Matrix<double, 7, 1> &q_g, double dq_max, double ddq_max){
    m_q_g=q_g;
    m_dq_max=dq_max;
    m_ddq_max=ddq_max;
}

}
