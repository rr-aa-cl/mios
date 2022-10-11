#include "mios/strategies/ff_strategy.hpp"
#include "mios/strategies/cart_compliance_strategy.hpp"
#include "mios/skills/tax_insertion.hpp"
#include "mios/strategies/move_to_pose.hpp"
#include "mios/strategies/ff_wiggle_strategy.hpp"
#include "mios/strategies/ff_wrench_lissajous_strategy.hpp"
#include "mios/strategies/twist_strategy.hpp"
#include "mirmi_cpp_utils/math/math.hpp"

namespace mios {

bool SkillParametersTaxInsertion::from_json(const nlohmann::json &parameters){

    if(parameters.find("p0")==parameters.end()){
        spdlog::error("Parameters for primitive 0 are missing.");
        return false;
    }else if(parameters.find("p0")!=parameters.end()){
        if(!mirmi_utils::read_json_param<double,6,1>(parameters["p0"],"K_x",p0.K_x)){
            spdlog::error("Missing parameter: p0.K_x");
            return false;
        }
        if(!mirmi_utils::read_json_param<double,6,1>(parameters["p0"],"DeltaX",p0.DeltaX)){
            spdlog::error("Missing parameter: p0.DeltaX");
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

    if(parameters.find("p1")==parameters.end()){
        spdlog::error("Parameters for primitive 1 are missing.");
        return false;
    }else if(parameters.find("p1")!=parameters.end()){
        if(!mirmi_utils::read_json_param<double,6,1>(parameters["p1"],"K_x",p1.K_x)){
            spdlog::error("Missing parameter: p1.K_x");
            return false;
        }
        if(!mirmi_utils::read_json_param<double,2,1>(parameters["p1"],"dX_d",p1.dX_d)){
            spdlog::error("Missing parameter: p1.dX_d");
            return false;
        }
        if(!mirmi_utils::read_json_param<double,2,1>(parameters["p1"],"ddX_d",p1.ddX_d)){
            spdlog::error("Missing parameter: p1.ddX_d");
            return false;
        }
    }

    if(parameters.find("p2")==parameters.end()){
        spdlog::error("Parameters for primitive 2 are missing.");
        return false;
    }else if(parameters.find("p2")!=parameters.end()){
        if(!mirmi_utils::read_json_param<double,6,1>(parameters["p2"],"K_x",p2.K_x)){
            spdlog::error("Missing parameter: p2.K_x");
            return false;
        }
        if(!mirmi_utils::read_json_param<double,6,1>(parameters["p2"],"search_a",p2.search_a)){
            spdlog::error("Missing parameter: p2.search_a");
            return false;
        }
        if(!mirmi_utils::read_json_param<double,6,1>(parameters["p2"],"search_f",p2.search_f)){
            spdlog::error("Missing parameter: p2.search_f");
            return false;
        }
        if(!mirmi_utils::read_json_param<double,6,1>(parameters["p2"],"search_phi",p2.search_phi)){
            spdlog::error("Missing parameter: p2.search_phi");
            return false;
        }
        if(!mirmi_utils::read_json_param<double,6,1>(parameters["p2"],"f_push",p2.f_push)){
            spdlog::error("Missing parameter: p2.f_push");
            return false;
        }
        if(!mirmi_utils::read_json_param<double,2,1>(parameters["p2"],"dX_d",p2.dX_d)){
            spdlog::error("Missing parameter: p2.dX_d");
            return false;
        }
        if(!mirmi_utils::read_json_param<double,2,1>(parameters["p2"],"ddX_d",p2.ddX_d)){
            spdlog::error("Missing parameter: p2.ddX_d");
            return false;
        }
    }

    if(parameters.find("p3")==parameters.end()){
        spdlog::error("Parameters for primitive 3 are missing.");
        return false;
    }else if(parameters.find("p3")!=parameters.end()){
        if(!mirmi_utils::read_json_param<double,6,1>(parameters["p3"],"K_x",p3.K_x)){
            spdlog::error("Missing parameter: p3.K_x");
            return false;
        }
        if(!mirmi_utils::read_json_param(parameters["p3"],"f_push",p3.f_push)){
            spdlog::error("Missing parameter: p3.f_push");
            return false;
        }
        if(!mirmi_utils::read_json_param<double,2,1>(parameters["p3"],"dX_d",p3.dX_d)){
            spdlog::error("Missing parameter: p3.dX_d");
            return false;
        }
        if(!mirmi_utils::read_json_param<double,2,1>(parameters["p3"],"ddX_d",p3.ddX_d)){
            spdlog::error("Missing parameter: p3.ddX_d");
            return false;
        }
    }

    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersTaxInsertion::get_parameter_list(){
    return {{"p0",{"K_x","DeltaX","dX_d","ddX_d"}},{"p1",{"K_x","dX_d","ddX_d"}},{"p2",{"K_x","search_a","search_f","f_push"}},{"p3",{"K_x","f_push","dX_d","ddX_d"}}};
}

TaxInsertion::TaxInsertion(const std::string &name, Memory *memory,Portal* portal):Skill("TaxInsertion",{"Insertable","Container","Approach"},name,memory,portal,
{ControlMode::mCartTorque}),m_dx_avg_last(0),m_is_stuck(false){
    m_dx_avg_mem.assign(100,0);
    m_E_avg=0;
}


Eigen::Matrix<double, 3, 3> TaxInsertion::get_O_R_T_0([[maybe_unused]] const Percept &p) const{
    return get_object("Container")->O_T_OB.block<3,3>(0,0);
}

std::shared_ptr<ManipulationPrimitive> TaxInsertion::get_initial_mp(const Percept &p_0){
    set_ROI_center(get_object_pose_T("Container").block<3,1>(0,3));
    return create_approach_mp(p_0);
}

std::optional<std::shared_ptr<ManipulationPrimitive> > TaxInsertion::graph_transition(const Percept &p){
    if(get_active_mp()->get_name()=="approach"){
        if(get_active_mp()->get_strategy_interface("move")->finished()){
            return create_contact_mp(p);
        }
    }
    if(get_active_mp()->get_name()=="contact"){
        if(p.proprioception.TF_F_ext_K(2)>m_memory->read_parameters()->user.F_ext_contact(0)){
            return create_wiggle_mp(p);
        }
    }
//    if(get_active_mp()->get_name()=="insert"){
//        if(is_stuck(p)){
//            return create_wiggle_mp(p);
//        }
//    }
    if(get_active_mp()->get_name()=="wiggle"){
//        if(!is_stuck(p)){
//            return create_insert_mp(p);
//        }
    }
//    if(get_active_mp()->get_name()=="insert"){
//        if(!is_stuck(p)){
//            return {};
//        }else{
//            return create_wiggle_mp(p);
//        }
//    }
//    if(get_active_mp()->get_name()=="wiggle"){
//        if(!is_stuck(p)){
//            return create_insert_mp(p);
//        }else{
//            return {};
//        }
//    }
    return {};
}

std::shared_ptr<ManipulationPrimitive> TaxInsertion::create_approach_mp(const Percept &p){
    spdlog::trace("TaxInsertion::create_approach_mp()");
    std::shared_ptr<SkillParametersTaxInsertion> skill_params = get_parameters<SkillParametersTaxInsertion>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("approach",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    Eigen::Matrix<double,4,4> T_a_offset = get_object_pose_T("Approach");
    T_a_offset.block<3,3>(0,0)=mirmi_utils::eulerRPY_to_mat(skill_params->p0.DeltaX(3),skill_params->p0.DeltaX(4),skill_params->p0.DeltaX(5));
    Eigen::Matrix<double,4,4> T_a = get_object_pose_T("Approach");
    T_a.block<3,3>(0,0)=T_a_offset.block<3,3>(0,0)*T_a.block<3,3>(0,0);
    T_a.block<3,1>(0,3)+=skill_params->p0.DeltaX.block<3,1>(0,0);
    move->set_goal(T_a,skill_params->p0.dX_d,skill_params->p0.ddX_d);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p0.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxInsertion::create_contact_mp(const Percept &p){
    spdlog::trace("TaxInsertion::create_contact_mp()");
    std::shared_ptr<SkillParametersTaxInsertion> skill_params = get_parameters<SkillParametersTaxInsertion>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("contact",p);
    mp->create_strategy<TwistStrategy>("move",1);
    std::shared_ptr<TwistStrategy> move = mp->get_strategy<TwistStrategy>("move");
    Eigen::Matrix<double,6,1> dX_d;
    Eigen::Matrix<double,3,1> dir=get_object_pose_T("Container").block<3,1>(0,3)+skill_params->p0.DeltaX.block<3,1>(0,0)-p.proprioception.T_T_EE.block<3,1>(0,3);
    dir/=dir.norm();
    dX_d<<dir*skill_params->p1.dX_d(0),0,0,0;
    move->set_TF_dX_d(dX_d,skill_params->p1.ddX_d);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p1.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxInsertion::create_insert_mp(const Percept &p){
    spdlog::trace("TaxInsertion::create_insert_mp");
    std::shared_ptr<SkillParametersTaxInsertion> skill_params = get_parameters<SkillParametersTaxInsertion>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("insert",p);
    mp->create_strategy<MoveToPoseStrategy>("orientation",1);
    std::shared_ptr<MoveToPoseStrategy> orientation = mp->get_strategy<MoveToPoseStrategy>("orientation");
    Eigen::Matrix<double,4,4> T_g=get_object_pose_T("Container");
    T_g.block<3,1>(0,3)=p.proprioception.T_T_EE.block<3,1>(0,3);
    orientation->set_goal(T_g,skill_params->p3.dX_d,skill_params->p3.ddX_d);

    mp->create_strategy<FFStrategy>("push",1);
    Eigen::Matrix<double,6,1> f_push;
    f_push<<0,0,skill_params->p3.f_push,0,0,0;
    mp->get_strategy<FFStrategy>("push")->set_TF_F_ff(f_push,m_memory->read_parameters()->limits.cartesian_space.dF_J_max);

    Eigen::Matrix<double,6,1> K_x=skill_params->p3.K_x;
    K_x(2)=0;
    Eigen::Matrix<double,6,1> xi_x=m_memory->read_parameters()->control.cart_imp.xi_x;
    xi_x(2)=0;
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(K_x,xi_x);

    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxInsertion::create_wiggle_mp(const Percept &p){
    spdlog::trace("TaxInsertion::create_wiggle_mp");
    std::shared_ptr<SkillParametersTaxInsertion> skill_params = get_parameters<SkillParametersTaxInsertion>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("wiggle",p);
    mp->create_strategy<MoveToPoseStrategy>("orientation",1);
    std::shared_ptr<MoveToPoseStrategy> orientation = mp->get_strategy<MoveToPoseStrategy>("orientation");
    Eigen::Matrix<double,4,4> T_g=get_object_pose_T("Container");
//    T_g.block<3,1>(0,3)=p.proprioception.T_T_EE.block<3,1>(0,3);
    orientation->set_goal(T_g,skill_params->p2.dX_d,skill_params->p2.ddX_d);
    mp->create_strategy<FFWrenchLissajousStrategy>("wiggle_x",1);
    mp->get_strategy<FFWrenchLissajousStrategy>("wiggle_x")->set_coefficients(skill_params->p2.search_a,skill_params->p2.search_f,skill_params->p2.search_phi);

    mp->create_strategy<FFStrategy>("push",1);
//    Eigen::Matrix<double,6,1> f_push;
//    f_push<<0,0,skill_params->p2.f_push,0,0,0;
    mp->get_strategy<FFStrategy>("push")->set_TF_F_ff(skill_params->p2.f_push,m_memory->read_parameters()->limits.cartesian_space.dF_J_max);
    mp->get_strategy<FFStrategy>("push")->set_frame(true);
    Eigen::Matrix<double,6,1> K_x=skill_params->p2.K_x;
    K_x(2)=0;
    Eigen::Matrix<double,6,1> xi_x=m_memory->read_parameters()->control.cart_imp.xi_x;
    xi_x(2)=0;
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(K_x,xi_x);
    return mp;
}

void TaxInsertion::update_policies(const Percept &p){


}

bool TaxInsertion::check_local_pre_conditions(const Percept &p){
    Eigen::Matrix<double,4,4> T_container = get_object_pose_T("Container");
    std::shared_ptr<SkillParametersTaxInsertion> skill_params = get_parameters<SkillParametersTaxInsertion>();
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Insertable")->name){
        spdlog::debug("TaxInsertion::check_local_pre_conditions: Have not grasped Insertable");
        return false;
    }
    return true;
}

bool TaxInsertion::check_local_suc_conditions(const Percept &p){
    bool depth = p.proprioception.T_T_EE(2,3)>get_object_pose_T("Container")(2,3)-m_memory->read_parameters()->user.env_X(2);
    bool lateral = (p.proprioception.T_T_EE.block<2,1>(0,3)-get_object_pose_T("Container").block<2,1>(0,3)).norm()<m_memory->read_parameters()->user.env_X(1);
    return depth && lateral;
}

bool TaxInsertion::check_local_err_conditions(const Percept &p){
    return false;
}

double TaxInsertion::get_goal_heuristic([[maybe_unused]] const Percept &p){
    m_E_avg+=(p.proprioception.T_T_EE.block<3,1>(0,3)-get_object_pose_T("Container").block<3,1>(0,3)).norm()*0.001;
    if(std::chrono::duration_cast<std::chrono::milliseconds>(p.time-m_memory->get_live_context()->t_skill).count()/1000.0==0){
        return 0;
    }
    return m_E_avg/(std::chrono::duration_cast<std::chrono::milliseconds>(p.time-m_memory->get_live_context()->t_skill).count()/1000.0);
}

bool TaxInsertion::is_stuck(const Percept &p){
    m_dx_avg_mem[m_dx_avg_last++]=p.proprioception.TF_dX_EE(2);
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
