#pragma once

#include <eigen3/Eigen/Core>

#include "data_structures/percept.hpp"
#include "data_structures/parameters.hpp"

namespace mios {

class Actuator{
public:
    Actuator(const Percept& p_0);

    void initialize(const Percept& p_0);
    void stop();
    void read_from_buffer();
    void limit_output(const LimitParameters &parameters);
    void limit_output_rate(const LimitParameters& parameters);

public:
    bool is_valid() const;
    bool is_stopped() const;
    bool is_settled(const LimitParameters& parameters) const;
    void set_zero();

public:


    Eigen::Matrix<double,4,4> TF_T_EE_d;
    Eigen::Matrix<double,6,1> TF_dX_d;
    Eigen::Matrix<double,7,1> q_d_nullspace;
    Eigen::Matrix<double,6,1> TF_F_d;
    Eigen::Matrix<double,6,1> TF_F_ff;
    Eigen::Matrix<double,6,1> K_x;
    Eigen::Matrix<double,6,1> xi_x;
    Eigen::Matrix<double,3,3> O_R_T;

    Eigen::Matrix<double,7,1> q_d;
    Eigen::Matrix<double,7,1> dq_d;
    Eigen::Matrix<double,7,1> tau_d;
    Eigen::Matrix<double,7,1> tau_ff;
    Eigen::Matrix<double,7,1> K_theta;
    Eigen::Matrix<double,7,1> xi_theta;

    double t;
private:

    Eigen::Matrix<double,4,4> m_TF_T_EE_d_buffer;
    Eigen::Matrix<double,6,1> m_TF_dX_d_buffer;
    Eigen::Matrix<double,7,1> m_q_d_nullspace_buffer;
    Eigen::Matrix<double,6,1> m_TF_F_d_buffer;
    Eigen::Matrix<double,6,1> m_TF_F_ff_buffer;
    Eigen::Matrix<double,6,1> m_K_x_buffer;
    Eigen::Matrix<double,6,1> m_xi_x_buffer;
    Eigen::Matrix<double,3,3> m_O_R_T_buffer;

    Eigen::Matrix<double,7,1> m_q_d_buffer;
    Eigen::Matrix<double,7,1> m_dq_d_buffer;
    Eigen::Matrix<double,7,1> m_tau_d_buffer;
    Eigen::Matrix<double,7,1> m_tau_ff_buffer;
    Eigen::Matrix<double,7,1> m_K_theta_buffer;
    Eigen::Matrix<double,7,1> m_xi_theta_buffer;

    Eigen::Matrix<double,4,4> m_TF_T_EE_d_limiter;
    Eigen::Matrix<double,6,1> m_TF_dX_d_limiter;
    Eigen::Matrix<double,7,1> m_q_d_nullspace_limiter;
    Eigen::Matrix<double,6,1> m_TF_F_d_limiter;
    Eigen::Matrix<double,6,1> m_TF_F_ff_limiter;
    Eigen::Matrix<double,6,1> m_K_x_limiter;
    Eigen::Matrix<double,6,1> m_xi_x_limiter;
    Eigen::Matrix<double,3,3> m_O_R_T_limiter;

    Eigen::Matrix<double,7,1> m_q_d_limiter;
    Eigen::Matrix<double,7,1> m_dq_d_limiter;
    Eigen::Matrix<double,7,1> m_tau_d_limiter;
    Eigen::Matrix<double,7,1> m_tau_ff_limiter;
    Eigen::Matrix<double,7,1> m_K_theta_limiter;
    Eigen::Matrix<double,7,1> m_xi_theta_limiter;

    bool m_stop;
};

}
