#include "skills/tax_wipe.hpp"
#include "strategies/move_to_pose.hpp"

#include "msrm_cpp_utils/math.hpp"

namespace mios{

bool SkillParametersTaxWipe::from_json(const nlohmann::json& parameters){
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"approach_speed",approach_speed)){
        spdlog::error("Parameter approach_speed could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"approach_acc",approach_acc)){
        spdlog::error("Parameter approach_acc could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"wipe_speed",wipe_speed)){
        spdlog::error("Parameter wipe_speed could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"wipe_acc",wipe_acc)){
        spdlog::error("Parameter wipe_acc could not be loaded but is mandatory.");
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

std::map<std::string, std::set<std::string> > SkillParametersTaxWipe::get_parameter_list(){
    return {{"approach_speed",{}},{"approach_acc",{}},{"wipe_speed",{}},{"wipe_acc",{}},{"ROI_x",{}},{"ROI_phi",{}}};
}

TaxWipe::TaxWipe(const std::string& name, Memory* memory, Portal* portal):Skill("TaxWipe",{"Wipeable"},name,memory,portal,{ControlMode::mCartTorque}){

}

Eigen::Matrix<double,3,3> TaxWipe::get_O_R_T_0(const Percept &p) const{
    if(get_object("Wipeable")->name!="NullObject"){
        return get_object("Wipeable")->O_T_OB.block<3,3>(0,0);
    }else{
        throw SkillException("No valid object has been grounded.");
    }
}

std::shared_ptr<ManipulationPrimitive> TaxWipe::get_initial_mp(const Percept& p){
    m_ROI_center=get_object_pose_T("Wipeable").block<3,1>(0,3);
    return create_approach_mp(p);
}

std::optional<std::shared_ptr<ManipulationPrimitive> > TaxWipe::graph_transition(const Percept &p){
    if(get_active_mp()->get_name()=="approach"){
        if(get_active_mp()->get_strategy_interface("move")->finished()){
            return create_wipe_mp(p);
        }else{
            return {};
        }
    }
    return {};
}

std::shared_ptr<ManipulationPrimitive> TaxWipe::create_approach_mp(const Percept &p){
    std::shared_ptr<SkillParametersTaxWipe> skill_params = get_parameters<SkillParametersTaxWipe>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("approach",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("Approach"),skill_params->wipe_speed,skill_params->wipe_acc);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> TaxWipe::create_wipe_mp(const Percept &p){
    std::shared_ptr<SkillParametersTaxWipe> skill_params = get_parameters<SkillParametersTaxWipe>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("wipe",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    move->set_goal(get_object_pose_T("Approach"),skill_params->wipe_speed,skill_params->wipe_acc);
    return mp;
}

bool TaxWipe::check_local_pre_conditions(const Percept &p){
    Eigen::Matrix<double,4,4> T_container = get_object_pose_T("Wipeable");
    std::shared_ptr<SkillParametersTaxWipe> skill_params = get_parameters<SkillParametersTaxWipe>();
    for(unsigned i=0;i<3;i++){
        if(p.proprioception.T_T_EE(3,i)<T_container(3,i)+skill_params->ROI_x(i*2) || p.proprioception.T_T_EE(3,i)<T_container(3,i)+skill_params->ROI_x(i*2+1)){
            return false;
        }
    }
    return true;
}

bool TaxWipe::check_local_err_conditions(const Percept &p){
    if(get_active_mp()->get_name()=="wipe"){
        if(get_active_mp()->get_strategy_interface("move")->finished()){
            std::shared_ptr<SkillParametersTaxWipe> skill_params = get_parameters<SkillParametersTaxWipe>();
            Eigen::Matrix<double,4,4> T_wipeable = get_object_pose_T("Wipeable");
            for(unsigned i=0;i<3;i++){
                if(T_wipeable(i,3) > m_ROI_center(i)+skill_params->ROI_x(i*2) || T_wipeable(i,3) < m_ROI_center(i)+skill_params->ROI_x(i*2+1)){
                    return true;
                }
            }
        }
    }
    return false;
}

void TaxWipe::update_internal_models(const Percept &p){
    if(p.proprioception.TF_F_ext_K.block<3,1>(0,0).norm()>m_memory->read_parameters()->user.F_ext_contact(0)){
        m_memory->get_object("Wipeable")->set_pose(p.proprioception.O_T_EE(0,3),p.proprioception.O_T_EE(1,3),p.proprioception.O_T_EE(2,3),{});
    }
}

bool TaxWipe::check_local_suc_conditions(const Percept &p){
    std::shared_ptr<SkillParametersTaxWipe> skill_params = get_parameters<SkillParametersTaxWipe>();
    Eigen::Matrix<double,4,4> T_wipeable = get_object_pose_T("Wipeable");
    for(unsigned i=0;i<3;i++){
        if(T_wipeable(i,3) > m_ROI_center(i)+skill_params->ROI_x(i*2) || T_wipeable(i,3) < m_ROI_center(i)+skill_params->ROI_x(i*2+1)){
            return false;
        }
    }
    return true;
}

bool TaxWipe::check_local_ex_conditions(const Percept &p){
    if(get_active_mp()->get_name()=="wipe"){
        return get_active_mp()->get_strategy_interface("move")->finished();
    }
    return false;
}

}
