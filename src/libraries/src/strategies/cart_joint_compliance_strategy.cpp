#include "mios/strategies/cart_joint_compliance_strategy.hpp"

namespace mios {

CartJointComplianceStrategy::CartJointComplianceStrategy():PrimitiveStrategy({CommandPatternCartesianJointCompliance}){
    m_K_x.setZero();
    m_xi_x.setZero();
    m_K_theta.setZero();
    m_xi_theta.setZero();
}

void CartJointComplianceStrategy::initialize([[maybe_unused]] const Percept &p_0){
}

void CartJointComplianceStrategy::get_next_command(Actuator &cmd, [[maybe_unused]] const Percept &p){
    cmd.K_x=m_K_x;
    cmd.xi_x=m_xi_x;
    cmd.K_theta=m_K_theta;
    cmd.xi_theta=m_xi_theta;
}

void CartJointComplianceStrategy::terminate([[maybe_unused]] const Percept &p){

}

bool CartJointComplianceStrategy::finished(){
    return false;
}

void CartJointComplianceStrategy::set_complicance(const Eigen::Matrix<double, 6, 1> &K_x, const Eigen::Matrix<double, 6, 1> &xi_x,
                                                  const Eigen::Matrix<double, 7, 1> &K_theta, const Eigen::Matrix<double, 7, 1> &xi_theta){
    m_K_x=K_x;
    m_xi_x=xi_x;
    m_K_theta=K_theta;
    m_xi_theta=xi_theta;
}



}
