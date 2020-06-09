#pragma once

#include <vector>
#include <string>
#include <memory>
#include <eigen3/Eigen/Core>

class motion_error_cartModelClass;

namespace motion_error_cart {

struct In_P_motion_error_cart{
In_P_motion_error_cart(){
}
};
struct In_U_motion_error_cart{
Eigen::Matrix<double,4,4> O_T_EE_d;
Eigen::Matrix<double,4,4> O_T_EE;
In_U_motion_error_cart(){
O_T_EE_d.setZero();
O_T_EE.setZero();
}
};
struct Out_Y_motion_error_cart{
Eigen::Matrix<double,6,1> e;
Eigen::Matrix<double,6,1> de;
Out_Y_motion_error_cart(){
e.setZero();
de.setZero();
}
};
struct Out_L_motion_error_cart{
Out_L_motion_error_cart(){
}
};
class motion_error_cart{
public:
motion_error_cart();
~motion_error_cart();
void initialize(bool log = false,unsigned long long l_len = 0,const std::string& path_logs="");
void step();
void terminate();
In_P_motion_error_cart p;
In_U_motion_error_cart u;
Out_Y_motion_error_cart y;
Out_L_motion_error_cart l;

private:
void write_input();
void write_output();
void write_log();
std::unique_ptr<motion_error_cartModelClass> m_model;
std::vector<In_U_motion_error_cart> m_log_u;
std::vector<Out_Y_motion_error_cart> m_log_y;
std::vector<Out_L_motion_error_cart> m_log_l;
std::string m_path_logs;
unsigned long long m_cnt_step;
bool m_flag_log;};

}