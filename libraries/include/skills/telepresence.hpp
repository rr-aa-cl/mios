#pragma once

#include "skill/skill.hpp"

namespace mios{

enum TelepresenceMode{tmJoystick,tmDirectJoint,tmDirectCart};

class SkillParametersTelepresence : public SkillParameters{
public:
    bool from_json(const nlohmann::json &parameters) override;

    bool is_master;
    std::string ip_dst;
    unsigned port_dst;
    unsigned port_src;
    TelepresenceMode mode;

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
    }direct_cart;
};

class Telepresence : public Skill{
public:
    Telepresence(const std::string& id, Memory *memory, Portal* portal, const Percept& p);
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

};

}
