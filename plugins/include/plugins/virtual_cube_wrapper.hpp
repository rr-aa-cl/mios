#pragma once

#include "simulink_pipeline/plugin.hpp"
class virtual_cubeModelClass;

namespace virtual_cube {

struct In_P_virtual_cube : public In_P{
Eigen::Matrix<double,1,1> rho_min;
Eigen::Matrix<double,1,1> eta;
Eigen::Matrix<double,1,1> damping_distance;
Eigen::Matrix<double,1,1> damping_factor;
Eigen::Matrix<double,6,1> cube_walls;
Eigen::Matrix<double,1,1> f_max;
In_P_virtual_cube(){
rho_min.setZero();
eta.setZero();
damping_distance.setZero();
damping_factor.setZero();
cube_walls.setZero();
f_max.setZero();
}
};
struct In_U_virtual_cube : public In_U{
Eigen::Matrix<double,6,1> dx_EE;
Eigen::Matrix<double,3,1> p_EE;
Eigen::Matrix<double,6,7> Jacobian_EE;
In_U_virtual_cube(){
dx_EE.setZero();
p_EE.setZero();
Jacobian_EE.setZero();
}
};
struct Out_Y_virtual_cube : public Out_Y{
Eigen::Matrix<double,7,1> tau_vwalls;
Eigen::Matrix<double,6,1> wall_flag;
Out_Y_virtual_cube(){
tau_vwalls.setZero();
wall_flag.setZero();
}
};
struct Out_L_virtual_cube : public Out_L{
Eigen::Matrix<double,1,1> arrived;
Out_L_virtual_cube(){
arrived.setZero();
}
};
class virtual_cube : Plugin{
public:
virtual_cube();
~virtual_cube();
Out_Y_virtual_cube get_out_y();
Out_L_virtual_cube get_out_l();
void initialize(const In_U& in_u,const In_P& in_p,bool log = false,unsigned long long l_len = 0,std::string path_logs="");
void step(const In_U& in_u,Out_Y& out_y);
void terminate();

private:
void write_params_to_model();
void write_logs();
virtual_cubeModelClass* _model;
std::vector<In_U_virtual_cube> _log_in_u;
std::vector<Out_Y_virtual_cube> _log_out_y;
std::vector<Out_L_virtual_cube> _log_out_l;
Out_L_virtual_cube _log;
};

}