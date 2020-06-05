#include "skills/insertion.hpp"
#include "strategies/move_to_pose.hpp"
#include "strategies/ff_wiggle_strategy.hpp"

namespace mios {

bool SkillParametersInsertion::read_parameters(const nlohmann::json &parameters){
    msrm_utils::read_json_param<double,2,1>(parameters,"traj_speed",traj_speed);
    msrm_utils::read_json_param(parameters,"F_limit",F_limit);
    msrm_utils::read_json_param<double,6,1>(parameters,"search_a",search_a);
    msrm_utils::read_json_param<double,6,1>(parameters,"search_f",search_f);
    msrm_utils::read_json_param<double,6,1>(parameters,"ROI_x",ROI_x);
    msrm_utils::read_json_param<double,6,1>(parameters,"ROI_phi",ROI_phi);
    return true;
}

Insertion::Insertion(const std::string &name, Memory *memory, const Percept &p):Skill("TestSkill1",{"object"},name,memory,p){

}


Eigen::Matrix<double, 3, 3> Insertion::get_O_R_T_0(const Percept &p) const{
    return get_object("hole")->O_T_OB.block<3,3>(0,0);
}

std::shared_ptr<ManipulationPrimitive> Insertion::get_initial_mp(const Percept &p_0){
    return create_move_mp(p_0);
}

std::optional<std::shared_ptr<ManipulationPrimitive> > Insertion::graph_transition(const Percept &p){
    if(get_active_mp()->get_name()=="move"){
        if(!is_stuck(p)){
            return {};
        }else{
            return create_wiggle_mp(p);
        }
    }
    if(get_active_mp()->get_name()=="wiggle"){
        if(!is_stuck(p)){
            return create_move_mp(p);
        }else{
            return {};
        }
    }
    return {};
}

std::shared_ptr<ManipulationPrimitive> Insertion::create_move_mp(const Percept &p){
    std::shared_ptr<SkillParametersInsertion> skill_params = get_parameters<SkillParametersInsertion>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("move",p);
    mp->create_strategy<MoveToPoseStrategy>("s_move",1);
    std::shared_ptr<MoveToPoseStrategy> s_move = mp->get_strategy<MoveToPoseStrategy>("s_move");
    s_move->set_goal(get_object("hole")->O_T_OB,skill_params->traj_speed,skill_params->traj_acc);
    return mp;
}

std::shared_ptr<ManipulationPrimitive> Insertion::create_wiggle_mp(const Percept &p){
    std::shared_ptr<SkillParametersInsertion> skill_params = get_parameters<SkillParametersInsertion>();
    std::shared_ptr<ManipulationPrimitive> mp = create_mp("wiggle",p);
    mp->create_strategy<FFWiggleStrategy>("wiggle_x",1);
    mp->get_strategy<FFWiggleStrategy>("s_move")->set_coefficients(Eigen::Matrix<double,6,1>::Zero(),skill_params->search_a,
                                                                   Eigen::Matrix<double,6,1>::Zero(),skill_params->search_f,
                                                                   Eigen::Matrix<double,6,1>::Zero(),Eigen::Matrix<double,6,1>::Zero());
    return mp;
}

void insertion::build_primitives(const Percept &p){

    this->_cf1_sum_force=0;
    this->_cf1_cnt=0;

    this->insert_mp<mp_basic>("insert",p);
    this->set_init_mp("insert");

    std::shared_ptr<ConfigMP_mp_basic> c_insert = std::static_pointer_cast<ConfigMP_mp_basic>(this->get_mp("insert")->get_config());

    std::shared_ptr<ConfigSkill_insertion> c = std::static_pointer_cast<ConfigSkill_insertion>(this->_config);

    Eigen::Matrix<double,4,4> O_T_hole_est=this->get_object_pose("hole");
    this->TF_T_hole_est=O_T_hole_est;
    Eigen::Matrix<double,3,1> x_current=msrm_utils::invert_matrix(this->_config->frames.O_R_TF)*p.TF_T_EE.block<3,1>(0,3);
    Eigen::Matrix<double,3,1> dir = this->TF_T_hole_est.block<3,1>(0,3)-x_current;
    dir(2)=0;
    Eigen::Matrix<double,3,1> dir_n = dir/msrm_utils::norm_2<3>(dir);

    this->dir_hole=dir_n;

    c_insert->F_h_p=c->k_h_p;
    c_insert->F_h_d=c->k_h_d;

    c_insert->ff_fourier_b_a<<c->wiggle_a_t(0),c->wiggle_a_t(0),0,c->wiggle_a_r(0),c->wiggle_a_r(0),c->wiggle_a_z(0);
    c_insert->ff_fourier_b_f<<c->wiggle_f_t(0),c->wiggle_f_t(0)*3.0/4.0,0,c->wiggle_f_r(0),c->wiggle_f_r(0)*3.0/4.0,c->wiggle_f_z(0);
    c_insert->dX_d<<c->speed(0)*c->user.dX_max(0),c->speed(1)*c->user.dX_max(1);
    c_insert->ddX_d<<c->user.ddX_max(0),c->user.ddX_max(1);

    c_insert->D_x<<200,200,200,0,0,0;
    c_insert->dX_limit<<c->user.dX_max(0),c->user.dX_max(0),c->user.dX_max(0),
            c->user.dX_max(1),c->user.dX_max(1),c->user.dX_max(1);

    c_insert->F_stop<<0,0,c->F_contact,0,0,0;
    c_insert->DF_stop<<0,0,2,0,0,0;

    std::shared_ptr<AttractorBasic> attr_insert=std::static_pointer_cast<AttractorBasic>(this->get_mp("insert")->get_attractor());
    attr_insert->attr_pose=this->TF_T_hole_est;

    attr_insert->attr_ff<<0,0,c->controller.F_ff_0(2),0,0,0;
}

bool Insertion::check_local_suc_conditions(const Percept &p){
    bool depth = p.proprioception.TF_T_EE(2,3)>this->TF_T_hole_est(2,3)-0.001;
    bool lateral = (p.proprioception.TF_T_EE.block<3,1>(0,3)-get_object("hole")->O_T_OB.block<3,1>(0,3)).norm()<0.002;
    return depth && lateral;
}

bool Insertion::check_local_ex_conditions(const Percept &p){
    return true;
}

bool Insertion::check_local_err_conditions(const Percept &p){
    double error_angle=acos(p.proprioception.TF_T_EE.block<3,1>(0,2).dot(this->TF_T_hole_est.block<3,1>(0,2)));
    double dist_xy=(p.proprioception.TF_T_EE.block<2,1>(0,3)-get_object("hole")->O_T_OB.block<2,1>(0,3)).norm();
    double dist_z=fabs(p.proprioception.TF_T_EE(2,3)-get_object("hole")->O_T_OB(2,3));
    double radius,depth;
    if(!msrm_utils::read_json_param(get_object("hole")->geometry,"radius",radius)){
        msrm_utils::print_error("Object "+get_object("hole")->name+" has no geometry property <depth>.");
        return false;
    }
    if(!msrm_utils::read_json_param(get_object("hole")->geometry,"depth",depth)){
        msrm_utils::print_error("Object "+get_object("hole")->name+" has no geometry property <radius>.");
        return false;
    }
    if(dist_xy>radius || dist_z>depth*2 || error_angle>30.0/180.0*M_PI || p.proprioception.TF_T_EE(2,3)<this->TF_T_hole_est(2,3)-depth-0.01){
        return true;
    }else{
        return false;
    }
}

void Insertion::evaluate(){

        double c_err_1=m_memory->read_parameters()->skill->time_max+exp((get_result().p_1.proprioception.TF_T_EE.block<3,1>(0,3)-get_object("hole")->O_T_OB.block<3,1>(0,3)).norm()*100)-1;
        double c_suc_1=std::chrono::duration_cast<std::chrono::seconds>(get_result().p_1.time-get_result().p_0.time).count();

        double c_err_2=m_memory->read_parameters()->user.F_ext_max(0)+exp((get_result().p_1.proprioception.TF_T_EE.block<3,1>(0,3)-get_object("hole")->O_T_OB.block<3,1>(0,3)).norm()*100)-1;
        double c_suc_2=0;
        if(m_cf1_cnt==0){
            c_suc_2=get_result().cost_err;
        }else{
            c_suc_2=m_cf1_sum_force/m_cf1_cnt;
        }
        msrm_utils::print_critical_error("COST_ERR: " + std::to_string(c_err_1));
        msrm_utils::print_critical_error("COST_SUC: " + std::to_string(c_suc_1));
        write_costs(m_memory->read_parameters()->skill->w_cost_function[0]*c_suc_1+m_memory->read_parameters()->skill->w_cost_function[1]*c_suc_2,
                m_memory->read_parameters()->skill->w_cost_function[0]*c_err_1+m_memory->read_parameters()->skill->w_cost_function[1]*c_err_2);
}

void Insertion::auxiliaries(const Percept &p){
    m_cf1_sum_force+=p.proprioception.K_F_ext_K.block<3,1>(0,0).norm();
    m_cf1_cnt++;
}

bool Insertion::is_stuck(const Percept &p){

}

}
