#pragma once

#include "manipulation_primitive/manipulation_primitive.hpp"

#include "plugins/mogen_p2p_wrapper.hpp"
#include "plugins/motion_error_cart_wrapper.hpp"

namespace mios {

struct MPParametersBasic : public MPParameters{
    MPParametersBasic(){
        dX_d.setZero();
        ddX_d.setZero();

        dX_fourier_a_a.setZero();
        dX_fourier_b_a.setZero();
        dX_fourier_a_f.setZero();
        dX_fourier_b_f.setZero();
        dX_fourier_a_phi.setZero();
        dX_fourier_b_phi.setZero();

        ff_fourier_a_a.setZero();
        ff_fourier_b_a.setZero();
        ff_fourier_a_f.setZero();
        ff_fourier_b_f.setZero();
        ff_fourier_a_phi.setZero();
        ff_fourier_b_phi.setZero();

        D_x.setZero();
        dX_limit.setZero();

        F_h_p.setZero();
        F_h_d.setZero();
        F_h_e.setZero();

        F_stop.setZero();
        DF_stop.setZero();
    }

    Eigen::Matrix<double,2,1> dX_d;
    Eigen::Matrix<double,2,1> ddX_d;

    Eigen::Matrix<double,6,1> dX_fourier_a_a;
    Eigen::Matrix<double,6,1> dX_fourier_b_a;
    Eigen::Matrix<double,6,1> dX_fourier_a_f;
    Eigen::Matrix<double,6,1> dX_fourier_b_f;
    Eigen::Matrix<double,6,1> dX_fourier_a_phi;
    Eigen::Matrix<double,6,1> dX_fourier_b_phi;

    Eigen::Matrix<double,6,1> ff_fourier_a_a;
    Eigen::Matrix<double,6,1> ff_fourier_b_a;
    Eigen::Matrix<double,6,1> ff_fourier_a_f;
    Eigen::Matrix<double,6,1> ff_fourier_b_f;
    Eigen::Matrix<double,6,1> ff_fourier_a_phi;
    Eigen::Matrix<double,6,1> ff_fourier_b_phi;

    Eigen::Matrix<double,6,1> D_x;
    Eigen::Matrix<double,6,1> dX_limit;

    Eigen::Matrix<double,6,1> F_h_p;
    Eigen::Matrix<double,6,1> F_h_d;
    Eigen::Matrix<double,6,1> F_h_e;

    Eigen::Matrix<double,6,1> F_stop;
    Eigen::Matrix<double,6,1> DF_stop;
};

class BasicAttractor : public Attractor{
public:
    BasicAttractor();
    bool reached(const Percept &p) override;

    bool motion_generator_finished;

    Eigen::Matrix<double,4,4> attr_pose;
    Eigen::Matrix<double,6,1> attr_vel;
    Eigen::Matrix<double,6,1> attr_fc;
    Eigen::Matrix<double,6,1> attr_ff;

    Eigen::Matrix<double,2,1> neighbourhood_X;
    Eigen::Matrix<double,2,1> neighbourhood_dX;

    Eigen::Matrix<double,2,1> neighbourhood_F;
    Eigen::Matrix<double,2,1> neighbourhood_dF;
};

class BasicPrimitive : public ManipulationPrimitive{
public:
    BasicPrimitive(const std::string& name, const Percept& p_0, std::shared_ptr<MPParameters> parameters, std::shared_ptr<Attractor> attractor, Memory* memory);

    void i_initialize(const Percept &p_0);
    Actuator* step(const Percept& p);
    void i_terminate();

private:

    Eigen::Matrix<double,6,1> _X_d_vel_old;

    mogen_p2p::mogen_p2p m_mogen_p2p;
    mogen_p2p::In_U_mogen_p2p m_mogen_p2p_in_u;
    mogen_p2p::Out_Y_mogen_p2p m_mogen_p2p_out_y;

    motion_error_cart::motion_error_cart m_motion_error;
    motion_error_cart::In_U_motion_error_cart m_motion_error_u;
    motion_error_cart::Out_Y_motion_error_cart m_motion_error_y;

    double _t_0;
    double _t;
    Eigen::Matrix<double,6,1> _e;
    Eigen::Matrix<double,6,1> _de;
    bool _flag_mg_init;



};

}
