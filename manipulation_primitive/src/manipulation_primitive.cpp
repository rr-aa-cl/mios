#include "manipulation_primitive/manipulation_primitive.hpp"
#include "memory/memory.hpp"
#include <spdlog/spdlog.h>

namespace mios {

ManipulationPrimitive::ManipulationPrimitive(const std::string& name, const Percept &p_0, Memory *memory)
    :m_name(name),m_memory(memory),m_cmd(Actuator(p_0,memory->read_parameters()->control)),m_flag_initialized(false),m_flag_terminated(false){
}

Actuator* ManipulationPrimitive::initialize(const Percept &p_0){
    spdlog::debug("ManipulationPrimitive::initialize(p_0)");
    m_cmd.initialize(p_0,m_memory->read_parameters()->control, m_memory->read_parameters()->frames.O_R_T);
    return initialize(p_0,m_cmd);
}

Actuator* ManipulationPrimitive::initialize(const Percept &p_0, const Actuator& cmd){
    spdlog::debug("ManipulationPrimitive::initialize(p_0,cmd)");
    m_cmd.blend(cmd,p_0);
    m_memory->get_live_context()->t_mp=std::chrono::high_resolution_clock::now();
    for(auto& s : m_strategies){
        s.second.cmd.blend(cmd,p_0);
        s.second.strategy->initialize(p_0);
        s.second.strategy->get_next_command(s.second.cmd,p_0);
    }
    m_flag_initialized=true;
    m_flag_terminated=false;
    return &m_cmd;
}

Actuator* ManipulationPrimitive::step(const Percept &p){
    for(auto& s : m_strategies){
        s.second.strategy->get_next_command(s.second.cmd,p);
    }
    if(!compose_command(p)){
        spdlog::error("Command composition at primitive layer failed.");
        m_cmd.stop();
    }
    m_cmd.t=std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::high_resolution_clock::now()-m_memory->get_live_context()->t_mp).count()/1000.0;
    for(auto& s : m_strategies){
        s.second.cmd.t=m_cmd.t;
    }
    m_cmd.write_to_buffer();
    return &m_cmd;
}

void ManipulationPrimitive::terminate(const Percept &p){
    if(m_flag_initialized && !m_flag_terminated){
        for(auto& s : m_strategies){
            s.second.strategy->terminate(p);
        }
    }
}

bool ManipulationPrimitive::compose_command(const Percept& p){
//    m_cmd.set_zero(p);
    m_cmd.TF_dX_d.setZero();
    m_cmd.TF_F_ff.setZero();
    m_cmd.dq_d.setZero();
    m_cmd.tau_ff.setZero();
    if(m_strategies.size()==0){
        return false;
    }
    bool TF_T_EE_d_set=false;
    bool TF_F_d_set=false;
    bool q_d_nullspace_set=false;
    bool q_d_set=false;
    bool tau_d_set=false;
    bool joint_compliance_set=false;
    bool cart_compliance_set=false;
    bool O_R_T_set=false;

    double weight_check=0;

    std::set<CommandPattern> actuator_command_pattern;
    for(auto& s : m_strategies){
        std::set<CommandPattern> strategy_command_pattern = s.second.strategy->get_command_pattern();
        if(strategy_command_pattern.find(CommandPatternCartesianPose)!=strategy_command_pattern.end()){
            if(!TF_T_EE_d_set){
                m_cmd.TF_T_EE_d=s.second.cmd.TF_T_EE_d;
                actuator_command_pattern.insert(CommandPatternCartesianPose);
                TF_T_EE_d_set=true;
            }else{
                spdlog::error("More than one policy is commanding TF_T_EE_d.");
                return false;
            }
        }
        if(strategy_command_pattern.find(CommandPatternJointPose)!=strategy_command_pattern.end()){
            if(!q_d_set){
                m_cmd.q_d=s.second.cmd.q_d;
                actuator_command_pattern.insert(CommandPatternJointPose);
                q_d_set=true;
            }else{
                spdlog::error("More than one policy is commanding q_d.");
                return false;
            }
        }
        if(strategy_command_pattern.find(CommandPatternNullspacePose)!=strategy_command_pattern.end()){
            if(!q_d_nullspace_set){
                m_cmd.q_d_nullspace=s.second.cmd.q_d_nullspace;
                actuator_command_pattern.insert(CommandPatternNullspacePose);
                q_d_nullspace_set=true;
            }else{
                spdlog::error("More than one policy is commanding q_d_nullspace.");
                return false;
            }
        }
        if(strategy_command_pattern.find(CommandPatternDesiredWrench)!=strategy_command_pattern.end()){
            if(!TF_F_d_set){
                m_cmd.TF_F_d=s.second.cmd.TF_F_d;
                actuator_command_pattern.insert(CommandPatternDesiredWrench);
                TF_F_d_set=true;
            }else{
                spdlog::error("More than one policy is commanding TF_F_d.");
                return false;
            }
        }
        if(strategy_command_pattern.find(CommandPatternDesiredTorque)!=strategy_command_pattern.end()){
            if(!tau_d_set){
                m_cmd.tau_d=s.second.cmd.tau_d;
                actuator_command_pattern.insert(CommandPatternDesiredTorque);
                tau_d_set=true;
            }else{
                spdlog::error("More than one policy is commanding tau_d.");
                return false;
            }
        }
        if(strategy_command_pattern.find(CommandPatternO_R_T)!=strategy_command_pattern.end()){
            if(!O_R_T_set){
                m_cmd.O_R_T=s.second.cmd.O_R_T;
                actuator_command_pattern.insert(CommandPatternO_R_T);
                O_R_T_set=true;
            }else{
                spdlog::error("More than one policy is commanding O_R_T.");
                return false;
            }
        }

        if(strategy_command_pattern.find(CommandPatternCartesianTwist)!=strategy_command_pattern.end()){
            m_cmd.TF_dX_d+=s.second.cmd.TF_dX_d*s.second.weight;
            actuator_command_pattern.insert(CommandPatternCartesianTwist);
        }
        if(strategy_command_pattern.find(CommandPatternCartesianFFWrench)!=strategy_command_pattern.end()){
            m_cmd.TF_F_ff+=s.second.cmd.TF_F_ff*s.second.weight;
            actuator_command_pattern.insert(CommandPatternCartesianFFWrench);
        }

        if(strategy_command_pattern.find(CommandPatternCartesianCompliance)!=strategy_command_pattern.end()){
            if(!cart_compliance_set){
                m_cmd.K_x.setZero();
                m_cmd.xi_x.setZero();
                cart_compliance_set=true;
                actuator_command_pattern.insert(CommandPatternCartesianCompliance);
            }
            m_cmd.K_x+=s.second.cmd.K_x*s.second.weight;
            m_cmd.xi_x+=s.second.cmd.xi_x*s.second.weight;
        }

        if(strategy_command_pattern.find(CommandPatternJointVelocities)!=strategy_command_pattern.end()){
            m_cmd.dq_d+=s.second.cmd.dq_d*s.second.weight;
            actuator_command_pattern.insert(CommandPatternJointVelocities);
        }
        if(strategy_command_pattern.find(CommandPatternJointFFTorque)!=strategy_command_pattern.end()){
            m_cmd.tau_ff+=s.second.cmd.tau_ff*s.second.weight;
            actuator_command_pattern.insert(CommandPatternJointFFTorque);
        }
        if(strategy_command_pattern.find(CommandPatternJointCompliance)!=strategy_command_pattern.end()){
            if(!joint_compliance_set){
                m_cmd.K_theta.setZero();
                m_cmd.xi_theta.setZero();
                joint_compliance_set=true;
                actuator_command_pattern.insert(CommandPatternJointCompliance);
            }
            m_cmd.K_theta+=s.second.cmd.K_theta*s.second.weight;
            m_cmd.xi_theta+=s.second.cmd.xi_theta*s.second.weight;
        }

        weight_check+=s.second.weight;
    }
    m_cmd.set_command_pattern(actuator_command_pattern);
    return true;
}

Actuator* ManipulationPrimitive::cmd_from_buffer(){
    m_cmd.read_from_buffer();
    return &m_cmd;
}

Actuator* ManipulationPrimitive::stop(const Percept& p, double stop_factor){
    m_cmd.set_zero(p);
    m_cmd.set_stop_factor(stop_factor);
    return &m_cmd;
}


bool ManipulationPrimitive::get_flag_error() const{
    return m_flag_error;
}

void ManipulationPrimitive::set_flag_error(){
    m_flag_error=true;
}

std::string ManipulationPrimitive::get_name() const{
    return m_name;
}

bool ManipulationPrimitive::is_settled() const{
    return m_cmd.is_settled(m_memory->read_parameters()->limits);
}

const std::shared_ptr<PrimitiveStrategy> ManipulationPrimitive::get_strategy_interface(const std::string &name) const{
    return m_strategies.at(name).strategy;
}

}
