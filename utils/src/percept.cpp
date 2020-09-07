#include "data_structures/percept.hpp"
#include <msrm_utils/math.hpp>

namespace mios {

void Percept::update(std::unique_ptr<franka::Model> const& model, const franka::RobotState &robot_state, const franka::GripperState &gripper_state,std::optional<Eigen::Matrix<double,3,3> > O_R_T){

    // Internal Model
    if(model!=nullptr){
        internal_model.B_J_EE=Eigen::Matrix<double,6,7>(model->bodyJacobian(franka::Frame::kEndEffector,robot_state).data());
        internal_model.B_J_O=Eigen::Matrix<double,6,7>(model->zeroJacobian(franka::Frame::kEndEffector,robot_state).data());
        internal_model.M=Eigen::Matrix<double,7,7>(model->mass(robot_state).data());
        internal_model.C=Eigen::Matrix<double,7,1>(model->coriolis(robot_state).data());
        internal_model.G=Eigen::Matrix<double,7,1>(model->gravity(robot_state).data());
    }
    internal_model.max_finger_width=gripper_state.max_width;

    // proprioception
    proprioception.q=Eigen::Matrix<double,7,1>(robot_state.q.data());
    proprioception.dq=Eigen::Matrix<double,7,1>(robot_state.dq.data());
    proprioception.theta=Eigen::Matrix<double,7,1>(robot_state.theta.data());
    proprioception.dtheta=Eigen::Matrix<double,7,1>(robot_state.dtheta.data());

    proprioception.tau_j=Eigen::Matrix<double,7,1>(robot_state.tau_J.data());
    proprioception.tau_ext=Eigen::Matrix<double,7,1>(robot_state.tau_ext_hat_filtered.data());

    proprioception.O_dX_EE=internal_model.B_J_O*proprioception.dq;
    proprioception.EE_dX_EE=internal_model.B_J_EE*proprioception.dq;
    proprioception.O_T_EE=Eigen::Matrix<double,4,4>(robot_state.O_T_EE.data());

    proprioception.O_F_ext_K=Eigen::Matrix<double,6,1>(robot_state.O_F_ext_hat_K.data());
    proprioception.K_F_ext_K=Eigen::Matrix<double,6,1>(robot_state.K_F_ext_hat_K.data());

    Eigen::Matrix<double,3,3> O_R_T_id = Eigen::Matrix<double,3,3>::Identity();
    proprioception.T_T_EE=msrm_utils::rotate_matrix(proprioception.O_T_EE,O_R_T.value_or(O_R_T_id).transpose());
    proprioception.TF_F_ext_K=msrm_utils::rotate_vector(proprioception.O_F_ext_K,O_R_T.value_or(O_R_T_id).transpose());
    proprioception.TF_dX_EE=msrm_utils::rotate_vector(proprioception.O_dX_EE,O_R_T.value_or(O_R_T_id).transpose());

    proprioception.finger_width=gripper_state.width;
    proprioception.finger_temperature=gripper_state.temperature;
    proprioception.is_grasping=gripper_state.is_grasped;

    // Others
    robot_mode=robot_state.robot_mode;
    time = std::chrono::high_resolution_clock::now();

    controller.O_R_T=O_R_T.value_or(O_R_T_id);
}

void Percept::update_controller(){
    controller.q_d=proprioception.q;
    controller.TF_T_EE_d=proprioception.T_T_EE;
}

}
