#include "primitives/mp_basic_joint.hpp"

#include "memory/memory.hpp"

namespace mios {

MPParametersBasicJointMP::MPParametersBasicJointMP(){
    dq_d<<0;
    ddq_d<<0;

    dq_fourier_a_a.setZero();
    dq_fourier_b_a.setZero();
    dq_fourier_a_f.setZero();
    dq_fourier_b_f.setZero();
    dq_fourier_a_phi.setZero();
    dq_fourier_b_phi.setZero();

    ff_fourier_a_a.setZero();
    ff_fourier_b_a.setZero();
    ff_fourier_a_f.setZero();
    ff_fourier_b_f.setZero();
    ff_fourier_a_phi.setZero();
    ff_fourier_b_phi.setZero();
}

BasicJointAttractor::BasicJointAttractor(){
    attr_pose.setZero();
    attr_vel.setZero();
    attr_tauc.setZero();
    attr_ff.setZero();

    neighbourhood_q<<std::numeric_limits<double>::max();
    neighbourhood_dq<<std::numeric_limits<double>::max();
    neighbourhood_tau<<std::numeric_limits<double>::max();
    neighbourhood_dtau<<std::numeric_limits<double>::max();
}

bool BasicJointAttractor::reached(const Percept &p){
    //    AttractorBasicJoint* attr = static_cast<AttractorBasicJoint*>(this->_attractor);
    bool in_attr_pose_q=true;
    bool in_attr_pose_dq=true;
    //    if(sqrt(pow(attr->attr_pose(0,3)-p.TF_T_EE(0,3),2)+pow(attr->attr_pose(1,3)-p.TF_T_EE(1,3),2)+pow(attr->attr_pose(2,3)-p.TF_T_EE(2,3),2))>attr->neighbourhood_X(0)){
    //        in_attr_pose_x=false;
    //    }
    //    if(sqrt(pow(p.TF_dX(0),2)+pow(p.TF_dX(1),2)+pow(p.TF_dX(2),2))>attr->neighbourhood_dX(0)){
    //        in_attr_pose_dx=false;
    //    }

    bool in_attr_vel_dq=true;
    //    bool in_attr_vel_dphi=true;
    //    if(sqrt(pow(p.TF_dX(0)-attr->attr_vel(0),2)+pow(p.TF_dX(1)-attr->attr_vel(1),2)+pow(p.TF_dX(2)-attr->attr_vel(2),2))>attr->neighbourhood_dX(0)){
    //        in_attr_vel_dx=false;
    //    }
    //    if(sqrt(pow(p.TF_dX(3)-attr->attr_vel(3),2)+pow(p.TF_dX(4)-attr->attr_vel(4),2)+pow(p.TF_dX(5)-attr->attr_vel(5),2))>attr->neighbourhood_dX(1)){
    //        in_attr_vel_dphi=false;
    //    }
    //    bool in_attr_fc_x=true;
    //    bool in_attr_fc_phi=true;
    //    bool in_attr_fc_dx=true;
    //    bool in_attr_fc_dphi=true;

    //    if(sqrt(pow(p.TF_F_ext(0)-attr->attr_fc(0),2)+pow(p.TF_F_ext(1)-attr->attr_fc(1),2)+pow(p.TF_F_ext(2)-attr->attr_fc(2),2))>attr->neighbourhood_F(0)){
    //        in_attr_fc_x=false;
    //    }
    //    if(sqrt(pow(p.TF_F_ext(3)-attr->attr_fc(3),2)+pow(p.TF_F_ext(4)-attr->attr_fc(4),2)+pow(p.TF_F_ext(5)-attr->attr_fc(5),2))>attr->neighbourhood_F(1)){
    //        in_attr_fc_phi=false;
    //    }
    //    if(sqrt(pow(p.TF_dF_ext(0),2)+pow(p.TF_dF_ext(1),2)+pow(p.TF_dF_ext(2),2))>attr->neighbourhood_dF(0)){
    //        in_attr_fc_dx=false;
    //    }
    //    if(sqrt(pow(p.TF_dF_ext(3),2)+pow(p.TF_dF_ext(4),2)+pow(p.TF_dF_ext(5),2))>attr->neighbourhood_dF(1)){
    //        in_attr_fc_dphi=false;
    //    }

    //    bool in_attr_ff_x=true;
    //    bool in_attr_ff_phi=true;

    //    if(sqrt(pow(p.TF_F_ff(0)-attr->attr_ff(0),2)+pow(p.TF_F_ff(1)-attr->attr_ff(1),2)+pow(p.TF_F_ff(2)-attr->attr_ff(2),2))>attr->neighbourhood_F(0)){
    //        in_attr_ff_x=false;
    //    }
    //    if(sqrt(pow(p.TF_F_ff(3)-attr->attr_ff(3),2)+pow(p.TF_F_ff(4)-attr->attr_ff(4),2)+pow(p.TF_F_ff(5)-attr->attr_ff(5),2))>attr->neighbourhood_F(1)){
    //        in_attr_ff_phi=false;
    //    }

    if(motion_generator_finished){
        return true;
    }else{
        return false;
    }
}

BasicJointPrimitive::BasicJointPrimitive(const std::string &name, const Percept &p_0, std::shared_ptr<MPParameters> parameters, std::shared_ptr<Attractor> attractor, Memory *memory):
    ManipulationPrimitive("BasicJointPrimitive",name,p_0,parameters,attractor,memory){
}

void BasicJointPrimitive::i_initialize(const Percept &p_0){

    std::shared_ptr<BasicJointAttractor> attr = get_attractor<BasicJointAttractor>();
    std::shared_ptr<MPParametersBasicJointMP> c_mp = get_parameters<MPParametersBasicJointMP>();

    mogen_p2p_joint::In_P_mogen_p2p_joint mogen_p2p_joint_in_p;

    mogen_p2p_joint_in_p.dq_max<<c_mp->dq_d(0);
    mogen_p2p_joint_in_p.ddq_max<<c_mp->ddq_d(0);

    mogen_p2p_joint_in_p.q_0=p_0.proprioception.q;
    mogen_p2p_joint_in_p.q_g=attr->attr_pose;
    m_mogen_p2p_joint.initialize(m_mogen_p2p_joint_in_u,mogen_p2p_joint_in_p);
}

Actuator* BasicJointPrimitive::step(const Percept &p){
    std::shared_ptr<BasicJointAttractor> attr = get_attractor<BasicJointAttractor>();
    std::shared_ptr<MPParametersBasicJointMP> c_mp = get_parameters<MPParametersBasicJointMP>();

    m_mogen_p2p_joint.step(m_mogen_p2p_joint_in_u,m_mogen_p2p_joint_out_y);

    Eigen::Matrix<double,7,1> dq_d_pose;
    if(attr->attr_pose.isZero(0)){
        dq_d_pose.setZero();
    }else{
        dq_d_pose=m_mogen_p2p_joint_out_y.dq_d;
    }

    Eigen::Matrix<double,7,1> dq_d_vel=attr->attr_vel;
    double t=std::chrono::duration_cast<std::chrono::seconds>(p.time-m_memory->get_live_context()->t_mp).count();
    for(unsigned i=0;i<7;i++){
        dq_d_vel(i)+=c_mp->dq_fourier_a_a(i)*cos(2*M_PI*c_mp->dq_fourier_a_f(i)*t+c_mp->dq_fourier_a_phi(i))+c_mp->dq_fourier_b_a(i)*sin(2*M_PI*c_mp->dq_fourier_b_f(i)*t+c_mp->dq_fourier_b_phi(i));
    }

    Eigen::Matrix<double,7,1> tau_ff=attr->attr_ff;
    for(unsigned i=0;i<7;i++){
        tau_ff(i)+=c_mp->ff_fourier_a_a(i)*cos(2*M_PI*c_mp->ff_fourier_a_f(i)*t+c_mp->ff_fourier_a_phi(i))+c_mp->ff_fourier_b_a(i)*sin(2*M_PI*c_mp->ff_fourier_b_f(i)*t+c_mp->ff_fourier_b_phi(i));
    }

    m_cmd.dq_d=dq_d_pose+dq_d_vel;
    m_cmd.tau_ff=tau_ff;
    m_cmd.q_d=m_mogen_p2p_joint_out_y.q_d;
    //    this->_cmd.TF_F_d=attr->attr_tauc;
    return &m_cmd;
}

void BasicJointPrimitive::i_terminate(){
    m_mogen_p2p_joint.terminate();
}

}
