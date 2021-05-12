#include "skills/tax_slide.hpp"
#include "strategies/ff_strategy.hpp"
#include "strategies/move_to_pose.hpp"
#include "strategies/cart_compliance_strategy.hpp"
#include <msrm_utils/math.hpp>

namespace mios{

bool SkillParametersTaxSlide::from_json(const nlohmann::json& parameters){
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
        if(!msrm_utils::read_json_param(parameters["p0"],"f_slide",p0.f_slide)){
            spdlog::error("Missing parameter: p0.f_slide");
            return false;
        }
    }
    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersTaxSlide::get_parameter_list(){
    return {{"p0",{"K_x","dX_d","ddX_d","f_slide"}}};
}

TaxSlide::TaxSlide(const std::string& name, Memory* memory, Portal *portal):Skill("TaxSlide",{"Surface","Slidable","GoalPose"},name,memory,portal,{ControlMode::mCartTorque}){

}

Eigen::Matrix<double,3,3> TaxSlide::get_O_R_T_0(const Percept &p) const{
    if(get_object("Surface")->name!="NullObject"){
        return get_object("Surface")->O_T_OB.block<3,3>(0,0);
    }else{
        throw SkillException("No valid object has been grounded.");
    }
}

std::shared_ptr<ManipulationPrimitive> TaxSlide::get_initial_mp(const Percept& p){
    return create_slide_mp(p);
}

std::shared_ptr<ManipulationPrimitive> TaxSlide::create_slide_mp(const Percept &p){
    spdlog::trace("TaxSlide::create_slide_mp()");
    std::shared_ptr<SkillParametersTaxSlide> skill_params = get_parameters<SkillParametersTaxSlide>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("pull",p);
    mp->create_strategy<MoveToPoseStrategy>("slide",1);
    mp->create_strategy<FFStrategy>("push",1);
    std::shared_ptr<MoveToPoseStrategy> slide = mp->get_strategy<MoveToPoseStrategy>("slide");
    slide->set_goal(get_object_pose_T("GoalPose"),skill_params->p0.dX_d,skill_params->p0.ddX_d);
    std::shared_ptr<FFStrategy> push = mp->get_strategy<FFStrategy>("push");
    Eigen::Matrix<double,6,1> F_d;
    F_d<<0,0,skill_params->p0.f_slide,0,0,0;
    push->set_TF_F_ff(F_d,m_memory->read_parameters()->limits.cartesian_space.dF_J_max);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p0.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

bool TaxSlide::check_local_pre_conditions(const Percept &p){
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Slidable")->name){
        return false;
    }
//    if(p.proprioception.TF_F_ext_K(2)<m_memory->read_parameters()->user.F_ext_contact(0)){
//        return false;
//    }
    return true;
}

bool TaxSlide::check_local_suc_conditions(const Percept &p){
    return get_active_mp()->get_strategy_interface("slide")->finished();
}

bool TaxSlide::check_local_err_conditions(const Percept &p){
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Slidable")->name){
        return true;
    }
//    if(p.proprioception.TF_F_ext_K(2)<m_memory->read_parameters()->user.F_ext_contact(0)){
//        return false;
//    }
    return false;
}

}
