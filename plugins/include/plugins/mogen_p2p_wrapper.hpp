#pragma once

#include <vector>
#include <string>
#include <memory>
#include <eigen3/Eigen/Core>

class mogen_p2pModelClass;

namespace mogen_p2p {

struct In_P_mogen_p2p{
Eigen::Matrix<double,4,4> TF_T_EE_0;
Eigen::Matrix<double,4,4> TF_T_EE_1;
Eigen::Matrix<double,2,1> dX_max;
Eigen::Matrix<double,2,1> ddX_max;
In_P_mogen_p2p(){
TF_T_EE_0.setZero();
TF_T_EE_1.setZero();
dX_max.setZero();
ddX_max.setZero();
}
};
struct In_U_mogen_p2p{
Eigen::Matrix<double,2,1> t_scale;
In_U_mogen_p2p(){
t_scale.setZero();
}
};
struct Out_Y_mogen_p2p{
Eigen::Matrix<double,6,1> dX_d;
Out_Y_mogen_p2p(){
dX_d.setZero();
}
};
struct Out_L_mogen_p2p{
Eigen::Matrix<double,1,1> arrived;
Eigen::Matrix<double,2,1> phase;
Out_L_mogen_p2p(){
arrived.setZero();
phase.setZero();
}
};
class mogen_p2p{
public:
mogen_p2p();
~mogen_p2p();
void initialize(bool log = false,unsigned long long l_len = 0,const std::string& path_logs="");
void step();
void terminate();
In_P_mogen_p2p p;
In_U_mogen_p2p u;
Out_Y_mogen_p2p y;
Out_L_mogen_p2p l;

private:
void write_input();
void write_output();
void write_log();
std::unique_ptr<mogen_p2pModelClass> m_model;
std::vector<In_U_mogen_p2p> m_log_u;
std::vector<Out_Y_mogen_p2p> m_log_y;
std::vector<Out_L_mogen_p2p> m_log_l;
std::string m_path_logs;
unsigned long long m_cnt_step;
bool m_flag_log;};

}