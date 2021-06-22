#include "mios/strategies/twist_wiggle_strategy.hpp"

namespace mios {

TwistWiggleStrategy::TwistWiggleStrategy():PrimitiveStrategy({CommandPatternCartesianTwist}){

}

void TwistWiggleStrategy::initialize([[maybe_unused]] const Percept &p_0){
    m_X_d_old.setZero();
}

void TwistWiggleStrategy::get_next_command(Actuator &cmd, [[maybe_unused]] const Percept &p){
    for(unsigned i=0;i<6;i++){
        m_X_d(i)=m_a_a(i)*cos(2*M_PI*m_a_f(i)*cmd.t+m_a_phi(i))+m_b_a(i)*sin(2*M_PI*m_b_f(i)*cmd.t+m_b_phi(i));
        cmd.TF_dX_d(i)=(m_X_d(i)-m_X_d_old(i))/0.001;
    }
    m_X_d_old=m_X_d;
}

void TwistWiggleStrategy::terminate([[maybe_unused]] const Percept &p){

}

bool TwistWiggleStrategy::finished(){
    return false;
}

void TwistWiggleStrategy::set_coefficients(Eigen::Matrix<double, 6, 1> a_a, Eigen::Matrix<double, 6, 1> b_a, Eigen::Matrix<double, 6, 1> a_f, Eigen::Matrix<double, 6, 1> b_f, Eigen::Matrix<double, 6, 1> a_phi, Eigen::Matrix<double, 6, 1> b_phi){
    m_a_a=a_a;
    m_b_a=b_a;
    m_a_f=a_f;
    m_b_f=b_f;
    m_a_phi=a_phi;
    m_b_phi=b_phi;
}

}
