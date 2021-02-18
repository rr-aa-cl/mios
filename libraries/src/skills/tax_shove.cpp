#include "skills/tax_shove.hpp"
#include "strategies/twist_strategy.hpp"
#include "strategies/move_to_pose.hpp"


namespace mios{
bool SkillParametersTaxShove::from_json(const nlohmann::json& parameters){
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"approach_speed",approach_speed)){
        spdlog::error("Parameter approach_speed could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"approach_acc",approach_acc)){
        spdlog::error("Parameter approach_acc could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"shove_speed",shove_speed)){
        spdlog::error("Parameter shove_speed could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"shove_acc",shove_acc)){
        spdlog::error("Parameter shove_acc could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters,"ROI_x",ROI_x)){
        spdlog::error("Parameter ROI_x could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters,"ROI_phi",ROI_phi)){
        spdlog::error("Parameter ROI_phi could not be loaded but is mandatory.");
        return false;
    }
    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersTaxShove::get_parameter_list(){
    return {{"approach_speed",{}},{"approach_acc",{}},{"shove_speed",{}},{"shove_acc",{}},{"ROI_x",{}},{"ROI_phi",{}}};
}

TaxShove::TaxShove(const std::string& name, Memory* memory, Portal* portal):Skill("TaxShove",{"Shovable","Approach","Location"},name,memory,portal,{ControlMode::mCartTorque,ControlMode::mCartVelocity}){

}

std::shared_ptr<ManipulationPrimitive> TaxShove::get_initial_mp(const Percept& p){
    return create_approach_mp(p);
}

std::optional<std::shared_ptr<ManipulationPrimitive> > TaxShove::graph_transition(const Percept &p){
    if(get_active_mp()->get_name()=="approach"){
        if(get_active_mp()->get_strategy_interface("move")->finished()){
            return create_contact_mp(p);
        }else{
            return {};
        }
    }
    if(get_active_mp()->get_name()=="contact"){
        if(p.proprioception.TF_F_ext_K(2)>m_memory->read_parameters()->user.F_ext_contact(2)){
            return create_shove_mp(p);
        }else{
            return {};
        }
    }
    return {};
}

std::shared_ptr<ManipulationPrimitive> TaxShove::create_approach_mp(const Percept &p){
    std::shared_ptr<SkillParametersTaxShove> skill_params = get_parameters<SkillParametersTaxShove>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("approach",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("Approach"),skill_params->approach_speed,skill_params->approach_acc);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxShove::create_contact_mp(const Percept &p){
    std::shared_ptr<SkillParametersTaxShove> skill_params = get_parameters<SkillParametersTaxShove>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("contact",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("Shoveable"),skill_params->approach_speed,skill_params->approach_acc);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxShove::create_shove_mp(const Percept &p){
    std::shared_ptr<SkillParametersTaxShove> skill_params = get_parameters<SkillParametersTaxShove>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("approach",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("Location"),skill_params->shove_speed,skill_params->shove_acc);
    return mp;
}

void TaxShove::update_internal_models(const Percept &p){
    update_object("Shovable")->O_T_OB=p.proprioception.O_T_EE;
}

bool TaxShove::check_local_pre_conditions(const Percept &p){
    Eigen::Matrix<double,4,4> T_shoveable = get_object_pose_T("Shoveable");
    std::shared_ptr<SkillParametersTaxShove> skill_params = get_parameters<SkillParametersTaxShove>();
    for(unsigned i=0;i<3;i++){
        if(p.proprioception.T_T_EE(3,i)<T_shoveable(3,i)+skill_params->ROI_x(i*2) || p.proprioception.T_T_EE(3,i)<T_shoveable(3,i)+skill_params->ROI_x(i*2+1)){
            return false;
        }
    }
    return true;
}

bool TaxShove::check_local_err_conditions(const Percept &p){
    std::shared_ptr<SkillParametersTaxShove> skill_params = get_parameters<SkillParametersTaxShove>();
    double f_contact = p.proprioception.TF_F_ext_K.block<3,1>(0,3).norm();
    if(f_contact<m_memory->read_parameters()->user.F_ext_contact(0)){
        return true;
    }
    return false;
}

bool TaxShove::check_local_suc_conditions(const Percept &p){
    if(get_active_mp()->get_name()=="shove" && get_active_mp()->get_strategy_interface("move")->finished()){
        return true;
    }
    return false;
}

}
