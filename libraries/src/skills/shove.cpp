#include "skills/shove.hpp"
#include "strategies/twist_strategy.hpp"


namespace mios{
bool SkillParametersShove::from_json(const nlohmann::json& parameters){
    if(!msrm_utils::read_json_param<double,4,4>(parameters,"O_T_OB_g",O_T_OB_g)){
        spdlog::error("Parameter O_T_OB_g could not be loaded but is mandatory.");
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
    if(!msrm_utils::read_json_param(parameters,"t_contactless",t_contactless)){
        t_contactless=0;
    }
    if(!msrm_utils::read_json_param(parameters,"delta_x",delta_x)){
        delta_x=0;
    }
    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersShove::get_parameter_list(){
    return {{"O_T_OB_g",{}},{"speed",{}},{"acceleration",{}},{"t_contactless",{}},{"delta_x",{}}};
}

Shove::Shove(const std::string& name, Memory* memory, Portal* portal):Skill("Shove",{"shovable","location"},name,memory,portal,{ControlMode::mCartTorque,ControlMode::mCartVelocity}),
m_in_contact(false){

}

std::shared_ptr<ManipulationPrimitive> Shove::get_initial_mp(const Percept& p){
    std::shared_ptr<SkillParametersShove> skill_params = get_parameters<SkillParametersShove>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("shove",p);
    mp->create_strategy<TwistStrategy>("twist",1);

    Eigen::Matrix<double,4,4> O_T_OB_g;
    if(get_object("location")->name=="NullObject"){
        O_T_OB_g=get_parameters<SkillParametersShove>()->O_T_OB_g;
    }else{
        O_T_OB_g=get_object("location")->O_T_OB;
    }

    Eigen::Matrix<double,3,1> dX_d = (p.controller.O_R_T.inverse()*O_T_OB_g.block<3,1>(0,3)-p.proprioception.T_T_EE.block<3,1>(0,3)).normalized()*skill_params->speed;
    Eigen::Matrix<double,6,1> TF_dX_d;
    TF_dX_d<<dX_d,0,0,0;
    Eigen::Matrix<double,2,1> ddX_max;
    ddX_max<<skill_params->acceleration,0;
    mp->get_strategy<TwistStrategy>("twist")->set_TF_dX_d(TF_dX_d,ddX_max);
    return mp;
}

void Shove::update_policies(const Percept &p){
    std::shared_ptr<SkillParametersShove> skill_params = get_parameters<SkillParametersShove>();
    Eigen::Matrix<double,4,4> O_T_OB_g;
    if(get_object("location")->name=="NullObject"){
        O_T_OB_g=get_parameters<SkillParametersShove>()->O_T_OB_g;
    }else{
        O_T_OB_g=get_object("location")->O_T_OB;
    }

    Eigen::Matrix<double,3,1> dX_d = (p.controller.O_R_T.inverse()*O_T_OB_g.block<3,1>(0,3)-p.proprioception.T_T_EE.block<3,1>(0,3)).normalized()*skill_params->speed;
    Eigen::Matrix<double,6,1> TF_dX_d;
    TF_dX_d<<dX_d,0,0,0;
    Eigen::Matrix<double,2,1> ddX_max;
    ddX_max<<skill_params->acceleration,0;
    get_active_mp()->get_strategy<TwistStrategy>("twist")->set_TF_dX_d(TF_dX_d,ddX_max);
}

void Shove::update_internal_models(const Percept &p){
    update_object("shovable")->O_T_OB=p.proprioception.O_T_EE;
}

bool Shove::check_local_pre_conditions(const Percept &p){
    Eigen::Matrix<double,4,4> O_T_OB = get_object("shovable")->O_T_OB;
    Eigen::Matrix<double,4,4> O_T_OB_g;
    if(get_object("location")->name=="NullObject"){
        O_T_OB_g=get_parameters<SkillParametersShove>()->O_T_OB_g;
    }else{
        O_T_OB_g=get_object("location")->O_T_OB;
    }

    Eigen::Matrix<double,3,1> E_n = p.controller.O_R_T.inverse()*(O_T_OB_g.block<3,1>(0,3)-O_T_OB.block<3,1>(0,3));
    Eigen::Matrix<double,3,1> E_p = p.controller.O_R_T.inverse()*O_T_OB.block<3,1>(0,3);
    if((p.proprioception.T_T_EE.block<3,1>(0,3).dot(E_n)-E_p.dot(E_n))/E_n.norm()<0){
        return true;
    }else{
        return false;
    }
}

bool Shove::check_local_err_conditions(const Percept &p){
    std::shared_ptr<SkillParametersShove> skill_params = get_parameters<SkillParametersShove>();
    double f_contact = p.proprioception.TF_F_ext_K.block<3,1>(0,3).norm();
    if(f_contact>m_memory->read_parameters()->user.F_ext_contact(0)){
        m_in_contact=true;
    }else{
        m_in_contact=false;
        m_t_contact_loss=p.time;
    }

    if(!m_in_contact && std::chrono::duration_cast<std::chrono::milliseconds>(p.time-m_t_contact_loss).count()>skill_params->t_contactless){
        return true;
    }
    return false;
}

bool Shove::check_local_suc_conditions(const Percept &p){
    std::shared_ptr<SkillParametersShove> skill_params = get_parameters<SkillParametersShove>();
    skill_params->O_T_OB_g.block<3,1>(0,3);
    if((skill_params->O_T_OB_g.block<3,1>(0,3)-get_object("shovable")->O_T_OB.block<3,1>(0,3)).norm()<skill_params->delta_x){
        return true;
    }

    return false;
}

}
