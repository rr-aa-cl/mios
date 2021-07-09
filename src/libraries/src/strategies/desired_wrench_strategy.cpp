#include "mios/strategies/desired_wrench_strategy.hpp"
#include "msrm_cpp_utils/math/math.hpp"

namespace mios{

DesiredWrenchStrategy::DesiredWrenchStrategy():PrimitiveStrategy({CommandPatternDesiredWrench}){
    m_TF_F_d.setZero();
    m_TF_F_d_limiter.setZero();
    m_dF_max.setZero();
}

void DesiredWrenchStrategy::initialize([[maybe_unused]] const Percept& p_0){

}

void DesiredWrenchStrategy::get_next_command(Actuator& cmd, [[maybe_unused]] const Percept& p_0){
    for(unsigned i=0;i<3;i++){
        double diff_TF_F_d_t = m_TF_F_d(i)-m_TF_F_d_limiter(i);
        double diff_TF_F_d_r = m_TF_F_d(i+3)-m_TF_F_d_limiter(i+3);
        if(fabs(diff_TF_F_d_t)/0.001>m_dF_max(0)){
            cmd.TF_F_d(i)=m_TF_F_d_limiter(i)+msrm_utils::sgn(diff_TF_F_d_t)*m_dF_max(0)*0.001;
        }else{
            cmd.TF_F_d(i)=m_TF_F_d(i);
        }
        if(fabs(diff_TF_F_d_r)/0.001>m_dF_max(1)){
            cmd.TF_F_d(i+3)=m_TF_F_d_limiter(i+3)+msrm_utils::sgn(diff_TF_F_d_r)*m_dF_max(1)*0.001;
        }else{
            cmd.TF_F_d(i+3)=m_TF_F_d(i+3);
        }
    }
    m_TF_F_d_limiter=cmd.TF_F_d;
}

void DesiredWrenchStrategy::terminate([[maybe_unused]] const Percept& p){

}

bool DesiredWrenchStrategy::finished(){
    return false;
}

void DesiredWrenchStrategy::set_TF_F_d(const Eigen::Matrix<double, 6, 1> &TF_F_d, Eigen::Matrix<double,2,1> dF_max){
    m_dF_max=dF_max;
    m_TF_F_d=TF_F_d;
}

}
