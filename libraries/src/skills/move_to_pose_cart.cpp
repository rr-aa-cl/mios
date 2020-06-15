#include "skills/move_to_pose_cart.hpp"
#include "strategies/move_to_pose.hpp"

namespace mios {

bool SkillParametersMoveToPoseCart::from_json(const nlohmann::json &p){
    if(!msrm_utils::read_json_param<double,2,1>(p,"speed",speed)){
        spdlog::error("Parameter speed could not be loaded but is mandatory.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(p,"acc",acc)){
        spdlog::error("Parameter acc could not be loaded but is mandatory.");
        return false;
    }
    msrm_utils::read_json_param<double,4,4>(p,"q_g_offset",TF_g_offset);

    if(!msrm_utils::read_json_param<double,4,4>(p,"TF_T_EE_g",TF_T_EE_g)){
        spdlog::error("Parameter TF_T_EE_g could not be loaded but is mandatory.");
        return false;
    }
    return true;
}

MoveToPoseCart::MoveToPoseCart(const std::string &id, Memory *memory, Portal *portal, const Percept &p):Skill("MoveToPoseJoint",{"goal_pose"},id,memory,portal,p){
}

std::shared_ptr<ManipulationPrimitive> MoveToPoseCart::get_initial_mp(const Percept &p_0){
    std::shared_ptr<SkillParametersMoveToPoseCart> skill_params = get_parameters<SkillParametersMoveToPoseCart>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("move",p_0);
    mp->create_strategy<MoveToPoseStrategy>("s_0",1);
    Eigen::Matrix<double,4,4> T_g;
    if(this->get_object("goal_pose")->name=="NullObject"){
        T_g=skill_params->TF_T_EE_g;
    }else{
        T_g=get_object("goal_pose")->O_T_OB;
    }
    Eigen::Matrix<double,2,1> speed;
    Eigen::Matrix<double,2,1> acc;
    speed<<skill_params->speed(0)*m_memory->read_parameters()->user.dX_max(0),skill_params->speed(1)*m_memory->read_parameters()->user.dX_max(1);
    acc<<skill_params->acc(0)*m_memory->read_parameters()->user.ddX_max(0),skill_params->acc(1)*m_memory->read_parameters()->user.ddX_max(1);
    mp->get_strategy<MoveToPoseStrategy>("s_0")->set_goal(T_g,speed,acc);
    Eigen::Matrix<double,2,1> scale;
    scale<<1,1;
    mp->get_strategy<MoveToPoseStrategy>("s_0")->set_scale(scale);
    return mp;
}

bool MoveToPoseCart::check_local_suc_conditions(const Percept &p){
    return get_active_mp()->get_strategy<MoveToPoseStrategy>("s_0")->finished();
}

bool MoveToPoseCart::check_local_ex_conditions(const Percept &p){
    return true;
}

void MoveToPoseCart::evaluate(){
    write_costs(0,std::chrono::duration_cast<std::chrono::seconds>(get_result().p_1.time-get_result().p_0.time).count());
}

}
