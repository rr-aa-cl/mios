#pragma once

#include <vector>
#include <string>
#include <memory>
#include <eigen3/Eigen/Core>

class cntr_forceModelClass;

namespace cntr_force {

struct In_P_cntr_force{
Eigen::Matrix<double,6,1> k_p;
Eigen::Matrix<double,6,1> k_i;
Eigen::Matrix<double,6,1> k_d;
Eigen::Matrix<double,6,1> k_d_N;
Eigen::Matrix<double,3,1> d_max;
Eigen::Matrix<double,1,1> phi_max;
Eigen::Matrix<double,1,1> sf_on;
Eigen::Matrix<double,6,1> F_d_max;
Eigen::Matrix<double,6,1> dF_d_max;
Eigen::Matrix<double,7,1> tau_max;
Eigen::Matrix<double,7,1> dtau_max;
Eigen::Matrix<double,6,1> active;
In_P_cntr_force(){
k_p.setZero();
k_i.setZero();
k_d.setZero();
k_d_N.setZero();
d_max.setZero();
phi_max.setZero();
sf_on.setZero();
F_d_max.setZero();
dF_d_max.setZero();
tau_max.setZero();
dtau_max.setZero();
active.setZero();
}
};
struct In_U_cntr_force{
Eigen::Matrix<double,6,1> TF_F_d_K;
Eigen::Matrix<double,6,1> TF_F_ext_K;
Eigen::Matrix<double,6,1> DX;
Eigen::Matrix<double,6,7> B_J_0;
Eigen::Matrix<double,3,3> O_R_T;
In_U_cntr_force(){
TF_F_d_K.setZero();
TF_F_ext_K.setZero();
DX.setZero();
B_J_0.setZero();
O_R_T.setZero();
}
};
struct Out_Y_cntr_force{
Eigen::Matrix<double,7,1> tau_J_d;
Out_Y_cntr_force(){
tau_J_d.setZero();
}
};
struct Out_L_cntr_force{
Eigen::Matrix<double,1,1> valid;
Eigen::Matrix<double,6,1> rho;
Eigen::Matrix<double,6,1> F_d;
Out_L_cntr_force(){
valid.setZero();
rho.setZero();
F_d.setZero();
}
};
class cntr_force{
public:
cntr_force();
~cntr_force();
void initialize(bool log = false,unsigned long long l_len = 0,const std::string& path_logs="");
void step();
void terminate();
In_P_cntr_force p;
In_U_cntr_force u;
Out_Y_cntr_force y;
Out_L_cntr_force l;

private:
void write_input();
void write_output();
void write_log();
std::unique_ptr<cntr_forceModelClass> m_model;
std::vector<In_U_cntr_force> m_log_u;
std::vector<Out_Y_cntr_force> m_log_y;
std::vector<Out_L_cntr_force> m_log_l;
std::string m_path_logs;
unsigned long long m_cnt_step;
bool m_flag_log;};

}