#include "data_structures/parameters.hpp"
#include <spdlog/spdlog.h>
#include <msrm_utils/json.hpp>
#include <nlohmann/json.hpp>
#include "skills/nullskill.hpp"

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
    if(parameters.find("joint_space")==parameters.end()){
        spdlog::error("Control parameters do not have joint_space subsection.");
        return false;
    }
    if(parameters.find("cartesian_space")==parameters.end()){
        spdlog::error("Control parameters do not have cartesian_space subsection.");
        return false;
    }

    if(!msrm_utils::read_json_param<double,7,1>(parameters["joint_space"],"dddq_max",joint_space.dddq_max)){
        spdlog::error("Could not read dddq_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,7,1>(parameters["joint_space"],"ddq_max",joint_space.ddq_max)){
        spdlog::error("Could not read joint_space.ddq_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,7,1>(parameters["joint_space"],"dq_max",joint_space.dq_max)){
        spdlog::error("Could not read joint_space.dq_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,7,1>(parameters["joint_space"],"q_upper",joint_space.q_upper)){
        spdlog::error("Could not read joint_space.q_upper.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,7,1>(parameters["joint_space"],"q_lower",joint_space.q_lower)){
        spdlog::error("Could not read joint_space.q_lower.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,7,1>(parameters["joint_space"],"tau_J_max",joint_space.tau_J_max)){
        spdlog::error("Could not read joint_space.tau_J_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,7,1>(parameters["joint_space"],"dtau_J_max",joint_space.dtau_J_max)){
        spdlog::error("Could not read joint_space.dtau_J_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,7,1>(parameters["joint_space"],"tau_ext_max",joint_space.tau_ext_max)){
        spdlog::error("Could not read joint_space.tau_ext_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,7,1>(parameters["joint_space"],"K_theta_max",joint_space.K_theta_max)){
        spdlog::error("Could not read joint_space.K_theta_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,7,1>(parameters["joint_space"],"dK_theta_max",joint_space.dK_theta_max)){
        spdlog::error("Could not read joint_space.dK_theta_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,7,1>(parameters["joint_space"],"xi_theta_max",joint_space.xi_theta_max)){
        spdlog::error("Could not read joint_space.xi_theta_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,7,1>(parameters["joint_space"],"dxi_theta_max",joint_space.dxi_theta_max)){
        spdlog::error("Could not read joint_space.dxi_theta_max.");
        return false;
    }

    if(!msrm_utils::read_json_param<double,2,1>(parameters["cartesian_space"],"dddX_max",cartesian_space.dddX_max)){
        spdlog::error("Could not read cartesian_space.dddX_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters["cartesian_space"],"ddX_max",cartesian_space.ddX_max)){
        spdlog::error("Could not read cartesian_space.ddX_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters["cartesian_space"],"dX_max",cartesian_space.dX_max)){
        spdlog::error("Could not read cartesian_space.dX_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,3,1>(parameters["cartesian_space"],"x_upper",cartesian_space.x_upper)){
        spdlog::error("Could not read cartesian_space.x_upper.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,3,1>(parameters["cartesian_space"],"x_lower",cartesian_space.x_lower)){
        spdlog::error("Could not read cartesian_space.x_lower.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters["cartesian_space"],"F_J_max",cartesian_space.F_J_max)){
        spdlog::error("Could not read cartesian_space.F_J_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters["cartesian_space"],"dF_J_max",cartesian_space.dF_J_max)){
        spdlog::error("Could not read cartesian_space.dF_J_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters["cartesian_space"],"F_ext_max",cartesian_space.F_ext_max)){
        spdlog::error("Could not read cartesian_space.F_ext_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters["cartesian_space"],"K_x_max",cartesian_space.K_x_max)){
        spdlog::error("Could not read cartesian_space.K_x_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters["cartesian_space"],"dK_x_max",cartesian_space.dK_x_max)){
        spdlog::error("Could not read cartesian_space.dK_x_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters["cartesian_space"],"xi_x_max",cartesian_space.xi_x_max)){
        spdlog::error("Could not read cartesian_space.xi_x_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters["cartesian_space"],"dxi_x_max",cartesian_space.dxi_x_max)){
        spdlog::error("Could not read cartesian_space.dxi_x_max.");
        return false;
    }
    return true;
}

nlohmann::json LimitParameters::get_default_values(){
    nlohmann::json default_values;
    nlohmann::json joint_space;
    nlohmann::json cartesian_space;
    joint_space["dddq"]={7500,3750,5000,6250,7500,10000,10000};
    joint_space["ddq"]={15,7.5,10,12.5,15,20,20};
    joint_space["dq"]={2.1,2.1,2.1,2.1,2.6,2.6,2.6};
    joint_space["q_upper"]={2.85,1.7,2.85,0,2.85,3.7,2.85};
    joint_space["q_lower"]={-2.85,-1.7,-2.85,-3,-2.85,-0.05,-2.85};
    joint_space["tau_J_max"]={87,87,87,87,12,12,12};
    joint_space["dtau_J_max"]={1000,1000,1000,1000,1000,1000,1000};

    joint_space["K_theta_max"]={10000,10000,10000,10000,10000,10000,10000};
    joint_space["dK_theta_max"]={10000,10000,10000,10000,10000,10000,10000};
    joint_space["xi_theta_max"]={2,2,2,2,2,2,2};
    joint_space["dxi_theta_max"]={10,10,10,10,10,10,10};

    joint_space["tau_ext_max"]={87,87,87,87,12,12,12};

    cartesian_space["x_upper"]={0.96,0.96,1.3};
    cartesian_space["x_lower"]={-0.96,-0.96,-0.4};

    cartesian_space["dX_max"]={1.7,2.5};
    cartesian_space["ddX_max"]={13,25};
    cartesian_space["dddX_max"]={6500,12500};

    cartesian_space["F_ext_max"]={100,50};

    cartesian_space["F_J_max"]={100,50};
    cartesian_space["dF_J_max"]={1000,500};

    cartesian_space["K_x_max"]={3000,3000,3000,200,200,200};
    cartesian_space["dK_x_max"]={5000,5000,5000,500,500,500};
    cartesian_space["xi_x_max"]={2,2,2,2,2,2};
    cartesian_space["dxi_x_max"]={10,10,10,10,10,10};

    default_values["joint_space"]=joint_space;
    default_values["cartesian_space"]=cartesian_space;
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
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"F_ext_contact",F_ext_contact)){
        spdlog::error("Could not read F_ext_contact.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,2,1>(parameters,"F_ext_max",F_ext_max)){
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
    F_T_EE=Eigen::Matrix<double,4,4>::Identity();
    EE_T_TCP=Eigen::Matrix<double,4,4>::Identity();
    EE_T_K=Eigen::Matrix<double,4,4>::Identity();
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
    desk_user={};
    desk_pwd={};

    has_robot=false;
    has_gripper=false;
}

bool SystemParameters::read_parameters(const nlohmann::json &parameters){
    if(!msrm_utils::read_json_param(parameters,"robot_ip",robot_ip)){
        spdlog::error("Could not read robot_ip.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters,"desk_name",desk_user)){
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

ControlParameters::ControlParameters(){
    cart_imp_adaptation_stage.L.setZero();
    cart_imp_adaptation_stage.alpha.setZero();
    cart_imp_adaptation_stage.beta.setZero();
    cart_imp_adaptation_stage.gamma_a.setZero();
    cart_imp_adaptation_stage.gamma_b.setZero();
    cart_imp_adaptation_stage.F_ff_0.setZero();
    cart_imp_adaptation_stage.kappa=0;
    cart_imp.K_x.setZero();
    cart_imp.xi.setZero();

    joint_imp.K_theta.setZero();
    joint_imp.xi_theta.setZero();

    force_control.k_p.setZero();
    force_control.k_i.setZero();
    force_control.k_d.setZero();
    force_control.k_d_N.setZero();
    force_control.d_max.setZero();
    force_control.phi_max.setZero();
    force_control.active.setZero();
    force_control.sf_on=false;

    virtual_cube.eta.setZero();
    virtual_cube.f_max.setZero();
    virtual_cube.walls.setZero();
    virtual_cube.active=false;
    virtual_cube.damping.setZero();
    virtual_cube.rho_min.setZero();
    virtual_cube.damping_dist.setZero();

    virtual_joint_walls.eta.setZero();
    virtual_joint_walls.tau_max.setZero();
    virtual_joint_walls.walls.setZero();
    virtual_joint_walls.active=false;
    virtual_joint_walls.damping.setZero();
    virtual_joint_walls.rho_min.setZero();
    virtual_joint_walls.damping_dist.setZero();

    nullspace_control.q_d.setZero();
    nullspace_control.active=false;
    nullspace_control.K_theta.setZero();
    nullspace_control.xi_theta.setZero();
}

bool ControlParameters::read_parameters(const nlohmann::json &parameters){
    if(parameters.find("cart_imp")==parameters.end()){
        spdlog::error("Control parameters do not have cart_imp subsection.");
        return false;
    }
    if(parameters.find("cart_imp_adaptation_stage")==parameters.end()){
        spdlog::error("Control parameters do not have cart_imp_adaptation_stage subsection.");
        return false;
    }
    if(parameters.find("joint_imp")==parameters.end()){
        spdlog::error("Control parameters do not have joint_imp subsection.");
        return false;
    }
    if(parameters.find("force_control")==parameters.end()){
        spdlog::error("Control parameters do not have force_control subsection.");
        return false;
    }
    if(parameters.find("virtual_cube")==parameters.end()){
        spdlog::error("Control parameters do not have virtual_cube subsection.");
        return false;
    }
    if(parameters.find("virtual_joint_walls")==parameters.end()){
        spdlog::error("Control parameters do not have virtual_joint_walls subsection.");
        return false;
    }
    if(parameters.find("nullspace_control")==parameters.end()){
        spdlog::error("Control parameters do not have nullspace_control subsection.");
        return false;
    }

    if(!msrm_utils::read_json_param<double,6,1>(parameters["cart_imp"],"K_x",cart_imp.K_x)){
        spdlog::error("Could not read cart_imp.K_x.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters["cart_imp"],"xi_x",cart_imp.xi)){
        spdlog::error("Could not read cart_imp.xi_x.");
        return false;
    }

    if(!msrm_utils::read_json_param<double,6,1>(parameters["cart_imp_adaptation_stage"],"L",cart_imp_adaptation_stage.L)){
        spdlog::error("Could not read cart_imp_adaptation_stage.L.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters["cart_imp_adaptation_stage"],"F_ff_0",cart_imp_adaptation_stage.F_ff_0)){
        spdlog::error("Could not read cart_imp_adaptation_stage.F_ff_0.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters["cart_imp_adaptation_stage"],"alpha",cart_imp_adaptation_stage.alpha)){
        spdlog::error("Could not read cart_imp_adaptation_stage.alpha.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters["cart_imp_adaptation_stage"],"beta",cart_imp_adaptation_stage.beta)){
        spdlog::error("Could not read cart_imp_adaptation_stage.beta.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters["cart_imp_adaptation_stage"],"gamma_a",cart_imp_adaptation_stage.gamma_a)){
        spdlog::error("Could not read cart_imp_adaptation_stage.gamma_a.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters["cart_imp_adaptation_stage"],"gamma_b",cart_imp_adaptation_stage.gamma_b)){
        spdlog::error("Could not read cart_imp_adaptation_stage.gamma_b.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters["cart_imp_adaptation_stage"],"kappa",cart_imp_adaptation_stage.kappa)){
        spdlog::error("Could not read cart_imp_adaptation_stage.kappa.");
        return false;
    }

    if(!msrm_utils::read_json_param<double,7,1>(parameters["joint_imp"],"K_theta",joint_imp.K_theta)){
        spdlog::error("Could not read joint_imp.K_theta.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,7,1>(parameters["joint_imp"],"xi_theta",joint_imp.xi_theta)){
        spdlog::error("Could not read joint_imp.xi_theta.");
        return false;
    }

    if(!msrm_utils::read_json_param<double,6,1>(parameters["force_control"],"k_p",force_control.k_p)){
        spdlog::error("Could not read force_control.k_p.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters["force_control"],"k_i",force_control.k_i)){
        spdlog::error("Could not read force_control.k_i.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters["force_control"],"k_d",force_control.k_d)){
        spdlog::error("Could not read force_control.k_d.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters["force_control"],"k_d_N",force_control.k_d_N)){
        spdlog::error("Could not read force_control.k_d_N.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,3,1>(parameters["force_control"],"d_max",force_control.d_max)){
        spdlog::error("Could not read force_control.d_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,1,1>(parameters["force_control"],"phi_max",force_control.phi_max)){
        spdlog::error("Could not read force_control.phi_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters["force_control"],"active",force_control.active)){
        spdlog::error("Could not read force_control.active.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters["force_control"],"sf_on",force_control.sf_on)){
        spdlog::error("Could not read force_control.sf_on.");
        return false;
    }

    if(!msrm_utils::read_json_param<double,1,1>(parameters["virtual_cube"],"damping",virtual_cube.damping)){
        spdlog::error("Could not read virtual_cube.damping.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,1,1>(parameters["virtual_cube"],"damping_dist",virtual_cube.damping_dist)){
        spdlog::error("Could not read virtual_cube.damping_dist.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,1,1>(parameters["virtual_cube"],"eta",virtual_cube.eta)){
        spdlog::error("Could not read virtual_cube.eta.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,1,1>(parameters["virtual_cube"],"rho_min",virtual_cube.rho_min)){
        spdlog::error("Could not read virtual_cube.rho_min.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,6,1>(parameters["virtual_cube"],"walls",virtual_cube.walls)){
        spdlog::error("Could not read virtual_cube.walls.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,1,1>(parameters["virtual_cube"],"f_max",virtual_cube.f_max)){
        spdlog::error("Could not read virtual_cube.f_max.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters["virtual_cube"],"active",virtual_cube.active)){
        spdlog::error("Could not read virtual_cube.active.");
        return false;
    }

    if(!msrm_utils::read_json_param<double,7,1>(parameters["virtual_joint_walls"],"damping",virtual_joint_walls.damping)){
        spdlog::error("Could not read virtual_joint_walls.damping.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,7,1>(parameters["virtual_joint_walls"],"damping_dist",virtual_joint_walls.damping_dist)){
        spdlog::error("Could not read virtual_joint_walls.damping_dist.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,7,1>(parameters["virtual_joint_walls"],"eta",virtual_joint_walls.eta)){
        spdlog::error("Could not read virtual_joint_walls.eta.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,7,1>(parameters["virtual_joint_walls"],"rho_min",virtual_joint_walls.rho_min)){
        spdlog::error("Could not read virtual_joint_walls.rho_min.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,7,1>(parameters["virtual_joint_walls"],"f_max",virtual_joint_walls.tau_max)){
        spdlog::error("Could not read virtual_joint_walls.f_max.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,14,1>(parameters["virtual_joint_walls"],"walls",virtual_joint_walls.walls)){
        spdlog::error("Could not read virtual_joint_walls.walls.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters["virtual_joint_walls"],"active",virtual_joint_walls.active)){
        spdlog::error("Could not read virtual_joint_walls.active.");
        return false;
    }

    if(!msrm_utils::read_json_param<double,7,1>(parameters["nullspace_control"],"q_d",nullspace_control.q_d)){
        spdlog::error("Could not read nullspace_control.q_d.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,7,1>(parameters["nullspace_control"],"K_theta",nullspace_control.K_theta)){
        spdlog::error("Could not read nullspace_control.K_theta.");
        return false;
    }
    if(!msrm_utils::read_json_param<double,7,1>(parameters["nullspace_control"],"xi_theta",nullspace_control.xi_theta)){
        spdlog::error("Could not read nullspace_control.xi_theta.");
        return false;
    }
    if(!msrm_utils::read_json_param(parameters["nullspace_control"],"active",nullspace_control.active)){
        spdlog::error("Could not read nullspace_control.active.");
        return false;
    }

    return true;
}

nlohmann::json ControlParameters::get_default_values(){
    nlohmann::json default_values;
    nlohmann::json cart_imp;
    nlohmann::json cart_imp_adaptation_stage;
    nlohmann::json joint_imp;
    nlohmann::json force_control;
    nlohmann::json virtual_cube;
    nlohmann::json virtual_joint_walls;
    nlohmann::json nullspace_control;
    cart_imp["K_x"]={1000,1000,1000,100,100,100};
    cart_imp["xi_x"]={0.7,0.7,0.7,0.7,0.7,0.7};

    cart_imp_adaptation_stage["alpha"]={0,0,0,0,0,0};
    cart_imp_adaptation_stage["beta"]={0,0,0,0,0,0};
    cart_imp_adaptation_stage["gamma_a"]={0,0,0,0,0,0};
    cart_imp_adaptation_stage["gamma_b"]={0,0,0,0,0,0};
    cart_imp_adaptation_stage["L"]={0,0,0,0,0,0};
    cart_imp_adaptation_stage["F_ff_0"]={0,0,0,0,0,0};
    cart_imp_adaptation_stage["kappa"]=0;

    joint_imp["K_theta"]={1000,1000,750,500,300,200,100};
    joint_imp["xi_theta"]={0.7,0.7,0.7,0.7,0.7,0.7,0.7};

    force_control["k_p"]={0,0,0,0,0,0};
    force_control["k_i"]={0,0,0,0,0,0};
    force_control["k_d"]={0,0,0,0,0,0};
    force_control["k_d_N"]={0,0,0,0,0,0};
    force_control["active"]={0,0,0,0,0,0};
    force_control["d_max"]={0,0,0};
    force_control["phi_max"]={0};
    force_control["sf_on"]=false;

    virtual_cube["damping"]={0};
    virtual_cube["damping-dist"]={0};
    virtual_cube["eta"]={0};
    virtual_cube["rho_min"]={0};
    virtual_cube["walls"]={0,0,0,0,0,0};
    virtual_cube["f_max"]={0};
    virtual_cube["active"]=false;

    virtual_joint_walls["damping"]={0};
    virtual_joint_walls["damping-dist"]={0};
    virtual_joint_walls["eta"]={0};
    virtual_joint_walls["rho_min"]={0};
    virtual_joint_walls["walls"]={0,0,0,0,0,0,0,0,0,0,0,0,0,0};
    virtual_joint_walls["f_max"]={0};
    virtual_joint_walls["active"]=false;

    nullspace_control["q_d"]={0,0,0,0,0,0,0};
    nullspace_control["K_theta"]={0,0,0,0,0,0,0};
    nullspace_control["xi_theta"]={0,0,0,0,0,0,0};
    nullspace_control["active"]=false;

    default_values["cart_imp"]=cart_imp;
    default_values["cart_imp_adaptation_stage"]=cart_imp_adaptation_stage;
    default_values["joint_imp"]=joint_imp;
    default_values["force_control"]=force_control;
    default_values["virtual_cube"]=virtual_cube;
    default_values["virtual_joint_walls"]=virtual_joint_walls;
    default_values["nullspace_control"]=nullspace_control;
    return default_values;
}

SkillParameters::SkillParameters(){
    common.time_max=0;
    common.w_cost_function.resize(1);
    common.w_cost_function[0]=1;
    common.parallels_frequency=1;
}

bool SkillParameters::read_global_skill_parameters(const nlohmann::json &p){
    if(!msrm_utils::read_json_param(p,"time_max",common.time_max)){
        spdlog::error("Could not read time_max.");
        return false;
    }
    if(!msrm_utils::read_json_param(p,"w_cost_function",common.w_cost_function)){
        spdlog::error("Could not read cost_function.");
        return false;
    }
    if(!msrm_utils::read_json_param(p,"parallels_frequency",common.parallels_frequency)){
        spdlog::error("Could not read parallels_frequency.");
        return false;
    }
    return true;
}

void SkillParameters::read_skill_objects(const nlohmann::json &p){
    for(const auto& o : p.items()){
        common.objects.insert(std::make_pair(o.key(),o.value()));
    }
}

Parameters::Parameters():control(ControlParameters()),system(SystemParameters()),limits(LimitParameters()),user(UserParameters()),
    frames(FramesParameters()),skill(std::make_unique<SkillParametersNullSkill>()){

}

}
