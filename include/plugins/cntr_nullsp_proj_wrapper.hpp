#pragma once

#include <vector>
#include <string>
#include <memory>
#include <eigen3/Eigen/Core>

class cntr_nullsp_projModelClass;

namespace cntr_nullsp_proj {

struct In_P_cntr_nullsp_proj{
Eigen::Matrix<double,1,1> singlr_comp_mode;
Eigen::Matrix<double,1,1> singlr_threshold;
In_P_cntr_nullsp_proj(){
singlr_comp_mode.setZero();
singlr_threshold.setZero();
}
};
struct In_U_cntr_nullsp_proj{
Eigen::Matrix<double,7,1> tau_c;
Eigen::Matrix<double,7,7> M;
Eigen::Matrix<double,6,7> J;
In_U_cntr_nullsp_proj(){
tau_c.setZero();
M.setZero();
J.setZero();
}
};
struct Out_Y_cntr_nullsp_proj{
Eigen::Matrix<double,7,1> tau_n;
Out_Y_cntr_nullsp_proj(){
tau_n.setZero();
}
};
struct Out_L_cntr_nullsp_proj{
Eigen::Matrix<double,1,1> singlr_flag;
Out_L_cntr_nullsp_proj(){
singlr_flag.setZero();
}
};
class cntr_nullsp_proj{
public:
cntr_nullsp_proj();
~cntr_nullsp_proj();
void initialize(bool log = false,unsigned long long l_len = 0,const std::string& path_logs="");
void step();
void terminate();
In_P_cntr_nullsp_proj p;
In_U_cntr_nullsp_proj u;
Out_Y_cntr_nullsp_proj y;
Out_L_cntr_nullsp_proj l;

private:
void write_input();
void write_output();
void write_log();
std::unique_ptr<cntr_nullsp_projModelClass> m_model;
std::vector<In_U_cntr_nullsp_proj> m_log_u;
std::vector<Out_Y_cntr_nullsp_proj> m_log_y;
std::vector<Out_L_cntr_nullsp_proj> m_log_l;
std::string m_path_logs;
unsigned long long m_cnt_step;
bool m_flag_log;};

}