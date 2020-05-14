#include "utils/percept.hpp"
#include <msrm_utils/math.hpp>

namespace mios {

void Percept::update(std::unique_ptr<franka::Model> const& model, const franka::RobotState &robot_state, const franka::GripperState &gripper_state,std::optional<Eigen::Matrix<double,3,3> > O_R_TF){

    // Internal Model
    InternalModel.B_J_EE=Eigen::Matrix<double,6,7>(model->bodyJacobian(franka::Frame::kEndEffector,robot_state).data());
    InternalModel.B_J_O=Eigen::Matrix<double,6,7>(model->zeroJacobian(franka::Frame::kEndEffector,robot_state).data());
    InternalModel.M=Eigen::Matrix<double,7,7>(model->mass(robot_state).data());
    InternalModel.C=Eigen::Matrix<double,7,1>(model->coriolis(robot_state).data());
    InternalModel.G=Eigen::Matrix<double,7,1>(model->gravity(robot_state).data());
    InternalModel.max_finger_width=gripper_state.max_width;

    // Proprioception
    Proprioception.q=Eigen::Matrix<double,7,1>(robot_state.q.data());
    Proprioception.dq=Eigen::Matrix<double,7,1>(robot_state.dq.data());
    Proprioception.theta=Eigen::Matrix<double,7,1>(robot_state.theta.data());
    Proprioception.dtheta=Eigen::Matrix<double,7,1>(robot_state.dtheta.data());

    Proprioception.tau_j=Eigen::Matrix<double,7,1>(robot_state.tau_J.data());
    Proprioception.tau_ext=Eigen::Matrix<double,7,1>(robot_state.tau_ext_hat_filtered.data());

    Proprioception.O_dX_EE=InternalModel.B_J_O*Proprioception.dq;
    Proprioception.EE_dX_EE=InternalModel.B_J_EE*Proprioception.dq;
    Proprioception.O_T_EE=Eigen::Matrix<double,4,4>(robot_state.O_T_EE.data());

    Proprioception.O_F_ext_K=Eigen::Matrix<double,6,1>(robot_state.O_F_ext_hat_K.data());
    Proprioception.K_F_ext_K=Eigen::Matrix<double,6,1>(robot_state.K_F_ext_hat_K.data());

    Eigen::Matrix<double,3,3> O_R_TF_id = Eigen::Matrix<double,3,3>::Identity();
    Proprioception.TF_T_EE=msrm_utils::rotate_matrix(Proprioception.O_T_EE,O_R_TF.value_or(O_R_TF_id).transpose());
    Proprioception.TF_F_ext_K=msrm_utils::rotate_vector(Proprioception.O_F_ext_K,O_R_TF.value_or(O_R_TF_id).transpose());
    Proprioception.TF_dX_EE=msrm_utils::rotate_vector(Proprioception.O_dX_EE,O_R_TF.value_or(O_R_TF_id).transpose());

    Proprioception.finger_width=gripper_state.width;
    Proprioception.finger_temperature=gripper_state.temperature;

    // Others
    robot_mode=robot_state.robot_mode;
    time = std::chrono::high_resolution_clock::now();


}

}
