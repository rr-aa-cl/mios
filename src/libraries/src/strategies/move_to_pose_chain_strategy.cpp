#include "mios/strategies/move_to_pose_chain_strategy.hpp"
#include <iostream>
#include "msrm_cpp_utils/math/math.hpp"

namespace mios{

MoveToPoseChainStrategy::MoveToPoseChainStrategy():PrimitiveStrategy({CommandPatternCartesianTwist}){
    m_cnt=0;
    m_path_pos=0;
    m_path_length=0;
    m_TF_dX_d.setZero();
    m_TF_dX_d_limiter.setZero();
    m_dX_d.setZero();
    m_ddX_d.setZero();
}

void MoveToPoseChainStrategy::initialize(const Percept &p_0){
    m_cnt=0;
    m_path_pos=0;
    m_path_length=0;
}

void MoveToPoseChainStrategy::get_next_command(Actuator &cmd, [[maybe_unused]] const Percept &p){
    Eigen::Matrix<double,3,1> dir=m_T_EE_d_chain[m_cnt+1].block<3,1>(0,3)-m_T_EE_d_chain[m_cnt].block<3,1>(0,3);
    m_path_length=dir.norm();
    m_path_pos+=(dir/dir.norm()*m_dX_d(0)).norm()*0.001;
    if(m_path_pos>=m_path_length && m_cnt<m_T_EE_d_chain.size()-2){
        m_cnt++;
        m_path_pos=0;
    }
    m_TF_dX_d<<dir/dir.norm()*m_dX_d(0),0,0,0;
    for(unsigned i=0;i<3;i++){
        double diff_TF_dX_d_t = m_TF_dX_d(i)-m_TF_dX_d_limiter(i);
        double diff_TF_dX_d_r = m_TF_dX_d(i+3)-m_TF_dX_d_limiter(i+3);
        if(fabs(diff_TF_dX_d_t)/0.001>m_ddX_d(0)){
            cmd.TF_dX_d(i)=m_TF_dX_d_limiter(i)+msrm_utils::sgn(diff_TF_dX_d_t)*m_ddX_d(0)*0.001;
        }
        if(fabs(diff_TF_dX_d_r)/0.001>m_ddX_d(1)){
            cmd.TF_dX_d(i+3)=m_TF_dX_d_limiter(i+3)+msrm_utils::sgn(diff_TF_dX_d_r)*m_ddX_d(1)*0.001;
        }
    }
    m_TF_dX_d_limiter=cmd.TF_dX_d;
}

void MoveToPoseChainStrategy::terminate([[maybe_unused]] const Percept &p){
}

bool MoveToPoseChainStrategy::finished(){
    if(m_path_pos>=m_path_length && m_cnt>=m_T_EE_d_chain.size()-2){
        return true;
    }
    return false;
}

void MoveToPoseChainStrategy::set_goal(const std::vector<Eigen::Matrix<double,4,4> >& T_EE_d_chain, const Eigen::Matrix<double,2,1>& dX_d, const Eigen::Matrix<double,2,1>& ddX_d){
    m_T_EE_d_chain=T_EE_d_chain;
    m_dX_d=dX_d;
    m_ddX_d=ddX_d;
}

}
