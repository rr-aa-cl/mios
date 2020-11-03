#include "controller_pipeline/cart_torque_pipeline.hpp"
#include "spdlog/spdlog.h"
#include <iostream>

namespace mios {

CartTorqueControllerPipeline::CartTorqueControllerPipeline():m_panda_cmd({0,0,0,0,0,0,0}),m_nullspace_control_on(false){
    spdlog::trace("CartTorqueControllerPipeline::CartTorqueControllerPipeline()");
}

CartTorqueControllerPipeline::~CartTorqueControllerPipeline(){
    spdlog::trace("CartTorqueControllerPipeline::~CartTorqueControllerPipeline()");
}

void CartTorqueControllerPipeline::initialize(const Percept &p_0, Memory *memory){
    initialize_cntr_aic(p_0,memory);
    initialize_cntr_force(p_0,memory);
    initialize_cntr_mux(p_0,memory);
    initialize_cntr_nullsp(p_0,memory);

    m_T_T_EE_0=p_0.proprioception.T_T_EE;
}

franka::Finishable *CartTorqueControllerPipeline::step(const Percept &p, const Actuator &cmd){
    input_cntr_aic(p);
    input_cntr_force(p);
    input_cntr_mux(p);
    input_cntr_nullsp(p);

    if(cmd.get_command_pattern()->find(CommandPatternCartesianPose)!=cmd.get_command_pattern()->end()){
        m_cntr_aic.u.TF_T_EE_d=cmd.TF_T_EE_d;
    }else if(cmd.get_command_pattern()->find(CommandPatternCartesianTwist)!=cmd.get_command_pattern()->end()){
        m_conv_vel2pose.u.TF_dX_d=cmd.TF_dX_d;
        m_conv_vel2pose.step();
        m_cntr_aic.u.TF_T_EE_d=m_conv_vel2pose.y.TF_T_EE_d;
    }
    else{
        m_cntr_aic.u.TF_T_EE_d=m_T_T_EE_0;
    }
    m_cntr_aic.u.O_R_T=cmd.O_R_T;

    m_cntr_aic.u.K_x=cmd.K_x;
    m_cntr_aic.u.xi_x=cmd.xi_x;
    m_cntr_aic.u.TF_F_ff=cmd.TF_F_ff;
    m_cntr_aic.step();

    m_cntr_force.u.TF_F_d_K=cmd.TF_F_d;
    m_cntr_force.u.O_R_T=cmd.O_R_T;
    m_cntr_force.step();

    m_cntr_nullsp_q.u.theta_d=cmd.q_d_nullspace;
    m_cntr_nullsp_q.step();
    m_cntr_nullsp_proj.u.tau_c=m_cntr_nullsp_q.y.tau_J_d;
    m_cntr_nullsp_proj.step();

    Eigen::Matrix<double,7,1> tau_J_d_total=m_cntr_aic.y.tau_J_d+m_cntr_force.y.tau_J_d+cmd.tau_ff;
    if(m_nullspace_control_on){
        tau_J_d_total+=m_cntr_nullsp_proj.y.tau_n;
    }

    m_cntr_mux.u.tau_J_d=tau_J_d_total;
    m_cntr_mux.step();
    m_panda_cmd.tau_J={m_cntr_mux.y.tau_J_d_checked(0),m_cntr_mux.y.tau_J_d_checked(1),m_cntr_mux.y.tau_J_d_checked(2),m_cntr_mux.y.tau_J_d_checked(3),m_cntr_mux.y.tau_J_d_checked(4),m_cntr_mux.y.tau_J_d_checked(5),m_cntr_mux.y.tau_J_d_checked(6)};

    return &m_panda_cmd;
}

bool CartTorqueControllerPipeline::is_valid_command(const franka::Finishable* const cmd) const{
    for(unsigned i=0;i<7;i++){
        if(static_cast<const franka::Torques*>(cmd)->tau_J[i]!=static_cast<const franka::Torques*>(cmd)->tau_J[i]){
            return false;
        }
    }
    return true;
}

void CartTorqueControllerPipeline::update_percept(Percept::Controller &p){
    p.TF_T_EE_d=m_cntr_aic.u.TF_T_EE_d;
    p.K_x=m_cntr_aic.l.K_x;
    p.K_theta=m_cntr_nullsp_q.l.K_theta;
}

void CartTorqueControllerPipeline::terminate(){
    spdlog::trace("CartTorqueControllerPipeline::terminate()");
    m_conv_vel2pose.terminate();
    m_cntr_aic.terminate();
    m_cntr_force.terminate();
    m_cntr_mux.terminate();
    m_cntr_nullsp_q.terminate();
    m_cntr_nullsp_proj.terminate();
}

void CartTorqueControllerPipeline::context_switch(const Percept &p){
    m_conv_vel2pose.u.TF_dX_d<<0,0,0,0,0,0;
    m_conv_vel2pose.u.TF_T_EE=m_cntr_aic.u.TF_T_EE_d;
    m_conv_vel2pose.u.reset<<1;
    m_conv_vel2pose.step();
    m_conv_vel2pose.u.reset<<0;
    m_T_T_EE_0=p.proprioception.T_T_EE;
}

void CartTorqueControllerPipeline::initialize_cntr_aic(const Percept &p,Memory* memory){
    const ControlParameters& p_cntr=memory->read_parameters()->control;
    const FramesParameters& p_frames=memory->read_parameters()->frames;
    const LimitParameters& p_limits=memory->read_parameters()->limits;
    m_cntr_aic.p.alpha=p_cntr.cart_imp_adaptation_stage.alpha;
    m_cntr_aic.p.beta=p_cntr.cart_imp_adaptation_stage.beta;
    m_cntr_aic.p.gamma_a=p_cntr.cart_imp_adaptation_stage.gamma_a;
    m_cntr_aic.p.gamma_b=p_cntr.cart_imp_adaptation_stage.gamma_b;
    m_cntr_aic.p.L=p_cntr.cart_imp_adaptation_stage.L;
    m_cntr_aic.p.F_ff_0=p_cntr.cart_imp_adaptation_stage.F_ff_0;
    m_cntr_aic.p.K_0=p_cntr.cart_imp.K_x;
    m_cntr_aic.p.xi=p_cntr.cart_imp.xi_x;
    m_cntr_aic.p.F_ff_max<<p_limits.cartesian_space.F_J_max(0),p_limits.cartesian_space.F_J_max(0),p_limits.cartesian_space.F_J_max(0),p_limits.cartesian_space.F_J_max(1),p_limits.cartesian_space.F_J_max(1),p_limits.cartesian_space.F_J_max(1);
    m_cntr_aic.p.dF_ff_max<<p_limits.cartesian_space.dF_J_max(0),p_limits.cartesian_space.dF_J_max(0),p_limits.cartesian_space.dF_J_max(0),p_limits.cartesian_space.dF_J_max(1),p_limits.cartesian_space.dF_J_max(1),p_limits.cartesian_space.dF_J_max(1);
    m_cntr_aic.p.K_max=p_limits.cartesian_space.K_x_max;
    m_cntr_aic.p.dK_max=p_limits.cartesian_space.dK_x_max;
    m_cntr_aic.p.EE_T_K=p_frames.EE_T_K;
    m_cntr_aic.p.dtau_max=p_limits.joint_space.dtau_J_max;
    m_cntr_aic.p.tau_max=p_limits.joint_space.tau_J_max;
    m_cntr_aic.p.kappa<<p_cntr.cart_imp_adaptation_stage.kappa;

    input_cntr_aic(p);

    m_cntr_aic.u.K_x=p_cntr.cart_imp.K_x;
    m_cntr_aic.u.xi_x=p_cntr.cart_imp.xi_x;

    m_cntr_aic.initialize();
    m_conv_vel2pose.u.reset<<1;
    m_conv_vel2pose.initialize();
    m_conv_vel2pose.step();

}

void CartTorqueControllerPipeline::input_cntr_aic(const Percept &p){
    m_cntr_aic.u.B_J_EE=p.internal_model.B_J_EE;
    m_cntr_aic.u.M=p.internal_model.M;
    m_cntr_aic.u.dtheta=p.proprioception.dtheta;
    m_cntr_aic.u.TF_F_ext=p.proprioception.TF_F_ext_K;
    m_cntr_aic.u.TF_F_ff<<0,0,0,0,0,0;
    m_cntr_aic.u.TF_T_EE=p.proprioception.T_T_EE;
    m_cntr_aic.u.TF_T_EE_d=p.proprioception.T_T_EE;
    m_cntr_aic.u.O_R_T=p.controller.O_R_T;

    m_conv_vel2pose.u.TF_dX_d<<0,0,0,0,0,0;
    m_conv_vel2pose.u.TF_T_EE=p.proprioception.T_T_EE;
    m_conv_vel2pose.u.reset<<0;
}

void CartTorqueControllerPipeline::initialize_cntr_force(const Percept &p, Memory *memory){
    const ControlParameters& p_cntr=memory->read_parameters()->control;
    const LimitParameters& p_limits=memory->read_parameters()->limits;
    m_cntr_force.p.active=p_cntr.force_control.active;
    m_cntr_force.p.dF_d_max<<p_limits.cartesian_space.dF_J_max(0),p_limits.cartesian_space.dF_J_max(0),p_limits.cartesian_space.dF_J_max(0),p_limits.cartesian_space.dF_J_max(1),p_limits.cartesian_space.dF_J_max(1),p_limits.cartesian_space.dF_J_max(1);
    m_cntr_force.p.F_d_max<<p_limits.cartesian_space.F_J_max(0),p_limits.cartesian_space.F_J_max(0),p_limits.cartesian_space.F_J_max(0),p_limits.cartesian_space.F_J_max(1),p_limits.cartesian_space.F_J_max(1),p_limits.cartesian_space.F_J_max(1);
    m_cntr_force.p.dtau_max<<std::numeric_limits<double>::max(),std::numeric_limits<double>::max(),std::numeric_limits<double>::max(),std::numeric_limits<double>::max(),
            std::numeric_limits<double>::max(),std::numeric_limits<double>::max(),std::numeric_limits<double>::max();
    m_cntr_force.p.tau_max<<std::numeric_limits<double>::max(),std::numeric_limits<double>::max(),std::numeric_limits<double>::max(),std::numeric_limits<double>::max(),
            std::numeric_limits<double>::max(),std::numeric_limits<double>::max(),std::numeric_limits<double>::max();
    m_cntr_force.p.k_p=p_cntr.force_control.k_p;
    m_cntr_force.p.k_i=p_cntr.force_control.k_i;
    m_cntr_force.p.k_d=p_cntr.force_control.k_d;
    m_cntr_force.p.k_d_N=p_cntr.force_control.k_d_N;
    m_cntr_force.p.d_max=p_cntr.force_control.d_max;
    m_cntr_force.p.phi_max<<p_cntr.force_control.phi_max;
    m_cntr_force.p.sf_on<<p_cntr.force_control.sf_on;

    input_cntr_force(p);

    m_cntr_force.initialize();
}

void CartTorqueControllerPipeline::input_cntr_force(const Percept &p){
    m_cntr_force.u.B_J_0=p.internal_model.B_J_O;
    m_cntr_force.u.DX<<0,0,0,0,0,0;
    m_cntr_force.u.TF_F_d_K<<0,0,0,0,0,0;
    m_cntr_force.u.TF_F_ext_K=-p.proprioception.TF_F_ext_K;
    m_cntr_force.u.O_R_T=p.controller.O_R_T;
}

void CartTorqueControllerPipeline::initialize_cntr_mux(const Percept &p,Memory* memory){
    const LimitParameters& p_limits=memory->read_parameters()->limits;

    m_cntr_mux.p.dtau_max=p_limits.joint_space.dtau_J_max;
    m_cntr_mux.p.tau_max=p_limits.joint_space.tau_J_max;

    input_cntr_mux(p);

    m_cntr_mux.initialize();
}

void CartTorqueControllerPipeline::input_cntr_mux(const Percept &p){
    m_cntr_mux.u.B_J_EE=p.internal_model.B_J_EE;
    m_cntr_mux.u.tau_J_d<<0,0,0,0,0,0,0;
}

void CartTorqueControllerPipeline::initialize_cntr_nullsp(const Percept& p,Memory* memory){
    const ControlParameters& p_cntr=memory->read_parameters()->control;

    m_cntr_nullsp_q.u.theta_d=p.proprioception.q;

    cntr_joint_var_imp::In_P_cntr_joint_var_imp in_p_cntr_nullsp_q;

    m_cntr_nullsp_q.p.enable_ffwd_acc.setZero();
    m_cntr_nullsp_q.p.enable_ffwd_vel.setZero();

    cntr_nullsp_proj::In_P_cntr_nullsp_proj in_p_cntr_nullsp_proj;
    m_cntr_nullsp_proj.p.singlr_comp_mode.setZero();
    m_cntr_nullsp_proj.p.singlr_threshold.setZero();

    input_cntr_nullsp(p);

    m_cntr_nullsp_q.u.K_theta=p_cntr.joint_imp.K_theta;
    m_cntr_nullsp_q.u.D_theta=p_cntr.joint_imp.xi_theta;

    m_cntr_nullsp_q.initialize();
    m_cntr_nullsp_proj.initialize();

    m_nullspace_control_on = memory->read_parameters()->control.nullspace_control.active;
}

void CartTorqueControllerPipeline::input_cntr_nullsp(const Percept &p){
    m_cntr_nullsp_q.u.theta=p.proprioception.q;
    m_cntr_nullsp_q.u.theta_d=p.proprioception.q;
    m_cntr_nullsp_q.u.dtheta=p.proprioception.dq;
    m_cntr_nullsp_q.u.dtheta_d<<0,0,0,0,0,0,0;
    m_cntr_nullsp_q.u.ddtheta_d<<0,0,0,0,0,0,0;
    m_cntr_nullsp_q.u.M=p.internal_model.M;
    m_cntr_nullsp_q.u.tau_ff.setZero();

    m_cntr_nullsp_proj.u.J=p.internal_model.B_J_EE;
    m_cntr_nullsp_proj.u.M=p.internal_model.M;
    m_cntr_nullsp_proj.u.tau_c.setZero();
}

}
