#pragma once

#include <vector>
#include <string>
#include <memory>
#include <eigen3/Eigen/Core>

class cntr_muxModelClass;

namespace cntr_mux {

struct In_P_cntr_mux{
Eigen::Matrix<double,7,1> tau_max;
Eigen::Matrix<double,7,1> dtau_max;
In_P_cntr_mux(){
tau_max.setZero();
dtau_max.setZero();
}
};
struct In_U_cntr_mux{
Eigen::Matrix<double,7,1> tau_J_d;
Eigen::Matrix<double,6,7> B_J_EE;
In_U_cntr_mux(){
tau_J_d.setZero();
B_J_EE.setZero();
}
};
struct Out_Y_cntr_mux{
Eigen::Matrix<double,7,1> tau_J_d_checked;
Out_Y_cntr_mux(){
tau_J_d_checked.setZero();
}
};
struct Out_L_cntr_mux{
Eigen::Matrix<double,1,1> valid_cart;
Out_L_cntr_mux(){
valid_cart.setZero();
}
};
class cntr_mux{
public:
cntr_mux();
~cntr_mux();
void initialize(bool log = false,unsigned long long l_len = 0,const std::string& path_logs="");
void step();
void terminate();
In_P_cntr_mux p;
In_U_cntr_mux u;
Out_Y_cntr_mux y;
Out_L_cntr_mux l;

private:
void write_input();
void write_output();
void write_log();
std::unique_ptr<cntr_muxModelClass> m_model;
std::vector<In_U_cntr_mux> m_log_u;
std::vector<Out_Y_cntr_mux> m_log_y;
std::vector<Out_L_cntr_mux> m_log_l;
std::string m_path_logs;
unsigned long long m_cnt_step;
bool m_flag_log;};

}