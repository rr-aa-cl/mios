#include "skills/tax_hammer.hpp"
#include "strategies/move_to_pose.hpp"
#include "strategies/ff_wiggle_strategy.hpp"

namespace mios {

bool SkillParametersTaxHammer::from_json(const nlohmann::json &parameters){
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"approach_speed",approach_speed)){
        spdlog::error("Parameter approach_speed could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"approach_acc",approach_acc)){
        spdlog::error("Parameter approach_acc could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"down_speed",down_speed)){
        spdlog::error("Parameter down_speed could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"down_acc",down_acc)){
        spdlog::error("Parameter down_acc could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"up_speed",up_speed)){
        spdlog::error("Parameter up_speed could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"up_acc",up_acc)){
        spdlog::error("Parameter up_acc could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"up_wrench",up_wrench)){
        spdlog::error("Parameter up_wrench could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"down_wrench",down_wrench)){
        spdlog::error("Parameter down_wrench could not be loaded but is mandatory.");
        return false;
    }

    if(!msrm_utils::read_json_param<double,6,1>(parameters,"ROI_x",ROI_x)){
        spdlog::error("Parameter ROI_x could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters,"ROI_phi",ROI_phi)){
        spdlog::error("Parameter ROI_phi could not be loaded but is mandatory.");
        return false;
    }

    if(!msrm_utils::read_json_param(parameters,"n_max",n_max)){
        spdlog::error("Parameter n_max could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"f_h",f_h)){
        spdlog::error("Parameter f_h could not be loaded but is mandatory.");
        return false;
    }

    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersTaxHammer::get_parameter_list(){
    return {{"approach_speed",{}},{"approach_acc",{}},{"down_speed",{}},{"down_acc",{}},{"up_speed",{}},{"up_acc",{}},{"down_wrench",{}},{"up_wrench",{}},{"f_h",{}},{"n_max",{}}};
}

TaxHammer::TaxHammer(const std::string &name, Memory *memory, Portal* portal):Skill("TaxHammer",{"AbovePose","GoalPose","Hammerable","Hammer","Surface"},name,memory,portal,
{ControlMode::mCartTorque}),m_n_cnt(0){

}


Eigen::Matrix<double, 3, 3> TaxHammer::get_O_R_T_0(const Percept &p) const{
    return get_object("Hammerable")->O_T_OB.block<3,3>(0,0);
}

std::shared_ptr<ManipulationPrimitive> TaxHammer::get_initial_mp(const Percept &p_0){
    return create_approach_mp(p_0);
}

std::optional<std::shared_ptr<ManipulationPrimitive> > TaxHammer::graph_transition(const Percept &p){
    std::shared_ptr<SkillParametersTaxHammer> skill_params = get_parameters<SkillParametersTaxHammer>();
    if(get_active_mp()->get_name()=="approach" || get_active_mp()->get_name()=="up"){
        if(get_active_mp()->get_strategy_interface("move")->finished()){
            return create_down_mp(p);
        }
        else{
            return {};
        }
    }
    if(get_active_mp()->get_name()=="down"){
        if(p.proprioception.TF_F_ext_K(2)>skill_params->f_h){
            m_n_cnt++;
            return create_up_mp(p);
        }else{
            return {};
        }

    }
    return {};
}

std::shared_ptr<ManipulationPrimitive> TaxHammer::create_approach_mp(const Percept &p){
    std::shared_ptr<SkillParametersTaxHammer> skill_params = get_parameters<SkillParametersTaxHammer>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("approach",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("AbovePose"),skill_params->approach_speed,skill_params->approach_acc);

    Eigen::Matrix<double,2,1> t_scale;
    t_scale<<1,1;
    move->set_scale(t_scale);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxHammer::create_down_mp(const Percept &p){
    std::shared_ptr<SkillParametersTaxHammer> skill_params = get_parameters<SkillParametersTaxHammer>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("down",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("GoalPose"),skill_params->approach_speed,skill_params->approach_acc);

    Eigen::Matrix<double,2,1> t_scale;
    t_scale<<1,1;
    move->set_scale(t_scale);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxHammer::create_up_mp(const Percept &p){
    std::shared_ptr<SkillParametersTaxHammer> skill_params = get_parameters<SkillParametersTaxHammer>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("down",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("AbovePose"),skill_params->approach_speed,skill_params->approach_acc);

    Eigen::Matrix<double,2,1> t_scale;
    t_scale<<1,1;
    move->set_scale(t_scale);
    return mp;
}

bool TaxHammer::check_local_pre_conditions(const Percept &p){
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Hammer")->name){
        return false;
    }
    Eigen::Matrix<double,4,4> T_container = get_object_pose_T("Hammerable");
    std::shared_ptr<SkillParametersTaxHammer> skill_params = get_parameters<SkillParametersTaxHammer>();
    for(unsigned i=0;i<3;i++){
        if(p.proprioception.T_T_EE(3,i)<T_container(3,i)+skill_params->ROI_x(i*2) || p.proprioception.T_T_EE(3,i)<T_container(3,i)+skill_params->ROI_x(i*2+1)){
            return false;
        }
    }
    return true;
}

bool TaxHammer::check_local_suc_conditions(const Percept &p){
    return fabs((p.proprioception.T_T_EE.block<3,1>(0,3)-get_object_pose_T("GoalPose").block<3,1>(0,3)).norm())<0.001;
}

bool TaxHammer::check_local_ex_conditions(const Percept &p){
    return true;
}

bool TaxHammer::check_local_err_conditions(const Percept &p){
    std::shared_ptr<SkillParametersTaxHammer> skill_params = get_parameters<SkillParametersTaxHammer>();
    const Eigen::Matrix<double,6,1>& ROI_x=get_parameters<SkillParametersTaxHammer>()->ROI_x;
    const Eigen::Matrix<double,6,1>& ROI_phi=get_parameters<SkillParametersTaxHammer>()->ROI_phi;
    double error_angle=acos(p.proprioception.T_T_EE.block<3,1>(0,2).dot(get_object_pose_T("Hammerable").block<3,1>(0,2)));
    Eigen::Matrix<double,3,1> dist = p.proprioception.T_T_EE.block<3,1>(0,3)-get_object_pose_T("Hammerable").block<3,1>(0,3);
    if(dist(0) < ROI_x(0) || dist(0) > ROI_x(1) || dist(1) < ROI_x(2) || dist(1) > ROI_x(3) || dist(2) < ROI_x(4) || dist(2) > ROI_x(5)){
        return true;
    }
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Stylus")->name){
        return true;
    }
    if(m_n_cnt>skill_params->n_max){
        return true;
    }
    return false;
}

}
