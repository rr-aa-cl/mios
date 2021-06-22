#pragma once

#include "mios/skill/skill.hpp"

namespace mios{

enum TelepresenceMode{tmJoystick,tmDirectJoint,tmDirectCart};

class SkillParametersTelepresence : public SkillParameters{
public:
    bool from_json(const nlohmann::json &parameters) override;
    std::map<std::string, std::set<std::string> > get_parameter_list() override;

    bool is_master;
    bool multicast;
    std::string ip_dst;
    std::vector<std::string> multicast_group;
    unsigned port_dst;
    unsigned port_src;
    unsigned ws_port_dst; // remote websocket port to be used for the handshake
    TelepresenceMode mode;
    bool use_zoh_deadband;
    double deadband_k;
    bool terminate_when_loc;

    struct Joystick{
        Eigen::Matrix<double,6,1> amp;
        Eigen::Matrix<double,6,1> force_thr;
        bool static_frame;
    }joystick;

    struct DirectJoint{
        Eigen::Matrix<double,7,1> alpha;
    }direct_joint;

    struct DirectCart{
        Eigen::Matrix<double,6,1> alpha;
        Eigen::Matrix<double,6,1> F_ff;
        bool plane;
    }direct_cart;
};

class Telepresence : public Skill{
public:
    Telepresence(const std::string& id, Memory *memory, Portal* portal);
    ~Telepresence();

    std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept &p_0) override;
    std::optional<std::shared_ptr<ManipulationPrimitive> > graph_transition(const Percept &p) override;

private:
    bool check_local_suc_conditions(const Percept &p) override;
    void auxiliaries(const Percept &p) override;

private:
    std::shared_ptr<msrm_utils::UDPStreamSender> m_udp_sender;

    unsigned m_handshake_stage;
    std::string m_handshake_message_uuid;
    std::vector<double> m_previous_payload;

private:
    Eigen::Matrix<double,4,4> m_O_T_EE_master;
    Eigen::Matrix<double,7,1> m_q_master;

};

}
