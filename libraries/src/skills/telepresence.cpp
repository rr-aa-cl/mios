#include "skills/telepresence.hpp"
#include "strategies/move_to_joint_pose.hpp"
#include "strategies/move_to_pose.hpp"
#include "strategies/null_strategy.hpp"
#include "strategies/cart_compliance_strategy.hpp"
#include "strategies/joint_compliance_strategy.hpp"
#include "strategies/remote_twist_strategy.hpp"
#include "strategies/remote_cart_pose_strategy.hpp"
#include "strategies/remote_wrench_strategy.hpp"
#include "strategies/remote_joint_pose_strategy.hpp"
#include "strategies/remote_torque_strategy.hpp"
#include "strategies/ff_strategy.hpp"

#include <msrm_cpp_utils/math.hpp>

namespace mios{

using Params=SkillParametersTelepresence;

bool SkillParametersTelepresence::from_json(const nlohmann::json &parameters){
    if(!msrm_utils::read_json_param(parameters,"is_master",is_master)){
        spdlog::error("Missing parameter: is_master");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"multicast",multicast)){
        multicast=false;
    }
    if(!msrm_utils::read_json_param(parameters,"multicast_group",multicast_group) && multicast && is_master){
        spdlog::error("Missing parameter: multicast_group");
        return false;
    }
    if(is_master && multicast && multicast_group.size()==0){
        spdlog::error("When using multicast, at least one slave must be defined.");
        return false;
    }

    if(!msrm_utils::read_json_param(parameters,"ip_dst",ip_dst)){
        spdlog::error("Missing parameter: ip_dst");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"port_dst",port_dst)){
        spdlog::error("Missing parameter: port_dst");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"port_src",port_src)){
        spdlog::error("Missing parameter: port_src");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"ws_port_dst",ws_port_dst)){
        ws_port_dst = 12000; // default port for remote websocket handshake
    }
    if(!msrm_utils::read_json_param(parameters,"use_zoh_deadband",use_zoh_deadband)){
        use_zoh_deadband=false;
    }
    if(!msrm_utils::read_json_param(parameters,"deadband_k",deadband_k)){
        deadband_k=0;
    }
    std::string telepresence_mode;
    if(!msrm_utils::read_json_param(parameters,"telepresence_mode",telepresence_mode)){
        spdlog::error("Missing parameter: telepresence_mode");
        return false;
    }
    if(telepresence_mode=="Joystick"){
        mode=TelepresenceMode::tmJoystick;
    }else if(telepresence_mode=="DirectCart"){
        mode=TelepresenceMode::tmDirectCart;
    }else if(telepresence_mode=="DirectJoint"){
        mode=TelepresenceMode::tmDirectJoint;
    }else{
        spdlog::error("Invalid telepresence mode.");
        return false;
    }

    if(parameters.find("joystick")==parameters.end() && mode==TelepresenceMode::tmJoystick){
        spdlog::error("Joystick mode has been selected but no mode-related parameters were given.");
        return false;
    }else if(parameters.find("joystick")!=parameters.end() && mode==TelepresenceMode::tmJoystick){
        if(is_master && !msrm_utils::read_json_param<double,6,1>(parameters["joystick"],"amp",joystick.amp)){
            spdlog::error("Missing parameter: joystick.amp");
            return false;
        }
        if(is_master && !msrm_utils::read_json_param<double,6,1>(parameters["joystick"],"force_thr",joystick.force_thr)){
            spdlog::error("Missing parameter: joystick.force_thr");
            return false;
        }
        if(!is_master && !msrm_utils::read_json_param(parameters["joystick"],"static_frame",joystick.static_frame)){
            joystick.static_frame=true;
        }
    }

    if(parameters.find("direct_joint")==parameters.end() && mode==TelepresenceMode::tmDirectJoint){
        spdlog::error("DirectJoint mode has been selected but no mode-related parameters were given.");
        return false;
    }else if(parameters.find("direct_joint")!=parameters.end() && mode==TelepresenceMode::tmDirectJoint){
        if(!msrm_utils::read_json_param<double,7,1>(parameters["direct_joint"],"alpha",direct_joint.alpha)){
            spdlog::warn("Could not load direct_joint.alpha");
            direct_joint.alpha.setZero();
        }
    }

    if(parameters.find("direct_cart")==parameters.end() && mode==TelepresenceMode::tmDirectCart){
        spdlog::error("DirectCart mode has been selected but no mode-related parameters were given.");
        return false;
    }else if(parameters.find("direct_cart")!=parameters.end() && mode==TelepresenceMode::tmDirectCart){
        if(!msrm_utils::read_json_param<double,6,1>(parameters["direct_cart"],"alpha",direct_cart.alpha)){
            direct_cart.alpha.setZero();
        }
        if(!msrm_utils::read_json_param(parameters["direct_cart"],"plane",direct_cart.plane)){
            direct_cart.plane=false;
        }
        if(!msrm_utils::read_json_param<double,6,1>(parameters["direct_cart"],"F_ff",direct_cart.F_ff)){
            direct_cart.F_ff.setZero();
        }
    }

    if(multicast && is_master){
        ip_dst="225.0.0.1";
    }

    return true;
}

std::map<std::string,std::set<std::string> > SkillParametersTelepresence::get_parameter_list(){
    return {{"is_master",{}},{"ip_dst",{}},{"port_dst",{}},{"port_src",{}},{"ws_port_dst",{}},{"multicast",{}},{"multicast_group",{}},{"telepresence_mode",{}},
        {"joystick",{"amp","force_thr","static_frame"}},{"direct_joint",{"alpha"}},{"direct_cart",{"alpha"}},{"direct_cart",{"plane"}}};
}

Telepresence::Telepresence(const std::string &name, Memory *memory, Portal *portal):Skill("Telepresence",{},name,memory,portal,
{ControlMode::mCartTorque,ControlMode::mJointTorque,ControlMode::mCartVelocity,ControlMode::mJointVelocity}),m_handshake_stage(0){
    m_memory->remove_event("sync_done");
    m_previous_payload.assign(6,0);
}

Telepresence::~Telepresence(){
    if(read_parameters<Params>()->mode==TelepresenceMode::tmDirectCart){
        m_portal->close_udp_outstream("remote_cart_pose_out");
        m_portal->close_udp_outstream("remote_force_out");
        m_portal->close_udp_instream("remote_cart_pose_in");
        m_portal->close_udp_instream("remote_wrench_in");
    }
    if(read_parameters<Params>()->mode==TelepresenceMode::tmDirectJoint){
        m_portal->close_udp_outstream("remote_joint_pose_out");
        m_portal->close_udp_outstream("remote_torque_out");
        m_portal->close_udp_instream("remote_joint_pose_in");
        m_portal->close_udp_instream("remote_torque_in");
    }
    if(read_parameters<Params>()->mode==TelepresenceMode::tmJoystick){
        m_portal->close_udp_outstream("remote_twist_out");
        m_portal->close_udp_outstream("remote_force_out");
        m_portal->close_udp_instream("remote_twist_in");
        m_portal->close_udp_instream("remote_wrench_in");
    }
}

std::shared_ptr<ManipulationPrimitive> Telepresence::get_initial_mp(const Percept &p_0){
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("handshake",p_0);
    nlohmann::json response;
    mp->create_strategy<NullStrategy>("idle",1);
    return mp;
}

std::optional<std::shared_ptr<ManipulationPrimitive> > Telepresence::graph_transition(const Percept &p){
    if(read_parameters<Params>()->is_master){
        if(get_active_mp()->get_name()=="handshake"){
            nlohmann::json response,request;
            request["name"]="handshake";
            request["content"]=nlohmann::json();
            if(read_parameters<Params>()->mode==TelepresenceMode::tmDirectCart){
                request["content"]["O_T_EE_master"]=msrm_utils::from_eigen<double,4,4>(p.proprioception.O_T_EE);
            }
            if(read_parameters<Params>()->mode==TelepresenceMode::tmDirectJoint){
                request["content"]["q_master"]=msrm_utils::from_eigen<double,7,1>(p.proprioception.q);
            }
            if(m_handshake_stage==0){
                spdlog::debug("Telepresence: Starting handshake (master)");
                if(read_parameters<Params>()->multicast){
                    for(const auto& ip : read_parameters<Params>()->multicast_group){
                        m_handshake_message_uuid=m_portal->send_message(ip,read_parameters<Params>()->ws_port_dst,"post_event",request);
                    }
                    m_handshake_stage=2;
                    m_memory->post_event("sync_done",nlohmann::json());
                }else{
                    m_handshake_message_uuid=m_portal->send_message(read_parameters<Params>()->ip_dst,read_parameters<Params>()->ws_port_dst,"post_event",request);
                    m_handshake_stage=1;
                }
            }
            if(m_handshake_stage==1){
                nlohmann::json response = m_portal->get_message_response(m_handshake_message_uuid);
                if(response.is_boolean()){
                    m_handshake_stage=0;
                    return {};
                }else if(response.is_null()){
                    return {};
                }else{
                    m_handshake_stage=2;
                }
            }
            if(m_handshake_stage==2){
                if(m_memory->get_event("sync_done")!=nullptr){
                    spdlog::debug("Telepresence: Received sync_done (master)");
                    m_memory->remove_event("sync_done");
                    std::shared_ptr<ManipulationPrimitive> mp = create_mp("telepresence",p);
                    if(read_parameters<Params>()->mode==TelepresenceMode::tmDirectCart){
                        mp->create_strategy<CartComplianceStrategy>("compliance",1);
                        if(!read_parameters<Params>()->multicast){
                            mp->create_strategy<RemoteWrenchStrategy>("telepresence",1);
                            mp->get_strategy<RemoteWrenchStrategy>("telepresence")->set_damping(get_parameters<Params>()->direct_cart.alpha);
                            if(!mp->get_strategy<RemoteWrenchStrategy>("telepresence")->connect(m_portal,"remote_wrench_in",get_parameters<Params>()->port_src,256,0,10000,200)){
                                throw SkillException("Could not open incoming udp channel.");
                            }
                        }
                        m_udp_sender = m_portal->open_udp_outstream("remote_cart_pose_out",read_parameters<Params>()->ip_dst,read_parameters<Params>()->port_dst);
                        Eigen::Matrix<double,6,1> K_x_0;
                        Eigen::Matrix<double,6,1> xi_x_0;
                        K_x_0<<0,0,0,0,0,0;
                        xi_x_0<<0,0,0,0,0,0;
                        mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(K_x_0,xi_x_0);
                    }
                    if(read_parameters<Params>()->mode==TelepresenceMode::tmDirectJoint){
                        mp->create_strategy<JointComplianceStrategy>("compliance",1);
                        if(!read_parameters<Params>()->multicast){
                            mp->create_strategy<RemoteTorqueStrategy>("telepresence",1);
                            mp->get_strategy<RemoteTorqueStrategy>("telepresence")->set_damping(get_parameters<Params>()->direct_joint.alpha);
                            if(!mp->get_strategy<RemoteTorqueStrategy>("telepresence")->connect(m_portal,"remote_torque_in",get_parameters<Params>()->port_src,256,0,10000,200)){
                                throw SkillException("Could not open incoming udp channel.");
                            }
                        }
                        m_udp_sender = m_portal->open_udp_outstream("remote_joint_pose_out",read_parameters<Params>()->ip_dst,read_parameters<Params>()->port_dst);
                        Eigen::Matrix<double,7,1> K_theta_0;
                        Eigen::Matrix<double,7,1> xi_theta_0;
                        K_theta_0<<0,0,0,0,0,0,0;
                        xi_theta_0<<0,0,0,0,0,0,0;
                        mp->get_strategy<JointComplianceStrategy>("compliance")->set_complicance(K_theta_0,xi_theta_0);
                    }
                    if(read_parameters<Params>()->mode==TelepresenceMode::tmJoystick){
                        if(!read_parameters<Params>()->multicast){
                            mp->create_strategy<RemoteWrenchStrategy>("telepresence",1);
                            if(!mp->get_strategy<RemoteWrenchStrategy>("telepresence")->connect(m_portal,"remote_wrench_in",get_parameters<Params>()->port_src,256,0,10000,200)){
                                throw SkillException("Could not open incoming udp channel.");
                            }
                        }
                        m_udp_sender = m_portal->open_udp_outstream("remote_twist_out",read_parameters<Params>()->ip_dst,read_parameters<Params>()->port_dst);
                    }
                    if(m_udp_sender==nullptr){
                        throw SkillException("Could not open outgoing udp channel.");
                    }
                    if(!m_udp_sender->connect()){
                        throw SkillException("Could not open outgoing udp channel.");
                    }
                    return mp;
                }
            }
        }
        if(get_active_mp()->get_name()=="telepresence"){
            if(!read_parameters<Params>()->multicast && get_active_mp()->get_strategy_interface("telepresence")->finished()){
                m_handshake_stage=0;
                spdlog::trace("Telepresence: Terminating telepresence (master)");
                std::shared_ptr<ManipulationPrimitive> mp = create_mp("handshake",p);
                if(read_parameters<Params>()->mode==TelepresenceMode::tmDirectCart){
                    m_portal->close_udp_outstream("remote_cart_pose_out");
                    m_portal->close_udp_instream("remote_wrench_in");
                }
                if(read_parameters<Params>()->mode==TelepresenceMode::tmDirectJoint){
                    m_portal->close_udp_outstream("remote_joint_pose_out");
                    m_portal->close_udp_instream("remote_torque_in");
                }
                if(read_parameters<Params>()->mode==TelepresenceMode::tmJoystick){
                    m_portal->close_udp_outstream("remote_twist_out");
                    m_portal->close_udp_instream("remote_wrench_in");
                }
                nlohmann::json response;
                spdlog::trace("Telepresence:graph_transition.master.finished");
                mp->create_strategy<NullStrategy>("idle",1);
                return mp;
            }
        }
    }else{
        if(get_active_mp()->get_name()=="handshake"){
            if(m_memory->get_event("handshake")!=nullptr){
                spdlog::debug("Telepresence: Received handshake (slave)");
                std::shared_ptr<ManipulationPrimitive> mp = create_mp("sync",p);
                if(read_parameters<Params>()->mode==TelepresenceMode::tmDirectCart){
                    msrm_utils::read_json_param<double,4,4>(m_memory->get_event("handshake")->get_content(),"O_T_EE_master",m_O_T_EE_master);
                    mp->create_strategy<MoveToPoseStrategy>("move",1);
                    std::cout<<"MASTER: "<<m_O_T_EE_master<<std::endl;
                    mp->get_strategy<MoveToPoseStrategy>("move")->set_goal(m_O_T_EE_master,m_memory->read_parameters()->user.dX_default,m_memory->read_parameters()->user.ddX_default);
                }
                if(read_parameters<Params>()->mode==TelepresenceMode::tmDirectJoint){
                    msrm_utils::read_json_param<double,7,1>(m_memory->get_event("handshake")->get_content(),"q_master",m_q_master);
                    mp->create_strategy<MoveToJointPoseStrategy>("move",1);
                    mp->get_strategy<MoveToJointPoseStrategy>("move")->set_goal(m_q_master,0.5,2);
                }
                if(read_parameters<Params>()->mode==TelepresenceMode::tmJoystick){
                    mp->create_strategy<NullStrategy>("move",1);
                }
                m_memory->remove_event("handshake");
                return mp;
            }
            else{
                return {};
            }
        }
        if(get_active_mp()->get_name()=="sync"){
            if(get_active_mp()->get_strategy_interface("move")->finished()){
                if(read_parameters<Params>()->mode==TelepresenceMode::tmDirectJoint && (m_q_master-p.proprioception.q).norm()>0.1){
                    spdlog::error("The master pose and my own pose do not match after syncing.");
                    invoke_failure();
                    return {};
                }
                if(read_parameters<Params>()->mode==TelepresenceMode::tmDirectCart && (m_O_T_EE_master.block<3,1>(0,3)-p.proprioception.O_T_EE.block<3,1>(0,3)).norm()>0.02){
                    spdlog::error("The master pose and my own pose do not match after syncing.");
                    invoke_failure();
                    return {};
                }
                nlohmann::json response;
                if(m_handshake_stage==0){
                    spdlog::debug("Telepresence: Sending sync_done (slave)");
                    m_handshake_message_uuid=m_portal->send_message(read_parameters<Params>()->ip_dst,read_parameters<Params>()->ws_port_dst,"post_event",{{"name","sync_done"}});
                    m_handshake_stage++;
                }
                if(m_handshake_stage==1){
                    nlohmann::json response = m_portal->get_message_response(m_handshake_message_uuid);
                    if(response.is_boolean()){
                        m_handshake_stage=0;
                        return {};
                    }else if(response.is_null()){
                        return {};
                    }else{
                        m_handshake_stage=2;
                    }
                }
                std::shared_ptr<ManipulationPrimitive> mp = create_mp("telepresence",p);
                if(read_parameters<Params>()->mode==TelepresenceMode::tmDirectCart){
                    mp->create_strategy<RemoteCartPoseStrategy>("telepresence",1);
                    if(!mp->get_strategy<RemoteCartPoseStrategy>("telepresence")->connect(m_portal,"remote_cart_pose_in",get_parameters<Params>()->port_src,256,0,10000,20,read_parameters<Params>()->multicast)){
                        throw SkillException("Could not open incoming udp channel.");
                    }
                    m_udp_sender = m_portal->open_udp_outstream("remote_force_out",read_parameters<Params>()->ip_dst,read_parameters<Params>()->port_dst);
                    mp->create_strategy<FFStrategy>("feed_forward",1);
                    mp->get_strategy<FFStrategy>("feed_forward")->set_TF_F_ff(read_parameters<Params>()->direct_cart.F_ff,m_memory->read_parameters()->limits.cartesian_space.dF_J_max);
                    mp->get_strategy<FFStrategy>("feed_forward")->set_frame(true);
                    if(read_parameters<Params>()->direct_cart.plane){
                        mp->create_strategy<CartComplianceStrategy>("compliance",1);
                        Eigen::Matrix<double,6,1> K_x_0;
                        Eigen::Matrix<double,6,1> xi_x_0;
                        K_x_0=m_memory->read_parameters()->control.cart_imp.K_x;
                        xi_x_0=m_memory->read_parameters()->control.cart_imp.xi_x;
                        K_x_0(2)=0;
                        xi_x_0(2)=0;
                        mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(K_x_0,xi_x_0);
                    }
                }
                if(read_parameters<Params>()->mode==TelepresenceMode::tmDirectJoint){
                    mp->create_strategy<RemoteJointPoseStrategy>("telepresence",1);
                    if(!mp->get_strategy<RemoteJointPoseStrategy>("telepresence")->connect(m_portal,"remote_joint_pose_in",get_parameters<Params>()->port_src,256,0,10000,20,read_parameters<Params>()->multicast)){
                        throw SkillException("Could not open incoming udp channel.");
                    }
                    m_udp_sender = m_portal->open_udp_outstream("remote_torque_out",read_parameters<Params>()->ip_dst,read_parameters<Params>()->port_dst);
                }
                if(read_parameters<Params>()->mode==TelepresenceMode::tmJoystick){
                    mp->create_strategy<RemoteTwistStrategy>("telepresence",1);
                    if(!mp->get_strategy<RemoteTwistStrategy>("telepresence")->connect(m_portal,"remote_twist_in",get_parameters<Params>()->port_src,256,0,10000,200,read_parameters<Params>()->multicast)){
                        throw SkillException("Could not open incoming udp channel.");
                    }
                    mp->get_strategy<RemoteTwistStrategy>("telepresence")->set_frame(read_parameters<Params>()->joystick.static_frame);
                    m_udp_sender = m_portal->open_udp_outstream("remote_force_out",read_parameters<Params>()->ip_dst,read_parameters<Params>()->port_dst);
                }
                if(m_udp_sender==nullptr){
                    throw SkillException("Could not open outgoing udp channel.");
                }
                if(!m_udp_sender->connect()){
                    throw SkillException("Could not open outgoing udp channel.");
                }
                return mp;
            }
        }
        if(get_active_mp()->get_name()=="telepresence"){
            if(get_active_mp()->get_strategy_interface("telepresence")->finished()){
                m_handshake_stage=0;
                spdlog::debug("Telepresence: Terminating telepresence (slave)");
                std::shared_ptr<ManipulationPrimitive> mp = create_mp("handshake",p);
                if(read_parameters<Params>()->mode==TelepresenceMode::tmDirectCart){
                    m_portal->close_udp_outstream("remote_force_out");
                    m_portal->close_udp_instream("remote_cart_pose_in");
                }
                if(read_parameters<Params>()->mode==TelepresenceMode::tmDirectJoint){
                    m_portal->close_udp_outstream("remote_torque_out");
                    m_portal->close_udp_instream("remote_joint_pose_in");
                }
                if(read_parameters<Params>()->mode==TelepresenceMode::tmJoystick){
                    m_portal->close_udp_outstream("remote_force_out");
                    m_portal->close_udp_instream("remote_twist_in");
                }
                nlohmann::json response;
                mp->create_strategy<NullStrategy>("idle",1);
                return mp;
            }
        }
    }
    return {};
}

void Telepresence::auxiliaries(const Percept &p){
    if(get_active_mp()->get_name()=="telepresence"){
        std::vector<double> payload;
        if(get_parameters<Params>()->is_master){
            if(read_parameters<Params>()->mode==TelepresenceMode::tmDirectCart){
                for(unsigned i=0;i<4;i++){
                    for(unsigned j=0;j<4;j++){
                        payload.emplace_back(p.proprioception.T_T_EE(j,i));
                    }
                }
            }
            if(read_parameters<Params>()->mode==TelepresenceMode::tmDirectJoint){
                for(unsigned i=0;i<7;i++){
                    payload.emplace_back(p.proprioception.q(i));
                }
            }
            if(read_parameters<Params>()->mode==TelepresenceMode::tmJoystick){
                Eigen::Matrix<double,6,1> joystick_command;
                for(unsigned i=0;i<6;i++){
                    if(fabs(p.proprioception.TF_F_ext_K(i))>get_parameters<Params>()->joystick.force_thr(i)){
                        joystick_command(i)=-(fabs(p.proprioception.TF_F_ext_K(i))-get_parameters<Params>()->joystick.force_thr(i))*
                                msrm_utils::sgn(p.proprioception.TF_F_ext_K(i))*get_parameters<Params>()->joystick.amp(i);
                    }else{
                        joystick_command(i)=0;
                    }
                    payload.emplace_back(joystick_command(i));
                }
            }
        }else{
            if(read_parameters<Params>()->mode==TelepresenceMode::tmDirectCart){
                for(unsigned i=0;i<6;i++){
                    payload.emplace_back(p.proprioception.TF_F_ext_K(i));
                }
            }
            if(read_parameters<Params>()->mode==TelepresenceMode::tmDirectJoint){
                for(unsigned i=0;i<7;i++){
                    payload.emplace_back(p.proprioception.tau_ext(i));
                }
            }
            if(read_parameters<Params>()->mode==TelepresenceMode::tmJoystick){
                for(unsigned i=0;i<6;i++){
                    payload.emplace_back(p.proprioception.TF_F_ext_K(i));
                }
            }
        }
        if(!(!read_parameters<Params>()->is_master && read_parameters<Params>()->multicast)){
            if(read_parameters<Params>()->use_zoh_deadband){
                std::vector<double> diff(payload.size());
                double mag_diff=0;
                double mag_prev=0;
                for(unsigned i=0;i<payload.size();i++){
                    diff[i]=payload[i]-m_previous_payload[i];
                    mag_diff+=pow(diff[i],2);
                    mag_prev+=pow(m_previous_payload[i],2);
                }
                mag_diff=sqrt(mag_diff);
                mag_prev=sqrt(mag_prev);
                if(mag_diff/(mag_prev+0.00001) >= read_parameters<Params>()->deadband_k){
                    m_udp_sender->send(payload);
                    m_previous_payload=payload;
                }
            }else{
                m_udp_sender->send(payload);
            }
        }
    }
}

bool Telepresence::check_local_suc_conditions(const Percept &p){
    return false;
}

}

