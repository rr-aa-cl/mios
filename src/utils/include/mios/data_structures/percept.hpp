#pragma once

#include "franka/robot_state.h"
#include "franka/gripper_state.h"
#include "franka/model.h"
#include "eigen3/Eigen/Core"

#include <chrono>
#include <memory>

namespace mios {

enum HandActivityState{hsIdle,hsBusy,hsFinished};

class Percept{
public:
    Percept();
    void update(std::unique_ptr<franka::Model> const& model, const franka::RobotState& robot_state, const franka::GripperState &gripper_state, std::optional<Eigen::Matrix<double,3,3> > O_R_T);
    void update_controller();

    struct Proprioception{

        /**
     * End effector pose in origin frame (O).
     */
        Eigen::Matrix<double,4,4> O_T_EE;

        /**
     * End effector pose in task frame (TF).
     */
        Eigen::Matrix<double,4,4> T_T_EE;

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
        Eigen::Matrix<double,6,1> O_dX_EE;

        /**
     * Cartesian twist in end effector frame (EE).
     */
        Eigen::Matrix<double,6,1> EE_dX_EE;

        /**
     * Cartesian twist in task frame (TF).
     */
        Eigen::Matrix<double,6,1> TF_dX_EE;

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
        Eigen::Matrix<double,6,1> K_F_ext_K;

        /**
     * Derivative of estimated external wrench at TCP in stiffness frame (K).
     */
        Eigen::Matrix<double,6,1> K_dF_ext_K;

        /**
     * Estimated external wrench at TCP in origin frame (O).
     */
        Eigen::Matrix<double,6,1> O_F_ext_K;

        /**
     * Derivative of estimated external wrench at TCP in origin frame (O).
     */
        Eigen::Matrix<double,6,1> O_dF_ext_K;

        /**
     * Estimated external wrench at TCP in task frame (TF).
     */
        Eigen::Matrix<double,6,1> TF_F_ext_K;

        /**
     * Derivative of estimated external wrench at TCP in task frame (TF).
     */
        Eigen::Matrix<double,6,1> TF_dF_ext_K;

        double finger_width;
        double finger_temperature;
        bool is_grasping;

    }proprioception;

    struct InternalModel{


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

        double max_finger_width;
        HandActivityState hand_activity_state;

    }internal_model;

    struct Controller{

        /**
     * Rho factor from force controllers's shaping function.
     */

        Eigen::Matrix<double,6,1> e;
        Eigen::Matrix<double,6,1> rho;

        Eigen::Matrix<double,6,1> K_x;
        Eigen::Matrix<double,6,1> xi_x;
        Eigen::Matrix<double,7,1> K_theta;
        Eigen::Matrix<double,7,1> xi_theta;

        Eigen::Matrix<double,4,4> TF_T_EE_d;
        Eigen::Matrix<double,6,1> TF_dX_d;
        Eigen::Matrix<double,6,1> TF_F_ff;
        Eigen::Matrix<double,3,3> O_R_T;

        Eigen::Matrix<double,7,1> q_d;
        Eigen::Matrix<double,7,1> dq_d;
        Eigen::Matrix<double,7,1> tau_ff;
    }controller;
    franka::RobotMode robot_mode;
    std::chrono::high_resolution_clock::time_point time;
};

}
