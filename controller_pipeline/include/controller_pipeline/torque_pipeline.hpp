#pragma once

#include "controller_pipeline/controller_pipeline.hpp"

#include "plugins/cntr_aic_wrapper.hpp"
#include "plugins/cntr_force_wrapper.hpp"
#include "plugins/cntr_joint_var_imp_wrapper.hpp"
#include "plugins/cntr_mux_wrapper.hpp"
#include "plugins/conv_vel2pose_wrapper.hpp"
#include "plugins/virtual_cube_wrapper.hpp"
#include "plugins/virtual_walls_joint_wrapper.hpp"
#include "plugins/cntr_nullsp_proj_wrapper.hpp"

namespace mios {

class CartTorqueControllerPipeline : public ControllerPipeline{
public:
    void initialize(const Percept& p_0,KnowledgeBase* kb);
    franka::Finishable step(const Percept &p, const Actuator &cmd);
    void terminate();

public:
    void set_virtual_cube(bool on);
    void set_virtual_joint_walls(bool on);
    void set_nullspace_control(bool on);

private:
    void initialize_cntr_aic(const Percept &p,KnowledgeBase* kb);
    void initialize_cntr_force(const Percept &p,KnowledgeBase* kb);
    void initialize_cntr_mux(const Percept &p, KnowledgeBase *kb);
    void initialize_virt_cube(const Percept &p, KnowledgeBase *kb);
    void initialize_virt_walls_joint(const Percept &p, KnowledgeBase *kb);
    void initialize_cntr_nullsp(const Percept &p,KnowledgeBase* kb);

    void input_cntr_aic(const Percept& p);
    void input_cntr_force(const Percept& p);
    void input_cntr_mux(const Percept& p);
    void input_virt_cube(const Percept& p);
    void input_virt_joint_walls(const Percept& p);
    void input_cntr_nullsp(const Percept& p);

private:
    bool is_virt_cube_valid(const Percept &p);
    bool is_virt_joint_walls_valid(const Percept &p);

private:
    bool m_virtual_cube_on;
    bool m_virtual_joint_walls_on;
    bool m_nullspace_control_on;

    Eigen::Matrix<double,6,1> m_virt_cube_distances;
    Eigen::Matrix<double,14,1> m_virt_joint_walls_distances;

private:
    cntr_aic::cntr_aic m_cntr_aic;
    cntr_force::cntr_force m_cntr_force;
    cntr_mux::cntr_mux m_cntr_mux;
    conv_vel2pose::conv_vel2pose m_conv_vel2pose;
    virtual_cube::virtual_cube m_virt_cube;
    virtual_walls_joint::virtual_walls_joint m_virt_walls_joint;
    cntr_joint_var_imp::cntr_joint_var_imp m_cntr_nullsp_q;
    cntr_nullsp_proj::cntr_nullsp_proj m_cntr_nullsp_proj;

    cntr_aic::In_U_cntr_aic m_in_u_aic;
    cntr_force::In_U_cntr_force m_in_u_force;
    cntr_mux::In_U_cntr_mux m_in_u_mux;
    conv_vel2pose::In_U_conv_vel2pose m_in_u_vel2pose;
    virtual_cube::In_U_virtual_cube m_in_u_virt_cube;
    virtual_walls_joint::In_U_virtual_walls_joint m_in_u_virt_walls_joint;
    cntr_joint_var_imp::In_U_cntr_joint_var_imp m_in_u_cntr_nullsp_q;
    cntr_nullsp_proj::In_U_cntr_nullsp_proj m_in_u_cntr_nullsp_proj;

    cntr_aic::Out_Y_cntr_aic m_out_y_aic;
    cntr_force::Out_Y_cntr_force m_out_y_force;
    cntr_mux::Out_Y_cntr_mux m_out_y_mux;
    conv_vel2pose::Out_Y_conv_vel2pose m_out_y_vel2pose;
    virtual_cube::Out_Y_virtual_cube m_out_y_virt_cube;
    virtual_walls_joint::Out_Y_virtual_walls_joint m_out_y_virt_walls_joint;
    cntr_joint_var_imp::Out_Y_cntr_joint_var_imp m_out_y_cntr_nullsp_q;
    cntr_nullsp_proj::Out_Y_cntr_nullsp_proj m_out_y_cntr_nullsp_proj;
};

}
