#pragma once

#include "simulink_pipeline/plugin.hpp"
class conv_vel2poseModelClass;

namespace conv_vel2pose {

struct In_P_conv_vel2pose : public In_P{
};
struct In_U_conv_vel2pose : public In_U{
Eigen::Matrix<double,6,1> TF_dX_d;
Eigen::Matrix<double,4,4> TF_T_EE;
};
struct Out_Y_conv_vel2pose : public Out_Y{
Eigen::Matrix<double,4,4> TF_T_EE_d;
};
struct Out_L_conv_vel2pose : public Out_L{
};
class conv_vel2pose : Plugin{
public:
conv_vel2pose();
~conv_vel2pose();
Out_Y_conv_vel2pose get_out_y();
Out_L_conv_vel2pose get_out_l();
void initialize(const In_U& in_u,const In_P& in_p,bool log = false,unsigned long long l_len = 0,std::string path_logs="");
void step(const In_U& in_u,Out_Y& out_y);
void terminate();

private:
void write_params_to_model();
void write_logs();
conv_vel2poseModelClass* _model;
std::vector<In_U_conv_vel2pose> _log_in_u;
std::vector<Out_Y_conv_vel2pose> _log_out_y;
std::vector<Out_L_conv_vel2pose> _log_out_l;
Out_L_conv_vel2pose _log;
};

}