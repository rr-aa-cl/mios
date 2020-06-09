#pragma once

#include <vector>
#include <string>
#include <memory>
#include <eigen3/Eigen/Core>

class mogen_p2p_jointModelClass;

namespace mogen_p2p_joint {

struct In_P_mogen_p2p_joint{
Eigen::Matrix<double,7,1> q_0;
Eigen::Matrix<double,7,1> q_g;
Eigen::Matrix<double,1,1> dq_max;
Eigen::Matrix<double,1,1> ddq_max;
In_P_mogen_p2p_joint(){
q_0.setZero();
q_g.setZero();
dq_max.setZero();
ddq_max.setZero();
}
};
struct In_U_mogen_p2p_joint{
Eigen::Matrix<double,2,1> dummy;
In_U_mogen_p2p_joint(){
dummy.setZero();
}
};
struct Out_Y_mogen_p2p_joint{
Eigen::Matrix<double,7,1> q_d;
Eigen::Matrix<double,7,1> dq_d;
Out_Y_mogen_p2p_joint(){
q_d.setZero();
dq_d.setZero();
}
};
struct Out_L_mogen_p2p_joint{
Eigen::Matrix<double,1,1> arrived;
Out_L_mogen_p2p_joint(){
arrived.setZero();
}
};
class mogen_p2p_joint{
public:
mogen_p2p_joint();
~mogen_p2p_joint();
void initialize(bool log = false,unsigned long long l_len = 0,const std::string& path_logs="");
void step();
void terminate();
In_P_mogen_p2p_joint p;
In_U_mogen_p2p_joint u;
Out_Y_mogen_p2p_joint y;
Out_L_mogen_p2p_joint l;

private:
void write_input();
void write_output();
void write_log();
std::unique_ptr<mogen_p2p_jointModelClass> m_model;
std::vector<In_U_mogen_p2p_joint> m_log_u;
std::vector<Out_Y_mogen_p2p_joint> m_log_y;
std::vector<Out_L_mogen_p2p_joint> m_log_l;
std::string m_path_logs;
unsigned long long m_cnt_step;
bool m_flag_log;};

}