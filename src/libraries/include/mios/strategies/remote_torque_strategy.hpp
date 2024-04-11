#pragma once

#include "mios/strategy/primitive_strategy.hpp"
#include <deque>
#include <array>
#include <memory>

namespace mirmi_utils{
class UDPStreamReceiver;
}

namespace mios {

class Portal;

class RemoteTorqueStrategy : public PrimitiveStrategy{
public:
    RemoteTorqueStrategy();
    void initialize(const Percept &p_0) override;
    void get_next_command(Actuator &cmd, const Percept &p) override;
    void terminate(const Percept &p) override;
    bool finished() override;

    bool connect(Portal* portal, const std::string name, unsigned port, unsigned buffer_size, unsigned timeout_s, unsigned timeout_us, unsigned max_lost_packets, bool multicast, const std::optional<std::string> &host, const std::optional<std::string> &multicast_group);
    void set_damping(Eigen::Matrix<double,7,1> alpha);
    void StartDSInterpolation();

private:
    void read_stream(std::vector<double> &data);

    std::deque<std::array<double,7> > m_tau_in;
    std::shared_ptr<mirmi_utils::UDPStreamReceiver> m_receiver;
    Portal* m_portal;
    std::string m_stream_name;
    Eigen::Matrix<double,7,1> m_alpha;

    std::array<double,7> tau_y, tau_dy;
    bool ds_inter = false;
};

}

