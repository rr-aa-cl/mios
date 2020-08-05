#include "skills/wipe.hpp"
#include "strategies/twist_strategy.hpp"
#include "strategies/ff_strategy.hpp"
#include "strategies/move_to_pose.hpp"

#include "msrm_utils/math.hpp"

namespace mios{

bool SkillParametersWipe::from_json(const nlohmann::json& parameters){
    if(!msrm_utils::read_json_param(parameters,"f_contact",f_contact)){
        spdlog::error("Parameter f_contact could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"speed",speed)){
        spdlog::error("Parameter speed could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"wipe_distance",wipe_distance)){
        spdlog::error("Parameter wipe_distance could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"t_contactless",t_contactless)){
        spdlog::error("Parameter t_contactless could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"wipe_dir",wipe_dir)){
        spdlog::error("Parameter wipe_dir could not be loaded but is mandatory.");
        return false;
    }
    if(wipe_dir.norm()!=1){
        spdlog::error("wipe_dir must be a unit vector.");
        return false;
    }
    return true;
}

Wipe::Wipe(const std::string& name, Memory* memory, Portal* portal, const Percept& p):Skill("Wipe",{"wipeable"},name,memory,portal,p,{ControlMode::mCartTorque}){

}

Eigen::Matrix<double,3,3> Wipe::get_O_R_T_0(const Percept &p) const{
    if(get_object("wipeable")->name!="NullObject"){
        return get_object("wipeable")->O_T_OB.block<3,3>(0,0);
    }else{
        throw SkillException("No valid object has been grounded.");
    }
}

std::shared_ptr<ManipulationPrimitive> Wipe::get_initial_mp(const Percept& p){


    std::shared_ptr<SkillParametersWipe> skill_params = get_parameters<SkillParametersWipe>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("approach",p);
    mp->create_strategy<MoveToPoseStrategy>("approach",1);

    Eigen::Matrix<double,4,4> T_g;
    if(this->get_object("wipeable")->name!="NullObject"){
        T_g=get_object_pose_T("wipeable");
        T_g(2,3)-=0.03;
    }else{
        throw SkillException("No valid object has been grounded.");
    }
    Eigen::Matrix<double,2,1> speed;
    Eigen::Matrix<double,2,1> acc;
    speed<<skill_params->speed,m_memory->read_parameters()->user.dX_default(1);
    mp->get_strategy<MoveToPoseStrategy>("approach")->set_goal(T_g,speed,m_memory->read_parameters()->user.ddX_default);
    Eigen::Matrix<double,2,1> t_scale;
    t_scale<<1,1;
    mp->get_strategy<MoveToPoseStrategy>("approach")->set_scale(t_scale);
    return mp;
}

std::optional<std::shared_ptr<ManipulationPrimitive> > Wipe::graph_transition(const Percept &p){
    if(get_active_mp()->get_name()=="approach"){
        if(get_active_mp()->get_strategy_interface("approach")->finished()){
            m_TF_T_EE_retract = p.proprioception.T_T_EE;
            std::shared_ptr<SkillParametersWipe> skill_params = get_parameters<SkillParametersWipe>();
            std::shared_ptr<ManipulationPrimitive> mp = create_mp("contact",p);
            mp->create_strategy<TwistStrategy>("twist",1);
            Eigen::Matrix<double,6,1> TF_dX_d;
            TF_dX_d<<0,0,skill_params->speed,0,0,0;
            Eigen::Matrix<double,2,1> ddX_max;
            ddX_max<<m_memory->read_parameters()->user.ddX_default;
            mp->get_strategy<TwistStrategy>("twist")->set_TF_dX_d(TF_dX_d,ddX_max);
            return mp;
        }
    }
    if(get_active_mp()->get_name()=="contact"){
        std::shared_ptr<SkillParametersWipe> skill_params = get_parameters<SkillParametersWipe>();
        if(p.proprioception.TF_F_ext_K(2)>skill_params->f_contact){
            m_TF_T_EE_contact = p.proprioception.T_T_EE;
            std::shared_ptr<ManipulationPrimitive> mp = create_mp("wipe",p);
            mp->create_strategy<TwistStrategy>("twist",1);
            Eigen::Matrix<double,6,1> TF_dX_d;
            TF_dX_d<<skill_params->speed*skill_params->wipe_dir(0),skill_params->speed*skill_params->wipe_dir(1),0,0,0,0;
            mp->get_strategy<TwistStrategy>("twist")->set_TF_dX_d(TF_dX_d,m_memory->read_parameters()->user.ddX_default);
            mp->create_strategy<FFStrategy>("press",1);
            Eigen::Matrix<double,6,1> TF_F_ff;
            TF_F_ff<<0,0,skill_params->f_contact,0,0,0;
            mp->get_strategy<FFStrategy>("press")->set_TF_F_ff(TF_F_ff,m_memory->read_parameters()->limits.cartesian_space.dF_J_max);
            return mp;
        }
    }
    if(get_active_mp()->get_name()=="wipe"){
        std::shared_ptr<SkillParametersWipe> skill_params = get_parameters<SkillParametersWipe>();
        if(fabs((p.proprioception.T_T_EE.block<2,1>(0,3)-m_TF_T_EE_contact.block<2,1>(0,3)).norm())>skill_params->wipe_distance){
            std::shared_ptr<ManipulationPrimitive> mp = create_mp("retract",p);
            mp->create_strategy<MoveToPoseStrategy>("move",1);
            Eigen::Matrix<double,2,1> dX_d,ddX_d,t_scale;
            t_scale<<1,1;
            dX_d<<skill_params->speed,m_memory->read_parameters()->user.dX_default(1);
            Eigen::Matrix<double,4,4> T_T_EE_retract=p.proprioception.T_T_EE;
            T_T_EE_retract(2,3)=m_TF_T_EE_retract(2,3);
            mp->get_strategy<MoveToPoseStrategy>("move")->set_goal(T_T_EE_retract,dX_d,m_memory->read_parameters()->user.ddX_default);
            mp->get_strategy<MoveToPoseStrategy>("move")->set_scale(t_scale);
            return mp;
        }
    }
    return {};
}

bool Wipe::check_local_err_conditions(const Percept &p){
    if(get_active_mp()->get_name()=="wipe"){
        std::shared_ptr<SkillParametersWipe> skill_params = get_parameters<SkillParametersWipe>();
        double f_contact = p.proprioception.TF_F_ext_K.block<3,1>(0,0).norm();
        if(f_contact>m_memory->read_parameters()->user.F_ext_contact(0)){
            m_in_contact=true;
        }else{
            m_in_contact=false;
            m_t_contact_loss=p.time;
        }

        if(!m_in_contact && std::chrono::duration_cast<std::chrono::milliseconds>(p.time-m_t_contact_loss).count()>skill_params->t_contactless){
            return true;
        }
        return false;
    }
    return false;
}

bool Wipe::check_local_suc_conditions(const Percept &p){
    return get_active_mp()->get_name()=="retract";
}

bool Wipe::check_local_ex_conditions(const Percept &p){
    if(get_active_mp()->get_name()=="retract"){
        return get_active_mp()->get_strategy_interface("move")->finished();
    }
    return false;
}

void Wipe::evaluate(){}
}
