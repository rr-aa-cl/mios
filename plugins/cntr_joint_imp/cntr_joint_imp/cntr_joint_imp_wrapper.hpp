#pragma once

#include "simulink_pipeline/plugin.hpp"
class cntr_joint_impModelClass;

namespace cntr_joint_imp {

struct In_P_cntr_joint_imp : public In_P{
Eigen::Matrix<double,7,1> K_theta;
Eigen::Matrix<double,7,1> D_theta;
Eigen::Matrix<double,1,1> enable_ffwd_vel;
Eigen::Matrix<double,1,1> enable_ffwd_acc;
};
struct In_U_cntr_joint_imp : public In_U{
Eigen::Matrix<double,7,1> theta;
Eigen::Matrix<double,7,1> dtheta;
Eigen::Matrix<double,7,1> theta_d;
Eigen::Matrix<double,7,1> dtheta_d;
Eigen::Matrix<double,7,1> ddtheta_d;
Eigen::Matrix<double,7,7> M;
Eigen::Matrix<double,7,1> tau_ff;
};
struct Out_Y_cntr_joint_imp : public Out_Y{
Eigen::Matrix<double,7,1> tau_J_d;
};
struct Out_L_cntr_joint_imp : public Out_L{
Eigen::Matrix<double,7,1> tau_J_d;
};
class cntr_joint_imp : Plugin{
public:
cntr_joint_imp();
~cntr_joint_imp();
Out_Y_cntr_joint_imp get_out_y();
Out_L_cntr_joint_imp get_out_l();
void initialize(const In_U& in_u,const In_P& in_p,bool log = false,unsigned long long l_len = 0,std::string path_logs="");
void step(const In_U& in_u,Out_Y& out_y);
void terminate();

private:
void write_params_to_model();
void write_logs();
cntr_joint_impModelClass* _model;
std::vector<In_U_cntr_joint_imp> _log_in_u;
std::vector<Out_Y_cntr_joint_imp> _log_out_y;
std::vector<Out_L_cntr_joint_imp> _log_out_l;
Out_L_cntr_joint_imp _log;
};

}