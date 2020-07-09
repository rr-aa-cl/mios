#include "strategies/joint_compliance_strategy.hpp"

namespace mios {

JointComplianceStrategy::JointComplianceStrategy():PrimitiveStrategy({CommandPatternJointCompliance}){

}

void JointComplianceStrategy::initialize(const Percept &p_0){
    m_K_theta=p_0.controller.K_theta;
    m_xi_theta=p_0.controller.xi_theta;
}

void JointComplianceStrategy::get_next_command(Actuator &cmd, const Percept &p){
    cmd.K_theta=m_K_theta;
    cmd.xi_theta=m_xi_theta;
}

void JointComplianceStrategy::terminate(const Percept &p){

}

bool JointComplianceStrategy::finished(){
    return false;
}

void JointComplianceStrategy::set_complicance(const Eigen::Matrix<double, 7, 1> &K_theta, const Eigen::Matrix<double, 7, 1> &xi_theta){
    m_K_theta=K_theta;
    m_xi_theta=xi_theta;
}



}
