#include "mios/strategies/joint_compliance_strategy.hpp"

namespace mios {

JointComplianceStrategy::JointComplianceStrategy():PrimitiveStrategy({CommandPatternJointCompliance}){
    m_K_theta.setZero();
    m_xi_theta.setZero();
}

void JointComplianceStrategy::initialize([[maybe_unused]] const Percept &p_0){
}

void JointComplianceStrategy::get_next_command(Actuator &cmd, [[maybe_unused]] const Percept &p){
    cmd.K_theta=m_K_theta;
    cmd.xi_theta=m_xi_theta;
}

void JointComplianceStrategy::terminate([[maybe_unused]] const Percept &p){

}

bool JointComplianceStrategy::finished(){
    return false;
}

void JointComplianceStrategy::set_complicance(const Eigen::Matrix<double, 7, 1> &K_theta, const Eigen::Matrix<double, 7, 1> &xi_theta){
    m_K_theta=K_theta;
    m_xi_theta=xi_theta;
}



}
