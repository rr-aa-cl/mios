#include "skills/tax_spoon.hpp"
#include "strategies/null_strategy.hpp"
#include "strategies/move_to_pose.hpp"
#include <msrm_cpp_utils/math.hpp>

namespace mios{

bool SkillParametersTaxSpoon::from_json(const nlohmann::json& parameters){
    if(!msrm_utils::read_json_param<double,6,1>(parameters,"ROI_x",ROI_x)){
        spdlog::error("Parameter ROI_x could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters,"ROI_phi",ROI_phi)){
        spdlog::error("Parameter ROI_phi could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"dip_speed",dip_speed)){
        spdlog::error("Parameter dip_speed could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"dip_acc",dip_acc)){
        spdlog::error("Parameter dip_acc could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"gather_speed",gather_speed)){
        spdlog::error("Parameter gather_speed could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"gather_acc",gather_acc)){
        spdlog::error("Parameter gather_acc could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"emerge_speed",emerge_speed)){
        spdlog::error("Parameter emerge_speed could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"emerge_acc",emerge_acc)){
        spdlog::error("Parameter emerge_acc could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"liquid_weight",liquid_weight)){
        spdlog::error("Parameter liquid_weight could not be loaded but is mandatory.");
        return false;
    }
    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersTaxSpoon::get_parameter_list(){
    return {{"f_swipe",{}},{"dip_speed",{}},{"dip_acc",{}},{"gather_speed",{}},{"gather_acc",{}},{"emerge_speed",{}},{"emerge_acc",{}},{"liquid_weight",{}},{"ROI_x",{}},{"ROI_phi",{}}};
}

TaxSpoon::TaxSpoon(const std::string& name, Memory* memory, Portal *portal):Skill("TaxSpoon",{"Approach","Dip","Gather","Emerge","Spoon","Spoonable"},name,memory,portal,{ControlMode::mCartTorque}){

}

Eigen::Matrix<double,3,3> TaxSpoon::get_O_R_T_0(const Percept &p) const{
    if(get_object("Spoonable")->name!="NullObject"){
        return get_object("Spoonable")->O_T_OB.block<3,3>(0,0);
    }else{
        throw SkillException("No valid object has been grounded.");
    }
}

std::shared_ptr<ManipulationPrimitive> TaxSpoon::get_initial_mp(const Percept& p){
    return create_approach_mp(p);
}

std::optional<std::shared_ptr<ManipulationPrimitive> > TaxSpoon::graph_transition(const Percept &p){
    if(get_active_mp()->get_name()=="approach"){
        if(get_active_mp()->get_strategy_interface("move")->finished()){
            return create_dip_mp(p);
        }else{
            return {};
        }
    }
    if(get_active_mp()->get_name()=="dip"){
        if(get_active_mp()->get_strategy_interface("move")->finished()){
            return create_gather_mp(p);
        }else{
            return {};
        }
    }
    if(get_active_mp()->get_name()=="gather"){
        if(get_active_mp()->get_strategy_interface("move")->finished()){
            return create_emerge_mp(p);
        }else{
            return {};
        }
    }
    if(get_active_mp()->get_name()=="emerge"){
        if(get_active_mp()->get_strategy_interface("move")->finished()){
            return create_check_mp(p);
        }else{
            return {};
        }
    }
    return {};
}

std::shared_ptr<ManipulationPrimitive> TaxSpoon::create_approach_mp(const Percept &p){
    std::shared_ptr<SkillParametersTaxSpoon> skill_params = get_parameters<SkillParametersTaxSpoon>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("approach",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("Approach"),skill_params->dip_speed,skill_params->dip_acc);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxSpoon::create_dip_mp(const Percept &p){
    std::shared_ptr<SkillParametersTaxSpoon> skill_params = get_parameters<SkillParametersTaxSpoon>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("push",p);
    mp->create_strategy<MoveToPoseStrategy>("push",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("push");
    move->set_goal(get_object_pose_T("SwipeStart"),skill_params->dip_speed,skill_params->dip_acc);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxSpoon::create_gather_mp(const Percept &p){
    std::shared_ptr<SkillParametersTaxSpoon> skill_params = get_parameters<SkillParametersTaxSpoon>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("swipe",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("SwipeEnd"),skill_params->gather_speed,skill_params->gather_acc);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxSpoon::create_emerge_mp(const Percept &p){
    std::shared_ptr<SkillParametersTaxSpoon> skill_params = get_parameters<SkillParametersTaxSpoon>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("retract",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("Retract"),skill_params->emerge_speed,skill_params->emerge_acc);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxSpoon::create_check_mp(const Percept &p){
    std::shared_ptr<SkillParametersTaxSpoon> skill_params = get_parameters<SkillParametersTaxSpoon>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("check",p);
    mp->create_strategy<NullStrategy>("check",1);
    return mp;
}

bool TaxSpoon::check_local_pre_conditions(const Percept &p){
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Spoon")->name){
        return false;
    }
    Eigen::Matrix<double,4,4> T_container = get_object_pose_T("Spoonable");
    std::shared_ptr<SkillParametersTaxSpoon> skill_params = get_parameters<SkillParametersTaxSpoon>();
    for(unsigned i=0;i<3;i++){
        if(p.proprioception.T_T_EE(3,i)<T_container(3,i)+skill_params->ROI_x(i*2) || p.proprioception.T_T_EE(3,i)<T_container(3,i)+skill_params->ROI_x(i*2+1)){
            return false;
        }
    }
    return true;
}

bool TaxSpoon::check_local_suc_conditions(const Percept &p){
    std::shared_ptr<SkillParametersTaxSpoon> skill_params = get_parameters<SkillParametersTaxSpoon>();
    if(get_active_mp()->get_name()=="check" && std::chrono::duration_cast<std::chrono::milliseconds>(p.time-m_memory->get_live_context()->t_mp).count()>1000){
        if(p.proprioception.TF_F_ext_K(2)>skill_params->liquid_weight*9.81){
            return true;
        }
    }
    return false;
}

bool TaxSpoon::check_local_err_conditions(const Percept &p){
    std::shared_ptr<SkillParametersTaxSpoon> skill_params = get_parameters<SkillParametersTaxSpoon>();
    const Eigen::Matrix<double,6,1>& ROI_x=get_parameters<SkillParametersTaxSpoon>()->ROI_x;
    const Eigen::Matrix<double,6,1>& ROI_phi=get_parameters<SkillParametersTaxSpoon>()->ROI_phi;
    double error_angle=acos(p.proprioception.T_T_EE.block<3,1>(0,2).dot(get_object_pose_T("Spoonable").block<3,1>(0,2)));
    Eigen::Matrix<double,3,1> dist = p.proprioception.T_T_EE.block<3,1>(0,3)-get_object_pose_T("Spoonable").block<3,1>(0,3);
    if(dist(0) < ROI_x(0) || dist(0) > ROI_x(1) || dist(1) < ROI_x(2) || dist(1) > ROI_x(3) || dist(2) < ROI_x(4) || dist(2) > ROI_x(5)){
        return true;
    }
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Spoon")->name){
        return true;
    }
    if(get_active_mp()->get_name()=="check" && std::chrono::duration_cast<std::chrono::milliseconds>(p.time-m_memory->get_live_context()->t_mp).count()>1000){
        if(p.proprioception.TF_F_ext_K(2)<skill_params->liquid_weight*9.81){
            return true;
        }
    }
    return false;
}

}
