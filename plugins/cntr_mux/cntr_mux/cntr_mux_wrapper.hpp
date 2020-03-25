#pragma once

#include "simulink_pipeline/plugin.hpp"
class cntr_muxModelClass;

namespace cntr_mux {

struct In_P_cntr_mux : public In_P{
Eigen::Matrix<double,7,1> tau_max;
Eigen::Matrix<double,7,1> dtau_max;
};
struct In_U_cntr_mux : public In_U{
Eigen::Matrix<double,7,1> tau_J_d;
Eigen::Matrix<double,6,7> B_J_EE;
};
struct Out_Y_cntr_mux : public Out_Y{
Eigen::Matrix<double,7,1> tau_J_d_checked;
};
struct Out_L_cntr_mux : public Out_L{
Eigen::Matrix<double,1,1> valid_cart;
};
class cntr_mux : Plugin{
public:
cntr_mux();
~cntr_mux();
Out_Y_cntr_mux get_out_y();
Out_L_cntr_mux get_out_l();
void initialize(const In_U& in_u,const In_P& in_p,bool log = false,unsigned long long l_len = 0,std::string path_logs="");
void step(const In_U& in_u,Out_Y& out_y);
void terminate();

private:
void write_params_to_model();
void write_logs();
cntr_muxModelClass* _model;
std::vector<In_U_cntr_mux> _log_in_u;
std::vector<Out_Y_cntr_mux> _log_out_y;
std::vector<Out_L_cntr_mux> _log_out_l;
Out_L_cntr_mux _log;
};

}