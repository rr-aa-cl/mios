#include "skills/tax_grab.hpp"
#include "strategies/twist_strategy.hpp"
#include "strategies/move_to_pose.hpp"
#include "strategies/gripper_strategy.hpp"
#include "strategies/cart_compliance_strategy.hpp"

namespace mios{

bool SkillParametersTaxGrab::from_json(const nlohmann::json& parameters){
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
        if(!msrm_utils::read_json_param(parameters["p0"],"gripper_speed",p0.gripper_speed)){
            spdlog::error("Missing parameter: p0.gripper_speed");
            return false;
        }
        if(!msrm_utils::read_json_param(parameters["p0"],"gripper_width",p0.gripper_width)){
            spdlog::error("Missing parameter: p0.gripper_width");
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
        if(!msrm_utils::read_json_param(parameters["p2"],"grasp_force",p2.grasp_force)){
            spdlog::error("Missing parameter: p2.grasp_force");
            return false;
        }
        if(!msrm_utils::read_json_param(parameters["p2"],"grasp_speed",p2.grasp_speed)){
            spdlog::error("Missing parameter: p2.grasp_speed");
            return false;
        }
        if(!msrm_utils::read_json_param(parameters["p2"],"grasp_width",p2.grasp_width)){
            spdlog::error("Missing parameter: p2.grasp_width");
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

std::map<std::string, std::set<std::string> > SkillParametersTaxGrab::get_parameter_list(){
    return {{"p0",{"K_x","dX_d","ddX_d","gripper_speed","gripper_width"}},{"p1",{"K_x","dX_d","ddX_d"}},{"p2",{"K_x","grasp_speed","grasp_force","grasp_width"}},{"p3",{"K_x","dX_d","ddX_d"}}};
}

TaxGrab::TaxGrab(const std::string& name, Memory* memory, Portal* portal):Skill("TaxGrab",{"Grabbable", "Approach", "Retract"},name,memory,portal,{ControlMode::mCartTorque,ControlMode::mCartVelocity}){

}

Eigen::Matrix<double,3,3> TaxGrab::get_O_R_T_0(const Percept &p) const{
    if(get_object("Grabbable")->name!="NullObject"){
        return get_object("Grabbable")->O_T_OB.block<3,3>(0,0);
    }else{
        throw SkillException("No valid object has been grounded.");
    }
}

std::shared_ptr<ManipulationPrimitive> TaxGrab::get_initial_mp(const Percept& p){
    return create_approach_mp(p);
}

std::optional<std::shared_ptr<ManipulationPrimitive> > TaxGrab::graph_transition(const Percept &p){
    if(get_active_mp()->get_name()=="approach"){
        if(get_active_mp()->get_strategy_interface("move")->finished() && get_active_mp()->get_strategy_interface("open_gripper")->finished()){
            return create_pre_grasp_mp(p);
        }else{
            return {};
        }
    }
    if(get_active_mp()->get_name()=="pre_grasp"){
        if(get_active_mp()->get_strategy_interface("move")->finished()){
            return create_grasp_mp(p);
        }else{
            return {};
        }
    }
    if(get_active_mp()->get_name()=="grasp"){
        if(get_active_mp()->get_strategy_interface("grasp")->finished()){
            return create_retract_mp(p);
        }else{
            return {};
        }
    }
    return {};
}

std::shared_ptr<ManipulationPrimitive> TaxGrab::create_approach_mp(const Percept &p){
    spdlog::trace("TaxGrab::create_approach_mp");
    std::shared_ptr<SkillParametersTaxGrab> skill_params = get_parameters<SkillParametersTaxGrab>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("approach",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("Approach"),skill_params->p0.dX_d,skill_params->p0.ddX_d);
    mp->create_strategy<GripperStrategy>("open_gripper",1);
    mp->get_strategy<GripperStrategy>("open_gripper")->move(skill_params->p0.gripper_speed,1000);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p0.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxGrab::create_pre_grasp_mp(const Percept &p){
    spdlog::trace("TaxGrab::create_pre_grasp_mp");
    std::shared_ptr<SkillParametersTaxGrab> skill_params = get_parameters<SkillParametersTaxGrab>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("pre_grasp",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("Grabbable"),skill_params->p1.dX_d,skill_params->p1.ddX_d);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p1.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxGrab::create_grasp_mp(const Percept &p){
    spdlog::trace("TaxGrab::create_grasp_mp");
    std::shared_ptr<SkillParametersTaxGrab> skill_params = get_parameters<SkillParametersTaxGrab>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("grasp",p);
    mp->create_strategy<GripperStrategy>("grasp",1);
    std::shared_ptr<GripperStrategy> grasp = mp->get_strategy<GripperStrategy>("grasp");
    grasp->grasp(skill_params->p2.grasp_width,skill_params->p2.grasp_speed,skill_params->p2.grasp_force,get_object("Grabbable")->name);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p2.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxGrab::create_retract_mp(const Percept &p){
    spdlog::trace("TaxGrab::create_retract_mp");
    std::shared_ptr<SkillParametersTaxGrab> skill_params = get_parameters<SkillParametersTaxGrab>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("retract",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("Retract"),skill_params->p3.dX_d,skill_params->p3.ddX_d);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p3.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

bool TaxGrab::check_local_pre_conditions(const Percept &p){
    Eigen::Matrix<double,4,4> T_container = get_object_pose_T("Grabbable");
    std::shared_ptr<SkillParametersTaxGrab> skill_params = get_parameters<SkillParametersTaxGrab>();
    for(unsigned i=0;i<3;i++){
        if(p.proprioception.T_T_EE(3,i)<T_container(3,i)+skill_params->ROI_x(i*2) || p.proprioception.T_T_EE(3,i)>T_container(3,i)+skill_params->ROI_x(i*2+1)){
            return false;
        }
    }
    return true;
}

bool TaxGrab::check_local_suc_conditions(const Percept &p){
    if(m_memory->get_live_context()->grasped_object->name==get_object("Grabbable")->name){
        return true;
    }
    return false;
}

bool TaxGrab::check_local_ex_conditions(const Percept &p){
    if(get_active_mp()->get_name()=="retract"){
        if(get_active_mp()->get_strategy_interface("move")->finished()){
            return true;
        }
    }
    return false;
}


bool TaxGrab::check_local_err_conditions(const Percept &p){
    const Eigen::Matrix<double,6,1>& ROI_x=get_parameters<SkillParametersTaxGrab>()->ROI_x;
    const Eigen::Matrix<double,6,1>& ROI_phi=get_parameters<SkillParametersTaxGrab>()->ROI_phi;
    double error_angle=acos(p.proprioception.T_T_EE.block<3,1>(0,2).dot(get_object_pose_T("Grabbable").block<3,1>(0,2)));
    Eigen::Matrix<double,3,1> dist = p.proprioception.T_T_EE.block<3,1>(0,3)-get_object_pose_T("Grabbable").block<3,1>(0,3);
    if(dist(0) < ROI_x(0) || dist(0) > ROI_x(1) || dist(1) < ROI_x(2) || dist(1) > ROI_x(3) || dist(2) < ROI_x(4) || dist(2) > ROI_x(5)){
        return true;
    }
    return false;
}

double TaxGrab::get_goal_heuristic(const Percept &p){
    bool h = !get_result().success;
    return (get_result().p_1.proprioception.T_T_EE.block<3,1>(0,3)-get_object_pose_T("Grabbable").block<3,1>(0,3)).norm() +
            h * (get_object_pose_T("Grabbable").block<3,1>(0,3)-get_object_pose_T("Retract").block<3,1>(0,3)).norm();
}

}
