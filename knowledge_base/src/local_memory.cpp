#include "knowledge_base/local_memory.hpp"

#include "interface/parameter_server.hpp"

namespace mios {

MiosState::MiosState(){
    this->active_skill="none";
    this->active_task="none";
    this->grasped_object="none";
}

Percept::Percept(){
    this->set_0();
    robot_mode=franka::RobotMode::kIdle;
    time=0;
}

void Percept::set_0(){
    O_T_EE.setZero();
    TF_T_EE.setZero();
    q.setZero();
    dq.setZero();
    theta.setZero();
    dtheta.setZero();
    O_dX.setZero();
    TF_dX.setZero();
    tau_ext.setZero();
    tau_j.setZero();
    K_F_ext.setZero();
    K_dF_ext.setZero();
    O_F_ext.setZero();
    O_dF_ext.setZero();
    TF_F_ext.setZero();
    TF_dF_ext.setZero();
    M.setZero();
    C.setZero();
    G.setZero();
    B_J_EE.setZero();
    B_J_O.setZero();
    rho.setZero();
    gripper_width=0;
    is_grasping=false;

    TF_T_EE_d=Eigen::Matrix<double,4,4>::Identity();
    TF_dX_d.setZero();
    TF_F_ff.setZero();
    q_d.setZero();
    dq_d.setZero();
    tau_ff.setZero();
}

ConfigLimits::ConfigLimits(){
    q_upper<<2.85,1.7,2.85,0,2.85,3.7,2.85;
    q_lower<<-2.85,-1.7,-2.85,-3,-2.85,-0.05,-2.85;

    dq_max<<2.1,2.1,2.1,2.1,2.6,2.6,2.6;
    ddq_max<<15,7.5,10,12.5,15,20,20;
    dddq_max<<7500,3750,5000,6250,7500,10000,10000;

    tau_J_max<<87,87,87,87,12,12,12;
    dtau_J_max<<1000,1000,1000,1000,1000,1000,1000;

    K_theta_max<<10000,10000,10000,10000,10000,10000,10000;
    dK_theta_max<<10000,10000,10000,10000,10000,10000,10000;
    xi_theta_max<<2,2,2,2,2,2,2;
    dxi_theta_max<<10,10,10,10,10,10,10;

    tau_ext_max<<87,87,87,87,12,12,12;

    x_upper<<0.96,0.96,1.3;
    x_lower<<-0.96,-0.96,-0.4;

    dX_max<<1.7,2.5;
    ddX_max<<1,2;
    dddX_max<<6500,12500;

    F_ext_max<<80,30;

    F_J_max<<80,30;
    dF_J_max<<800,300;

    K_x_max<<2000,2000,2000,200,200,200;
    dK_x_max<<5000,5000,5000,500,500,500;
    xi_x_max<<2,2,2,2,2,2;
    dxi_x_max<<10,10,10,10,10,10;
}

ConfigUser::ConfigUser(){
    neighborhood_X.setOnes()*std::numeric_limits<double>::max();
    neighborhood_dX.setOnes()*std::numeric_limits<double>::max();
    neighborhood_F.setOnes()*std::numeric_limits<double>::max();
    neighborhood_dF.setOnes()*std::numeric_limits<double>::max();
    neighborhood_q.setOnes()*std::numeric_limits<double>::max();
    neighborhood_dq.setOnes()*std::numeric_limits<double>::max();

    x_limits<<-2,2,-2,2,-2,2;
    phi_limits<<-5,5,-5,5,-5,5;

    dX_max.setZero();
    ddX_max.setZero();
    dq_max.setZero();
    ddq_max.setZero();

    F_contact<<4,4,4,1,1,1;
    tau_contact<<1,1,1,1,1,1,1;

    F_max<<60,60,60,30,30,30;
    tau_max<<60,60,60,60,10,10,10;

    e_x_max.setZero();
    e_q_max.setZero();

    load_m=0;
    load_com.setZero();
    load_I.setZero();

    this->grasped_object="none";
}

void ConfigUser::read_parameters(const nlohmann::json &p){
    cpp_utils::read_json_param<double,2,1>(p,"neighborhood_X",neighborhood_X);
    cpp_utils::read_json_param<double,2,1>(p,"neighborhood_dX",neighborhood_dX);
    cpp_utils::read_json_param<double,2,1>(p,"neighborhood_F",neighborhood_F);
    cpp_utils::read_json_param<double,2,1>(p,"neighborhood_dF",neighborhood_dF);
    cpp_utils::read_json_param<double,1,1>(p,"neighborhood_q",neighborhood_q);
    cpp_utils::read_json_param<double,1,1>(p,"neighborhood_dq",neighborhood_dq);

    cpp_utils::read_json_param<double,6,1>(p,"x_limits",x_limits);
    cpp_utils::read_json_param<double,6,1>(p,"phi_limits",phi_limits);

    cpp_utils::read_json_param<double,2,1>(p,"dX_max",dX_max);
    cpp_utils::read_json_param<double,2,1>(p,"ddX_max",ddX_max);
    cpp_utils::read_json_param<double,1,1>(p,"dq_max",dq_max);
    cpp_utils::read_json_param<double,1,1>(p,"ddq_max",ddq_max);

    cpp_utils::read_json_param<double,6,1>(p,"F_contact",F_contact);
    cpp_utils::read_json_param<double,7,1>(p,"tau_contact",tau_contact);
    cpp_utils::read_json_param<double,6,1>(p,"F_max",F_max);
    cpp_utils::read_json_param<double,7,1>(p,"tau_max",tau_max);

    cpp_utils::read_json_param<double,2,1>(p,"e_x_max",e_x_max);
    cpp_utils::read_json_param<double,1,1>(p,"e_q_max",e_q_max);

    cpp_utils::read_json_param(p,"load_m",load_m);
    cpp_utils::read_json_param<double,3,1>(p,"load_com",load_com);
    cpp_utils::read_json_param<double,3,3>(p,"load_I",load_I);
}

void ConfigUser::read_hidden_parameters(const nlohmann::json &p){
    cpp_utils::read_json_param(p,"grasped_object",grasped_object);
}

ConfigFrames::ConfigFrames(){
    O_R_TF.setIdentity();
    F_T_EE<<0.7071,-0.7071,0,0,0.7071,0.7071,0,0,0,0,1,0,0,0,0.1034,1;
    EE_T_TCP.setIdentity();
    EE_T_K.setIdentity();
    EE_T_C.setIdentity();
}

void ConfigFrames::read_parameters(const nlohmann::json &p){
    cpp_utils::read_json_param<double,3,3>(p,"O_R_TF",O_R_TF);
    cpp_utils::read_json_param<double,4,4>(p,"F_T_EE",F_T_EE);
    cpp_utils::read_json_param<double,4,4>(p,"EE_T_TCP",EE_T_TCP);
    cpp_utils::read_json_param<double,4,4>(p,"EE_T_K",EE_T_K);
    cpp_utils::read_json_param<double,4,4>(p,"EE_T_C",EE_T_C);
}

ConfigGeneral::ConfigGeneral(){
    safe_mode=true;
    instant_recovery=false;
    logging=false;
    control_mode=0;
    command_mode=0;
}

void ConfigGeneral::read_parameters(const nlohmann::json &p){
    cpp_utils::read_json_param(p,"safe_mode",safe_mode);
    cpp_utils::read_json_param(p,"instant_recovery",instant_recovery);
    cpp_utils::read_json_param(p,"logging",logging);
    cpp_utils::read_json_param(p,"control_mode",control_mode);
    cpp_utils::read_json_param(p,"command_mode",command_mode);
}

ConfigSystem::ConfigSystem(){
    ip_robot="none";
    id_robot="none";
    desk_pwd="frankaRSI";
    desk_name="franka";
    ip_simulation="none";

    port_simulation=0;

    verbosity=0;

    has_robot=true;
    has_gripper=true;
    has_simulation=false;
    has_sound=false;
    has_led=false;

    this->path_executable="";

//    telemetry_domain="none";
//    telemetry_url="none";
//    telemetry_key="none";
//    telemetry_device_id="none";
//    telemetry_port=443;
//    telemetry_frequency=50;
//    telemetry_send=false;
    telemetry_on=false;
    telemetry_udp_ip="none";
    telemetry_udp_port=0;
    telemetry_udp_frequency=1000;
}

void ConfigSystem::read_parameters(const nlohmann::json &p){
    cpp_utils::read_json_param(p,"ip_robot",ip_robot);
    cpp_utils::read_json_param(p,"id_robot",id_robot);
    cpp_utils::read_json_param(p,"desk_name",desk_name);
    cpp_utils::read_json_param(p,"desk_pwd",desk_pwd);
    cpp_utils::read_json_param(p,"ip_simulation",ip_simulation);
    cpp_utils::read_json_param(p,"port_simulation",port_simulation);

    cpp_utils::read_json_param(p,"location",location);

    cpp_utils::read_json_param(p,"verbosity",verbosity);

    cpp_utils::read_json_param(p,"has_robot",has_robot);
    cpp_utils::read_json_param(p,"has_gripper",has_gripper);
    cpp_utils::read_json_param(p,"has_simulation",has_simulation);
    cpp_utils::read_json_param(p,"has_sound",has_sound);
    cpp_utils::read_json_param(p,"has_led",has_led);

    if(has_simulation){
        has_robot=false;
        has_gripper=false;
    }

//    cpp_utils::read_json_param(p["telemetry_domain"],telemetry_domain);
//    cpp_utils::read_json_param(p["telemetry_url"],telemetry_url);
//    cpp_utils::read_json_param(p["telemetry_key"],telemetry_key);
//    cpp_utils::read_json_param(p["telemetry_device_id"],telemetry_device_id);
//    cpp_utils::read_json_param(p["telemetry_port"],telemetry_port);
//    cpp_utils::read_json_param(p["telemetry_frequency"],telemetry_frequency);
//    cpp_utils::read_json_param(p["telemetry_send"],telemetry_send);

    cpp_utils::read_json_param(p,"telemetry_on",telemetry_on);
    cpp_utils::read_json_param(p,"telemetry_udp_ip",telemetry_udp_ip);
    cpp_utils::read_json_param(p,"telemetry_udp_port",telemetry_udp_port);
    cpp_utils::read_json_param(p,"telemetry_udp_frequency",telemetry_udp_frequency);
}

ConfigController::ConfigController(){
    this->alpha.setZero();
    this->beta.setZero();
    this->gamma_a.setZero();
    this->gamma_b.setZero();
    this->K_0.setZero();
    this->F_ff_0.setZero();
    this->L.setZero();
    this->xi.setZero();
    this->kappa=5;
    this->K_max.setZero();
    this->dK_max.setZero();
    this->F_ff_max<<1000,1000,1000,1000,1000,1000;
    this->dF_ff_max<<1000,1000,1000,1000,1000,1000;
    this->F_c_max<<1000,1000,1000,1000,1000,1000;
    this->dF_c_max<<1000,1000,1000,1000,1000,1000;
    this->tau_c_max.setZero();
    this->dtau_c_max.setZero();
    this->K_theta.setZero();
    this->xi_theta.setZero();

    this->f_cntr_k_p.setZero();
    this->f_cntr_k_i.setZero();
    this->f_cntr_k_d.setZero();
    this->f_cntr_k_d_N.setZero();
    this->f_cntr_d_max.setZero();
    this->f_cntr_phi_max.setZero();
    this->f_cntr_active.setZero();
    this->f_cntr_sf_on=false;

    this->virt_cube_on=false;
    this->virt_cube_damp.setZero();
    this->virt_cube_damp_dist.setZero();
    this->virt_cube_eta.setZero();
    this->virt_cube_rho_min.setZero();
    this->virt_cube_walls.setZero();
    this->virt_cube_f_max.setZero();

    this->virt_walls_joint_on=false;
    this->virt_walls_joint_damp.setZero();
    this->virt_walls_joint_damp_dist.setZero();
    this->virt_walls_joint_eta.setZero();
    this->virt_walls_joint_rho_min.setZero();
    this->virt_walls_joint_tau_max.setZero();
    this->virt_walls_joint_walls.setZero();

    this->nullspace_cntr_on=false;
    this->nullspace_cntr_K.setZero();
    this->nullspace_cntr_xi.setZero();
    this->nullspace_cntr_q.setZero();
}

void ConfigController::read_parameters(const nlohmann::json &p){
    cpp_utils::read_json_param<double,6,1>(p,"alpha",alpha);
    cpp_utils::read_json_param<double,6,1>(p,"beta",beta);
    cpp_utils::read_json_param<double,6,1>(p,"gamma_a",gamma_a);
    cpp_utils::read_json_param<double,6,1>(p,"gamma_b",gamma_b);
    cpp_utils::read_json_param<double,6,1>(p,"K_0",K_0);
    cpp_utils::read_json_param<double,6,1>(p,"F_ff_0",F_ff_0);
    cpp_utils::read_json_param<double,6,1>(p,"L",L);
    cpp_utils::read_json_param<double,6,1>(p,"xi",xi);
    cpp_utils::read_json_param<double,6,1>(p,"K_max",K_max);
    cpp_utils::read_json_param<double,6,1>(p,"dK_max",dK_max);
    cpp_utils::read_json_param<double,6,1>(p,"F_ff_max",F_ff_max);
    cpp_utils::read_json_param<double,6,1>(p,"dF_ff_max",dF_ff_max);

    cpp_utils::read_json_param<double,7,1>(p,"K_theta",K_theta);
    cpp_utils::read_json_param<double,7,1>(p,"xi_theta",xi_theta);

    cpp_utils::read_json_param(p,"kappa",kappa);
    cpp_utils::read_json_param(p,"TF_control",TF_control);

    cpp_utils::read_json_param<double,6,1>(p,"f_cntr_k_p",f_cntr_k_p);
    cpp_utils::read_json_param<double,6,1>(p,"f_cntr_k_i",f_cntr_k_i);
    cpp_utils::read_json_param<double,6,1>(p,"f_cntr_k_d",f_cntr_k_d);
    cpp_utils::read_json_param<double,6,1>(p,"f_cntr_k_d_N",f_cntr_k_d_N);
    cpp_utils::read_json_param<double,3,1>(p,"f_cntr_d_max",f_cntr_d_max);
    cpp_utils::read_json_param<double,1,1>(p,"f_cntr_phi_max",f_cntr_phi_max);
    cpp_utils::read_json_param<double,6,1>(p,"F_c_max",F_c_max);
    cpp_utils::read_json_param<double,6,1>(p,"dF_c_max",dF_c_max);
    cpp_utils::read_json_param<double,6,1>(p,"f_cntr_active",f_cntr_active);
    cpp_utils::read_json_param(p,"f_cntr_sf_on",f_cntr_sf_on);

    cpp_utils::read_json_param<double,7,1>(p,"tau_c_max",tau_c_max);
    cpp_utils::read_json_param<double,7,1>(p,"dtau_c_max",dtau_c_max);

    cpp_utils::read_json_param<double,1,1>(p,"virt_cube_damp",virt_cube_damp);
    cpp_utils::read_json_param<double,1,1>(p,"virt_cube_damp_dist",virt_cube_damp_dist);
    cpp_utils::read_json_param<double,1,1>(p,"virt_cube_eta",virt_cube_eta);
    cpp_utils::read_json_param<double,1,1>(p,"virt_cube_rho_min",virt_cube_rho_min);
    cpp_utils::read_json_param<double,6,1>(p,"virt_cube_walls",virt_cube_walls);
    cpp_utils::read_json_param<double,1,1>(p,"virt_cube_f_max",virt_cube_f_max);
    cpp_utils::read_json_param(p,"virt_cube_on",virt_cube_on);

    cpp_utils::read_json_param<double,7,1>(p,"virt_walls_joint_damp",virt_walls_joint_damp);
    cpp_utils::read_json_param<double,7,1>(p,"virt_walls_joint_damp_dist",virt_walls_joint_damp_dist);
    cpp_utils::read_json_param<double,7,1>(p,"virt_walls_joint_eta",virt_walls_joint_eta);
    cpp_utils::read_json_param<double,7,1>(p,"virt_walls_joint_rho_min",virt_walls_joint_rho_min);
    cpp_utils::read_json_param<double,7,1>(p,"virt_walls_joint_tau_max",virt_walls_joint_tau_max);
    cpp_utils::read_json_param<double,14,1>(p,"virt_walls_joint_walls",virt_walls_joint_walls);
    cpp_utils::read_json_param(p,"virt_walls_joint_on",virt_walls_joint_on);

    cpp_utils::read_json_param(p,"nullspace_cntr_on",nullspace_cntr_on);
    cpp_utils::read_json_param<double,7,1>(p,"nullspace_cntr_K",nullspace_cntr_K);
    cpp_utils::read_json_param<double,7,1>(p,"nullspace_cntr_xi",nullspace_cntr_xi);
}

PersistentData::PersistentData(){
    EE_T_TCP=Eigen::Matrix<double,4,4>::Identity();
}

PersistentData* const LocalMemory::get_persistent_data(){
    return &this->_pdata;
}

void LocalMemory::modify_config_cntr(const nlohmann::json& p){
    this->_c_cntr.read_parameters(p);
}

void LocalMemory::modify_config_frames(const nlohmann::json& p){
    this->_c_frames.read_parameters(p);
}

void LocalMemory::modify_config_general(const nlohmann::json& p){
    this->_c_general.read_parameters(p);
}

void LocalMemory::modify_config_user(const nlohmann::json& p){
    this->_c_user.read_parameters(p);
}

void LocalMemory::modify_hidden_config_user(const nlohmann::json& p){
    this->_c_user.read_hidden_parameters(p);
}

void LocalMemory::modify_config_system(const nlohmann::json& p){
    this->_c_system.read_parameters(p);
}

void LocalMemory::upload_config_cntr(const ConfigController &c){
    this->_c_cntr=c;
}

void LocalMemory::upload_config_frames(const ConfigFrames &c){
    this->_c_frames=c;
}

void LocalMemory::upload_config_general(const ConfigGeneral &c){
    this->_c_general=c;
}

void LocalMemory::upload_config_user(const ConfigUser &c){
    this->_c_user=c;
}

void LocalMemory::upload_config_system(const ConfigSystem &c){
    this->_c_system=c;
}

const ConfigController &LocalMemory::access_config_cntr(){
    return this->_c_cntr;
}

const ConfigFrames& LocalMemory::access_config_frames(){
    return this->_c_frames;
}

const ConfigGeneral& LocalMemory::access_config_general(){
    return this->_c_general;
}

const ConfigUser& LocalMemory::access_config_user(){
    return this->_c_user;
}

const ConfigLimits& LocalMemory::access_config_limits(){
    return this->_c_limits;
}

const ConfigSystem& LocalMemory::access_config_system(){
    return this->_c_system;
}

}
