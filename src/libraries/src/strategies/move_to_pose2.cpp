#include "mios/strategies/move_to_pose2.hpp"
#include "mirmi_cpp_utils/math/math.hpp"
#include <iostream>
#include <cmath>

namespace mios{

MoveToPoseStrategy2::MoveToPoseStrategy2():PrimitiveStrategy({CommandPatternCartesianPose}){ //maybe use caretan position here

}

void MoveToPoseStrategy2::initialize(const Percept &p_0){
    m_T_EE_0=p_0.controller.TF_T_EE_d;
    m_q_0 = m_T_EE_0.block<3,3>(0,0);
    m_q_d = m_T_EE_d.block<3,3>(0,0);
    m_wiggle = false;

    
}

void MoveToPoseStrategy2::get_next_command(Actuator &cmd, [[maybe_unused]] const Percept &p){
    m_t++;
    m_s = m_a*pow(m_t/1000*m_t_d,3)+m_b*pow(m_t/1000*m_t_d,2); 
    if(m_s<0){
        m_s=0;
    }
    if(m_s>1){
        m_s=1;
    }
    m_q_t = m_q_0.slerp(m_s,m_q_d);

    if(m_wiggle){
        for(unsigned i=0;i<6;i++){
            m_deltaPose(i)=m_deltaPose_a(i)* (sin(2*M_PI*m_deltaPose_f(i)*m_t+m_deltaPose_phi(i)) - sin(m_deltaPose_phi(i)));
        }
        m_deltaPose.block<3,1>(0,0) = m_T_EE_d.block<3,3>(0,0) * m_deltaPose.block<3,1>(0,0);
        m_deltaPose.block<3,1>(3,0) = m_T_EE_d.block<3,3>(0,0) * m_deltaPose.block<3,1>(3,0);
        m_R_delta = mirmi_utils::eulerZYX_to_mat(m_deltaPose(5),m_deltaPose(4),m_deltaPose(3));
        m_q_delta = m_R_delta;
        m_q_t = m_q_delta * m_q_t;

            /*
                deltaPose[0:3]=np.matmul(self.TGoal[0:3,0:3],deltaPose[0:3])
                deltaPose[3:6]=np.matmul(self.TGoal[0:3,0:3],deltaPose[3:6])

                rR=R.from_euler('zyx',[deltaPose[5], deltaPose[4],deltaPose[3]])

                qDelta=Quaternion(matrix=rR.as_matrix())
                
                qD=qDelta*qD

               cmd.TF_T_EE_d.block<3,1>(0,3) = cmd.TF_T_EE_d.block<3,1>(0,3) + m_deltaPose.block<3,1>(0,0)
            */
    }
    m_q_t.normalize();
    cmd.TF_T_EE_d.block<3,3>(0,0) = m_q_t.toRotationMatrix();
    for(unsigned i=0;i<3;i++){
        cmd.TF_T_EE_d.block<1,1>(i,3) = m_T_EE_0.block<1,1>(i,3)*(1-m_s) + m_T_EE_d.block<1,1>(i,3)*m_s;
    }



}

void MoveToPoseStrategy2::terminate([[maybe_unused]] const Percept &p){

}

bool MoveToPoseStrategy2::finished(){
    return m_t>=m_t_d;
}

void MoveToPoseStrategy2::set_goal(const Eigen::Matrix<double, 4, 4> &T_EE_d, double T_d){
    m_T_EE_d=T_EE_d;
    m_t_d = T_d;
}

void MoveToPoseStrategy2::set_scale(double t_scale){
    m_t_d=t_scale;
}

void MoveToPoseStrategy2::set_wiggle_coefficients(Eigen::Matrix<double, 6, 1> offset_a, Eigen::Matrix<double, 6, 1> offset_f, Eigen::Matrix<double, 6, 1> offset_phi){
    m_wiggle=true;
    m_deltaPose_a = offset_a;
    m_deltaPose_f = offset_f;
    m_deltaPose_phi = offset_phi;
}
}
