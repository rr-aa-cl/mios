#include "skills/tax_extraction.hpp"
#include "strategies/move_to_pose.hpp"
#include "strategies/ff_wiggle_strategy.hpp"
#include "strategies/ff_strategy.hpp"
#include "strategies/cart_compliance_strategy.hpp"

namespace mios {

bool SkillParametersTaxExtraction::from_json(const nlohmann::json &parameters){
    if(parameters.find("p0")==parameters.end()){
        spdlog::error("Parameters for primitive 0 are missing.");
        return false;
    }else if(parameters.find("p0")!=parameters.end()){
        if(!msrm_utils::read_json_param<double,6,1>(parameters["p0"],"K_x",p0.K_x)){
            spdlog::error("Missing parameter: p0.K_x");
            return false;
        }
        if(!msrm_utils::read_json_param<double,6,1>(parameters["p0"],"search_a",p0.search_a)){
            spdlog::error("Missing parameter: p0.search_a");
            return false;
        }
        if(!msrm_utils::read_json_param<double,6,1>(parameters["p0"],"search_f",p0.search_f)){
            spdlog::error("Missing parameter: p0.search_f");
            return false;
        }
        if(!msrm_utils::read_json_param(parameters["p0"],"f_pull",p0.f_pull)){
            spdlog::error("Missing parameter: p0.f_pull");
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
        if(!msrm_utils::read_json_param(parameters["p1"],"f_pull",p1.f_pull)){
            spdlog::error("Missing parameter: p1.f_pull");
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

std::map<std::string, std::set<std::string> > SkillParametersTaxExtraction::get_parameter_list(){
    return {{"p0",{"K_x","search_a","search_f","f_pull"}},{"p1",{"K_x","f_pull","dX_d","ddX_d"}}};
}

TaxExtraction::TaxExtraction(const std::string &name, Memory *memory, Portal* portal):Skill("TaxExtraction",{"Extractable","Container","ExtractTo"},name,memory,portal,
{ControlMode::mCartTorque}),m_is_stuck(false),m_dx_avg_last(0){
    m_dx_avg_mem.assign(100,0);
}


Eigen::Matrix<double, 3, 3> TaxExtraction::get_O_R_T_0(const Percept &p) const{
    return get_object("Container")->O_T_OB.block<3,3>(0,0);
}

std::shared_ptr<ManipulationPrimitive> TaxExtraction::get_initial_mp(const Percept &p_0){
    return create_move_mp(p_0);
}

std::optional<std::shared_ptr<ManipulationPrimitive> > TaxExtraction::graph_transition(const Percept &p){
    if(get_active_mp()->get_name()=="move"){
        if(!is_stuck(p)){
            return {};
        }else{
            return create_wiggle_mp(p);
        }
    }
    if(get_active_mp()->get_name()=="wiggle"){
        if(!is_stuck(p)){
            return create_move_mp(p);
        }else{
            return {};
        }
    }
    return {};
}

std::shared_ptr<ManipulationPrimitive> TaxExtraction::create_move_mp(const Percept &p){
    spdlog::debug("TaxExtraction::create_move_mp");

    std::shared_ptr<SkillParametersTaxExtraction> skill_params = get_parameters<SkillParametersTaxExtraction>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("extract",p);
    mp->create_strategy<MoveToPoseStrategy>("orientation",1);
    std::shared_ptr<MoveToPoseStrategy> orientation = mp->get_strategy<MoveToPoseStrategy>("orientation");
    Eigen::Matrix<double,4,4> T_g=get_object_pose_T("ExtractTo");
    T_g.block<3,1>(0,3)=p.proprioception.T_T_EE.block<3,1>(0,3);
    orientation->set_goal(T_g,skill_params->p1.dX_d,skill_params->p1.ddX_d);

    mp->create_strategy<FFStrategy>("pull",1);
    Eigen::Matrix<double,6,1> f_pull;
    f_pull<<0,0,skill_params->p1.f_pull,0,0,0;
    mp->get_strategy<FFStrategy>("pull")->set_TF_F_ff(f_pull,m_memory->read_parameters()->limits.cartesian_space.dF_J_max);

    Eigen::Matrix<double,6,1> K_x=skill_params->p1.K_x;
    K_x(2)=0;
    Eigen::Matrix<double,6,1> xi_x=m_memory->read_parameters()->control.cart_imp.xi_x;
    xi_x(2)=0;
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(K_x,xi_x);

    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxExtraction::create_wiggle_mp(const Percept &p){
    spdlog::debug("TaxExtraction::create_wiggle_mp");
    std::shared_ptr<SkillParametersTaxExtraction> skill_params = get_parameters<SkillParametersTaxExtraction>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("wiggle",p);
    mp->create_strategy<FFWiggleStrategy>("wiggle_x",1);
    mp->get_strategy<FFWiggleStrategy>("wiggle_x")->set_coefficients(Eigen::Matrix<double,6,1>::Zero(),skill_params->p0.search_a,
                                                                   Eigen::Matrix<double,6,1>::Zero(),skill_params->p0.search_f,
                                                                   Eigen::Matrix<double,6,1>::Zero(),Eigen::Matrix<double,6,1>::Zero());

    mp->create_strategy<FFStrategy>("pull",1);
    Eigen::Matrix<double,6,1> f_pull;
    f_pull<<0,0,skill_params->p0.f_pull,0,0,0;
    mp->get_strategy<FFStrategy>("pull")->set_TF_F_ff(f_pull,m_memory->read_parameters()->limits.cartesian_space.dF_J_max);
    Eigen::Matrix<double,6,1> K_x=skill_params->p0.K_x;
    K_x(2)=0;
    Eigen::Matrix<double,6,1> xi_x=m_memory->read_parameters()->control.cart_imp.xi_x;
    xi_x(2)=0;
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(K_x,xi_x);
    return mp;
}

bool TaxExtraction::check_local_pre_conditions(const Percept &p){
    return m_memory->get_live_context()->grasped_object->name==get_object("Extractable")->name;
}

bool TaxExtraction::check_local_suc_conditions(const Percept &p){
    return p.proprioception.T_T_EE(2,3)>get_object_pose_T("ExtractTo")(2,3)-m_memory->read_parameters()->user.env_X(0);
}

bool TaxExtraction::check_local_ex_conditions(const Percept &p){
    return true;
}

bool TaxExtraction::check_local_err_conditions(const Percept &p){
    return false;
}

double TaxExtraction::get_goal_heuristic(const Percept &p){
    return (get_result().p_1.proprioception.T_T_EE.block<3,1>(0,3)-get_object_pose_T("ExtractTo").block<3,1>(0,3)).norm();
}

bool TaxExtraction::is_stuck(const Percept &p){
    m_dx_avg_mem[m_dx_avg_last++]=p.proprioception.TF_dX_EE.block<3,1>(0,0).norm();
    if(m_dx_avg_last==m_dx_avg_mem.size()){
        m_dx_avg_last=0;
    }
    m_dx_avg=0;
    for(unsigned i=0;i<m_dx_avg_mem.size();i++){
        m_dx_avg+=m_dx_avg_mem[i];
    }
    m_dx_avg/=m_dx_avg_mem.size();
//    m_dx_avg=std::accumulate(m_dx_avg_mem.begin(),m_dx_avg_mem.end(),0)/(double)m_dx_avg_mem.size();
    if(!m_is_stuck && m_dx_avg<m_memory->read_parameters()->user.env_dX(0)-m_memory->read_parameters()->user.env_dX(0)*0.1){
        m_is_stuck=true;
        return true;
    }else if(m_is_stuck && m_dx_avg>m_memory->read_parameters()->user.env_dX(0)+m_memory->read_parameters()->user.env_dX(0)*0.1){
        m_is_stuck=false;
        return false;
    }
    return m_is_stuck;
}

}
