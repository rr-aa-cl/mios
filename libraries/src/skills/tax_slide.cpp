#include "skills/tax_slide.hpp"
#include "strategies/desired_wrench_strategy.hpp"
#include "strategies/move_to_pose.hpp"
#include <msrm_cpp_utils/math.hpp>

namespace mios{

bool SkillParametersTaxSlide::from_json(const nlohmann::json& parameters){
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"speed",speed)){
        spdlog::error("Parameter speed could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"acc",acc)){
        spdlog::error("Parameter acc could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"f_slide",f_slide)){
        spdlog::error("Parameter f_slide could not be loaded but is mandatory.");
        return false;
    }
    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersTaxSlide::get_parameter_list(){
    return {{"speed",{}},{"acc",{}},{"f_slide",{}}};
}

TaxSlide::TaxSlide(const std::string& name, Memory* memory, Portal *portal):Skill("TaxSlide",{"Slidable","GoalLocation"},name,memory,portal,{ControlMode::mCartTorque}){

}

Eigen::Matrix<double,3,3> TaxSlide::get_O_R_T_0(const Percept &p) const{
    if(get_object("Slidable")->name!="NullObject"){
        return get_object("Slidable")->O_T_OB.block<3,3>(0,0);
    }else{
        throw SkillException("No valid object has been grounded.");
    }
}

std::shared_ptr<ManipulationPrimitive> TaxSlide::get_initial_mp(const Percept& p){
    return create_slide_mp(p);
}

std::shared_ptr<ManipulationPrimitive> TaxSlide::create_slide_mp(const Percept &p){
    std::shared_ptr<SkillParametersTaxSlide> skill_params = get_parameters<SkillParametersTaxSlide>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("pull",p);
    mp->create_strategy<MoveToPoseStrategy>("slide",1);
    mp->create_strategy<DesiredWrenchStrategy>("push",1);
    std::shared_ptr<MoveToPoseStrategy> slide = mp->get_strategy<MoveToPoseStrategy>("slide");
    slide->set_goal(get_object_pose_T("GoalLocation"),skill_params->speed,skill_params->acc);
    std::shared_ptr<DesiredWrenchStrategy> push = mp->get_strategy<DesiredWrenchStrategy>("push");
    Eigen::Matrix<double,6,1> F_d;
    F_d<<0,0,skill_params->f_slide,0,0,0;
    push->set_TF_F_d(F_d,m_memory->read_parameters()->limits.cartesian_space.dF_J_max);
    return mp;
}

bool TaxSlide::check_local_pre_conditions(const Percept &p){
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Slidable")->name){
        return false;
    }
    if(p.proprioception.TF_F_ext_K(2)<m_memory->read_parameters()->user.F_ext_contact(2)){
        return false;
    }
    return true;
}

bool TaxSlide::check_local_suc_conditions(const Percept &p){
    return get_active_mp()->get_strategy_interface("move")->finished();
}

bool TaxSlide::check_local_err_conditions(const Percept &p){
    if(m_memory->get_live_context()->grasped_object->name!=get_object("Slidable")->name){
        return true;
    }
    if(p.proprioception.TF_F_ext_K(2)<m_memory->read_parameters()->user.F_ext_contact(2)){
        return false;
    }
    return false;
}

}
