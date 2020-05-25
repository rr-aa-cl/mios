#pragma once

#include "manipulation_primitive/manipulation_primitive.hpp"

#include "plugins/mogen_p2p_joint_wrapper.hpp"

namespace mios {

class MPParametersBasicJointMP : public MPParameters{
public:
    MPParametersBasicJointMP();

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

class BasicJointAttractor : public Attractor{
public:
    BasicJointAttractor();
    bool reached(const Percept &p) override;

    Eigen::Matrix<double,7,1> attr_pose;
    Eigen::Matrix<double,7,1> attr_vel;
    Eigen::Matrix<double,7,1> attr_tauc;
    Eigen::Matrix<double,7,1> attr_ff;

    Eigen::Matrix<double,1,1> neighbourhood_q;
    Eigen::Matrix<double,1,1> neighbourhood_dq;

    Eigen::Matrix<double,1,1> neighbourhood_tau;
    Eigen::Matrix<double,1,1> neighbourhood_dtau;

    bool motion_generator_finished;
};

class BasicJointPrimitive : public ManipulationPrimitive{
public:
    BasicJointPrimitive(const std::string& name, const Percept& p_0, std::shared_ptr<MPParameters> parameters, std::shared_ptr<Attractor> attractor, Memory* memory);

    void i_initialize(const Percept &p_0) override;
    Actuator* step(const Percept& p);
    void i_terminate();

    bool in_attractor(const Percept &p);
    bool init_attractor(const Percept &p, const std::shared_ptr<ConfigUser> config);
    bool check_attractor();

    void setup_logs(unsigned long long length);
    void write_logs();

private:

    mogen_p2p_joint::mogen_p2p_joint m_mogen_p2p_joint;
    mogen_p2p_joint::In_U_mogen_p2p_joint m_mogen_p2p_joint_in_u;
    mogen_p2p_joint::Out_Y_mogen_p2p_joint m_mogen_p2p_joint_out_y;

};

}
