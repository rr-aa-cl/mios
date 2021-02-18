#include "skills/tax_tip.hpp"
#include "strategies/twist_strategy.hpp"
#include "strategies/move_to_pose.hpp"

namespace mios{

bool SkillParametersTaxTip::from_json(const nlohmann::json& parameters){
    if(!msrm_utils::read_json_param(parameters,"f_contact",f_contact)){
        spdlog::error("Parameter f_contact could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"approach_speed",approach_speed)){
        spdlog::error("Parameter approach_speed could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"approach_acc",approach_acc)){
        spdlog::error("Parameter approach_acc could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"tip_speed",tip_speed)){
        spdlog::error("Parameter tip_speed could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"tip_acc",tip_acc)){
        spdlog::error("Parameter tip_acc could not be loaded but is mandatory.");
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

std::map<std::string, std::set<std::string> > SkillParametersTaxTip::get_parameter_list(){
    return {{"f_contact",{}},{"approach_speed",{}},{"approach_acc",{}},{"tip_speed",{}},{"tip_acc",{}},{"ROI_x",{}},{"ROI_phi",{}}};
}

TaxTip::TaxTip(const std::string& name, Memory* memory, Portal* portal):Skill("TaxTip",{"Tippable", "Approach"},name,memory,portal,{ControlMode::mCartTorque,ControlMode::mCartVelocity}){

}

Eigen::Matrix<double,3,3> TaxTip::get_O_R_T_0(const Percept &p) const{
    if(get_object("Tippable")->name!="NullObject"){
        return get_object("Tippable")->O_T_OB.block<3,3>(0,0);
    }else{
        throw SkillException("No valid object has been grounded.");
    }
}

std::shared_ptr<ManipulationPrimitive> TaxTip::get_initial_mp(const Percept& p){
    return create_approach_mp(p);
}

std::optional<std::shared_ptr<ManipulationPrimitive> > TaxTip::graph_transition(const Percept &p){
    if(get_active_mp()->get_name()=="approach"){
        if(get_active_mp()->get_strategy_interface("move")->finished()){
            return create_push_mp(p);
        }else{
            return {};
        }
    }
    if(get_active_mp()->get_name()=="tip"){
        if(get_active_mp()->get_strategy_interface("tip")->finished() && p.proprioception.TF_F_ext_K(2)>get_parameters<SkillParametersTaxTip>()->f_contact){
            return create_retract_mp(p);
        }else{
            return {};
        }
    }
    return {};
}

std::shared_ptr<ManipulationPrimitive> TaxTip::create_approach_mp(const Percept &p){
    std::shared_ptr<SkillParametersTaxTip> skill_params = get_parameters<SkillParametersTaxTip>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("approach",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("Approach"),skill_params->approach_speed,skill_params->approach_acc);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxTip::create_push_mp(const Percept &p){
    std::shared_ptr<SkillParametersTaxTip> skill_params = get_parameters<SkillParametersTaxTip>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("tip",p);
    mp->create_strategy<MoveToPoseStrategy>("tip",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("tip");
    move->set_goal(get_object_pose_T("Tippable"),skill_params->tip_speed,skill_params->tip_acc);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxTip::create_retract_mp(const Percept &p){
    std::shared_ptr<SkillParametersTaxTip> skill_params = get_parameters<SkillParametersTaxTip>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("retract",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("Approach"),skill_params->tip_speed,skill_params->tip_acc);
    return mp;
}

bool TaxTip::check_local_pre_conditions(const Percept &p){
    Eigen::Matrix<double,4,4> T_container = get_object_pose_T("Tippable");
    std::shared_ptr<SkillParametersTaxTip> skill_params = get_parameters<SkillParametersTaxTip>();
    for(unsigned i=0;i<3;i++){
        if(p.proprioception.T_T_EE(3,i)<T_container(3,i)+skill_params->ROI_x(i*2) || p.proprioception.T_T_EE(3,i)<T_container(3,i)+skill_params->ROI_x(i*2+1)){
            return false;
        }
    }
    return true;
}

bool TaxTip::check_local_suc_conditions(const Percept &p){
    std::shared_ptr<SkillParametersTaxTip> skill_params = get_parameters<SkillParametersTaxTip>();
    if(p.proprioception.TF_F_ext_K(2)>skill_params->f_contact){
        return true;
    }
    return false;
}

bool TaxTip::check_local_ex_conditions(const Percept &p){
    if(get_active_mp()->get_name()=="retract"){
        return get_active_mp()->get_strategy_interface("move")->finished();
    }
    return false;
}


bool TaxTip::check_local_err_conditions(const Percept &p){
    const Eigen::Matrix<double,6,1>& ROI_x=get_parameters<SkillParametersTaxTip>()->ROI_x;
    const Eigen::Matrix<double,6,1>& ROI_phi=get_parameters<SkillParametersTaxTip>()->ROI_phi;
    double error_angle=acos(p.proprioception.T_T_EE.block<3,1>(0,2).dot(get_object_pose_T("Tippable").block<3,1>(0,2)));
    Eigen::Matrix<double,3,1> dist = p.proprioception.T_T_EE.block<3,1>(0,3)-get_object_pose_T("Tippable").block<3,1>(0,3);
    if(dist(0) < ROI_x(0) || dist(0) > ROI_x(1) || dist(1) < ROI_x(2) || dist(1) > ROI_x(3) || dist(2) < ROI_x(4) || dist(2) > ROI_x(5)){
        return true;
    }
    return false;
}

}
