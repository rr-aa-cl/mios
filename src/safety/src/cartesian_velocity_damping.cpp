#include "safety_stage_2/cartesian_velocity_damping.hpp"
#include "msrm_cpp_utils/math.hpp"

namespace mios{

CartesianVelocityDampingSafetyModule::CartesianVelocityDampingSafetyModule():m_damping_on(false),m_D_x(Eigen::Matrix<double,6,1>::Zero(6,1)),m_dX_thr(Eigen::Matrix<double,6,1>::Zero(6,1)){

}

void CartesianVelocityDampingSafetyModule::initialize(const Percept &p_0, const Memory *memory){
    m_damping_on = memory->read_parameters()->safety.cartesian_velocity_damping.active;
    m_dX_thr = memory->read_parameters()->safety.cartesian_velocity_damping.dX_thr;
    m_D_x = memory->read_parameters()->safety.cartesian_velocity_damping.D_x;
}

void CartesianVelocityDampingSafetyModule::step(const Percept &p, franka::Finishable *cmd){
    if(m_damping_on){

        Eigen::Matrix<double,6,1> F_damp;
        F_damp.setZero();
        for(unsigned i=0;i<6;i++){
            if(fabs(p.proprioception.TF_dX_EE(i))>m_dX_thr(i)){
                F_damp(i)=-msrm_utils::sgn(p.proprioception.TF_dX_EE(i))*(fabs(p.proprioception.TF_dX_EE(i))-m_dX_thr(i))*m_D_x(i);
            }
        }
        Eigen::Matrix<double,7,1> tau_damp = p.internal_model.B_J_EE.transpose()*F_damp;
        for(unsigned i=0;i<7;i++){
            static_cast<franka::Torques*>(cmd)->tau_J[i]+=tau_damp(i);
        }
    }
}

void CartesianVelocityDampingSafetyModule::terminate(){

}

}
