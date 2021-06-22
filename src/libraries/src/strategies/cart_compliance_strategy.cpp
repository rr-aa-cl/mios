#include "mios/strategies/cart_compliance_strategy.hpp"

namespace mios {

CartComplianceStrategy::CartComplianceStrategy():PrimitiveStrategy({CommandPatternCartesianCompliance}){
    m_K_x.setZero();
    m_xi_x.setZero();
}

void CartComplianceStrategy::initialize([[maybe_unused]] const Percept &p_0){
}

void CartComplianceStrategy::get_next_command(Actuator &cmd, [[maybe_unused]] const Percept &p){
    cmd.K_x=m_K_x;
    cmd.xi_x=m_xi_x;
}

void CartComplianceStrategy::terminate([[maybe_unused]] const Percept &p){

}

bool CartComplianceStrategy::finished(){
    return false;
}

void CartComplianceStrategy::set_complicance(const Eigen::Matrix<double, 6, 1> &K_x, const Eigen::Matrix<double, 6, 1> &xi_x){
    m_K_x=K_x;
    m_xi_x=xi_x;
}



}
