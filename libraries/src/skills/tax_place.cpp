#include "skills/tax_place.hpp"
#include "strategies/twist_strategy.hpp"
#include "strategies/move_to_pose.hpp"
#include "strategies/gripper_strategy.hpp"
#include "strategies/cart_compliance_strategy.hpp"
#include "strategies/twist_strategy.hpp"
#include "msrm_utils/math.hpp"

namespace mios{

bool SkillParametersTaxPlace::from_json(const nlohmann::json& parameters){
    if(parameters.find("p0")==parameters.end()){
        spdlog::error("Parameters for primitive 0 are missing.");
        return false;
    }else if(parameters.find("p0")!=parameters.end()){
        if(!msrm_utils::read_json_param<double,6,1>(parameters["p0"],"K_x",p0.K_x)){
            spdlog::error("Missing parameter: p0.K_x");
            return false;
        }
        if(!msrm_utils::read_json_param<double,2,1>(parameters["p0"],"dX_d",p0.dX_d)){
            spdlog::error("Missing parameter: p0.dX_d");
            return false;
        }
        if(!msrm_utils::read_json_param<double,2,1>(parameters["p0"],"ddX_d",p0.ddX_d)){
            spdlog::error("Missing parameter: p0.ddX_d");
            return false;
        }
    }
    if(parameters.find("p1")==parameters.end()){
        spdlog::error("Parameters for primitive 1 are missing.");
        return false;
    }else if(parameters.find("p1")!=parameters.end()){
        if(!msrm_utils::read_json_param<double,6,1>(parameters["p1"],"K_x",p1.K_x)){
            spdlog::error("Missing parameter: p1.K_x");
            return false;
        }
        if(!msrm_utils::read_json_param<double,2,1>(parameters["p1"],"dX_d",p1.dX_d)){
            spdlog::error("Missing parameter: p1.dX_d");
            return false;
        }
        if(!msrm_utils::read_json_param<double,2,1>(parameters["p1"],"ddX_d",p1.ddX_d)){
            spdlog::error("Missing parameter: p1.ddX_d");
            return false;
        }
    }
    if(parameters.find("p2")==parameters.end()){
        spdlog::error("Parameters for primitive 2 are missing.");
        return false;
    }else if(parameters.find("p2")!=parameters.end()){
        if(!msrm_utils::read_json_param<double,6,1>(parameters["p2"],"K_x",p2.K_x)){
            spdlog::error("Missing parameter: p2.K_x");
            return false;
        }
        if(!msrm_utils::read_json_param(parameters["p2"],"release_speed",p2.release_speed)){
            spdlog::error("Missing parameter: p2.release_speed");
            return false;
        }
        if(!msrm_utils::read_json_param(parameters["p2"],"release_width",p2.release_width)){
            spdlog::error("Missing parameter: p2.release_width");
            return false;
        }
    }
    if(parameters.find("p3")==parameters.end()){
        spdlog::error("Parameters for primitive 3 are missing.");
        return false;
    }else if(parameters.find("p3")!=parameters.end()){
        if(!msrm_utils::read_json_param<double,6,1>(parameters["p3"],"K_x",p3.K_x)){
            spdlog::error("Missing parameter: p3.K_x");
            return false;
        }
        if(!msrm_utils::read_json_param<double,2,1>(parameters["p3"],"dX_d",p3.dX_d)){
            spdlog::error("Missing parameter: p3.dX_d");
            return false;
        }
        if(!msrm_utils::read_json_param<double,2,1>(parameters["p3"],"ddX_d",p3.ddX_d)){
            spdlog::error("Missing parameter: p3.ddX_d");
            return false;
        }
    }
    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersTaxPlace::get_parameter_list(){
    return {{"p0",{"K_x","dX_d","ddX_d"}},{"p1",{"K_x","dX_d","ddX_d"}},{"p2",{"K_x","release_speed","release_force","grasp_width"}},{"p3",{"K_x","dX_d","ddX_d"}}};
}

TaxPlace::TaxPlace(const std::string& name, Memory* memory, Portal* portal):Skill("TaxPlace",{"Placeable","Surface", "Approach", "Retract"},name,memory,portal,{ControlMode::mCartTorque,ControlMode::mCartVelocity}){

}

Eigen::Matrix<double,3,3> TaxPlace::get_O_R_T_0(const Percept &p) const{
    if(get_object("Surface")->name!="NullObject"){
        return get_object("Surface")->O_T_OB.block<3,3>(0,0);
    }else{
        throw SkillException("No valid object has been grounded.");
    }
}

std::shared_ptr<ManipulationPrimitive> TaxPlace::get_initial_mp(const Percept& p){
    return create_approach_mp(p);
}

std::optional<std::shared_ptr<ManipulationPrimitive> > TaxPlace::graph_transition(const Percept &p){
    if(get_active_mp()->get_name()=="approach"){
        if(get_active_mp()->get_strategy_interface("move")->finished()){
            return create_contact_mp(p);
        }else{
            return {};
        }
    }
    if(get_active_mp()->get_name()=="contact"){
        if(p.proprioception.TF_F_ext_K(2)>m_memory->read_parameters()->user.F_ext_contact(0)){
            return create_release_mp(p);
        }else{
            return {};
        }
    }
    if(get_active_mp()->get_name()=="release"){
//        if(get_result().success){
        if(get_active_mp()->get_strategy_interface("release")->finished()){
            return create_retract_mp(p);
        }else{
            return {};
        }
    }
    return {};
}

std::shared_ptr<ManipulationPrimitive> TaxPlace::create_approach_mp(const Percept &p){
    spdlog::trace("TaxPlace::create_approach_mp");
    std::shared_ptr<SkillParametersTaxPlace> skill_params = get_parameters<SkillParametersTaxPlace>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("approach",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("Approach"),skill_params->p0.dX_d,skill_params->p0.ddX_d);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p0.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxPlace::create_contact_mp(const Percept &p){
    spdlog::trace("TaxPlace::create_contact_mp");
    std::shared_ptr<SkillParametersTaxPlace> skill_params = get_parameters<SkillParametersTaxPlace>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("contact",p);
    mp->create_strategy<TwistStrategy>("move",1);
    std::shared_ptr<TwistStrategy> move = mp->get_strategy<TwistStrategy>("move");
    Eigen::Matrix<double,6,1> dX_d;
    Eigen::Matrix<double,3,1> dir=get_object_pose_T("Surface").block<3,1>(0,3)-p.proprioception.T_T_EE.block<3,1>(0,3);;
    dir/=dir.norm();
    dX_d<<dir*skill_params->p1.dX_d(0),0,0,0;
    move->set_TF_dX_d(dX_d,skill_params->p1.ddX_d);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p1.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxPlace::create_release_mp(const Percept &p){
    spdlog::trace("TaxPlace::create_release_mp");
    std::shared_ptr<SkillParametersTaxPlace> skill_params = get_parameters<SkillParametersTaxPlace>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("release",p);
    mp->create_strategy<GripperStrategy>("release",1);
    std::shared_ptr<GripperStrategy> release = mp->get_strategy<GripperStrategy>("release");
    release->move(skill_params->p2.release_width,skill_params->p2.release_speed);
    std::cout<<skill_params->p2.release_speed<<std::endl;
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p2.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxPlace::create_retract_mp(const Percept &p){
    spdlog::trace("TaxPlace::create_retract_mp");
    std::shared_ptr<SkillParametersTaxPlace> skill_params = get_parameters<SkillParametersTaxPlace>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("retract",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("Retract"),skill_params->p3.dX_d,skill_params->p3.ddX_d);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p3.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

bool TaxPlace::check_local_pre_conditions(const Percept &p){
    return true;
    Eigen::Matrix<double,4,4> T_container = get_object_pose_T("Surface");
    std::shared_ptr<SkillParametersTaxPlace> skill_params = get_parameters<SkillParametersTaxPlace>();
    for(unsigned i=0;i<3;i++){
        if(p.proprioception.T_T_EE(3,i)<T_container(3,i)+skill_params->ROI_x(i*2) || p.proprioception.T_T_EE(3,i)>T_container(3,i)+skill_params->ROI_x(i*2+1)){
            return false;
        }
    }
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Placeable")->name){
        return false;
    }
    return true;
}

bool TaxPlace::check_local_suc_conditions(const Percept &p){
    if(m_memory->get_live_context()->grasped_object->name=="NullObject"){
        return true;
    }
    return false;
}

bool TaxPlace::check_local_ex_conditions(const Percept &p){
    if(get_active_mp()->get_name()=="retract"){
        if(get_active_mp()->get_strategy_interface("move")->finished()){
            return true;
        }
    }
    return false;
}


bool TaxPlace::check_local_err_conditions(const Percept &p){
    const Eigen::Matrix<double,6,1>& ROI_x=get_parameters<SkillParametersTaxPlace>()->ROI_x;
    const Eigen::Matrix<double,6,1>& ROI_phi=get_parameters<SkillParametersTaxPlace>()->ROI_phi;
    double error_angle=acos(p.proprioception.T_T_EE.block<3,1>(0,2).dot(get_object_pose_T("Surface").block<3,1>(0,2)));
    Eigen::Matrix<double,3,1> dist = p.proprioception.T_T_EE.block<3,1>(0,3)-get_object_pose_T("Surface").block<3,1>(0,3);
    if(dist(0) < ROI_x(0) || dist(0) > ROI_x(1) || dist(1) < ROI_x(2) || dist(1) > ROI_x(3) || dist(2) < ROI_x(4) || dist(2) > ROI_x(5)){
        return true;
    }
    return false;
}

double TaxPlace::get_goal_heuristic(const Percept &p){
//    bool h = m_memory->get_live_context()->grasped_object->name==get_object("Placeable")->name;
    bool h = !get_result().success;
    return (get_result().p_1.proprioception.T_T_EE.block<3,1>(0,3)-get_object_pose_T("Retract").block<3,1>(0,3)).norm() +
            acos(((get_object_pose_T("Retract").block<3,3>(0,0).transpose()*p.proprioception.T_T_EE.block<3,3>(0,0)).trace()-1)/2) +
            h * 1;
}

}
