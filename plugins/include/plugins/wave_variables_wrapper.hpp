#pragma once

#include <vector>
#include <string>
#include <memory>
#include <eigen3/Eigen/Core>

class wave_variablesModelClass;

namespace wave_variables {

struct In_P_wave_variables{
Eigen::Matrix<double,6,1> b;
Eigen::Matrix<double,6,1> lambda_u_l;
Eigen::Matrix<double,6,1> lambda_u_r;
Eigen::Matrix<double,1,1> master;
In_P_wave_variables(){
b.setZero();
lambda_u_l.setZero();
lambda_u_r.setZero();
master.setZero();
}
};
struct In_U_wave_variables{
Eigen::Matrix<double,6,1> dX_l;
Eigen::Matrix<double,6,1> v_l;
Eigen::Matrix<double,6,1> v_r;
Eigen::Matrix<double,6,1> F_r;
In_U_wave_variables(){
dX_l.setZero();
v_l.setZero();
v_r.setZero();
F_r.setZero();
}
};
struct Out_Y_wave_variables{
Eigen::Matrix<double,6,1> F_l;
Eigen::Matrix<double,6,1> u_l;
Eigen::Matrix<double,6,1> u_r;
Eigen::Matrix<double,6,1> dX_r;
Out_Y_wave_variables(){
F_l.setZero();
u_l.setZero();
u_r.setZero();
dX_r.setZero();
}
};
struct Out_L_wave_variables{
Out_L_wave_variables(){
}
};
class wave_variables{
public:
wave_variables();
~wave_variables();
void initialize(bool log = false,unsigned long long l_len = 0,const std::string& path_logs="");
void step();
void terminate();
In_P_wave_variables p;
In_U_wave_variables u;
Out_Y_wave_variables y;
Out_L_wave_variables l;

private:
void write_input();
void write_output();
void write_log();
std::unique_ptr<wave_variablesModelClass> m_model;
std::vector<In_U_wave_variables> m_log_u;
std::vector<Out_Y_wave_variables> m_log_y;
std::vector<Out_L_wave_variables> m_log_l;
std::string m_path_logs;
unsigned long long m_cnt_step;
bool m_flag_log;};

}