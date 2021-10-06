#include "mios/strategies/cart_compliance_strategy.hpp"
#include "mios/skills/tax_drag.hpp"
#include "mios/strategies/move_to_pose.hpp"
#include "msrm_cpp_utils/math/math.hpp"

namespace mios{

bool SkillParametersTaxDrag::from_json(const nlohmann::json& parameters){
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
    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersTaxDrag::get_parameter_list(){
    return {{"p0",{"K_x","f_pull","duration"}}};
}

TaxDrag::TaxDrag(const std::string& name, Memory* memory, Portal *portal):Skill("TaxDrag",{"Draggable", "GoalPose"},name,memory,portal,{ControlMode::mCartTorque}){

}

Eigen::Matrix<double,3,3> TaxDrag::get_O_R_T_0([[maybe_unused]] const Percept &p) const{
    return get_object("Draggable")->O_T_OB.block<3,3>(0,0);
}

std::shared_ptr<ManipulationPrimitive> TaxDrag::get_initial_mp(const Percept& p){
    return create_drag_mp(p);
}

std::shared_ptr<ManipulationPrimitive> TaxDrag::create_drag_mp(const Percept &p){
    spdlog::trace("TaxDrag::create_drag_mp");
    std::shared_ptr<SkillParametersTaxDrag> skill_params = get_parameters<SkillParametersTaxDrag>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("drag",p);
    mp->create_strategy<MoveToPoseStrategy>("drag",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("drag");
    move->set_goal(get_object_pose_T("GoalPose"),skill_params->p0.dX_d,skill_params->p0.ddX_d);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p0.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

bool TaxDrag::check_local_pre_conditions([[maybe_unused]] const Percept &p){
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Draggable")->name){
        return false;
    }
    return true;
}

bool TaxDrag::check_local_suc_conditions(const Percept &p){
    if(is_in_env("GoalPose",p)){
        return true;
    }else{
        return false;
    }
}

bool TaxDrag::check_local_err_conditions([[maybe_unused]] const Percept &p){
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Draggable")->name){
        return true;
    }
    return false;
}

double TaxDrag::get_goal_heuristic(const Percept &p){
    return (p.proprioception.T_T_EE.block<3,1>(0,3)-get_object_pose_T("GoalPose").block<3,1>(0,3)).norm() +
            acos(((get_object_pose_T("GoalPose").block<3,3>(0,0).transpose()*p.proprioception.T_T_EE.block<3,3>(0,0)).trace()-1)/2);
}

}
