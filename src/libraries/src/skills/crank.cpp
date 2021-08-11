#include "mios/skills/crank.hpp"
#include "mios/strategies/twist_wiggle_strategy.hpp"
#include "mios/strategies/cart_compliance_strategy.hpp"

namespace mios{


bool SkillParametersCrank::from_json(const nlohmann::json &parameters){
    if(!msrm_utils::read_json_param(parameters,"radius",radius)){
        spdlog::error("Parameter radius could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"n_turns",n_turns)){
        spdlog::error("Parameter n_turns could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"clockwise",clockwise)){
        spdlog::error("Parameter clockwise could not be loaded but is mandatory.");
        return false;
    }

    if(!msrm_utils::read_json_param<double,2,1>(parameters,"crank_speed",crank_speed)){
        spdlog::error("Parameter crank_speed could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"crank_acc",crank_acc)){
        spdlog::error("Parameter crank_acc could not be loaded but is mandatory.");
        return false;
    }
    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersCrank::get_parameter_list(){
    return {{"radius",{}},{"n_turns",{}},{"clockwise",{}},{"crank_speed",{}},{"crank_acc",{}}};
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
    b_a<<skill_params->radius,skill_params->radius,0,0,0,0;
    double f=skill_params->crank_speed(0)/skill_params->radius;
    Eigen::Matrix<double,3,1> zero_line,current_line;
    zero_line<<1,0,0;
    current_line=p.proprioception.T_T_EE.block<3,1>(0,3)-get_object_pose_T("Center").block<3,1>(0,3);
    current_line(2)=0;
    current_line=current_line/current_line.norm();
    double phi_0=atan2(current_line(0),current_line(1));
    std::cout<<"phi_0: "<<phi_0<<std::endl;
    b_f<<f,f,0,0,0,0;
    if(skill_params->clockwise){
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
    double f=skill_params->crank_speed(0)/skill_params->radius;
    if(std::chrono::duration_cast<std::chrono::milliseconds>(p.time-m_memory->get_live_context()->t_mp).count()>1000*skill_params->n_turns/f){
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
