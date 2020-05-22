#include "data_structures/parameters.hpp"
#include <spdlog/spdlog.h>
#include <msrm_utils/json.hpp>
#include <nlohmann/json.hpp>

namespace mios {

LimitParameters::LimitParameters(){
    joint_space.dddq_max.setZero();
    joint_space.ddq_max.setZero();
    joint_space.dq_max.setZero();
    joint_space.q_upper.setZero();
    joint_space.q_lower.setZero();
    joint_space.tau_J_max.setZero();
    joint_space.dtau_J_max.setZero();
    joint_space.tau_ext_max.setZero();
    joint_space.K_theta_max.setZero();
    joint_space.dK_theta_max.setZero();
    joint_space.xi_theta_max.setZero();
    joint_space.dxi_theta_max.setZero();

    cartesian_space.dddX_max.setZero();
    cartesian_space.ddX_max.setZero();
    cartesian_space.dX_max.setZero();
    cartesian_space.x_lower.setZero();
    cartesian_space.x_upper.setZero();
    cartesian_space.F_J_max.setZero();
    cartesian_space.dF_J_max.setZero();
    cartesian_space.K_x_max.setZero();
    cartesian_space.dK_x_max.setZero();
    cartesian_space.xi_x_max.setZero();
    cartesian_space.dxi_x_max.setZero();
}

bool LimitParameters::read_parameters(const nlohmann::json &parameters){
    if(!msrm_utils::read_json_param<double,7,1>(parameters,"dddq_max",joint_space.dddq_max)){
        spdlog::error("Could not read dddq_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,7,1>(parameters,"ddq_max",joint_space.ddq_max)){
        spdlog::error("Could not read ddq_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,7,1>(parameters,"dq_max",joint_space.dq_max)){
        spdlog::error("Could not read dq_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,7,1>(parameters,"q_upper",joint_space.q_upper)){
        spdlog::error("Could not read q_upper.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,7,1>(parameters,"q_lower",joint_space.q_lower)){
        spdlog::error("Could not read q_lower.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,7,1>(parameters,"tau_J_max",joint_space.tau_J_max)){
        spdlog::error("Could not read tau_J_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,7,1>(parameters,"dtau_J_max",joint_space.dtau_J_max)){
        spdlog::error("Could not read dtau_J_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,7,1>(parameters,"tau_ext_max",joint_space.tau_ext_max)){
        spdlog::error("Could not read tau_ext_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,7,1>(parameters,"K_theta_max",joint_space.K_theta_max)){
        spdlog::error("Could not read K_theta_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,7,1>(parameters,"dK_theta_max",joint_space.dK_theta_max)){
        spdlog::error("Could not read dK_theta_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,7,1>(parameters,"xi_theta_max",joint_space.xi_theta_max)){
        spdlog::error("Could not read xi_theta_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,7,1>(parameters,"dxi_theta_max",joint_space.dxi_theta_max)){
        spdlog::error("Could not read dxi_theta_max.");
        return false;
    }

    if(!msrm_utils::read_json_param<double,2,1>(parameters,"dddX_max",cartesian_space.dddX_max)){
        spdlog::error("Could not read dddX_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"ddX_max",cartesian_space.ddX_max)){
        spdlog::error("Could not read ddX_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"dX_max",cartesian_space.dX_max)){
        spdlog::error("Could not read dX_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,3,1>(parameters,"x_upper",cartesian_space.x_upper)){
        spdlog::error("Could not read x_upper.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,3,1>(parameters,"x_lower",cartesian_space.x_lower)){
        spdlog::error("Could not read x_lower.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"F_J_max",cartesian_space.F_J_max)){
        spdlog::error("Could not read F_J_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"dF_J_max",cartesian_space.dF_J_max)){
        spdlog::error("Could not read dF_J_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"F_ext_max",cartesian_space.F_ext_max)){
        spdlog::error("Could not read F_ext_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters,"K_x_max",cartesian_space.K_x_max)){
        spdlog::error("Could not read K_x_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters,"dK_x_max",cartesian_space.dK_x_max)){
        spdlog::error("Could not read dK_x_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters,"xi_x_max",cartesian_space.xi_x_max)){
        spdlog::error("Could not read xi_x_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters,"dxi_x_max",cartesian_space.dxi_x_max)){
        spdlog::error("Could not read dxi_x_max.");
        return false;
    }
    return true;
}

nlohmann::json LimitParameters::get_default_values(){
    nlohmann::json default_values;
    default_values["dddq"]={7500,3750,5000,6250,7500,10000,10000};
    default_values["ddq"]={15,7.5,10,12.5,15,20,20};
    default_values["dq"]={2.1,2.1,2.1,2.1,2.6,2.6,2.6};
    default_values["q_upper"]={2.85,1.7,2.85,0,2.85,3.7,2.85};
    default_values["q_lower"]={-2.85,-1.7,-2.85,-3,-2.85,-0.05,-2.85};
    default_values["tau_J_max"]={87,87,87,87,12,12,12};
    default_values["dtau_J_max"]={1000,1000,1000,1000,1000,1000,1000};

    default_values["K_theta_max"]={10000,10000,10000,10000,10000,10000,10000};
    default_values["dK_theta_max"]={10000,10000,10000,10000,10000,10000,10000};
    default_values["xi_theta_max"]={2,2,2,2,2,2,2};
    default_values["dxi_theta_max"]={10,10,10,10,10,10,10};

    default_values["tau_ext_max"]={87,87,87,87,12,12,12};

    default_values["x_upper"]={0.96,0.96,1.3};
    default_values["x_lower"]={-0.96,-0.96,-0.4};

    default_values["dX_max"]={1.7,2.5};
    default_values["ddX_max"]={13,25};
    default_values["dddX_max"]={6500,12500};

    default_values["F_ext_max"]={100,50};

    default_values["F_J_max"]={100,50};
    default_values["dF_J_max"]={1000,500};

    default_values["K_x_max"]={3000,3000,3000,200,200,200};
    default_values["dK_x_max"]={5000,5000,5000,500,500,500};
    default_values["xi_x_max"]={2,2,2,2,2,2};
    default_values["dxi_x_max"]={10,10,10,10,10,10};
    return default_values;
}

UserParameters::UserParameters(){
    dX_max.setZero();
    ddX_max.setZero();
    dq_max.setZero();
    ddq_max.setZero();

    F_ext_contact.setZero();
    tau_ext_contact.setZero();
    F_ext_max.setZero();
    tau_ext_max.setZero();

    load_m=0;
    load_com.setZero();
    load_I.setZero();

    safe_mode=true;
}

bool UserParameters::read_parameters(const nlohmann::json &parameters){
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"dX_max",dX_max)){
        spdlog::error("Could not read dX_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"ddX_max",ddX_max)){
        spdlog::error("Could not read ddX_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,7,1>(parameters,"dq_max",dq_max)){
        spdlog::error("Could not read dq_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,7,1>(parameters,"ddq_max",ddq_max)){
        spdlog::error("Could not read ddq_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters,"F_ext_contact",F_ext_contact)){
        spdlog::error("Could not read F_ext_contact.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters,"F_ext_max",F_ext_max)){
        spdlog::error("Could not read F_ext_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,7,1>(parameters,"tau_ext_contact",tau_ext_contact)){
        spdlog::error("Could not read tau_ext_contact.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,7,1>(parameters,"tau_ext_max",tau_ext_max)){
        spdlog::error("Could not read tau_ext_max.");
        return false;
    }

    if(!msrm_utils::read_json_param(parameters,"load_m",load_m)){
        spdlog::error("Could not read load_m.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,3,1>(parameters,"load_com",load_com)){
        spdlog::error("Could not read load_com.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,3,3>(parameters,"load_I",load_I)){
        spdlog::error("Could not read load_I.");
        return false;
    }

    if(!msrm_utils::read_json_param(parameters,"safe_mode",safe_mode)){
        spdlog::error("Could not read safe_mode.");
        return false;
    }
    return true;
}

nlohmann::json UserParameters::get_default_values(){
    nlohmann::json default_values;
    default_values["dX_max"]={1.7,2.5};
    default_values["ddX_max"]={13,25};
    default_values["dq_max"]={2.1,2.1,2.1,2.1,2.6,2.6,2.6};
    default_values["ddq_max"]={15,7.5,10,12.5,15,20,20};

    default_values["F_ext_contact"]={4,2};
    default_values["F_ext_max"]={100,50};
    default_values["tau_ext_contact"]={2,2,2,2,2,2,2};
    default_values["tau_ext_max"]={87,87,87,87,12,12,12};

    default_values["load_m"]=0;
    default_values["load_com"]={0,0,0};
    default_values["load_I"]={0,0,0,0,0,0,0,0,0};

    default_values["safe_mode"]=true;
    return default_values;
}

FramesParameters::FramesParameters(){
    O_R_T=Eigen::Matrix<double,3,3>::Identity();
    F_T_EE=Eigen::Matrix<double,3,3>::Identity();
    EE_T_TCP=Eigen::Matrix<double,3,3>::Identity();
    EE_T_K=Eigen::Matrix<double,3,3>::Identity();
}

bool FramesParameters::read_parameters(const nlohmann::json &parameters){
    if(!msrm_utils::read_json_param<double,3,3>(parameters,"O_R_T",O_R_T)){
        spdlog::error("Could not read O_R_T.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,4,4>(parameters,"F_T_EE",F_T_EE)){
        spdlog::error("Could not read F_T_EE.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,4,4>(parameters,"EE_T_TCP",EE_T_TCP)){
        spdlog::error("Could not read EE_T_TCP.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,4,4>(parameters,"EE_T_K",EE_T_K)){
        spdlog::error("Could not read EE_T_K.");
        return false;
    }
    return true;
}

nlohmann::json FramesParameters::get_default_values(){
    nlohmann::json default_values;
    default_values["O_R_T"]={1,0,0,0,1,0,0,0,1};
    default_values["F_T_EE"]={1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1};
    default_values["EE_T_TCP"]={1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1};
    default_values["EE_T_K"]={1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1};
    return default_values;
}

SystemParameters::SystemParameters(){
    robot_ip={};
    desk_name={};
    desk_pwd={};

    has_robot=false;
    has_gripper=false;
}

bool SystemParameters::read_parameters(const nlohmann::json &parameters){
    if(!msrm_utils::read_json_param(parameters,"robot_ip",robot_ip)){
        spdlog::error("Could not read robot_ip.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"desk_name",desk_name)){
        spdlog::error("Could not read desk_name.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"desk_pwd",desk_pwd)){
        spdlog::error("Could not read desk_pwd.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"has_robot",has_robot)){
        spdlog::error("Could not read has_robot.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"has_gripper",has_gripper)){
        spdlog::error("Could not read has_gripper.");
        return false;
    }
    return true;
}

nlohmann::json SystemParameters::get_default_values(){
    nlohmann::json default_values;
    default_values["robot_ip"]="";
    default_values["desk_name"]="";
    default_values["desk_pwd"]="";
    default_values["has_robot"]=false;
    default_values["has_gripper"]=false;
    return default_values;
}

SkillParameters::SkillParameters(){
    common.time_max=0;
    common.w_cost_function.resize(1);
    common.w_cost_function[0]=1;
    common.parallels_frequency=1;
}

void SkillParameters::read_global_skill_parameters(const nlohmann::json &p){
    msrm_utils::read_json_param(p,"time_max",common.time_max);
    msrm_utils::read_json_param(p,"w_cost_function",common.w_cost_function);
    msrm_utils::read_json_param(p,"parallels_frequency",common.parallels_frequency);
}

void SkillParameters::read_skill_objects(const nlohmann::json &p){
    for(const auto& o : p.items()){
        common.objects.insert(std::make_pair(o.key(),o.value()));
    }
}

Parameters::Parameters():limits(LimitParameters()),system(ParametersSystem()),control(ParametersControl()),prototype(nullptr){

}

}
