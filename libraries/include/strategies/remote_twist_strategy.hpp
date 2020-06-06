#pragma once

#include "strategy/primitive_strategy.hpp"
#include <deque>
#include <array>

namespace mios {

class Portal;

class RemoteTwistStrategy : public PrimitiveStrategy{
public:
    void initialize(const Percept &p_0) override;
    void get_next_command(Actuator &cmd, const Percept &p) override;
    void terminate(const Percept &p) override;
    bool finished() override;

    bool connect(Portal* portal, const std::string name, unsigned port, unsigned buffer_size, unsigned timeout_s, unsigned timeout_us, unsigned max_lost_packets);

private:
    void read_stream(std::vector<double> &data);

    std::deque<std::array<double,6> > m_TF_dX_d_in;
};

}

