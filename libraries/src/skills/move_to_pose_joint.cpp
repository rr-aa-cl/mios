#include "skills/move_to_pose_joint.hpp"
#include <spdlog/spdlog.h>
#include "strategies/move_to_joint_pose.hpp"

namespace mios {

bool SkillParametersMoveToPoseJoint::read_parameters(const nlohmann::json &p){
    if(!msrm_utils::read_json_param(p,"speed",speed)){
        spdlog::error("Parameter speed could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param(p,"acc",acc)){
        spdlog::error("Parameter acc could not be loaded but is mandatory.");
        return false;
    }
    msrm_utils::read_json_param<double,7,1>(p,"q_g_offset",q_g_offset);

    if(!msrm_utils::read_json_param<double,7,1>(p,"q_g",q_g)){
        spdlog::error("Parameter q_g could not be loaded but is mandatory.");
        return false;
    }
    return true;
}

MoveToPoseJoint::MoveToPoseJoint(const std::string &id, Memory *memory, const Percept &p):Skill("MoveToPoseJoint",{"goal_pose"},id,memory,p){
}

std::shared_ptr<ManipulationPrimitive> MoveToPoseJoint::get_initial_mp(const Percept &p_0){
    std::shared_ptr<SkillParametersMoveToPoseJoint> skill_params = get_parameters<SkillParametersMoveToPoseJoint>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("move",p_0);
    mp->create_strategy<MoveToJointPoseStrategy>("s_0",1);
    std::shared_ptr<MoveToJointPoseStrategy> move_s0 = mp->get_strategy<MoveToJointPoseStrategy>("s_0");
    Eigen::Matrix<double,7,1> q_g;
    if(this->get_object("goal_pose")->name=="NullObject"){
        q_g=skill_params->q_g;
    }else{
        q_g=get_object("goal_pose")->q;
    }
    move_s0->set_goal(q_g,skill_params->speed*m_memory->read_parameters()->user.dq_max(0),skill_params->acc*m_memory->read_parameters()->user.ddq_max(0));
    return mp;
}

bool MoveToPoseJoint::check_local_suc_conditions(const Percept &p){
    return get_active_mp()->get_strategy<MoveToJointPoseStrategy>("s_0")->finished();
}

bool MoveToPoseJoint::check_local_ex_conditions(const Percept &p){
    return true;
}

void MoveToPoseJoint::evaluate(){
    write_costs(0,std::chrono::duration_cast<std::chrono::seconds>(get_result().p_1.time-get_result().p_0.time).count());
}

}
