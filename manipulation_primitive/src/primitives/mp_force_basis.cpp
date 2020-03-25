#include "primitives/mp_force_basis.hpp"

#include "cpp_utils/math.hpp"

namespace mios {

mp_force_basis::mp_force_basis():ManipulationPrimitive("mp_force_basis"){
    this->_eval = new EvalMP_mp_force_basis();
    this->_config = new ConfigMP_mp_force_basis();
    this->_attractor=new AttractorForceBasis();
}

mp_force_basis::~mp_force_basis(){

}

void mp_force_basis::initialize(const Percept &p_0, const ConfigUser *config){
    this->_flag_init=false;

    AttractorForceBasis* attr = static_cast<AttractorForceBasis*>(this->_attractor);
    ConfigMP_mp_force_basis* c_mp = static_cast<ConfigMP_mp_force_basis*>(this->_config);

    this->_t_0=p_0.time;
    this->_t=0;

    this->_motion_error_u.O_T_EE=p_0.TF_T_EE;
    this->_motion_error_u.O_T_EE_d=attr->attr_pose;

    motion_error_cart::In_P_motion_error_cart motion_error_p;
    this->_motion_error.initialize(this->_motion_error_u,motion_error_p);

}

CmdMP& mp_force_basis::step(const Percept &p){

    AttractorForceBasis* attr = static_cast<AttractorForceBasis*>(this->_attractor);
    ConfigMP_mp_force_basis* c_mp = static_cast<ConfigMP_mp_force_basis*>(this->_config);


    Eigen::Matrix<double,6,1> F_B;
    F_B<<0,0,0,0,0,0;
    for(unsigned i=0;i<6;i++){
        F_B(i)+=c_mp->ff_fourier_a_a(i)*cos(2*M_PI*c_mp->ff_fourier_a_f(i)*this->_t+c_mp->ff_fourier_a_phi(i))+c_mp->ff_fourier_b_a(i)*sin(2*M_PI*c_mp->ff_fourier_b_f(i)*this->_t+c_mp->ff_fourier_b_phi(i));
    }

    this->_motion_error_u.O_T_EE=p.TF_T_EE;
    this->_motion_error_u.O_T_EE_d=attr->attr_pose;

    this->_motion_error.step(this->_motion_error_u,this->_motion_error_y);

    this->_e=this->_motion_error_y.e;
    this->_de=this->_motion_error_y.de;

    Eigen::Matrix<double,6,1> F_h_p;
    Eigen::Matrix<double,6,1> F_h_d;
    Eigen::Matrix<double,6,1> F_h_e;

    for(unsigned i=0;i<6;i++){
        F_h_p(i)=this->_e(i)*c_mp->F_h_p(i);
        F_h_d(i)=this->_de(i)*c_mp->F_h_d(i);
        F_h_e(i)=p.TF_F_ext(i)*c_mp->F_h_e(i);
    }

    this->_cmd.TF_dX_d.setZero();
    this->_cmd.TF_F_d.setZero();
    this->_cmd.TF_F_ff=F_h_p+F_h_d+F_B;

    this->_t+=0.001;
    return this->_cmd;
}

void mp_force_basis::terminate(){
    this->_motion_error.terminate();
}

bool mp_force_basis::check_attractor(){
    AttractorForceBasis* attr = static_cast<AttractorForceBasis*>(this->_attractor);
    if(!attr->attr_pose.isZero(0) && !attr->attr_vel.isZero(0)){
        cpp_utils::print_error("MP can not have a pose attractor and a direction attractor at the same time.");
        return false;
    }

    if(!attr->attr_fc.isZero(0) && !attr->attr_ff.isZero(0)){
        cpp_utils::print_error("MP can not have a contact attractor and a momvement attractor at the same time.");
        return false;
    }
    if(!attr->attr_pose.isZero(0) && !attr->attr_fc.isZero(0)){
        cpp_utils::print_error("MP can not have a pose attractor and a contact attractor at the same time.");
        return false;
    }
    return true;
}

bool mp_force_basis::init_attractor(const Percept &p, const ConfigUser *config){
    AttractorForceBasis* attr = static_cast<AttractorForceBasis*>(this->_attractor);
    attr->neighbourhood_X=config->neighborhood_X;
    attr->neighbourhood_dX=config->neighborhood_dX;
    attr->neighbourhood_F=config->neighborhood_F;
    attr->neighbourhood_dF=config->neighborhood_dF;
    return true;
}

bool mp_force_basis::in_attractor(const Percept &p){
    AttractorForceBasis* attr = static_cast<AttractorForceBasis*>(this->_attractor);
    bool in_attr_pose_x=true;
    bool in_attr_pose_phi=true;
    bool in_attr_pose_dx=true;
    bool in_attr_pose_dphi=true;
    if(sqrt(pow(attr->attr_pose(0,3)-p.TF_T_EE(0,3),2)+pow(attr->attr_pose(1,3)-p.TF_T_EE(1,3),2)+pow(attr->attr_pose(2,3)-p.TF_T_EE(2,3),2))>attr->neighbourhood_X(0)){
        in_attr_pose_x=false;
    }
    if(sqrt(pow(p.TF_dX(0),2)+pow(p.TF_dX(1),2)+pow(p.TF_dX(2),2))>attr->neighbourhood_dX(0)){
        in_attr_pose_dx=false;
    }

    bool in_attr_vel_dx=true;
    bool in_attr_vel_dphi=true;
    if(sqrt(pow(p.TF_dX(0)-attr->attr_vel(0),2)+pow(p.TF_dX(1)-attr->attr_vel(1),2)+pow(p.TF_dX(2)-attr->attr_vel(2),2))>attr->neighbourhood_dX(0)){
        in_attr_vel_dx=false;
    }
    if(sqrt(pow(p.TF_dX(3)-attr->attr_vel(3),2)+pow(p.TF_dX(4)-attr->attr_vel(4),2)+pow(p.TF_dX(5)-attr->attr_vel(5),2))>attr->neighbourhood_dX(1)){
        in_attr_vel_dphi=false;
    }
    bool in_attr_fc_x=true;
    bool in_attr_fc_phi=true;
    bool in_attr_fc_dx=true;
    bool in_attr_fc_dphi=true;

    if(sqrt(pow(p.TF_F_ext(0)-attr->attr_fc(0),2)+pow(p.TF_F_ext(1)-attr->attr_fc(1),2)+pow(p.TF_F_ext(2)-attr->attr_fc(2),2))>attr->neighbourhood_F(0)){
        in_attr_fc_x=false;
    }
    if(sqrt(pow(p.TF_F_ext(3)-attr->attr_fc(3),2)+pow(p.TF_F_ext(4)-attr->attr_fc(4),2)+pow(p.TF_F_ext(5)-attr->attr_fc(5),2))>attr->neighbourhood_F(1)){
        in_attr_fc_phi=false;
    }
    if(sqrt(pow(p.TF_dF_ext(0),2)+pow(p.TF_dF_ext(1),2)+pow(p.TF_dF_ext(2),2))>attr->neighbourhood_dF(0)){
        in_attr_fc_dx=false;
    }
    if(sqrt(pow(p.TF_dF_ext(3),2)+pow(p.TF_dF_ext(4),2)+pow(p.TF_dF_ext(5),2))>attr->neighbourhood_dF(1)){
        in_attr_fc_dphi=false;
    }

    bool in_attr_ff_x=true;
    bool in_attr_ff_phi=true;

    if(sqrt(pow(p.TF_F_ff(0)-attr->attr_ff(0),2)+pow(p.TF_F_ff(1)-attr->attr_ff(1),2)+pow(p.TF_F_ff(2)-attr->attr_ff(2),2))>attr->neighbourhood_F(0)){
        in_attr_ff_x=false;
    }
    if(sqrt(pow(p.TF_F_ff(3)-attr->attr_ff(3),2)+pow(p.TF_F_ff(4)-attr->attr_ff(4),2)+pow(p.TF_F_ff(5)-attr->attr_ff(5),2))>attr->neighbourhood_F(1)){
        in_attr_ff_phi=false;
    }

    //    std::cout<<"ARRIVED: "<<this->_mogen_p2p.get_out_l().arrived(0)<<std::endl;
    if(in_attr_pose_x && in_attr_pose_phi && in_attr_pose_dx && in_attr_pose_dphi
            && in_attr_vel_dx && in_attr_vel_dphi
            && in_attr_fc_x && in_attr_fc_phi && in_attr_fc_dx && in_attr_fc_dphi
            && in_attr_ff_x && in_attr_ff_phi){
        return true;
    }else{
        return false;
    }
}

void mp_force_basis::setup_logs(unsigned long long length){

}

void mp_force_basis::write_logs(){

}

}
