#include "primitives/mp_basic_joint.hpp"

namespace mios {

mp_basic_joint::mp_basic_joint():ManipulationPrimitive("mp_basic_joint"){
    this->_eval = std::make_shared<EvalMP_mp_basic_joint>();
    this->_config = std::make_shared<ConfigMP_mp_basic_joint>();
    this->_attractor= std::make_shared<AttractorBasicJoint>();
}

mp_basic_joint::~mp_basic_joint(){

}

void mp_basic_joint::initialize(const Percept &p_0, const std::shared_ptr<ConfigUser> config){
    this->_flag_init=false;

    std::shared_ptr<AttractorBasicJoint> attr = std::static_pointer_cast<AttractorBasicJoint>(this->_attractor);
    std::shared_ptr<ConfigMP_mp_basic_joint> c_mp = std::static_pointer_cast<ConfigMP_mp_basic_joint>(this->_config);

    this->_mogen_p2p_joint_in_p.dq_max<<c_mp->dq_d(0);
    this->_mogen_p2p_joint_in_p.ddq_max<<c_mp->ddq_d(0);

    this->_mogen_p2p_joint_in_p.q_0=p_0.q;
    this->_mogen_p2p_joint_in_p.q_g=attr->attr_pose;
    this->_mogen_p2p_joint.initialize(this->_mogen_p2p_joint_in_u,this->_mogen_p2p_joint_in_p);

}

CmdMP& mp_basic_joint::step(const Percept &p){
    std::shared_ptr<AttractorBasicJoint> attr = std::static_pointer_cast<AttractorBasicJoint>(this->_attractor);
    std::shared_ptr<ConfigMP_mp_basic_joint> c_mp = std::static_pointer_cast<ConfigMP_mp_basic_joint>(this->_config);

    this->_mogen_p2p_joint.step(this->_mogen_p2p_joint_in_u,this->_mogen_p2p_joint_out_y);

    Eigen::Matrix<double,7,1> dq_d_pose;
    if(attr->attr_pose.isZero(0)){
        dq_d_pose.setZero();
    }else{
        dq_d_pose=this->_mogen_p2p_joint_out_y.dq_d;
    }

    Eigen::Matrix<double,7,1> dq_d_vel=attr->attr_vel;
    for(unsigned i=0;i<7;i++){
        dq_d_vel(i)+=c_mp->dq_fourier_a_a(i)*cos(2*M_PI*c_mp->dq_fourier_a_f(i)*p.time+c_mp->dq_fourier_a_phi(i))+c_mp->dq_fourier_b_a(i)*sin(2*M_PI*c_mp->dq_fourier_b_f(i)*p.time+c_mp->dq_fourier_b_phi(i));
    }

    Eigen::Matrix<double,7,1> tau_ff=attr->attr_ff;
    for(unsigned i=0;i<7;i++){
        tau_ff(i)+=c_mp->ff_fourier_a_a(i)*cos(2*M_PI*c_mp->ff_fourier_a_f(i)*p.time+c_mp->ff_fourier_a_phi(i))+c_mp->ff_fourier_b_a(i)*sin(2*M_PI*c_mp->ff_fourier_b_f(i)*p.time+c_mp->ff_fourier_b_phi(i));
    }

    this->_cmd.dq_d=dq_d_pose+dq_d_vel;
    this->_cmd.tau_ff=tau_ff;
    this->_cmd.q_d=this->_mogen_p2p_joint_out_y.q_d;
//    this->_cmd.TF_F_d=attr->attr_tauc;
    return this->_cmd;
}

void mp_basic_joint::terminate(){
    this->_mogen_p2p_joint.terminate();
}

bool mp_basic_joint::check_attractor(){
    std::shared_ptr<AttractorBasicJoint> attr = std::static_pointer_cast<AttractorBasicJoint>(this->_attractor);
    if(!attr->attr_pose.isZero(0) && !attr->attr_vel.isZero(0)){
        msrm_utils::print_error("MP can not have a pose attractor and a direction attractor at the same time.");
        return false;
    }

    if(!attr->attr_tauc.isZero(0) && !attr->attr_ff.isZero(0)){
        msrm_utils::print_error("MP can not have a contact attractor and a momvement attractor at the same time.");
        return false;
    }
    if(!attr->attr_pose.isZero(0) && !attr->attr_tauc.isZero(0)){
        msrm_utils::print_error("MP can not have a pose attractor and a contact attractor at the same time.");
        return false;
    }
    return true;
}

bool mp_basic_joint::init_attractor(const Percept &p, const std::shared_ptr<ConfigUser> config){
    std::shared_ptr<AttractorBasicJoint> attr = std::static_pointer_cast<AttractorBasicJoint>(this->_attractor);
    attr->neighbourhood_q=config->neighborhood_q;
    attr->neighbourhood_dq=config->neighborhood_dq;
    attr->neighbourhood_tau=config->neighborhood_q;
    attr->neighbourhood_dtau=config->neighborhood_dq;
    return true;
}

bool mp_basic_joint::in_attractor(const Percept &p){
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

    if(in_attr_pose_q && in_attr_pose_dq
            && in_attr_vel_dq
            && this->_mogen_p2p_joint.get_out_l().arrived(0)==1){
        return true;
    }else{
        return false;
    }

}

void mp_basic_joint::setup_logs(unsigned long long length){

}

void mp_basic_joint::write_logs(){

}

}
