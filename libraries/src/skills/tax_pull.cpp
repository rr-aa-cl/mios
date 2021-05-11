#include "skills/tax_pull.hpp"
#include "strategies/cart_compliance_strategy.hpp"
#include "strategies/ff_strategy.hpp"
#include <msrm_utils/math.hpp>

namespace mios{

bool SkillParametersTaxPull::from_json(const nlohmann::json& parameters){
    if(parameters.find("p0")==parameters.end()){
        spdlog::error("Parameters for primitive 0 are missing.");
        return false;
    }else if(parameters.find("p0")!=parameters.end()){
        if(!msrm_utils::read_json_param<double,6,1>(parameters["p0"],"K_x",p0.K_x)){
            spdlog::error("Missing parameter: p0.K_x");
            return false;
        }
        if(!msrm_utils::read_json_param(parameters["p0"],"f_pull",p0.f_pull)){
            spdlog::error("Missing parameter: p0.f_pull");
            return false;
        }
        if(!msrm_utils::read_json_param(parameters["p0"],"duration",p0.duration)){
            spdlog::error("Missing parameter: p0.duration");
            return false;
        }
    }
    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersTaxPull::get_parameter_list(){
    return {{"p0",{"K_x","f_pull","duration"}}};
}

TaxPull::TaxPull(const std::string& name, Memory* memory, Portal *portal):Skill("TaxPull",{"Pullable"},name,memory,portal,{ControlMode::mCartTorque}){

}

Eigen::Matrix<double,3,3> TaxPull::get_O_R_T_0(const Percept &p) const{
    if(get_object("Pullable")->name!="NullObject"){
        return get_object("Pullable")->O_T_OB.block<3,3>(0,0);
    }else{
        throw SkillException("No valid object has been grounded.");
    }
}

std::shared_ptr<ManipulationPrimitive> TaxPull::get_initial_mp(const Percept& p){
    return create_pull_mp(p);
}

std::shared_ptr<ManipulationPrimitive> TaxPull::create_pull_mp(const Percept &p){
    spdlog::trace("TaxPull::create_pull_mp");
    std::shared_ptr<SkillParametersTaxPull> skill_params = get_parameters<SkillParametersTaxPull>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("pull",p);
    mp->create_strategy<FFStrategy>("wrench",1);
    Eigen::Matrix<double,6,1> TF_F_d;
    TF_F_d<<0,0,-skill_params->p0.f_pull,0,0,0;
    mp->get_strategy<FFStrategy>("wrench")->set_TF_F_ff(TF_F_d,m_memory->read_parameters()->limits.cartesian_space.dF_J_max);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p0.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

bool TaxPull::check_local_pre_conditions(const Percept &p){
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Pullable")->name){
        return false;
    }
    return true;
}

bool TaxPull::check_local_suc_conditions(const Percept &p){
    std::shared_ptr<SkillParametersTaxPull> skill_params = get_parameters<SkillParametersTaxPull>();
    if(std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::high_resolution_clock::now()-m_memory->get_live_context()->t_mp).count()>=skill_params->p0.duration*1000){
        return true;
    }
    return false;
}

bool TaxPull::check_local_err_conditions(const Percept &p){
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Pullable")->name){
        return true;
    }
    return false;
}

}
