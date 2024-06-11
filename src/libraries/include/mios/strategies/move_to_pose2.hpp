#pragma once

#include "mios/strategy/primitive_strategy.hpp"
#include "Eigen/Core"
#include "Eigen/Geometry"

namespace mios {

class MoveToPoseStrategy2 : public PrimitiveStrategy{
public:
    MoveToPoseStrategy2();
    void initialize(const Percept &p_0) override;
    void get_next_command(Actuator &cmd, const Percept &p) override;
    void terminate(const Percept &p) override;
    bool finished() override;

public:
    void set_goal(const Eigen::Matrix<double,4,4>& T_EE_d, double T_d);
    void set_scale(double t_scale);
    void set_wiggle_coefficients(Eigen::Matrix<double,6,1> offset_a, Eigen::Matrix<double,6,1> offset_f, Eigen::Matrix<double,6,1> offset_phi);

private:
    Eigen::Matrix<double,4,4> m_T_EE_d;  // goal pose
    Eigen::Matrix<double,4,4> m_T_EE_0;  // start pose
    Eigen::Quaternion<double> m_q_0;
    Eigen::Quaternion<double> m_q_d;
    Eigen::Quaternion<double> m_q_t;
    Eigen::Quaternion<double> m_q_delta;  //wiggle
    Eigen::Matrix<double,3,3> m_R_delta;
    
    
    double m_t_d; //desired total duration
    double m_t = 0;  // duration progress
    double m_a = 2;  //  term for shaping function  
    double m_b = 3; // termn for shaping function
    double m_s;
    bool m_wiggle;
    //wigle parameters:
    Eigen::Matrix<double,6,1> m_deltaPose_a;
    Eigen::Matrix<double,6,1> m_deltaPose_f;
    Eigen::Matrix<double,6,1> m_deltaPose_phi;
    Eigen::Matrix<double,6,1> m_deltaPose;
    
};

}
