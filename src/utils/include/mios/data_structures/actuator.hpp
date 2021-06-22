#pragma once

#include "eigen3/Eigen/Core"
#include <set>

#include "mios/data_structures/percept.hpp"
#include "mios/data_structures/parameters.hpp"

namespace mios {

enum CommandPattern{CommandPatternCartesianPose,CommandPatternJointPose,CommandPatternNullspacePose,CommandPatternDesiredWrench,CommandPatternDesiredTorque,
                   CommandPatternCartesianCompliance,CommandPatternJointCompliance,CommandPatternCartesianTwist,CommandPatternCartesianFFWrench,
                   CommandPatternJointVelocities,CommandPatternJointFFTorque,CommandPatternO_R_T,CommandPatternGripper};

enum GripperRequest{None,Grasp,Move};

class Actuator{
public:
    Actuator(const Percept& p_0, const ControlParameters& controller);

    void initialize(const Percept& p_0, const ControlParameters &controller, Eigen::Matrix<double,3,3> O_R_T_0);
    void blend(const Actuator& cmd, const Percept& p);
    void stop();
    void read_from_buffer();
    void write_to_buffer();
    void limit_output(const LimitParameters &parameters);
    void limit_output_rate(const LimitParameters& parameters);

public:
    bool is_valid() const;
    bool is_stopped() const;
    bool is_settled(const LimitParameters& parameters, bool ignore=false) const;
    void set_zero(const Percept& p_0);
    void set_stop_factor(double stop_factor);
    bool is_new();
    void set_command_pattern(const std::set<CommandPattern>& command_pattern);
    const std::set<CommandPattern>* get_command_pattern() const;

    void grasp(double width, double speed, double force, std::string object);
    void move_fingers(double width, double speed);
    void accecpt_gripper_request();
    GripperRequest get_gripper_request();

private:
    void refresh_limiter();

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

    double gripper_width;
    double gripper_speed;
    double gripper_force;
    std::string gripper_object;
    GripperRequest gripper_request;

    double t;

private:
    std::set<CommandPattern> m_command_pattern;

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
    double m_stop_factor;

    bool m_new_command;

};

}
