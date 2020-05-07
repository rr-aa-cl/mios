#pragma once

#include "simulink_pipeline/plugin.hpp"
class cntr_nullsp_projModelClass;

namespace cntr_nullsp_proj {

struct In_P_cntr_nullsp_proj : public In_P{
Eigen::Matrix<double,1,1> singlr_comp_mode;
Eigen::Matrix<double,1,1> singlr_threshold;
In_P_cntr_nullsp_proj(){
singlr_comp_mode.setZero();
singlr_threshold.setZero();
}
};
struct In_U_cntr_nullsp_proj : public In_U{
Eigen::Matrix<double,7,1> tau_c;
Eigen::Matrix<double,7,7> M;
Eigen::Matrix<double,6,7> J;
In_U_cntr_nullsp_proj(){
tau_c.setZero();
M.setZero();
J.setZero();
}
};
struct Out_Y_cntr_nullsp_proj : public Out_Y{
Eigen::Matrix<double,7,1> tau_n;
Out_Y_cntr_nullsp_proj(){
tau_n.setZero();
}
};
struct Out_L_cntr_nullsp_proj : public Out_L{
Eigen::Matrix<double,1,1> singlr_flag;
Out_L_cntr_nullsp_proj(){
singlr_flag.setZero();
}
};
class cntr_nullsp_proj : Plugin{
public:
cntr_nullsp_proj();
~cntr_nullsp_proj();
Out_Y_cntr_nullsp_proj get_out_y();
Out_L_cntr_nullsp_proj get_out_l();
void initialize(const In_U& in_u,const In_P& in_p,bool log = false,unsigned long long l_len = 0,std::string path_logs="");
void step(const In_U& in_u,Out_Y& out_y);
void terminate();

private:
void write_params_to_model();
void write_logs();
cntr_nullsp_projModelClass* _model;
std::vector<In_U_cntr_nullsp_proj> _log_in_u;
std::vector<Out_Y_cntr_nullsp_proj> _log_out_y;
std::vector<Out_L_cntr_nullsp_proj> _log_out_l;
Out_L_cntr_nullsp_proj _log;
};

}