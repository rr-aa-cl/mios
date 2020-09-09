#include "skills/tip.hpp"
#include "strategies/twist_strategy.hpp"
#include "strategies/move_to_pose.hpp"

namespace mios{

bool SkillParametersTip::from_json(const nlohmann::json& parameters){
    if(!msrm_utils::read_json_param(parameters,"f_contact",f_contact)){
        spdlog::error("Parameter f_contact could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"speed",speed)){
        spdlog::error("Parameter speed could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"acceleration",acceleration)){
        spdlog::error("Parameter acceleration could not be loaded but is mandatory.");
        return false;
    }
    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersTip::get_parameter_list(){
    return {{"f_contact",{}},{"speed",{}},{"acceleration",{}}};
}

Tip::Tip(const std::string& name, Memory* memory, Portal* portal):Skill("Tip",{"tippable"},name,memory,portal,{ControlMode::mCartTorque,ControlMode::mCartVelocity}){

}

Eigen::Matrix<double,3,3> Tip::get_O_R_T_0(const Percept &p) const{
    if(get_object("tippable")->name!="NullObject"){
        return get_object("tippable")->O_T_OB.block<3,3>(0,0);
    }else{
        throw SkillException("No valid object has been grounded.");
    }
}

std::shared_ptr<ManipulationPrimitive> Tip::get_initial_mp(const Percept& p){
    std::shared_ptr<SkillParametersTip> skill_params = get_parameters<SkillParametersTip>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("tip",p);
    mp->create_strategy<TwistStrategy>("twist",1);
    Eigen::Matrix<double,6,1> TF_dX_d;
    TF_dX_d<<0,0,skill_params->speed,0,0,0;
    Eigen::Matrix<double,2,1> ddX_max;
    ddX_max<<skill_params->acceleration,0;
    mp->get_strategy<TwistStrategy>("twist")->set_TF_dX_d(TF_dX_d,ddX_max);
    m_TF_T_EE_0=p.proprioception.T_T_EE;
    return mp;
}

std::optional<std::shared_ptr<ManipulationPrimitive> > Tip::graph_transition(const Percept &p){
    if(get_active_mp()->get_name()=="tip"){
        std::shared_ptr<SkillParametersTip> skill_params = get_parameters<SkillParametersTip>();
        if(p.proprioception.TF_F_ext_K(2)>skill_params->f_contact){
            std::shared_ptr<ManipulationPrimitive> mp = create_mp("retract",p);
            mp->create_strategy<MoveToPoseStrategy>("move",1);
            Eigen::Matrix<double,2,1> dX_d,ddX_d,t_scale;
            t_scale<<1,1;
            dX_d<<skill_params->speed,m_memory->read_parameters()->user.dX_default(1);
            ddX_d<<skill_params->acceleration,m_memory->read_parameters()->user.ddX_default(1);
            mp->get_strategy<MoveToPoseStrategy>("move")->set_goal(m_TF_T_EE_0,dX_d,ddX_d);
            mp->get_strategy<MoveToPoseStrategy>("move")->set_scale(t_scale);
            return mp;
        }
    }
    return {};
}

bool Tip::check_local_suc_conditions(const Percept &p){
    std::shared_ptr<SkillParametersTip> skill_params = get_parameters<SkillParametersTip>();
    if(p.proprioception.TF_F_ext_K(2)>skill_params->f_contact){
        return true;
    }
    return false;
}

bool Tip::check_local_ex_conditions(const Percept &p){
    if(get_active_mp()->get_name()=="retract"){
        return get_active_mp()->get_strategy_interface("move")->finished();
    }
    return false;
}

}
