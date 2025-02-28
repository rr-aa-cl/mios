#include "mios/strategies/ff_wrench_lissajous_strategy.hpp"

namespace mios {

FFWrenchLissajousStrategy::FFWrenchLissajousStrategy():PrimitiveStrategy({CommandPatternCartesianFFWrench}){

}

void FFWrenchLissajousStrategy::initialize([[maybe_unused]] const Percept &p_0){
}

void FFWrenchLissajousStrategy::get_next_command(Actuator &cmd, [[maybe_unused]] const Percept &p){
    for(unsigned i=0;i<6;i++){
        //cmd.TF_F_ff(i)=m_a(i)*sin(2*M_PI*m_f(i)*cmd.t+m_phi(i));
        cmd.TF_F_ff(i) = m_c(i) + m_a(i)*( sin(2*M_PI*m_f(i)*cmd.t + m_phi(i)) - sin(m_phi(i)));
    }
}

void FFWrenchLissajousStrategy::terminate([[maybe_unused]] const Percept &p){

}

bool FFWrenchLissajousStrategy::finished(){
    return false;
}

void FFWrenchLissajousStrategy::set_coefficients(Eigen::Matrix<double, 6, 1> a, Eigen::Matrix<double, 6, 1> f, Eigen::Matrix<double, 6, 1> phi){
    m_c << 0,0,0,0,0,0;
    m_a=a;
    m_f=f;
    m_phi=phi;
}
void FFWrenchLissajousStrategy::set_coefficients(Eigen::Matrix<double, 6, 1> c, Eigen::Matrix<double, 6, 1> a, Eigen::Matrix<double, 6, 1> f, Eigen::Matrix<double, 6, 1> phi){
    m_c=c;
    m_a=a;
    m_f=f;
    m_phi=phi;
}
}
