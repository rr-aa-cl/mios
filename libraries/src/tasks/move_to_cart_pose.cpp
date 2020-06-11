#include "tasks/move_to_cart_pose.hpp"
#include "skills/move_to_pose_cart.hpp"
#include <msrm_utils/json.hpp>

namespace mios {

MoveToCartPose::MoveToCartPose(Core* core):Task("MoveToCartPose",core){

}

void MoveToCartPose::initialize_context(){
    reserve_skill("move");
}

void MoveToCartPose::execute(){
    overwrite_context("move","control","control_mode",2);
    overwrite_context("move","skill","speed",msrm_utils::from_eigen<double,2,1>(m_speed));
    overwrite_context("move","skill","acc",msrm_utils::from_eigen<double,2,1>(m_acc));
    overwrite_context("move","skill","TF_T_EE_g",msrm_utils::from_eigen<double,4,4>(m_T_EE_g));
    write_skill_object("move","goal_pose",m_pose.value_or("NullObject"));
    execute_skill<MoveToPoseCart,SkillParametersMoveToPoseCart>("move");
}

bool MoveToCartPose::read_parameters(const nlohmann::json &params){
    m_pose = msrm_utils::from_json<std::string>(params,"pose");
    if(!msrm_utils::read_json_param<double,4,4>(params,"T_EE_g",m_T_EE_g)){
        m_T_EE_g.setZero();
    }
    if(m_T_EE_g.isZero() && !m_pose.has_value()){
        spdlog::error("MoveToCartPose task requires either a location that exists in memory or an explicit goal pose.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(params,"speed",m_speed)){
        spdlog::error("Could not read parameter: speed");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(params,"acc",m_acc)){
        spdlog::error("Could not read parameter: acc");
        return false;
    }
    return true;
}

void MoveToCartPose::evaluate(){
    write_result(get_result().skill_results["move"].success,get_result().skill_results["move"].cost_suc,get_result().skill_results["move"].cost_err,get_result().skill_results["move"].results);
}

}
