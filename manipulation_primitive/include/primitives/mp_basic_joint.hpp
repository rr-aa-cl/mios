#pragma once

#include "manipulation_primitive/manipulation_primitive.hpp"

#include "mogen_p2p_joint/mogen_p2p_joint_wrapper.hpp"

namespace mios {

struct ConfigMP_mp_basic_joint : public ConfigMP{
    ConfigMP_mp_basic_joint(){
        dq_d<<0;
        ddq_d<<0;

        dq_fourier_a_a.setZero();
        dq_fourier_b_a.setZero();
        dq_fourier_a_f.setZero();
        dq_fourier_b_f.setZero();
        dq_fourier_a_phi.setZero();
        dq_fourier_b_phi.setZero();

        ff_fourier_a_a.setZero();
        ff_fourier_b_a.setZero();
        ff_fourier_a_f.setZero();
        ff_fourier_b_f.setZero();
        ff_fourier_a_phi.setZero();
        ff_fourier_b_phi.setZero();
    }

    Eigen::Matrix<double,1,1> dq_d;
    Eigen::Matrix<double,1,1> ddq_d;

    Eigen::Matrix<double,7,1> dq_fourier_a_a;
    Eigen::Matrix<double,7,1> dq_fourier_b_a;
    Eigen::Matrix<double,7,1> dq_fourier_a_f;
    Eigen::Matrix<double,7,1> dq_fourier_b_f;
    Eigen::Matrix<double,7,1> dq_fourier_a_phi;
    Eigen::Matrix<double,7,1> dq_fourier_b_phi;

    Eigen::Matrix<double,7,1> ff_fourier_a_a;
    Eigen::Matrix<double,7,1> ff_fourier_b_a;
    Eigen::Matrix<double,7,1> ff_fourier_a_f;
    Eigen::Matrix<double,7,1> ff_fourier_b_f;
    Eigen::Matrix<double,7,1> ff_fourier_a_phi;
    Eigen::Matrix<double,7,1> ff_fourier_b_phi;
};

struct EvalMP_mp_basic_joint : public EvalMP{

};

struct AttractorBasicJoint : public Attractor{
    void reset(){
        attr_pose.setZero();
        attr_vel.setZero();
        attr_tauc.setZero();
        attr_ff.setZero();

        neighbourhood_q<<std::numeric_limits<double>::max();
        neighbourhood_dq<<std::numeric_limits<double>::max();
        neighbourhood_tau<<std::numeric_limits<double>::max();
        neighbourhood_dtau<<std::numeric_limits<double>::max();
    }

    Eigen::Matrix<double,7,1> attr_pose;
    Eigen::Matrix<double,7,1> attr_vel;
    Eigen::Matrix<double,7,1> attr_tauc;
    Eigen::Matrix<double,7,1> attr_ff;

    Eigen::Matrix<double,1,1> neighbourhood_q;
    Eigen::Matrix<double,1,1> neighbourhood_dq;

    Eigen::Matrix<double,1,1> neighbourhood_tau;
    Eigen::Matrix<double,1,1> neighbourhood_dtau;
};

class mp_basic_joint : public ManipulationPrimitive{
public:
    mp_basic_joint();
    ~mp_basic_joint();

    void initialize(const Percept &p_0,const std::shared_ptr<ConfigUser> config);
    CmdMP& step(const Percept& p);
    void terminate();

    bool in_attractor(const Percept &p);
    bool init_attractor(const Percept &p, const std::shared_ptr<ConfigUser> config);
    bool check_attractor();

    void setup_logs(unsigned long long length);
    void write_logs();

private:

    mogen_p2p_joint::mogen_p2p_joint _mogen_p2p_joint;
    mogen_p2p_joint::In_P_mogen_p2p_joint _mogen_p2p_joint_in_p;
    mogen_p2p_joint::In_U_mogen_p2p_joint _mogen_p2p_joint_in_u;
    mogen_p2p_joint::Out_Y_mogen_p2p_joint _mogen_p2p_joint_out_y;

};

}
