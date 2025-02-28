#pragma once

#include "mios/strategy/primitive_strategy.hpp"

namespace mios {

class FFWrenchLissajousStrategy : public PrimitiveStrategy{
public:
    FFWrenchLissajousStrategy();
    void initialize(const Percept &p_0) override;
    void get_next_command(Actuator &cmd, const Percept &p) override;
    void terminate(const Percept &p) override;
    bool finished() override;

    void set_coefficients(Eigen::Matrix<double,6,1> a, Eigen::Matrix<double,6,1> f, Eigen::Matrix<double,6,1> phi);
    void set_coefficients(Eigen::Matrix<double,6,1> c, Eigen::Matrix<double,6,1> a, Eigen::Matrix<double,6,1> f, Eigen::Matrix<double,6,1> phi);
private:
    Eigen::Matrix<double,6,1> m_c;
    Eigen::Matrix<double,6,1> m_a;
    Eigen::Matrix<double,6,1> m_f;
    Eigen::Matrix<double,6,1> m_phi;
};

}

