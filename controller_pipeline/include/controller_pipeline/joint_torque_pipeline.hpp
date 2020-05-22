#pragma once

#include "controller_pipeline/controller_pipeline.hpp"

#include "plugins/cntr_joint_var_imp_wrapper.hpp"
#include "plugins/cntr_mux_wrapper.hpp"
#include "plugins/virtual_cube_wrapper.hpp"
#include "plugins/virtual_walls_joint_wrapper.hpp"

namespace mios {

class JointTorqueControllerPipeline : public ControllerPipeline{
public:
    JointTorqueControllerPipeline();
    void initialize(const Percept& p_0,Memory* memory) override;
    franka::Finishable* step(const Percept &p, const Actuator &cmd) override;
    bool is_valid_command(const franka::Finishable* const cmd) const;
    void update_percept(Percept::Controller &p) override;
    void terminate() override;

public:
    void set_virtual_cube(bool on);
    void set_virtual_joint_walls(bool on);
    void set_nullspace_control(bool on);

private:
    void initialize_cntr_joint_imp(const Percept &p,Memory* memory);
    void initialize_cntr_mux(const Percept &p, Memory *memory);
    void initialize_virt_cube(const Percept &p, Memory *memory);
    void initialize_virt_walls_joint(const Percept &p, Memory *memory);

    void input_cntr_joint_imp(const Percept& p);
    void input_cntr_mux(const Percept& p);
    void input_virt_cube(const Percept& p);
    void input_virt_joint_walls(const Percept& p);

private:
    bool is_virt_cube_valid(const Percept &p);
    bool is_virt_joint_walls_valid(const Percept &p);

private:
    bool m_virtual_cube_on;
    bool m_virtual_joint_walls_on;

    Eigen::Matrix<double,6,1> m_virt_cube_distances;
    Eigen::Matrix<double,14,1> m_virt_joint_walls_distances;

    franka::Torques m_panda_cmd;

    Eigen::Matrix<double,7,1> m_q_d_old;

private:
    cntr_mux::cntr_mux m_cntr_mux;
    virtual_cube::virtual_cube m_virt_cube;
    virtual_walls_joint::virtual_walls_joint m_virt_walls_joint;
    cntr_joint_var_imp::cntr_joint_var_imp m_cntr_joint_imp;

    cntr_mux::In_U_cntr_mux m_in_u_mux;
    virtual_cube::In_U_virtual_cube m_in_u_virt_cube;
    virtual_walls_joint::In_U_virtual_walls_joint m_in_u_virt_walls_joint;
    cntr_joint_var_imp::In_U_cntr_joint_var_imp m_in_u_cntr_joint_imp;

    cntr_mux::Out_Y_cntr_mux m_out_y_mux;
    virtual_cube::Out_Y_virtual_cube m_out_y_virt_cube;
    virtual_walls_joint::Out_Y_virtual_walls_joint m_out_y_virt_walls_joint;
    cntr_joint_var_imp::Out_Y_cntr_joint_var_imp m_out_y_cntr_joint_imp;
};

}
