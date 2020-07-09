#include "strategies/cart_compliance_strategy.hpp"

namespace mios {

CartComplianceStrategy::CartComplianceStrategy():PrimitiveStrategy({CommandPatternCartesianCompliance}){

}

void CartComplianceStrategy::initialize(const Percept &p_0){
    m_K_x=p_0.controller.K_x;
    m_xi_x=p_0.controller.xi_x;
}

void CartComplianceStrategy::get_next_command(Actuator &cmd, const Percept &p){
    cmd.K_x=m_K_x;
    cmd.xi_x=m_xi_x;
}

void CartComplianceStrategy::terminate(const Percept &p){

}

bool CartComplianceStrategy::finished(){
    return false;
}

void CartComplianceStrategy::set_complicance(const Eigen::Matrix<double, 6, 1> &K_x, const Eigen::Matrix<double, 6, 1> &xi_x){
    m_K_x=K_x;
    m_xi_x=xi_x;
}



}
