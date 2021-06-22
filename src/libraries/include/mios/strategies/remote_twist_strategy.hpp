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

class RemoteTwistStrategy : public PrimitiveStrategy{
public:
    RemoteTwistStrategy();
    void initialize(const Percept &p_0) override;
    void get_next_command(Actuator &cmd, const Percept &p) override;
    void terminate(const Percept &p) override;
    bool finished() override;

    bool connect(Portal* portal, const std::string name, unsigned port, unsigned buffer_size, unsigned timeout_s, unsigned timeout_us, unsigned max_lost_packets,bool multicast);
    void set_frame(bool static_frame);

private:
    void read_stream(std::vector<double> &data);

    std::deque<std::array<double,6> > m_TF_dX_d_in;
    std::shared_ptr<msrm_utils::UDPStreamReceiver> m_receiver;
    bool m_static_frame;
    Portal* m_portal;
    std::string m_stream_name;
};

}

