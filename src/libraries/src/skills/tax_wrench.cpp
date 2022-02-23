#include "mios/strategies/cart_compliance_strategy.hpp"
#include "mios/skills/tax_wrench.hpp"
#include "mios/strategies/desired_wrench_strategy.hpp"
#include "mios/strategies/move_to_pose.hpp"
#include "mirmi_cpp_utils/math/math.hpp"

namespace mios{

bool SkillParametersTaxWrench::from_json(const nlohmann::json& parameters){
    if(parameters.find("p0")==parameters.end()){
        spdlog::error("Parameters for primitive 0 are missing.");
        return false;
    }else if(parameters.find("p0")!=parameters.end()){
        if(!mirmi_utils::read_json_param<double,6,1>(parameters["p0"],"K_x",p0.K_x)){
            spdlog::error("Missing parameter: p0.K_x");
            return false;
        }
        if(!mirmi_utils::read_json_param<double,2,1>(parameters["p0"],"dX_d",p0.dX_d)){
            spdlog::error("Missing parameter: p0.dX_d");
            return false;
        }
        if(!mirmi_utils::read_json_param<double,2,1>(parameters["p0"],"ddX_d",p0.ddX_d)){
            spdlog::error("Missing parameter: p0.ddX_d");
            return false;
        }
    }
    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersTaxWrench::get_parameter_list(){
    return {{"p0",{"K_x","dX_d","ddX_d"}}};
}

TaxWrench::TaxWrench(const std::string& name, Memory* memory, Portal *portal):Skill("TaxWrench",{"Wrench", "GoalPosition"},name,memory,portal,{ControlMode::mCartTorque}){

}

Eigen::Matrix<double,3,3> TaxWrench::get_O_R_T_0(const Percept &p) const{
    return get_object("Wrench")->O_T_OB.block<3,3>(0,0);
}

std::shared_ptr<ManipulationPrimitive> TaxWrench::get_initial_mp(const Percept& p){
    return create_turn_mp(p);
}

std::shared_ptr<ManipulationPrimitive> TaxWrench::create_turn_mp(const Percept &p){
    spdlog::trace("TaxWrench::create_turn_mp");
    std::shared_ptr<SkillParametersTaxWrench> skill_params = get_parameters<SkillParametersTaxWrench>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("turn",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("GoalPosition"),skill_params->p0.dX_d,skill_params->p0.ddX_d);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p0.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

bool TaxWrench::check_local_pre_conditions(const Percept &p){
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Lever")->name){
        return false;
    }
    return true;
}

bool TaxWrench::check_local_suc_conditions(const Percept &p){
    return is_in_env("GoalPosition",p);
}

bool TaxWrench::check_local_err_conditions(const Percept &p){
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Lever")->name){
        return true;
    }
    return false;
}

}
