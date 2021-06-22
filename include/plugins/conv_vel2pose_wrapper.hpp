#pragma once

#include <vector>
#include <string>
#include <memory>
#include <eigen3/Eigen/Core>

class conv_vel2poseModelClass;

namespace conv_vel2pose {

struct In_P_conv_vel2pose{
In_P_conv_vel2pose(){
}
};
struct In_U_conv_vel2pose{
Eigen::Matrix<double,6,1> TF_dX_d;
Eigen::Matrix<double,4,4> TF_T_EE;
Eigen::Matrix<double,1,1> reset;
In_U_conv_vel2pose(){
TF_dX_d.setZero();
TF_T_EE.setZero();
reset.setZero();
}
};
struct Out_Y_conv_vel2pose{
Eigen::Matrix<double,4,4> TF_T_EE_d;
Out_Y_conv_vel2pose(){
TF_T_EE_d.setZero();
}
};
struct Out_L_conv_vel2pose{
Out_L_conv_vel2pose(){
}
};
class conv_vel2pose{
public:
conv_vel2pose();
~conv_vel2pose();
void initialize(bool log = false,unsigned long long l_len = 0,const std::string& path_logs="");
void step();
void terminate();
In_P_conv_vel2pose p;
In_U_conv_vel2pose u;
Out_Y_conv_vel2pose y;
Out_L_conv_vel2pose l;

private:
void write_input();
void write_output();
void write_log();
std::unique_ptr<conv_vel2poseModelClass> m_model;
std::vector<In_U_conv_vel2pose> m_log_u;
std::vector<Out_Y_conv_vel2pose> m_log_y;
std::vector<Out_L_conv_vel2pose> m_log_l;
std::string m_path_logs;
unsigned long long m_cnt_step;
bool m_flag_log;};

}