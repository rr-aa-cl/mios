#pragma once

#include <vector>
#include <string>
#include <memory>
#include <eigen3/Eigen/Core>

class cntr_aicModelClass;

namespace cntr_aic {

struct In_P_cntr_aic{
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
}
};
struct In_U_cntr_aic{
Eigen::Matrix<double,4,4> TF_T_EE_d;
Eigen::Matrix<double,4,4> TF_T_EE;
Eigen::Matrix<double,6,1> TF_F_ff;
Eigen::Matrix<double,6,1> TF_F_ext;
Eigen::Matrix<double,7,7> M;
Eigen::Matrix<double,6,7> B_J_EE;
Eigen::Matrix<double,7,1> dtheta;
Eigen::Matrix<double,6,1> K_x;
Eigen::Matrix<double,6,1> xi_x;
Eigen::Matrix<double,3,3> O_R_T;
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
O_R_T.setZero();
}
};
struct Out_Y_cntr_aic{
Eigen::Matrix<double,7,1> tau_J_d;
Out_Y_cntr_aic(){
tau_J_d.setZero();
}
};
struct Out_L_cntr_aic{
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
class cntr_aic{
public:
cntr_aic();
~cntr_aic();
void initialize(bool log = false,unsigned long long l_len = 0,const std::string& path_logs="");
void step();
void terminate();
In_P_cntr_aic p;
In_U_cntr_aic u;
Out_Y_cntr_aic y;
Out_L_cntr_aic l;

private:
void write_input();
void write_output();
void write_log();
std::unique_ptr<cntr_aicModelClass> m_model;
std::vector<In_U_cntr_aic> m_log_u;
std::vector<Out_Y_cntr_aic> m_log_y;
std::vector<Out_L_cntr_aic> m_log_l;
std::string m_path_logs;
unsigned long long m_cnt_step;
bool m_flag_log;};

}