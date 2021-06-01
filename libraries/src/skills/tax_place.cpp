#include "skills/tax_place.hpp"
#include "strategies/twist_strategy.hpp"
#include "strategies/move_to_pose.hpp"
#include "strategies/gripper_strategy.hpp"
#include "strategies/null_strategy.hpp"
#include "msrm_cpp_utils/math.hpp"

namespace mios{

bool SkillParametersTaxPlace::from_json(const nlohmann::json& parameters){
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"approach_speed",approach_speed)){
        spdlog::error("Parameter approach_speed could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"approach_acc",approach_acc)){
        spdlog::error("Parameter approach_acc could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"place_speed",place_speed)){
        spdlog::error("Parameter place_speed could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"place_acc",place_acc)){
        spdlog::error("Parameter place_acc could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"release_width",release_width)){
        spdlog::error("Parameter release_width could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"release_speed",release_speed)){
        spdlog::error("Parameter release_speed could not be loaded but is mandatory.");
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
    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersTaxPlace::get_parameter_list(){
    return {{"approach_speed",{}},{"approach_acc",{}},{"place_speed",{}},{"place_acc",{}},{"release_width",{}},{"release_speed",{}},{"ROI_x",{}},{"ROI_phi",{}}};
}

TaxPlace::TaxPlace(const std::string& name, Memory* memory, Portal* portal):Skill("TaxPlace",{"Placeable","Surface", "Approach", "Retract"},name,memory,portal,{ControlMode::mCartTorque,ControlMode::mCartVelocity}){

}

Eigen::Matrix<double,3,3> TaxPlace::get_O_R_T_0(const Percept &p) const{
    if(get_object("Surface")->name!="NullObject"){
        return get_object("Surface")->O_T_OB.block<3,3>(0,0);
    }else{
        throw SkillException("No valid object has been grounded.");
    }
}

std::shared_ptr<ManipulationPrimitive> TaxPlace::get_initial_mp(const Percept& p){
    return create_approach_mp(p);
}

std::optional<std::shared_ptr<ManipulationPrimitive> > TaxPlace::graph_transition(const Percept &p){
    if(get_active_mp()->get_name()=="approach"){
        if(get_active_mp()->get_strategy_interface("move")->finished()){
            return create_pre_release_mp(p);
        }else{
            return {};
        }
    }
    if(get_active_mp()->get_name()=="pre_release"){
        if(p.proprioception.TF_F_ext_K(2)>m_memory->read_parameters()->user.F_ext_contact(0)){
            return create_release_mp(p);
        }else{
            return {};
        }
    }
    if(get_active_mp()->get_name()=="release"){
//        if(get_result().success){
        if(get_active_mp()->get_strategy_interface("release")->finished()){
            return create_retract_mp(p);
        }else{
            return {};
        }
    }
    return {};
}

std::shared_ptr<ManipulationPrimitive> TaxPlace::create_approach_mp(const Percept &p){
    std::shared_ptr<SkillParametersTaxPlace> skill_params = get_parameters<SkillParametersTaxPlace>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("approach",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("Approach"),skill_params->approach_speed,skill_params->approach_acc);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxPlace::create_pre_release_mp(const Percept &p){
    std::shared_ptr<SkillParametersTaxPlace> skill_params = get_parameters<SkillParametersTaxPlace>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("pre_release",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");

    Eigen::Matrix<double,4,4> T_g=get_object_pose_T("Surface");
    T_g.block<3,3>(0,0)=p.proprioception.T_T_EE.block<3,3>(0,0);
    Eigen::Matrix<double,3,1> goal_dir=T_g.block<3,1>(0,3)-p.proprioception.T_T_EE.block<3,1>(0,3);
    goal_dir.normalize();
    T_g.block<3,1>(0,3)+=goal_dir*0.1;

    move->set_goal(T_g,skill_params->place_speed,skill_params->place_acc);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxPlace::create_release_mp(const Percept &p){


    std::shared_ptr<SkillParametersTaxPlace> skill_params = get_parameters<SkillParametersTaxPlace>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("release",p);
//    mp->create_strategy<NullStrategy>("sim_release",1);
//    m_t_sim=std::chrono::high_resolution_clock::now();


    mp->create_strategy<GripperStrategy>("release",1);
    std::shared_ptr<GripperStrategy> release = mp->get_strategy<GripperStrategy>("release");
    release->move(skill_params->release_width,skill_params->release_speed);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxPlace::create_retract_mp(const Percept &p){
    std::shared_ptr<SkillParametersTaxPlace> skill_params = get_parameters<SkillParametersTaxPlace>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("retract",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("Retract"),skill_params->place_speed,skill_params->place_acc);
    return mp;
}

bool TaxPlace::check_local_pre_conditions(const Percept &p){
    return true;
    Eigen::Matrix<double,4,4> T_container = get_object_pose_T("Surface");
    std::shared_ptr<SkillParametersTaxPlace> skill_params = get_parameters<SkillParametersTaxPlace>();
    for(unsigned i=0;i<3;i++){
        if(p.proprioception.T_T_EE(3,i)<T_container(3,i)+skill_params->ROI_x(i*2) || p.proprioception.T_T_EE(3,i)>T_container(3,i)+skill_params->ROI_x(i*2+1)){
            return false;
        }
    }
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Placeable")->name){
        return false;
    }
    return true;
}

bool TaxPlace::check_local_suc_conditions(const Percept &p){
//    if(std::chrono::duration_cast<std::chrono::milliseconds>(std::chrono::high_resolution_clock::now()-m_t_sim).count()>700 && get_active_mp()->get_name()=="release"){
//        return true;
//    }
    if(m_memory->get_live_context()->grasped_object->name=="NullObject"){
        return true;
    }
    return false;
}

bool TaxPlace::check_local_ex_conditions(const Percept &p){
    if(m_memory->get_live_context()->grasped_object->name=="NullObject"){
        return true;
    }
    if(get_active_mp()->get_name()=="retract"){
        if(get_active_mp()->get_strategy_interface("move")->finished()){
            if((p.proprioception.T_T_EE.block<3,1>(0,3)-get_object_pose_T("Retract").block<3,1>(0,3)).norm()<m_memory->read_parameters()->user.env_X(0)
               && acos(((get_object_pose_T("Retract").block<3,3>(0,0).transpose()*p.proprioception.T_T_EE.block<3,3>(0,0)).trace()-1)/2) < m_memory->read_parameters()->user.env_X(1)){
                return true;
            }else{
                return false;
            }
        }
    }
    return false;
}


bool TaxPlace::check_local_err_conditions(const Percept &p){
    const Eigen::Matrix<double,6,1>& ROI_x=get_parameters<SkillParametersTaxPlace>()->ROI_x;
    const Eigen::Matrix<double,6,1>& ROI_phi=get_parameters<SkillParametersTaxPlace>()->ROI_phi;
    double error_angle=acos(p.proprioception.T_T_EE.block<3,1>(0,2).dot(get_object_pose_T("Surface").block<3,1>(0,2)));
    Eigen::Matrix<double,3,1> dist = p.proprioception.T_T_EE.block<3,1>(0,3)-get_object_pose_T("Surface").block<3,1>(0,3);
    if(dist(0) < ROI_x(0) || dist(0) > ROI_x(1) || dist(1) < ROI_x(2) || dist(1) > ROI_x(3) || dist(2) < ROI_x(4) || dist(2) > ROI_x(5)){
        return true;
    }
    return false;
}

double TaxPlace::get_goal_heuristic(const Percept &p){
//    bool h = m_memory->get_live_context()->grasped_object->name==get_object("Placeable")->name;
    bool h = !get_result().success;
    return (get_result().p_1.proprioception.T_T_EE.block<3,1>(0,3)-get_object_pose_T("Retract").block<3,1>(0,3)).norm() +
            acos(((get_object_pose_T("Retract").block<3,3>(0,0).transpose()*p.proprioception.T_T_EE.block<3,3>(0,0)).trace()-1)/2) +
            h * 1;
}

}
