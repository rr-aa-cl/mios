#include "primitives/mp_basic.hpp"

#include <msrm_utils/math.hpp>

namespace mios {


BasicAttractor::BasicAttractor(){
    attr_pose=Eigen::Matrix<double,4,4>::Identity();
    attr_vel<<0,0,0,0,0,0;
    attr_fc<<0,0,0,0,0,0;
    attr_ff<<0,0,0,0,0,0;

    neighbourhood_X<<std::numeric_limits<double>::max(),std::numeric_limits<double>::max();
    neighbourhood_dX<<std::numeric_limits<double>::max(),std::numeric_limits<double>::max();
    neighbourhood_F<<std::numeric_limits<double>::max(),std::numeric_limits<double>::max();
    neighbourhood_dF<<std::numeric_limits<double>::max(),std::numeric_limits<double>::max();

    motion_generator_finished=false;
}

bool BasicAttractor::reached(const Percept &p){
    bool in_attr_pose_x=true;
    bool in_attr_pose_phi=true;
    bool in_attr_pose_dx=true;
    bool in_attr_pose_dphi=true;
    if(sqrt(pow(attr_pose(0,3)-p.proprioception.TF_T_EE(0,3),2)+pow(attr_pose(1,3)-p.proprioception.TF_T_EE(1,3),2)+pow(attr_pose(2,3)-p.proprioception.TF_T_EE(2,3),2))>neighbourhood_X(0)){
        in_attr_pose_x=false;
    }
    if(sqrt(pow(p.proprioception.TF_dX_EE(0),2)+pow(p.proprioception.TF_dX_EE(1),2)+pow(p.proprioception.TF_dX_EE(2),2))>neighbourhood_dX(0)){
        in_attr_pose_dx=false;
    }

    bool in_attr_vel_dx=true;
    bool in_attr_vel_dphi=true;
    if(sqrt(pow(p.proprioception.TF_dX_EE(0)-attr_vel(0),2)+pow(p.proprioception.TF_dX_EE(1)-attr_vel(1),2)+pow(p.proprioception.TF_dX_EE(2)-attr_vel(2),2))>neighbourhood_dX(0)){
        in_attr_vel_dx=false;
    }
    if(sqrt(pow(p.proprioception.TF_dX_EE(3)-attr_vel(3),2)+pow(p.proprioception.TF_dX_EE(4)-attr_vel(4),2)+pow(p.proprioception.TF_dX_EE(5)-attr_vel(5),2))>neighbourhood_dX(1)){
        in_attr_vel_dphi=false;
    }
    bool in_attr_fc_x=true;
    bool in_attr_fc_phi=true;
    bool in_attr_fc_dx=true;
    bool in_attr_fc_dphi=true;

    if(sqrt(pow(p.proprioception.TF_F_ext_K(0)-attr_fc(0),2)+pow(p.proprioception.TF_F_ext_K(1)-attr_fc(1),2)+pow(p.proprioception.TF_F_ext_K(2)-attr_fc(2),2))>neighbourhood_F(0)){
        in_attr_fc_x=false;
    }
    if(sqrt(pow(p.proprioception.TF_F_ext_K(3)-attr_fc(3),2)+pow(p.proprioception.TF_F_ext_K(4)-attr_fc(4),2)+pow(p.proprioception.TF_F_ext_K(5)-attr_fc(5),2))>neighbourhood_F(1)){
        in_attr_fc_phi=false;
    }
    if(sqrt(pow(p.proprioception.TF_dF_ext_K(0),2)+pow(p.proprioception.TF_dF_ext_K(1),2)+pow(p.proprioception.TF_dF_ext_K(2),2))>neighbourhood_dF(0)){
        in_attr_fc_dx=false;
    }
    if(sqrt(pow(p.proprioception.TF_dF_ext_K(3),2)+pow(p.proprioception.TF_dF_ext_K(4),2)+pow(p.proprioception.TF_dF_ext_K(5),2))>neighbourhood_dF(1)){
        in_attr_fc_dphi=false;
    }

    bool in_attr_ff_x=true;
    bool in_attr_ff_phi=true;

//    if(sqrt(pow(p.proprioception.TF_F_ff(0)-attr->attr_ff(0),2)+pow(p.proprioception.TF_F_ff(1)-attr->attr_ff(1),2)+pow(p.proprioception.TF_F_ff(2)-attr->attr_ff(2),2))>attr->neighbourhood_F(0)){
//        in_attr_ff_x=false;
//    }
//    if(sqrt(pow(p.proprioception.TF_F_ff(3)-attr->attr_ff(3),2)+pow(p.proprioception.TF_F_ff(4)-attr->attr_ff(4),2)+pow(p.proprioception.TF_F_ff(5)-attr->attr_ff(5),2))>attr->neighbourhood_F(1)){
//        in_attr_ff_phi=false;
//    }

    //    if(in_attr_pose_x && in_attr_pose_phi && in_attr_pose_dx && in_attr_pose_dphi
    //            && in_attr_vel_dx && in_attr_vel_dphi
    //            && in_attr_fc_x && in_attr_fc_phi && in_attr_fc_dx && in_attr_fc_dphi
    //            && in_attr_ff_x && in_attr_ff_phi
    //            && this->_mogen_p2p.proprioception.get_out_l().arrived(0)==1){


    //        return true;

    if(motion_generator_finished){
        return true;
    }else{
        return false;
    }
}

BasicPrimitive::BasicPrimitive(const std::string &name, const Percept &p_0, std::shared_ptr<MPParameters> parameters, std::shared_ptr<Attractor> attractor, Memory *memory):
    ManipulationPrimitive("BasicPrimitive",name,p_0,parameters,attractor,memory){
}

void BasicPrimitive::i_initialize(const Percept &p_0){
    std::shared_ptr<BasicAttractor> attr = get_attractor<BasicAttractor>();
    std::shared_ptr<MPParametersBasic> c_mp = get_parameters<MPParametersBasic>();

    for(unsigned i=0;i<6;i++){
        this->_X_d_vel_old(i)=c_mp->dX_fourier_a_a(i)*cos(2*M_PI*c_mp->dX_fourier_a_f(i)*0+c_mp->dX_fourier_a_phi(i))+c_mp->dX_fourier_b_a(i)*sin(2*M_PI*c_mp->dX_fourier_b_f(i)*0+c_mp->dX_fourier_b_phi(i));
    }
    mogen_p2p::In_P_mogen_p2p mogen_p2p_in_p;

    mogen_p2p_in_p.dX_max<<c_mp->dX_d(0),c_mp->dX_d(1);
    mogen_p2p_in_p.ddX_max<<c_mp->ddX_d(0),c_mp->ddX_d(1);

    mogen_p2p_in_p.TF_T_EE_0=p_0.proprioception.TF_T_EE;
    mogen_p2p_in_p.TF_T_EE_1=attr->attr_pose;
    m_mogen_p2p.initialize(m_mogen_p2p_in_u,mogen_p2p_in_p);

    m_motion_error_u.O_T_EE=p_0.proprioception.TF_T_EE;
    m_motion_error_u.O_T_EE_d=attr->attr_pose;

    motion_error_cart::In_P_motion_error_cart motion_error_p;
    m_motion_error.initialize(m_motion_error_u,motion_error_p);
}

Actuator* BasicPrimitive::step(const Percept &p){

    std::shared_ptr<BasicAttractor> attr = get_attractor<BasicAttractor>();
    std::shared_ptr<MPParametersBasic> c_mp = get_parameters<MPParametersBasic>();

    Eigen::Matrix<double,3,1> scale_t,scale_r;
    for(unsigned i=0;i<3;i++){
        if(fabs(p.proprioception.TF_F_ext_K(i))<c_mp->F_stop(i)-c_mp->DF_stop(i)){
            scale_t(i)=1;
        }else if(fabs(p.proprioception.TF_F_ext_K(i))<c_mp->F_stop(i)){
            scale_t(i)=1+1/c_mp->DF_stop(i)*(c_mp->F_stop(i)-c_mp->DF_stop(i))-1/c_mp->DF_stop(i)*fabs(p.proprioception.TF_F_ext_K(i));
        }else{
            scale_t(i)=0;
        }
        if(c_mp->F_stop(i)==0){
            scale_t(i)=1;
        }
        if(fabs(p.proprioception.TF_F_ext_K(i+3))<c_mp->F_stop(i+3)-c_mp->DF_stop(i+3)){
            scale_r(i)=1;
        }else if(fabs(p.proprioception.TF_F_ext_K(i+3))<c_mp->F_stop(i+3)){
            scale_r(i)=1+1/c_mp->DF_stop(i+3)*(c_mp->F_stop(i+3)-c_mp->DF_stop(i+3))-1/c_mp->DF_stop(i+3)*fabs(p.proprioception.TF_F_ext_K(i+3));
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

    m_mogen_p2p_in_u.t_scale<<scale_t.minCoeff(),scale_r.minCoeff();

    m_mogen_p2p.step(m_mogen_p2p_in_u,m_mogen_p2p_out_y);

    Eigen::Matrix<double,6,1> dX_d_pose;
    if(attr->attr_pose.isZero(0)){
        dX_d_pose.setZero();
    }else{
        dX_d_pose=m_mogen_p2p_out_y.dX_d;
    }

    Eigen::Matrix<double,6,1> dX_d_vel=attr->attr_vel;
    for(unsigned i=0;i<3;i++){
        dX_d_vel(i)*=scale_t.minCoeff();
        dX_d_vel(i+3)*=scale_r.minCoeff();
    }
    for(unsigned i=0;i<6;i++){
        double X_d_vel=c_mp->dX_fourier_a_a(i)*cos(2*M_PI*c_mp->dX_fourier_a_f(i)*this->_t+c_mp->dX_fourier_a_phi(i))+c_mp->dX_fourier_b_a(i)*sin(2*M_PI*c_mp->dX_fourier_b_f(i)*this->_t+c_mp->dX_fourier_b_phi(i));
        //        dX_d_vel(i)+=-c_mp->dX_fourier_a_a(i)*2*M_PI*c_mp->dX_fourier_a_f(i)*sin(2*M_PI*c_mp->dX_fourier_a_f(i)*p.proprioception.time+c_mp->dX_fourier_a_phi(i))+
        //                c_mp->dX_fourier_b_a(i)*2*M_PI*c_mp->dX_fourier_b_f(i)*cos(2*M_PI*c_mp->dX_fourier_b_f(i)*p.proprioception.time+c_mp->dX_fourier_b_phi(i));
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
        if(fabs(p.proprioception.TF_dX_EE(i))>c_mp->dX_limit(i)){
            //            F_ff_damp(i)=(fabs(p.proprioception.TF_dX[i])-c_mp->dX_limit(i))*msrm_utils::sgn(p.proprioception.TF_dX(i))*c_mp->D_x(i);
        }
    }

    m_motion_error_u.O_T_EE=p.proprioception.TF_T_EE;
    m_motion_error_u.O_T_EE_d=attr->attr_pose;

    m_motion_error.step(m_motion_error_u,m_motion_error_y);

    this->_e=m_motion_error_y.e;
    this->_de=m_motion_error_y.de;

    Eigen::Matrix<double,6,1> F_h_p;
    Eigen::Matrix<double,6,1> F_h_d;
    Eigen::Matrix<double,6,1> F_h_e;

    for(unsigned i=0;i<6;i++){
        F_h_p(i)=this->_e(i)*c_mp->F_h_p(i);
        F_h_d(i)=this->_de(i)*c_mp->F_h_d(i);
        F_h_e(i)=p.proprioception.TF_F_ext_K(i)*c_mp->F_h_e(i);
    }

    m_cmd.TF_dX_d=dX_d_pose+dX_d_vel;
    m_cmd.TF_F_ff=F_ff-F_ff_damp+F_h_p+F_h_d+F_h_e;
    m_cmd.TF_F_d=attr->attr_fc;

    this->_t+=0.001;
    return &m_cmd;
}

void BasicPrimitive::i_terminate(){
    m_mogen_p2p.terminate();
}

}
