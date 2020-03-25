#pragma once

#include "simulink_pipeline/plugin.hpp"
class cntr_aicModelClass;

namespace cntr_aic {

struct In_P_cntr_aic : public In_P{
Eigen::Matrix<double,6,1> alpha;
Eigen::Matrix<double,6,1> beta;
Eigen::Matrix<double,6,1> gamma_a;
Eigen::Matrix<double,6,1> gamma_b;
Eigen::Matrix<double,6,1> K_0;
Eigen::Matrix<double,6,1> F_ff_0;
Eigen::Matrix<double,6,1> L;
Eigen::Matrix<double,6,1> xi;
Eigen::Matrix<double,1,1> kappa;
Eigen::Matrix<double,1,1> TF_control;
Eigen::Matrix<double,6,1> K_max;
Eigen::Matrix<double,6,1> dK_max;
Eigen::Matrix<double,6,1> F_ff_max;
Eigen::Matrix<double,6,1> dF_ff_max;
Eigen::Matrix<double,7,1> tau_max;
Eigen::Matrix<double,7,1> dtau_max;
Eigen::Matrix<double,4,4> EE_T_K;
Eigen::Matrix<double,3,3> O_R_TF;
In_P_cntr_aic(){
alpha.setZero();
beta.setZero();
gamma_a.setZero();
gamma_b.setZero();
K_0.setZero();
F_ff_0.setZero();
L.setZero();
xi.setZero();
kappa.setZero();
TF_control.setZero();
K_max.setZero();
dK_max.setZero();
F_ff_max.setZero();
dF_ff_max.setZero();
tau_max.setZero();
dtau_max.setZero();
EE_T_K.setZero();
O_R_TF.setZero();
}
};
struct In_U_cntr_aic : public In_U{
Eigen::Matrix<double,4,4> TF_T_EE_d;
Eigen::Matrix<double,4,4> TF_T_EE;
Eigen::Matrix<double,6,1> TF_F_ff;
Eigen::Matrix<double,6,1> TF_F_ext;
Eigen::Matrix<double,7,7> M;
Eigen::Matrix<double,6,7> B_J_EE;
Eigen::Matrix<double,7,1> dtheta;
Eigen::Matrix<double,6,1> K_x;
Eigen::Matrix<double,6,1> xi_x;
In_U_cntr_aic(){
TF_T_EE_d.setZero();
TF_T_EE.setZero();
TF_F_ff.setZero();
TF_F_ext.setZero();
M.setZero();
B_J_EE.setZero();
dtheta.setZero();
K_x.setZero();
xi_x.setZero();
}
};
struct Out_Y_cntr_aic : public Out_Y{
Eigen::Matrix<double,7,1> tau_J_d;
Out_Y_cntr_aic(){
tau_J_d.setZero();
}
};
struct Out_L_cntr_aic : public Out_L{
Eigen::Matrix<double,1,1> valid;
Eigen::Matrix<double,6,1> TF_F_ff;
Eigen::Matrix<double,6,1> K_x;
Eigen::Matrix<double,6,1> xi_x;
Out_L_cntr_aic(){
valid.setZero();
TF_F_ff.setZero();
K_x.setZero();
xi_x.setZero();
}
};
class cntr_aic : Plugin{
public:
cntr_aic();
~cntr_aic();
Out_Y_cntr_aic get_out_y();
Out_L_cntr_aic get_out_l();
void initialize(const In_U& in_u,const In_P& in_p,bool log = false,unsigned long long l_len = 0,std::string path_logs="");
void step(const In_U& in_u,Out_Y& out_y);
void terminate();

private:
void write_params_to_model();
void write_logs();
cntr_aicModelClass* _model;
std::vector<In_U_cntr_aic> _log_in_u;
std::vector<Out_Y_cntr_aic> _log_out_y;
std::vector<Out_L_cntr_aic> _log_out_l;
Out_L_cntr_aic _log;
};

}