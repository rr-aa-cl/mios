#include "mios/strategies/move_to_pose.hpp"
#include <iostream>

namespace mios{

MoveToPoseStrategy::MoveToPoseStrategy():PrimitiveStrategy({CommandPatternCartesianTwist}){

}

void MoveToPoseStrategy::initialize(const Percept &p_0){
    m_mogen_p2p.p.dX_max=m_dX_max;
    m_mogen_p2p.p.ddX_max=m_ddX_max;
    m_mogen_p2p.p.TF_T_EE_0=p_0.proprioception.T_T_EE;
    m_mogen_p2p.p.TF_T_EE_1=m_T_EE_d;
    m_t_scale<<1,1;
    m_mogen_p2p.initialize();
}

void MoveToPoseStrategy::get_next_command(Actuator &cmd, [[maybe_unused]] const Percept &p){
    m_mogen_p2p.u.t_scale=m_t_scale;
    m_mogen_p2p.step();
    cmd.TF_dX_d=m_mogen_p2p.y.dX_d;
}

void MoveToPoseStrategy::terminate([[maybe_unused]] const Percept &p){
    m_mogen_p2p.terminate();
}

bool MoveToPoseStrategy::finished(){
    return m_mogen_p2p.l.arrived(0)==1;
}

void MoveToPoseStrategy::set_goal(const Eigen::Matrix<double, 4, 4> &T_EE_d, const Eigen::Matrix<double, 2, 1> &dX_max, const Eigen::Matrix<double, 2, 1> &ddX_max){
    m_T_EE_d=T_EE_d;
    m_dX_max=dX_max;
    m_ddX_max=ddX_max;
}

void MoveToPoseStrategy::set_scale(Eigen::Matrix<double, 2, 1> t_scale){
    m_t_scale=t_scale;
}

}
