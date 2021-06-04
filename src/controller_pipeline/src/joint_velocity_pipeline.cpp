#include "controller_pipeline/joint_velocity_pipeline.hpp"

namespace mios {

JointVelocityControllerPipeline::JointVelocityControllerPipeline():m_panda_cmd({0,0,0,0,0,0,0}){

}


void JointVelocityControllerPipeline::initialize(const Percept &p_0, Memory *memory){

}

franka::Finishable *JointVelocityControllerPipeline::step(const Percept &p, const Actuator &cmd){
    if(cmd.get_command_pattern()->find(CommandPatternJointPose)!=cmd.get_command_pattern()->end()){

    }
    m_panda_cmd.dq={cmd.dq_d(0),cmd.dq_d(1),cmd.dq_d(2),cmd.dq_d(3),cmd.dq_d(4),cmd.dq_d(5),cmd.dq_d(6)};
    return &m_panda_cmd;
}

bool JointVelocityControllerPipeline::is_valid_command(const franka::Finishable* const cmd) const{
    for(unsigned i=0;i<7;i++){
        if(static_cast<const franka::JointVelocities*>(cmd)->dq[i]!=static_cast<const franka::JointVelocities*>(cmd)->dq[i]){
            return false;
        }
    }
    return true;
}

void JointVelocityControllerPipeline::update_percept(Percept::Controller &p){
}

void JointVelocityControllerPipeline::terminate(){

}

void JointVelocityControllerPipeline::context_switch(const Percept &p){

}

}
