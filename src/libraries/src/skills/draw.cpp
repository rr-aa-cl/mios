#include "mios/skills/draw.hpp"
#include "mios/strategies/move_to_pose.hpp"

namespace mios{


bool SkillParametersDraw::from_json(const nlohmann::json &parameters){
    if(!msrm_utils::read_json_param(parameters,"path_file",path_file)){
        spdlog::error("Parameter path_file could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"f_draw",f_draw)){
        spdlog::error("Parameter f_draw could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"file_mode",file_mode)){
        spdlog::error("Parameter file_mode could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"port_src",port_src)){
        spdlog::error("Parameter port_src could not be loaded but is mandatory.");
        return false;
    }

    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersDraw::get_parameter_list(){
    return {{"path_file",{}},{"f_draw",{}},{"file_mode",{}},{"port_src",{}}};
}

Draw::Draw(const std::string &name, Memory *memory,Portal* portal):Skill("Draw",{"Surface","Pen"},name,memory,portal,{ControlMode::mCartTorque}){

}

Eigen::Matrix<double, 3, 3> Draw::get_O_R_T_0([[maybe_unused]] const Percept &p) const{
    return get_object("Surface")->O_T_OB.block<3,3>(0,0);
}

std::shared_ptr<ManipulationPrimitive> Draw::get_initial_mp(const Percept &p_0){
    return create_approach_mp(p_0);
}

std::shared_ptr<ManipulationPrimitive> Draw::create_approach_mp(const Percept &p){
    std::shared_ptr<SkillParametersDraw> skill_params = get_parameters<SkillParametersDraw>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("approach",p);
    mp->create_strategy<MoveToPoseStrategy>("move",1);
    std::shared_ptr<MoveToPoseStrategy> move = mp->get_strategy<MoveToPoseStrategy>("move");
    Eigen::Matrix<double,4,4> T_a_offset = get_object_pose_T("Approach");
    Eigen::Matrix<double,4,4> T_a = get_object_pose_T("Approach");
    T_a.block<3,3>(0,0)=T_a_offset.block<3,3>(0,0)*T_a.block<3,3>(0,0);
    T_a.block<3,1>(0,3)+=skill_params->DeltaX.block<3,1>(0,0);
    move->set_goal(T_a,skill_params->approach_speed,skill_params->approach_acc);
    return mp;
}


}
