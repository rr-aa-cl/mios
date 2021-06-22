#include "mios/skills/turn.hpp"

#include "mios/strategies/twist_strategy.hpp"

namespace mios{
bool SkillParametersTurn::from_json(const nlohmann::json& parameters){
    if(!msrm_utils::read_json_param(parameters,"phi",phi)){
        spdlog::error("Parameter phi could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"dphi",dphi)){
        spdlog::error("Parameter dphi could not be loaded but is mandatory.");
        return false;
    }
    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersTurn::get_parameter_list(){
    return {{"phi",{}},{"dphi",{}}};
}

Turn::Turn(const std::string& id, Memory* memory, Portal* portal):Skill("Turn",{"turnable"},id,memory,portal,{ControlMode::mCartTorque,ControlMode::mCartVelocity}){

}

std::shared_ptr<ManipulationPrimitive> Turn::get_initial_mp(const Percept& p){
    std::shared_ptr<SkillParametersTurn> skill_params = get_parameters<SkillParametersTurn>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("turn",p);
    mp->create_strategy<TwistStrategy>("twist",1);
    Eigen::Matrix<double,6,1> TF_dX_d;
    TF_dX_d<<0,0,0,0,0,skill_params->dphi;
    Eigen::Matrix<double,2,1> ddX_max;
    mp->get_strategy<TwistStrategy>("twist")->set_TF_dX_d(TF_dX_d,m_memory->read_parameters()->user.ddX_default);
    m_T_T_EE_0=p.proprioception.T_T_EE;
    return mp;
}

Eigen::Matrix<double,3,3> Turn::get_O_R_T_0(const Percept &p) const{
    if(get_object("turnable")->name!="NullObject"){
        return get_object("turnable")->O_T_OB.block<3,3>(0,0);
    }else{
        throw SkillException("No valid object has been grounded.");
    }
}

bool Turn::check_local_suc_conditions(const Percept &p){
    Eigen::Matrix<double,3,3> T_R_EE_diff = p.proprioception.T_T_EE.block<3,3>(0,0)*m_T_T_EE_0.block<3,3>(0,0).transpose();
    double phi_current = atan2(T_R_EE_diff(1,0),T_R_EE_diff(0,0));
    if(phi_current>get_parameters<SkillParametersTurn>()->phi){
        return true;
    }
    return false;
}

}
