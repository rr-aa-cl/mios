#include "skills/tax_press_button.hpp"
#include "strategies/desired_wrench_strategy.hpp"
#include "strategies/ff_strategy.hpp"
#include "strategies/move_to_pose.hpp"
#include "strategies/twist_strategy.hpp"
#include "strategies/null_strategy.hpp"
#include <msrm_cpp_utils/math.hpp>

namespace mios{

bool SkillParametersTaxPressButton::from_json(const nlohmann::json& parameters){
    if(!msrm_utils::read_json_param<double,6,1>(parameters,"ROI_x",ROI_x)){
        spdlog::error("Parameter ROI_x could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters,"ROI_phi",ROI_phi)){
        spdlog::error("Parameter ROI_phi could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"approach_speed",approach_speed)){
        spdlog::error("Parameter approach_speed could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"approach_acc",approach_acc)){
        spdlog::error("Parameter approach_acc could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"press_speed",press_speed)){
        spdlog::error("Parameter press_speed could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"press_acc",press_acc)){
        spdlog::error("Parameter press_acc could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"duration",duration)){
        spdlog::error("Parameter duration could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"f_push",f_push)){
        spdlog::error("Parameter f_push could not be loaded but is mandatory.");
        return false;
    }
    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersTaxPressButton::get_parameter_list(){
    return {{"duration",{}},{"f_push",{}},{"approach_speed",{}},{"approach_acc",{}},{"press_speed",{}},{"press_acc",{}},{"ROI_x",{}},{"ROI_phi",{}}};
}

TaxPressButton::TaxPressButton(const std::string& name, Memory* memory, Portal *portal):Skill("TaxPressButton",{"Button","Approach"},name,memory,portal,{ControlMode::mCartTorque}),
    m_press_started(false){
    m_memory->remove_event("button_press");
}

Eigen::Matrix<double,3,3> TaxPressButton::get_O_R_T_0(const Percept &p) const{
    if(get_object("Button")->name!="NullObject"){
        return get_object("Button")->O_T_OB.block<3,3>(0,0);
    }else{
        throw SkillException("No valid object has been grounded.");
    }
}

double TaxPressButton::get_goal_heuristic(const Percept &p){
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
    std::shared_ptr<SkillParametersTaxPressButton> skill_params = get_parameters<SkillParametersTaxPressButton>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("approach",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("Approach"),skill_params->approach_speed,skill_params->approach_acc);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxPressButton::create_contact_mp(const Percept &p){
    std::shared_ptr<SkillParametersTaxPressButton> skill_params = get_parameters<SkillParametersTaxPressButton>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("contact",p);
    mp->create_strategy<TwistStrategy>("move",1);
    std::shared_ptr<TwistStrategy> move = mp->get_strategy<TwistStrategy>("move");
    Eigen::Matrix<double,6,1> dX_d;
    Eigen::Matrix<double,3,1> dir=get_object_pose_T("Button").block<3,1>(0,3)-p.proprioception.T_T_EE.block<3,1>(0,3);
    dir/=dir.norm();
    dX_d<<0,0,skill_params->press_speed(0),0,0,0;
    std::cout<<"SPEED: "<<dX_d<<std::endl;
    move->set_TF_dX_d(dX_d,skill_params->press_acc);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxPressButton::create_push_mp(const Percept &p){
    std::shared_ptr<SkillParametersTaxPressButton> skill_params = get_parameters<SkillParametersTaxPressButton>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("push",p);
    mp->create_strategy<FFStrategy>("push",1);
    std::shared_ptr<FFStrategy> move = mp->get_strategy<FFStrategy>("push");
    Eigen::Matrix<double,6,1> F_d;
    F_d<<0,0,skill_params->f_push,0,0,0;
    move->set_TF_F_ff(F_d,m_memory->read_parameters()->limits.cartesian_space.dF_J_max);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxPressButton::create_retract_mp(const Percept &p){
    spdlog::trace("TaxPressButton::create_retract_mp()");
    std::shared_ptr<SkillParametersTaxPressButton> skill_params = get_parameters<SkillParametersTaxPressButton>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("retract",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("Approach"),skill_params->press_speed,skill_params->press_acc);
    return mp;
}

bool TaxPressButton::check_local_pre_conditions(const Percept &p){
    Eigen::Matrix<double,4,4> T_container = get_object_pose_T("Button");
    std::shared_ptr<SkillParametersTaxPressButton> skill_params = get_parameters<SkillParametersTaxPressButton>();
    for(unsigned i=0;i<3;i++){
        if(p.proprioception.T_T_EE(3,i)<T_container(3,i)+skill_params->ROI_x(i*2) || p.proprioception.T_T_EE(3,i)>T_container(3,i)+skill_params->ROI_x(i*2+1)){
            return false;
        }
    }
    return true;
}

bool TaxPressButton::check_local_suc_conditions(const Percept &p){
    if(get_parameters<SkillParametersTaxPressButton>()->condition_level_success==SkillConditionLevel::sclModel){
        if(fabs(p.proprioception.TF_dX_EE(2))<0.1 && p.proprioception.TF_F_ext_K(2)>m_memory->read_parameters()->user.F_ext_contact(0)){
            if(!m_press_started  && !get_result().success){
                m_press_t_0=std::chrono::high_resolution_clock::now();
                m_press_started=true;
            }else if(std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::high_resolution_clock::now()-m_press_t_0).count()>get_parameters<SkillParametersTaxPressButton>()->duration*1000){
                m_press_started=false;
                return true;
            }
        }
    }
    if(get_parameters<SkillParametersTaxPressButton>()->condition_level_success==SkillConditionLevel::sclSpecification){
        if((p.proprioception.T_T_EE.block<3,1>(0,3)-get_object_pose_T("Button").block<3,1>(0,3)).norm()<m_memory->read_parameters()->user.env_X(0)){
            if(!m_press_started && !get_result().success){
                m_press_t_0=std::chrono::high_resolution_clock::now();
                m_press_started=true;
            }else if(std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::high_resolution_clock::now()-m_press_t_0).count()>get_parameters<SkillParametersTaxPressButton>()->duration*1000){
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
                }else if(std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::high_resolution_clock::now()-m_press_t_0).count()>get_parameters<SkillParametersTaxPressButton>()->duration*1000){
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
            if(!(fabs(p.proprioception.TF_dX_EE(2))<0.1 && p.proprioception.TF_F_ext_K(2)>m_memory->read_parameters()->user.F_ext_contact(0))){
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

    const Eigen::Matrix<double,6,1>& ROI_x=get_parameters<SkillParametersTaxPressButton>()->ROI_x;
    const Eigen::Matrix<double,6,1>& ROI_phi=get_parameters<SkillParametersTaxPressButton>()->ROI_phi;
    double error_angle=acos(p.proprioception.T_T_EE.block<3,1>(0,2).dot(get_object_pose_T("Button").block<3,1>(0,2)));
    Eigen::Matrix<double,3,1> dist = p.proprioception.T_T_EE.block<3,1>(0,3)-get_object_pose_T("Button").block<3,1>(0,3);
    if(dist(0) < ROI_x(0) || dist(0) > ROI_x(1) || dist(1) < ROI_x(2) || dist(1) > ROI_x(3) || dist(2) < ROI_x(4) || dist(2) > ROI_x(5)){
        return true;
    }
    return false;
}

bool TaxPressButton::check_local_ex_conditions(const Percept &p){
    if(get_result().success){
        if((p.proprioception.T_T_EE.block<3,1>(0,3)-get_object_pose_T("Approach").block<3,1>(0,3)).norm()<m_memory->read_parameters()->user.env_X(0)
                && acos(((get_object_pose_T("Approach").block<3,3>(0,0).transpose()*p.proprioception.T_T_EE.block<3,3>(0,0)).trace()-1)/2) < m_memory->read_parameters()->user.env_X(1)){
            return true;
        }else{
            return false;
        }
    }
    return false;
}

}
