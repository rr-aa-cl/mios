#pragma once

#include "simulink_pipeline/plugin.hpp"
class cntr_forceModelClass;

namespace cntr_force {

struct In_P_cntr_force : public In_P{
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
};
struct In_U_cntr_force : public In_U{
Eigen::Matrix<double,6,1> TF_F_d_K;
Eigen::Matrix<double,6,1> TF_F_ext_K;
Eigen::Matrix<double,6,1> DX;
Eigen::Matrix<double,6,7> B_J_EE;
};
struct Out_Y_cntr_force : public Out_Y{
Eigen::Matrix<double,7,1> tau_J_d;
};
struct Out_L_cntr_force : public Out_L{
Eigen::Matrix<double,1,1> valid;
Eigen::Matrix<double,6,1> rho;
Eigen::Matrix<double,6,1> F_d;
};
class cntr_force : Plugin{
public:
cntr_force();
~cntr_force();
Out_Y_cntr_force get_out_y();
Out_L_cntr_force get_out_l();
void initialize(const In_U& in_u,const In_P& in_p,bool log = false,unsigned long long l_len = 0,std::string path_logs="");
void step(const In_U& in_u,Out_Y& out_y);
void terminate();

private:
void write_params_to_model();
void write_logs();
cntr_forceModelClass* _model;
std::vector<In_U_cntr_force> _log_in_u;
std::vector<Out_Y_cntr_force> _log_out_y;
std::vector<Out_L_cntr_force> _log_out_l;
Out_L_cntr_force _log;
};

}