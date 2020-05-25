#include "skills/move_to_pose_joint.hpp"

namespace mios {

bool SkillParametersMoveToPoseJoint::read_parameters(const nlohmann::json &p){
    msrm_utils::read_json_param<double,1,1>(p,"speed",speed);
    msrm_utils::read_json_param<double,1,1>(p,"acc",acc);
    msrm_utils::read_json_param<double,7,1>(p,"q_g_offset",q_g_offset);

    if(!msrm_utils::read_json_param<double,7,1>(p,"q_g",q_g)){
        msrm_utils::print_error("Parameter q_g could not be loaded but is mandatory.");
        return false;
    }
    return true;
}

MoveToPoseJoint::MoveToPoseJoint(const std::string &id, Memory *memory, const Percept &p):Skill("MoveToPoseJoint",{"goal_pose"},id,memory,p){
}

std::shared_ptr<ManipulationPrimitive> MoveToPoseJoint::get_initial_mp(const Percept &p_0){
    std::shared_ptr<ManipulationPrimitive> mp = create_mp<BasicJointPrimitive,MPParametersBasicJointMP,BasicJointAttractor>("move",p_0);
    std::shared_ptr<MPParametersBasicJointMP> mp_params = mp->get_parameters<MPParametersBasicJointMP>();
    std::shared_ptr<BasicJointAttractor> mp_attr = mp->get_attractor<BasicJointAttractor>();
    std::shared_ptr<SkillParametersMoveToPoseJoint> skill_params = get_parameters<SkillParametersMoveToPoseJoint>();
    mp_params->dq_d<<skill_params->speed(0)*m_memory->read_parameters()->user.dq_max(0);
    mp_params->dq_d<<skill_params->acc(0)*m_memory->read_parameters()->user.ddq_max(0);

    mp_attr->attr_vel<<0,0,0,0,0,0,0;
    if(this->get_object("loc_goal")->name=="none"){
        mp_attr->attr_pose=skill_params->q_g;
    }else{
        mp_attr->attr_pose=get_object("goal_pose")->q;
    }

    mp_attr->attr_pose=mp_attr->attr_pose+skill_params->q_g_offset;
    return mp;
}

bool MoveToPoseJoint::check_local_suc_conditions(const Percept &p){
    return get_active_mp()->get_attractor<BasicJointAttractor>()->reached(p);
}

bool MoveToPoseJoint::check_local_ex_conditions(const Percept &p){
    return true;
}

void MoveToPoseJoint::evaluate(){
    write_costs(0,std::chrono::duration_cast<std::chrono::seconds>(get_result().p_1.time-get_result().p_0.time).count());
}

}
