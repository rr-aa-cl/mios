#pragma once

#include "mios/strategy/primitive_strategy.hpp"
#include <deque>
#include <array>
#include <memory>

namespace msrm_utils{
class UDPStreamReceiver;
}

namespace mios {

class Portal;

class RemoteCartPoseStrategy : public PrimitiveStrategy{
public:
    RemoteCartPoseStrategy();
    void initialize(const Percept &p_0) override;
    void get_next_command(Actuator &cmd, const Percept &p) override;
    void terminate(const Percept &p) override;
    bool finished() override;

    bool connect(Portal* portal, const std::string name, unsigned port, unsigned buffer_size, unsigned timeout_s, unsigned timeout_us, unsigned max_lost_packets, bool multicast=false);

private:
    void read_stream(std::vector<double> &data);

    std::deque<std::array<double,16> > m_O_T_EE_d_in;
    std::shared_ptr<msrm_utils::UDPStreamReceiver> m_receiver;
    Portal* m_portal;
    std::string m_stream_name;

    Eigen::Matrix<double,4,4> m_last_valid_O_T_EE_d;
};

}

