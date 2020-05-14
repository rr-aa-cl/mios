#include "controller_pipeline/torque_pipeline.hpp"

namespace mios {


void CartTorqueControllerPipeline::initialize(const Percept &p_0, KnowledgeBase *kb){
    initialize_cntr_aic(p_0,kb);
    initialize_cntr_force(p_0,kb);
    initialize_cntr_mux(p_0,kb);
    initialize_virt_cube(p_0,kb);
    initialize_virt_walls_joint(p_0,kb);
    initialize_cntr_nullsp(p_0,kb);
}

franka::Finishable CartTorqueControllerPipeline::step(const Percept &p, const Actuator &cmd){
    input_cntr_aic(p);
    input_cntr_force(p);
    input_cntr_mux(p);
    input_virt_cube(p);
    input_virt_joint_walls(p);
    input_cntr_nullsp(p);

    m_in_u_vel2pose.TF_dX_d=cmd.TF_dX_d;
    m_conv_vel2pose.step(m_in_u_vel2pose,m_out_y_vel2pose);
    m_in_u_aic.TF_T_EE_d=m_out_y_vel2pose.TF_T_EE_d;
    m_cntr_aic.step(m_in_u_aic,m_out_y_aic);

    m_in_u_force.TF_F_d_K=cmd.TF_F_d;
    m_cntr_force.step(m_in_u_force,m_out_y_force);

    m_virt_cube.step(m_in_u_virt_cube,m_out_y_virt_cube);

    m_virt_walls_joint.step(m_in_u_virt_walls_joint,m_out_y_virt_walls_joint);

    m_cntr_nullsp_q.step(m_in_u_cntr_nullsp_q,m_out_y_cntr_nullsp_q);
    m_in_u_cntr_nullsp_proj.tau_c=m_out_y_cntr_nullsp_q.tau_J_d;
    m_cntr_nullsp_proj.step(m_in_u_cntr_nullsp_proj,m_out_y_cntr_nullsp_proj);

    Eigen::Matrix<double,7,1> tau_J_d_total=m_out_y_aic.tau_J_d+m_out_y_force.tau_J_d+cmd.tau_ff;
    if(m_virtual_cube_on && is_virt_cube_valid(p)){
        tau_J_d_total+=m_out_y_virt_cube.tau_vwalls;
    }
    if(m_virtual_joint_walls_on && is_virt_joint_walls_valid(p)){
        tau_J_d_total+=m_out_y_virt_walls_joint.tau_vwalls;
    }
    if(m_nullspace_control_on){
        tau_J_d_total+=m_out_y_cntr_nullsp_proj.tau_n;
    }

    m_in_u_mux.tau_J_d=tau_J_d_total;
    m_cntr_mux.step(m_in_u_mux,m_out_y_mux);

    return franka::Torques({tau_J_d_total(0),tau_J_d_total(1),tau_J_d_total(2),tau_J_d_total(3),tau_J_d_total(4),tau_J_d_total(5),tau_J_d_total(6)});
}

void CartTorqueControllerPipeline::terminate(){
    m_conv_vel2pose.terminate();
    m_cntr_aic.terminate();
    m_cntr_force.terminate();
    m_cntr_mux.terminate();
}

void CartTorqueControllerPipeline::set_virtual_cube(bool on){
    m_virtual_cube_on=on;
}

void CartTorqueControllerPipeline::set_virtual_joint_walls(bool on){
    m_virtual_joint_walls_on=on;
}

void CartTorqueControllerPipeline::initialize_cntr_aic(const Percept &p,KnowledgeBase* kb){
    cntr_aic::In_P_cntr_aic in_p_aic;
    conv_vel2pose::In_P_conv_vel2pose in_p_vel2pose;
    const ConfigController& c_cntr=kb->get_local_memory()->access_config_cntr();
    const ConfigFrames& c_frames=kb->get_local_memory()->access_config_frames();
    in_p_aic.alpha=c_cntr.alpha;
    in_p_aic.beta=c_cntr.beta;
    in_p_aic.gamma_a=c_cntr.gamma_a;
    in_p_aic.gamma_b=c_cntr.gamma_b;
    in_p_aic.L=c_cntr.L;
    in_p_aic.K_0=c_cntr.K_0;
    in_p_aic.F_ff_0=c_cntr.F_ff_0;
    in_p_aic.xi=c_cntr.xi;
    in_p_aic.F_ff_max=c_cntr.F_ff_max;
    in_p_aic.dF_ff_max=c_cntr.dF_ff_max;
    in_p_aic.K_max=c_cntr.K_max;
    in_p_aic.dK_max=c_cntr.dK_max;
    in_p_aic.O_R_TF=c_frames.O_R_TF;
    in_p_aic.EE_T_K=c_frames.EE_T_K;
    in_p_aic.dtau_max<<1000,1000,1000,1000,1000,1000,1000;
    in_p_aic.tau_max<<87,87,87,87,12,12,12;
    in_p_aic.TF_control<<c_cntr.TF_control;
    in_p_aic.kappa<<c_cntr.kappa;

    input_cntr_aic(p);

    m_in_u_aic.K_x=c_cntr.K_0;
    m_in_u_aic.xi_x=c_cntr.xi;

    m_cntr_aic.initialize(m_in_u_aic,in_p_aic);
    m_conv_vel2pose.initialize(m_in_u_vel2pose,in_p_vel2pose);

}

void CartTorqueControllerPipeline::input_cntr_aic(const Percept &p){
    m_in_u_aic.B_J_EE=p.InternalModel.B_J_EE;
    m_in_u_aic.M=p.InternalModel.M;
    m_in_u_aic.dtheta=p.Proprioception.dtheta;
    m_in_u_aic.TF_F_ext=p.Proprioception.TF_F_ext_K;
    m_in_u_aic.TF_F_ff<<0,0,0,0,0,0;
    m_in_u_aic.TF_T_EE=p.Proprioception.TF_T_EE;
    m_in_u_aic.TF_T_EE_d=p.Proprioception.TF_T_EE;

    m_in_u_vel2pose.TF_dX_d<<0,0,0,0,0,0;
    m_in_u_vel2pose.TF_T_EE=p.Proprioception.TF_T_EE;
}

void CartTorqueControllerPipeline::initialize_cntr_force(const Percept &p, KnowledgeBase *kb){
    cntr_force::In_P_cntr_force in_p_force;
    const ConfigController& c_cntr=kb->get_local_memory()->access_config_cntr();
    in_p_force.active=c_cntr.f_cntr_active;
    in_p_force.dF_d_max=c_cntr.dF_c_max;
    in_p_force.F_d_max=c_cntr.F_c_max;
    in_p_force.dtau_max<<std::numeric_limits<double>::max(),std::numeric_limits<double>::max(),std::numeric_limits<double>::max(),std::numeric_limits<double>::max(),
            std::numeric_limits<double>::max(),std::numeric_limits<double>::max(),std::numeric_limits<double>::max();
    in_p_force.tau_max<<std::numeric_limits<double>::max(),std::numeric_limits<double>::max(),std::numeric_limits<double>::max(),std::numeric_limits<double>::max(),
            std::numeric_limits<double>::max(),std::numeric_limits<double>::max(),std::numeric_limits<double>::max();
    in_p_force.k_p=c_cntr.f_cntr_k_p;
    in_p_force.k_i=c_cntr.f_cntr_k_i;
    in_p_force.k_d=c_cntr.f_cntr_k_d;
    in_p_force.k_d_N=c_cntr.f_cntr_k_d_N;
    in_p_force.d_max=c_cntr.f_cntr_d_max;
    in_p_force.phi_max=c_cntr.f_cntr_phi_max;
    in_p_force.sf_on<<c_cntr.f_cntr_sf_on;

    input_cntr_force(p);

    m_cntr_force.initialize(m_in_u_force,in_p_force);
}

void CartTorqueControllerPipeline::input_cntr_force(const Percept &p){
    m_in_u_force.B_J_EE=p.InternalModel.B_J_EE;
    m_in_u_force.DX<<0,0,0,0,0,0;
    m_in_u_force.TF_F_d_K<<0,0,0,0,0,0;
    m_in_u_force.TF_F_ext_K=-p.Proprioception.TF_F_ext;
}

void CartTorqueControllerPipeline::initialize_cntr_mux(const Percept &p,KnowledgeBase* kb){
    cntr_mux::In_P_cntr_mux in_p_mux;
    const ConfigController& c_cntr=kb->get_local_memory()->access_config_cntr();

    in_p_mux.dtau_max=c_cntr.dtau_c_max;
    in_p_mux.tau_max=c_cntr.tau_c_max;

    input_cntr_mux(p);

    m_cntr_mux.initialize(m_in_u_mux,in_p_mux);
}

void CartTorqueControllerPipeline::input_cntr_mux(const Percept &p){
    m_in_u_mux.B_J_EE=p.InternalModel.B_J_EE;
    m_in_u_mux.tau_J_d<<0,0,0,0,0,0,0;
}

void CartTorqueControllerPipeline::initialize_virt_cube(const Percept &p,KnowledgeBase* kb){
    virtual_cube::In_P_virtual_cube in_p_virt_cube;
    const ConfigController& c_cntr=kb->get_local_memory()->access_config_cntr();
    in_p_virt_cube.damping_distance=c_cntr.virt_cube_damp_dist;
    in_p_virt_cube.damping_factor=c_cntr.virt_cube_damp;
    in_p_virt_cube.eta=c_cntr.virt_cube_eta;
    in_p_virt_cube.rho_min=c_cntr.virt_cube_rho_min;
    in_p_virt_cube.cube_walls=c_cntr.virt_cube_walls;
    in_p_virt_cube.f_max=c_cntr.virt_cube_f_max;

    m_virt_cube_distances=c_cntr.virt_cube_walls;

    input_virt_cube(p);

    m_virt_cube.initialize(m_in_u_virt_cube,in_p_virt_cube);

    m_flag_virt_cube_valid=false;
}

void CartTorqueControllerPipeline::input_virt_cube(const Percept &p){
    m_in_u_virt_cube.dx_EE=p.Proprioception.O_dX_EE;
    m_in_u_virt_cube.p_EE=p.Proprioception.O_T_EE.block<3,1>(0,3);
    m_in_u_virt_cube.Jacobian_EE=p.InternalModel.B_J_O;
}

void CartTorqueControllerPipeline::initialize_virt_walls_joint(const Percept &p,KnowledgeBase* kb){
    virtual_walls_joint::In_P_virtual_walls_joint in_p_virt_walls_joint;
    const ConfigController& c_cntr=kb->get_local_memory()->access_config_cntr();
    in_p_virt_walls_joint.damping_distance=c_cntr.virt_walls_joint_damp_dist;
    in_p_virt_walls_joint.damping_factor=c_cntr.virt_walls_joint_damp;
    in_p_virt_walls_joint.eta=c_cntr.virt_walls_joint_eta;
    in_p_virt_walls_joint.rho_min=c_cntr.virt_walls_joint_rho_min;
    in_p_virt_walls_joint.tau_max=c_cntr.virt_walls_joint_tau_max;
    in_p_virt_walls_joint.walls=c_cntr.virt_walls_joint_walls;

    m_virt_joint_walls_distances=c_cntr.virt_walls_joint_walls;

    input_virt_joint_walls(p);

    m_virt_walls_joint.initialize(m_in_u_virt_walls_joint,in_p_virt_walls_joint);

    m_flag_virt_joint_walls_valid=false;
}

void CartTorqueControllerPipeline::input_virt_joint_walls(const Percept &p){
    m_in_u_virt_walls_joint.dq=p.Proprioception.dq;
    m_in_u_virt_walls_joint.q=p.Proprioception.q;
}

void CartTorqueControllerPipeline::initialize_cntr_nullsp(const Percept& p,KnowledgeBase* kb){
    const ConfigController& c_cntr=kb->get_local_memory()->access_config_cntr();

    m_in_u_cntr_nullsp_q.theta_d=p.Proprioception.q;

    cntr_joint_var_imp::In_P_cntr_joint_var_imp in_p_cntr_nullsp_q;

    in_p_cntr_nullsp_q.enable_ffwd_acc.setZero();
    in_p_cntr_nullsp_q.enable_ffwd_vel.setZero();

    cntr_nullsp_proj::In_P_cntr_nullsp_proj in_p_cntr_nullsp_proj;
    in_p_cntr_nullsp_proj.singlr_comp_mode.setZero();
    in_p_cntr_nullsp_proj.singlr_threshold.setZero();

    input_cntr_nullsp(p);

    m_in_u_cntr_nullsp_q.K_theta=c_cntr.K_theta;
    m_in_u_cntr_nullsp_q.D_theta=c_cntr.xi_theta;

    m_cntr_nullsp_q.initialize(m_in_u_cntr_nullsp_q,in_p_cntr_nullsp_q);
    m_cntr_nullsp_proj.initialize(m_in_u_cntr_nullsp_proj,in_p_cntr_nullsp_proj);
}

void CartTorqueControllerPipeline::input_cntr_nullsp(const Percept &p){
    m_in_u_cntr_nullsp_q.theta=p.Proprioception.q;
    m_in_u_cntr_nullsp_q.theta_d=p.q;
    m_in_u_cntr_nullsp_q.dtheta=p.Proprioception.dq;
    m_in_u_cntr_nullsp_q.dtheta_d<<0,0,0,0,0,0,0;
    m_in_u_cntr_nullsp_q.ddtheta_d<<0,0,0,0,0,0,0;
    m_in_u_cntr_nullsp_q.M=p.InternalModel.M;
    m_in_u_cntr_nullsp_q.tau_ff.setZero();

    m_in_u_cntr_nullsp_proj.J=p.InternalModel.B_J_EE;
    m_in_u_cntr_nullsp_proj.M=p.InternalModel.M;
    m_in_u_cntr_nullsp_proj.tau_c.setZero();
}

bool CartTorqueControllerPipeline::is_virt_cube_valid(const Percept& p){
    std::array<bool,3> in_cube={false,false,false};
    bool safe_activation=true;
    for(unsigned i=0;i<6;i++){
        if(fabs(m_out_y_virt_cube.wall_flag(i))>0){
            safe_activation=false;
            break;
        }
    }
    for(unsigned i=0;i<3;i++){
        if(p.Proprioception.O_T_EE(i,3)>m_virt_cube_distances(i*2) || p.Proprioception.O_T_EE(i,3)<m_virt_cube_distances(i*2+1)){
            in_cube[i]=false;
        }else{
            in_cube[i]=true;
        }
    }
    if(in_cube[0] && in_cube[1] && in_cube[2] && safe_activation){
        return true;
    }
    else{
        return false;
    }
}

bool CartTorqueControllerPipeline::is_virt_joint_walls_valid(const Percept& p){
    std::array<bool,7> in_walls={false,false,false,false,false,false,false};

    bool safe_activation=true;
    for(unsigned i=0;i<7;i++){
        if(fabs(m_out_y_virt_walls_joint.wall_flag(i))>0){
            safe_activation=false;
            break;
        }
    }
    for(unsigned i=0;i<7;i++){
        if(p.Proprioception.q(i)>m_virt_joint_walls_distances(i*2) || p.Proprioception.q(i)<m_virt_joint_walls_distances(i*2+1)){
            in_walls[i]=false;
        }else{
            in_walls[i]=true;
        }
    }
    if(in_walls[0] && in_walls[1] && in_walls[2] && in_walls[3] && in_walls[4] && in_walls[5] && in_walls[6] && safe_activation){
        return true;
    }else{
        return false;
    }
}

}
