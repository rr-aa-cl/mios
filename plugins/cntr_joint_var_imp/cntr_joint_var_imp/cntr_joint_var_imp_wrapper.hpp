#pragma once

#include "simulink_pipeline/plugin.hpp"
class cntr_joint_var_impModelClass;

namespace cntr_joint_var_imp {

struct In_P_cntr_joint_var_imp : public In_P{
Eigen::Matrix<double,1,1> enable_ffwd_vel;
Eigen::Matrix<double,1,1> enable_ffwd_acc;
In_P_cntr_joint_var_imp(){
enable_ffwd_vel.setZero();
enable_ffwd_acc.setZero();
}
};
struct In_U_cntr_joint_var_imp : public In_U{
Eigen::Matrix<double,7,1> theta;
Eigen::Matrix<double,7,1> dtheta;
Eigen::Matrix<double,7,1> theta_d;
Eigen::Matrix<double,7,1> dtheta_d;
Eigen::Matrix<double,7,1> ddtheta_d;
Eigen::Matrix<double,7,7> M;
Eigen::Matrix<double,7,1> tau_ff;
Eigen::Matrix<double,7,1> K_theta;
Eigen::Matrix<double,7,1> D_theta;
In_U_cntr_joint_var_imp(){
theta.setZero();
dtheta.setZero();
theta_d.setZero();
dtheta_d.setZero();
ddtheta_d.setZero();
M.setZero();
tau_ff.setZero();
K_theta.setZero();
D_theta.setZero();
}
};
struct Out_Y_cntr_joint_var_imp : public Out_Y{
Eigen::Matrix<double,7,1> tau_J_d;
Out_Y_cntr_joint_var_imp(){
tau_J_d.setZero();
}
};
struct Out_L_cntr_joint_var_imp : public Out_L{
Eigen::Matrix<double,7,1> tau_J_d_K;
Eigen::Matrix<double,7,1> tau_J_d_D;
Eigen::Matrix<double,7,1> K_theta;
Eigen::Matrix<double,7,1> D_theta;
Out_L_cntr_joint_var_imp(){
tau_J_d_K.setZero();
tau_J_d_D.setZero();
K_theta.setZero();
D_theta.setZero();
}
};
class cntr_joint_var_imp : Plugin{
public:
cntr_joint_var_imp();
~cntr_joint_var_imp();
Out_Y_cntr_joint_var_imp get_out_y();
Out_L_cntr_joint_var_imp get_out_l();
void initialize(const In_U& in_u,const In_P& in_p,bool log = false,unsigned long long l_len = 0,std::string path_logs="");
void step(const In_U& in_u,Out_Y& out_y);
void terminate();

private:
void write_params_to_model();
void write_logs();
cntr_joint_var_impModelClass* _model;
std::vector<In_U_cntr_joint_var_imp> _log_in_u;
std::vector<Out_Y_cntr_joint_var_imp> _log_out_y;
std::vector<Out_L_cntr_joint_var_imp> _log_out_l;
Out_L_cntr_joint_var_imp _log;
};

}