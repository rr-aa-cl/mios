#include "mios/strategies/ff_wrench_fourier_strategy.hpp"
#include "msrm_cpp_utils/math/math.hpp"

namespace mios {

FFWrenchFourierStrategy::FFWrenchFourierStrategy():PrimitiveStrategy({CommandPatternCartesianFFWrench}){
    m_a0.setZero();
    m_a1.setZero();
    m_a2.setZero();
    m_b1.setZero();
    m_b2.setZero();
    m_f.setZero();
}

void FFWrenchFourierStrategy::initialize([[maybe_unused]] const Percept &p_0){
}

void FFWrenchFourierStrategy::get_next_command(Actuator &cmd, const Percept &p){
    for(unsigned i=0;i<6;i++){
        cmd.TF_F_ff(i)=m_a0(i)/2 + m_a1(i)*cos(2*M_PI*m_f(i)*cmd.t) + m_a2(i)*cos(2*M_PI*m_f(i)*cmd.t) + m_b1(i)*cos(2*M_PI*m_f(i)*cmd.t) + m_b2(i)*cos(2*M_PI*m_f(i)*cmd.t);
    }
}

void FFWrenchFourierStrategy::terminate([[maybe_unused]] const Percept &p){

}

bool FFWrenchFourierStrategy::finished(){
    return false;
}

void FFWrenchFourierStrategy::set_params(const Eigen::Matrix<double, 6, 1> &a0, const Eigen::Matrix<double, 6, 1> &a1, const Eigen::Matrix<double, 6, 1> &a2, const Eigen::Matrix<double, 6, 1> &b1, const Eigen::Matrix<double, 6, 1> &b2, const Eigen::Matrix<double, 6, 1> &f, Eigen::Matrix<double, 2, 1> dF_max){
    m_a0=a0;
    m_a1=a1;
    m_a2=a2;
    m_b1=b1;
    m_b2=b2;
    m_f=f;
}

}
