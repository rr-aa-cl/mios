#pragma once

#include "simulink_pipeline/plugin.hpp"
class virtual_walls_jointModelClass;

namespace virtual_walls_joint {

struct In_P_virtual_walls_joint : public In_P{
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
struct In_U_virtual_walls_joint : public In_U{
Eigen::Matrix<double,7,1> q;
Eigen::Matrix<double,7,1> dq;
In_U_virtual_walls_joint(){
q.setZero();
dq.setZero();
}
};
struct Out_Y_virtual_walls_joint : public Out_Y{
Eigen::Matrix<double,7,1> tau_vwalls;
Eigen::Matrix<double,14,1> wall_flag;
Out_Y_virtual_walls_joint(){
tau_vwalls.setZero();
wall_flag.setZero();
}
};
struct Out_L_virtual_walls_joint : public Out_L{
Out_L_virtual_walls_joint(){
}
};
class virtual_walls_joint : Plugin{
public:
virtual_walls_joint();
~virtual_walls_joint();
Out_Y_virtual_walls_joint get_out_y();
Out_L_virtual_walls_joint get_out_l();
void initialize(const In_U& in_u,const In_P& in_p,bool log = false,unsigned long long l_len = 0,std::string path_logs="");
void step(const In_U& in_u,Out_Y& out_y);
void terminate();

private:
void write_params_to_model();
void write_logs();
virtual_walls_jointModelClass* _model;
std::vector<In_U_virtual_walls_joint> _log_in_u;
std::vector<Out_Y_virtual_walls_joint> _log_out_y;
std::vector<Out_L_virtual_walls_joint> _log_out_l;
Out_L_virtual_walls_joint _log;
};

}