#pragma once

#include "simulink_pipeline/plugin.hpp"
class tp_joint_limModelClass;

namespace tp_joint_lim {

struct In_P_tp_joint_lim : public In_P{
Eigen::Matrix<double,14,1> joint_lims;
};
struct In_U_tp_joint_lim : public In_U{
Eigen::Matrix<double,6,1> dx;
Eigen::Matrix<double,6,7> B_J_EE;
Eigen::Matrix<double,7,1> q;
};
struct Out_Y_tp_joint_lim : public Out_Y{
Eigen::Matrix<double,7,1> dq_hat;
Eigen::Matrix<double,14,1> lim_triggered;
};
struct Out_L_tp_joint_lim : public Out_L{
Eigen::Matrix<double,7,1> dq_hat_log;
};
class tp_joint_lim : Plugin{
public:
tp_joint_lim();
~tp_joint_lim();
Out_Y_tp_joint_lim get_out_y();
Out_L_tp_joint_lim get_out_l();
void initialize(const In_U& in_u,const In_P& in_p,bool log = false,unsigned long long l_len = 0,std::string path_logs="");
void step(const In_U& in_u,Out_Y& out_y);
void terminate();

private:
void write_params_to_model();
void write_logs();
tp_joint_limModelClass* _model;
std::vector<In_U_tp_joint_lim> _log_in_u;
std::vector<Out_Y_tp_joint_lim> _log_out_y;
std::vector<Out_L_tp_joint_lim> _log_out_l;
Out_L_tp_joint_lim _log;
};

}