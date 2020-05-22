#include "controller_pipeline/cart_velocity_pipeline.hpp"

namespace mios {

CartVelocityControllerPipeline::CartVelocityControllerPipeline():m_panda_cmd({0,0,0,0,0,0}){

}


void CartVelocityControllerPipeline::initialize(const Percept &p_0, Memory *memory){

}

franka::Finishable *CartVelocityControllerPipeline::step(const Percept &p, const Actuator &cmd){

    Eigen::Matrix<double,6,1> O_dX_d;
    O_dX_d<<cmd.O_R_T*cmd.TF_dX_d.block<3,1>(0,0),cmd.O_R_T*cmd.TF_dX_d.block<3,1>(3,0);
    m_panda_cmd.O_dP_EE={O_dX_d(0),O_dX_d(1),O_dX_d(2),O_dX_d(3),O_dX_d(4),O_dX_d(5)};
    return &m_panda_cmd;
}

bool CartVelocityControllerPipeline::is_valid_command(const franka::Finishable* const cmd) const{
    for(unsigned i=0;i<6;i++){
        if(static_cast<franka::CartesianVelocities*>(cmd)->O_dP_EE[i]!=static_cast<franka::CartesianVelocities*>(cmd)->O_dP_EE[i]){
            return false;
        }
    }
    return true;
}

}
