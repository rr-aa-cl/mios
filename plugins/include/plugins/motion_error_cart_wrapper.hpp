#pragma once

#include "simulink_pipeline/plugin.hpp"
class motion_error_cartModelClass;

namespace motion_error_cart {

struct In_P_motion_error_cart : public In_P{
};
struct In_U_motion_error_cart : public In_U{
Eigen::Matrix<double,4,4> O_T_EE_d;
Eigen::Matrix<double,4,4> O_T_EE;
};
struct Out_Y_motion_error_cart : public Out_Y{
Eigen::Matrix<double,6,1> e;
Eigen::Matrix<double,6,1> de;
};
struct Out_L_motion_error_cart : public Out_L{
};
class motion_error_cart : Plugin{
public:
motion_error_cart();
~motion_error_cart();
Out_Y_motion_error_cart get_out_y();
Out_L_motion_error_cart get_out_l();
void initialize(const In_U& in_u,const In_P& in_p,bool log = false,unsigned long long l_len = 0,std::string path_logs="");
void step(const In_U& in_u,Out_Y& out_y);
void terminate();

private:
void write_params_to_model();
void write_logs();
motion_error_cartModelClass* _model;
std::vector<In_U_motion_error_cart> _log_in_u;
std::vector<Out_Y_motion_error_cart> _log_out_y;
std::vector<Out_L_motion_error_cart> _log_out_l;
Out_L_motion_error_cart _log;
};

}