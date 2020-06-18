#include "strategy/primitive_strategy.hpp"

namespace mios{

PrimitiveStrategy::PrimitiveStrategy(bool command_TF_T_EE_d,bool command_TF_F_d,bool command_q_d,bool command_q_d_nullspace, bool command_tau_d):
m_command_TF_T_EE_d(command_TF_T_EE_d),m_command_TF_F_d(command_TF_F_d),m_command_q_d(command_q_d),m_command_q_d_nullspace(command_q_d_nullspace),
m_command_tau_d(command_tau_d){

}

bool PrimitiveStrategy::is_commanding_TF_T_EE_d() const{
    return m_command_TF_T_EE_d;
}

bool PrimitiveStrategy::is_commanding_TF_F_d() const{
    return m_command_TF_F_d;
}

bool PrimitiveStrategy::is_commanding_q_d() const{
    return m_command_q_d;
}

bool PrimitiveStrategy::is_commanding_q_d_nullspace() const{
    return m_command_q_d_nullspace;
}

bool PrimitiveStrategy::is_commanding_tau_d() const{
    return m_command_tau_d;
}

}
