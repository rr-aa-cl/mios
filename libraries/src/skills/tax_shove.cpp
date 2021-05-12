#include "skills/tax_shove.hpp"
#include "strategies/move_to_pose.hpp"
#include "strategies/cart_compliance_strategy.hpp"


namespace mios{
bool SkillParametersTaxShove::from_json(const nlohmann::json& parameters){
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
    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersTaxShove::get_parameter_list(){
    return {{"p0",{"K_x","dX_d","ddX_d"}},{"p1",{"K_x","dX_d","ddX_d"}}};
}

TaxShove::TaxShove(const std::string& name, Memory* memory, Portal* portal):Skill("TaxShove",{"Shovable","Approach","Location"},name,memory,portal,{ControlMode::mCartTorque,ControlMode::mCartVelocity}){
    m_has_contact=false;
}

std::shared_ptr<ManipulationPrimitive> TaxShove::get_initial_mp(const Percept& p){
    return create_approach_mp(p);
}

std::optional<std::shared_ptr<ManipulationPrimitive> > TaxShove::graph_transition(const Percept &p){
    if(get_active_mp()->get_name()=="approach"){
        if(get_active_mp()->get_strategy_interface("move")->finished()){
            return create_shove_mp(p);
        }else{
            return {};
        }
    }
    return {};
}

std::shared_ptr<ManipulationPrimitive> TaxShove::create_approach_mp(const Percept &p){
    spdlog::trace("TaxShove::create_approach_mp");
    std::shared_ptr<SkillParametersTaxShove> skill_params = get_parameters<SkillParametersTaxShove>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("approach",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    Eigen::Matrix<double,4,4> T_a = get_object_pose_T("Approach");
    move->set_goal(T_a,skill_params->p0.dX_d,skill_params->p0.ddX_d);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p0.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxShove::create_shove_mp(const Percept &p){
    spdlog::trace("TaxShove::create_shove_mp");
    std::shared_ptr<SkillParametersTaxShove> skill_params = get_parameters<SkillParametersTaxShove>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("shove",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("Location"),skill_params->p1.dX_d,skill_params->p1.ddX_d);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p1.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

void TaxShove::update_internal_models(const Percept &p){
    update_object("Shovable")->O_T_OB=p.proprioception.O_T_EE;
    double f_contact = p.proprioception.TF_F_ext_K.block<3,1>(0,0).norm();
    if(f_contact>m_memory->read_parameters()->user.F_ext_contact(0)){
        m_has_contact=true;
    }
}

bool TaxShove::check_local_pre_conditions(const Percept &p){
    Eigen::Matrix<double,4,4> T_shovable = get_object_pose_T("Shovable");
    std::shared_ptr<SkillParametersTaxShove> skill_params = get_parameters<SkillParametersTaxShove>();
    for(unsigned i=0;i<3;i++){
        if(p.proprioception.T_T_EE(3,i)<T_shovable(3,i)+skill_params->ROI_x(i*2) || p.proprioception.T_T_EE(3,i)>T_shovable(3,i)+skill_params->ROI_x(i*2+1)){
            return false;
        }
    }
    return true;
}

bool TaxShove::check_local_err_conditions(const Percept &p){
    std::shared_ptr<SkillParametersTaxShove> skill_params = get_parameters<SkillParametersTaxShove>();
    if(get_active_mp()->get_name()=="shove" && get_active_mp()->get_strategy_interface("move")->finished()){
        if(!m_has_contact){
            return true;
        }
    }
    return false;
}

bool TaxShove::check_local_suc_conditions(const Percept &p){
    if(get_active_mp()->get_name()=="shove" && get_active_mp()->get_strategy_interface("move")->finished()){
        return true;
    }
    return false;
}

}
