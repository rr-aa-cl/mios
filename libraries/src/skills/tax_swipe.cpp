#include "skills/tax_swipe.hpp"
#include "strategies/desired_wrench_strategy.hpp"
#include "strategies/move_to_pose.hpp"
#include <msrm_cpp_utils/math.hpp>

namespace mios{

bool SkillParametersTaxSwipe::from_json(const nlohmann::json& parameters){
    if(!msrm_utils::read_json_param<double,6,1>(parameters,"ROI_x",ROI_x)){
        spdlog::error("Parameter ROI_x could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters,"ROI_phi",ROI_phi)){
        spdlog::error("Parameter ROI_phi could not be loaded but is mandatory.");
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
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"swipe_speed",swipe_speed)){
        spdlog::error("Parameter swipe_speed could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"swipe_acc",swipe_acc)){
        spdlog::error("Parameter swipe_acc could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"f_swipe",f_swipe)){
        spdlog::error("Parameter f_swipe could not be loaded but is mandatory.");
        return false;
    }
    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersTaxSwipe::get_parameter_list(){
    return {{"f_swipe",{}},{"approach_speed",{}},{"approach_acc",{}},{"swipe_speed",{}},{"swipe_acc",{}},{"ROI_x",{}},{"ROI_phi",{}}};
}

TaxSwipe::TaxSwipe(const std::string& name, Memory* memory, Portal *portal):Skill("TaxSwipe",{"SwipeStart","SwipeEnd","Approach","Retract","Stylus"},name,memory,portal,{ControlMode::mCartTorque}){

}

Eigen::Matrix<double,3,3> TaxSwipe::get_O_R_T_0(const Percept &p) const{
    if(get_object("SwipeStart")->name!="NullObject"){
        return get_object("SwipeStart")->O_T_OB.block<3,3>(0,0);
    }else{
        throw SkillException("No valid object has been grounded.");
    }
}

std::shared_ptr<ManipulationPrimitive> TaxSwipe::get_initial_mp(const Percept& p){
    return create_approach_mp(p);
}

std::optional<std::shared_ptr<ManipulationPrimitive> > TaxSwipe::graph_transition(const Percept &p){
    if(get_active_mp()->get_name()=="approach"){
        if(get_active_mp()->get_strategy_interface("move")->finished()){
            return create_contact_mp(p);
        }else{
            return {};
        }
    }
    if(get_active_mp()->get_name()=="contact"){
        if(p.proprioception.TF_F_ext_K(2)>m_memory->read_parameters()->user.F_ext_contact(2)){
            return create_swipe_mp(p);
        }else{
            return {};
        }
    }
    if(get_active_mp()->get_name()=="swipe"){
        if(get_active_mp()->get_strategy_interface("move")->finished()){
            return create_retract_mp(p);
        }else{
            return {};
        }
    }
    return {};
}

std::shared_ptr<ManipulationPrimitive> TaxSwipe::create_approach_mp(const Percept &p){
    std::shared_ptr<SkillParametersTaxSwipe> skill_params = get_parameters<SkillParametersTaxSwipe>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("approach",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("Approach"),skill_params->approach_speed,skill_params->approach_acc);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxSwipe::create_contact_mp(const Percept &p){
    std::shared_ptr<SkillParametersTaxSwipe> skill_params = get_parameters<SkillParametersTaxSwipe>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("push",p);
    mp->create_strategy<MoveToPoseStrategy>("push",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("push");
    move->set_goal(get_object_pose_T("SwipeStart"),skill_params->approach_speed,skill_params->approach_acc);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxSwipe::create_swipe_mp(const Percept &p){
    std::shared_ptr<SkillParametersTaxSwipe> skill_params = get_parameters<SkillParametersTaxSwipe>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("swipe",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    mp->create_strategy<DesiredWrenchStrategy>("push",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    std::shared_ptr<DesiredWrenchStrategy> push = mp->get_strategy<DesiredWrenchStrategy>("push");
    move->set_goal(get_object_pose_T("SwipeEnd"),skill_params->swipe_speed,skill_params->swipe_acc);
    Eigen::Matrix<double,6,1> F_d;
    F_d<<0,0,skill_params->f_swipe,0,0,0;
    push->set_TF_F_d(F_d,m_memory->read_parameters()->limits.cartesian_space.dF_J_max);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxSwipe::create_retract_mp(const Percept &p){
    std::shared_ptr<SkillParametersTaxSwipe> skill_params = get_parameters<SkillParametersTaxSwipe>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("retract",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("Retract"),skill_params->approach_speed,skill_params->approach_acc);
    return mp;
}

bool TaxSwipe::check_local_pre_conditions(const Percept &p){
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Stylus")->name){
        return false;
    }
    Eigen::Matrix<double,4,4> T_container = get_object_pose_T("SwipeStart");
    std::shared_ptr<SkillParametersTaxSwipe> skill_params = get_parameters<SkillParametersTaxSwipe>();
    for(unsigned i=0;i<3;i++){
        if(p.proprioception.T_T_EE(3,i)<T_container(3,i)+skill_params->ROI_x(i*2) || p.proprioception.T_T_EE(3,i)<T_container(3,i)+skill_params->ROI_x(i*2+1)){
            return false;
        }
    }
    return true;
}

bool TaxSwipe::check_local_suc_conditions(const Percept &p){
    std::shared_ptr<SkillParametersTaxSwipe> skill_params = get_parameters<SkillParametersTaxSwipe>();
        if((p.proprioception.O_T_EE.block<3,1>(0,3)-get_object_pose_T("Approach").block<3,1>(0,3)).norm()<0.005 && get_active_mp()->get_name()=="retract"){
            return true;
        }
    return false;
}

bool TaxSwipe::check_local_err_conditions(const Percept &p){
    const Eigen::Matrix<double,6,1>& ROI_x=get_parameters<SkillParametersTaxSwipe>()->ROI_x;
    const Eigen::Matrix<double,6,1>& ROI_phi=get_parameters<SkillParametersTaxSwipe>()->ROI_phi;
    double error_angle=acos(p.proprioception.T_T_EE.block<3,1>(0,2).dot(get_object_pose_T("Button").block<3,1>(0,2)));
    Eigen::Matrix<double,3,1> dist = p.proprioception.T_T_EE.block<3,1>(0,3)-get_object_pose_T("Button").block<3,1>(0,3);
    if(dist(0) < ROI_x(0) || dist(0) > ROI_x(1) || dist(1) < ROI_x(2) || dist(1) > ROI_x(3) || dist(2) < ROI_x(4) || dist(2) > ROI_x(5)){
        return true;
    }
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Stylus")->name){
        return true;
    }
    return false;
}

}
