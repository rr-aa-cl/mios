#pragma once

#include <memory>
#include <nlohmann/json.hpp>
#include <eigen3/Eigen/Core>


namespace mios {

class Object;

enum CommandMode{None,Torque,CartesianVelocity,JointVelocity,CartesianPose,JointPose};

class LimitParameters{
    LimitParameters();

    bool read_parameters(const nlohmann::json& parameters);
    static nlohmann::json get_default_values();

    struct{
        Eigen::Matrix<double,7,1> q_upper;
        Eigen::Matrix<double,7,1> q_lower;
        Eigen::Matrix<double,7,1> dq_max;
        Eigen::Matrix<double,7,1> ddq_max;
        Eigen::Matrix<double,7,1> dddq_max;
        Eigen::Matrix<double,7,1> tau_J_max;
        Eigen::Matrix<double,7,1> dtau_J_max;
        Eigen::Matrix<double,7,1> tau_ext_max;

        Eigen::Matrix<double,7,1> K_theta_max;
        Eigen::Matrix<double,7,1> dK_theta_max;
        Eigen::Matrix<double,7,1> xi_theta_max;
        Eigen::Matrix<double,7,1> dxi_theta_max;
    }joint_space;
    struct{
        Eigen::Matrix<double,3,1> x_upper;
        Eigen::Matrix<double,3,1> x_lower;
        Eigen::Matrix<double,2,1> dX_max;
        Eigen::Matrix<double,2,1> ddX_max;
        Eigen::Matrix<double,2,1> dddX_max;
        Eigen::Matrix<double,6,1> F_ext_max;

        Eigen::Matrix<double,2,1> F_J_max;
        Eigen::Matrix<double,2,1> dF_J_max;

        Eigen::Matrix<double,6,1> K_x_max;
        Eigen::Matrix<double,6,1> dK_x_max;
        Eigen::Matrix<double,6,1> xi_x_max;
        Eigen::Matrix<double,6,1> dxi_x_max;
    }cartesian_space;
};

class UserParameters{
    UserParameters();

    bool read_parameters(const nlohmann::json& parameters);
    static nlohmann::json get_default_values();

    Eigen::Matrix<double,2,1> dX_max;
    Eigen::Matrix<double,2,1> ddX_max;
    Eigen::Matrix<double,7,1> dq_max;
    Eigen::Matrix<double,7,1> ddq_max;

    Eigen::Matrix<double,2,1> F_ext_contact;
    Eigen::Matrix<double,7,1> tau_ext_contact;

    Eigen::Matrix<double,2,1> F_ext_max;
    Eigen::Matrix<double,7,1> tau_ext_max;

    double load_m;
    Eigen::Matrix<double,3,1> load_com;
    Eigen::Matrix<double,3,3> load_I;

    bool safe_mode;

};

struct FramesParameters{
    FramesParameters();

    bool read_parameters(const nlohmann::json& parameters);
    static nlohmann::json get_default_values();

    Eigen::Matrix<double,3,3> O_R_T;
    Eigen::Matrix<double,4,4> F_T_EE;
    Eigen::Matrix<double,4,4> EE_T_TCP;
    Eigen::Matrix<double,4,4> EE_T_K;
};

struct GeneralParameters{
    GeneralParameters();

    bool read_parameters(const nlohmann::json& parameters);
    static nlohmann::json get_default_values();

    bool safe_mode;
    bool instant_recovery;
    unsigned control_mode;
    unsigned command_mode;
};

struct SystemParameters{
    SystemParameters();

    bool read_parameters(const nlohmann::json& parameters);
    static nlohmann::json get_default_values();

    std::string robot_ip;
    std::string desk_name;
    std::string desk_pwd;


    bool has_robot;
    bool has_gripper;
};

enum ControlMode{mCartTorque,mJointTorque,mCartVelocity,mJointVelocity};

class ControlParameters{
    ControlParameters();
    bool read_parameters(const nlohmann::json& parameters);
    static nlohmann::json get_default_values();

    ControlMode control_mode;

    struct CartImpAdaptationStage{
        Eigen::Matrix<double,6,1> alpha;
        Eigen::Matrix<double,6,1> beta;
        Eigen::Matrix<double,6,1> gamma_a;
        Eigen::Matrix<double,6,1> gamma_b;
        Eigen::Matrix<double,6,1> L;
        Eigen::Matrix<double,6,1> F_ff_0;
        double kappa;
    }cart_imp_adaptation_stage;

    struct CartImp{
        Eigen::Matrix<double,6,1> K_x;
        Eigen::Matrix<double,6,1> xi;
    }cart_imp;

    struct JointImp{
        Eigen::Matrix<double,7,1> K_theta;
        Eigen::Matrix<double,7,1> xi_theta;
    }joint_imp;

    struct ForceControl{
        Eigen::Matrix<double,6,1> k_p;
        Eigen::Matrix<double,6,1> k_i;
        Eigen::Matrix<double,6,1> k_d;
        Eigen::Matrix<double,6,1> k_d_N;
        Eigen::Matrix<double,3,1> d_max;
        Eigen::Matrix<double,1,1> phi_max;
        Eigen::Matrix<double,6,1> active;
        bool sf_on;
    }force_control;

    struct VirtualCube{
        Eigen::Matrix<double,1,1> damping;
        Eigen::Matrix<double,1,1> damping_dist;
        Eigen::Matrix<double,1,1> eta;
        Eigen::Matrix<double,1,1> rho_min;
        Eigen::Matrix<double,6,1> walls;
        Eigen::Matrix<double,1,1> f_max;
        bool active;
    }virtual_cube;

    struct VirtualJointWalls{
        Eigen::Matrix<double,7,1> damping;
        Eigen::Matrix<double,7,1> damping_dist;
        Eigen::Matrix<double,7,1> eta;
        Eigen::Matrix<double,7,1> rho_min;
        Eigen::Matrix<double,7,1> tau_max;
        Eigen::Matrix<double,14,1> walls;
        bool active;
    }virtual_joint_walls;

    struct NullSpaceControl{
        Eigen::Matrix<double,7,1> K_theta;
        Eigen::Matrix<double,7,1> xi_theta;
        Eigen::Matrix<double,7,1> q_d;
        bool active;
    }nullspace_control;
};

class SkillParameters{
public:
    SkillParameters();

    /**
     * Reads common skill parameters into the local configuration struct.
     * @param[in] p Common skill parameters in json format.
     */
    void read_global_skill_parameters(const nlohmann::json& p);
    void read_skill_objects(const nlohmann::json& p);
    virtual bool read_parameters(const nlohmann::json& parameters) = 0;

    struct Common{
        /**
         * Mapping of skill objects to objects in the knowledge base.
         */
        std::unordered_map<std::string,std::string> objects;

        /**
         * Maximum time for skill execution. After exceeding this time the skill is terminated unsuccessful. A value of 0 allows for infinite execution time.
         */
        double time_max;

        /**
         * Id to select a custom cost function.
         */
        std::vector<double> w_cost_function;

        /**
         * Frequency of parallel thread
         */
        unsigned parallels_frequency;

    }common;
};

class Parameters{
public:
    Parameters();
    ControlParameters control;
    SystemParameters system;
    LimitParameters limits;
    UserParameters user;
    FramesParameters frames;
    std::unique_ptr<SkillParameters> skill;

    template<typename T>void create_skill_parameters(){
        skill = std::make_unique<T>();
    }
};

class LiveContext{
public:
    LiveContext();
    std::string executable_path;
    nlohmann::json live_parameters;
    Object* grasped_object;
};

}
