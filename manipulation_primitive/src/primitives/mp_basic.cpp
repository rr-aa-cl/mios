#include "primitives/mp_basic.hpp"

#include "cpp_utils/math.hpp"

namespace mios {

mp_basic::mp_basic():ManipulationPrimitive("mp_basic"){
    this->_eval = std::make_shared<EvalMP_mp_basic>();
    this->_config = std::make_shared<ConfigMP_mp_basic>();
    this->_attractor= std::make_shared<AttractorBasic>();
}

void mp_basic::initialize(const Percept &p_0, const std::shared_ptr<ConfigUser> config){
    this->_flag_init=false;
    this->_flag_mg_init=false;

    std::shared_ptr<AttractorBasic> attr = std::static_pointer_cast<AttractorBasic>(this->_attractor);
    std::shared_ptr<ConfigMP_mp_basic> c_mp = std::static_pointer_cast<ConfigMP_mp_basic>(this->_config);

    for(unsigned i=0;i<6;i++){
        this->_X_d_vel_old(i)=c_mp->dX_fourier_a_a(i)*cos(2*M_PI*c_mp->dX_fourier_a_f(i)*0+c_mp->dX_fourier_a_phi(i))+c_mp->dX_fourier_b_a(i)*sin(2*M_PI*c_mp->dX_fourier_b_f(i)*0+c_mp->dX_fourier_b_phi(i));
    }

//    if(!attr->attr_pose.isZero(0) && (c_mp->dX_d(0)==0 || c_mp->dX_d(1)==0)){
//        cpp_utils::print_warning("Cartesian velocities have been set to zero but a pose has been given.");
//    }

    this->_mogen_p2p_in_p.dX_max<<c_mp->dX_d(0),c_mp->dX_d(1);
    this->_mogen_p2p_in_p.ddX_max<<c_mp->ddX_d(0),c_mp->ddX_d(1);

    this->_mogen_p2p_in_p.TF_T_EE_0=p_0.TF_T_EE;
    this->_mogen_p2p_in_p.TF_T_EE_1=attr->attr_pose;
    this->_mogen_p2p.initialize(this->_mogen_p2p_in_u,this->_mogen_p2p_in_p);
    this->_flag_mg_init=true;

    this->_motion_error_u.O_T_EE=p_0.TF_T_EE;
    this->_motion_error_u.O_T_EE_d=attr->attr_pose;

    motion_error_cart::In_P_motion_error_cart motion_error_p;
    this->_motion_error.initialize(this->_motion_error_u,motion_error_p);

    this->_t_0=p_0.time;
    this->_t=0;

}

CmdMP& mp_basic::step(const Percept &p){

    std::shared_ptr<AttractorBasic> attr = std::static_pointer_cast<AttractorBasic>(this->_attractor);
    std::shared_ptr<ConfigMP_mp_basic> c_mp = std::static_pointer_cast<ConfigMP_mp_basic>(this->_config);

    Eigen::Matrix<double,3,1> scale_t,scale_r;
    for(unsigned i=0;i<3;i++){
        if(fabs(p.TF_F_ext(i))<c_mp->F_stop(i)-c_mp->DF_stop(i)){
            scale_t(i)=1;
        }else if(fabs(p.TF_F_ext(i))<c_mp->F_stop(i)){
            scale_t(i)=1+1/c_mp->DF_stop(i)*(c_mp->F_stop(i)-c_mp->DF_stop(i))-1/c_mp->DF_stop(i)*fabs(p.TF_F_ext(i));
        }else{
            scale_t(i)=0;
        }
        if(c_mp->F_stop(i)==0){
            scale_t(i)=1;
        }
        if(fabs(p.TF_F_ext(i+3))<c_mp->F_stop(i+3)-c_mp->DF_stop(i+3)){
            scale_r(i)=1;
        }else if(fabs(p.TF_F_ext(i+3))<c_mp->F_stop(i+3)){
            scale_r(i)=1+1/c_mp->DF_stop(i+3)*(c_mp->F_stop(i+3)-c_mp->DF_stop(i+3))-1/c_mp->DF_stop(i+3)*fabs(p.TF_F_ext(i+3));
        }else{
            scale_r(i)=0;
        }
        if(c_mp->F_stop(i+3)==0){
            scale_r(i)=1;
        }
        if(scale_t(i)>1) scale_t(i)=1;
        if(scale_t(i)<0) scale_t(i)=0;
        if(scale_r(i)>1) scale_r(i)=1;
        if(scale_r(i)<0) scale_r(i)=0;
    }

    this->_mogen_p2p_in_u.t_scale<<scale_t.minCoeff(),scale_r.minCoeff();

    this->_mogen_p2p.step(this->_mogen_p2p_in_u,this->_mogen_p2p_out_y);

    Eigen::Matrix<double,6,1> dX_d_pose;
    if(attr->attr_pose.isZero(0)){
        dX_d_pose.setZero();
    }else{
        dX_d_pose=this->_mogen_p2p_out_y.dX_d;
    }

    Eigen::Matrix<double,6,1> dX_d_vel=attr->attr_vel;
    for(unsigned i=0;i<3;i++){
        dX_d_vel(i)*=scale_t.minCoeff();
        dX_d_vel(i+3)*=scale_r.minCoeff();
    }
    for(unsigned i=0;i<6;i++){
        double X_d_vel=c_mp->dX_fourier_a_a(i)*cos(2*M_PI*c_mp->dX_fourier_a_f(i)*this->_t+c_mp->dX_fourier_a_phi(i))+c_mp->dX_fourier_b_a(i)*sin(2*M_PI*c_mp->dX_fourier_b_f(i)*this->_t+c_mp->dX_fourier_b_phi(i));
        //        dX_d_vel(i)+=-c_mp->dX_fourier_a_a(i)*2*M_PI*c_mp->dX_fourier_a_f(i)*sin(2*M_PI*c_mp->dX_fourier_a_f(i)*p.time+c_mp->dX_fourier_a_phi(i))+
        //                c_mp->dX_fourier_b_a(i)*2*M_PI*c_mp->dX_fourier_b_f(i)*cos(2*M_PI*c_mp->dX_fourier_b_f(i)*p.time+c_mp->dX_fourier_b_phi(i));
        dX_d_vel(i)+=(X_d_vel-this->_X_d_vel_old(i))/0.001;
        this->_X_d_vel_old(i)=X_d_vel;
    }

    Eigen::Matrix<double,6,1> F_ff=attr->attr_ff;
    for(unsigned i=0;i<6;i++){
        F_ff(i)+=c_mp->ff_fourier_a_a(i)*cos(2*M_PI*c_mp->ff_fourier_a_f(i)*this->_t+c_mp->ff_fourier_a_phi(i))+c_mp->ff_fourier_b_a(i)*sin(2*M_PI*c_mp->ff_fourier_b_f(i)*this->_t+c_mp->ff_fourier_b_phi(i));
    }

    Eigen::Matrix<double,6,1> F_ff_damp;
    F_ff_damp<<0,0,0,0,0,0;
    for(unsigned i=0;i<6;i++){
        if(fabs(p.TF_dX(i))>c_mp->dX_limit(i)){
//            F_ff_damp(i)=(fabs(p.TF_dX[i])-c_mp->dX_limit(i))*cpp_utils::sgn(p.TF_dX(i))*c_mp->D_x(i);
        }
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

    this->_cmd.TF_dX_d=dX_d_pose+dX_d_vel;
    this->_cmd.TF_F_ff=F_ff-F_ff_damp+F_h_p+F_h_d+F_h_e;
    this->_cmd.TF_F_d=attr->attr_fc;

    this->_t+=0.001;
    return this->_cmd;
}

void mp_basic::terminate(){
    if(this->_flag_mg_init){
        this->_mogen_p2p.terminate();
    }
}

bool mp_basic::check_attractor(){
    std::shared_ptr<AttractorBasic> attr = std::static_pointer_cast<AttractorBasic>(this->_attractor);
    if(!attr->attr_pose.isZero(0) && !attr->attr_vel.isZero(0)){
        cpp_utils::print_error("MP can not have a pose attractor and a direction attractor at the same time.");
        return false;
    }

    if(!attr->attr_fc.isZero(0) && !attr->attr_ff.isZero(0)){
        cpp_utils::print_error("MP can not have a contact attractor and a momvement attractor at the same time.");
        return false;
    }
//    if(!attr->attr_pose.isZero(0) && !attr->attr_fc.isZero(0)){
//        cpp_utils::print_error("MP can not have a pose attractor and a contact attractor at the same time.");
//        return false;
//    }
    return true;
}

bool mp_basic::init_attractor(const Percept &p, const std::shared_ptr<ConfigUser> config){
    std::shared_ptr<AttractorBasic> attr = std::static_pointer_cast<AttractorBasic>(this->_attractor);
    attr->neighbourhood_X=config->neighborhood_X;
    attr->neighbourhood_dX=config->neighborhood_dX;
    attr->neighbourhood_F=config->neighborhood_F;
    attr->neighbourhood_dF=config->neighborhood_dF;
    return true;
}

bool mp_basic::in_attractor(const Percept &p){
    std::shared_ptr<AttractorBasic> attr = std::static_pointer_cast<AttractorBasic>(this->_attractor);
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

    //    if(in_attr_pose_x && in_attr_pose_phi && in_attr_pose_dx && in_attr_pose_dphi
    //            && in_attr_vel_dx && in_attr_vel_dphi
    //            && in_attr_fc_x && in_attr_fc_phi && in_attr_fc_dx && in_attr_fc_dphi
    //            && in_attr_ff_x && in_attr_ff_phi
    //            && this->_mogen_p2p.get_out_l().arrived(0)==1){


    //        return true;

    if(this->_mogen_p2p.get_out_l().arrived(0)==1){
        return true;
    }else{
        return false;
    }
}

void mp_basic::setup_logs(unsigned long long length){

}

void mp_basic::write_logs(){

}

}
