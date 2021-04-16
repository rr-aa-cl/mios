#include "skills/tax_move.hpp"
#include "strategies/move_to_pose.hpp"
#include "strategies/gripper_strategy.hpp"
#include <franka/exception.h>

namespace mios {

bool SkillParametersTaxMove::from_json(const nlohmann::json &p){
    spdlog::trace("SkillParametersTaxMove::from_json");
    if(!msrm_utils::read_json_param(p,"t_settle",t_settle)){
        t_settle=0;
    }
    if(!msrm_utils::read_json_param<double,2,1>(p,"speed",speed)){
        spdlog::error("Parameter speed could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(p,"acc",acc)){
        spdlog::error("Parameter acc could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,4,4>(p,"T_T_EE_g_offset",T_T_EE_g_offset)){
        T_T_EE_g_offset.setIdentity();
    }
    bool object_set=false;
    if(!p["objects"].is_null()){
        if(p["objects"].find("GoalPose")!=p["objects"].end()){
            object_set=true;
        }
    }

    if(!msrm_utils::read_json_param<double,4,4>(p,"T_T_EE_g",T_T_EE_g) && !object_set){
        T_T_EE_g.setIdentity();
    }
    if(!msrm_utils::read_json_param(p,"finger_width",finger_width)){
        finger_width=-1;
    }
    if(!msrm_utils::read_json_param(p,"finger_speed",finger_speed)){
        finger_speed=0;
    }
    return true;
}

std::map<std::string, std::set<std::string> > SkillParametersTaxMove::get_parameter_list(){
    return {{"t_settle",{}},{"speed",{}},{"acc",{}},{"T_T_EE_g_offset",{}},{"T_T_EE_g",{}},{"finger_width",{}},{"finger_speed",{}}};
}

TaxMove::TaxMove(const std::string &id, Memory *memory, Portal *portal):Skill("TaxMove",{"GoalPose"},id,memory,portal,{ControlMode::mCartTorque,ControlMode::mCartVelocity}),
m_finished(false){
}

std::shared_ptr<ManipulationPrimitive> TaxMove::get_initial_mp(const Percept &p_0){
    std::shared_ptr<SkillParametersTaxMove> skill_params = get_parameters<SkillParametersTaxMove>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("move",p_0);
    mp->create_strategy<MoveToPoseStrategy>("s_0",1);
    Eigen::Matrix<double,4,4> T_g;
    if(this->get_object("GoalPose")->name=="NullObject"){
        T_g=skill_params->T_T_EE_g;
        spdlog::warn("No GoalPose was set, moving to O_T_OB");
    }else{
        T_g=get_object("GoalPose")->O_T_OB;
    }
    T_g.block<3,1>(0,3)+=skill_params->T_T_EE_g_offset.block<3,1>(0,3);
    T_g.block<3,3>(0,0)=skill_params->T_T_EE_g_offset.block<3,3>(0,0)*T_g.block<3,3>(0,0);
    mp->get_strategy<MoveToPoseStrategy>("s_0")->set_goal(T_g,skill_params->speed,skill_params->acc);
    Eigen::Matrix<double,2,1> scale;
    scale<<1,1;
    mp->get_strategy<MoveToPoseStrategy>("s_0")->set_scale(scale);

    if(skill_params->finger_width!=-1 && skill_params->finger_speed!=0){
        mp->create_strategy<GripperStrategy>("gripper",1);
        mp->get_strategy<GripperStrategy>("gripper")->move(skill_params->finger_width,skill_params->finger_speed);
    }
    return mp;
}

bool TaxMove::check_local_suc_conditions(const Percept &p){
    if(get_active_mp()->get_strategy<MoveToPoseStrategy>("s_0")->finished()){
        if(!m_finished){
            m_finished=true;
            m_t_finished=std::chrono::high_resolution_clock::now();
        }

        if((p.proprioception.T_T_EE.block<3,1>(0,3)-get_object_pose_T("GoalPose").block<3,1>(0,3)).norm()<m_memory->read_parameters()->user.env_X(0)
           && acos(((get_object_pose_T("GoalPose").block<3,3>(0,0).transpose()*p.proprioception.T_T_EE.block<3,3>(0,0)).trace()-1)/2) < m_memory->read_parameters()->user.env_X(1)){
            return true;
        }else{
            return false;
        }
    }else{
        return false;
    }
}

bool TaxMove::check_local_ex_conditions(const Percept &p){
    if(std::chrono::duration_cast<std::chrono::milliseconds>(p.time-m_t_finished).count()>=get_parameters<SkillParametersTaxMove>()->t_settle*1000){
        return true;
    }else{
        return false;
    }
}

double TaxMove::get_goal_heuristic(const Percept &p){
    return (p.proprioception.T_T_EE.block<3,1>(0,3)-get_object_pose_T("GoalPose").block<3,1>(0,3)).norm() +
            acos(((get_object_pose_T("GoalPose").block<3,3>(0,0).transpose()*p.proprioception.T_T_EE.block<3,3>(0,0)).trace()-1)/2);
}

}
