#include "mios/controller_pipeline/cart_velocity_pipeline.hpp"
#include "spdlog/spdlog.h"

namespace mios {

CartVelocityControllerPipeline::CartVelocityControllerPipeline():m_panda_cmd({0,0,0,0,0,0}){
    spdlog::trace("CartVelocityControllerPipeline::CartVelocityControllerPipeline");
}


void CartVelocityControllerPipeline::initialize([[maybe_unused]] const Percept &p_0, [[maybe_unused]] Memory *memory){
    spdlog::trace("CartVelocityControllerPipeline::initialize");
}

franka::Finishable *CartVelocityControllerPipeline::step([[maybe_unused]] const Percept &p, const Actuator &cmd){

    Eigen::Matrix<double,6,1> O_dX_d;
    O_dX_d<<cmd.O_R_T*cmd.TF_dX_d.block<3,1>(0,0),cmd.O_R_T*cmd.TF_dX_d.block<3,1>(3,0);
    m_panda_cmd.O_dP_EE={O_dX_d(0),O_dX_d(1),O_dX_d(2),O_dX_d(3),O_dX_d(4),O_dX_d(5)};
    return &m_panda_cmd;
}

bool CartVelocityControllerPipeline::is_valid_command(const franka::Finishable* const cmd) const{
    for(unsigned i=0;i<6;i++){
        if(static_cast<const franka::CartesianVelocities*>(cmd)->O_dP_EE[i]!=static_cast<const franka::CartesianVelocities*>(cmd)->O_dP_EE[i]){
            return false;
        }
    }
    return true;
}

void CartVelocityControllerPipeline::update_percept([[maybe_unused]] Percept::Controller &p){

}

void CartVelocityControllerPipeline::terminate(){
    spdlog::trace("CartVelocityControllerPipeline::terminate");
}

void CartVelocityControllerPipeline::context_switch([[maybe_unused]] const Percept &p){
    spdlog::trace("CartVelocityControllerPipeline::context_switch");
}

}
