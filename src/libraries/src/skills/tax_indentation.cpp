#include "mios/strategies/cart_compliance_strategy.hpp"
#include "mios/strategies/ff_strategy.hpp"
#include "mios/strategies/twist_strategy.hpp"
#include "mios/skills/tax_indentation.hpp"
#include "mios/strategies/desired_wrench_strategy.hpp"
#include "mios/strategies/move_to_pose.hpp"
#include "msrm_cpp_utils/math/math.hpp"

namespace mios{

bool SkillParametersTaxIndentation::from_json(const nlohmann::json& parameters){
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
        if(!msrm_utils::read_json_param(parameters["p2"],"f_push",p2.f_push)){
            spdlog::error("Missing parameter: p2.f_push");
            return false;
        }
        if(!msrm_utils::read_json_param(parameters["p2"],"distance",p2.distance)){
            spdlog::error("Missing parameter: p2.distance");
            return false;
        }
    }
    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersTaxIndentation::get_parameter_list(){
    return {{"p0",{"K_x","dX_d","ddX_d"}},{"p1",{"K_x","dX_d","ddX_d"}},{"p2",{"K_x","f_push","distance"}}};
}

TaxIndentation::TaxIndentation(const std::string& name, Memory* memory, Portal *portal):Skill("TaxIndentation",{"Surface", "Approach"},name,memory,portal,{ControlMode::mCartTorque}){

}

Eigen::Matrix<double,3,3> TaxIndentation::get_O_R_T_0([[maybe_unused]] const Percept &p) const{
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
        }
    }
    if(get_active_mp()->get_name()=="contact"){
        if(p.proprioception.TF_F_ext_K(2)>m_memory->read_parameters()->user.F_ext_contact(2)){
            return create_push_mp(p);
        }
    }
    return {};
}

std::shared_ptr<ManipulationPrimitive> TaxIndentation::create_approach_mp(const Percept &p){
    spdlog::trace("TaxIndentation::create_approach_mp");
    std::shared_ptr<SkillParametersTaxIndentation> skill_params = get_parameters<SkillParametersTaxIndentation>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("approach",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    Eigen::Matrix<double,4,4> T_a = get_object_pose_T("Approach");
    move->set_goal(T_a,skill_params->p0.dX_d,skill_params->p0.ddX_d);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p0.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxIndentation::create_contact_mp(const Percept &p){
    spdlog::trace("TaxIndentation::create_contact_mp");
    std::shared_ptr<SkillParametersTaxIndentation> skill_params = get_parameters<SkillParametersTaxIndentation>();
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

std::shared_ptr<ManipulationPrimitive> TaxIndentation::create_push_mp(const Percept &p){
    spdlog::trace("TaxIndentation::create_push_mp");
    m_T_T_EE_contact=p.proprioception.T_T_EE;
    std::shared_ptr<SkillParametersTaxIndentation> skill_params = get_parameters<SkillParametersTaxIndentation>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("push",p);
    mp->create_strategy<DesiredWrenchStrategy>("wrench",1);
    Eigen::Matrix<double,6,1> TF_F_d;
    TF_F_d<<0,0,skill_params->p2.f_push,0,0,0;
    mp->get_strategy<DesiredWrenchStrategy>("wrench")->set_TF_F_d(TF_F_d,m_memory->read_parameters()->limits.cartesian_space.dF_J_max);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p1.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

bool TaxIndentation::check_local_pre_conditions(const Percept &p){
    Eigen::Matrix<double,4,4> T_container = get_object_pose_T("Surface");
    std::shared_ptr<SkillParametersTaxIndentation> skill_params = get_parameters<SkillParametersTaxIndentation>();
    for(unsigned i=0;i<3;i++){
        if(p.proprioception.T_T_EE(3,i)<T_container(3,i)+skill_params->ROI_x(i*2) || p.proprioception.T_T_EE(3,i)>T_container(3,i)+skill_params->ROI_x(i*2+1)){
            return false;
        }
    }
    return true;
}

bool TaxIndentation::check_local_suc_conditions(const Percept &p){
    std::shared_ptr<SkillParametersTaxIndentation> skill_params = get_parameters<SkillParametersTaxIndentation>();
    return p.proprioception.T_T_EE(2,3)-m_T_T_EE_contact(2,3)>skill_params->p2.distance;
}

bool TaxIndentation::check_local_err_conditions(const Percept &p){
    const Eigen::Matrix<double,6,1>& ROI_x=get_parameters<SkillParametersTaxIndentation>()->ROI_x;
    [[maybe_unused]] const Eigen::Matrix<double,6,1>& ROI_phi=get_parameters<SkillParametersTaxIndentation>()->ROI_phi;
    [[maybe_unused]] double error_angle=acos(p.proprioception.T_T_EE.block<3,1>(0,2).dot(get_object_pose_T("Surface").block<3,1>(0,2)));
    Eigen::Matrix<double,3,1> dist = p.proprioception.T_T_EE.block<3,1>(0,3)-get_object_pose_T("Surface").block<3,1>(0,3);
    if(dist(0) < ROI_x(0) || dist(0) > ROI_x(1) || dist(1) < ROI_x(2) || dist(1) > ROI_x(3) || dist(2) < ROI_x(4) || dist(2) > ROI_x(5)){
        return true;
    }
    return false;
}

}
