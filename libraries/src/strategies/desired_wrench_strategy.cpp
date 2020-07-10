#include "strategies/desired_wrench_strategy.hpp"
namespace mios{

DesiredWrenchStrategy::DesiredWrenchStrategy():PrimitiveStrategy({CommandPatternDesiredWrench}){

}

void DesiredWrenchStrategy::initialize(const Percept& p_0){
    m_TF_F_d.setZero();
}

void DesiredWrenchStrategy::get_next_command(Actuator& cmd, const Percept& p_0){
    cmd.TF_F_d=m_TF_F_d;
}

void DesiredWrenchStrategy::terminate(const Percept& p){

}

bool DesiredWrenchStrategy::finished(){
    return false;
}

void DesiredWrenchStrategy::set_TF_F_d(const Eigen::Matrix<double, 6, 1> &TF_F_d){
    m_TF_F_d=TF_F_d;
}

}
