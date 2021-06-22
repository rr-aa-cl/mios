#pragma once

#include "mios/strategy/primitive_strategy.hpp"
#include <eigen3/Eigen/Core>

namespace mios {


class ReadFromFileStrategy : public PrimitiveStrategy{
public:
    ReadFromFileStrategy();
    void initialize(const Percept &p_0) override;
    void get_next_command(Actuator &cmd, const Percept &p) override;
    void terminate(const Percept &p) override;
    bool finished() override;

public:
    void set_data(const std::vector<std::array<double,16> >& data);

private:

    std::vector<std::array<double,16> > m_data;
    unsigned long m_cnt_data;

};

}
