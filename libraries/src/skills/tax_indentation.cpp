#include "skills/tax_indentation.hpp"
#include "strategies/desired_wrench_strategy.hpp"
#include "strategies/move_to_pose.hpp"
#include <msrm_cpp_utils/math.hpp>

namespace mios{

bool SkillParametersTaxIndentation::from_json(const nlohmann::json& parameters){
    if(!msrm_utils::read_json_param<double,3,1>(parameters,"F_push",F_push)){
        spdlog::error("Parameter F_push could not be loaded but is mandatory.");
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
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"approach_speed",approach_speed)){
        spdlog::error("Parameter approach_speed could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"approach_acc",approach_acc)){
        spdlog::error("Parameter approach_acc could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters,"ROI_phi",ROI_phi)){
        spdlog::error("Parameter ROI_phi could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"distance",distance)){
        spdlog::error("Parameter DX_max could not be loaded but is mandatory.");
        return false;
    }
    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersTaxIndentation::get_parameter_list(){
    return {{"F_push",{}},{"distance",{}},{"approach_speed",{}},{"approach_acc",{}},{"ROI_x",{}},{"ROI_phi",{}}};
}

TaxIndentation::TaxIndentation(const std::string& name, Memory* memory, Portal *portal):Skill("TaxIndentation",{"Surface", "Approach"},name,memory,portal,{ControlMode::mCartTorque}){

}

Eigen::Matrix<double,3,3> TaxIndentation::get_O_R_T_0(const Percept &p) const{
    if(get_object("Surface")->name!="NullObject"){
        return get_object("Surface")->O_T_OB.block<3,3>(0,0);
    }else{
        throw SkillException("No valid object has been grounded.");
    }
}

std::shared_ptr<ManipulationPrimitive> TaxIndentation::get_initial_mp(const Percept& p){
    return create_approach_mp(p);
}

std::optional<std::shared_ptr<ManipulationPrimitive> > TaxIndentation::graph_transition(const Percept &p){
    if(get_active_mp()->get_name()=="approach"){
        if(get_active_mp()->get_strategy_interface("move")->finished()){
            return create_contact_mp(p);
        }else{
            return {};
        }
    }
    if(get_active_mp()->get_name()=="contact"){
        if(p.proprioception.TF_F_ext_K(2)>m_memory->read_parameters()->user.F_ext_contact(2)){
            return create_push_mp(p);
        }else{
            return {};
        }
    }
    if(get_active_mp()->get_name()=="push"){
        std::shared_ptr<SkillParametersTaxIndentation> skill_params = get_parameters<SkillParametersTaxIndentation>();
        if((p.proprioception.T_T_EE.block<3,1>(0,3)-m_T_T_EE_contact.block<3,1>(0,3)).norm()>=skill_params->distance){
            return create_retract_mp(p);
        }else{
            return {};
        }
    }
    return {};
}

std::shared_ptr<ManipulationPrimitive> TaxIndentation::create_approach_mp(const Percept &p){
    std::shared_ptr<SkillParametersTaxIndentation> skill_params = get_parameters<SkillParametersTaxIndentation>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("approach",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("Approach"),skill_params->approach_speed,skill_params->approach_acc);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxIndentation::create_contact_mp(const Percept &p){
    m_T_T_EE_contact=p.proprioception.T_T_EE;
    std::shared_ptr<SkillParametersTaxIndentation> skill_params = get_parameters<SkillParametersTaxIndentation>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("contact",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("Surface"),skill_params->approach_speed,skill_params->approach_acc);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxIndentation::create_push_mp(const Percept &p){
    std::shared_ptr<SkillParametersTaxIndentation> skill_params = get_parameters<SkillParametersTaxIndentation>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("push",p);
    mp->create_strategy<DesiredWrenchStrategy>("wrench",1);
    Eigen::Matrix<double,6,1> TF_F_d;
    TF_F_d<<skill_params->F_push,0,0,0;
    mp->get_strategy<DesiredWrenchStrategy>("wrench")->set_TF_F_d(TF_F_d,m_memory->read_parameters()->limits.cartesian_space.dF_J_max);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxIndentation::create_retract_mp(const Percept &p){
    std::shared_ptr<SkillParametersTaxIndentation> skill_params = get_parameters<SkillParametersTaxIndentation>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("retract",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("Approach"),skill_params->approach_speed,skill_params->approach_acc);
    return mp;
}

bool TaxIndentation::check_local_pre_conditions(const Percept &p){
    Eigen::Matrix<double,4,4> T_container = get_object_pose_T("Surface");
    std::shared_ptr<SkillParametersTaxIndentation> skill_params = get_parameters<SkillParametersTaxIndentation>();
    for(unsigned i=0;i<3;i++){
        if(p.proprioception.T_T_EE(3,i)<T_container(3,i)+skill_params->ROI_x(i*2) || p.proprioception.T_T_EE(3,i)<T_container(3,i)+skill_params->ROI_x(i*2+1)){
            return false;
        }
    }
    return true;
}

bool TaxIndentation::check_local_suc_conditions(const Percept &p){
    return get_active_mp()->get_name()=="retract" && get_active_mp()->get_strategy_interface("move")->finished();
}

bool TaxIndentation::check_local_err_conditions(const Percept &p){
    const Eigen::Matrix<double,6,1>& ROI_x=get_parameters<SkillParametersTaxIndentation>()->ROI_x;
    const Eigen::Matrix<double,6,1>& ROI_phi=get_parameters<SkillParametersTaxIndentation>()->ROI_phi;
    double error_angle=acos(p.proprioception.T_T_EE.block<3,1>(0,2).dot(get_object_pose_T("Surface").block<3,1>(0,2)));
    Eigen::Matrix<double,3,1> dist = p.proprioception.T_T_EE.block<3,1>(0,3)-get_object_pose_T("Surface").block<3,1>(0,3);
    if(dist(0) < ROI_x(0) || dist(0) > ROI_x(1) || dist(1) < ROI_x(2) || dist(1) > ROI_x(3) || dist(2) < ROI_x(4) || dist(2) > ROI_x(5)){
        return true;
    }
    return false;
}

}
