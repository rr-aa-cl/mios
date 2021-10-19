#include "mios/strategies/cart_compliance_strategy.hpp"
#include "mios/skills/tax_press_button.hpp"
#include "mios/strategies/desired_wrench_strategy.hpp"
#include "mios/strategies/ff_strategy.hpp"
#include "mios/strategies/move_to_pose.hpp"
#include "mios/strategies/twist_strategy.hpp"
#include "mios/strategies/null_strategy.hpp"
#include "msrm_cpp_utils/math/math.hpp"

namespace mios{

bool SkillParametersTaxPressButton::from_json(const nlohmann::json& parameters){

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
    }

    if(parameters.find("p3")==parameters.end()){
        spdlog::error("Parameters for primitive 3 are missing.");
        return false;
    }else if(parameters.find("p3")!=parameters.end()){
        if(!msrm_utils::read_json_param<double,6,1>(parameters["p3"],"K_x",p3.K_x)){
            spdlog::error("Missing parameter: p3.K_x");
            return false;
        }
        if(!msrm_utils::read_json_param(parameters["p3"],"f_push",p3.f_push)){
            spdlog::error("Missing parameter: p3.f_push");
            return false;
        }
        if(!msrm_utils::read_json_param(parameters["p3"],"duration",p3.duration)){
            spdlog::error("Missing parameter: p3.duration");
            return false;
        }
    }

    if(parameters.find("p4")==parameters.end()){
        spdlog::error("Parameters for primitive 4 are missing.");
        return false;
    }else if(parameters.find("p4")!=parameters.end()){
        if(!msrm_utils::read_json_param<double,6,1>(parameters["p4"],"K_x",p4.K_x)){
            spdlog::error("Missing parameter: p4.K_x");
            return false;
        }
        if(!msrm_utils::read_json_param<double,2,1>(parameters["p4"],"dX_d",p4.dX_d)){
            spdlog::error("Missing parameter: p4.dX_d");
            return false;
        }
        if(!msrm_utils::read_json_param<double,2,1>(parameters["p4"],"ddX_d",p4.ddX_d)){
            spdlog::error("Missing parameter: p4.ddX_d");
            return false;
        }
    }
    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersTaxPressButton::get_parameter_list(){
    return {{"p0",{"K_x","dX_d","ddX_d"}},{"p1",{"K_x","dX_d","ddX_d"}},{"p2",{"K_x","f_push"}},{"p3",{"K_x","f_push","duration"}},{"p4",{"K_x","dX_d","ddX_d"}}};
}

TaxPressButton::TaxPressButton(const std::string& name, Memory* memory, Portal *portal):Skill("TaxPressButton",{"Button","Approach"},name,memory,portal,{ControlMode::mCartTorque}),
    m_press_started(false){
    m_memory->remove_event("button_press");
}

Eigen::Matrix<double,3,3> TaxPressButton::get_O_R_T_0([[maybe_unused]] const Percept &p) const{
    return get_object("Button")->O_T_OB.block<3,3>(0,0);
}

double TaxPressButton::get_goal_heuristic([[maybe_unused]] const Percept &p){
    bool h = !get_result().success;
    return (get_result().p_1.proprioception.T_T_EE.block<3,1>(0,3)-get_object_pose_T("Approach").block<3,1>(0,3)).norm() +
            h * (get_object_pose_T("Button").block<3,1>(0,3)-get_object_pose_T("Approach").block<3,1>(0,3)).norm();
}

std::shared_ptr<ManipulationPrimitive> TaxPressButton::get_initial_mp(const Percept& p){
    return create_approach_mp(p);
}

std::optional<std::shared_ptr<ManipulationPrimitive> > TaxPressButton::graph_transition(const Percept &p){
    if(get_active_mp()->get_name()=="approach"){
        if(get_active_mp()->get_strategy_interface("move")->finished()){
            return create_contact_mp(p);
        }else{
            return {};
        }
    }
    if(get_active_mp()->get_name()=="contact"){
        if(p.proprioception.TF_F_ext_K(2)>m_memory->read_parameters()->user.F_ext_contact(0)){
            return create_push_down_mp(p);
        }else{
            return {};
        }
    }
    if(get_active_mp()->get_name()=="push_down"){
        if(m_press_started){
            return create_push_mp(p);
        }else{
            return {};
        }
    }
    if(get_active_mp()->get_name()=="push"){
        if(get_result().success){
            return create_retract_mp(p);
        }else{
            return {};
        }
    }
    return {};
}

std::shared_ptr<ManipulationPrimitive> TaxPressButton::create_approach_mp(const Percept &p){
    spdlog::trace("TaxPressButton::create_approach_mp()");
    std::shared_ptr<SkillParametersTaxPressButton> skill_params = get_parameters<SkillParametersTaxPressButton>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("approach",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("Approach"),skill_params->p0.dX_d,skill_params->p0.ddX_d);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p0.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxPressButton::create_contact_mp(const Percept &p){
    spdlog::trace("TaxPressButton::create_contact_mp()");
    std::shared_ptr<SkillParametersTaxPressButton> skill_params = get_parameters<SkillParametersTaxPressButton>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("contact",p);
    mp->create_strategy<TwistStrategy>("move",1);
    std::shared_ptr<TwistStrategy> move = mp->get_strategy<TwistStrategy>("move");
    Eigen::Matrix<double,6,1> dX_d;
    Eigen::Matrix<double,3,1> dir=get_object_pose_T("Button").block<3,1>(0,3)-p.proprioception.T_T_EE.block<3,1>(0,3);
    dir/=dir.norm();
    dX_d<<0,0,skill_params->p1.dX_d(0),0,0,0;
    move->set_TF_dX_d(dX_d,skill_params->p1.ddX_d);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p1.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxPressButton::create_push_down_mp(const Percept &p){
    spdlog::trace("TaxPressButton::create_push_mp()");
    std::shared_ptr<SkillParametersTaxPressButton> skill_params = get_parameters<SkillParametersTaxPressButton>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("push_down",p);
    mp->create_strategy<FFStrategy>("push_down",1);
    std::shared_ptr<FFStrategy> move = mp->get_strategy<FFStrategy>("push_down");
    Eigen::Matrix<double,6,1> F_d;
    F_d<<0,0,skill_params->p2.f_push,0,0,0;
    move->set_TF_F_ff(F_d,m_memory->read_parameters()->limits.cartesian_space.dF_J_max);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p2.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxPressButton::create_push_mp(const Percept &p){
    spdlog::trace("TaxPressButton::create_push_mp()");
    std::shared_ptr<SkillParametersTaxPressButton> skill_params = get_parameters<SkillParametersTaxPressButton>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("push",p);
    mp->create_strategy<FFStrategy>("push",1);
    std::shared_ptr<FFStrategy> move = mp->get_strategy<FFStrategy>("push");
    Eigen::Matrix<double,6,1> F_d;
    F_d<<0,0,skill_params->p3.f_push,0,0,0;
    move->set_TF_F_ff(F_d,m_memory->read_parameters()->limits.cartesian_space.dF_J_max);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p3.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxPressButton::create_retract_mp(const Percept &p){
    spdlog::trace("TaxPressButton::create_retract_mp()");
    std::shared_ptr<SkillParametersTaxPressButton> skill_params = get_parameters<SkillParametersTaxPressButton>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("retract",p);
    mp->create_strategy<TwistStrategy>("move",1);
    std::shared_ptr<TwistStrategy> move = mp->get_strategy<TwistStrategy>("move");
    Eigen::Matrix<double,6,1> dX_d;
    dX_d<<0,0,-skill_params->p4.dX_d(0),0,0,0;
    move->set_TF_dX_d(dX_d,skill_params->p4.ddX_d);
    mp->create_strategy<CartComplianceStrategy>("compliance",1);
    mp->get_strategy<CartComplianceStrategy>("compliance")->set_complicance(skill_params->p4.K_x,m_memory->read_parameters()->control.cart_imp.xi_x);
    return mp;
}

bool TaxPressButton::check_local_pre_conditions(const Percept &p){
    return true;
}

bool TaxPressButton::check_local_suc_conditions(const Percept &p){
    if(get_parameters<SkillParametersTaxPressButton>()->condition_level_success==SkillConditionLevel::sclModel){
        if(fabs(p.proprioception.TF_dX_EE(2))<0.1 && p.proprioception.TF_F_ext_K(2)>m_memory->read_parameters()->user.F_ext_contact(0)){
            if(!m_press_started  && !get_result().success){
                m_press_t_0=std::chrono::high_resolution_clock::now();
                m_press_started=true;
            }else if(std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::high_resolution_clock::now()-m_press_t_0).count()>get_parameters<SkillParametersTaxPressButton>()->p3.duration*1000){
                m_press_started=false;
                return true;
            }
        }
    }
    if(get_parameters<SkillParametersTaxPressButton>()->condition_level_success==SkillConditionLevel::sclSpecification){
        if(fabs((p.proprioception.T_T_EE(2,3)-get_object_pose_T("Button")(2,3)))<m_memory->read_parameters()->user.env_X(0)){
            if(!m_press_started && !get_result().success){
                m_press_t_0=std::chrono::high_resolution_clock::now();
                m_press_started=true;
            }else if(std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::high_resolution_clock::now()-m_press_t_0).count()>get_parameters<SkillParametersTaxPressButton>()->p3.duration*1000){
                m_press_started=false;
                return true;
            }
        }
    }
    if(get_parameters<SkillParametersTaxPressButton>()->condition_level_success==SkillConditionLevel::sclExternal){
        const Event* e = m_memory->get_event("button_press");
        if(e!=nullptr){
            bool button_state;
            nlohmann::json content=e->get_content();
            if(content.find("button_state")==content.end()){
                spdlog::error("TaxButtonPress: The event button_press has invalid content. Must be of the form {\"button_state\": <bool>}");
                return false;
            }
            content["button_state"].get_to(button_state);
            if(button_state){
                if(!m_press_started && !get_result().success){
                    m_press_t_0=std::chrono::high_resolution_clock::now();
                    m_press_started=true;
                }else if(std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::high_resolution_clock::now()-m_press_t_0).count()>get_parameters<SkillParametersTaxPressButton>()->p3.duration*1000){
                    m_press_started=false;
                    return true;
                }
            }
        }
    }
    return false;
}

bool TaxPressButton::check_local_err_conditions(const Percept &p){
    if(get_parameters<SkillParametersTaxPressButton>()->condition_level_error==SkillConditionLevel::sclModel){
        if(m_press_started && !get_result().success){
            if(!(fabs(p.proprioception.TF_dX_EE(2))<0.1 && p.proprioception.TF_F_ext_K(2)>m_memory->read_parameters()->user.F_ext_contact(0))){
                return true;
            }
        }
    }
    if(get_parameters<SkillParametersTaxPressButton>()->condition_level_error==SkillConditionLevel::sclSpecification){
        if(m_press_started && !get_result().success){
            if(!(fabs(p.proprioception.TF_dX_EE(2))<0.1 && fabs(p.proprioception.TF_F_ext_K(2))>m_memory->read_parameters()->user.F_ext_contact(0))){
                return true;
            }
        }
    }
    if(get_parameters<SkillParametersTaxPressButton>()->condition_level_error==SkillConditionLevel::sclExternal){
        const Event* e = m_memory->get_event("button_press");
        if(m_press_started && !get_result().success){
            if(e!=nullptr){
                bool button_state;
                nlohmann::json content=e->get_content();
                if(content.find("button_state")==content.end()){
                    spdlog::error("TaxButtonPress: The event button_press has invalid content. Must be of the form {\"button_state\": <bool>}");
                    return false;
                }
                content["button_state"].get_to(button_state);
                if(!button_state){
                    return true;
                }

            }
        }
    }
    return false;
}

bool TaxPressButton::check_local_ex_conditions(const Percept &p){
    if(get_result().success){
        if((p.proprioception.T_T_EE(2,3)<get_object_pose_T("Approach")(2,3))){
            return true;
        }else{
            return false;
        }
    }
    return false;
}

}
