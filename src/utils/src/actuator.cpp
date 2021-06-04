#include "data_structures/actuator.hpp"
#include <spdlog/spdlog.h>
#include <msrm_cpp_utils/math.hpp>

namespace mios {

Actuator::Actuator(const Percept &p_0, const ControlParameters& controller){
    spdlog::debug("Actuator:Constructor");
    initialize(p_0, controller, Eigen::Matrix<double,3,3>::Identity());
}

void Actuator::initialize(const Percept &p_0, const ControlParameters& controller, Eigen::Matrix<double, 3, 3> O_R_T_0){
    TF_T_EE_d=p_0.proprioception.T_T_EE;
    TF_dX_d.setZero();
    q_d_nullspace=p_0.proprioception.q;
    TF_F_d.setZero();
    TF_F_ff.setZero();
    K_x=controller.cart_imp.K_x;
    xi_x=controller.cart_imp.xi_x;
    O_R_T=O_R_T_0;

    q_d=p_0.proprioception.q;
    dq_d.setZero();
    tau_d.setZero();
    tau_ff.setZero();
    K_theta=controller.joint_imp.K_theta;
    xi_theta=controller.joint_imp.xi_theta;

    refresh_limiter();
    write_to_buffer();

    m_stop=false;
    m_stop_factor=1;

    m_new_command=true;

    gripper_width=0;
    gripper_speed=0;
    gripper_force=0;
    gripper_object="NullObject";

    gripper_request=GripperRequest::None;
}

void Actuator::blend(const Actuator &cmd, const Percept& p){
    spdlog::debug("Actuator::blend(cmd,p)");
    TF_T_EE_d=p.controller.TF_T_EE_d;
    TF_dX_d=cmd.TF_dX_d;
    q_d_nullspace=cmd.q_d_nullspace;
    TF_F_d=cmd.TF_F_d;
    TF_F_ff=cmd.TF_F_ff;
    K_x=cmd.K_x;
    xi_x=cmd.xi_x;
    O_R_T=cmd.O_R_T;

    q_d=p.controller.q_d;
    dq_d=cmd.dq_d;
    tau_d=cmd.tau_d;
    tau_ff=cmd.tau_ff;
    K_theta=cmd.K_theta;
    xi_theta=cmd.xi_theta;

    m_TF_T_EE_d_buffer=cmd.m_TF_T_EE_d_buffer;
    m_TF_dX_d_buffer=cmd.m_TF_dX_d_buffer;
    m_q_d_nullspace_buffer=cmd.m_q_d_nullspace_buffer;
    m_TF_F_d_buffer=cmd.m_TF_F_d_buffer;
    m_TF_F_ff_buffer=cmd.m_TF_F_ff_buffer;
    m_K_x_buffer=cmd.m_K_x_buffer;
    m_xi_x_buffer=cmd.m_xi_x_buffer;
    m_O_R_T_buffer=cmd.m_O_R_T_buffer;

    m_q_d_buffer=cmd.m_q_d_buffer;
    m_dq_d_buffer=cmd.m_dq_d_buffer;
    m_tau_d_buffer=cmd.m_tau_d_buffer;
    m_tau_ff_buffer=cmd.m_tau_ff_buffer;
    m_K_theta_buffer=cmd.m_K_theta_buffer;
    m_xi_theta_buffer=cmd.m_xi_theta_buffer;

    m_TF_T_EE_d_limiter=cmd.m_TF_T_EE_d_limiter;
    m_TF_dX_d_limiter=cmd.m_TF_dX_d_limiter;
    m_q_d_nullspace_limiter=cmd.m_q_d_nullspace_limiter;
    m_TF_F_d_limiter=cmd.m_TF_F_d_limiter;
    m_TF_F_ff_limiter=cmd.m_TF_F_ff_limiter;
    m_K_x_limiter=cmd.m_K_x_limiter;
    m_xi_x_limiter=cmd.m_xi_x_limiter;
    m_O_R_T_limiter=cmd.m_O_R_T_limiter;

    m_q_d_limiter=cmd.m_q_d_limiter;
    m_dq_d_limiter=cmd.m_dq_d_limiter;
    m_tau_d_limiter=cmd.m_tau_d_limiter;
    m_tau_ff_limiter=cmd.m_tau_ff_limiter;
    m_K_theta_limiter=cmd.m_K_theta_limiter;
    m_xi_theta_limiter=cmd.m_xi_theta_limiter;

    if(m_command_pattern!=*cmd.get_command_pattern()){
        refresh_limiter();
    }

}

void Actuator::stop(){
    m_stop=true;
}

void Actuator::read_from_buffer(){
    TF_T_EE_d=m_TF_T_EE_d_buffer;
    TF_dX_d=m_TF_dX_d_buffer;
    q_d_nullspace=m_q_d_nullspace_buffer;
    TF_F_d=m_TF_F_d_buffer;
    TF_F_ff=m_TF_F_ff_buffer;
    K_x=m_K_x_buffer;
    xi_x=m_xi_x_buffer;
    O_R_T=m_O_R_T_buffer;

    q_d=m_q_d_buffer;
    dq_d=m_dq_d_buffer;
    tau_d=m_tau_d_buffer;
    tau_ff=m_tau_ff_buffer;
    K_theta=m_K_theta_buffer;
    xi_theta=m_xi_theta_buffer;
}

void Actuator::refresh_limiter(){
    m_TF_T_EE_d_limiter=TF_T_EE_d;
    m_TF_dX_d_limiter=TF_dX_d;
    m_q_d_nullspace_limiter=q_d_nullspace;
    m_TF_F_d_limiter=TF_F_d;
    m_TF_F_ff_limiter=TF_F_ff;
    m_K_x_limiter=K_x;
    m_xi_x_limiter=xi_x;
    m_O_R_T_limiter=O_R_T;

    m_q_d_limiter=q_d;
    m_dq_d_limiter=dq_d;
    m_tau_d_limiter=tau_d;
    m_tau_ff_limiter=tau_ff;
    m_K_theta_limiter=K_theta;
    m_xi_theta_limiter=xi_theta;
}

void Actuator::write_to_buffer(){
    m_TF_T_EE_d_buffer=TF_T_EE_d;
    m_TF_dX_d_buffer=TF_dX_d;
    m_q_d_nullspace_buffer=q_d_nullspace;
    m_TF_F_d_buffer=TF_F_d;
    m_TF_F_ff_buffer=TF_F_ff;
    m_K_x_buffer=K_x;
    m_xi_x_buffer=xi_x;
    m_O_R_T_buffer=O_R_T;

    m_q_d_buffer=q_d;
    m_dq_d_buffer=dq_d;
    m_tau_d_buffer=tau_d;
    m_tau_ff_buffer=tau_ff;
    m_K_theta_buffer=K_theta;
    m_xi_theta_buffer=xi_theta;
}

void Actuator::limit_output(const LimitParameters &parameters){
    for(unsigned i=0;i<7;i++){
        if(q_d[i]>parameters.joint_space.q_upper(i)){
            q_d[i]=parameters.joint_space.q_upper(i);
        }
        if(q_d[i]<parameters.joint_space.q_lower(i)){
            q_d[i]=parameters.joint_space.q_lower(i);
        }
    }
    for(unsigned i=0;i<7;i++){
        if(q_d_nullspace[i]>parameters.joint_space.q_upper(i)){
            q_d_nullspace[i]=parameters.joint_space.q_upper(i);
        }
        if(q_d_nullspace[i]<parameters.joint_space.q_lower(i)){
            q_d_nullspace[i]=parameters.joint_space.q_lower(i);
        }
    }

    // Check for joint velocity limits
    for(unsigned i=0;i<7;i++){
        if(dq_d(i)>parameters.joint_space.dq_max(i)){
            dq_d(i)=parameters.joint_space.dq_max(i);
        }
        if(dq_d(i)<-parameters.joint_space.dq_max(i)){
            dq_d(i)=-parameters.joint_space.dq_max(i);
        }
    }

    // Check for joint stiffness limits
    for(unsigned i=0;i<7;i++){
        if(K_theta(i)>parameters.joint_space.K_theta_max(i)){
            K_theta(i)=parameters.joint_space.K_theta_max(i);
        }
        if(K_theta(i)<0){
            K_theta(i)=0;
        }
        if(xi_theta(i)>parameters.joint_space.xi_theta_max(i)){
            xi_theta(i)=parameters.joint_space.xi_theta_max(i);
        }
        if(xi_theta(i)<0){
            xi_theta(i)=0;
        }
    }

    // Check for Cartesian pose limits
    for(unsigned i=0;i<3;i++){
        if(TF_T_EE_d(i,3)>parameters.cartesian_space.x_upper(i)){
            TF_T_EE_d(i,3)=parameters.cartesian_space.x_upper(i);
        }
        if(TF_T_EE_d(i,3)<parameters.cartesian_space.x_lower(i)){
            TF_T_EE_d(i,3)=parameters.cartesian_space.x_lower(i);
        }
    }

    // Check for Cartesian stiffness limits
    for(unsigned i=0;i<6;i++){
        if(K_x(i)>parameters.cartesian_space.K_x_max(i)){
            K_x(i)=parameters.cartesian_space.K_x_max(i);
        }
        if(K_x(i)<0){
            K_x(i)=0;
        }
        if(xi_x(i)>parameters.cartesian_space.xi_x_max(i)){
            xi_x(i)=parameters.cartesian_space.xi_x_max(i);
        }
        if(xi_x(i)<0){
            xi_x(i)=0;
        }
    }

    // Check for Cartesian velocity limits
    for(unsigned i=0;i<3;i++){
        if(TF_dX_d(i)>parameters.cartesian_space.dX_max(0)){
            TF_dX_d(i)=parameters.cartesian_space.dX_max(0);
        }
        if(TF_dX_d(i)<-parameters.cartesian_space.dX_max(0)){
            TF_dX_d(i)=-parameters.cartesian_space.dX_max(0);
        }
        if(TF_dX_d(i+3)>parameters.cartesian_space.dX_max(1)){
            TF_dX_d(i+3)=parameters.cartesian_space.dX_max(1);
        }
        if(TF_dX_d(i+3)<-parameters.cartesian_space.dX_max(1)){
            TF_dX_d(i+3)=-parameters.cartesian_space.dX_max(1);
        }
    }
}

void Actuator::limit_output_rate(const LimitParameters &parameters){
    for(unsigned i=0;i<3;i++){
        double diff_dX_t = TF_dX_d(i)-m_TF_dX_d_limiter(i);
        double diff_dX_r = TF_dX_d(i+3)-m_TF_dX_d_limiter(i+3);
        double diff_dF_t = TF_F_d(i)-m_TF_F_d_limiter(i);
        double diff_dF_r = TF_F_d(i+3)-m_TF_F_d_limiter(i+3);
        double diff_dF_ff_t = TF_F_ff(i)-m_TF_F_ff_limiter(i);
        double diff_dF_ff_r = TF_F_ff(i+3)-m_TF_F_ff_limiter(i+3);
        if(fabs(diff_dX_t)/0.001>parameters.cartesian_space.ddX_max(0)*m_stop_factor){
            TF_dX_d(i)=m_TF_dX_d_limiter(i)+msrm_utils::sgn(diff_dX_t)*parameters.cartesian_space.ddX_max(0)*0.001*m_stop_factor;
        }
        if(fabs(diff_dX_r)/0.001>parameters.cartesian_space.ddX_max[1]*m_stop_factor){
            TF_dX_d(i+3)=m_TF_dX_d_limiter(i+3)+msrm_utils::sgn(diff_dX_r)*parameters.cartesian_space.ddX_max(1)*0.001*m_stop_factor;
        }
        if(fabs(diff_dF_t)/0.001>parameters.cartesian_space.dF_J_max[0]*m_stop_factor){
            TF_F_d(i)=m_TF_F_d_limiter(i)+msrm_utils::sgn(diff_dF_t)*parameters.cartesian_space.dF_J_max(0)*0.001*m_stop_factor;
        }
        if(fabs(diff_dF_r)/0.001>parameters.cartesian_space.dF_J_max[1]*m_stop_factor){
            TF_F_d(i+3)=m_TF_F_d_limiter(i+3)+msrm_utils::sgn(diff_dF_r)*parameters.cartesian_space.dF_J_max(1)*0.001*m_stop_factor;
        }
        if(fabs(diff_dF_ff_t)/0.001>parameters.cartesian_space.dF_J_max[0]*m_stop_factor){
            TF_F_ff(i)=m_TF_F_ff_limiter(i)+msrm_utils::sgn(diff_dF_ff_t)*parameters.cartesian_space.dF_J_max(0)*0.001*m_stop_factor;
        }
        if(fabs(diff_dF_ff_r)/0.001>parameters.cartesian_space.dF_J_max[1]*m_stop_factor){
            TF_F_ff(i+3)=m_TF_F_ff_limiter(i+3)+msrm_utils::sgn(diff_dF_ff_r)*parameters.cartesian_space.dF_J_max(1)*0.001*m_stop_factor;
        }
    }

    for(unsigned i=0;i<6;i++){
        double diff_K_x = K_x(i)-m_K_x_limiter[i];
        double diff_xi_x = xi_x(i)-m_xi_x_limiter[i];
        if(fabs(diff_K_x)/0.001>parameters.cartesian_space.dK_x_max[i]){
            K_x(i)=m_K_x_limiter(i)+msrm_utils::sgn(diff_K_x)*parameters.cartesian_space.dK_x_max(i)*0.001;
        }
        if(fabs(diff_xi_x)/0.001>parameters.cartesian_space.dxi_x_max[i]){
            xi_x(i)=m_xi_x_limiter(i)+msrm_utils::sgn(diff_xi_x)*parameters.cartesian_space.dxi_x_max(i)*0.001;
        }
    }
    for(unsigned i=0;i<7;i++){
        double diff_q = q_d(i)-m_q_d_limiter(i);
        double diff_q_nullspace = q_d_nullspace(i)-m_q_d_nullspace_limiter(i);
        double diff_dq = dq_d(i)-m_dq_d_limiter(i);
        double diff_tau = tau_d(i)-m_tau_d_limiter(i);
        double diff_tau_ff = tau_ff(i)-m_tau_ff_limiter(i);
        double diff_K_theta = K_theta(i)-m_K_theta_limiter(i);
        double diff_xi_theta = xi_theta(i)-m_xi_theta_limiter(i);
        if(fabs(diff_q)/0.001>parameters.joint_space.dq_max(i)*m_stop_factor){
            q_d(i)=m_q_d_limiter(i)+msrm_utils::sgn(diff_q)*parameters.joint_space.dq_max(i)*0.001*m_stop_factor;
        }
        if(fabs(diff_q_nullspace)/0.001>parameters.joint_space.dq_max(i)*m_stop_factor){
            q_d_nullspace(i)=m_q_d_nullspace_limiter(i)+msrm_utils::sgn(diff_q_nullspace)*parameters.joint_space.dq_max(i)*0.001*m_stop_factor;
        }
        if(fabs(diff_dq)/0.001>parameters.joint_space.ddq_max(i)*m_stop_factor){
            dq_d(i)=m_dq_d_limiter(i)+msrm_utils::sgn(diff_dq)*parameters.joint_space.ddq_max(i)*0.001*m_stop_factor;
        }
        if(fabs(diff_tau)/0.001>parameters.joint_space.tau_J_max(i)*m_stop_factor){
            tau_d(i)=m_tau_d_limiter(i)+msrm_utils::sgn(diff_tau)*parameters.joint_space.tau_J_max(i)*0.001*m_stop_factor;
        }
        if(fabs(diff_tau_ff)/0.001>parameters.joint_space.tau_J_max(i)*m_stop_factor){
            tau_ff(i)=m_tau_ff_limiter(i)+msrm_utils::sgn(diff_tau_ff)*parameters.joint_space.tau_J_max(i)*0.001*m_stop_factor;
        }
        if(fabs(diff_K_theta)/0.001>parameters.joint_space.dK_theta_max(i)){
            K_theta(i)=m_K_theta_limiter(i)+msrm_utils::sgn(diff_K_theta)*parameters.joint_space.dK_theta_max(i)*0.001;
        }
        if(fabs(diff_xi_theta)/0.001>parameters.joint_space.dxi_theta_max(i)){
            xi_theta(i)=m_xi_theta_limiter(i)+msrm_utils::sgn(diff_xi_theta)*parameters.joint_space.dxi_theta_max(i)*0.001;
        }
    }
    refresh_limiter();
}

bool Actuator::is_valid() const{
    for(unsigned i=0;i<7;i++){
        if(q_d(i)!=q_d(i)){
            spdlog::error("Detected NaN in skill command at q_d["+std::to_string(i)+"].");
            return false;
        }
        if(q_d_nullspace(i)!=q_d_nullspace(i)){
            spdlog::error("Detected NaN in skill command at q_d_nullspace["+std::to_string(i)+"].");
            return false;
        }
        if(dq_d(i)!=dq_d(i)){
            spdlog::error("Detected NaN in skill command at dq_d["+std::to_string(i)+"].");
            return false;
        }
        if(tau_d(i)!=tau_d(i)){
            spdlog::error("Detected NaN in skill command at tau_d["+std::to_string(i)+"].");
            return false;
        }
        if(tau_ff(i)!=tau_ff(i)){
            spdlog::error("Detected NaN in skill command at tau_ff["+std::to_string(i)+"].");
            return false;
        }
        if(K_theta(i)!=K_theta(i)){
            spdlog::error("Detected NaN in skill command at K_theta["+std::to_string(i)+"].");
            return false;
        }
        if(xi_theta(i)!=xi_theta(i)){
            spdlog::error("Detected NaN in skill command at xi_theta["+std::to_string(i)+"].");
            return false;
        }
    }
    for(unsigned i=0;i<6;i++){
        if(TF_dX_d(i)!=TF_dX_d(i)){
            spdlog::error("Detected NaN in skill command at TF_dX_d["+std::to_string(i)+"].");
            return false;
        }
        if(TF_F_d(i)!=TF_F_d(i)){
            spdlog::error("Detected NaN in skill command at TF_F_d["+std::to_string(i)+"].");
            return false;
        }
        if(TF_F_ff(i)!=TF_F_ff(i)){
            spdlog::error("Detected NaN in skill command at TF_F_ff["+std::to_string(i)+"].");
            return false;
        }
        if(K_x(i)!=K_x(i)){
            spdlog::error("Detected NaN in skill command at K_x["+std::to_string(i)+"].");
            return false;
        }
        if(xi_x(i)!=xi_x(i)){
            spdlog::error("Detected NaN in skill command at xi_x["+std::to_string(i)+"].");
            return false;
        }
    }
    for(unsigned i=0;i<4;i++){
        for(unsigned j=0;j<4;j++){
            if(TF_T_EE_d(i)!=TF_T_EE_d(i)){
                spdlog::error("Detected NaN in skill command at TF_T_EE_d["+std::to_string(i)+","+std::to_string(j)+"].");
                return false;
            }
        }
    }
    if(!msrm_utils::is_orthonormal(TF_T_EE_d.block<3,3>(0,0))){
        spdlog::error("Rotation part of TF_T_EE_d is not orthonormal.");
        return false;
    }
    return true;
}

bool Actuator::is_stopped() const{
    return m_stop;
}

bool Actuator::is_settled(const LimitParameters &parameters, bool ignore) const{
    if(ignore){
        return true;
    }
    bool all_zero=true;
    for(unsigned i=0;i<7;i++){
        if(fabs(dq_d(i))>parameters.joint_space.ddq_max(0)/1000*m_stop_factor ||
                fabs(tau_d(i))>parameters.joint_space.dtau_J_max(0)/1000*m_stop_factor ||
                fabs(tau_ff(i))>parameters.joint_space.dtau_J_max(0)/1000*m_stop_factor){
            all_zero=false;
            break;
        }
    }
    for(unsigned i=0;i<3;i++){
        if(fabs(TF_dX_d(i))>parameters.cartesian_space.ddX_max(0)/1000*m_stop_factor ||
                fabs(TF_F_d(i))>parameters.cartesian_space.dF_J_max(0)/1000*m_stop_factor ||
                fabs(TF_F_ff(i))>parameters.cartesian_space.dF_J_max(0)/1000*m_stop_factor){
            all_zero=false;
            break;
        }
    }
    for(unsigned i=3;i<6;i++){
        if(fabs(TF_dX_d(i))>parameters.cartesian_space.ddX_max(1)/1000*m_stop_factor ||
                fabs(TF_F_d(i))>parameters.cartesian_space.dF_J_max(1)/1000*m_stop_factor ||
                fabs(TF_F_ff(i))>parameters.cartesian_space.dF_J_max(1)/1000*m_stop_factor){
            all_zero=false;
            break;
        }
    }
    return all_zero;
}

void Actuator::set_zero(const Percept &p_0){
    TF_T_EE_d=p_0.proprioception.T_T_EE;
    TF_dX_d.setZero();
    TF_F_d.setZero();
    TF_F_ff.setZero();
    K_x=p_0.controller.K_x;
    xi_x=p_0.controller.xi_x;

    q_d_nullspace=p_0.proprioception.q;
    q_d=p_0.proprioception.q;
    dq_d.setZero();
    tau_d.setZero();
    tau_ff.setZero();
    K_theta=p_0.controller.K_theta;
    xi_theta=p_0.controller.xi_theta;

//    O_R_T.setIdentity();
}

void Actuator::set_stop_factor(double stop_factor){
    m_stop_factor=stop_factor;
    if(m_stop_factor>1){
        m_stop_factor=1;
    }
    if(m_stop_factor<0.01){
        m_stop_factor=0.01;
    }
}

bool Actuator::is_new(){
    if(m_new_command){
        m_new_command=false;
        return true;
    }else{
        return false;
    }
}

void Actuator::set_command_pattern(const std::set<CommandPattern> &command_pattern){
    m_command_pattern=command_pattern;
}

const std::set<CommandPattern>* Actuator::get_command_pattern() const{
    return &m_command_pattern;
}

void Actuator::grasp(double width, double speed, double force, std::string object){
    gripper_width=width;
    gripper_speed=speed;
    gripper_force=force;
    gripper_object=object;
    gripper_request=GripperRequest::Grasp;
}

void Actuator::move_fingers(double width, double speed){
    gripper_width=width;
    gripper_speed=speed;
    gripper_request=GripperRequest::Move;
}

void Actuator::accecpt_gripper_request(){
    gripper_request=GripperRequest::None;
}

GripperRequest Actuator::get_gripper_request(){
    return gripper_request;
}

}
