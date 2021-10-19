#include "mios/strategies/ff_strategy.hpp"
#include "mios/strategies/cart_compliance_strategy.hpp"
#include "mios/strategies/twist_strategy.hpp"
#include "mios/skills/tax_screw_out.hpp"
#include "mios/strategies/desired_wrench_strategy.hpp"
#include "mios/strategies/move_to_pose.hpp"
#include "msrm_cpp_utils/math/math.hpp"

namespace mios{

bool SkillParametersTaxScrewOut::from_json(const nlohmann::json& parameters){
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
        if(!msrm_utils::read_json_param<double,2,1>(parameters["p2"],"dX_d",p2.dX_d)){
            spdlog::error("Missing parameter: p1.dX_d");
            return false;
        }
        if(!msrm_utils::read_json_param<double,2,1>(parameters["p2"],"ddX_d",p2.ddX_d)){
            spdlog::error("Missing parameter: p2.ddX_d");
            return false;
        }
        if(!msrm_utils::read_json_param(parameters["p2"],"f_screw",p2.f_screw)){
            spdlog::error("Missing parameter: p2.f_screw");
            return false;
        }
        if(!msrm_utils::read_json_param(parameters["p2"],"phi",p2.phi)){
            spdlog::error("Missing parameter: p2.phi");
            return false;
        }
    }
    if(parameters.find("p3")==parameters.end()){
        spdlog::error("Parameters for primitive 1 are missing.");
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

std::map<std::string, std::set<std::string> > SkillParametersTaxScrewOut::get_parameter_list(){
    return {{"p0",{"K_x","dX_d","ddX_d"}},{"p1",{"K_x","dX_d","ddX_d"}},{"p2",{"K_x","dX_d","ddX_d","f_screw","phi"}},{"p3",{"K_x","dX_d","ddX_d"}}};
}

TaxScrewOut::TaxScrewOut(const std::string& name, Memory* memory, Portal *portal):Skill("TaxScrewOut",{"Screw","Approach","Screwdriver","GoalPosition"},name,memory,portal,{ControlMode::mCartTorque}){

}

Eigen::Matrix<double,3,3> TaxScrewOut::get_O_R_T_0(const Percept &p) const{
    return get_object("Screw")->O_T_OB.block<3,3>(0,0);
}

std::shared_ptr<ManipulationPrimitive> TaxScrewOut::get_initial_mp(const Percept& p){
    return create_approach_mp(p);
}

std::optional<std::shared_ptr<ManipulationPrimitive> > TaxScrewOut::graph_transition(const Percept &p){
    if(get_active_mp()->get_name()=="approach"){
        if(get_active_mp()->get_strategy_interface("move")->finished()){
            return create_contact_mp(p);
        }else{
            return {};
        }
    }
    if(get_active_mp()->get_name()=="contact"){
        if(p.proprioception.TF_F_ext_K(2)>m_memory->read_parameters()->user.F_ext_contact(0)){
            return create_screw_mp(p);
        }else{
            return {};
        }
    }
    if(get_active_mp()->get_name()=="screw"){
        if(get_active_mp()->get_strategy_interface("move")->finished()){
            m_current_approach_pose(2,3)+=p.proprioception.T_T_EE(2,3)-m_current_screw_pose(2,3);
            m_current_screw_pose(2,3)=p.proprioception.T_T_EE(2,3);
            return create_reset_mp(p);
        }else{
            return {};
        }
    }
    if(get_active_mp()->get_name()=="reset"){
        if(get_active_mp()->get_strategy_interface("move")->finished()){
            return create_contact_mp(p);
        }else{
            return {};
        }
    }
    return {};
}

std::shared_ptr<ManipulationPrimitive> TaxScrewOut::create_approach_mp(const Percept &p){
    spdlog::trace("TaxScrew::create_approach_mp");
    m_current_approach_pose=get_object_pose_T("Approach");
    m_current_screw_pose=get_object_pose_T("Screw");
    std::shared_ptr<SkillParametersTaxScrewOut> skill_params = get_parameters<SkillParametersTaxScrewOut>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("approach",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    Eigen::Matrix<double,4,4> T_a = m_current_approach_pose;
    move->set_goal(T_a,skill_params->p0.dX_d,skill_params->p0.ddX_d);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p0.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxScrewOut::create_contact_mp(const Percept &p){
    spdlog::trace("TaxScrew::create_contact_mp");
    std::shared_ptr<SkillParametersTaxScrewOut> skill_params = get_parameters<SkillParametersTaxScrewOut>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("contact",p);
    mp->create_strategy<TwistStrategy>("move",1);
    std::shared_ptr<TwistStrategy> move = mp->get_strategy<TwistStrategy>("move");
    Eigen::Matrix<double,6,1> dX_d;
    Eigen::Matrix<double,3,1> dir=m_current_screw_pose.block<3,1>(0,3)-p.proprioception.T_T_EE.block<3,1>(0,3);;
    dir/=dir.norm();
    dX_d<<dir*skill_params->p1.dX_d(0),0,0,0;
    move->set_TF_dX_d(dX_d,skill_params->p1.ddX_d);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p1.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxScrewOut::create_screw_mp(const Percept &p){
    spdlog::trace("TaxScrew::create_screw_mp()");
    std::shared_ptr<SkillParametersTaxScrewOut> skill_params = get_parameters<SkillParametersTaxScrewOut>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("screw",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    mp->create_strategy<FFStrategy>("push",1);
    std::shared_ptr<FFStrategy> push = mp->get_strategy<FFStrategy>("push");
    Eigen::Matrix<double,6,1> F_d;
    F_d<<0,0,skill_params->p2.f_screw,0,0,0;
    push->set_TF_F_ff(F_d,m_memory->read_parameters()->limits.cartesian_space.dF_J_max);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    Eigen::Matrix<double,4,4> goal_pose=p.proprioception.T_T_EE;
    goal_pose.block<3,3>(0,0)=msrm_utils::eulerRPY_to_mat(0,0,skill_params->p2.phi)*get_object_pose_T("Approach").block<3,3>(0,0);
    move->set_goal(goal_pose,skill_params->p2.dX_d,skill_params->p2.ddX_d);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p2.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxScrewOut::create_reset_mp(const Percept &p){
    spdlog::trace("TaxScrew::create_reset_mp()");
    std::shared_ptr<SkillParametersTaxScrewOut> skill_params = get_parameters<SkillParametersTaxScrewOut>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("reset",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    Eigen::Matrix<double,4,4> T_a = m_current_approach_pose;
    move->set_goal(T_a,skill_params->p3.dX_d,skill_params->p3.ddX_d);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p3.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

bool TaxScrewOut::check_local_pre_conditions(const Percept &p){
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Screwdriver")->name){
        return false;
    }
    return true;
}

bool TaxScrewOut::check_local_suc_conditions(const Percept &p){
    std::shared_ptr<SkillParametersTaxScrewOut> skill_params = get_parameters<SkillParametersTaxScrewOut>();
    if(get_active_mp()->get_name()=="screw"){
        if(is_in_env("GoalPosition",p,true)){
            return true;
        }
    }
    return false;
}

bool TaxScrewOut::check_local_ex_conditions(const Percept &p){
    std::shared_ptr<SkillParametersTaxScrewOut> skill_params = get_parameters<SkillParametersTaxScrewOut>();
    if(get_active_mp()->get_name()=="reset" && get_result().success){
        if(get_active_mp()->get_strategy_interface("move")->finished()){
            return true;
        }
    }
    return false;
}

bool TaxScrewOut::check_local_err_conditions(const Percept &p){
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Screwdriver")->name){
        return true;
    }
//    if(get_active_mp()->get_name()=="swipe"){
//        if(p.proprioception.TF_F_ext_K(2)<m_memory->read_parameters()->user.F_ext_contact(0)){
//            return true;
//        }
//    }
    return false;
}

}
