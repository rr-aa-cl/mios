#pragma once

#include <vector>
#include <string>
#include <memory>
#include <eigen3/Eigen/Core>

class virtual_cubeModelClass;

namespace virtual_cube {

struct P_virtual_cube{
Eigen::Matrix<double,1,1> rho_min;
Eigen::Matrix<double,1,1> eta;
Eigen::Matrix<double,1,1> damping_distance;
Eigen::Matrix<double,1,1> damping_factor;
Eigen::Matrix<double,6,1> cube_walls;
Eigen::Matrix<double,1,1> f_max;
P_virtual_cube(){
rho_min.setZero();
eta.setZero();
damping_distance.setZero();
damping_factor.setZero();
cube_walls.setZero();
f_max.setZero();
}
};
struct U_virtual_cube{
Eigen::Matrix<double,6,1> dx_EE;
Eigen::Matrix<double,3,1> p_EE;
Eigen::Matrix<double,6,7> Jacobian_EE;
U_virtual_cube(){
dx_EE.setZero();
p_EE.setZero();
Jacobian_EE.setZero();
}
};
struct Y_virtual_cube{
Eigen::Matrix<double,7,1> tau_vwalls;
Eigen::Matrix<double,6,1> wall_flag;
Y_virtual_cube(){
tau_vwalls.setZero();
wall_flag.setZero();
}
};
struct L_virtual_cube{
Eigen::Matrix<double,1,1> arrived;
L_virtual_cube(){
arrived.setZero();
}
};
class virtual_cube{
public:
virtual_cube();
~virtual_cube();
void initialize(bool log = false,unsigned long long l_len = 0,const std::string& path_logs="");
void step();
void terminate();
P_virtual_cube p;
U_virtual_cube u;
Y_virtual_cube y;
L_virtual_cube l;

private:
void write_input();
void write_output();
void write_log();
std::unique_ptr<virtual_cubeModelClass> m_model;
std::vector<U_virtual_cube> m_log_u;
std::vector<Y_virtual_cube> m_log_y;
std::vector<L_virtual_cube> m_log_l;
std::string m_path_logs;
unsigned long long m_cnt_step;
bool m_flag_log;};

}