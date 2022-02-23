#include "mios/strategies/cart_compliance_strategy.hpp"
#include "mios/skills/tax_displace.hpp"
#include "mios/strategies/move_to_pose.hpp"
#include "mirmi_cpp_utils/math/math.hpp"

namespace mios{

bool SkillParametersTaxDisplace::from_json(const nlohmann::json& parameters){
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

std::map<std::string, std::set<std::string> > SkillParametersTaxDisplace::get_parameter_list(){
    return {{"p0",{"K_x","dX_d","ddX_d"}}};
}

TaxDisplace::TaxDisplace(const std::string& name, Memory* memory, Portal *portal):Skill("TaxBend",{"Displaceable", "GoalPose"},name,memory,portal,{ControlMode::mCartTorque}){

}

Eigen::Matrix<double,3,3> TaxDisplace::get_O_R_T_0(const Percept &p) const{
    return get_object("Displaceable")->O_T_OB.block<3,3>(0,0);
}

std::shared_ptr<ManipulationPrimitive> TaxDisplace::get_initial_mp(const Percept& p){
    return create_displace_mp(p);
}

std::shared_ptr<ManipulationPrimitive> TaxDisplace::create_displace_mp(const Percept &p){
    spdlog::trace("TaxBend::create_bend_mp");
    std::shared_ptr<SkillParametersTaxDisplace> skill_params = get_parameters<SkillParametersTaxDisplace>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("bend",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("GoalPose"),skill_params->p0.dX_d,skill_params->p0.ddX_d);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p0.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

bool TaxDisplace::check_local_pre_conditions(const Percept &p){
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Displaceable")->name){
        return false;
    }
    return true;
}

bool TaxDisplace::check_local_suc_conditions(const Percept &p){
    return is_in_env("GoalPose",p);
}

bool TaxDisplace::check_local_err_conditions(const Percept &p){
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Displaceable")->name){
        return true;
    }
    return false;
}

}
