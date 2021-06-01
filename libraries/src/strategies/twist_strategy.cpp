#include "strategies/twist_strategy.hpp"
#include "msrm_cpp_utils/math.hpp"

namespace mios {

TwistStrategy::TwistStrategy():PrimitiveStrategy({CommandPatternCartesianTwist}){
    m_TF_dX_d.setZero();
    m_TF_dX_d_limiter.setZero();
    m_ddX_max.setZero();
}

void TwistStrategy::initialize(const Percept &p_0){
}

void TwistStrategy::get_next_command(Actuator &cmd, const Percept &p){
    for(unsigned i=0;i<3;i++){
        double diff_TF_dX_d_t = m_TF_dX_d(i)-m_TF_dX_d_limiter(i);
        double diff_TF_dX_d_r = m_TF_dX_d(i+3)-m_TF_dX_d_limiter(i+3);
        if(fabs(diff_TF_dX_d_t)/0.001>m_ddX_max(0)){
            cmd.TF_dX_d(i)=m_TF_dX_d_limiter(i)+msrm_utils::sgn(diff_TF_dX_d_t)*m_ddX_max(0)*0.001;
        }
        if(fabs(diff_TF_dX_d_r)/0.001>m_ddX_max(1)){
            cmd.TF_dX_d(i+3)=m_TF_dX_d_limiter(i+3)+msrm_utils::sgn(diff_TF_dX_d_r)*m_ddX_max(1)*0.001;
        }
    }
    m_TF_dX_d_limiter=cmd.TF_dX_d;
}

void TwistStrategy::terminate(const Percept &p){

}

bool TwistStrategy::finished(){
    return false;
}

void TwistStrategy::set_TF_dX_d(const Eigen::Matrix<double, 6, 1> &TF_dX_d, const Eigen::Matrix<double, 2, 1> &ddX_max){
    m_ddX_max=ddX_max;
    m_TF_dX_d=TF_dX_d;
}

}
