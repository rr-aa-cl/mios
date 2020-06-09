#pragma once

#include <vector>
#include <string>
#include <memory>
#include <eigen3/Eigen/Core>

class virtual_walls_jointModelClass;

namespace virtual_walls_joint {

struct In_P_virtual_walls_joint{
Eigen::Matrix<double,7,1> rho_min;
Eigen::Matrix<double,7,1> eta;
Eigen::Matrix<double,7,1> damping_distance;
Eigen::Matrix<double,7,1> damping_factor;
Eigen::Matrix<double,14,1> walls;
Eigen::Matrix<double,7,1> tau_max;
In_P_virtual_walls_joint(){
rho_min.setZero();
eta.setZero();
damping_distance.setZero();
damping_factor.setZero();
walls.setZero();
tau_max.setZero();
}
};
struct In_U_virtual_walls_joint{
Eigen::Matrix<double,7,1> q;
Eigen::Matrix<double,7,1> dq;
In_U_virtual_walls_joint(){
q.setZero();
dq.setZero();
}
};
struct Out_Y_virtual_walls_joint{
Eigen::Matrix<double,7,1> tau_vwalls;
Eigen::Matrix<double,14,1> wall_flag;
Out_Y_virtual_walls_joint(){
tau_vwalls.setZero();
wall_flag.setZero();
}
};
struct Out_L_virtual_walls_joint{
Out_L_virtual_walls_joint(){
}
};
class virtual_walls_joint{
public:
virtual_walls_joint();
~virtual_walls_joint();
void initialize(bool log = false,unsigned long long l_len = 0,const std::string& path_logs="");
void step();
void terminate();
In_P_virtual_walls_joint p;
In_U_virtual_walls_joint u;
Out_Y_virtual_walls_joint y;
Out_L_virtual_walls_joint l;

private:
void write_input();
void write_output();
void write_log();
std::unique_ptr<virtual_walls_jointModelClass> m_model;
std::vector<In_U_virtual_walls_joint> m_log_u;
std::vector<Out_Y_virtual_walls_joint> m_log_y;
std::vector<Out_L_virtual_walls_joint> m_log_l;
std::string m_path_logs;
unsigned long long m_cnt_step;
bool m_flag_log;};

}