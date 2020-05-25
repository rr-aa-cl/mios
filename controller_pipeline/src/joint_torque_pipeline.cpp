#include "controller_pipeline/joint_torque_pipeline.hpp"

namespace mios {

JointTorqueControllerPipeline::JointTorqueControllerPipeline():m_panda_cmd({0,0,0,0,0,0,0}){

}


void JointTorqueControllerPipeline::initialize(const Percept &p_0, Memory *memory){
    initialize_cntr_joint_imp(p_0,memory);
    initialize_cntr_mux(p_0,memory);
    initialize_virt_cube(p_0,memory);
    initialize_virt_walls_joint(p_0,memory);
}

franka::Finishable *JointTorqueControllerPipeline::step(const Percept &p, const Actuator &cmd){
    input_cntr_joint_imp(p);
    input_cntr_mux(p);
    input_virt_cube(p);
    input_virt_joint_walls(p);

    m_in_u_cntr_joint_imp.theta_d=m_q_d_old+cmd.dq_d*0.001;
    m_in_u_cntr_joint_imp.K_theta=cmd.K_theta;
    m_q_d_old+=cmd.dq_d*0.001;

    m_cntr_joint_imp.step(m_in_u_cntr_joint_imp,m_out_y_cntr_joint_imp);

    m_virt_cube.step(m_in_u_virt_cube,m_out_y_virt_cube);

    m_virt_walls_joint.step(m_in_u_virt_walls_joint,m_out_y_virt_walls_joint);

    Eigen::Matrix<double,7,1> tau_J_d_total=m_out_y_cntr_joint_imp.tau_J_d+cmd.tau_ff;
    if(m_virtual_cube_on && is_virt_cube_valid(p)){
        tau_J_d_total+=m_out_y_virt_cube.tau_vwalls;
    }
    if(m_virtual_joint_walls_on && is_virt_joint_walls_valid(p)){
        tau_J_d_total+=m_out_y_virt_walls_joint.tau_vwalls;
    }

    m_in_u_mux.tau_J_d=tau_J_d_total;
    m_cntr_mux.step(m_in_u_mux,m_out_y_mux);
    m_panda_cmd.tau_J={tau_J_d_total(0),tau_J_d_total(1),tau_J_d_total(2),tau_J_d_total(3),tau_J_d_total(4),tau_J_d_total(5),tau_J_d_total(6)};

    return &m_panda_cmd;
}

bool JointTorqueControllerPipeline::is_valid_command(const franka::Finishable* const cmd) const{
    for(unsigned i=0;i<7;i++){
        if(static_cast<const franka::Torques*>(cmd)->tau_J[i]!=static_cast<const franka::Torques*>(cmd)->tau_J[i]){
            return false;
        }
    }
    return true;
}

void JointTorqueControllerPipeline::update_percept(Percept::Controller &p){
    p.q_d=m_in_u_cntr_joint_imp.theta_d;
    p.dq_d=m_in_u_cntr_joint_imp.dtheta_d;
}

void JointTorqueControllerPipeline::terminate(){
    m_cntr_joint_imp.terminate();
    m_cntr_mux.terminate();
    m_virt_cube.terminate();
    m_virt_walls_joint.terminate();
}


void JointTorqueControllerPipeline::initialize_cntr_joint_imp(const Percept &p, Memory *memory){
    m_q_d_old=p.proprioception.q;
    const ControlParameters& p_cntr=memory->read_parameters()->control;

    cntr_joint_var_imp::In_P_cntr_joint_var_imp in_p_cntr_joint_imp;

    in_p_cntr_joint_imp.enable_ffwd_acc.setZero();
    in_p_cntr_joint_imp.enable_ffwd_vel.setZero();

    input_cntr_joint_imp(p);

    m_in_u_cntr_joint_imp.K_theta=p_cntr.joint_imp.K_theta;
    m_in_u_cntr_joint_imp.D_theta=p_cntr.joint_imp.xi_theta;

    m_cntr_joint_imp.initialize(m_in_u_cntr_joint_imp,in_p_cntr_joint_imp);
}

void JointTorqueControllerPipeline::input_cntr_joint_imp(const Percept &p){
    m_in_u_cntr_joint_imp.theta=p.proprioception.q;
    m_in_u_cntr_joint_imp.theta_d=p.proprioception.q;
    m_in_u_cntr_joint_imp.dtheta=p.proprioception.dq;
    m_in_u_cntr_joint_imp.dtheta_d<<0,0,0,0,0,0,0;
    m_in_u_cntr_joint_imp.ddtheta_d<<0,0,0,0,0,0,0;
    m_in_u_cntr_joint_imp.M=p.internal_model.M;
    m_in_u_cntr_joint_imp.tau_ff.setZero();

}

void JointTorqueControllerPipeline::initialize_cntr_mux(const Percept &p,Memory* memory){
    cntr_mux::In_P_cntr_mux in_p_mux;
    const LimitParameters& p_limits=memory->read_parameters()->limits;

    in_p_mux.dtau_max=p_limits.joint_space.dtau_J_max;
    in_p_mux.tau_max=p_limits.joint_space.tau_J_max;

    input_cntr_mux(p);

    m_cntr_mux.initialize(m_in_u_mux,in_p_mux);
}

void JointTorqueControllerPipeline::input_cntr_mux(const Percept &p){
    m_in_u_mux.B_J_EE=p.internal_model.B_J_EE;
    m_in_u_mux.tau_J_d<<0,0,0,0,0,0,0;
}

void JointTorqueControllerPipeline::initialize_virt_cube(const Percept &p,Memory* memory){
    virtual_cube::In_P_virtual_cube in_p_virt_cube;
    const ControlParameters& p_cntr=memory->read_parameters()->control;
    in_p_virt_cube.damping_distance=p_cntr.virtual_cube.damping_dist;
    in_p_virt_cube.damping_factor=p_cntr.virtual_cube.damping;
    in_p_virt_cube.eta=p_cntr.virtual_cube.eta;
    in_p_virt_cube.rho_min=p_cntr.virtual_cube.rho_min;
    in_p_virt_cube.cube_walls=p_cntr.virtual_cube.walls;
    in_p_virt_cube.f_max=p_cntr.virtual_cube.f_max;

    m_virt_cube_distances=p_cntr.virtual_cube.walls;

    input_virt_cube(p);

    m_virt_cube.initialize(m_in_u_virt_cube,in_p_virt_cube);
}

void JointTorqueControllerPipeline::input_virt_cube(const Percept &p){
    m_in_u_virt_cube.dx_EE=p.proprioception.O_dX_EE;
    m_in_u_virt_cube.p_EE=p.proprioception.O_T_EE.block<3,1>(0,3);
    m_in_u_virt_cube.Jacobian_EE=p.internal_model.B_J_O;
}

void JointTorqueControllerPipeline::initialize_virt_walls_joint(const Percept &p,Memory* memory){
    virtual_walls_joint::In_P_virtual_walls_joint in_p_virt_walls_joint;
    const ControlParameters& p_cntr=memory->read_parameters()->control;
    in_p_virt_walls_joint.damping_distance=p_cntr.virtual_joint_walls.damping_dist;
    in_p_virt_walls_joint.damping_factor=p_cntr.virtual_joint_walls.damping;
    in_p_virt_walls_joint.eta=p_cntr.virtual_joint_walls.eta;
    in_p_virt_walls_joint.rho_min=p_cntr.virtual_joint_walls.rho_min;
    in_p_virt_walls_joint.tau_max=p_cntr.virtual_joint_walls.tau_max;
    in_p_virt_walls_joint.walls=p_cntr.virtual_joint_walls.walls;

    m_virt_joint_walls_distances=p_cntr.virtual_joint_walls.walls;

    input_virt_joint_walls(p);

    m_virt_walls_joint.initialize(m_in_u_virt_walls_joint,in_p_virt_walls_joint);
}

void JointTorqueControllerPipeline::input_virt_joint_walls(const Percept &p){
    m_in_u_virt_walls_joint.dq=p.proprioception.dq;
    m_in_u_virt_walls_joint.q=p.proprioception.q;
}

bool JointTorqueControllerPipeline::is_virt_cube_valid(const Percept& p){
    std::array<bool,3> in_cube={false,false,false};
    bool safe_activation=true;
    for(unsigned i=0;i<6;i++){
        if(fabs(m_out_y_virt_cube.wall_flag(i))>0){
            safe_activation=false;
            break;
        }
    }
    for(unsigned i=0;i<3;i++){
        if(p.proprioception.O_T_EE(i,3)>m_virt_cube_distances(i*2) || p.proprioception.O_T_EE(i,3)<m_virt_cube_distances(i*2+1)){
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

bool JointTorqueControllerPipeline::is_virt_joint_walls_valid(const Percept& p){
    std::array<bool,7> in_walls={false,false,false,false,false,false,false};

    bool safe_activation=true;
    for(unsigned i=0;i<7;i++){
        if(fabs(m_out_y_virt_walls_joint.wall_flag(i))>0){
            safe_activation=false;
            break;
        }
    }
    for(unsigned i=0;i<7;i++){
        if(p.proprioception.q(i)>m_virt_joint_walls_distances(i*2) || p.proprioception.q(i)<m_virt_joint_walls_distances(i*2+1)){
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
