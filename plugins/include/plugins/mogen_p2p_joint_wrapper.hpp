#pragma once

#include "simulink_pipeline/plugin.hpp"
class mogen_p2p_jointModelClass;

namespace mogen_p2p_joint {

struct In_P_mogen_p2p_joint : public In_P{
Eigen::Matrix<double,7,1> q_0;
Eigen::Matrix<double,7,1> q_g;
Eigen::Matrix<double,1,1> dq_max;
Eigen::Matrix<double,1,1> ddq_max;
};
struct In_U_mogen_p2p_joint : public In_U{
Eigen::Matrix<double,2,1> dummy;
};
struct Out_Y_mogen_p2p_joint : public Out_Y{
Eigen::Matrix<double,7,1> q_d;
Eigen::Matrix<double,7,1> dq_d;
};
struct Out_L_mogen_p2p_joint : public Out_L{
Eigen::Matrix<double,1,1> arrived;
};
class mogen_p2p_joint : Plugin{
public:
mogen_p2p_joint();
~mogen_p2p_joint();
Out_Y_mogen_p2p_joint get_out_y();
Out_L_mogen_p2p_joint get_out_l();
void initialize(const In_U& in_u,const In_P& in_p,bool log = false,unsigned long long l_len = 0,std::string path_logs="");
void step(const In_U& in_u,Out_Y& out_y);
void terminate();

private:
void write_params_to_model();
void write_logs();
mogen_p2p_jointModelClass* _model;
std::vector<In_U_mogen_p2p_joint> _log_in_u;
std::vector<Out_Y_mogen_p2p_joint> _log_out_y;
std::vector<Out_L_mogen_p2p_joint> _log_out_l;
Out_L_mogen_p2p_joint _log;
};

}