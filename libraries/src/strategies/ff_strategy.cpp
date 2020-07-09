#include "strategies/ff_strategy.hpp"

namespace mios {

FFStrategy::FFStrategy():PrimitiveStrategy({CommandPatternCartesianFFWrench}){

}

void FFStrategy::initialize(const Percept &p_0){
    m_TF_F_ff.setZero();
}

void FFStrategy::get_next_command(Actuator &cmd, const Percept &p){
    cmd.TF_F_ff=m_TF_F_ff;
}

void FFStrategy::terminate(const Percept &p){

}

bool FFStrategy::finished(){
    return false;
}

void FFStrategy::set_TF_F_ff(const Eigen::Matrix<double,6,1> &TF_F_ff){
    m_TF_F_ff=TF_F_ff;
}



}
