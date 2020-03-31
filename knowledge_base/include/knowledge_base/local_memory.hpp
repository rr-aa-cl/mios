#pragma once


#include <eigen3/Eigen/Core>

#include <franka/robot.h>

#include "cpp_utils/json.hpp"


namespace mios {

class ParameterServer;

struct MiosState{
    MiosState();

    std::string active_task;
    std::string active_skill;
    std::string grasped_object;
};

/**
 * The percept struct. This is an abstraction from franka::RobotState.
 */
struct Percept{

    Percept();

    void set_0();

    /**
     * End effector pose in origin frame (O).
     */
    Eigen::Matrix<double,4,4> O_T_EE;

    /**
     * End effector pose in task frame (TF).
     */
    Eigen::Matrix<double,4,4> TF_T_EE;

    /**
     * Link-side joint pose.
     */
    Eigen::Matrix<double,7,1> q;

    /**
     * Link-side joint velocities.
     */
    Eigen::Matrix<double,7,1> dq;

    /**
     * Motor-side joint pose.
     */
    Eigen::Matrix<double,7,1> theta;

    /**
     * Motor-side joint velocities.
     */
    Eigen::Matrix<double,7,1> dtheta;

    /**
     * Cartesian twist in origin frame (O).
     */
    Eigen::Matrix<double,6,1> O_dX;

    /**
     * Cartesian twist in task frame (TF).
     */
    Eigen::Matrix<double,6,1> TF_dX;

    /**
     * Estimated external torques.
     */
    Eigen::Matrix<double,7,1> tau_ext;

    /**
     * Joint torques.
     */
    Eigen::Matrix<double,7,1> tau_j;

    /**
     * Estimated external wrench at TCP in stiffness frame (K).
     */
    Eigen::Matrix<double,6,1> K_F_ext;

    /**
     * Derivative of estimated external wrench at TCP in stiffness frame (K).
     */
    Eigen::Matrix<double,6,1> K_dF_ext;

    /**
     * Estimated external wrench at TCP in origin frame (O).
     */
    Eigen::Matrix<double,6,1> O_F_ext;

    /**
     * Derivative of estimated external wrench at TCP in origin frame (O).
     */
    Eigen::Matrix<double,6,1> O_dF_ext;

    /**
     * Estimated external wrench at TCP in task frame (TF).
     */
    Eigen::Matrix<double,6,1> TF_F_ext;

    /**
     * Derivative of estimated external wrench at TCP in task frame (TF).
     */
    Eigen::Matrix<double,6,1> TF_dF_ext;

    /**
     * Mass matrix.
     */
    Eigen::Matrix<double,7,7> M;

    /**
     * Coriolis vector.
     */
    Eigen::Matrix<double,7,1> C;

    /**
     * Gravity vector.
     */
    Eigen::Matrix<double,7,1> G;

    /**
     * Body jacobian.
     */
    Eigen::Matrix<double,6,7> B_J_EE;

    /**
     * Zero jacobian.
     */
    Eigen::Matrix<double,6,7> B_J_O;

    /**
     * Rho factor from force controllers's shaping function.
     */

    Eigen::Matrix<double,6,1> e;
    Eigen::Matrix<double,6,1> rho;

    Eigen::Matrix<double,6,1> K_x;
    Eigen::Matrix<double,6,1> xi_x;
    Eigen::Matrix<double,7,1> K_theta;
    Eigen::Matrix<double,7,1> xi_theta;

    double gripper_width;
    bool is_grasping;

    franka::RobotMode robot_mode;

    double time;

    Eigen::Matrix<double,4,4> TF_T_EE_d;
    Eigen::Matrix<double,6,1> TF_dX_d;
    Eigen::Matrix<double,6,1> TF_F_ff;

    Eigen::Matrix<double,7,1> q_d;
    Eigen::Matrix<double,7,1> dq_d;
    Eigen::Matrix<double,7,1> tau_ff;

    std::shared_ptr<ParameterServer> live_params;
    MiosState mios_state;

};

struct ConfigLimits{
    ConfigLimits();

    Eigen::Matrix<double,7,1> q_upper;
    Eigen::Matrix<double,7,1> q_lower;
    Eigen::Matrix<double,7,1> dq_max;
    Eigen::Matrix<double,7,1> ddq_max;
    Eigen::Matrix<double,7,1> dddq_max;
    Eigen::Matrix<double,7,1> tau_J_max;
    Eigen::Matrix<double,7,1> dtau_J_max;

    Eigen::Matrix<double,7,1> K_theta_max;
    Eigen::Matrix<double,7,1> dK_theta_max;
    Eigen::Matrix<double,7,1> xi_theta_max;
    Eigen::Matrix<double,7,1> dxi_theta_max;

    Eigen::Matrix<double,7,1> tau_ext_max;

    Eigen::Matrix<double,3,1> x_upper;
    Eigen::Matrix<double,3,1> x_lower;
    Eigen::Matrix<double,2,1> dX_max;
    Eigen::Matrix<double,2,1> ddX_max;
    Eigen::Matrix<double,2,1> dddX_max;
    Eigen::Matrix<double,2,1> F_ext_max;

    Eigen::Matrix<double,2,1> F_J_max;
    Eigen::Matrix<double,2,1> dF_J_max;

    Eigen::Matrix<double,6,1> K_x_max;
    Eigen::Matrix<double,6,1> dK_x_max;
    Eigen::Matrix<double,6,1> xi_x_max;
    Eigen::Matrix<double,6,1> dxi_x_max;

};

struct ConfigUser{
    ConfigUser();

    void read_parameters(const nlohmann::json& p);
    void read_hidden_parameters(const nlohmann::json& p);

    Eigen::Matrix<double,2,1> neighborhood_X;
    Eigen::Matrix<double,2,1> neighborhood_dX;
    Eigen::Matrix<double,2,1> neighborhood_F;
    Eigen::Matrix<double,2,1> neighborhood_dF;
    Eigen::Matrix<double,1,1> neighborhood_q;
    Eigen::Matrix<double,1,1> neighborhood_dq;

    Eigen::Matrix<double,6,1> x_limits;
    Eigen::Matrix<double,6,1> phi_limits;

    Eigen::Matrix<double,2,1> dX_max;
    Eigen::Matrix<double,2,1> ddX_max;
    Eigen::Matrix<double,1,1> dq_max;
    Eigen::Matrix<double,1,1> ddq_max;

    Eigen::Matrix<double,6,1> F_contact;
    Eigen::Matrix<double,7,1> tau_contact;

    Eigen::Matrix<double,6,1> F_max;
    Eigen::Matrix<double,7,1> tau_max;

    Eigen::Matrix<double,2,1> e_x_max;
    Eigen::Matrix<double,1,1> e_q_max;

    double load_m;
    Eigen::Matrix<double,3,1> load_com;
    Eigen::Matrix<double,3,3> load_I;

    std::string grasped_object;
};

struct ConfigFrames{
    ConfigFrames();

    void read_parameters(const nlohmann::json& p);

    Eigen::Matrix<double,3,3> O_R_TF;
    Eigen::Matrix<double,4,4> F_T_EE;
    Eigen::Matrix<double,4,4> EE_T_TCP;
    Eigen::Matrix<double,4,4> EE_T_K;
    Eigen::Matrix<double,4,4> EE_T_C;
    Eigen::Matrix<double,4,4> D_T_O;
};

struct ConfigGeneral{
    ConfigGeneral();

    void read_parameters(const nlohmann::json& p);

    bool safe_mode;
    bool instant_recovery;
    bool logging;
    unsigned control_mode;
    unsigned command_mode;
};

struct ConfigSystem{
    ConfigSystem();

    void read_parameters(const nlohmann::json& p);

    std::string ip_robot;
    std::string id_robot;
    std::string desk_name;
    std::string desk_pwd;
    std::string ip_simulation;

    std::string location;

    unsigned port_simulation;

    bool telemetry_on;

    std::string telemetry_udp_ip;
    unsigned telemetry_udp_port;
    unsigned telemetry_udp_frequency;

    std::string path_executable;

    unsigned verbosity;

    bool has_robot;
    bool has_gripper;
    bool has_simulation;
    bool has_sound;
    bool has_led;
};

struct ConfigController{
    ConfigController();
    void read_parameters(const nlohmann::json& p);

    Eigen::Matrix<double,6,1> alpha;
    Eigen::Matrix<double,6,1> beta;
    Eigen::Matrix<double,6,1> gamma_a;
    Eigen::Matrix<double,6,1> gamma_b;
    Eigen::Matrix<double,6,1> K_0;
    Eigen::Matrix<double,6,1> F_ff_0;
    Eigen::Matrix<double,6,1> L;
    Eigen::Matrix<double,6,1> xi;
    Eigen::Matrix<double,6,1> K_max;
    Eigen::Matrix<double,6,1> dK_max;
    Eigen::Matrix<double,6,1> F_ff_max;
    Eigen::Matrix<double,6,1> dF_ff_max;

    Eigen::Matrix<double,7,1> K_theta;
    Eigen::Matrix<double,7,1> xi_theta;

    double kappa;
    bool TF_control;

    Eigen::Matrix<double,6,1> f_cntr_k_p;
    Eigen::Matrix<double,6,1> f_cntr_k_i;
    Eigen::Matrix<double,6,1> f_cntr_k_d;
    Eigen::Matrix<double,6,1> f_cntr_k_d_N;
    Eigen::Matrix<double,3,1> f_cntr_d_max;
    Eigen::Matrix<double,1,1> f_cntr_phi_max;
    Eigen::Matrix<double,6,1> F_c_max;
    Eigen::Matrix<double,6,1> dF_c_max;
    Eigen::Matrix<double,6,1> f_cntr_active;

    bool f_cntr_sf_on;

    Eigen::Matrix<double,7,1> tau_c_max;
    Eigen::Matrix<double,7,1> dtau_c_max;

    Eigen::Matrix<double,1,1> virt_cube_damp;
    Eigen::Matrix<double,1,1> virt_cube_damp_dist;
    Eigen::Matrix<double,1,1> virt_cube_eta;
    Eigen::Matrix<double,1,1> virt_cube_rho_min;
    Eigen::Matrix<double,6,1> virt_cube_walls;
    Eigen::Matrix<double,1,1> virt_cube_f_max;

    bool virt_cube_on;

    Eigen::Matrix<double,7,1> virt_walls_joint_damp;
    Eigen::Matrix<double,7,1> virt_walls_joint_damp_dist;
    Eigen::Matrix<double,7,1> virt_walls_joint_eta;
    Eigen::Matrix<double,7,1> virt_walls_joint_rho_min;
    Eigen::Matrix<double,7,1> virt_walls_joint_tau_max;
    Eigen::Matrix<double,14,1> virt_walls_joint_walls;

    bool virt_walls_joint_on;

    bool nullspace_cntr_on;
    Eigen::Matrix<double,7,1> nullspace_cntr_K;
    Eigen::Matrix<double,7,1> nullspace_cntr_xi;

    Eigen::Matrix<double,7,1> nullspace_cntr_q;

};

struct PersistentData{
    PersistentData();

    Eigen::Matrix<double,4,4> EE_T_TCP;
};

class LocalMemory{
public:
    PersistentData* const get_persistent_data();

    void modify_config_cntr(const nlohmann::json& p);
    void upload_config_cntr(const ConfigController& c);
    void modify_config_frames(const nlohmann::json& p);
    void upload_config_frames(const ConfigFrames& c);
    void modify_config_general(const nlohmann::json& p);
    void upload_config_general(const ConfigGeneral& c);
    void modify_config_user(const nlohmann::json& p);
    void modify_hidden_config_user(const nlohmann::json& p);
    void upload_config_user(const ConfigUser& c);
    void modify_config_limits(const nlohmann::json& p);
    void upload_config_limits(const ConfigLimits& c);
    void modify_config_system(const nlohmann::json& p);
    void upload_config_system(const ConfigSystem& c);

    const ConfigController& access_config_cntr();
    const ConfigFrames& access_config_frames();
    const ConfigGeneral& access_config_general();
    const ConfigUser& access_config_user();
    const ConfigLimits& access_config_limits();
    const ConfigSystem& access_config_system();

private:

    ConfigController _c_cntr;
    ConfigFrames _c_frames;
    ConfigGeneral _c_general;
    ConfigUser _c_user;
    ConfigLimits _c_limits;
    ConfigSystem _c_system;

    PersistentData _pdata;

};

}
