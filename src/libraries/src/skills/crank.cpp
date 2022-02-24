#include "mios/skills/crank.hpp"
#include "mios/strategies/twist_wiggle_strategy.hpp"
#include "mios/strategies/cart_compliance_strategy.hpp"

namespace mios{


bool SkillParametersCrank::from_json(const nlohmann::json &parameters){
    if(parameters.find("p0")==parameters.end()){
        spdlog::error("Parameters for primitive 0 are missing.");
        return false;
    }else if(parameters.find("p0")!=parameters.end()){
        if(!mirmi_utils::read_json_param<double,6,1>(parameters["p0"],"K_x",p0.K_x)){
            spdlog::error("Missing parameter: p0.K_x");
            return false;
        }
        if(!mirmi_utils::read_json_param<double,2,1>(parameters["p0"],"dX_d",p0.dX_d)){
            spdlog::error("Missing parameter: p0.dX_d");
            return false;
        }
        if(!mirmi_utils::read_json_param<double,2,1>(parameters["p0"],"ddX_d",p0.ddX_d)){
            spdlog::error("Missing parameter: p0.ddX_d");
            return false;
        }
        if(!mirmi_utils::read_json_param(parameters["p0"],"radius",p0.radius)){
            spdlog::error("Missing parameter: p0.radius");
            return false;
        }
        if(!mirmi_utils::read_json_param(parameters["p0"],"n_turns",p0.n_turns)){
            spdlog::error("Missing parameter: p0.n_turns");
            return false;
        }
        if(!mirmi_utils::read_json_param(parameters["p0"],"clockwise",p0.clockwise)){
            spdlog::error("Missing parameter: p0.clockwise");
            return false;
        }
    }
    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersCrank::get_parameter_list(){
    return {{"p0",{"K_x","dX_d","ddX_d","radius","n_turns","clockwise"}}};
}

Crank::Crank(const std::string &name, Memory *memory,Portal* portal):Skill("Crank",{"Crank","Center"},name,memory,portal,{ControlMode::mCartTorque}){
}

Eigen::Matrix<double, 3, 3> Crank::get_O_R_T_0([[maybe_unused]] const Percept &p) const{
    return get_object("Crank")->O_T_OB.block<3,3>(0,0);
}

std::shared_ptr<ManipulationPrimitive> Crank::get_initial_mp(const Percept &p_0){
    return create_crank_mp(p_0);
}

std::optional<std::shared_ptr<ManipulationPrimitive> > Crank::graph_transition(const Percept &p){
    return {};
}

std::shared_ptr<ManipulationPrimitive> Crank::create_crank_mp(const Percept &p){
    spdlog::trace("Draw::create_crank_mp");
    std::shared_ptr<SkillParametersCrank> skill_params = get_parameters<SkillParametersCrank>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("crank",p);
    mp->create_strategy<TwistWiggleStrategy>("crank",1);
    Eigen::Matrix<double,6,1> b_a;
    Eigen::Matrix<double,6,1> b_f;
    Eigen::Matrix<double,6,1> b_phi;
    b_a<<skill_params->p0.radius,skill_params->p0.radius,0,0,0,0;
    double f=skill_params->p0.dX_d(0)/skill_params->p0.radius;
    Eigen::Matrix<double,3,1> zero_line,current_line;
    zero_line<<1,0,0;
    current_line=p.proprioception.T_T_EE.block<3,1>(0,3)-get_object_pose_T("Center").block<3,1>(0,3);
    current_line(2)=0;
    current_line=current_line/current_line.norm();
    double phi_0=atan2(current_line(0),current_line(1));
    std::cout<<"phi_0: "<<phi_0<<std::endl;
    b_f<<f,f,0,0,0,0;
    if(skill_params->p0.clockwise){
        phi_0-=M_PI*1.5;
        b_phi<<phi_0+M_PI*0.5,phi_0,0,0,0,0;
    }else{
        b_phi<<phi_0,phi_0+M_PI*0.5,0,0,0,0;

    }

    mp->get_strategy<TwistWiggleStrategy>("crank")->set_coefficients(Eigen::Matrix<double,6,1>::Zero(),b_a,Eigen::Matrix<double,6,1>::Zero(),b_f,Eigen::Matrix<double,6,1>::Zero(),b_phi);
    return mp;
}

bool Crank::check_local_pre_conditions(const Percept &p){
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Crank")->name){
        spdlog::error("Crank skill: I have not grasped the crank.");
        return false;
    }
    return true;
}

bool Crank::check_local_suc_conditions(const Percept &p){
    std::shared_ptr<SkillParametersCrank> skill_params = get_parameters<SkillParametersCrank>();
    double f=skill_params->p0.dX_d(0)/skill_params->p0.radius;
    if(std::chrono::duration_cast<std::chrono::milliseconds>(p.time-m_memory->get_live_context()->t_mp).count()>1000*skill_params->p0.n_turns/f){
        return true;
    }
    return false;
}

bool Crank::check_local_err_conditions(const Percept &p){
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Crank")->name){
        spdlog::error("Crank skill: I lost crank.");
        return true;
    }
    return false;
}


}
