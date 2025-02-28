#pragma once

#include "mios/strategy/primitive_strategy.hpp"
#include "Eigen/Core"

namespace mios {


class ReadFromFileStrategy : public PrimitiveStrategy{
public:
    ReadFromFileStrategy();
    void initialize(const Percept &p_0) override;
    void get_next_command(Actuator &cmd, const Percept &p) override;
    void terminate(const Percept &p) override;
    bool finished() override;
    void set_joint_mode();

public:
    void set_data(const std::vector<std::array<double,16> >& data);
    void set_data(const std::vector<std::array<double,7> >& data);

private:

    std::vector<std::array<double,16> > m_data;
    std::vector<std::array<double,7> > m_data_joint;
    unsigned long m_cnt_data;
    bool m_joint_mode;

};

}
