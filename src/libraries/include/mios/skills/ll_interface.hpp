#pragma once

#include "mios/skill/skill.hpp"

namespace mios{

enum LLInterfaceMode{llTwist,llWrench,llTorque,llJointPose,llCartPose};

class SkillParametersLLInterface : public SkillParameters{
public:
    bool from_json(const nlohmann::json &parameters) override;
    std::map<std::string, std::set<std::string> > get_parameter_list() override;

    bool multicast;
    std::optional<std::string> host;  //hostname or sending IP to specify the right interface 
    std::string ip_dst;
    std::vector<std::string> multicast_group;
    std::string multicast_ip; //ip for multicast group, if not set -> "225.0.0.1"
    unsigned port_dst;
    unsigned port_src;
    unsigned remote_event_port; // remote port to be used for the handshake event
    std::string remote_event_protocol;
    LLInterfaceMode mode;
    bool terminate_when_loc;

    bool static_frame;


    struct DirectJoint{
        Eigen::Matrix<double,7,1> alpha;
    }direct_joint;

    struct DirectCart{
        Eigen::Matrix<double,6,1> alpha;
        Eigen::Matrix<double,6,1> F_ff;
        bool plane;
    }direct_cart;
};

class LLInterface : public Skill{
public:
    LLInterface(const std::string& id, Memory *memory, Portal* portal);
    ~LLInterface();

    std::shared_ptr<ManipulationPrimitive> get_initial_mp(const Percept &p_0) override;
    std::optional<std::shared_ptr<ManipulationPrimitive> > graph_transition(const Percept &p) override;

private:
    bool check_local_suc_conditions(const Percept &p) override;

private:
    std::shared_ptr<mirmi_utils::UDPStreamSender> m_udp_sender;

    unsigned m_handshake_stage;
    std::string m_handshake_message_uuid;
    std::vector<double> m_previous_payload;

private:
    //Eigen::Matrix<double,4,4> m_O_T_EE_master;
    Eigen::Matrix<double,7,1> m_q_init;

};

}
