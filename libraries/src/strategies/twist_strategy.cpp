#include "strategies/twist_strategy.hpp"

namespace mios {

void TwistStrategy::initialize(const Percept &p_0){
    m_TF_dX_d.setZero();
}

void TwistStrategy::get_next_command(Actuator &cmd, const Percept &p){
    cmd.TF_dX_d=m_TF_dX_d;
}

void TwistStrategy::terminate(const Percept &p){

}

bool TwistStrategy::finished(){
    return false;
}

void TwistStrategy::set_TF_dX_d(const Eigen::Matrix<double, 6, 1> &TF_dX_d){
    m_TF_dX_d=TF_dX_d;
}

}
