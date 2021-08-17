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

class RemoteJointPoseStrategy : public PrimitiveStrategy{
public:
    RemoteJointPoseStrategy();
    void initialize(const Percept &p_0) override;
    void get_next_command(Actuator &cmd, const Percept &p) override;
    void terminate(const Percept &p) override;
    bool finished() override;

    bool connect(Portal* portal, const std::string name, unsigned port, unsigned buffer_size, unsigned timeout_s, unsigned timeout_us, unsigned max_lost_packets,bool multicast);

private:
    void read_stream(std::vector<double> &data);

    std::deque<std::array<double,7> > m_q_d_in;
    std::shared_ptr<msrm_utils::UDPStreamReceiver> m_receiver;
    Portal* m_portal;
    std::string m_stream_name;

    Eigen::Matrix<double,7,1> m_last_valid_q_d;
};

}

