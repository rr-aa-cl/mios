#pragma once

#include "manipulation_primitive/manipulation_primitive.hpp"

#include "motion_error_cart/motion_error_cart_wrapper.hpp"

namespace mios {

struct ConfigMP_mp_force_basis : public ConfigMP{
    ConfigMP_mp_force_basis(){

        ff_fourier_a_a<<0,0,0,0,0,0;
        ff_fourier_b_a<<0,0,0,0,0,0;
        ff_fourier_a_f<<0,0,0,0,0,0;
        ff_fourier_b_f<<0,0,0,0,0,0;
        ff_fourier_a_phi<<0,0,0,0,0,0;
        ff_fourier_b_phi<<0,0,0,0,0,0;
    }

    Eigen::Matrix<double,6,1> ff_fourier_a_a;
    Eigen::Matrix<double,6,1> ff_fourier_b_a;
    Eigen::Matrix<double,6,1> ff_fourier_a_f;
    Eigen::Matrix<double,6,1> ff_fourier_b_f;
    Eigen::Matrix<double,6,1> ff_fourier_a_phi;
    Eigen::Matrix<double,6,1> ff_fourier_b_phi;

    Eigen::Matrix<double,6,1> F_h_p;
    Eigen::Matrix<double,6,1> F_h_d;
    Eigen::Matrix<double,6,1> F_h_e;
};

struct EvalMP_mp_force_basis : public EvalMP{

};

struct AttractorForceBasis : public Attractor{
    void reset(){
        attr_pose=Eigen::Array44d::Zero(4,4);
        attr_vel<<0,0,0,0,0,0;
        attr_fc<<0,0,0,0,0,0;
        attr_ff<<0,0,0,0,0,0;

        neighbourhood_X<<std::numeric_limits<double>::max(),std::numeric_limits<double>::max();
        neighbourhood_dX<<std::numeric_limits<double>::max(),std::numeric_limits<double>::max();
        neighbourhood_F<<std::numeric_limits<double>::max(),std::numeric_limits<double>::max();
        neighbourhood_dF<<std::numeric_limits<double>::max(),std::numeric_limits<double>::max();
    }

    Eigen::Matrix<double,4,4> attr_pose;
    Eigen::Matrix<double,6,1> attr_vel;
    Eigen::Matrix<double,6,1> attr_fc;
    Eigen::Matrix<double,6,1> attr_ff;

    Eigen::Matrix<double,2,1> neighbourhood_X;
    Eigen::Matrix<double,2,1> neighbourhood_dX;

    Eigen::Matrix<double,2,1> neighbourhood_F;
    Eigen::Matrix<double,2,1> neighbourhood_dF;
};

class mp_force_basis : public ManipulationPrimitive{
public:
    mp_force_basis();
    ~mp_force_basis();

    void initialize(const Percept &p_0,const ConfigUser* config);
    CmdMP& step(const Percept& p);
    void terminate();

    bool in_attractor(const Percept &p);
    bool init_attractor(const Percept &p, const ConfigUser *config);
    bool check_attractor();

    void setup_logs(unsigned long long length);
    void write_logs();

private:

    motion_error_cart::motion_error_cart _motion_error;
    motion_error_cart::In_U_motion_error_cart _motion_error_u;
    motion_error_cart::Out_Y_motion_error_cart _motion_error_y;

    double _t_0;
    double _t;

    Eigen::Matrix<double,6,1> _e;
    Eigen::Matrix<double,6,1> _de;

};

}
