#include "strategies/move_to_pose.hpp"

namespace mios{

void MoveToPoseStrategy::initialize(const Percept &p_0){
    mogen_p2p::In_P_mogen_p2p mogen_p2p_in_p;
    mogen_p2p_in_p.dX_max=m_dX_max;
    mogen_p2p_in_p.ddX_max=m_ddX_max;
    mogen_p2p_in_p.TF_T_EE_0=p_0.proprioception.TF_T_EE;
    mogen_p2p_in_p.TF_T_EE_1=m_T_EE_d;
    m_mogen_p2p.initialize(m_mogen_p2p_in_u,mogen_p2p_in_p);
}

void MoveToPoseStrategy::get_next_command(Actuator &cmd, const Percept &p){
    m_mogen_p2p_in_u.t_scale=m_t_scale;
    m_mogen_p2p.step(m_mogen_p2p_in_u,m_mogen_p2p_out_y);
    cmd.TF_dX_d=m_mogen_p2p_out_y.dX_d;
}

void MoveToPoseStrategy::terminate(const Percept &p){
    m_mogen_p2p.terminate();
}

bool MoveToPoseStrategy::finished(){
    return m_mogen_p2p.get_out_l().arrived(0)==1;
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
